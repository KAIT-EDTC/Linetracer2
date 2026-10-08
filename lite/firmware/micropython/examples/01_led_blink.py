# 01 Lチカ: 基板のフルカラー LED（5 こ）と、XIAO に付いている黄色の LED を交互に光らせる
# フルカラー LED は 1 本の線で 5 こ つながっている（NeoPixel と同じしくみ）。色は (赤, 緑, 青) を 0〜255 で
from machine import Pin
from neopixel import NeoPixel
import time

led = NeoPixel(Pin(16), 5, timing=(350, 1360, 1360, 350))   # D6 につながる 5 こ（PL9823 の速さ）
led_xiao = Pin(15, Pin.OUT)   # 黄（XIAO の上の小さい LED）。0 で光る（つなぎ方が逆）

while True:
    led.fill((0, 40, 0))      # 5 こ ぜんぶ 緑（40 = 少し暗め。255 だとまぶしくて熱くなる）
    led.write()               # write() で はじめて 光る
    led_xiao.value(1)         # 黄は消える
    time.sleep(0.5)
    led.fill((0, 0, 0))       # ぜんぶ 消す
    led.write()
    led_xiao.value(0)         # 黄が光る
    time.sleep(0.5)
