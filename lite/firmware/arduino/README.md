# Linetracer2 Lite の Arduino（C++）版ソフト

MicroPython 版（`../micropython/`）と同じことを Arduino IDE（C++）で書いたもの。ピン番号・設定・動きは MicroPython の `linetracer.py` / `main.py` と同じ（rev.L3 の基板用）。

> **どちらか一方だけ**: Arduino で書き込むと XIAO の中の MicroPython は消える。MicroPython に戻すときは `lite/README.md` §8.1 のとおり書き込み直す。

| フォルダ | 中身 |
|---------|------|
| `Linetracer2Lite/src/` | ライブラリ（`Robot` ＝ モーター・センサー・ボタン・ブザー・フルカラー LED、`LineFollower` ＝ PD ライントレース） |
| `Linetracer2Lite/examples/01_LineTrace/` | ふつうのライントレース（`main.py` と同じ操作） |
| `Linetracer2Lite/examples/02_SelfTest/` | 先生用: 組み立てたロボットの動作チェック（LED・ブザー・ボタン・センサー・モーター・Wi-Fi） |
| `Linetracer2Lite/examples/03_WiFiControl/` | ロボットが Wi-Fi の電波を出して、スマホのブラウザでラジコンのように動かす |

## 1. 準備（1 回だけ）

1. **Arduino IDE 2** を入れる。
2. 「ファイル → 基本設定 → 追加のボードマネージャの URL」に次を入れる:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. 「ツール → ボード → ボードマネージャ」で **esp32（Espressif Systems）3.x** を入れる（3.3.11 で確認）。
4. ライブラリを入れる: `Linetracer2Lite` フォルダを丸ごと **スケッチブックの `libraries/`** にコピーする（Linux / Mac: `~/Arduino/libraries/`、Windows: `ドキュメント\Arduino\libraries\`）。ZIP にして「スケッチ → ライブラリをインクルード → .ZIP 形式のライブラリをインストール」でもよい。ほかのライブラリはいらない（Wi-Fi・Web サーバーは esp32 に入っている）。
5. Arduino IDE を開き直すと「ファイル → スケッチ例 → Linetracer2Lite」に 3 つのスケッチが出る。

## 2. 書き込み

- ボード: **XIAO_ESP32C6**（ツール → ボード → esp32 → XIAO_ESP32C6）
- **ツール → USB CDC On Boot: Enabled**（標準で Enabled。Disabled だとシリアル出力が D6 ＝ フルカラー LED の信号線に出てしまうので、コンパイルがエラーで止まるようにしてある）
- ポート: XIAO をつないで出てきたもの（Linux は `/dev/ttyACM0`）
- 書き込めないときは XIAO の **BOOT ボタンを押したまま USB を差す**（書き込みモード）。書き込んだら RESET を押す。
- シリアルモニタは **115200 bps**。

コマンド（arduino-cli、リポジトリの `lite/firmware/arduino/` で）:

```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32C6:CDCOnBoot=cdc --library Linetracer2Lite Linetracer2Lite/examples/01_LineTrace
```

```bash
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32C6:CDCOnBoot=cdc -p /dev/ttyACM0 Linetracer2Lite/examples/01_LineTrace
```

## 3. スケッチ

### 3.1 `01_LineTrace`（ふつうのライントレース）

操作は MicroPython の `main.py` と同じ（`lite/README.md` §8.2 の表）。START 短く: 1 回目 = 自動キャリブレーション、2 回目から = 走る／止まる。START 長押し: 速さレベル 1→2→3。START を押したまま電源 ON: しずかモード。速さと Kp / Kd はスケッチの `LEVELS` で変える。

### 3.2 `02_SelfTest`（動作チェック、先生用）

シリアルモニタを開いて `a`（全部）か `1`〜`7`（1 つだけ）を送る。PC が無くても START を短く押せば全部が順に動く。

| # | テスト | 判定 | NG のときに見る所（シリアルモニタにも出る） |
|---|-------|------|------------------------------------------|
| 1 | XIAO の黄色 LED、フルカラー LED を 1 こずつ赤・緑・青 | 目で見る | 光らない LED の 1 つ前の DOUT か、その LED の DIN のはんだ |
| 2 | ブザー（ドレミと 4 kHz） | 耳で聞く | ブザー・R9 のはんだ |
| 3 | START ボタン（10 秒以内に押す） | 自動 | ボタン・R10・D4 のはんだ |
| 4 | 赤外 LED ON / OFF の S1〜S3 の電圧（白い紙の上） | 自動 | OFF でも低い → 10 kΩ・センサーの向き。ON と OFF が同じ → センサー・100 Ω、3 つとも → Q1・R7・D3 |
| 5 | 黒い線の上で左右に 8 秒動かす（白と黒の差） | 自動 | センサーの高さ・はんだ |
| 6 | モーター（車輪を浮かせ、電池 ON → START）左前・左後・右前・右後・両方前 | 目で見る | 逆に回る車輪 → `robot.motors.left.invert = true` など |
| 7 | Wi-Fi のスキャン（アンテナの確認） | 自動 | 1 つも見つからないとき（電波の無い部屋ならしかたない） |

最後にまとめ（OK / NG / 見て確認）。NG が無ければ LED が緑、あれば赤。テストパッドをテスターで測るときは 4 の電圧と比べる（`lite/README.md` §4.9）。

### 3.3 `03_WiFiControl`（スマホで動かす）

ロボットが自分で Wi-Fi の電波を出す（アクセスポイント）。インターネットも家の Wi-Fi もいらない。

1. 電池のスイッチ ON で電源を入れる（LED むらさき = 準備中 → 緑 = つないでよい、「ド・ミ・ソ」）。
2. スマホの Wi-Fi で **`Linetracer2-XXXX`** につなぐ。XXXX はロボットごとに違う（XIAO の MAC アドレスの最後 4 けた。シリアルモニタにも出る）。パスワードはスケッチの `PASSWORD`（標準 `edtc1234`）。
3. たいていページが自動で開く。開かなければブラウザで **http://192.168.4.1**。
4. まるいパッドを指でドラッグ = 走る（上 = 前、横 = 回る）、離す = 止まる。「はやさ」で最高速度。ほかに ブザー・メロディ・LED の色・センサーの値（白いほど長いバー）・ライントレース（① 白黒をおぼえる → ② スタート / ストップ）。

あんぜん:
- スマホから **1 秒合図が来ないと止まる**（画面を閉じた・電波が切れた・ページが固まった）。
- ロボットの **START を押すと止まる**（「ブー」）。
- 1 台のロボットにつなげるスマホは 1 台だけ。電波はロボットごとに ch 1 / 6 / 11 に分かれる（教室で何台も使うとき）。

しくみ: ページはロボットの中にある（`index_html.h`）。ページが `/api?l=左&r=右`（-100〜100 %）を 1 秒に約 10 回送り、ロボットがセンサーの値を返す。ほかに `/beep?f=&ms=`、`/led?c=rrggbb`、`/cal`、`/trace?on=1&level=1..3`。

## 4. ライブラリの使い方

```cpp
#include <Linetracer2Lite.h>
Robot robot;
LineFollower follower(robot);       // PD ライントレース（1 回の update() で 1 歩）

