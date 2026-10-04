#!/usr/bin/env python3
"""Generate hardware/lite/kicad/Linetracer2-Lite.kicad_sch (low-cost Lite board, single A3 sheet).

    LT2_VARIANT=lite python3 gen_schematic_lite.py

Differences from the standard board (gen_schematic.py):
  * Pico soldered flat on the board (no pin headers), footprint Linetracer2:RaspberryPi_Pico_DirectSolder
  * 3 sensors straight into ADC0..2 (no 4051 multiplexer)
  * battery voltage = VSYS/3 inside the Pico (GP29/ADC3), no divider R13/R14/C3
  * 1 button, 1 LED, no buzzer, no power LED, no EXT header (I2C holes kept, not fitted)
"""
import os

from kicad_env import KDIR, PROJ, VARIANT
from schlib import Sch

assert VARIANT == "lite", "run with LT2_VARIANT=lite"

R_FP = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
C_FP = "Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm"
CP_FP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
LED_FP = "LED_THT:LED_D3.0mm"

s = Sch("Linetracer2 Lite - low-cost kids line tracer")

# Akizuki (akizukidenshi.com) 通販コード for parts that are placed many times (checked 2026-10-05)
AKIZUKI = {
    "100": "125101 (100pcs)", "1k": "125102 (100pcs)", "10k": "125103 (100pcs)",
    "470uF 16V": "108426 (Rubycon 16WXA470MEFC 8x9)",
    "0.1uF (at motor)": "113582 (10pcs)",
    "LED red": "111577",
}
_place = s.place


def _place_with_code(lib_id, ref, value, *args, **kw):
    fields = dict(kw.pop("fields", None) or {})
    if "Akizuki" not in fields and value in AKIZUKI:
        fields["Akizuki"] = AKIZUKI[value]
    return _place(lib_id, ref, value, *args, fields=fields or None, **kw)


s.place = _place_with_code

# ----------------------------------------------------------------- headings
s.text("Linetracer2 Lite  :  low-cost version (Pico without pin headers, 3 sensors, 1 button, 1 LED)", 20.32, 17.78, 3, True)
s.text("Power: AA x3 (alkaline 4.5V / NiMH 3.6V) -> VBAT (motors) ; VBAT -> D1 Schottky -> VSYS (Pico). "
       "USB 5V can not back-feed the batteries. Never use 4 cells (Pico VSYS max 5.5V).", 20.32, 24.13, 1.5)

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
             fields={"Note": "hold-up for Pico when motors pull the battery down"})
s.lab(c2, "1", "VSYS")
s.pwr(c2, "2", "GND")
s.power("PWR_FLAG", 116.84, 43.18, "up")
s.wire(116.84, 43.18, 116.84, 45.72)
s.label("VSYS", 116.84, 45.72, "down")

s.text("Battery voltage: no divider on this board. The Pico measures VSYS/3 on GP29 (ADC3) internally;", 127.0, 50.8, 1.27)
s.text("VBAT = VSYS + about 0.3 V (D1).  GP24 = 1 while USB is plugged in.", 127.0, 54.61, 1.27)

# ---- mechanical (mounting holes, kept in the schematic for PCB parity)
s.text("MECHANICAL: H1-H4 = gearbox frame M3 (x30/x70, y62/y96), H5 = front skid M3 (x50, y11: behind the centre sensor)",
       20.32, 83.82, 1.27)
for i in range(5):
    s.place("Mechanical:MountingHole", "H%d" % (i + 1), "M3" if i < 4 else "SKID M3", 27.94 + i * 22.86, 91.44, 0,
            footprint="MountingHole:MountingHole_3.2mm_M3", in_bom=False,
            ref_off=(2.54, -1.27), val_off=(2.54, 1.27))

# ================================================================= MCU block
s.rect(119.38, 101.6, 264.16, 193.04)
s.text("2. MCU  Raspberry Pi Pico / Pico 2  (soldered flat, no pin headers)", 121.92, 106.68, 2, True)
u1 = s.place("Linetracer2:RaspberryPi_Pico_THT", "U1", "Raspberry Pi Pico", 190.5, 149.86, 0,
             footprint="Linetracer2:RaspberryPi_Pico_DirectSolder",
             fields={"Akizuki": "116132 (Pico, Pico 2 also OK; not Pico W)",
                     "Note": "solder the castellated edge straight onto the pads, no pin header"},
             ref_off=(-17.78, -27.94), val_off=(-17.78, -25.4))
left = {"1": None, "2": "SENS_LED_EN", "4": None, "5": None, "6": "I2C_SDA", "7": "I2C_SCL",
        "9": None, "10": None, "11": None, "12": None, "14": None, "15": "MOT_STBY",
        "16": "MOT_IN1", "17": "MOT_IN2", "19": "MOT_IN3", "20": "MOT_IN4", "30": None, "37": None}
# ADC pins chosen so the three sensor lines do not cross on the board (GP28 is the leftmost of the three)
right = {"21": "SW1", "22": None, "24": "LED1", "25": None, "26": None,
         "27": None, "29": None, "31": "SENS3", "32": "SENS2", "34": "SENS1", "35": None}
