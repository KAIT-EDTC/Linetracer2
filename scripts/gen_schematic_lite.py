#!/usr/bin/env python3
"""Generate hardware/kicad/Linetracer2-Lite.kicad_sch (Lite board rev.L4, single A3 sheet).

    cd scripts && python3 gen_schematic_lite.py

Differences from the former standard board rev.A1 (removed; see the git history):
  * Seeed Studio XIAO ESP32C6 on two 1x7 pin headers (footprint Linetracer2:XIAO_ESP32C6_Header);
    powered through its 5V pin (= USB VBUS) from a buck-boost module (rev.L4, see below)
  * 3 x LBR-127HLD sensors straight into the XIAO's three ADC pins (no 4051 multiplexer)
  * no battery measurement (the XIAO has only 3 ADC pins; all of them are used by the sensors)
  * 1 button, a passive piezo buzzer sharing the button's pin (D4), 6 full-colour LEDs (PL9823, one data line
    on D6 through R11 1k), test pads for a multimeter, no power LED, no expansion header

rev.L4 (power): the XIAO reset whenever the motors pulled hard (start, stall, 100 %): 3 x AA under 2-3 A of motor
current sag to 2.5-3.3 V, but the XIAO needs about 4 V on its 5V pin (its own Schottky + buck regulator).  Now
VBAT -> D1 -> AE-TPS63802 buck-boost (keeps running down to 1.3 V in) -> 5.13 V -> D8 -> VSYS (XIAO 5V pin,
right LED column); D8 keeps the module from feeding the PC's USB port and USB from feeding the module.
The 470 uF that sat on VSYS (= USB VBUS) is gone (USB allows 10 uF there).  The left LED column (D2 = the first
LED) runs from VSYS through D9 (1N4148, -0.7 V), so its 3.3 V data input is a valid "1" (PL9823: 0.7 x VDD).
"""
import os
import sys

from kicad_env import KDIR, PROJ
from schlib import Sch


R_FP = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
C_FP = "Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm"
CP_FP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
RGB_FP = "Linetracer2:LED_PL9823_5mm"

s = Sch("Linetracer2 Lite rev.L4 - XIAO ESP32C6 kids line tracer")

# Akizuki (akizukidenshi.com) 通販コード for parts that are placed many times (checked 2026-10-05)
AKIZUKI = {
    "100": "125101 (100pcs)", "1k": "125102 (100pcs)", "10k": "125103 (100pcs)",
    "470uF 16V": "108426 (Rubycon 16WXA470MEFC 8x9)",
    "0.1uF (at motor)": "113582 (10pcs)",
    "0.1uF": "113582 (10pcs)",
    "PL9823": "108411 (PL9823-F5)",
    "1N5819": "117244 (10pcs)",
    "TP": "",
}
_place = s.place


def _place_with_code(lib_id, ref, value, *args, **kw):
    fields = dict(kw.pop("fields", None) or {})
    if "Akizuki" not in fields and value in AKIZUKI:
        fields["Akizuki"] = AKIZUKI[value]
    return _place(lib_id, ref, value, *args, fields=fields or None, **kw)


s.place = _place_with_code

# ----------------------------------------------------------------- headings
s.text("Linetracer2 Lite rev.L4  :  XIAO ESP32C6 on pin headers, 3 x LBR-127HLD, 1 button, 1 buzzer, 6 RGB LEDs, 5 V buck-boost", 20.32, 17.78, 3, True)
s.text("Power: AA x3 (alkaline 4.5V / NiMH 3.6V) -> VBAT (motors) ; VBAT -> D1 -> buck-boost 5.13 V -> D8 -> VSYS -> XIAO 5V pin. "
       "The XIAO no longer resets when the motors pull the cells down. Never use 4 cells (the module takes 5.5 V max).", 20.32, 24.13, 1.5)

# ================================================================= POWER block
s.rect(17.78, 30.48, 264.16, 99.06)
s.text("1. POWER", 20.32, 35.56, 2, True)

