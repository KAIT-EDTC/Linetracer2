# 04 モーターのテスト（車輪を浮かせて実行！）
#   1) 前進 → 2) 後退 → 3) その場で右回り → 4) その場で左回り
#   前進のはずが後ろに回る車輪があったら、linetracer.py の
#   LEFT_INVERT / RIGHT_INVERT を True/False 入れ替える（またはモーターの線を入れ替える）
from linetracer import Robot
import time

robot = Robot()
m = robot.motors
print("battery: %.2f V" % robot.battery.read(8))

for name, l, r in (("forward", 40, 40), ("back", -40, -40), ("turn right", 40, -40), ("turn left", -40, 40)):
    print(name)
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 1500:
        m.run(l, r)            # ゆっくり加速する（ソフトスタート）
        time.sleep_ms(5)
    m.brake()
    time.sleep(0.5)
m.stop()
print("done")
