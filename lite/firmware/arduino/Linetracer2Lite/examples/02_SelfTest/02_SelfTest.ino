// 02_SelfTest  -  組み立てた ロボットの 動作チェック（先生用）
//   シリアルモニタ（115200 bps）を ひらいて 使う。PC が なくても START で 全部の テストが 順に 動く。
//
//   シリアルモニタで 1〜7 を 送る = その テストだけ、a = 全部、START みじかく = 全部
//     1 XIAO の 黄色 LED と フルカラー LED（1 こずつ 赤・緑・青）     ... 目で 見る
//     2 ブザー（ドレミ）                                               ... 耳で 聞く
//     3 START ボタン（10 びょう いないに おす）                         ... 自動で 判定
//     4 センサー: 赤外 LED ON/OFF の 電圧（テストパッド S1〜S3 と くらべる）... 自動で 判定
//     5 センサー: 黒い 線の 上を 左右に 動かす（8 びょう）              ... 自動で 判定
//     6 モーター（車輪を 浮かせて、電池の スイッチ ON）                  ... 目で 見る
//     7 Wi-Fi（まわりの 電波を さがす = アンテナの チェック）            ... 自動で 判定
//   さいごに まとめ: OK / NG / 見て確認。NG が なければ LED が みどり、あれば あか。
#include <Linetracer2Lite.h>
#include <WiFi.h>

Robot robot;

enum class Result { NotRun, Ok, Ng, Look };
const char* RESULT_TEXT[] = {"-", "OK", "NG", "見て確認"};
const char* NAMES[] = {"LED", "ブザー", "START ボタン", "センサー 電圧", "センサー 白黒", "モーター", "Wi-Fi"};
const int N_TESTS = 7;
Result results[N_TESTS];

void printMenu() {
  Serial.println();
  Serial.println("=== Linetracer2 Lite セルフテスト ===");
  for (int i = 0; i < N_TESTS; i++) Serial.printf("  %d  %s\n", i + 1, NAMES[i]);
  Serial.println("  a  全部（START みじかく でも 同じ）");
}

// ------------------------------------------------------------------ 1 LED
Result testLeds() {
  Serial.println("XIAO の 黄色 LED を 3 回 点滅");
  for (int i = 0; i < 3; i++) {
    robot.ledXiao(true);
    delay(200);
    robot.ledXiao(false);
    delay(200);
  }
  Serial.println("フルカラー LED を 1 こずつ 赤 -> 緑 -> 青（0..2 = 左 後ろ->前、3..5 = 右 前->後ろ）");
  Serial.println("  ひからない LED が あったら、その ひとつ まえの LED の DOUT か その LED の DIN の はんだを みる");
  const Color cs[] = {Colors::RED, Colors::GREEN, Colors::BLUE};
  for (int i = 0; i < lt2::N_RGB; i++) {
    Serial.printf("  LED %d\n", i);
    for (const Color& c : cs) {
      robot.led.fill(Colors::OFF);
      robot.led.set(i, c);
      robot.led.show();
      delay(250);
    }
  }
  robot.led.fill(Colors::WHITE);
  delay(500);
  robot.led.fill(Colors::OFF);
  return Result::Look;
}

// ------------------------------------------------------------------ 2 buzzer
Result testBuzzer() {
  Serial.println("ドレミファソラシド と 4 kHz の ピー（いちばん 大きく 鳴る 音）");
  const Robot::Note scale[] = {{523, 150}, {587, 150}, {659, 150}, {698, 150}, {784, 150},
                               {880, 150}, {988, 150}, {1047, 300}, {0, 200}, {4000, 300}};
  robot.melody(scale, sizeof(scale) / sizeof(scale[0]));
  return Result::Look;
}

// ------------------------------------------------------------------ 3 button
Result testButton() {
  robot.waitRelease();
  Serial.println("START を 10 びょう いないに おして はなす");
  robot.led.fill(Colors::YELLOW);
  uint32_t t0 = millis();
  while (!robot.startPressed()) {
    if (millis() - t0 > 10000) {
      robot.led.fill(Colors::OFF);
      Serial.println("  おされなかった: ボタンの はんだ、R10（1 kΩ）、D4 の ピンを みる");
      return Result::Ng;
    }
    delay(10);
  }
  uint32_t t1 = millis();
  robot.led.fill(Colors::GREEN);
  robot.waitRelease();
  Serial.printf("  おした（%lu ms）\n", millis() - t1);
  robot.led.fill(Colors::OFF);
  return Result::Ok;
}

