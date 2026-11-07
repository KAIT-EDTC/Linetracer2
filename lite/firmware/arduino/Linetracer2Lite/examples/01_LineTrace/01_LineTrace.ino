// 01_LineTrace  -  Linetracer2 Lite のふつうのプログラム（3 センサーの PD ライントレース）
//   MicroPython の main.py と 同じ うごき。
//
//   キャリブレーション（手で、電源 ON の あと 1 回）: LED むらさき = センサーを 3 つとも 黒の 上に おいて START、
//                    LED しろ = 3 つとも 白の 上に おいて START。はかった 値は シリアルモニタ（115200 bps）に 出る
//                    （黒い 線と センサーの 列が 同じ 向きに なるように、ロボットを 線に 横むきに おくと 3 つとも 黒に のる）
//                    MANUAL_CAL = false に すると 自動（線の上で その場で 左右に まわる。START 1 回目）
//   START みじかく : 走る。もう一度 START で 止まる。
//   START ながおし : 速さレベル 1〜3 を かえる（LED が 消えたら はなす。ピッと鳴って 黄色の LED が 1〜3 こ つく）
//                    電源 ON の ときは レベル 3 = 基本の速さ 60 %。曲がるときも どの 車輪も 80 % まで
//   LED（左右 3 こずつ）: みどり = じゅんび OK、むらさき / しろ = 黒 / 白を はかる、あお = 自動キャリブレーション中、
//                    あか = キャリブレーション しっぱい（もう一度 黒から）、
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
    {10, 0.001, 0.00},  // 1: ゆっくり
    {45, 0.032, 0.50},  // 2: ふつう
    {60, 0.040, 0.65},  // 3: はやい
};
const int N_LEVELS = sizeof(LEVELS) / sizeof(LEVELS[0]);
int level = 0;          // 電源を 入れたときの レベル（3 = 基本の速さ 60 %）
const float MAX_PCT = 80;  // 曲がるときも 車輪は これより 速くしない（%）
// true = 走っている間 0.05 びょうごとに 線の 位置・P・D・左右の 速さを シリアルに 出す（調整用。USB を つないで
// シリアルモニタか シリアルプロッタを ひらいて おく。ひらかずに つなぐだけだと 出力が つまって 走りが おかしくなる）
const bool DEBUG_PRINT = false;
// true = S2 を 線の 上、S3 を 線の 右の 境目に のせて 走る（ロボットは 線の 少し 左を 走る）。19 mm の 線で
// センサーが 12 mm おきだと、まん中では S1 / S3 が 線の 境目に とどかず、ずれ始めを 見のがして ぐらつく。
// 境目の S3 は 少しの ずれでも 値が かわる（Kp は 半分くらいから 合わせる）。false = 3 つの 重心で 線の まん中を 走る
const bool EDGE = true;
const bool MANUAL_CAL = true;  // true = 手で キャリブレーション（黒 → 白）、false = 自動（その場で 左右に まわる）
const bool REVERSE = false;  // 前に 走るはずが 後ろに 走るとき true（前と 後ろを 入れかえる。回る 向きは そのまま）

