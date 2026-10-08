# linetracer.py  -  Linetracer2 Lite library for MicroPython (Seeed Studio XIAO ESP32C6)
#
# For the Lite board rev.L3: XIAO ESP32C6 (on pin headers), 3 x LBR-127HLD, 1 button + a buzzer on the same pin,
# 5 full-colour LEDs (PL9823, NeoPixel type) on one data pin.
# MicroPython: the official "ESP32_GENERIC_C6" firmware (micropython.org).
# (The standard rev.A1 board has its own library in firmware/micropython/ at the top of the repo.)
#
# Copy this file to the XIAO (Thonny: "Upload to /").  Then:
#
#     from linetracer import Robot
#     robot = Robot()
#     robot.motors.run(30, 30)     # left %, right %  (100 % = MAX_MOTOR_VOLT)
#
# Hardware: see lite/README.md  (pin numbers below must match the PCB)

from machine import Pin, PWM, ADC
from neopixel import NeoPixel
import time

# ----------------------------------------------------------------- pins (PCB rev.L3)
# GPIO numbers of the ESP32-C6 (XIAO pin names in the comments).
# rev.L3 swapped D3/D4 and D8/D10 against rev.L2 (so that no tracks cross on the board).
PIN_SENS_LED = 21          # D3   1 = IR LEDs on (through Q1)
PIN_STBY = 17              # D7 (RX)  TC78H653 STBY
PIN_IN1, PIN_IN2 = 19, 23  # D8, D5   LEFT  motor
PIN_IN3, PIN_IN4 = 20, 18  # D9, D10  RIGHT motor
PIN_SW = 22                # D4   START (pressed = 0) + buzzer: the button hangs on R10 1k, the piezo on R9 100R.
                           #      The piezo passes no DC, so the button reads normally; to beep, D4 becomes a PWM
                           #      output for a moment (it sounds even while START is held)
PIN_BUZZER = PIN_SW
PIN_RGB = 16               # D6 (TX)  data of the 5 full-colour LEDs (the boot log may light them for a moment)
PIN_LED_XIAO = 15          # yellow user LED on the XIAO itself (0 = on)
ADC_SENS = (2, 1, 0)       # S1 (left), S2 (centre), S3 (right)  -> D2, D1, D0 (the XIAO's only ADC pins)

SENSOR_PITCH_MM = 12

# ----------------------------------------------------------------- settings
MAX_MOTOR_VOLT = 3.0      # FA-130RA-2270 is rated 1.5-3.0 V. 100 % = this voltage (with BATTERY_VOLT)
BATTERY_VOLT = 4.2        # the board can NOT measure the battery (no ADC pin left): AA alkaline x3 while
                          # driving is about 4.2 V.  NiMH x3: set 3.7.  The robot gets slower as the cells run down.
PWM_FREQ = 20000          # 20 kHz (not audible)
RAMP_PER_CALL = 0.04      # max change of duty per run() call (soft start, avoids ISD trip)
LEFT_INVERT = False       # set True if the left wheel turns backwards on run(30, 30)
RIGHT_INVERT = False      # the motors face opposite directions, but M2's + pad is on OUT4 (wired reversed)
LONG_PRESS_MS = 1500      # button held this long = "long press" (children often hold a normal press ~0.8 s)
BEEP_FREQ = 4000          # the piezo (PKM13EPYH4000) is loudest around 4 kHz
BEEP_VOLUME = 0.4         # 0 (silent) .. 1 (loudest, 50 % duty). 4 kHz is where ears are most sensitive
CAL_MIN_SPAN = 4000       # calibration is good if white and black differ by this much (of 65535) on every
                          # sensor.  Check the real numbers with examples/03_sensor_monitor.py
