# 06 ブザー: ドレミを鳴らす。ブザーはスタートボタンと同じピン（D4）につながっている
#   ・ふだんはボタンを読む入力
#   ・鳴らすあいだだけ、ピンを速く 0/1 させる（PWM）→ ブザーが鳴る（ボタンを押していても鳴る）
#   ・LED（D6）はブザーと関係なく使える
from linetracer import Robot
import time

robot = Robot()

DOREMI = [523, 587, 659, 698, 784, 880, 988, 1047]   # ド レ ミ ファ ソ ラ シ ド（Hz）
for f in DOREMI:
    robot.beep(f, 200)
    time.sleep_ms(50)

time.sleep(0.5)
robot.beep()                  # 「ピッ」: いちばん大きく鳴るのは 4000 Hz くらい
time.sleep(0.3)
robot.melody([(1047, 120), (1319, 120), (1568, 120), (2093, 300)])   # できた！の音

print("ボタンを押すと「ピッ」（30 秒）")
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 30000:
    if robot.start_pressed():
        robot.led.value(1)
        robot.beep(2000, 80)
        robot.led.value(0)
        robot.wait_release()
    time.sleep_ms(10)
