# 00 XIAO チェック（先生用）: 基板に付ける前に、XIAO ESP32C6 の「ライントレーサーで使う所」がちゃんと動くかを調べる
#
#   使い方: XIAO だけを USB で PC につなぐ（基板やブレッドボードには さしていない状態。ピンヘッダは はんだ付けしてあってよい）。
#           MicroPython（ESP32_GENERIC_C6）を書き込み、Thonny でこのファイルを開いて実行（linetracer.py は いらない）。
#           ジャンパー線（オス-オス）が 1 本あると 6. の ADC も調べられる（なければ 20 秒待つと とばす）。
#
#   調べること（ライントレーサーで使う所だけ）
#     1. MicroPython・メモリ・ファイル（linetracer.py を保存できるか）
#     2. 使う 11 本のピン D0〜D10: 1 本ずつ H / L を出し、ほかのピンに もれていないか
#        → ピンヘッダの はんだブリッジ、3V3・GND・5V とのショート、こわれたピンが分かる
#     3. PWM: モーター 4 本（D5・D8・D9・D10）を 20 kHz、ブザー（D4）を 4 kHz で同時に
#     4. フルカラー LED の信号（D6）を出せるか
#     5. センサーを読む速さ（走る制御が 1 秒に何回まわるか）
#     6. ADC（センサーの D0〜D2）: ジャンパー線で 3V3 と GND につなぐと 3.3 V / 0 V と読めるか
#     7. XIAO の上の黄色の LED（目で見る: 3 回点滅 → PWM でゆっくり明るく・暗く）
#   最後に まとめを表示。黄色の LED: ゆっくり点滅 = ぜんぶ OK、速く点滅 = NG がある
#
#   注意: 基板に さしたまま動かすと、基板の部品（センサー・ボタン・ドライバー）のせいで 2. が NG になる（XIAO が悪いのではない）。
#         モーターやブザーもつながっていると動いてしまうので、かならず XIAO だけで。

from machine import Pin, PWM, ADC
import machine
import time
import os
import sys
import gc

# ライントレーサー（Lite rev.L3）で使うピン（名前, GPIO, 使い道）。linetracer.py と同じ
PINS = (
    ("D0", 0, "右センサー S3 (ADC)"),
    ("D1", 1, "真ん中センサー S2 (ADC)"),
    ("D2", 2, "左センサー S1 (ADC)"),
    ("D3", 21, "赤外 LED"),
    ("D4", 22, "START ボタン + ブザー"),
    ("D5", 23, "左モーター IN2"),
    ("D6", 16, "フルカラー LED"),
    ("D7", 17, "モーター STBY"),
    ("D8", 19, "左モーター IN1"),
    ("D9", 20, "右モーター IN3"),
    ("D10", 18, "右モーター IN4"),
)
ADC_PINS = (("D0", 0), ("D1", 1), ("D2", 2))
MOTOR_PINS = (23, 19, 20, 18)
PIN_BUZZER = 22
PIN_RGB = 16
PIN_SENS_LED = 21
PIN_LED_XIAO = 15          # 黄色の LED（0 で点灯）

results = []               # (項目, "OK" / "NG" / "SKIP", 説明)


def report(item, state, msg=""):
    results.append((item, state, msg))
    print("  [{}] {}  {}".format(state, item, msg))


def head(t):
    print()
    print("=" * 50)
    print(t)
    print("=" * 50)


