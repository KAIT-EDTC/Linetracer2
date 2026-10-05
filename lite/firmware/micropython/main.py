# main.py  -  Linetracer2 Lite standard program (PD line following, 3 sensors)
#
#   START short press : 1st time = auto calibration (robot spins on the line)
#                       after that = run.  Press START again to stop.
#   START long press  : change speed level 1..3 (hold until the Pico's LED lights, then let go;
#                       the red LED blinks the new level)
#   red LED on        : ready (the Lite board has no power LED)
#
# Put the robot on the line before pressing START.

import time
from linetracer import Robot

robot = Robot()
m, s = robot.motors, robot.sensors

# speed level -> (base speed %, Kp, Kd)   100 % = 3.0 V on the motors
# Position is -1000 .. +1000 (3 sensors, 12 mm apart), so Kp is larger than on the 6-sensor board.
# (starting values - tune them on your course: Kp first, then Kd)
LEVELS = {
    1: (30, 0.025, 0.35),     # slow
    2: (45, 0.032, 0.50),     # medium
    3: (60, 0.040, 0.65),     # fast
}
level = 1


def run_course(base, kp, kd):
    s.ambient_cancel = True
    last_err = 0
    d_f = 0.0
    lost_since = None
    t_prev = time.ticks_us()
    robot.led.value(0)
    robot.wait_release()
    while not robot.start_pressed():
        pos = s.position()
        now = time.ticks_us()
        dt = max(1, time.ticks_diff(now, t_prev)) / 1000.0   # ms
        t_prev = now
        if pos is None:
            # line lost: turn hard to the side where it was last seen
            if lost_since is None:
                lost_since = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), lost_since) > 800:
                break                       # gave up (off the course)
            turn = 60 if s.last_pos > 0 else -60
            m.run(base * 0.3 + turn, base * 0.3 - turn)
            continue
        lost_since = None
        err = pos                           # -1000 .. +1000  (+ = line is right)
        d = (err - last_err) / dt           # change per millisecond
        d_f += (d - d_f) * 0.3              # smooth it: with 3 sensors the position moves in steps
        last_err = err
        steer = kp * err + kd * d_f
        m.run(base + steer, base - steer)
    m.brake()
    time.sleep_ms(300)
    m.stop()
    robot.led.value(1)


robot.blink(1)
ok, v = robot.battery_ok()
if robot.battery.usb():
    print("USB connected (battery not measured). Motors run only with the battery switch ON.")
else:
    print("battery %.2f V" % v)
if not ok:
    robot.blink(5, 60)                      # low battery
robot.led.value(1)                          # ready

while True:
    kind = robot.wait_press()
    if kind == "long":
        level = level % len(LEVELS) + 1
        print("level", level)
        time.sleep_ms(300)
        robot.led.value(0)
        time.sleep_ms(300)
        robot.blink(level, 200)
        robot.led.value(1)
        continue
    if not s.calibrated():
        robot.led.value(0)
        ok = robot.auto_calibrate()
        print("calibrated" if ok else "calibration failed", s.lo, s.hi)
        if not ok:
            robot.blink(4, 300)
        robot.led.value(1)
        continue
    robot.blink(3, 80)                      # ready...
    base, kp, kd = LEVELS[level]
    run_course(base, kp, kd)
    robot.wait_release()
