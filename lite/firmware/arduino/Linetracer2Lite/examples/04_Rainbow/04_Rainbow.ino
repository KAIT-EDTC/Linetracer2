// 04_Rainbow  -  フルカラー LED に にじ色を 上（前）から 下（後ろ）へ 流す
//   ロボットを 前を 上に して 見ると、左右の LED（3 こずつ）を にじ色が 上から 下へ ながれる。
//
//   START みじかく : 速さを かえる（ゆっくり → ふつう → はやい）
//   START ながおし : 流れる 向きを 反対に（下から 上へ）
//   USB だけで 光る（電池は いらない）。
#include <Linetracer2Lite.h>

Robot robot;

const float SPEEDS[] = {0.15, 0.4, 1.0};  // 1 びょうに 色が 何周 するか
const int N_SPEEDS = sizeof(SPEEDS) / sizeof(SPEEDS[0]);
const float STEP = 0.12;                  // となりの LED との 色の ずれ（1 = 1 周）
int speed = 1;
bool down = true;  // true = 上（前）から 下（後ろ）へ
float hue = 0;     // いちばん 上の LED の 色（0〜1 で にじ 1 周）

// 色相 h（0〜1、赤 → 黄 → 緑 → 水 → 青 → むらさき → 赤）を 赤・緑・青に
Color rainbow(float h) {
  h = h - floorf(h);
  float x = h * 6;
  int k = (int)x;
  uint8_t up = (x - k) * 255, dn = 255 - up;
  switch (k) {
    case 0: return {255, up, 0};
    case 1: return {dn, 255, 0};
    case 2: return {0, 255, up};
    case 3: return {0, dn, 255};
    case 4: return {up, 0, 255};
    default: return {255, 0, dn};
  }
}

void setup() {
  robot.begin();
}

void loop() {
  static uint32_t tPrev = millis();
  uint32_t now = millis();
  float dt = (now - tPrev) / 1000.0f;
  tPrev = now;

  // 上の LED の 色を 先に すすめ、下の LED は 少し 前の 色に する -> 色が 上から 下へ 流れる
  hue += SPEEDS[speed] * dt * (down ? 1 : -1);
  hue -= floorf(hue);  // 0〜1 に もどす
  for (int j = 0; j < 3; j++) {  // j = 0 が いちばん 上（前）
    Color c = rainbow(hue - j * STEP);
    robot.led.set(lt2::LEFT_SIDE[j], c);
    robot.led.set(lt2::RIGHT_SIDE[j], c);
  }
  robot.led.show();

  if (robot.startPressed()) {
    if (robot.waitPress() == Press::LONG) {
      down = !down;
    } else {
      speed = (speed + 1) % N_SPEEDS;
      robot.beep(1000 + 500 * speed, 60);  // 速いほど 高い 音
    }
    tPrev = millis();
  }
  delay(20);
}