// ------------------------------------------------------------------ 4 sensor voltages
Result testSensorVolts() {
  Serial.println("センサーの 下に 白い 紙を おく。赤外 LED を ON / OFF して S1〜S3 の 電圧を はかる");
  Serial.println("  （テスターで テストパッド S1〜S3 を はかっても 同じ くらいの はず）");
  float on[lt2::N_SENS], off[lt2::N_SENS];
  delay(1000);
  robot.sensors.leds(true);
  delay(5);
  robot.sensors.readVolts(on);
  robot.sensors.leds(false);
  delay(5);
  robot.sensors.readVolts(off);
  Serial.printf("  赤外 LED ON : S1 %.2f V  S2 %.2f V  S3 %.2f V   (白い 紙なら ひくい 0.3〜1 V)\n", on[0], on[1], on[2]);
  Serial.printf("  赤外 LED OFF: S1 %.2f V  S2 %.2f V  S3 %.2f V   (高い 2.5 V 以上)\n", off[0], off[1], off[2]);
  Result r = Result::Ok;
  int ledSide = 0;
  for (int i = 0; i < lt2::N_SENS; i++) {
    float diff = off[i] - on[i];
    if (off[i] < 2.0f) {
      Serial.printf("  S%d: OFF でも ひくい -> 10 kΩ（だいだい）の はんだ、センサーの 向き、強い 光（日光）が 当たっていないか\n", i + 1);
      r = Result::Ng;
    } else if (diff < 0.3f) {
      Serial.printf("  S%d: ON と OFF が ほとんど 同じ（%.2f V）-> センサーの 向き・高さ、100 Ω（ちゃ）\n", i + 1, diff);
      r = Result::Ng;
      ledSide++;
    }
  }
  if (ledSide == lt2::N_SENS) Serial.println("  3 つとも 赤外 LED が ついていない -> Q1 の 向き、R7、D3 ピンの はんだ（テストパッド IR）");
  return r;
}

// ------------------------------------------------------------------ 5 sensor white/black
Result testSensorLine() {
  Serial.println("8 びょう の 間に センサーを 黒い 線の 上で 左右に ゆっくり 動かす（LED が 線の 位置を しめす）");
  robot.sensors.resetCalibration();
  uint32_t t0 = millis(), tPrint = 0;
  while (millis() - t0 < 8000) {
    robot.sensors.calibrate();
    int raw[lt2::N_SENS];
    robot.sensors.readRaw(raw);
    // 線の 上の センサーの 側を 光らせる（キャリブレーション前でも わかるように 生の 値で）
    int dark = 0;
    for (int i = 0; i < lt2::N_SENS; i++) {
      int span = robot.sensors.hi[i] - robot.sensors.lo[i];
      bool black = span > lt2::CAL_MIN_SPAN && raw[i] < robot.sensors.lo[i] + span / 2;
      dark |= black << i;
    }
    robot.led.side((dark & 0b011) ? Colors::CYAN : Colors::OFF, (dark & 0b110) ? Colors::CYAN : Colors::OFF);
    if (millis() - tPrint > 250) {
      tPrint = millis();
      Serial.printf("  S1 %4d  S2 %4d  S3 %4d\n", raw[0], raw[1], raw[2]);
    }
    delay(10);
  }
  robot.led.fill(Colors::OFF);
  LineSensors& s = robot.sensors;
  Result r = Result::Ok;
  for (int i = 0; i < lt2::N_SENS; i++) {
    int span = s.hi[i] - s.lo[i];
    bool good = span > lt2::CAL_MIN_SPAN;
    Serial.printf("  S%d: 白 %4d  黒 %4d  差 %4d  %s\n", i + 1, s.hi[i], s.lo[i], span, good ? "OK" : "NG（差が 小さい）");
    if (!good) r = Result::Ng;
  }
  if (r == Result::Ng) Serial.println("  線の 上を 通らなかった? 通ったなら センサーの 高さ（紙から 3〜5 mm）と はんだを みる");
  return r;
}