j1 = s.place("Connector_Generic:Conn_01x02", "J1", "BATTERY (AA x3, XH 2P)", 30.48, 48.26, 90,
             footprint="Linetracer2:BatteryXH_2P",
             fields={"Akizuki": "112247 (B2B-XH-A) / battery box 112243", "Note": "red wire = + (pin 1)"},
             ref_off=(-2.54, -6.35), val_off=(-7.62, -3.81))
s.pwr(j1, "2", "GND")
xj, yj, _ = j1.pin("1")
s.path((xj, yj), (xj, yj + 10.16), (xj + 7.62, yj + 10.16))
s.label("VBAT", xj + 7.62, yj + 10.16, "right")
s.text("Insert the plug first and solder the header so that the RED wire is on '+'", 20.32, 69.85, 1.27)

s.power("PWR_FLAG", 50.8, 43.18, "up")     # right of J1's value text
s.wire(50.8, 43.18, 50.8, 45.72)
s.label("VBAT", 50.8, 45.72, "down")

c1 = s.place("Device:C_Polarized", "C1", "470uF 16V", 55.88, 55.88, 0, footprint=CP_FP,
             fields={"Note": "motor bulk capacitor, place near U2 VM"})
s.lab(c1, "1", "VBAT")
s.pwr(c1, "2", "GND")

