# linetracer.py  -  Linetracer2 library for MicroPython (Raspberry Pi Pico / Pico 2)
#
# Copy this file to the Pico (Thonny: "Upload to /").  Then:
#
#     from linetracer import Robot
#     robot = Robot()
#     robot.motors.run(30, 30)     # left %, right %  (100 % = MAX_MOTOR_VOLT)
#
# Hardware: see docs/03_circuit.md  (pin numbers below must match the PCB)

from machine import Pin, PWM, ADC
import time

# ----------------------------------------------------------------- pins (PCB rev.A)
PIN_BUZZER = 0
PIN_SENS_LED = 1          # 1 = IR LEDs on (through Q1)
PIN_SDA, PIN_SCL = 4, 5   # J2 (I2C0)
PIN_STBY = 11             # TC78H653 STBY
PIN_IN1, PIN_IN2 = 12, 13  # LEFT  motor (PWM slice 6 A/B)
PIN_IN3, PIN_IN4 = 14, 15  # RIGHT motor (PWM slice 7 A/B)
PIN_SW1, PIN_SW2 = 16, 17  # START, SELECT (pressed = 0)
PIN_LED1, PIN_LED2 = 18, 19
PIN_MUX = (20, 21, 22)     # 4051 A, B, C
ADC_SENS = 26              # 4051 common
ADC_VBAT = 27              # battery / 2

# sensor S1 (far left) ... S6 (far right) -> 4051 channel (chosen for PCB routing)
SENSOR_CH = (4, 2, 1, 0, 3, 5)
SENSOR_PITCH_MM = 12

# ----------------------------------------------------------------- settings
MAX_MOTOR_VOLT = 3.0      # FA-130RA-2270 is rated 1.5-3.0 V. 100 % = this voltage
PWM_FREQ = 20000          # 20 kHz (not audible)
RAMP_PER_CALL = 0.04      # max change of duty per run() call (soft start, avoids ISD trip)
LEFT_INVERT = False       # set True if the left wheel turns backwards on run(30, 30)
RIGHT_INVERT = True       # the two motors face opposite directions
VBAT_SCALE = 2.0 * 3.3 / 65535   # R13/R14 = 10k/10k


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Battery:
    """Battery voltage through the 1/2 divider on GP27."""

    def __init__(self):
        self.adc = ADC(Pin(ADC_VBAT))
        self.volt = self.read(16)

    def read(self, n=4):
        s = 0
        for _ in range(n):
            s += self.adc.read_u16()
        self.volt = s / n * VBAT_SCALE
        return self.volt

    def update(self):
        """Low-pass filtered reading (call often while driving; motors make it noisy)."""
        v = self.adc.read_u16() * VBAT_SCALE
        self.volt += (v - self.volt) * 0.2
        return self.volt


class Motor:
    """One DC motor on two inputs of the TC78H653FTG (IN/IN mode).

    duty  > 0 : forward,  duty < 0 : reverse  (-1.0 .. 1.0, fraction of battery voltage)
    brake=True  : OFF-phase = short brake (slow decay, speed follows duty, strong braking)
    brake=False : OFF-phase = coast (fast decay)
    """

    def __init__(self, pin_a, pin_b, invert=False):
        self.a = PWM(Pin(pin_a))
        self.b = PWM(Pin(pin_b))
        self.a.freq(PWM_FREQ)
        self.b.freq(PWM_FREQ)
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

    def __init__(self, battery):
        self.bat = battery
        self.stby = Pin(PIN_STBY, Pin.OUT, value=0)
        self.left = Motor(PIN_IN1, PIN_IN2, LEFT_INVERT)
        self.right = Motor(PIN_IN3, PIN_IN4, RIGHT_INVERT)
        self.max_volt = MAX_MOTOR_VOLT
        self._t_recover = time.ticks_ms()
        self.stby.value(1)

    def recover(self):
        """Over-current protection (ISD) of the driver latches the outputs OFF.
        STBY L -> H clears it.  Called automatically every 100 ms while driving."""
        self.stby.value(0)
        time.sleep_us(5)
        self.stby.value(1)

    def _target(self, pct):
        vb = self.bat.volt if self.bat.volt > 1.0 else 4.5
        return _clamp(pct / 100.0 * self.max_volt / vb, -1.0, 1.0)

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
            self.bat.update()                # keeps the voltage compensation up to date
            if self.left.duty or self.right.duty:
                self.recover()

    def brake(self):
        self.left.set_duty(0)
        self.right.set_duty(0)

    def stop(self):
        self.left.coast()
        self.right.coast()


