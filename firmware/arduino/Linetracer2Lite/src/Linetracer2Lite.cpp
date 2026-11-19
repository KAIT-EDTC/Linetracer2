// Linetracer2Lite.cpp  -  see Linetracer2Lite.h
#include "Linetracer2Lite.h"

using namespace lt2;

static constexpr uint32_t DUTY_MAX = (1u << PWM_BITS) - 1;

static float clampf(float x, float lo, float hi) { return x < lo ? lo : x > hi ? hi : x; }

// ================================================================ Motor
void Motor::begin() {
  ledcAttach(a_, PWM_FREQ, PWM_BITS);
  ledcAttach(b_, PWM_FREQ, PWM_BITS);
  coast();
}

void Motor::setDuty(float duty) {
  duty = clampf(duty, -1.0f, 1.0f);
  duty_ = duty;
  if (invert) duty = -duty;
  uint32_t d = (uint32_t)(fabsf(duty) * DUTY_MAX + 0.5f);
  if (brake) {
    if (duty > 0) {
      ledcWrite(a_, DUTY_MAX);
      ledcWrite(b_, DUTY_MAX - d);
    } else if (duty < 0) {
      ledcWrite(a_, DUTY_MAX - d);
      ledcWrite(b_, DUTY_MAX);
    } else {
      ledcWrite(a_, DUTY_MAX);  // H/H = short brake
      ledcWrite(b_, DUTY_MAX);
    }
  } else {
    ledcWrite(a_, duty >= 0 ? d : 0);
    ledcWrite(b_, duty >= 0 ? 0 : d);
  }
}

void Motor::coast() {
  duty_ = 0;
  ledcWrite(a_, 0);  // L/L = stop (free running)
  ledcWrite(b_, 0);
}

// ================================================================ Motors
void Motors::begin() {
  pinMode(PIN_STBY, OUTPUT);
  digitalWrite(PIN_STBY, LOW);
  left.begin();
  right.begin();
  tRecover_ = millis();
  digitalWrite(PIN_STBY, HIGH);
}

void Motors::recover() {
  digitalWrite(PIN_STBY, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_STBY, HIGH);
}

float Motors::target(float pct) const { return clampf(pct / 100.0f * maxVolt / batteryVolt, -1.0f, 1.0f); }

void Motors::run(float leftPct, float rightPct, float ramp) {
  Motor* ms[2] = {&left, &right};
  float pcts[2] = {leftPct, rightPct};
  for (int i = 0; i < 2; i++) {
    float t = target(pcts[i]);
    float d = ms[i]->duty();
    t = clampf(t, d - ramp, d + ramp);
    ms[i]->setDuty(t);
  }
  uint32_t now = millis();
  if (now - tRecover_ > 100) {
    tRecover_ = now;
    if (left.duty() != 0 || right.duty() != 0) recover();
  }
}

void Motors::brake() {
  left.setDuty(0);
  right.setDuty(0);
}

void Motors::stop() {
  left.coast();
  right.coast();
}

void Motors::off() {
  stop();
  digitalWrite(PIN_STBY, LOW);
}

// ================================================================ LineSensors
void LineSensors::begin() {
  analogReadResolution(12);
  for (int i = 0; i < N_SENS; i++) analogSetPinAttenuation(ADC_SENS[i], ADC_11db);  // 0 .. about 3.1 V
  pinMode(PIN_SENS_LED, OUTPUT);
  digitalWrite(PIN_SENS_LED, LOW);
  resetCalibration();
}

void LineSensors::leds(bool on) { digitalWrite(PIN_SENS_LED, on ? HIGH : LOW); }

void LineSensors::readRaw(int out[N_SENS]) {
  int on[N_SENS], off[N_SENS];
  leds(true);
  delayMicroseconds(settleUs);
  for (int i = 0; i < N_SENS; i++) on[i] = analogRead(ADC_SENS[i]);
  if (!ambientCancel) {
    for (int i = 0; i < N_SENS; i++) out[i] = 4095 - on[i];
    return;
  }
  leds(false);
  delayMicroseconds(settleUs);
  for (int i = 0; i < N_SENS; i++) off[i] = analogRead(ADC_SENS[i]);
  // more reflected IR -> lower voltage when the LED is on
  for (int i = 0; i < N_SENS; i++) out[i] = max(0, off[i] - on[i]);
}

void LineSensors::readVolts(float out[N_SENS]) {
  for (int i = 0; i < N_SENS; i++) out[i] = analogReadMilliVolts(ADC_SENS[i]) / 1000.0f;
}

void LineSensors::resetCalibration() {
  for (int i = 0; i < N_SENS; i++) {
    lo[i] = 4095;
    hi[i] = 0;
  }
}

void LineSensors::calibrate(int samples) {
  int r[N_SENS];
  for (int k = 0; k < samples; k++) {
    readRaw(r);
    for (int i = 0; i < N_SENS; i++) {
      if (r[i] < lo[i]) lo[i] = r[i];
      if (r[i] > hi[i]) hi[i] = r[i];
    }
  }
}

