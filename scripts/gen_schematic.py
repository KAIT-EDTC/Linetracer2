#!/usr/bin/env python3
"""Generate hardware/kicad/Linetracer2.kicad_sch (single A3 sheet).

All inter-block connections are made with net labels; power uses GND/+3V3 symbols.
Net names here are the names that appear on the PCB and in the docs.
"""
import os

from kicad_env import KDIR, PROJ
from schlib import Sch

R_FP = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
C_FP = "Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm"
CP_FP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
LED_FP = "LED_THT:LED_D3.0mm"

s = Sch("Linetracer2 - kids line tracer (Raspberry Pi Pico + TC78H653FTG)")

# Akizuki (akizukidenshi.com) 通販コード for parts that are placed many times (checked 2026-10-05)
AKIZUKI = {
    "100": "125101 (100pcs)", "1k": "125102 (100pcs)", "10k": "125103 (100pcs)",
    "470uF 16V": "108426 (Rubycon 16WXA470MEFC 8x9)",
    "0.1uF": "113582 (10pcs)", "0.1uF (at motor)": "113582 (10pcs)",
    "LED red": "111577", "LED yellow": "111639", "LED yellow-green (POWER)": "111637",
    "piezo (option)": "104118 (PKM13EPYH4000-A0)",
}
_place = s.place


def _place_with_code(lib_id, ref, value, *args, **kw):
    fields = dict(kw.pop("fields", None) or {})
    if "Akizuki" not in fields and value in AKIZUKI:
        fields["Akizuki"] = AKIZUKI[value]
    return _place(lib_id, ref, value, *args, fields=fields or None, **kw)


s.place = _place_with_code

# ----------------------------------------------------------------- headings
s.text("Linetracer2  :  Raspberry Pi Pico line tracer for kids (all through-hole)", 20.32, 17.78, 3, True)
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

flg = s.power("PWR_FLAG", 45.72, 43.18, "up")
s.wire(45.72, 43.18, 45.72, 45.72)
s.label("VBAT", 45.72, 45.72, "down")

c1 = s.place("Device:C_Polarized", "C1", "470uF 16V", 63.5, 55.88, 0, footprint=CP_FP,
             fields={"Note": "motor bulk capacitor, place near U3 VM"})
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
flg2 = s.power("PWR_FLAG", 116.84, 43.18, "up")
s.wire(116.84, 43.18, 116.84, 45.72)
s.label("VSYS", 116.84, 45.72, "down")

r13 = s.place("Device:R", "R13", "10k", 132.08, 48.26, 0, footprint=R_FP, ref_off=(-7.62, -1.27), val_off=(-7.62, 1.27))
r14 = s.place("Device:R", "R14", "10k", 132.08, 63.5, 0, footprint=R_FP, ref_off=(-7.62, -1.27), val_off=(-7.62, 1.27))
s.lab(r13, "1", "VBAT")
s.pwr(r14, "2", "GND")
x13, y13, _ = r13.pin("2")
x14, y14, _ = r14.pin("1")
ym = 55.88
s.wire(x13, y13, x13, ym)
s.wire(x13, ym, x14, y14)
s.junction(x13, ym)
c3 = s.place("Device:C", "C3", "0.1uF", 144.78, 59.69, 0, footprint=C_FP)
xc3, yc3, _ = c3.pin("1")
s.path((x13, ym), (xc3, ym), (xc3, yc3))
s.label("VBAT_SENSE", 137.16, ym, "up")
s.pwr(c3, "2", "GND")
s.text("VBAT/2 -> GP27(ADC1)", 125.73, 76.2, 1.27)

