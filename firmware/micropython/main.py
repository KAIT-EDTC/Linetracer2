# main.py  -  Linetracer2 standard program (PD line following)
#
#   SELECT (SW2) : change speed level 1..3  (LED1 = 1, LED2 = 2, both = 3, + beeps)
#   START  (SW1) : 1st press = auto calibration (robot spins on the line)
#                  2nd press = run.  Press START again to stop.
#
# Put the robot on the line before pressing START.

import time
from linetracer import Robot

robot = Robot()
m, s = robot.motors, robot.sensors

# speed level -> (base speed %, Kp, Kd)   100 % = 3.0 V on the motors
# (starting values - tune them on your course: Kp first, then Kd)
LEVELS = {
    1: (30, 0.012, 0.35),     # slow
    2: (45, 0.016, 0.50),     # medium
    3: (60, 0.020, 0.65),     # fast
}
level = 1


def show_level(lv):
    robot.led1.value(lv & 1)
    robot.led2.value((lv >> 1) & 1)


def run_course(base, kp, kd):
    s.ambient_cancel = True
    last_err = 0
    lost_since = None
    t_prev = time.ticks_us()
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
        err = pos                           # -2500 .. +2500  (+ = line is right)
        d = (err - last_err) / dt           # change per millisecond
        last_err = err
        steer = kp * err + kd * d
        m.run(base + steer, base - steer)
    m.brake()
    time.sleep_ms(300)
    m.stop()


robot.buzzer.beep(1, 1500)
ok, v = robot.battery_ok()
print("battery %.2f V" % v)
if not ok:
    robot.buzzer.beep(5, 800, 120)          # low battery (or USB only)

show_level(level)
while True:
    if robot.select_pressed():
        level = level % len(LEVELS) + 1
        show_level(level)
        robot.buzzer.beep(level, 2500, 40)
        robot.wait_release()
    if robot.start_pressed():
        robot.wait_release()
        if not s.calibrated():
            robot.buzzer.beep(2, 1200)
            ok = robot.auto_calibrate()
            print("calibrated" if ok else "calibration failed", s.lo, s.hi)
            robot.buzzer.beep(1 if ok else 4, 2000 if ok else 600)
            continue
        robot.buzzer.beep(3, 3000, 50)       # ready...
        base, kp, kd = LEVELS[level]
        run_course(base, kp, kd)
        robot.buzzer.beep(1, 1000, 200)
        robot.wait_release()
    time.sleep_ms(20)
