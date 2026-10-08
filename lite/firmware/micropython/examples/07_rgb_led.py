# 07 フルカラー LED: 1 こずつ ちがう色、にじ色、センサーの位置
#   robot.led[番号] = 色  → robot.led.show() で光る。番号は 0〜4（つながっている順）:
#     0 = 前の左、1 = 前の真ん中、2 = 前の右、3 = うしろの右、4 = うしろの左
#   色は "red" "orange" "yellow" "green" "cyan" "blue" "purple" "pink" "white" "off" か (赤, 緑, 青) 0〜255
from linetracer import Robot, LEFT_TO_RIGHT
import time

robot = Robot()
led = robot.led

# 1) つながっている順に 1 こずつ
for i, c in enumerate(("red", "yellow", "green", "blue", "purple")):
    led[i] = c
    led.show()
    time.sleep(0.4)
time.sleep(1)

# 2) にじ色が 左から右へ 流れる（LEFT_TO_RIGHT = 左から何番目が どの LED か）
rainbow = ("red", "orange", "yellow", "green", "blue")
for t in range(20):
    for k in range(5):
        led[LEFT_TO_RIGHT[k]] = rainbow[(k + t) % 5]
    led.show()
    time.sleep(0.15)

# 3) 線の ある 場所の LED が 光る
#    はじめの 5 びょうは「白と黒を おぼえる」時間: 手で ロボットを 線の上で 左右に ゆっくり うごかす（青）
print("5 びょう、線の上で ロボットを 左右に うごかして（白と黒を おぼえる）")
led.fill("blue")
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 5000:
    robot.sensors.calibrate()
print("線の上で ロボットを 左右に うごかしてみよう（30 びょう）")
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 30000:
    led.bar(robot.sensors.position())
    time.sleep_ms(50)
led.fill("off")
