# 03 センサーの値を見る
#   Thonny の「表示」→「プロッター」を開くとグラフで見られる。
#   白い紙と黒い線の上で、値がどう変わるか調べよう。
from linetracer import LineSensors, Battery
import time

s = LineSensors()
bat = Battery()
if bat.usb():
    print("USB につながっている（電池の電圧は測れない）")
else:
    print("battery: %.2f V" % bat.read(8))

while True:
    r = s.read_raw()          # 大きいほど明るい（白）
    print(r[0], r[1], r[2])   # S1（左）, S2（真ん中）, S3（右）
    time.sleep(0.05)