bool LineSensors::calibrated() const {
  for (int i = 0; i < N_SENS; i++)
    if (hi[i] - lo[i] <= CAL_MIN_SPAN) return false;
  return true;
}

void LineSensors::read(int out[N_SENS]) {
  int r[N_SENS];
  readRaw(r);
  for (int i = 0; i < N_SENS; i++) {
    int span = hi[i] - lo[i];
    int x = span <= 0 ? 0 : (hi[i] - r[i]) * 1000 / span;  // white(hi) -> 0, black(lo) -> 1000
    values[i] = out[i] = constrain(x, 0, 1000);
  }
}

int LineSensors::position(int threshold) {
  int v[N_SENS];
  read(v);
  long total = 0, acc = 0;
  for (int i = 0; i < N_SENS; i++) {
    if (v[i] > threshold) {
      total += v[i];
      acc += (long)v[i] * (i - 1) * 1000;
    }
  }
  if (total < 300) {  // line lost: remember which side it went
    lastPos = lastPos > 0 ? 1000 : -1000;
    return LINE_LOST;
  }
  lastPos = acc / total;
  return lastPos;
}

// ================================================================ Lights
// PL9823 bit timing: 0 = 0.35 us high + 1.36 us low, 1 = 1.36 + 0.35.  RMT at 20 MHz = 0.05 us per tick.
static constexpr uint32_t RMT_HZ = 20000000;
static constexpr uint16_t T_SHORT = 7, T_LONG = 27;
static rmt_data_t rmtBuf[N_RGB * 24];

void Lights::begin() {
  ok_ = rmtInit(PIN_RGB, RMT_TX_MODE, RMT_MEM_NUM_BLOCKS_1, RMT_HZ);
  t_ = millis();
  fill(Colors::OFF);
}

void Lights::set(int i, Color c, float k) {
  if (i < 0 || i >= N_RGB) return;
  k = k * brightness / 255.0f;
  px_[i][0] = c.r * k;  // PL9823 takes red, green, blue
  px_[i][1] = c.g * k;
  px_[i][2] = c.b * k;
}

void Lights::show() {
  if (!ok_) return;
  int n = 0;
  for (int i = 0; i < N_RGB; i++) {
    for (int ch = 0; ch < 3; ch++) {
      for (int bit = 7; bit >= 0; bit--) {
        bool one = px_[i][ch] & (1 << bit);
        rmtBuf[n].level0 = 1;
        rmtBuf[n].duration0 = one ? T_LONG : T_SHORT;
        rmtBuf[n].level1 = 0;
        rmtBuf[n].duration1 = one ? T_SHORT : T_LONG;
        n++;
      }
    }
  }
  rmtWrite(PIN_RGB, rmtBuf, n, 20);
  delayMicroseconds(60);  // > 50 us low = latch
}

void Lights::fill(Color c) {
  for (int i = 0; i < N_RGB; i++) set(i, c);
  show();
}

void Lights::side(Color l, Color r) {
  for (int j = 0; j < 3; j++) {
    set(LEFT_SIDE[j], l);
    set(RIGHT_SIDE[j], r);
  }
  show();
}

void Lights::value(bool on) {
  on_ = on;
  fill(on ? color : Colors::OFF);
}

void Lights::flow(float left, float right, Color c) {
  uint32_t now = millis();
  float dt = min<uint32_t>(now - t_, 200) / 1000.0f;  // seconds
  t_ = now;
  const uint8_t* sides[2] = {LEFT_SIDE, RIGHT_SIDE};
  float sp[2] = {left, right};
  for (int k = 0; k < 2; k++) {
    phase_[k] = fmodf(phase_[k] + FLOW_SPEED * sp[k] / 100 * dt, 3.0f);
    if (phase_[k] < 0) phase_[k] += 3.0f;
    int head = (int)phase_[k] % 3;
    int tail = sp[k] >= 0 ? (head + 2) % 3 : (head + 1) % 3;
    for (int j = 0; j < 3; j++) {
      if (j == head) set(sides[k][j], c);
      else if (j == tail) set(sides[k][j], c, 0.2f);
      else set(sides[k][j], Colors::OFF);
    }
  }
  show();
}

void Lights::count(int n, Color c) {
  for (int j = 0; j < 3; j++) {
    set(LEFT_SIDE[j], j < n ? c : Colors::OFF);
    set(RIGHT_SIDE[j], j < n ? c : Colors::OFF);
  }
  show();
}

void Lights::bar(int pos, Color c) {
  if (pos == LINE_LOST) side(Colors::OFF, Colors::OFF);
  else side(pos < 300 ? c : Colors::OFF, pos > -300 ? c : Colors::OFF);
}

// ================================================================ Robot
void Robot::begin() {
  pinMode(PIN_SW, INPUT_PULLUP);
  pinMode(PIN_LED_XIAO, OUTPUT);
  digitalWrite(PIN_LED_XIAO, HIGH);
  motors.begin();  // first: the motors take LEDC channels 0..3 (2 timers at 20 kHz), the buzzer gets the next one
  sensors.begin();
  led.begin();
}

