# 02 ボタン: START を押している間だけ LED が光る。押した回数も数える
from machine import Pin
from neopixel import NeoPixel
import time

sw = Pin(22, Pin.IN, Pin.PULL_UP)   # 押すと 0 になる（基板の D4）
led = NeoPixel(Pin(16), 6, timing=(350, 1360, 1360, 350))   # フルカラー LED 6 こ

count = 0
before = 1
while True:
    now = sw.value()
    led.fill((40, 0, 0) if now == 0 else (0, 0, 0))   # 押している間は 赤
    led.write()
    if before == 1 and now == 0:        # 「離れている → 押された」に変わった瞬間
        count += 1
        print("押した回数:", count)
    before = now
    time.sleep(0.02)                    # チャタリング（接点のバタつき）よけ