for num, net in list(left.items()) + list(right.items()):
    if net is None:
        s.nc(u1, num)
    else:
        s.lab(u1, num, net)
s.pwr(u1, "33", "GND")      # AGND
s.pwr(u1, "36", "+3V3")
xv, yv, _ = u1.pin("39")
s.path((xv, yv), (xv, yv - 2.54), (xv - 10.16, yv - 2.54))
s.label("VSYS", xv - 10.16, yv - 2.54, "left")
s.nc(u1, "40")              # VBUS (USB 5V, not used on the board)
s.pwr(u1, "3", "GND")
s.text("GP25 = on-board LED (a 2nd indicator for free).  GP29/ADC3 = VSYS/3, GP24 = VBUS sense (inside Pico).",
       121.92, 182.88, 1.27)
s.text("Pico W / Pico 2 W: GP29 and GP25 belong to the radio chip -> battery reading does not work, not recommended.",
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
for ref, val, cref, ya, yb, yc in (("M1", "LEFT motor  FA-130RA", "C3", 1, 2, 44.45),
                                   ("M2", "RIGHT motor FA-130RA", "C4", 3, 4, 69.85)):
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
s.text("IN1/IN2 -> OUT1/OUT2 = LEFT motor,   IN3/IN4 -> OUT3/OUT4 = RIGHT motor", 271.78, 88.9, 1.27)
s.text("H/L fwd, L/H rev, H/H brake, L/L coast.  Over-current (ISD) latches OFF:", 271.78, 92.71, 1.27)
s.text("toggle STBY L->H to recover (done by the library).", 271.78, 96.52, 1.27)

# ================================================================= UI block
s.rect(269.24, 101.6, 340.36, 190.5)
s.text("4. BUTTON / LED", 271.78, 106.68, 2, True)
sw1 = s.place("Switch:SW_Push", "SW1", "START", 294.64, 116.84, 0, footprint="Button_Switch_THT:SW_PUSH_6mm",
              fields={"Akizuki": "108075"}, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
s.lab(sw1, "1", "SW1")
s.pwr(sw1, "2", "GND")
s.text("internal pull-up, pressed = 0", 279.4, 124.46, 1.27)
s.text("short press = start / stop, long press = speed level", 279.4, 128.27, 1.27)

r8 = s.place("Device:R", "R8", "1k", 287.02, 147.32, 90, footprint=R_FP,
             ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
d2 = s.place("Device:LED", "D2", "LED red", 302.26, 147.32, 180,
             footprint=LED_FP, ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
s.lab(r8, "1", "LED1")
s.connect(r8, "2", d2, "2")
s.pwr(d2, "1", "GND")
s.text("no buzzer, no power LED on the Lite board", 279.4, 165.1, 1.27)

# ================================================================= EXPANSION block
s.rect(345.44, 101.6, 408.94, 190.5)
s.text("5. EXPANSION (holes only)", 347.98, 106.68, 2, True)
j2 = s.place("Connector_Generic:Conn_01x04", "J2", "I2C (0.96in OLED order)", 386.08, 124.46, 0,
             footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
             fields={"Note": "not fitted in the kit (no pin header). Solder a 1x4 header to add an OLED"},
             in_bom=False, dnp=True, ref_off=(-2.54, -6.35), val_off=(-7.62, 8.89))
s.pwr(j2, "1", "GND")
s.pwr(j2, "2", "+3V3", length=10.16)
s.lab(j2, "3", "I2C_SCL")
s.lab(j2, "4", "I2C_SDA")

# ================================================================= SENSOR block
s.rect(17.78, 195.58, 299.72, 281.94)
s.text("6. LINE SENSORS  3 x LBR-123F (mount on the BOTTOM side, lens to the floor, 2-3 mm gap), 12 mm apart",
       20.32, 200.66, 2, True)
s.text("IR LED: (3.3V - 1.25V) / 100 ohm = about 19 mA each.  Q1 switches all LEDs (ambient light cancel).  "
       "Photo transistor: 10k pull-up -> white = low voltage, black = high voltage", 20.32, 205.74, 1.27)
by = 238.76
for i in range(3):
    bx = 38.1 + i * 60.96
    ps = s.place("Linetracer2:LBR-123F", "PS%d" % (i + 1), "LBR-123F", bx, by, 0,
                 fields={"Akizuki": "116455"}, ref_off=(-3.81, -6.35), val_off=(-3.81, 7.62))
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
s.text("PS1 = LEFT -> GP28/ADC2,  PS2 = CENTRE -> GP27/ADC1,  PS3 = RIGHT -> GP26/ADC0  "
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
s.text("Q1: all IR LEDs on when SENS_LED_EN = 1 (about 57 mA)", 200.66, 270.51, 1.27)

out = os.path.join(KDIR, PROJ + ".kicad_sch")
s.save(out, date="2026-10-05", rev="L1",
       comments=("All parts through-hole. Pico soldered flat (castellated edge)",
                 "Pico + Akizuki AE-TC78H653FTG module + 3 x LBR-123F",
                 "Design notes: docs/09_lite.md"))
