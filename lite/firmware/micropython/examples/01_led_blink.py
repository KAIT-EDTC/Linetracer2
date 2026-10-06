# 01 Lチカ: 基板の赤い LED と、XIAO に付いている黄色の LED を交互に光らせる
from machine import Pin
import time

led = Pin(16, Pin.OUT)        # 赤（基板の D2）。1 で光る
led_xiao = Pin(15, Pin.OUT)   # 黄（XIAO の上の小さい LED）。0 で光る（つなぎ方が逆）

while True:
    led.value(1)
    led_xiao.value(1)         # 黄は消える
    time.sleep(0.5)
    led.value(0)
    led_xiao.value(0)         # 黄が光る
    time.sleep(0.5)
