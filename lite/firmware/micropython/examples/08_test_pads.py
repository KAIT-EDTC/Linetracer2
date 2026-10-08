# 08 テストパッド（先生用）: テスターで基板の どこが こわれているかを さがす
#   黒い テスト棒を GND のパッドに。赤い テスト棒を 下の パッドに 当てて、表示の 値と くらべる。
#   電池を入れて スイッチ ON（USB だけだと VBAT は 0 V、VSYS は 5 V）。
#
#   パッド   ふつうの値                     ちがうときに うたがう所
#   VBAT     3.6〜4.8 V（D1 の 上の パッド）   電池・電池ボックス・J1 の はんだ
#   VSYS     VBAT より 0.2〜0.3 V ひくい      D1 の 向き・はんだ（USB だけなら 5 V）
#   3V3      3.3 V                          XIAO の ピンヘッダ（3V3・GND）のはんだ、ブリッジ
#   IR       赤外 LED が ON: 0.1 V くらい、OFF: 2 V くらい（下の 1 の 間に 切りかわる）
#                                           Q1 の 向き、R7、センサーの 足（LED 側）
#   S1〜S3   白い 紙: 低い（0.3〜1 V）、黒い 線: 高い（3 V くらい）。赤外 LED が ON の とき
#                                           センサーの 向き・高さ、10 kΩ（だいだい）、100 Ω（ちゃ）
from linetracer import Robot
import time

robot = Robot()
s = robot.sensors

print("1) 赤外 LED を 5 びょう ON → 5 びょう OFF（IR と S1〜S3 を はかる）")
for on in (True, False):
    s.leds(on)
    print("   赤外 LED", "ON" if on else "OFF")
    for _ in range(5):
        v = [round(a.read_u16() * 3.1 / 65535, 2) for a in s.adc]   # XIAO が はかった 電圧（だいたい）
        print("     XIAO が はかった S1 S2 S3 =", v, "V")
        time.sleep(1)

print("2) フルカラー LED を 1 こずつ（ひからない LED の ひとつ まえまでは 信号が きている）")
for i in range(6):
    robot.led.fill("off")
    robot.led[i] = "white"
    robot.led.show()
    print("   LED", i)
    time.sleep(1)
robot.led.fill("off")
print("おわり")
