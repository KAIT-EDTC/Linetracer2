// Linetracer2Lite.h  -  Linetracer2 Lite library for Arduino (Seeed Studio XIAO ESP32C6)
//
// For the Lite board rev.L3: XIAO ESP32C6 (on pin headers), 3 x LBR-127HLD, 1 button + a buzzer on the same pin,
// 6 full-colour LEDs (PL9823, NeoPixel type, 3 down each side of the board) on one data pin.
// C++ port of lite/firmware/micropython/linetracer.py (same pins, same behaviour, same settings).
//
// Arduino IDE: board "XIAO_ESP32C6" (esp32 by Espressif Systems, core 3.x), Tools > USB CDC On Boot: Enabled.
//
//     #include <Linetracer2Lite.h>
//     Robot robot;
//     void setup() { robot.begin(); }
//     void loop()  { robot.motors.run(30, 30); }     // left %, right %  (100 % = maxVolt)
//
// Hardware: see lite/README.md  (pin numbers below must match the PCB)
#pragma once

#include <Arduino.h>

#if !ARDUINO_USB_CDC_ON_BOOT
// Without it Serial is the UART on D6 (TX) = the data line of the full-colour LEDs.
#error "Tools > USB CDC On Boot: Enabled  (arduino-cli: --fqbn esp32:esp32:XIAO_ESP32C6:CDCOnBoot=cdc)"
#endif

namespace lt2 {

// ----------------------------------------------------------------- pins (PCB rev.L3)
// GPIO numbers of the ESP32-C6 (XIAO pin names in the comments).
constexpr uint8_t PIN_SENS_LED = 21;           // D3   HIGH = IR LEDs on (through Q1)
constexpr uint8_t PIN_STBY = 17;               // D7 (RX)  TC78H653 STBY
constexpr uint8_t PIN_IN1 = 19, PIN_IN2 = 23;  // D8, D5   LEFT  motor
constexpr uint8_t PIN_IN3 = 20, PIN_IN4 = 18;  // D9, D10  RIGHT motor
constexpr uint8_t PIN_SW = 22;                 // D4   START (pressed = LOW) + buzzer: the button hangs on R10 1k, the
                                               //      piezo on R9 100R.  To beep, D4 is a PWM output for a moment.
constexpr uint8_t PIN_RGB = 16;                // D6 (TX)  data of the 6 full-colour LEDs
constexpr uint8_t PIN_LED_XIAO = 15;           // yellow user LED on the XIAO itself (LOW = on)
constexpr uint8_t ADC_SENS[3] = {2, 1, 0};     // S1 (left), S2 (centre), S3 (right) -> D2, D1, D0 (the only ADC pins)

// ----------------------------------------------------------------- settings
constexpr float MAX_MOTOR_VOLT = 3.0f;    // FA-130RA-2270 is rated 1.5-3.0 V. 100 % = this voltage (with BATTERY_VOLT)
constexpr float BATTERY_VOLT = 4.2f;      // the board can NOT measure the battery: AA alkaline x3 while driving ~4.2 V
                                          // (NiMH x3: 3.7).  The robot gets slower as the cells run down.
constexpr uint32_t PWM_FREQ = 20000;      // 20 kHz (not audible)
constexpr uint8_t PWM_BITS = 10;          // 0 .. 1023
constexpr float RAMP_PER_CALL = 0.04f;    // max change of duty per run() call (soft start, avoids ISD trip)
constexpr uint32_t LONG_PRESS_MS = 1500;  // button held this long = "long press"
constexpr uint32_t BEEP_FREQ = 4000;      // the piezo (PKM13EPYH4000) is loudest around 4 kHz
constexpr float BEEP_VOLUME = 0.4f;       // 0 (silent) .. 1 (loudest, 50 % duty)
constexpr int CAL_MIN_SPAN = 250;         // calibration is good if white and black differ by this much (of 4095) on
                                          // every sensor (= 4000 of 65535 in the MicroPython version)
constexpr int N_SENS = 3;
constexpr int N_RGB = 6;
constexpr uint8_t RGB_MAX = 60;           // brightness limit 0..255: 6 x white at 255 = 0.36 A and they get warm
constexpr float FLOW_SPEED = 6.0f;        // running lights: steps per second at 100 % motor speed
// chain order: D2 (left rear) -> D3 -> D4 (left front) -> D5 (right front) -> D6 -> D7 (right rear)
constexpr uint8_t LEFT_SIDE[3] = {2, 1, 0};   // the left LEDs, front -> rear
constexpr uint8_t RIGHT_SIDE[3] = {3, 4, 5};  // the right LEDs, front -> rear
constexpr int LINE_LOST = INT32_MIN;      // position() when no sensor sees the line

}  // namespace lt2

struct Color {
  uint8_t r, g, b;
};

namespace Colors {
constexpr Color OFF{0, 0, 0}, RED{255, 0, 0}, ORANGE{255, 80, 0}, YELLOW{255, 200, 0}, GREEN{0, 255, 0},
    CYAN{0, 220, 255}, BLUE{0, 0, 255}, PURPLE{180, 0, 255}, PINK{255, 60, 150}, WHITE{255, 255, 255};
}

// One DC motor on two inputs of the TC78H653FTG (IN/IN mode).
//   duty > 0 : forward,  duty < 0 : reverse  (-1.0 .. 1.0, fraction of battery voltage)
//   brake = true  : OFF-phase = short brake (slow decay, speed follows duty, strong braking)
//   brake = false : OFF-phase = coast (fast decay)
class Motor {
 public:
  Motor(uint8_t pinA, uint8_t pinB) : a_(pinA), b_(pinB) {}
  void begin();
  void setDuty(float duty);
  void coast();
  float duty() const { return duty_; }
  bool invert = false;  // set true if this wheel turns backwards on run(30, 30)
  bool brake = true;