void setup() {
  Serial.begin(115200);
  robot.begin();                    // はじめに必ず
}

void loop() {
  int v[3];
  robot.sensors.read(v);            // [S1, S2, S3] 0(白)〜1000(黒)（キャリブレーションのあと）
  int pos = robot.sensors.position();   // -1000(左)〜0(真ん中)〜+1000(右)、見失うと lt2::LINE_LOST
  Press kind = robot.waitPress();   // ボタンを押して離すまで待つ → Press::SHORT か Press::LONG（1.5 秒以上）
  robot.led.set(0, Colors::RED);    // フルカラー LED（0〜2 = 左のうしろ→前、3〜5 = 右の前→うしろ）
  robot.led.show();                 // show() で光る。fill(Colors::BLUE) は 6 こ全部、side(左の色, 右の色)
  robot.led.set(1, {255, 128, 0});  // 色は {赤, 緑, 青} 0〜255 でもよい
  robot.led.flow(30, 30);           // 流れる光（何度も呼ぶ）
  robot.beep();                     // 「ピッ」（4 kHz、0.1 秒）。robot.beep(880, 300) で「ラ」を 0.3 秒
  const Robot::Note doMiSo[] = {{1047, 150}, {1319, 150}, {1568, 300}};
  robot.melody(doMiSo, 3);
  robot.volume = 0.2;               // 音の大きさ 0〜1（標準 0.4）。0 = しずかモード
  robot.motors.run(40, 40);         // 左 %, 右 %（-100〜100、100 % = 3.0 V）。何度も呼ぶと少しずつ加速
  robot.motors.brake();             // すぐ止まる（stop() = 惰性で止まる、off() = ドライバーも待機に）
  robot.ledXiao(true);              // XIAO の黄色い LED
  robot.motors.batteryVolt = 3.7;   // 電池の電圧（決め打ち）。ニッケル水素なら 3.7
  robot.motors.left.invert = true;  // 前のはずが後ろに回る車輪があるとき
}
```

MicroPython 版とのちがい:
- センサーの生の値（`readRaw`）は **0〜4095**（MicroPython は 0〜65535）。キャリブレーションの合格ライン `CAL_MIN_SPAN` は 250（= 65535 換算で 4000、同じ）。
- フルカラー LED は RMT（ESP32 の信号を作る回路）で PL9823 のタイミング（0.35 / 1.36 µs）を出している。Adafruit NeoPixel などのライブラリはいらない。
- PWM は LEDC。モーター 4 本（20 kHz、2 タイマー）、ブザーは鳴る間だけ 1 本使う。

## 5. まだ確かめていないこと

- **実機ではまだ動かしていない**（基板が無いので、コンパイルと、スマホの画面をまねたサーバーでの確認だけ。2026-10-27）。
- フルカラー LED のタイミング（RMT 20 MHz で 0.35 / 1.35 µs）で PL9823 が正しく光るか。色が入れかわるときは `Lights::set()` の並び。
- Wi-Fi で走りながらのセンサー読み取り・ライントレースの速さ（Web の処理が入るので、`01_LineTrace` より 1 周が少し遅い）。
- iPhone / Android でページが自動で開くか（開かなければ http://192.168.4.1 を手で開く）。
