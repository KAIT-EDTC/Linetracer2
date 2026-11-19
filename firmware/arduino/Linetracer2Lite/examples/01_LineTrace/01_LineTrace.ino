// 01_LineTrace  -  Linetracer2 Lite のふつうのプログラム（3 センサーの PD ライントレース）
//   MicroPython の main.py と 同じ うごき。
//
//   START みじかく : 1 回目 = 自動キャリブレーション（線の上で その場で 左右に まわる）
//                    2 回目から = 走る。もう一度 START で 止まる。
//   START ながおし : 速さレベル 1〜3 を かえる（LED が 消えたら はなす。ピッと鳴って 黄色の LED が 1〜3 こ つく）
//   LED（左右 3 こずつ）: みどり = じゅんび OK、あお = キャリブレーション中、あか = キャリブレーション しっぱい、
//                    走っている間: 車輪の 速さで 前から 後ろへ 光が 流れる（線を 見うしなうと あか）
//   ブザー         : 電源 ON で あいさつ、走る前に 「ピ・ピ・ピ・ピー」、しっぱいすると ひくい音
//                    （START を おしたまま 電源 ON = しずかモード: 音の かわりに LED が 光る）
//   USB だけでは モーターは 動かない（電池ボックスの スイッチを ON）。
//
// 線の 上に おいてから START を おす。
#include <Linetracer2Lite.h>

Robot robot;
LineFollower follower(robot);

// 速さレベル -> (基本の速さ %, Kp, Kd)   100 % = モーターに 3.0 V
// （コースに あわせて 調整する: まず Kp、つぎに Kd）
struct Level {
  float base, kp, kd;
};
const Level LEVELS[] = {
    {30, 0.025, 0.35},  // 1: ゆっくり
    {45, 0.032, 0.50},  // 2: ふつう
    {60, 0.040, 0.65},  // 3: はやい
};
const int N_LEVELS = sizeof(LEVELS) / sizeof(LEVELS[0]);
int level = 1;

void setup() {
  Serial.begin(115200);
  robot.begin();
  if (robot.startPressed()) {  // START を おしたまま 電源 ON -> しずかモード
    robot.volume = 0;
    robot.blink(2, 100);
    robot.waitRelease();
  }
  const Robot::Note hello[] = {{1047, 120}, {1319, 120}, {1568, 200}};
  robot.melody(hello, 3);
  Serial.println("Linetracer2 Lite (XIAO ESP32C6, Arduino). Motors run only with the battery switch ON.");
  robot.led.value(true);  // じゅんび OK
}

void changeLevel() {
  level = level % N_LEVELS + 1;
  Serial.printf("level %d\n", level);
  delay(300);
  robot.led.value(false);
  delay(300);
  robot.led.count(level);  // 黄色の LED が 1〜3 こ
  for (int i = 0; i < level; i++) {
    robot.beep(2000, 120);
    delay(150);
  }
  delay(600);
  robot.led.value(true);
}

void calibrate() {
  robot.led.fill(Colors::BLUE);  // キャリブレーション中
  robot.beep(2000, 60);          // ロボットから 手を はなす ...
  delay(1000);                   // ... 1 びょう後に まわりはじめる
  bool ok = robot.autoCalibrate();
  LineSensors& s = robot.sensors;
  Serial.printf("%s  lo=[%d %d %d] hi=[%d %d %d]\n", ok ? "calibrated" : "calibration failed", s.lo[0], s.lo[1],
                s.lo[2], s.hi[0], s.hi[1], s.hi[2]);
  if (!ok) {
    robot.led.fill(Colors::RED);
    robot.beep(400, 600);  // ひくい音 = しっぱい
    delay(1000);
  } else {
    const Robot::Note good[] = {{1568, 100}, {2093, 200}};
    robot.melody(good, 2);
  }
  robot.led.value(true);
}

void runCourse() {
  const uint32_t go[] = {2000, 2000, 2000, 4000};  // ピ・ピ・ピ・ピー ... スタート!
  for (uint32_t f : go) {
    robot.beep(f, f < 4000 ? 80 : 250);
    delay(250);
  }
  const Level& lv = LEVELS[level - 1];
  robot.led.value(false);
  robot.waitRelease();
  follower.start(lv.base, lv.kp, lv.kd);
  while (!robot.startPressed()) {
    if (!follower.update()) break;  // 線を 見うしなって あきらめた
  }
  if (follower.running()) follower.stop();
  robot.led.value(true);
  robot.waitRelease();
}

void loop() {
  Press kind = robot.waitPress();
  if (kind == Press::LONG) {
    changeLevel();
  } else if (!robot.sensors.calibrated()) {
    calibrate();
  } else {
    runCourse();
  }
}