 private:
  uint8_t a_, b_;
  float duty_ = 0;
};

// Both motors.  run(left, right) takes -100..100 % of maxVolt.
class Motors {
 public:
  Motors() : left(lt2::PIN_IN1, lt2::PIN_IN2), right(lt2::PIN_IN3, lt2::PIN_IN4) {}
  void begin();
  void run(float leftPct, float rightPct, float ramp = lt2::RAMP_PER_CALL);
  void brake();    // short brake (stops quickly)
  void stop();     // coast (free running)
  void off();      // coast + driver in standby
  void recover();  // STBY L -> H clears a latched over-current shutdown (called by run() every 100 ms)
  Motor left, right;
  // true = front and rear swapped (left/right motors swapped and both inverted): use it when run(30, 30) drives
  // the robot backwards although it still turns the right way
  bool reverse = false;
  float maxVolt = lt2::MAX_MOTOR_VOLT;
  float batteryVolt = lt2::BATTERY_VOLT;

 private:
  float target(float pct) const;
  uint32_t tRecover_ = 0;
};

// 3 x LBR-127HLD, each on its own ADC pin.
//   readRaw(v)   -> reflection of each sensor (bigger = brighter / whiter), 0..4095
//   calibrate()  -> learn white/black for each sensor (move the sensors over the line!)
//   read(v)      -> 0 (white) .. 1000 (black) for each sensor
//   position()   -> -1000 (line under S1, left) .. 0 (centre, S2) .. +1000 (S3, right), or lt2::LINE_LOST
class LineSensors {
 public:
  void begin();
  void readRaw(int out[lt2::N_SENS]);
  void readVolts(float out[lt2::N_SENS]);  // the voltage on S1..S3 as it is now (for the test pads)
  void leds(bool on);
  void resetCalibration();
  void calibrate(int samples = 1);
  bool calibrated() const;
  void read(int out[lt2::N_SENS]);
  int position(int threshold = 150);
  bool ambientCancel = true;
  uint32_t settleUs = 300;
  int lo[lt2::N_SENS], hi[lt2::N_SENS];
  int values[lt2::N_SENS] = {0, 0, 0};  // the last read()
  int lastPos = 0;
};

// The 6 full-colour LEDs (PL9823), 3 down each side, sent with the RMT peripheral.
//   robot.led.set(0, Colors::RED);  robot.led.show();   // 0..2 = left rear -> front, 3..5 = right front -> rear
//   robot.led.fill(Colors::BLUE);                       // all of them (shown at once)
//   robot.led.side(Colors::RED, Colors::OFF);           // left side / right side
//   robot.led.flow(30, 30);                             // running lights at the speed of each wheel
class Lights {
 public:
  void begin();
  void set(int i, Color c, float k = 1.0f);
  void show();
  void fill(Color c);
  void side(Color left, Color right);
  void value(bool on);  // like a plain LED: all on in `color`, or all off
  bool value() const { return on_; }
  void flow(float left, float right, Color c = Colors::CYAN);
  void count(int n, Color c = Colors::YELLOW);   // light n LEDs from the front on both sides
  void bar(int pos, Color c = Colors::CYAN);     // where the line is (pos from LineSensors::position)
  uint8_t brightness = lt2::RGB_MAX;
  Color color = Colors::GREEN;  // colour for value(true)

 private:
  uint8_t px_[lt2::N_RGB][3] = {};
  bool on_ = false;
  bool ok_ = false;
  float phase_[2] = {0, 0};
  uint32_t t_ = 0;
};

enum class Press { SHORT, LONG };

class Robot {
 public:
  void begin();
  // button
  bool startPressed() const;
  void waitRelease();
  Press waitPress();  // waits for one press; LONG = held LONG_PRESS_MS or more (the LEDs go out when it becomes long)
  // LEDs
  void ledXiao(bool on);  // the small yellow LED on the XIAO itself
  void blink(int n = 1, uint32_t ms = 120);
  // buzzer (on the button's pin D4: for the length of the tone the pin is a PWM output, the button can't be read)
  void beep(uint32_t freq = lt2::BEEP_FREQ, uint32_t ms = 100, float volume = -1);
  struct Note {
    uint16_t freq, ms;
  };
  void melody(const Note* notes, size_t n, uint32_t gapMs = 20);
  // helpers
  bool autoCalibrate(uint32_t ms = 2400, float speed = 25);  // spin left and right over the line

  Motors motors;
  LineSensors sensors;
  Lights led;
  float volume = lt2::BEEP_VOLUME;  // 0 = quiet mode (the LEDs flash instead of the sound)
};

// PD line following, one step per update() so that a sketch can do other things in between
// (main.py's run_course() as a class).
//   follower.start(45, 0.032, 0.50);
//   while (follower.update()) { ... }      // false = it gave up (line lost for too long)
class LineFollower {
 public:
  explicit LineFollower(Robot& r) : robot_(r) {}
  void start(float base, float kp, float kd);
  bool update();
  void stop();  // brake, then coast
  bool running() const { return running_; }
  float left = 0, right = 0;  // the last motor command (%)
  int pos = 0;                // the last position (or lt2::LINE_LOST)
  uint32_t lostTimeoutMs = 800;

 private:
  Robot& robot_;
  float base_ = 0, kp_ = 0, kd_ = 0;
  int lastErr_ = 0;
  float dF_ = 0;
  uint32_t tPrev_ = 0, lostSince_ = 0, n_ = 0;
  bool lost_ = false, running_ = false;
};
