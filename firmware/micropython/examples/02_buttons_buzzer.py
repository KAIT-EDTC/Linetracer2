# 02 ボタンとブザー: START を押すと「ド」、SELECT を押すと「ソ」が鳴る
from machine import Pin, PWM
import time

sw1 = Pin(16, Pin.IN, Pin.PULL_UP)   # 押すと 0 になる
sw2 = Pin(17, Pin.IN, Pin.PULL_UP)
bz = PWM(Pin(0))

while True:
    if sw1.value() == 0:
        bz.freq(523)          # ド
        bz.duty_u16(32768)
    elif sw2.value() == 0:
        bz.freq(784)          # ソ
        bz.duty_u16(32768)
    else:
        bz.duty_u16(0)        # 音を止める
    time.sleep(0.01)
