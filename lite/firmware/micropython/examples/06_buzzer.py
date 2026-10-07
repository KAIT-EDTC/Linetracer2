# 06 ブザー: ドレミを鳴らす。ブザーは赤い LED と同じピン（D6）につながっている
#   ・ピンを 1 にしたまま → LED が光るだけ（ブザーは鳴らない）
#   ・ピンを速く 0/1 させる（PWM）→ ブザーが鳴る（LED もうすく光る）
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
