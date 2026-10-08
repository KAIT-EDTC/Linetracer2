#!/usr/bin/env python3
"""Generate lite/hardware/kicad/Linetracer2-Lite.kicad_sch (Lite board rev.L3, single A3 sheet).

    cd scripts && LT2_VARIANT=lite python3 ../lite/scripts/gen_schematic_lite.py

Differences from the standard board (gen_schematic.py):
  * Seeed Studio XIAO ESP32C6 on two 1x7 pin headers (footprint Linetracer2:XIAO_ESP32C6_Header);
    powered through its 5V pin (= USB VBUS) behind D1
  * 3 x LBR-127HLD sensors straight into the XIAO's three ADC pins (no 4051 multiplexer)
  * no battery measurement (the XIAO has only 3 ADC pins; all of them are used by the sensors)
  * 1 button, a passive piezo buzzer sharing the button's pin (D4), 5 full-colour LEDs (PL9823, one data line
    on D6), no power LED, no expansion header
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))   # shared modules
from kicad_env import KDIR, PROJ, VARIANT
from schlib import Sch

assert VARIANT == "lite", "run with LT2_VARIANT=lite"

R_FP = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
C_FP = "Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm"
CP_FP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
RGB_FP = "Linetracer2:LED_PL9823_5mm"

s = Sch("Linetracer2 Lite rev.L3 - XIAO ESP32C6 kids line tracer")

# Akizuki (akizukidenshi.com) 通販コード for parts that are placed many times (checked 2026-10-05)
AKIZUKI = {
    "100": "125101 (100pcs)", "1k": "125102 (100pcs)", "10k": "125103 (100pcs)",
    "470uF 16V": "108426 (Rubycon 16WXA470MEFC 8x9)",
    "0.1uF (at motor)": "113582 (10pcs)",
    "0.1uF": "113582 (10pcs)",
    "PL9823": "108411 (PL9823-F5)",
}
_place = s.place


def _place_with_code(lib_id, ref, value, *args, **kw):
    fields = dict(kw.pop("fields", None) or {})
    if "Akizuki" not in fields and value in AKIZUKI:
        fields["Akizuki"] = AKIZUKI[value]
    return _place(lib_id, ref, value, *args, fields=fields or None, **kw)


s.place = _place_with_code

# ----------------------------------------------------------------- headings
s.text("Linetracer2 Lite rev.L3  :  XIAO ESP32C6 on pin headers, 3 x LBR-127HLD, 1 button, 1 buzzer, 5 RGB LEDs", 20.32, 17.78, 3, True)
s.text("Power: AA x3 (alkaline 4.5V recommended / NiMH 3.6V) -> VBAT (motors) ; VBAT -> D1 Schottky -> VSYS -> XIAO 5V pin. "
       "USB 5V can not back-feed the batteries. Never use 4 cells (the XIAO's 5V input clamps above about 6 V).", 20.32, 24.13, 1.5)

# ================================================================= POWER block
s.rect(17.78, 30.48, 172.72, 99.06)
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

s.power("PWR_FLAG", 45.72, 43.18, "up")
s.wire(45.72, 43.18, 45.72, 45.72)
s.label("VBAT", 45.72, 45.72, "down")

c1 = s.place("Device:C_Polarized", "C1", "470uF 16V", 63.5, 55.88, 0, footprint=CP_FP,
             fields={"Note": "motor bulk capacitor, place near U2 VM"})
s.lab(c1, "1", "VBAT")
s.pwr(c1, "2", "GND")

d1 = s.place("Device:D_Schottky", "D1", "1N5819", 86.36, 45.72, 180,
             footprint="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
             fields={"Akizuki": "117244", "Note": "blocks USB 5V back-feed into batteries"},
             ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
s.lab(d1, "2", "VBAT")      # A
s.lab(d1, "1", "VSYS")      # K

c2 = s.place("Device:C_Polarized", "C2", "470uF 16V", 106.68, 55.88, 0, footprint=CP_FP,
             fields={"Note": "hold-up for the XIAO when motors pull the battery down"})
s.lab(c2, "1", "VSYS")
s.pwr(c2, "2", "GND")
s.power("PWR_FLAG", 116.84, 43.18, "up")
s.wire(116.84, 43.18, 116.84, 45.72)
s.label("VSYS", 116.84, 45.72, "down")

# GND: nothing on this board is a power output for GND (the XIAO's GND pin is a power input)
s.power("PWR_FLAG", 139.7, 68.58, "up")
s.wire(139.7, 68.58, 139.7, 71.12)
s.power("GND", 139.7, 71.12, "down")

s.text("XIAO 5V pin = USB VBUS: an external supply needs a diode (D1), otherwise USB 5V charges the AA cells.", 127.0, 50.8, 1.27)
s.text("Battery voltage is NOT measured: the XIAO has 3 ADC pins only (D0..D2) and the sensors use all of them.", 127.0, 54.61, 1.27)
s.text("Inside the XIAO: 5V pin -> Schottky -> buck regulator -> 3V3 (3V3 stays up while VBAT > about 4 V).", 127.0, 58.42, 1.27)

# ---- mechanical (mounting holes, kept in the schematic for PCB parity)
s.text("MECHANICAL: H1-H4 = gearbox frame M3 (x30/x70, y62/y96), H5 = front ball caster / skid, snap-in (x50, y11: behind the centre sensor)",
       20.32, 83.82, 1.27)
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
# D4 (SW1) also drives the buzzer (through R9; the button hangs on R10).  D6 = data of the 5 RGB LEDs.
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
s.text("Never solder a Li-ion cell to the XIAO's BAT pads on this robot (AA cells are on the 5V pin).",
       121.92, 186.69, 1.27)

# ================================================================= MOTOR block
s.rect(269.24, 30.48, 408.94, 99.06)
s.text("3. MOTOR DRIVER  (Akizuki AE-TC78H653FTG module, DIP16)", 271.78, 35.56, 2, True)
u2 = s.place("Linetracer2:AE-TC78H653FTG", "U2", "AE-TC78H653FTG", 304.8, 60.96, 0,
             fields={"Akizuki": "114746", "Note": "uses the two 1x8 pin headers that come with the module"},
             ref_off=(-5.08, -13.97), val_off=(-7.62, 13.97))
s.pwr(u2, "1", "GND")   # LARGE = L : small mode (2 motors, 2A/ch)
s.pwr(u2, "2", "GND")   # MODE  = L : IN/IN control
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
s.rect(269.24, 101.6, 408.94, 190.5)
s.text("4. BUTTON / BUZZER / RGB LEDs", 271.78, 106.68, 2, True)
sw1 = s.place("Switch:SW_Push", "SW1", "START", 294.64, 116.84, 0, footprint="Button_Switch_THT:SW_PUSH_6mm",
              fields={"Akizuki": "108075"}, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
r10 = s.place("Device:R", "R10", "1k", 279.4, 116.84, 90, footprint=R_FP,
              ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
s.lab(r10, "1", "SW1")
s.lab(r10, "2", "BTN")
s.lab(sw1, "1", "BTN")
s.pwr(sw1, "2", "GND")
s.text("internal pull-up, pressed = 0.  R10: if START is pressed while D4 beeps, only 3.3 mA flows",
       271.78, 124.46, 1.27)
s.text("short press = start / stop, long press = speed level", 271.78, 128.27, 1.27)

# 5 full-colour LEDs in one chain: D6 -> D2 DIN, DO -> next DIN ... D6 DO open.  Powered from VSYS (battery - 0.3 V,
# or USB 5 V): the PL9823 asks for 4.5-6 V, on fresh AA cells VSYS is about 4.2 V (works, a little out of spec;
# blue / green get dimmer as the cells run down).  C5 = 0.1 uF next to the LEDs.
leds = []
for i in range(5):
    d = s.place("Linetracer2:PL9823", "D%d" % (i + 2), "PL9823", 284.48 + 22.86 * i, 149.86, 0, footprint=RGB_FP,
                ref_off=(-5.08, -7.62), val_off=(2.54, 7.62))
    s.lab(d, "3", "VSYS")
    s.pwr(d, "1", "GND")
    leds.append(d)
s.lab(leds[0], "4", "RGB_DIN")
for a, b in zip(leds, leds[1:]):
    s.connect(a, "2", b, "4")
s.nc(leds[-1], "2")
c5 = s.place("Device:C", "C5", "0.1uF", 396.24, 149.86, 0, footprint=C_FP, ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
s.lab(c5, "1", "VSYS")
s.pwr(c5, "2", "GND")
s.text("D2..D6 = PL9823 (NeoPixel type, 800 kHz, 24 bit per LED).  Data from D6 (TX: the boot log may flash them once).",
       271.78, 163.83, 1.27)
s.text("All 5 white at full power = about 0.3 A: the library limits the brightness.", 271.78, 167.64, 1.27)
r9 = s.place("Device:R", "R9", "100", 287.02, 172.72, 90, footprint=R_FP,
             ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
bz = s.place("Device:Buzzer", "BZ1", "piezo 13mm", 304.8, 175.26, 0,
             footprint="Linetracer2:Buzzer_PKM13_P5.0",
             fields={"Akizuki": "104118 (Murata PKM13EPYH4000-A0)", "Note": "passive piezo, + on the square pad"},
             ref_off=(3.81, -2.54), val_off=(3.81, 2.54))
s.lab(r9, "1", "SW1")
s.connect(r9, "2", bz, "1")
s.pwr(bz, "2", "GND", length=2.54)
s.text("The buzzer shares D4 with the START button (no free XIAO pin).  A piezo passes no DC, so reading the",
       271.78, 182.88, 1.27)
s.text("button (input + pull-up) works; to beep, D4 becomes a PWM output - it also sounds while START is held.",
       271.78, 186.69, 1.27)

# ================================================================= SENSOR block
s.rect(17.78, 195.58, 299.72, 281.94)
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
                 fields={"Akizuki": "104500"}, ref_off=(-3.81, -6.35), val_off=(-3.81, 7.62))
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
q1 = s.place("Transistor_BJT:2SC1815", "Q1", "2SC1815-GR", 279.4, 251.46, 0,
             footprint="Package_TO_SOT_THT:TO-92_Inline_Wide", fields={"Akizuki": "117089"},
             ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
r7 = s.place("Device:R", "R7", "1k", 266.7, 251.46, 90, footprint=R_FP,
             ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
qb = [n for n, v in q1._pins.items() if v[0][3] == "B"][0]
qc = [n for n, v in q1._pins.items() if v[0][3] == "C"][0]
qe = [n for n, v in q1._pins.items() if v[0][3] == "E"][0]
s.connect(r7, "2", q1, qb)
s.lab(r7, "1", "SENS_LED_EN")
s.lab(q1, qc, "LED_K")
s.pwr(q1, qe, "GND")
s.text("Q1: all IR LEDs on when SENS_LED_EN = 1 (about 60 mA)", 200.66, 270.51, 1.27)

out = os.path.join(KDIR, PROJ + ".kicad_sch")
s.save(out, date="2026-10-07", rev="L3",
       comments=("All parts through-hole. XIAO on two 1x7 pin headers",
                 "XIAO ESP32C6 + Akizuki AE-TC78H653FTG module + 3 x LBR-127HLD",
                 "Design notes: lite/README.md"))
