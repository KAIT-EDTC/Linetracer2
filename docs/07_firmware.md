# 07. ソフトウェア（MicroPython）

> ファイル: `firmware/micropython/`
> - `linetracer.py` … ライブラリ（ピン番号・モーター・センサー・ブザー）。**基板を変えたらここを直す**
> - `main.py` … 標準プログラム（PD 制御のライントレース）
> - `examples/01〜05` … 授業用の段階別サンプル

---

## 1. 準備（はじめの 1 回）

1. **MicroPython を書き込む**
   - https://micropython.org/download/ から、使うボードに合った `.uf2` をダウンロード
     （Raspberry Pi Pico → `RPI_PICO`、Pico 2 → `RPI_PICO2`、Pico W → `RPI_PICO_W`）
   - Pico の **BOOTSEL ボタンを押しながら** USB をつなぐ → `RPI-RP2`（Pico 2 は `RP2350`）というドライブが出る → `.uf2` をコピー
2. **Thonny**（https://thonny.org/）をインストール → 右下のインタプリタを「MicroPython (Raspberry Pi Pico)」に
3. `linetracer.py` と `main.py` を Pico に保存（Thonny の「ファイル」→「名前を付けて保存」→「Raspberry Pi Pico」）
   - `main.py` という名前のファイルは、電源を入れると自動で動く

## 2. 授業の流れ（例）

| 回 | サンプル | 学ぶこと |
|----|---------|---------|
| 1 | `01_led_blink.py` | 出力、`time.sleep` |
| 2 | `02_buttons_buzzer.py` | 入力（プルアップ）、`if`、PWM で音 |
| 3 | `03_sensor_monitor.py` | アナログ値、白と黒の違い、Thonny のプロッター |
| 4 | `04_motor_test.py` | モーターの前進・後退・旋回（車輪を浮かせて） |
| 5 | `05_simple_tracer.py` | ON/OFF 制御のライントレース（2 センサー） |
| 6 | `main.py` | 6 センサーで線の位置を計算 → P 制御 → PD 制御、速さの調整 |

## 3. ライブラリの使い方

```python
from linetracer import Robot
robot = Robot()

robot.motors.run(30, 30)        # 左 30%、右 30%（100% = 3.0V）。マイナスで後退
robot.motors.brake()            # ブレーキ
robot.motors.stop()             # 空転（力を抜く）

robot.sensors.calibrate()       # 呼ぶたびに白と黒を覚える（線の上で左右に動かす）
robot.auto_calibrate()          # その場で左右に回って自動キャリブレーション
v = robot.sensors.read()        # [S1..S6] 0(白)〜1000(黒)
pos = robot.sensors.position()  # 線の位置 -2500(左端)〜0(真ん中)〜+2500(右端)、見失うと None

robot.start_pressed()           # START が押されていれば True
robot.led1.value(1)             # LED1 点灯
robot.buzzer.beep(2)            # ピピッ
robot.battery.read()            # 電池電圧 [V]
```

### 3.1 モーターまわりの安全機能（子どもが知らなくても動く）

| 機能 | しくみ |
|------|-------|
| 電圧上限 | `run(100, 100)` でもモーターには 3.0 V（`MAX_MOTOR_VOLT`）までしかかからないよう、**電池電圧を測ってデューティを自動計算**。電池が減っても同じ % なら同じ速さ |
| ソフトスタート | `run()` 1 回あたりデューティは最大 4% しか変えない（`RAMP_PER_CALL`）。急発進でドライバの過電流保護が働くのを防ぐ |
| ISD 自動復帰 | 走行中は 0.1 秒ごとに STBY を一瞬 L→H にして、過電流で止まった出力を復帰させる |
| ブレーキ駆動 | PWM の OFF 時間はショートブレーキ（速度がデューティに比例しやすい） |
| 起動時は停止 | Pico が起動するまでドライバの入力は内部プルダウンで L → モーターは回らない |

### 3.2 センサーの読み方（外乱光キャンセル）

1. 赤外 LED を点灯 → 0.3 ms 待つ → 6 個読む
2. LED を消灯 → 0.3 ms 待つ → 6 個読む
3. 「消灯の値 − 点灯の値」= 反射光だけの強さ（窓からの光などを打ち消す）

1 回の読み取りは約 1 ms。`robot.sensors.ambient_cancel = False` にすると速くなる（点灯のみ）。

MUX のチャンネルは配線の都合でセンサー順と違う（`SENSOR_CH = (4, 2, 1, 0, 3, 5)`）。ライブラリの中で並べ替えているので、使う側は S1〜S6 の順で考えればよい。

## 4. PD 制御（`main.py`）

```
誤差 e   = 線の位置（-2500〜+2500）
操作量 u = Kp × e + Kd × (e の変化 / ミリ秒)
左モーター = 基本速度 + u
右モーター = 基本速度 − u
```

| レベル | 基本速度 | Kp | Kd |
|-------|---------|----|----|
| 1（遅い） | 30% | 0.012 | 0.35 |
| 2 | 45% | 0.016 | 0.50 |
| 3（速い） | 60% | 0.020 | 0.65 |

**これらは計算上の初期値**。実機で必ず調整する:

1. Kd = 0 にして Kp を少しずつ上げる → 線の上でジグザグ（蛇行）し始める少し手前の値にする
2. Kd を上げて蛇行を止める（上げすぎるとガタガタ震える）
3. 基本速度を上げる → カーブで外れたら Kp・Kd を上げ直す

線を見失ったら、最後に見えた側へ強く曲がり、0.8 秒見つからなければ止まる。

## 5. ピン番号を変えたいとき

`linetracer.py` の先頭の `PIN_…` を書き換えるだけ。基板（rev.A）の配線は `03_circuit.md` の表のとおり。

## 6. よくある質問

- **Q. モーターが回らない** → 電池ボックスのスイッチ、`robot.battery.read()` が 3V 以上か。USB だけではモーターは回らない（仕様）。
- **Q. 左右どちらかが逆に回る** → `LEFT_INVERT` / `RIGHT_INVERT` を変える。
- **Q. 走るとすぐ止まる・リセットする** → 電池が弱い。`MAX_MOTOR_VOLT` を 2.5 にする、ソフトスタートを強める（`RAMP_PER_CALL = 0.02`）。
- **Q. Pico W / Pico 2 W を使いたい** → そのまま動く。ただし基板上の Pico の LED は GP25 ではない（`Pin("LED")` を使う）。
- **Q. C/C++（Arduino）で書きたい** → Arduino-Pico（earlephilhower 版）で同じピン番号を使えば OK。PWM は `analogWriteFreq(20000)`、`analogWriteRange(65535)`。
