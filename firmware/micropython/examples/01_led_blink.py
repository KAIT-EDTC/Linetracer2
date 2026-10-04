# 01 Lチカ: LED1 と LED2 を交互に光らせる
from machine import Pin
import time

led1 = Pin(18, Pin.OUT)   # 赤
led2 = Pin(19, Pin.OUT)   # 黄

while True:
    led1.value(1)
    led2.value(0)
    time.sleep(0.5)
    led1.value(0)
    led2.value(1)
    time.sleep(0.5)
