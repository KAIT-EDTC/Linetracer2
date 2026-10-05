# 05 いちばん簡単なライントレース（左右のセンサーだけ見る「ON/OFF 制御」）
#   S1（左）と S3（右）の 2 つだけを使う。
#   左が黒なら左に曲がる、右が黒なら右に曲がる、どちらも白ならまっすぐ。
#   最初に、線の上でゆっくりロボットを左右に動かしながら START を押す（キャリブレーション）。
from linetracer import Robot
import time

robot = Robot()
m, s = robot.motors, robot.sensors

print("キャリブレーション: 線の上で左右に動かしてから START")
while not robot.start_pressed():
    s.calibrate()
robot.wait_release()
robot.blink(2)

SPEED = 30
while not robot.start_pressed():
    v = s.read()              # 0 = 白 ... 1000 = 黒
    left_black = v[0] > 500   # S1
    right_black = v[2] > 500  # S3
    if left_black and not right_black:
        m.run(SPEED * 0.3, SPEED)      # 左に曲がる
    elif right_black and not left_black:
        m.run(SPEED, SPEED * 0.3)      # 右に曲がる
    else:
        m.run(SPEED, SPEED)            # まっすぐ
m.brake()
time.sleep(0.3)
m.stop()
