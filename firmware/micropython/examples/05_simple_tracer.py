# 05 いちばん簡単なライントレース（左右のセンサーだけ見る「ON/OFF 制御」）
#   S3（左寄り）と S4（右寄り）の 2 つだけを使う。
#   線が左にあれば左に曲がる、右にあれば右に曲がる。
#   最初に START を押して、線の上でゆっくりロボットを左右に動かしてキャリブレーション。
from linetracer import Robot
import time

robot = Robot()
m, s = robot.motors, robot.sensors

print("キャリブレーション: 線の上で左右に動かしてから START")
while not robot.start_pressed():
    s.calibrate()
robot.wait_release()
robot.buzzer.beep(2)

SPEED = 30
while not robot.start_pressed():
    v = s.read()              # 0 = 白 ... 1000 = 黒
    left_black = v[2] > 500   # S3
    right_black = v[3] > 500  # S4
    if left_black and not right_black:
        m.run(SPEED * 0.3, SPEED)      # 左に曲がる
    elif right_black and not left_black:
        m.run(SPEED, SPEED * 0.3)      # 右に曲がる
    else:
        m.run(SPEED, SPEED)            # まっすぐ
m.brake()
time.sleep(0.3)
m.stop()