r19 = s.place("Device:R", "R19", "1k", 160.02, 48.26, 0, footprint=R_FP, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
d4 = s.place("Device:LED", "D4", "LED yellow-green (POWER)", 160.02, 62.23, 90, footprint=LED_FP,
             ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
s.pwr(r19, "1", "+3V3")
s.connect(r19, "2", d4, "2")
s.pwr(d4, "1", "GND")

# ---- mechanical (mounting holes, kept in the schematic for PCB parity)
s.text("MECHANICAL: H1-H4 = gearbox frame M3 (x30/x70, y62/y96), H5 = front skid M3", 20.32, 83.82, 1.27)
for i in range(5):
    s.place("Mechanical:MountingHole", "H%d" % (i + 1), "M3" if i < 4 else "SKID M3", 27.94 + i * 22.86, 91.44, 0,
            footprint="MountingHole:MountingHole_3.2mm_M3", in_bom=False,
            ref_off=(2.54, -1.27), val_off=(2.54, 1.27))

# ================================================================= MCU block
s.rect(119.38, 101.6, 264.16, 193.04)
s.text("2. MCU  Raspberry Pi Pico / Pico 2", 121.92, 106.68, 2, True)
u1 = s.place("Linetracer2:RaspberryPi_Pico_THT", "U1", "Raspberry Pi Pico", 190.5, 149.86, 0,
             fields={"Akizuki": "116132 (Pico, Pico 2 / Pico W also OK)"},
             ref_off=(-17.78, -27.94), val_off=(-17.78, -25.4))
left = {"1": "BUZZER", "2": "SENS_LED_EN", "4": None, "5": None, "6": "I2C_SDA", "7": "I2C_SCL",
        "9": None, "10": None, "11": None, "12": None, "14": "EXT_GP10", "15": "MOT_STBY",
        "16": "MOT_IN1", "17": "MOT_IN2", "19": "MOT_IN3", "20": "MOT_IN4", "30": None, "37": None}
right = {"21": "SW1", "22": "SW2", "24": "LED1", "25": "LED2", "26": "MUX_S0",
         "27": "MUX_S1", "29": "MUX_S2", "31": "SENS_A", "32": "VBAT_SENSE", "34": "EXT_A2", "35": None}
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
s.text("GP25 = on-board LED (Pico only).  GP29/ADC3 = VSYS/3 (inside Pico).", 121.92, 182.88, 1.27)

# ================================================================= MOTOR block
s.rect(269.24, 30.48, 408.94, 99.06)
s.text("3. MOTOR DRIVER  (Akizuki AE-TC78H653FTG module, DIP16)", 271.78, 35.56, 2, True)
u3 = s.place("Linetracer2:AE-TC78H653FTG", "U3", "AE-TC78H653FTG", 304.8, 60.96, 0,
             fields={"Akizuki": "114746"}, ref_off=(-5.08, -13.97), val_off=(-7.62, 13.97))
s.pwr(u3, "1", "GND")   # LARGE = L : small mode (2 motors, 2A/ch)
s.pwr(u3, "2", "GND")   # MODE  = L : IN/IN control
s.lab(u3, "3", "MOT_STBY")
s.lab(u3, "4", "MOT_IN4")
s.lab(u3, "5", "MOT_IN3")
s.lab(u3, "6", "MOT_IN1")
s.lab(u3, "7", "MOT_IN2")
s.pwr(u3, "8", "GND")
s.lab(u3, "16", "VBAT")
s.lab(u3, "15", "VBAT")
s.lab(u3, "14", "MOT_OUT4")
s.lab(u3, "13", "MOT_OUT3")
s.lab(u3, "12", "MOT_OUT1")
s.lab(u3, "11", "MOT_OUT2")
s.pwr(u3, "10", "GND")
s.pwr(u3, "9", "GND")

# motors drawn horizontally: pin 1 (+) left, pin 2 (-) right
for i, (ref, val, cref, ya, yb, yc) in enumerate((("M1", "LEFT motor  FA-130RA", "C5", 1, 2, 44.45),
                                                  ("M2", "RIGHT motor FA-130RA", "C6", 3, 4, 69.85))):
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
s.text("4. BUTTONS / LEDs / SOUND", 271.78, 106.68, 2, True)
sw1 = s.place("Switch:SW_Push", "SW1", "START", 294.64, 116.84, 0, footprint="Button_Switch_THT:SW_PUSH_6mm",
              fields={"Akizuki": "108075"}, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
s.lab(sw1, "1", "SW1")
s.pwr(sw1, "2", "GND")
sw2 = s.place("Switch:SW_Push", "SW2", "SELECT", 294.64, 129.54, 0, footprint="Button_Switch_THT:SW_PUSH_6mm",
              fields={"Akizuki": "108075"}, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
s.lab(sw2, "1", "SW2")
s.pwr(sw2, "2", "GND")
s.text("internal pull-up, pressed = 0", 279.4, 137.16, 1.27)

for i, (net, y) in enumerate((("LED1", 147.32), ("LED2", 160.02))):
    r = s.place("Device:R", "R%d" % (16 + i), "1k", 287.02, y, 90, footprint=R_FP,
                ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
    d = s.place("Device:LED", "D%d" % (2 + i), "LED red" if i == 0 else "LED yellow", 302.26, y, 180,
                footprint=LED_FP, ref_off=(-2.54, -3.81), val_off=(-3.81, 3.81))
    s.lab(r, "1", net)
    s.connect(r, "2", d, "2")
    s.pwr(d, "1", "GND")

r18 = s.place("Device:R", "R18", "100", 287.02, 175.26, 90, footprint=R_FP,
              ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
bz = s.place("Device:Buzzer", "BZ1", "piezo (option)", 304.8, 177.8, 0,
             footprint="Linetracer2:Buzzer_P5.0_P7.6",
             fields={"Note": "passive piezo, optional. 13mm PKM13EPYH4000-A0 (pitch 5.0) or 12mm (pitch 7.6)"},
             ref_off=(3.81, -2.54), val_off=(3.81, 2.54))
s.lab(r18, "1", "BUZZER")
s.connect(r18, "2", bz, "1")
s.pwr(bz, "2", "GND", length=2.54)

# ================================================================= EXPANSION block
s.rect(345.44, 101.6, 408.94, 190.5)
s.text("5. EXPANSION (not needed for basic kit)", 347.98, 106.68, 2, True)
j2 = s.place("Connector_Generic:Conn_01x04", "J2", "I2C (0.96in OLED order)", 386.08, 124.46, 0,
             footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
             ref_off=(-2.54, -6.35), val_off=(-7.62, 8.89))
s.pwr(j2, "1", "GND")
s.pwr(j2, "2", "+3V3", length=10.16)
s.lab(j2, "3", "I2C_SCL")
s.lab(j2, "4", "I2C_SDA")
j3 = s.place("Connector_Generic:Conn_02x03_Odd_Even", "J3", "EXT (2x3)", 375.92, 157.48, 0,
             footprint="Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
             ref_off=(-1.27, -6.35), val_off=(-3.81, 7.62))
s.pwr(j3, "1", "GND")
s.pwr(j3, "2", "+3V3")
s.lab(j3, "3", "MUX_X6")
s.lab(j3, "4", "MUX_X7")
s.lab(j3, "5", "EXT_A2")
s.lab(j3, "6", "EXT_GP10")
s.text("MUX_X6/X7: two extra analog sensors (e.g. side markers)", 347.98, 180.34, 1.27)

# ================================================================= SENSOR block
s.rect(17.78, 195.58, 299.72, 281.94)
s.text("6. LINE SENSORS  6 x LBR-123F (mount on the BOTTOM side, lens to the floor, 2-3 mm gap)", 20.32, 200.66, 2, True)
s.text("IR LED: (3.3V - 1.25V) / 100 ohm = about 19 mA each.  Q1 switches all LEDs (ambient light cancel).  "
       "Photo transistor: 10k pull-up -> white = low voltage, black = high voltage", 20.32, 205.74, 1.27)
by = 238.76
for i in range(6):
    bx = 38.1 + i * 40.64
    ps = s.place("Linetracer2:LBR-123F", "PS%d" % (i + 1), "LBR-123F", bx, by, 0,
                 fields={"Akizuki": "116455"}, ref_off=(-3.81, -6.35), val_off=(-3.81, 7.62))
    rl = s.place("Device:R", "R%d" % (i + 1), "100", bx - 12.7, by - 12.7, 0, footprint=R_FP,
                 ref_off=(-6.35, -1.27), val_off=(-6.35, 1.27))
    rp = s.place("Device:R", "R%d" % (i + 7), "10k", bx + 12.7, by - 12.7, 0, footprint=R_FP,
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
s.text("PS1 = far LEFT ... PS6 = far RIGHT (seen from above, robot moving up the page)", 20.32, 276.86, 1.27)

# LED switch
q1 = s.place("Transistor_BJT:2SC1815", "Q1", "2SC1815-GR", 279.4, 251.46, 0,
             footprint="Package_TO_SOT_THT:TO-92_Inline_Wide", fields={"Akizuki": "117089"},
             ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
r15 = s.place("Device:R", "R15", "1k", 266.7, 251.46, 90, footprint=R_FP,
              ref_off=(-2.54, -2.54), val_off=(-1.27, 2.54))
qb = [n for n, v in q1._pins.items() if v[0][3] == "B"][0]
qc = [n for n, v in q1._pins.items() if v[0][3] == "C"][0]
qe = [n for n, v in q1._pins.items() if v[0][3] == "E"][0]
s.connect(r15, "2", q1, qb)
s.lab(r15, "1", "SENS_LED_EN")
s.lab(q1, qc, "LED_K")
s.pwr(q1, qe, "GND")
s.text("Q1: all IR LEDs on when SENS_LED_EN = 1 (about 115 mA)", 175.26, 276.86, 1.27)

# Analog mux
s.rect(304.8, 195.58, 408.94, 251.46)
s.text("7. ANALOG MUX (6 sensors -> 1 ADC)", 307.34, 200.66, 2, True)
u2 = s.place("Analog_Switch:CD4051B", "U2", "TC4051BP (CD4051B)", 345.44, 226.06, 0,
             footprint="Package_DIP:DIP-16_W7.62mm", fields={"Akizuki": "110914"},
             ref_off=(-12.7, -20.32), val_off=(5.08, -20.32))
s.lab(u2, "11", "MUX_S0")
s.lab(u2, "10", "MUX_S1")
s.lab(u2, "9", "MUX_S2")
s.pwr(u2, "6", "GND")      # INH
s.lab(u2, "3", "SENS_A")   # common -> GP26/ADC0
# channel map chosen for clean PCB routing (firmware: SENSOR_CH = [4, 2, 1, 0, 3, 5])
MUXMAP = {"1": "SENS1", "15": "SENS2", "14": "SENS3", "13": "SENS4", "12": "SENS5", "5": "SENS6",
          "2": "MUX_X6", "4": "MUX_X7"}
for num, net in MUXMAP.items():
    s.lab(u2, num, net)
s.pwr(u2, "16", "+3V3")
s.pwr(u2, "8", "GND")
xe7, ye7, _ = u2.pin("7")
xe8, ye8, _ = u2.pin("8")
s.path((xe7, ye7), (xe7, ye7 + 1.27), (xe8, ye8 + 1.27))
s.junction(xe8, ye8 + 1.27)
c4 = s.place("Device:C", "C4", "0.1uF", 393.7, 220.98, 0, footprint=C_FP)
s.pwr(c4, "1", "+3V3")
s.pwr(c4, "2", "GND")

out = os.path.join(KDIR, PROJ + ".kicad_sch")
s.save(out, comments=("All parts are through-hole (kids can solder).",
                      "Motor driver = Akizuki AE-TC78H653FTG module (TC78H653FTG is QFN, pre-mounted)",
                      "See docs/03_circuit.md for the design notes"))
