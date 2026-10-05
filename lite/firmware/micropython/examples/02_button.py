# 02 ボタン: START を押している間だけ LED が光る。押した回数も数える
from machine import Pin
import time

sw = Pin(16, Pin.IN, Pin.PULL_UP)   # 押すと 0 になる
led = Pin(18, Pin.OUT)

count = 0
before = 1
while True:
    now = sw.value()
    led.value(1 if now == 0 else 0)
    if before == 1 and now == 0:        # 「離れている → 押された」に変わった瞬間
        count += 1
        print("押した回数:", count)
    before = now
    time.sleep(0.02)                    # チャタリング（接点のバタつき）よけ