# full-colour LEDs (PL9823): chain order D2 (front left) -> D3 -> D4 (front right) -> D5 (rear right) -> D6 (rear left)
N_RGB = 5
RGB_TIMING = (350, 1360, 1360, 350)   # PL9823 bit timing in ns: 0 = 0.35 us high + 1.36 low, 1 = 1.36 + 0.35
RGB_ORDER = (0, 1, 2)     # PL9823 takes red, green, blue.  If red and green come out swapped, use (1, 0, 2)
RGB_MAX = 60              # brightness limit 0..255: 5 x white at 255 = 0.3 A and they get warm
LEFT_TO_RIGHT = (0, 4, 1, 3, 2)   # the LEDs from left to right on the board (front, rear, front, rear, front)
COLORS = {"off": (0, 0, 0), "red": (255, 0, 0), "orange": (255, 80, 0), "yellow": (255, 200, 0),
          "green": (0, 255, 0), "cyan": (0, 220, 255), "blue": (0, 0, 255), "purple": (180, 0, 255),
          "pink": (255, 60, 150), "white": (255, 255, 255)}


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Motor:
    """One DC motor on two inputs of the TC78H653FTG (IN/IN mode).

    duty  > 0 : forward,  duty < 0 : reverse  (-1.0 .. 1.0, fraction of battery voltage)
    brake=True  : OFF-phase = short brake (slow decay, speed follows duty, strong braking)
    brake=False : OFF-phase = coast (fast decay)
    """

    def __init__(self, pin_a, pin_b, invert=False):
        # (on the ESP32 a new PWM starts at 50 % unless a duty is given)
        self.a = PWM(Pin(pin_a), freq=PWM_FREQ, duty_u16=0)
        self.b = PWM(Pin(pin_b), freq=PWM_FREQ, duty_u16=0)
        self.invert = invert
        self.brake = True
        self.duty = 0.0
        self.coast()

    def set_duty(self, duty):
        duty = _clamp(duty, -1.0, 1.0)
        self.duty = duty
        if self.invert:
            duty = -duty
        d = int(abs(duty) * 65535)
        if self.brake:
            if duty > 0:
                self.a.duty_u16(65535)
                self.b.duty_u16(65535 - d)
            elif duty < 0:
                self.a.duty_u16(65535 - d)
                self.b.duty_u16(65535)
            else:
                self.a.duty_u16(65535)       # H/H = short brake
                self.b.duty_u16(65535)
        else:
            if duty >= 0:
                self.a.duty_u16(d)
                self.b.duty_u16(0)
            else:
                self.a.duty_u16(0)
                self.b.duty_u16(d)

    def coast(self):
        self.duty = 0.0
        self.a.duty_u16(0)                   # L/L = stop (free running)
        self.b.duty_u16(0)


class Motors:
    """Both motors.  run(left, right) takes -100..100 % of MAX_MOTOR_VOLT."""

    def __init__(self):
        self.stby = Pin(PIN_STBY, Pin.OUT, value=0)
        self.left = Motor(PIN_IN1, PIN_IN2, LEFT_INVERT)
        self.right = Motor(PIN_IN3, PIN_IN4, RIGHT_INVERT)
        self.max_volt = MAX_MOTOR_VOLT
        self.battery_volt = BATTERY_VOLT
        self._t_recover = time.ticks_ms()
        self.stby.value(1)

    def recover(self):
        """Over-current protection (ISD) of the driver latches the outputs OFF.
        STBY L -> H clears it.  Called automatically every 100 ms while driving."""
        self.stby.value(0)
        time.sleep_us(5)
        self.stby.value(1)

    def _target(self, pct):
        return _clamp(pct / 100.0 * self.max_volt / self.battery_volt, -1.0, 1.0)

    def run(self, left_pct, right_pct, ramp=RAMP_PER_CALL):
        for m, pct in ((self.left, left_pct), (self.right, right_pct)):
            t = self._target(pct)
            d = m.duty
            if t > d + ramp:
                t = d + ramp
            elif t < d - ramp:
                t = d - ramp
            m.set_duty(t)
        now = time.ticks_ms()
        if time.ticks_diff(now, self._t_recover) > 100:
            self._t_recover = now
            if self.left.duty or self.right.duty:
                self.recover()

    def brake(self):
        self.left.set_duty(0)
        self.right.set_duty(0)

    def stop(self):
        self.left.coast()
        self.right.coast()

    def off(self):
        """Motors off and the driver in standby (use in `finally:` so Ctrl-C in Thonny never leaves them running)."""
        self.stop()
        self.stby.value(0)