# ----------------------------------------------------------------- 1. MicroPython・メモリ・ファイル
def check_system():
    head("1. MicroPython・メモリ・ファイル")
    u = os.uname()
    print("  ボード     :", u.machine)
    print("  MicroPython:", u.release, "/", sys.version)
    try:
        print("  ID         :", "".join("{:02x}".format(b) for b in machine.unique_id()))
    except Exception:
        pass
    if "C6" in u.machine.upper():
        report("ボード", "OK", "ESP32-C6")
    else:
        report("ボード", "NG", "ESP32-C6 ではない → ESP32_GENERIC_C6 の MicroPython を書き込む")

    f = machine.freq()
    f = f[0] if isinstance(f, tuple) else f
    report("CPU", "OK" if f >= 80000000 else "NG", "{} MHz".format(f // 1000000))

    gc.collect()
    free = gc.mem_free()
    report("メモリ", "OK" if free >= 100000 else "NG", "空き {} KB".format(free // 1024))

    try:
        import neopixel    # noqa: F401  （フルカラー LED に使う）
        report("neopixel", "OK", "ある")
    except ImportError:
        report("neopixel", "NG", "neopixel が無い MicroPython")

    try:
        try:
            import esp32
            print("  チップの温度: 約 {} ℃".format(esp32.mcu_temperature()))
        except Exception:
            pass
        st = os.statvfs("/")
        free_fs = st[0] * st[3]
        name = "xiao_check.tmp"
        data = bytes(range(256)) * 32          # 8 KB
        with open(name, "wb") as fp:
            fp.write(data)
        with open(name, "rb") as fp:
            back = fp.read()
        os.remove(name)
        if back == data and free_fs >= 64 * 1024:
            report("ファイル", "OK", "書いて読めた。空き {} KB".format(free_fs // 1024))
        else:
            report("ファイル", "NG", "読み返しが合わない / 空き {} KB".format(free_fs // 1024))
    except Exception as e:
        report("ファイル", "NG", repr(e))


# ----------------------------------------------------------------- 2. ピン（はんだブリッジ・ショート・こわれたピン）
def check_pins():
    head("2. ピン D0〜D10（XIAO だけで動かすこと）")
    # 2a. 中のプルアップ / プルダウンだけで 1 / 0 になるか（GND・3V3 とショートしていると変わらない）
    bad = set()
    for level, pull, pname in ((1, Pin.PULL_UP, "プルアップ"), (0, Pin.PULL_DOWN, "プルダウン")):
        ps = [(n, Pin(g, Pin.IN, pull)) for n, g, _ in PINS]
        time.sleep_ms(5)
        for n, p in ps:
            if p.value() != level:
                bad.add(n)
                report("ピン " + n, "NG", "{}で {} にならない（{} とショート？）".format(
                    pname, level, "GND" if level else "3V3 / 5V"))
    # 2b. 1 本ずつ H（ほかはプルダウン）/ L（ほかはプルアップ）を出し、ほかに もれていないか
    for name, g, use in PINS:
        if name in bad:
            continue                           # ショートしているピンには出力しない
        msgs = []
        for level, pull in ((1, Pin.PULL_DOWN), (0, Pin.PULL_UP)):
            others = [(n, Pin(g2, Pin.IN, pull)) for n, g2, _ in PINS if g2 != g]
            p = Pin(g, Pin.OUT, value=level)
            time.sleep_us(300)
            if p.value() != level:
                msgs.append("{} を出せない".format("H" if level else "L"))
            leak = [n for n, q in others if q.value() == level]
            if leak:
                msgs.append("{} とつながっている（はんだブリッジ？）".format("・".join(leak)))
            p.init(Pin.IN, pull)
        if msgs:
            report("ピン " + name, "NG", " / ".join(msgs))
            bad.add(name)
        else:
            report("ピン " + name, "OK", use)
    for _, g, _ in PINS:
        Pin(g, Pin.IN, Pin.PULL_UP)            # 最後は入力に（何も出さない）
    return bad


# ----------------------------------------------------------------- 3. PWM
def check_pwm():
    head("3. PWM（モーター 4 本 20 kHz ＋ ブザー 4 kHz を同時に）")
    pwms = []
    try:
        for g in MOTOR_PINS:
            pwms.append(("モーター GPIO{}".format(g), PWM(Pin(g), freq=20000, duty_u16=32768), 20000))
        pwms.append(("ブザー D4", PWM(Pin(PIN_BUZZER), freq=4000, duty_u16=16384), 4000))
        time.sleep_ms(20)
        for name, p, f in pwms:
            fr = p.freq()
            du = p.duty_u16()
            want = 32768 if f == 20000 else 16384
            ok = abs(fr - f) <= f * 0.02 and abs(du - want) <= 700
            report("PWM " + name, "OK" if ok else "NG", "{} Hz, duty {} %".format(fr, du * 100 // 65535))
        # ライントレーサーと同じように duty を変えられるか（モーターの速さを変える）
        p = pwms[0][1]
        okd = True
        for d in (0, 16384, 49152, 65535):
            p.duty_u16(d)
            if abs(p.duty_u16() - d) > 700:
                okd = False
        report("PWM duty を変える", "OK" if okd else "NG", "0 / 25 / 75 / 100 %")
    except Exception as e:
        report("PWM", "NG", "作れない: " + repr(e))
    finally:
        for _, p, _ in pwms:
            p.deinit()
        for g in MOTOR_PINS + (PIN_BUZZER,):
            Pin(g, Pin.IN, Pin.PULL_UP)


# ----------------------------------------------------------------- 4. フルカラー LED の信号
def check_rgb():
    head("4. フルカラー LED の信号（D6、PL9823 の速さ）")
    try:
        from neopixel import NeoPixel
        np = NeoPixel(Pin(PIN_RGB, Pin.OUT), 6, timing=(350, 1360, 1360, 350))
        np.fill((0, 0, 0))
        t0 = time.ticks_us()
        for _ in range(10):
            np.write()
        dt = time.ticks_diff(time.ticks_us(), t0) / 10
        report("フルカラー LED 信号", "OK" if dt < 5000 else "NG", "1 回 {:.2f} ms".format(dt / 1000))
    except Exception as e:
        report("フルカラー LED 信号", "NG", repr(e))
    Pin(PIN_RGB, Pin.IN, Pin.PULL_UP)


# ----------------------------------------------------------------- 5. センサーを読む速さ
def check_speed():
    head("5. センサーを読む速さ")
    try:
        adc = [ADC(Pin(g), atten=ADC.ATTN_11DB) for _, g in ADC_PINS]
        t0 = time.ticks_us()
        for _ in range(100):
            for a in adc:
                a.read_u16()
        t_read = time.ticks_diff(time.ticks_us(), t0) / 300
        report("ADC 1 回", "OK" if t_read < 200 else "NG", "{:.0f} µs".format(t_read))

        # linetracer.py の read_raw()（赤外 LED ON で 3 本、OFF で 3 本）＋ 計算 と同じことを 200 回
        led = Pin(PIN_SENS_LED, Pin.OUT, value=0)
        t0 = time.ticks_us()
        for _ in range(200):
            led.value(1)
            time.sleep_us(300)
            on = [a.read_u16() for a in adc]
            led.value(0)
            time.sleep_us(300)
            off = [a.read_u16() for a in adc]
            v = [max(0, b - a) for a, b in zip(on, off)]
            total = sum(v) + 1
            pos = (v[2] - v[0]) * 1000 // total     # noqa: F841
        hz = 200 * 1000000 // time.ticks_diff(time.ticks_us(), t0)
        led.init(Pin.IN, Pin.PULL_UP)
        report("制御のまわる速さ", "OK" if hz >= 400 else "NG",
               "1 秒に {} 回（センサーだけ。400 回以上で OK）".format(hz))
    except Exception as e:
        report("センサーを読む速さ", "NG", repr(e))


# ----------------------------------------------------------------- 6. ADC（ジャンパー線）
def _volt(a):
    try:
        return a.read_uv() / 1000000
    except Exception:
        return a.read_u16() * 3.3 / 65535


def _wait(a, cond, sec=20):
    """cond(電圧) が 5 回続けて（0.1 秒）なりたつまで待つ。待てなければ None"""
    t0 = time.ticks_ms()
    n = 0
    last_print = -1
    while time.ticks_diff(time.ticks_ms(), t0) < sec * 1000:
        v = _volt(a)
        n = n + 1 if cond(v) else 0
        if n >= 5:
            return v
        left = sec - time.ticks_diff(time.ticks_ms(), t0) // 1000
        if left != last_print and left % 5 == 0:
            print("     ... あと {} 秒（いま {:.2f} V）".format(left, v))
            last_print = left
        time.sleep_ms(20)
    return None


def check_adc():
    head("6. ADC（センサーの D0〜D2）: ジャンパー線で つなぐ")
    print("  ジャンパー線で 3V3 ピンや GND ピンと つなぐ（USB を上にして右の列、上から 5V・GND・3V3）。")
    print("  なければ 20 秒待つと とばす。")
    for name, g in ADC_PINS:
        try:
            a = ADC(Pin(g), atten=ADC.ATTN_11DB)
        except Exception as e:
            report("ADC " + name, "NG", repr(e))
            continue
        print("  → {} を 3V3 に つないで".format(name))
        hi = _wait(a, lambda v: v > 2.8)
        if hi is None:
            report("ADC " + name, "SKIP", "3V3 につながなかった（または 2.8 V 未満しか読めない）")
            continue
        print("     {:.2f} V。次は {} を GND に つないで".format(hi, name))
        lo = _wait(a, lambda v: v < 0.15)
        if lo is None:
            report("ADC " + name, "SKIP", "3V3 = {:.2f} V。GND につながなかった（または 0.15 V 以上）".format(hi))
            continue
        report("ADC " + name, "OK", "3V3 = {:.2f} V, GND = {:.2f} V".format(hi, lo))
        print("     はずして OK")
        time.sleep_ms(1500)


# ----------------------------------------------------------------- 7. 黄色の LED（目で見る）
def check_led_xiao():
    head("7. 黄色の LED（XIAO の上）: 3 回点滅 → ゆっくり明るく・暗く を 2 回")
    led = Pin(PIN_LED_XIAO, Pin.OUT, value=1)
    for _ in range(3):
        led.value(0)
        time.sleep_ms(250)
        led.value(1)
        time.sleep_ms(250)
    p = PWM(led, freq=1000, duty_u16=65535)
    for _ in range(2):
        for d in list(range(65535, 0, -1300)) + list(range(0, 65535, 1300)):
            p.duty_u16(d)                    # 0 で いちばん明るい
            time.sleep_ms(10)
    p.deinit()
    led.init(Pin.OUT, value=1)
    report("黄色の LED", "SKIP", "目で見て たしかめる（点滅して、なめらかに明るさが変われば OK）")


# ----------------------------------------------------------------- まとめ
def summary(bad_pins):
    head("まとめ")
    ng = [r for r in results if r[1] == "NG"]
    skip = [r for r in results if r[1] == "SKIP"]
    print("  OK {}  NG {}  SKIP {}".format(len(results) - len(ng) - len(skip), len(ng), len(skip)))
    for item, state, msg in ng + skip:
        print("  [{}] {}  {}".format(state, item, msg))
    print()
    if ng:
        print("  ★ NG がある。この XIAO は そのままでは使わない。")
        if bad_pins:
            print("    ピンの NG は、まずピンヘッダの はんだ（となりと つながっていないか）を見て、直してから もう一度。")
            print("    基板に さしたまま動かしていないかも たしかめる。")
    else:
        print("  ★ ぜんぶ OK。ライントレーサーに使える。")
    led = Pin(PIN_LED_XIAO, Pin.OUT, value=1)
    ms = 100 if ng else 500
    for _ in range(30 if ng else 10):
        led.value(0)
        time.sleep_ms(ms)
        led.value(1)
        time.sleep_ms(ms)


print("XIAO ESP32C6 チェック（Linetracer2 Lite で使う所）")
print("XIAO だけを USB につないで動かすこと（基板に さしたままは ダメ）")
bad_pins = set()
try:
    check_system()
    bad_pins = check_pins()
    check_pwm()
    check_rgb()
    check_speed()
    check_adc()
    check_led_xiao()
    summary(bad_pins)
finally:
    for _, g, _ in PINS:
        Pin(g, Pin.IN, Pin.PULL_UP)
    Pin(PIN_LED_XIAO, Pin.OUT, value=1)