d1 = s.place("Device:D_Schottky", "D1", "1N5819", 73.66, 45.72, 180,
             footprint="Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal",
             fields={"Note": "reverse battery: protects U3 and the XIAO"},
             ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
s.lab(d1, "2", "VBAT")      # A
# D1 K -> U3 VIN with EN tied to it (EN must not float: always on); one VIN_BB label names the net for the PCB
u3 = s.place("Linetracer2:AE-TPS63802", "U3", "AE-TPS63802", 104.14, 48.26, 0,
             footprint="Linetracer2:AE-TPS63802",
             fields={"Akizuki": "115557 (AE-TPS63802 kit) + 470k 125474 for VR1",
                     "Note": "VR1 = 470k resistor (5.13 V), lying flat; header 4P from the kit"},
             ref_off=(0, -10.16), val_off=(0, -7.62))
xk, yk, _ = d1.pin("1")
xv, yv, _ = u3.pin("1")
xe, ye, _ = u3.pin("4")
s.wire(xk, yk, xv, yv)
s.path((xe, ye), (xe - 5.08, ye), (xe - 5.08, yv))
s.junction(xe - 5.08, yv)
s.label("VIN_BB", xk + 2.54, yk, "right")
s.power("PWR_FLAG", 83.82, 43.18, "up")
s.wire(83.82, 43.18, 83.82, yk)
s.junction(83.82, yk)
s.pwr(u3, "2", "GND")

# U3 VOUT -> D8 A (one VOUT_BB label), D8 K -> VSYS
d8 = s.place("Device:D_Schottky", "D8", "1N5819", 132.08, 45.72, 180,
             footprint="Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal",
             fields={"Note": "OR diode: U3 can not feed the PC's USB port, USB 5 V can not feed U3"},
             ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
xo, yo, _ = u3.pin("3")
xa, ya, _ = d8.pin("2")
s.wire(xo, yo, xa, ya)
s.label("VOUT_BB", xo + 2.54, yo, "right")
xk8, yk8, _ = d8.pin("1")    # K -> VSYS, with its PWR_FLAG on the same wire
s.wire(xk8, yk8, 147.32, yk8)
s.label("VSYS", 147.32, yk8, "right")
s.power("PWR_FLAG", 142.24, 43.18, "up")
s.wire(142.24, 43.18, 142.24, yk8)
s.junction(142.24, yk8)

# D9: supply of the left LED column (D2..D4), 0.7 V below VSYS: the first LED then reads the XIAO's 3.3 V data
d9 = s.place("Device:D", "D9", "1N4148", 182.88, 45.72, 180,
             footprint="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
             fields={"Akizuki": "1N4148 (check the code)", "Note": "level shift: the first LED runs 0.7 V lower"},
             ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
s.lab(d9, "2", "VSYS")      # A
s.lab(d9, "1", "VLED_L")    # K
s.power("PWR_FLAG", 198.12, 43.18, "up")
s.wire(198.12, 43.18, 198.12, 45.72)
s.label("VLED_L", 198.12, 45.72, "down")
s.text("D9: VLED_L = VSYS - 0.7 V = about 4.1 V for the left LEDs D2-D4.", 167.64, 55.88, 1.27)
s.text("A PL9823 reads '1' above 0.7 x VDD: 2.9 V there, so the XIAO's 3.3 V", 167.64, 59.69, 1.27)
s.text("data is enough.  D2-D4 pass the data on at 4.1 V, enough for D5-D7.", 167.64, 63.5, 1.27)

# GND: nothing on this board is a power output for GND (the XIAO's GND pin is a power input)
s.power("PWR_FLAG", 228.6, 43.18, "up")
s.wire(228.6, 43.18, 228.6, 45.72)
s.power("GND", 228.6, 45.72, "down")

s.text("Why rev.L4: 2 motors starting / stalled pull 2-4 A and the AA cells sag to 2.5-3.3 V; the XIAO needs about 4 V on its "
       "5V pin and reset.", 20.32, 73.66, 1.27)
s.text("U3 makes 5.13 V from 1.3-5.5 V (start 1.8 V).  VSYS = about 4.8 V (USB: 5 V).  No bulk capacitor on VSYS: it is USB "
       "VBUS (max 10 uF).", 20.32, 77.47, 1.27)
s.text("U3 kit: solder a 470k resistor (flat) in place of VR1 BEFORE power-up.  Battery voltage is NOT measured (3 ADC pins, "
       "all used by the sensors).", 20.32, 81.28, 1.27)

# ---- mechanical (mounting holes, kept in the schematic for PCB parity)
s.text("MECHANICAL: H1-H4 = gearbox frame M3 (x30/x70, y62/y96), H5 = front ball caster / skid, snap-in (x50, y11: behind the centre sensor)",
       20.32, 85.09, 1.27)
for i in range(5):
    s.place("Mechanical:MountingHole", "H%d" % (i + 1), "M3" if i < 4 else "SKID M3", 27.94 + i * 22.86, 91.44, 0,
            footprint="MountingHole:MountingHole_3.2mm_M3", in_bom=False,
            ref_off=(2.54, -1.27), val_off=(2.54, 1.27))

# ================================================================= MCU block
s.rect(119.38, 101.6, 264.16, 193.04)
s.text("2. MCU  Seeed Studio XIAO ESP32C6  (on two 1x7 pin headers)", 121.92, 106.68, 2, True)
u1 = s.place("Linetracer2:XIAO_ESP32C6", "U1", "XIAO ESP32C6", 190.5, 144.78, 0,
             footprint="Linetracer2:XIAO_ESP32C6_Header",
             fields={"Akizuki": "129481 (Seeed Studio XIAO ESP32C6) + pin header 1x40 100167 (2 x 7 pins)",
                     "Note": "solder the XIAO on two 1x7 pin headers (cut from a 1x40 strip), then into the board"},
             ref_off=(-20.32, -19.05), val_off=(-20.32, -16.51))
# D0..D2 are the only ADC pins: sensors, in the order that keeps the three lines from crossing on the board.
# IN1..IN4 + button on GPIO18..23: weak pull-up only while the chip is held in reset, then floating.
# STBY on RX (GPIO17): floating during reset (-> the driver's 150k pull-down = standby), pulled up after reset
# when IN1..IN4 already float low (= coast).  Either way the motors can not start before the program runs.
# TX / RX carry the boot log and the UART REPL: only outputs there (RGB LED data, STBY), never the button.
# The XIAO's rear row (D7..D10) feeds only the motor driver behind it; everything else leaves from the front row.
# rev.L3: D3/D4 and D8/D10 swapped against rev.L2 so that no two tracks cross on the top side (see layout_lite.py).
# D4 (SW1) also drives the buzzer (through R9; the button hangs on R10).  D6 = data of the 6 RGB LEDs.
pins = {"1": "SENS3", "2": "SENS2", "3": "SENS1", "4": "SENS_LED_EN", "5": "SW1", "6": "MOT_IN2",
        "7": "RGB_DIN", "8": "MOT_STBY", "9": "MOT_IN1", "10": "MOT_IN3", "11": "MOT_IN4"}
for num, net in pins.items():
    s.lab(u1, num, net)
s.pwr(u1, "12", "+3V3")
s.pwr(u1, "13", "GND")
s.lab(u1, "14", "VSYS")
s.text("GPIO15 = yellow user LED on the XIAO (on = 0), a 2nd indicator for free.  "
       "BOOT / RESET buttons are on the XIAO.", 121.92, 171.45, 1.27)
s.text("Reset state (ESP32-C6 datasheet): GPIO18-23 weak pull-up during reset, then floating;", 121.92, 175.26, 1.27)
s.text("GPIO16 (TX) / GPIO17 (RX) pull-up after reset + boot log / UART REPL -> no button and no motor input there.",
       121.92, 179.07, 1.27)
s.text("On pin headers the XIAO sits 2.5 mm above the board: its bare bottom test pads can not touch the tracks.",
       121.92, 182.88, 1.27)
s.text("Never solder a Li-ion cell to the XIAO's BAT pads on this robot (the AA cells feed the 5V pin through U3).",
       121.92, 186.69, 1.27)

# ================================================================= MOTOR block
s.rect(269.24, 30.48, 406.4, 99.06)
s.text("3. MOTOR DRIVER  (Akizuki AE-TC78H653FTG module, DIP16)", 271.78, 35.56, 2, True)
u2 = s.place("Linetracer2:AE-TC78H653FTG", "U2", "AE-TC78H653FTG", 304.8, 60.96, 0,
             fields={"Akizuki": "114746", "Note": "uses the two 1x8 pin headers that come with the module"},
             ref_off=(-5.08, -13.97), val_off=(-7.62, 13.97))
# LARGE = L : small mode (2 motors, 2A/ch), MODE = L : IN/IN control.  One GND symbol for both pins: a second one
# on pin 2 would put its "GND" on top of the MOT_STBY label below it.
x1, y1, d = s.stub_end(u2, "1")
x2, y2, _ = s.stub_end(u2, "2")
s.wire(x1, y1, x2, y2)
s.junction(x1, y1)
s.power("GND", x1, y1, d)
s.lab(u2, "3", "MOT_STBY")
s.lab(u2, "4", "MOT_IN4")
s.lab(u2, "5", "MOT_IN3")
s.lab(u2, "6", "MOT_IN1")
s.lab(u2, "7", "MOT_IN2")
s.pwr(u2, "8", "GND")
s.lab(u2, "16", "VBAT")
s.lab(u2, "15", "VBAT")
s.lab(u2, "14", "MOT_OUT4")
s.lab(u2, "13", "MOT_OUT3")
s.lab(u2, "12", "MOT_OUT1")
s.lab(u2, "11", "MOT_OUT2")
s.pwr(u2, "10", "GND")
s.pwr(u2, "9", "GND")

# motors drawn horizontally: pin 1 (+) left, pin 2 (-) right
# M2: + on OUT4 (the driver's OUT3/OUT4 pins come out in the opposite order to M2's pads on the board;
# swapping them here keeps the motor tracks from crossing.  linetracer.py: RIGHT_INVERT = False)
for ref, val, cref, ya, yb, yc in (("M1", "LEFT motor  FA-130RA", "C3", 1, 2, 44.45),
                                   ("M2", "RIGHT motor FA-130RA", "C4", 4, 3, 69.85)):
    m = s.place("Motor:Motor_DC", ref, val, 375.92, yc, 90,
                footprint="Linetracer2:MotorPads_2P_Relief", fields={"Akizuki": "106437"},
                ref_off=(-3.81, -6.35), val_off=(1.27, -6.35))
    s.lab(m, "1", "MOT_OUT%d" % ya)
    s.lab(m, "2", "MOT_OUT%d" % yb)
    c = s.place("Device:C", cref, "0.1uF (at motor)", 375.92, yc + 10.16, 90, footprint=C_FP,
                ref_off=(-3.81, -3.81), val_off=(1.27, -3.81))
    s.lab(c, "1", "MOT_OUT%d" % ya)
    s.lab(c, "2", "MOT_OUT%d" % yb)
s.text("LARGE=L : small mode (2 motors, 2A/ch)    MODE=L : IN/IN control", 271.78, 85.09, 1.27)
s.text("IN1/IN2 -> OUT1/OUT2 = LEFT motor,   IN3/IN4 -> OUT3/OUT4 = RIGHT motor (+ = OUT4)", 271.78, 88.9, 1.27)
s.text("H/L fwd, L/H rev, H/H brake, L/L coast.  Over-current (ISD) latches OFF:", 271.78, 92.71, 1.27)
s.text("toggle STBY L->H to recover (done by the library).", 271.78, 96.52, 1.27)

# ================================================================= UI block
s.rect(269.24, 101.6, 406.4, 190.5)
s.text("4. BUTTON / BUZZER / RGB LEDs", 271.78, 106.68, 2, True)
sw1 = s.place("Switch:SW_Push", "SW1", "START", 302.26, 116.84, 0, footprint="Button_Switch_THT:SW_PUSH_6mm",
              fields={"Akizuki": "108075"}, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
r10 = s.place("Device:R", "R10", "1k", 284.48, 116.84, 90, footprint=R_FP,
              ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
s.lab(r10, "1", "SW1")
s.connect(r10, "2", sw1, "1")       # one wire with one BTN label (the PCB routes this net by name)
s.label("BTN", r10.pin("2")[0] + 1.27, r10.pin("2")[1], "right")
s.pwr(sw1, "2", "GND")
s.text("internal pull-up, pressed = 0.  R10: if START is pressed while D4 beeps, only 3.3 mA flows",
       271.78, 124.46, 1.27)
s.text("short press = start / stop, long press = speed level", 271.78, 128.27, 1.27)

# 6 full-colour LEDs in one chain, 3 down each side of the board: D6 -> D2 DIN (left rear), D2 -> D3 -> D4 (left front)
# -> D5 (right front) -> D6 -> D7 (right rear), D7 DO open.  The right column runs from VSYS (about 4.8 V from U3 / D8,
# 5 V on USB: inside the PL9823's 4.5-6 V).  A PL9823 reads "1" above 0.7 x VDD = 3.4-3.5 V there, more than the
# XIAO's 3.3 V: so the left column (with D2, the first LED) runs from VLED_L = VSYS - D9 (1N4148) = about 4.1 V
# (USB 4.3 V) -> 2.9-3.0 V is enough.  D2..D4 pass the data on at their own VDD (4.1 V), enough for D5..D7.
# No 0.1 uF at the LEDs and no bulk capacitor on VSYS (it is USB VBUS).
# R11 1k in the data line: no current flows into DIN in normal use (CMOS input), so it does not change the levels
# above; but a solder bridge from DIN to VDD or GND, or D2 put in backwards, would load D6 far beyond the ESP32-C6's
# 28 mA (sink) / 40 mA (source).  With 1k it is 5 mA at most; the edges slow down by about 1k x 15 pF = 15 ns.
leds = []
for i in range(6):
    d = s.place("Linetracer2:PL9823", "D%d" % (i + 2), "PL9823", 298.45 + 19.05 * i, 146.05, 0, footprint=RGB_FP,
                ref_off=(-5.08, -8.89), val_off=(2.54, 8.89))
    s.lab(d, "3", "VLED_L" if i < 3 else "VSYS")
    s.pwr(d, "1", "GND")
    leds.append(d)
r11 = s.place("Device:R", "R11", "1k", 284.48, 146.05, 90, footprint=R_FP,
              ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
s.lab(r11, "1", "RGB_DIN")
s.connect(r11, "2", leds[0], "4")
for a, b in zip(leds, leds[1:]):
    s.connect(a, "2", b, "4")
s.nc(leds[-1], "2")
s.text("D2..D7 = PL9823 (NeoPixel type, 800 kHz, 24 bit per LED): D2-D4 left side (rear -> front, VDD = VLED_L),",
       271.78, 165.1, 1.27)
s.text("D5-D7 right side (front -> rear, VDD = VSYS).  Data from D6 (TX: the boot log may flash them once) through R11 1k:",
       271.78, 168.91, 1.27)
s.text("5 mA at most if DIN touches VDD or GND, or D2 is in backwards.  6 x white = 0.36 A: the library limits it.",
       292.1, 172.72, 1.27)
r9 = s.place("Device:R", "R9", "100", 287.02, 175.26, 90, footprint=R_FP,
             ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
bz = s.place("Device:Buzzer", "BZ1", "piezo 13mm", 304.8, 177.8, 0,
             footprint="Linetracer2:Buzzer_PKM13_P5.0",
             fields={"Akizuki": "104118 (Murata PKM13EPYH4000-A0)", "Note": "passive piezo, + on the square pad"},
             ref_off=(3.81, -2.54), val_off=(3.81, 2.54))
s.lab(r9, "1", "SW1")
s.connect(r9, "2", bz, "1")
s.pwr(bz, "2", "GND", length=2.54)
# beside the buzzer (below it the frame ends)
s.text("The buzzer shares D4 with the START button (no free XIAO pin).", 327.66, 176.53, 1.27)
s.text("A piezo passes no DC, so reading the button (input + pull-up)", 327.66, 180.34, 1.27)
s.text("works; to beep, D4 becomes a PWM output - it also sounds while", 327.66, 184.15, 1.27)
s.text("START is held.", 327.66, 187.96, 1.27)

# ================================================================= SENSOR block
s.rect(17.78, 195.58, 297.18, 281.94)
s.text("5. LINE SENSORS  3 x LBR-127HLD (mount on the BOTTOM side, lens to the floor), 12 mm apart",
       20.32, 200.66, 2, True)
s.text("IR LED: (3.3V - 1.2V - 0.1V) / 100 ohm = about 20 mA each.  Q1 switches all LEDs (ambient light cancel).  "
       "Photo transistor: 10k pull-up -> white = low voltage, black = high voltage", 20.32, 205.74, 1.27)
s.text("The body is 5.6 mm tall: the front of the robot is lifted by the 7.5 mm ball caster or skid (lens about 2.25 mm above the floor)",
       20.32, 209.55, 1.27)
by = 238.76
for i in range(3):
    bx = 38.1 + i * 60.96
    ps = s.place("Linetracer2:LBR-127HLD", "PS%d" % (i + 1), "LBR-127HLD", bx, by, 0,
                 fields={"Akizuki": "104500"}, ref_off=(-3.81, -6.35), val_off=(-8.89, 7.62))   # value clear of E's GND
    rl = s.place("Device:R", "R%d" % (i + 1), "100", bx - 12.7, by - 12.7, 0, footprint=R_FP,
                 ref_off=(-6.35, -1.27), val_off=(-6.35, 1.27))
    rp = s.place("Device:R", "R%d" % (i + 4), "10k", bx + 12.7, by - 12.7, 0, footprint=R_FP,
                 ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
    s.pwr(rl, "1", "+3V3")
    s.pwr(rp, "1", "+3V3")
    # R_LED -> A
    xa, ya, _ = ps.pin("1")
    xr, yr, _ = rl.pin("2")
    s.path((xr, yr), (xr, ya), (xa, ya))
    # K -> LED_K
    s.lab(ps, "2", "LED_K")
    # C -> SENSn  (+ pull-up)
    xc, yc, _ = ps.pin("4")
    xp, yp, _ = rp.pin("2")
    s.wire(xc, yc, xp, yc)
    s.wire(xp, yp, xp, yc)
    s.wire(xp, yc, xp + 2.54, yc)
    s.junction(xp, yc)
    s.label("SENS%d" % (i + 1), xp + 2.54, yc, "right")
    # E -> GND
    xe, ye, _ = ps.pin("3")
    s.path((xe, ye), (xe + 2.54, ye), (xe + 2.54, ye + 2.54))
    s.power("GND", xe + 2.54, ye + 2.54, "down")
s.text("PS1 = LEFT -> D2 (GPIO2/ADC),  PS2 = CENTRE -> D1 (GPIO1/ADC),  PS3 = RIGHT -> D0 (GPIO0/ADC)  "
       "(seen from above, robot moving up the page)", 20.32, 276.86, 1.27)

# LED switch
q1 = s.place("Transistor_BJT:2SC1815", "Q1", "2SC1815-GR", 274.32, 251.46, 0,
             footprint="Package_TO_SOT_THT:TO-92_Inline_Wide", fields={"Akizuki": "117089"},
             ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
r7 = s.place("Device:R", "R7", "1k", 261.62, 251.46, 90, footprint=R_FP,
             ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
qb = [n for n, v in q1._pins.items() if v[0][3] == "B"][0]
qc = [n for n, v in q1._pins.items() if v[0][3] == "C"][0]
qe = [n for n, v in q1._pins.items() if v[0][3] == "E"][0]
s.connect(r7, "2", q1, qb)
s.lab(r7, "1", "SENS_LED_EN")
s.lab(q1, qc, "LED_K")
s.pwr(q1, qe, "GND")
s.text("Q1: all IR LEDs on when SENS_LED_EN = 1 (about 60 mA)", 200.66, 270.51, 1.27)

# ================================================================= TEST PADS
# above the title block (it starts at y = 253 on A3), so one row of pads and the notes under it
s.rect(299.72, 195.58, 406.4, 248.92)
s.text("6. TEST PADS  (multimeter, black probe on GND)", 302.26, 200.66, 2, True)
TPS = (("TP1", "GND"), ("TP2", "+3V3"), ("TP3", "VSYS"), ("TP4", "SENS1"), ("TP5", "SENS2"), ("TP6", "SENS3"),
       ("TP7", "LED_K"))
for i, (ref, net) in enumerate(TPS):
    x, y = 309.88 + 13.97 * i, 212.09
    t = s.place("Connector:TestPoint", ref, net if net[0] != "+" else net[1:], x, y, 0,
                footprint="TestPoint:TestPoint_Pad_D1.5mm", in_bom=False, ref_off=(2.54, -2.54), val_off=(2.54, 0))
    if net in ("GND", "+3V3"):
        s.pwr(t, "1", net)
    else:
        s.lab(t, "1", net)
s.text("VBAT (D1 anode / J1 +) 3.6-4.8 V,  VSYS about 4.8 V (USB: 5 V),  3V3 = 3.3 V.", 302.26, 228.6, 1.27)
s.text("S1-S3: white low, black about 3 V.", 302.26, 232.41, 1.27)     # not '~3 V': it prints like '-3 V'
s.text("IR (LED_K): about 0.1 V while the IR LEDs are on (robot.sensors.leds(True)),", 302.26, 236.22, 1.27)
s.text("about 2 V when off.", 302.26, 240.03, 1.27)

out = os.path.join(KDIR, PROJ + ".kicad_sch")
s.save(out, date="2026-10-30", rev="L4",
       comments=("All parts through-hole. XIAO on two 1x7 pin headers",
                 "XIAO ESP32C6 + AE-TC78H653FTG + AE-TPS63802 (5 V) + 3 x LBR-127HLD",
                 "Design notes: README.md"))