class LineSensors:
    """3 x LBR-127HLD, each on its own ADC pin (no multiplexer on the Lite board).

    read_raw()        -> reflection of each sensor (bigger = brighter / whiter)
    calibrate()       -> learn white/black for each sensor (move the sensors over the line!)
    read()            -> 0 (white) .. 1000 (black) for each sensor
    position()        -> -1000 (line under S1, left) .. 0 (centre, S2) .. +1000 (S3, right)
    """

    N = 3

    def __init__(self):
        # 11 dB attenuation: measures 0 .. about 3.1 V (the sensor output swings 0.3 .. 3.3 V)
        self.adc = [ADC(Pin(p), atten=ADC.ATTN_11DB) for p in ADC_SENS]
        self.led = Pin(PIN_SENS_LED, Pin.OUT, value=0)
        self.ambient_cancel = True
        self.settle_us = 300
        self.lo = [65535] * self.N
        self.hi = [0] * self.N
        self.last_pos = 0
        self.values = [0] * self.N

    def _read_all(self):
        return [a.read_u16() for a in self.adc]

    def read_raw(self):
        self.led.value(1)
        time.sleep_us(self.settle_us)
        on = self._read_all()
        if not self.ambient_cancel:
            return [65535 - v for v in on]
        self.led.value(0)
        time.sleep_us(self.settle_us)
        off = self._read_all()
        # more reflected IR -> lower voltage when the LED is on
        return [max(0, b - a) for a, b in zip(on, off)]

    def leds(self, on):
        self.led.value(1 if on else 0)

    def calibrate(self, samples=1):
        for _ in range(samples):
            r = self.read_raw()
            for i in range(self.N):
                if r[i] < self.lo[i]:
                    self.lo[i] = r[i]
                if r[i] > self.hi[i]:
                    self.hi[i] = r[i]

    def calibrated(self):
        return all(self.hi[i] - self.lo[i] > CAL_MIN_SPAN for i in range(self.N))

    def read(self):
        r = self.read_raw()
        v = []
        for i in range(self.N):
            span = self.hi[i] - self.lo[i]
            if span <= 0:
                x = 0
            else:
                x = (self.hi[i] - r[i]) * 1000 // span   # white(hi) -> 0, black(lo) -> 1000
            v.append(_clamp(x, 0, 1000))
        self.values = v
        return v

    def position(self, threshold=150):
        v = self.read()
        total = 0
        acc = 0
        for i in range(self.N):
            if v[i] > threshold:
                total += v[i]
                acc += v[i] * (i - 1) * 1000
        if total < 300:            # line lost: remember which side it went
            self.last_pos = 1000 if self.last_pos > 0 else -1000
            return None
        self.last_pos = acc // total
        return self.last_pos


