# 01 Lチカ: 基板の赤い LED と、Pico に付いている緑の LED を交互に光らせる
from machine import Pin
import time

led = Pin(18, Pin.OUT)        # 赤（基板の D2）
led_pico = Pin("LED", Pin.OUT)  # 緑（Pico の上の LED）

while True:
    led.value(1)
    led_pico.value(0)
    time.sleep(0.5)
    led.value(0)
    led_pico.value(1)
    time.sleep(0.5)
