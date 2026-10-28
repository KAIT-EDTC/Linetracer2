// 03_WiFiControl  -  スマホの ブラウザで ラジコンの ように 動かす
//   ロボットが 自分で Wi-Fi の 電波を 出す（アクセスポイント）。インターネットは いらない。
//
//   1) 電池の スイッチを ON にして 電源を 入れる（LED が むらさき = じゅんび中、みどり = つないでよい）
//   2) スマホの Wi-Fi で「Linetracer2-XXXX」に つなぐ（XXXX は ロボットごとに ちがう。パスワードは 下の PASSWORD）
//      シリアルモニタ（115200 bps）にも 名前と パスワードが 出る
//   3) ページが 自動で ひらかない ときは ブラウザで http://192.168.4.1 を ひらく
//   4) まるい パッドを 指で ドラッグ = 走る、はなす = 止まる。ブザー・LED の 色・ライントレースも できる
//
//   あんぜん: スマホから 1 びょう 合図が とどかないと 止まる。ロボットの START を おしても 止まる。
//   1 台の ロボットに つなげる スマホは 1 台だけ。
#include <Linetracer2Lite.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include "index_html.h"

const char* PASSWORD = "edtc1234";  // 8 文字 以上。かえてよい
const uint32_t WATCHDOG_MS = 1000;  // これだけ スマホから 合図が ないと 止まる
const bool REVERSE = true;          // パッドを 上に たおすと 後ろに 走るとき true（前と 後ろを 入れかえる。回る 向きは そのまま）

Robot robot;
LineFollower follower(robot);
WebServer server(80);
DNSServer dns;

struct Level {
  float base, kp, kd;
};
const Level LEVELS[] = {{30, 0.025, 0.35}, {45, 0.032, 0.50}, {60, 0.040, 0.65}};  // 01_LineTrace と 同じ

float targetL = 0, targetR = 0;  // スマホからの 速さ（%）
uint32_t lastContact = 0;
Color ledColor = Colors::CYAN;
char ssid[24];

void stopAll() {
  if (follower.running()) follower.stop();
  targetL = targetR = 0;
}

// /api?l=..&r=..  運転（l, r = -100..100 %）。返事は センサーの 値など
void handleApi() {
  lastContact = millis();
  if (server.hasArg("l") && !follower.running()) {
    targetL = constrain(server.arg("l").toFloat(), -100.0f, 100.0f);
    targetR = constrain(server.arg("r").toFloat(), -100.0f, 100.0f);
  }
  int raw[lt2::N_SENS];
  robot.sensors.readRaw(raw);
  char json[160];
  snprintf(json, sizeof(json), "{\"mode\":\"%s\",\"cal\":%s,\"s\":[%d,%d,%d],\"l\":%d,\"r\":%d}",
           follower.running() ? "trace" : "drive", robot.sensors.calibrated() ? "true" : "false", raw[0], raw[1],
           raw[2], (int)(follower.running() ? follower.left : targetL),
           (int)(follower.running() ? follower.right : targetR));
  server.send(200, "application/json", json);
}

// /beep?f=..&ms=..
void handleBeep() {
  lastContact = millis();
  uint32_t f = server.hasArg("f") ? server.arg("f").toInt() : lt2::BEEP_FREQ;
  uint32_t ms = server.hasArg("ms") ? min<long>(server.arg("ms").toInt(), 1000) : 150;
  robot.beep(f, ms);
  server.send(200, "text/plain", "ok");
}

// /led?c=rrggbb
void handleLed() {
  lastContact = millis();
  uint32_t v = strtoul(server.arg("c").c_str(), nullptr, 16);
  ledColor = {(uint8_t)(v >> 16), (uint8_t)(v >> 8), (uint8_t)v};
  server.send(200, "text/plain", "ok");
}

// /cal  その場で 左右に まわって 白と 黒を おぼえる（3 びょうくらい）
void handleCal() {
  stopAll();
  robot.led.fill(Colors::BLUE);
  bool ok = robot.autoCalibrate();
  robot.led.fill(ok ? Colors::GREEN : Colors::RED);
  if (ok) {
    const Robot::Note good[] = {{1568, 100}, {2093, 200}};
    robot.melody(good, 2);
  } else {
    robot.beep(400, 600);
  }
  lastContact = millis();
  server.send(200, "application/json", ok ? "{\"ok\":true}" : "{\"ok\":false}");
}

// /trace?on=1&level=1..3
void handleTrace() {
  lastContact = millis();
  bool on = server.arg("on") == "1";
  stopAll();
  if (on) {
    if (!robot.sensors.calibrated()) {
      server.send(409, "text/plain", "calibrate first");
      return;
    }
    int lv = constrain(server.arg("level").toInt(), 1, 3);
    const Level& L = LEVELS[lv - 1];
    follower.start(L.base, L.kp, L.kd);
  }
  server.send(200, "text/plain", "ok");
}

void handleRoot() { server.send(200, "text/html", INDEX_HTML); }

// スマホの「ネットに つながるか」の 確認にも このページを 返す -> ページが 自動で ひらく（キャプティブポータル）
void handleNotFound() {
  server.sendHeader("Location", "http://192.168.4.1/", true);
  server.send(302, "text/plain", "");
}

void setup() {
  Serial.begin(115200);
  robot.begin();
  robot.motors.reverse = REVERSE;
  robot.led.fill(Colors::PURPLE);

  uint8_t mac[6];
  WiFi.mode(WIFI_AP);
  WiFi.softAPmacAddress(mac);
  snprintf(ssid, sizeof(ssid), "Linetracer2-%02X%02X", mac[4], mac[5]);
  const int channels[] = {1, 6, 11};  // ロボットが たくさん あっても 電波が ぶつかりにくいように ちらす
  WiFi.softAP(ssid, PASSWORD, channels[mac[5] % 3], 0, 1);  // さいごの 1 = つなげる スマホは 1 台
  dns.start(53, "*", WiFi.softAPIP());

  server.on("/", handleRoot);
  server.on("/api", handleApi);
  server.on("/beep", handleBeep);
  server.on("/led", handleLed);
  server.on("/cal", handleCal);
  server.on("/trace", handleTrace);
  server.onNotFound(handleNotFound);
  server.begin();

  Serial.printf("\nWi-Fi: %s  password: %s  ->  http://%s\n", ssid, PASSWORD, WiFi.softAPIP().toString().c_str());
  robot.led.fill(Colors::GREEN);
  const Robot::Note hello[] = {{1047, 120}, {1319, 120}, {1568, 200}};
  robot.melody(hello, 3);
}

void loop() {
  dns.processNextRequest();
  server.handleClient();

  // あんぜん: スマホから 合図が こない / START が おされた -> 止まる
  bool moving = follower.running() || targetL != 0 || targetR != 0;
  if (moving && millis() - lastContact > WATCHDOG_MS) {
    Serial.println("no signal from the phone -> stop");
    stopAll();
  }
  if (robot.startPressed()) {
    stopAll();
    robot.beep(400, 200);
    robot.waitRelease();
  }

  if (follower.running()) {
    follower.update();  // 線を 見うしなうと 自分で 止まる
    return;
  }

  static uint32_t tRun = 0, tLed = 0;
  if (millis() - tRun >= 5) {  // 5 ms ごとに 少しずつ 速さを かえる（ソフトスタート）
    tRun = millis();
    robot.motors.run(targetL, targetR);
  }
  if (millis() - tLed >= 50) {
    tLed = millis();
    if (targetL != 0 || targetR != 0) robot.led.flow(targetL, targetR, ledColor);
    else robot.led.fill(ledColor);
  }
}