class Lights:
    """The 5 full-colour LEDs.  Colours are (red, green, blue) 0..255 or a name from COLORS ("red", "blue", ...).

        robot.led[0] = "red"          # one LED (0 = front left ... 4 = rear left, see LEFT_TO_RIGHT)
        robot.led.show()              # nothing changes until show()
        robot.led.fill("blue")        # all of them (shown at once)
        robot.led.value(1)            # like a plain LED: all on in robot.led.color, value(0) = all off
        robot.led.brightness = 30     # 0..255 (limit, default RGB_MAX)
    """

    def __init__(self, pin=PIN_RGB, n=N_RGB):
        self.n = n
        self.np = NeoPixel(Pin(pin, Pin.OUT), n, timing=RGB_TIMING)
        self.np.ORDER = RGB_ORDER + (3,)
        self.brightness = RGB_MAX
        self.color = "green"          # colour for value(1)
        self._on = 0
        self.fill("off")

    def _rgb(self, c):
        c = COLORS[c] if isinstance(c, str) else c
        k = _clamp(self.brightness, 0, 255) / 255
        return (int(c[0] * k), int(c[1] * k), int(c[2] * k))

    def __setitem__(self, i, c):
        self.np[i] = self._rgb(c)

    def show(self):
        self.np.write()

    def fill(self, c):
        self.np.fill(self._rgb(c))
        self.np.write()

    def value(self, v=None):
        if v is None:
            return self._on
        self._on = 1 if v else 0
        self.fill(self.color if v else "off")

    def bar(self, pos, c="cyan"):
        """Show a line position -1000 (left) .. +1000 (right) on the LED that sits there (None = all off)."""
        self.np.fill((0, 0, 0))
        if pos is not None:
            k = _clamp((pos + 1000) * self.n // 2001, 0, self.n - 1)
            self.np[LEFT_TO_RIGHT[k]] = self._rgb(c)
        self.np.write()

    def count(self, n, c="yellow"):
        """Light n LEDs from the left (e.g. the speed level)."""
        self.np.fill((0, 0, 0))
        for k in range(min(n, self.n)):
            self.np[LEFT_TO_RIGHT[k]] = self._rgb(c)
        self.np.write()


class Robot:
    def __init__(self):
        self.motors = Motors()
        self.sensors = LineSensors()
        self.sw = Pin(PIN_SW, Pin.IN, Pin.PULL_UP)
        self.led = Lights()
        self._led_xiao = Pin(PIN_LED_XIAO, Pin.OUT, value=1)   # yellow LED on the XIAO (free 2nd LED, 0 = on)
        self.volume = BEEP_VOLUME                                  # 0 = quiet mode (no sound at all)

    def led_xiao(self, on):
        """The small yellow LED on the XIAO itself (it lights when the pin is 0)."""
        self._led_xiao.value(0 if on else 1)

    # button ----------------------------------------------------------------
    def start_pressed(self):
        return self.sw.value() == 0

    def wait_release(self):
        while self.start_pressed():
            time.sleep_ms(10)
        time.sleep_ms(30)

    def wait_press(self):
        """Wait for one press.  Returns 'short' or 'long' (held LONG_PRESS_MS or more).
        When the press becomes 'long' the LEDs go out (and the XIAO's yellow LED lights),
        so you know when to let go."""
        while not self.start_pressed():
            time.sleep_ms(10)
        t0 = time.ticks_ms()
        was = self.led.value()
        kind = "short"
        while self.start_pressed():
            if kind == "short" and time.ticks_diff(time.ticks_ms(), t0) >= LONG_PRESS_MS:
                kind = "long"
                self.led.value(0)
                self.led_xiao(True)
                self.beep(2000, 30)                # "click": you can let go now
                self.led.value(0)
            time.sleep_ms(10)
        self.led_xiao(False)
        self.led.value(was)
        time.sleep_ms(30)
        return kind

    # LED --------------------------------------------------------------------
    def blink(self, n=1, ms=120):
        """Blink the LEDs n times (robot.led.color), then leave them as they were."""
        was = self.led.value()
        for _ in range(n):
            self.led.value(1)
            time.sleep_ms(ms)
            self.led.value(0)
            time.sleep_ms(ms)
        self.led.value(was)

    # buzzer (on the button's pin D4: for the length of the tone the pin is a PWM output) --------------------
    def beep(self, freq=BEEP_FREQ, ms=100, volume=None):
        """Sound the buzzer.  freq in Hz (0 = a rest), ms = length, volume 0..1 (default robot.volume).
        The button can not be read while it sounds.  With volume 0 (quiet mode) the LEDs flash instead."""
        v = self.volume if volume is None else volume
        if freq > 0 and v > 0:
            pwm = PWM(self.sw, freq=int(freq), duty_u16=int(32768 * min(1.0, v)))
            time.sleep_ms(ms)
            pwm.deinit()
            self.sw.init(Pin.OUT, value=1)        # charge the piezo at once (the pull-up alone takes ~1 ms) ...
            time.sleep_us(100)
            self.sw.init(Pin.IN, Pin.PULL_UP)     # ... and back to a button input
        elif freq > 0:                            # quiet mode: a flash of the LED instead of the sound
            was = self.led.value()
            self.led.value(1)
            time.sleep_ms(ms)
            self.led.value(was)
        else:                                     # a rest
            time.sleep_ms(ms)

    def melody(self, notes, gap_ms=20):
        """Play [(freq, ms), ...]  e.g.  robot.melody([(1047, 150), (1319, 150), (1568, 300)])"""
        for freq, ms in notes:
            self.beep(freq, ms)
            time.sleep_ms(gap_ms)

    # helpers ---------------------------------------------------------------
    def auto_calibrate(self, ms=2400, speed=25):
        """Spin left and right over the line while learning white/black."""
        n = LineSensors.N
        self.sensors.lo = [65535] * n
        self.sensors.hi = [0] * n
        t0 = time.ticks_ms()
        while True:
            t = time.ticks_diff(time.ticks_ms(), t0)
            if t > ms:
                break
            phase = (t * 4) // ms          # left, right, right, left
            s = speed if phase in (0, 3) else -speed
            self.motors.run(-s, s)
            self.sensors.calibrate()
        self.motors.brake()
        time.sleep_ms(200)
        self.motors.stop()
        return self.sensors.calibrated()