// ------------------------------------------------------------------ 6 motors
Result testMotors() {
  Serial.println("車輪を 浮かせて、電池ボックスの スイッチを ON。じゅんびが できたら START");
  robot.led.fill(Colors::ORANGE);
  robot.waitPress();
  robot.led.fill(Colors::OFF);
  struct Step {
    const char* name;
    float l, r;
  };
  const Step steps[] = {{"左 前へ", 40, 0}, {"左 後ろへ", -40, 0}, {"右 前へ", 0, 40}, {"右 後ろへ", 0, -40},
                        {"両方 前へ", 40, 40}};
  for (const Step& st : steps) {
    Serial.printf("  %s\n", st.name);
    robot.led.side(st.l ? Colors::GREEN : Colors::OFF, st.r ? Colors::GREEN : Colors::OFF);
    uint32_t t0 = millis();
    while (millis() - t0 < 1200) {
      robot.motors.run(st.l, st.r);  // ゆっくり 加速する（ソフトスタート）
      delay(5);
    }
    robot.motors.brake();
    delay(500);
  }
  robot.motors.stop();
  robot.led.fill(Colors::OFF);
  Serial.println("  前へ の はずが 後ろに 回った 車輪は、スケッチで robot.motors.left.invert / right.invert = true");
  Serial.println("  回らない: 電池・スイッチ、モーターの はんだ、ドライバ（U2）の はんだ。とちゅうで XIAO が");
  Serial.println("  リセットした（LED が 消えた）なら 電池が へっている");
  return Result::Look;
}

// ------------------------------------------------------------------ 7 Wi-Fi
Result testWifi() {
  Serial.println("まわりの Wi-Fi を さがす（XIAO の アンテナの チェック）");
  robot.led.fill(Colors::PURPLE);
  WiFi.mode(WIFI_STA);
  int n = WiFi.scanNetworks();
  robot.led.fill(Colors::OFF);
  if (n <= 0) {
    WiFi.mode(WIFI_OFF);
    Serial.println("  1 つも 見つからない（まわりに 電波が ない 場所なら しかたない）");
    return Result::Look;
  }
  int best = 0;
  for (int i = 1; i < n; i++)
    if (WiFi.RSSI(i) > WiFi.RSSI(best)) best = i;
  Serial.printf("  %d こ 見つかった。いちばん 強い: %s  %d dBm\n", n, WiFi.SSID(best).c_str(), (int)WiFi.RSSI(best));
  WiFi.scanDelete();
  WiFi.mode(WIFI_OFF);
  return Result::Ok;
}

// ------------------------------------------------------------------
Result (*const TESTS[N_TESTS])() = {testLeds,       testBuzzer, testButton, testSensorVolts,
                                    testSensorLine, testMotors, testWifi};

void runTest(int i) {
  Serial.printf("\n--- %d %s ---\n", i + 1, NAMES[i]);
  results[i] = TESTS[i]();
  robot.motors.stop();  // 何が あっても モーターは 止める
  Serial.printf("=> %s\n", RESULT_TEXT[(int)results[i]]);
}

void summary() {
  Serial.println("\n=== まとめ ===");
  bool anyNg = false;
  for (int i = 0; i < N_TESTS; i++) {
    Serial.printf("  %d %-14s %s\n", i + 1, NAMES[i], RESULT_TEXT[(int)results[i]]);
    anyNg |= results[i] == Result::Ng;
  }
  robot.led.fill(anyNg ? Colors::RED : Colors::GREEN);
  if (anyNg) robot.beep(400, 600);
  else {
    const Robot::Note good[] = {{1568, 100}, {2093, 200}};
    robot.melody(good, 2);
  }
}

void runAll() {
  for (int i = 0; i < N_TESTS; i++) {
    runTest(i);
    delay(800);
  }
  summary();
}

void setup() {
  Serial.begin(115200);
  robot.begin();
  delay(1500);  // USB の シリアルが つながるのを 少し 待つ
  Serial.printf("\nchip %s rev %d, %lu MHz, flash %lu KB, MAC %s\n", ESP.getChipModel(), ESP.getChipRevision(),
                ESP.getCpuFreqMHz(), ESP.getFlashChipSize() / 1024, WiFi.macAddress().c_str());
  printMenu();
  robot.led.fill(Colors::WHITE);
  delay(300);
  robot.led.fill(Colors::OFF);
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c >= '1' && c < '1' + N_TESTS) {
      runTest(c - '1');
      printMenu();
    } else if (c == 'a' || c == 'A') {
      runAll();
      printMenu();
    }
  }
  if (robot.startPressed()) {
    robot.waitRelease();
    runAll();
    printMenu();
  }
  delay(10);
}