class LineSensors:
    """6 x LBR-123F through the 4051 multiplexer.

    read_raw()        -> reflection of each sensor (bigger = brighter / whiter)
    calibrate()       -> learn white/black for each sensor (move the sensors over the line!)
    read()            -> 0 (white) .. 1000 (black) for each sensor
    position()        -> -2500 (line under S1, far left) .. 0 (centre) .. +2500 (S6, far right)
    """

    def __init__(self):
        self.sel = [Pin(p, Pin.OUT, value=0) for p in PIN_MUX]
        self.adc = ADC(Pin(ADC_SENS))
        self.led = Pin(PIN_SENS_LED, Pin.OUT, value=0)
        self.ambient_cancel = True
        self.settle_us = 300
        self.lo = [65535] * 6
        self.hi = [0] * 6
        self.last_pos = 0
        self.values = [0] * 6

    def _read_all(self):
        out = []
        for ch in SENSOR_CH:
            self.sel[0].value(ch & 1)
            self.sel[1].value((ch >> 1) & 1)
            self.sel[2].value((ch >> 2) & 1)
            time.sleep_us(8)
            out.append(self.adc.read_u16())
        return out

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
            for i in range(6):
                if r[i] < self.lo[i]:
                    self.lo[i] = r[i]
                if r[i] > self.hi[i]:
                    self.hi[i] = r[i]

    def calibrated(self):
        return all(self.hi[i] - self.lo[i] > 500 for i in range(6))

    def read(self):
        r = self.read_raw()
        v = []
        for i in range(6):
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
        for i in range(6):
            if v[i] > threshold:
                total += v[i]
                acc += v[i] * (i * 1000 - 2500)
        if total < 300:            # line lost: remember which side it went
            self.last_pos = 2500 if self.last_pos > 0 else -2500
            return None
        self.last_pos = acc // total
        return self.last_pos


class Buzzer:
    def __init__(self):
        self.pwm = PWM(Pin(PIN_BUZZER))
        self.pwm.duty_u16(0)

    def tone(self, freq, ms):
        if freq > 0:
            self.pwm.freq(int(freq))
            self.pwm.duty_u16(32768)
        time.sleep_ms(ms)
        self.pwm.duty_u16(0)

    def beep(self, n=1, freq=2000, ms=60):
        for _ in range(n):
            self.tone(freq, ms)
            time.sleep_ms(60)


class Robot:
    def __init__(self):
        self.battery = Battery()
        self.motors = Motors(self.battery)
        self.sensors = LineSensors()
        self.buzzer = Buzzer()
        self.sw1 = Pin(PIN_SW1, Pin.IN, Pin.PULL_UP)
        self.sw2 = Pin(PIN_SW2, Pin.IN, Pin.PULL_UP)
        self.led1 = Pin(PIN_LED1, Pin.OUT, value=0)
        self.led2 = Pin(PIN_LED2, Pin.OUT, value=0)

    # buttons -------------------------------------------------------------
    def start_pressed(self):
        return self.sw1.value() == 0

    def select_pressed(self):
        return self.sw2.value() == 0

    def wait_release(self):
        while self.start_pressed() or self.select_pressed():
            time.sleep_ms(10)
        time.sleep_ms(30)

    # helpers ---------------------------------------------------------------
    def battery_ok(self, low=3.3):
        v = self.battery.read(8)
        return v >= low, v

    def auto_calibrate(self, ms=2400, speed=25):
        """Spin left and right over the line while learning white/black."""
        self.sensors.lo = [65535] * 6
        self.sensors.hi = [0] * 6
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