bool Robot::startPressed() const { return digitalRead(PIN_SW) == LOW; }

void Robot::waitRelease() {
  while (startPressed()) delay(10);
  delay(30);
}

Press Robot::waitPress() {
  while (!startPressed()) delay(10);
  uint32_t t0 = millis();
  bool was = led.value();
  Press kind = Press::SHORT;
  while (startPressed()) {
    if (kind == Press::SHORT && millis() - t0 >= LONG_PRESS_MS) {
      kind = Press::LONG;
      led.value(false);
      ledXiao(true);
      beep(2000, 30);  // "click": you can let go now
    }
    delay(10);
  }
  ledXiao(false);
  led.value(was);
  delay(30);
  return kind;
}

void Robot::ledXiao(bool on) { digitalWrite(PIN_LED_XIAO, on ? LOW : HIGH); }

void Robot::blink(int n, uint32_t ms) {
  bool was = led.value();
  for (int i = 0; i < n; i++) {
    led.value(true);
    delay(ms);
    led.value(false);
    delay(ms);
  }
  led.value(was);
}

void Robot::beep(uint32_t freq, uint32_t ms, float vol) {
  float v = vol < 0 ? volume : vol;
  if (freq > 0 && v > 0) {
    // 10 bit up to ~78 kHz with the 80 MHz clock, plenty for a buzzer
    if (ledcAttach(PIN_SW, freq, 10)) {
      ledcWrite(PIN_SW, (uint32_t)(512 * min(1.0f, v)));
      delay(ms);
      ledcDetach(PIN_SW);
    }
    pinMode(PIN_SW, OUTPUT);  // charge the piezo at once (the pull-up alone takes ~1 ms) ...
    digitalWrite(PIN_SW, HIGH);
    delayMicroseconds(100);
    pinMode(PIN_SW, INPUT_PULLUP);  // ... and back to a button input
  } else if (freq > 0) {            // quiet mode: a flash of the LEDs instead of the sound
    bool was = led.value();
    led.value(true);
    delay(ms);
    led.value(was);
  } else {  // a rest
    delay(ms);
  }
}

void Robot::melody(const Note* notes, size_t n, uint32_t gapMs) {
  for (size_t i = 0; i < n; i++) {
    beep(notes[i].freq, notes[i].ms);
    delay(gapMs);
  }
}

bool Robot::autoCalibrate(uint32_t ms, float speed) {
  sensors.resetCalibration();
  uint32_t t0 = millis();
  for (uint32_t t; (t = millis() - t0) <= ms;) {
    int phase = t * 4 / ms;  // left, right, right, left
    float s = (phase == 0 || phase == 3) ? speed : -speed;
    motors.run(-s, s);
    sensors.calibrate();
  }
  motors.brake();
  delay(200);
  motors.stop();
  return sensors.calibrated();
}

// ================================================================ LineFollower
void LineFollower::start(float base, float kp, float kd) {
  base_ = base;
  kp_ = kp;
  kd_ = kd;
  robot_.sensors.ambientCancel = true;
  lastErr_ = 0;
  dF_ = 0;
  lost_ = false;
  n_ = 0;
  left = right = base;
  tPrev_ = micros();
  running_ = true;
}

bool LineFollower::update() {
  if (!running_) return false;
  LineSensors& s = robot_.sensors;
  pos = s.position();
  if (++n_ % 10 == 0)  // running lights (not every time: a frame takes ~0.2 ms)
    robot_.led.flow(left, right, pos != LINE_LOST ? Colors::CYAN : Colors::RED);
  uint32_t now = micros();
  float dt = max<uint32_t>(1, now - tPrev_) / 1000.0f;  // ms
  tPrev_ = now;
  if (pos == LINE_LOST) {
    // line lost: turn hard to the side where it was last seen
    if (!lost_) {
      lost_ = true;
      lostSince_ = millis();
    }
    if (millis() - lostSince_ > lostTimeoutMs) {  // gave up (off the course)
      stop();
      return false;
    }
    float turn = s.lastPos > 0 ? 60 : -60;
    left = base_ * 0.3f + turn;
    right = base_ * 0.3f - turn;
    robot_.motors.run(left, right);
    return true;
  }
  lost_ = false;
  int err = pos;                         // -1000 .. +1000  (+ = line is right)
  float d = (err - lastErr_) / dt;       // change per millisecond
  dF_ += (d - dF_) * 0.3f;               // smooth it: with 3 sensors the position moves in steps
  lastErr_ = err;
  float steer = kp_ * err + kd_ * dF_;
  left = base_ + steer;
  right = base_ - steer;
  robot_.motors.run(left, right);
  return true;
}

void LineFollower::stop() {
  running_ = false;
  robot_.motors.brake();
  delay(300);
  robot_.motors.stop();
}
