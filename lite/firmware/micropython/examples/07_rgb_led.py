# 07 フルカラー LED: 1 こずつ ちがう色、ながれる ひかり、線の ある がわ
#   robot.led[番号] = 色  → robot.led.show() で光る。番号は 0〜5（つながっている順）:
#     0 = 左の うしろ、1 = 左の まんなか、2 = 左の まえ、3 = 右の まえ、4 = 右の まんなか、5 = 右の うしろ
#   色は "red" "orange" "yellow" "green" "cyan" "blue" "purple" "pink" "white" "off" か (赤, 緑, 青) 0〜255
from linetracer import Robot
import time

robot = Robot()
led = robot.led

# 1) つながっている順に 1 こずつ（左の うしろ → 左の まえ → 右の まえ → 右の うしろ）
for i, c in enumerate(("red", "orange", "yellow", "green", "blue", "purple")):
    led[i] = c
    led.show()
    time.sleep(0.4)
time.sleep(1)

# 2) ながれる ひかり: 左は ゆっくり、右は はやく（数字は モーターの はやさと おなじ -100〜100）
print("ながれる ひかり（10 びょう）")
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    led.flow(20, 60)                  # 左 20、右 60（マイナスに すると うしろ → まえ）
    time.sleep_ms(20)

# 3) 線の ある がわが 光る
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