void setup() {
  Serial.begin(115200);
  robot.begin();
  robot.motors.reverse = REVERSE;
  if (robot.startPressed()) {  // START を おしたまま 電源 ON -> しずかモード
    robot.volume = 0;
    robot.blink(2, 100);
    robot.waitRelease();
  }
  const Robot::Note hello[] = {{1047, 120}, {1319, 120}, {1568, 200}};
  robot.melody(hello, 3);
  Serial.println("Linetracer2 Lite (XIAO ESP32C6, Arduino). Motors run only with the battery switch ON.");
  if (!MANUAL_CAL) robot.led.value(true);  // じゅんび OK（手で するときは loop() が 黒を はかる ところから）
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

// センサー 3 つの 値の 平均（32 回 = 約 20 ms）。大きいほど 白い
void sample(int out[lt2::N_SENS]) {
  long sum[lt2::N_SENS] = {0, 0, 0};
  int r[lt2::N_SENS];
  for (int k = 0; k < 32; k++) {
    robot.sensors.readRaw(r);
    for (int i = 0; i < lt2::N_SENS; i++) sum[i] += r[i];
  }
  for (int i = 0; i < lt2::N_SENS; i++) out[i] = sum[i] / 32;
}

// START を おすまで 今の 値を シリアルに 出しつづけ、はなしたら その 場所の 値を はかる
void measureOnPress(const char* what, Color c, int out[lt2::N_SENS]) {
  robot.led.fill(c);
  Serial.printf("\nセンサーを 3 つとも %s の 上に おいて START\n", what);
  uint32_t t = 0;
  while (!robot.startPressed()) {
    if (millis() - t > 300) {
      t = millis();
      int r[lt2::N_SENS];
      robot.sensors.readRaw(r);
      Serial.printf("  いま   S1 %4d  S2 %4d  S3 %4d\n", r[0], r[1], r[2]);
    }
    delay(10);
  }
  robot.waitRelease();
  delay(300);  // ボタンを おして ずれた ロボットが おちつくまで
  sample(out);
  Serial.printf("  %s   S1 %4d  S2 %4d  S3 %4d\n", what, out[0], out[1], out[2]);
  robot.beep(2000, 60);
}

void manualCalibrate() {
  int black[lt2::N_SENS], white[lt2::N_SENS];
  measureOnPress("黒", Colors::PURPLE, black);
  measureOnPress("白", Colors::WHITE, white);
  LineSensors& s = robot.sensors;
  Serial.println("  センサー  黒    白    差（" + String(lt2::CAL_MIN_SPAN) + " より 大きければ OK）");
  for (int i = 0; i < lt2::N_SENS; i++) {
    s.lo[i] = black[i];
    s.hi[i] = white[i];
    int span = white[i] - black[i];
    Serial.printf("  S%d     %4d  %4d  %5d  %s\n", i + 1, black[i], white[i], span,
                  span > lt2::CAL_MIN_SPAN ? "OK" : "NG");
  }
  if (!s.calibrated()) {
    Serial.println("しっぱい: 黒と 白の 差が 小さい。センサーの 高さ、置き方を みて もう一度 黒から");
    s.resetCalibration();  // 次の loop() で また 黒から
    robot.led.fill(Colors::RED);
    robot.beep(400, 600);  // ひくい音 = しっぱい
    delay(1000);
    return;
  }
  Serial.println("OK! 線の 上に おいて START で 走る");
  const Robot::Note good[] = {{1568, 100}, {2093, 200}};
  robot.melody(good, 2);
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
  follower.maxPct = MAX_PCT;
  follower.edge = EDGE;
  follower.start(lv.base, lv.kp, lv.kd);
  uint32_t tLog = 0;
  while (!robot.startPressed()) {
    if (!follower.update()) break;  // 線を 見うしなって あきらめた
    if (DEBUG_PRINT && millis() - tLog >= 50) {
      tLog = millis();
      bool lost = follower.pos == lt2::LINE_LOST;  // 見うしなったら pos/10 = 0、lost = 100
      const int* v = robot.sensors.values;  // 0（白）〜 1000（黒）
      Serial.printf("S1/10:%d,S2/10:%d,S3/10:%d,pos/10:%d,P:%.1f,D:%.1f,L:%.1f,R:%.1f,lost:%d\n", v[0] / 10,
                    v[1] / 10, v[2] / 10, lost ? 0 : follower.pos / 10, follower.pTerm, follower.dTerm, follower.left,
                    follower.right, lost ? 100 : 0);
    }
  }
  if (follower.running()) follower.stop();
  robot.led.value(true);
  robot.waitRelease();
}

void loop() {
  if (MANUAL_CAL && !robot.sensors.calibrated()) {
    manualCalibrate();
    return;
  }
  Press kind = robot.waitPress();
  if (kind == Press::LONG) {
    changeLevel();
  } else if (!robot.sensors.calibrated()) {
    calibrate();
  } else {
    runCourse();
  }
}
