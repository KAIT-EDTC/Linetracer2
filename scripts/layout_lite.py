#!/usr/bin/env python3
"""Lite board rev.L3: placement + hand-drawn routes.  Pure data (no pcbnew), shared by
gen_pcb_lite.py (placement), route_lite.py (tracks into the board) and the preview tool.

Board coordinates (mm): x -> right, y -> rear, (0, 0) = front-left corner of the standard board; the Lite board
is x 17.5 .. 82.5, y 0 .. 100 (the rear 40 mm is under the gearbox frames).

Routing style ("beautiful" by rule, not by an autorouter):
  * only horizontal, vertical and 45 deg segments; every 90 deg corner gets a 45 deg chamfer
  * signals that travel together run as a bus at a fixed pitch (sensor lines 1.3 mm, motor inputs 1.27 mm,
    the three button/LED lines 1.0 mm) and keep their order, so nothing on the top side crosses
  * the top side (F.Cu) carries almost everything; the bottom side only the IR LED cathode bus right behind the
    sensors (they are on the bottom too) and the driver's STBY line, plus a GND pour on both sides
  * symmetric where the parts allow it: the driver sits on the centre line and fans out to both motors alike
"""

# ---------------------------------------------------------------- placement
# ref: (x, y, rotation, side)
PLACE = {}

SENSOR_X = [38.0, 50.0, 62.0]
SENSOR_Y = 4.0
SKID_HOLE = (50.0, 11.0)
FRAME_HOLES = [(30.0, 62.0), (30.0, 96.0), (70.0, 62.0), (70.0, 96.0)]

for _i, _x in enumerate(SENSOR_X):
    PLACE["PS%d" % (_i + 1)] = (_x, SENSOR_Y, 180, "B")    # LED (A front, K rear) left, photo transistor right

# sensor resistors: one row, pad 2 (sensor side) at the front (y 8.0), pad 1 (3V3) at the rear (y 18.16).
# The two in the middle (R2, R5) stay 6 mm away from the caster under the board.
R_FRONT, R_REAR = 8.0, 18.16
for _ref, _x in {"R1": 32.0, "R4": 38.0, "R2": 44.0, "R5": 56.0, "R3": 62.0, "R6": 68.0}.items():
    PLACE[_ref] = (_x, R_REAR, 90, "F")

# XIAO ESP32C6 on pin headers, USB-C at the right edge (rotation 270: front row D6..D0, rear row D7..5V)
XIAO_C = (71.05, 31.0)
PLACE["U1"] = (XIAO_C[0], XIAO_C[1], 270, "F")
# motor driver on the centre line (rotation 270: front row = inputs, rear row = outputs + VM)
U2_Y = 51.6
U2_F, U2_R = U2_Y - 3.81, U2_Y + 3.81            # pin rows
PLACE["U2"] = (50.0, U2_Y, 270, "F")
# motor pads (frame cut-outs) and the 0.1 uF caps sitting right on the fan-out tracks
PLACE["M1"] = (45.58, 61.5, 180, "F")
PLACE["M2"] = (59.5, 61.5, 180, "F")
CAP_Y = 58.35                                     # between the driver (courtyard 57.0) and the motor pads (59.7)
PLACE["C3"] = (48.73 - (CAP_Y - U2_R), CAP_Y, 180, "F")   # pad 1 on OUT1's diagonal, pad 2 on OUT2's
PLACE["C4"] = (53.81 + (CAP_Y - U2_R), CAP_Y, 180, "F")   # pad 1 on OUT4's diagonal, pad 2 on OUT3's

# power, right rear (between the motor-input bus, the frame at y 58 and the board edge):
# VBAT runs straight from the driver's VM pins to D1's anode; C1 and J1 hang on it with short stubs.
# VSYS: the XIAO's 5V pin straight back onto the line C2+ -> D1's cathode.
PLACE["C1"] = (64.8, 54.25, 90, "F")     # + rear (next to the VBAT line), - front
PLACE["J1"] = (72.8, 53.0, 0, "F")       # + (red) left, - right
PLACE["D1"] = (80.6, U2_R - 10.16, 270, "F")   # K front (VSYS), A rear = end of the VBAT line
PLACE["C2"] = (76.35, U2_R - 10.16, 180, "F")  # + right (in line with D1's K), - left

# IR LED switch, front left (turned 180 deg: base on the left, straight in front of R7)
PLACE["Q1"] = (30.66, 3.2, 180, "F")
PLACE["R7"] = (25.58, R_REAR, 90, "F")   # pad 2 straight behind Q1's base

# user interface, left: one row of resistors (pad 1 at the front, on the bus), the parts right behind them.
# D4 drives both the buzzer (through R9) and the button (through R10).
UI_R = 24.5
PLACE["R10"] = (25.58, UI_R, 270, "F")   # 1k: D4 -> button (right behind R7, same column)
PLACE["SW1"] = (19.08, 37.4, 0, "F")     # pin 1 (front) on R10, pin 2 (rear) GND
PLACE["R9"] = (32.5, UI_R, 270, "F")     # 100: D4 -> buzzer +
PLACE["BZ1"] = (32.5, 47.5, 270, "F")    # + front, - rear (body centre 32.5 / 50.0; 1 mm from the frame pillar)

# 6 full-colour LEDs (PL9823), 3 down each side edge of the front half (the board is free there in front of the
# XIAO).  One data chain: left rear -> left front (turned 90: DIN rear, DO front), along the front edge,
# right front -> right rear (turned 270: DIN front, DO rear).  VDD on the inner side of each column (bottom bars),
# GND on the outer side (pours).
LED_L, LED_R, LED_Y = 20.75, 79.25, (18.6, 11.6, 4.6)        # rear, middle, front
for _ref, _y in zip(("D2", "D3", "D4"), LED_Y):
    PLACE[_ref] = (LED_L, _y, 90, "F")
for _ref, _y in zip(("D5", "D6", "D7"), LED_Y[::-1]):
    PLACE[_ref] = (LED_R, _y, 270, "F")

# test pads (SMD, top) for a multimeter: GND/3V3 in the middle, the sensors on their bus lines, VSYS beside D1,
# IR (= IR LED cathodes) at Q1.  (VBAT: D1's anode pad, labelled - there is no room for one more pad there.)
TEST_PADS = {"TP1": (50.0, 22.6), "TP2": (50.0, R_REAR), "TP3": (81.0, 41.5),
             "TP4": (47.2, 16.6), "TP5": (59.0, 15.3), "TP6": (71.0, 14.0), "TP7": (28.79, 7.8)}
for _ref, (_x, _y) in TEST_PADS.items():
    PLACE[_ref] = (_x, _y, 0, "F")

for _i, (_x, _y) in enumerate(FRAME_HOLES + [SKID_HOLE]):
    PLACE["H%d" % (_i + 1)] = (_x, _y, 0, "F")

# ---------------------------------------------------------------- keep-outs
# ("circle", x, y, r, layer): steel screw heads on the bottom, the caster's snap pin on the top
KEEPOUTS = [("circle", x, y, 3.5, "B") for x, y in FRAME_HOLES] + [("circle", SKID_HOLE[0], SKID_HOLE[1], 2.6, "F")]
# on the bottom, solder joints must stay out of these (preview only): caster box, sensor bodies
BOTTOM_ZONES = [("rect", 45.0, 6.5, 55.0, 16.0)] + [("rect", x - 4.35, 1.75, x + 4.35, 6.25) for x in SENSOR_X]

# ---------------------------------------------------------------- routes
W_SIG, W_LED, W_3V3, W_VSYS, W_PWR = 0.25, 0.3, 0.4, 0.8, 1.0
W_LEDV = 0.4                 # VSYS to the RGB LEDs (bottom)
CHAMFER = 0.8
ROUTES = []      # dict(net, layer, w, pts, c)
VIAS = []        # (x, y, net)


def P(ref, num):
    return ("pad", ref, num)


def X(x):
    """horizontal to x"""
    return ("x", x)


def Y(y):
    """vertical to y"""
    return ("y", y)


def DX(x, sy=1):
    """45 deg to x (y moves the same distance, +1 = rear)"""
    return ("dx", x, sy)


def DY(y, sx=1):
    """45 deg to y (x moves the same distance)"""
    return ("dy", y, sx)


def route(net, layer, w, *pts, c=CHAMFER):
    ROUTES.append(dict(net=net, layer=layer, w=w, pts=list(pts), c=c))


# ---- sensors: LED anode -> 100R (one 45 deg line), collector -> trunk back to the bus, 10k as a side branch
for i, (r100, r10k) in enumerate((("R1", "R4"), ("R2", "R5"), ("R3", "R6"))):
    ps = "PS%d" % (i + 1)
    xs = SENSOR_X[i]
    xr = PLACE[r100][0]
    route("A%d" % (i + 1), "F", W_LED, P(ps, "1"), DX(xr), P(r100, "2"))

# collector trunks: x = 40.05 (S1), 53.5 (S2: clears the caster pin), 64.05 (S3); levels 16.6 / 15.3 / 14.0
SENS = (("SENS1", "PS1", "R4", "3", 40.05, 16.6, 73.59),
        ("SENS2", "PS2", "R5", "2", 53.5, 15.3, 76.13),
        ("SENS3", "PS3", "R6", "1", 64.05, 14.0, 78.67))
SENS_TP = {"SENS1": "TP4", "SENS2": "TP5", "SENS3": "TP6"}
for net, ps, r10k, upin, xt, lvl, xu in SENS:
    tp = SENS_TP[net]
    if ps == "PS2":
        route(net, "F", W_SIG, P(ps, "4"), DX(xt), Y(lvl), P(tp, "1"))
    else:
        route(net, "F", W_SIG, P(ps, "4"), Y(lvl), P(tp, "1"))
    if net == "SENS3":       # down at x 77.0, then 45 deg onto D0 (the right LED column is at x 78.35 ..)
        route(net, "F", W_SIG, P(tp, "1"), X(77.0), Y(23.38 - 1.67), DX(xu), P("U1", upin))
    else:
        route(net, "F", W_SIG, P(tp, "1"), X(xu), P("U1", upin))
    route(net, "F", W_SIG, (xt, R_FRONT), P(r10k, "2"))

# 3V3: along the resistors' rear pads, then between D3 and D2 under the XIAO to its 3V3 pin
route("+3V3", "F", W_3V3, P("R1", "1"), P("TP2", "1"))
route("+3V3", "F", W_3V3, P("TP2", "1"), P("R6", "1"))
route("+3V3", "F", W_SIG + 0.05, P("R6", "1"), X(72.32), Y(37.35), P("U1", "12"))   # 0.3: between two XIAO pins

# IR LED enable / button+buzzer / RGB data: a 3-line bus between the resistors and the XIAO, 1.0 mm pitch
route("SENS_LED_EN", "F", W_SIG, P("U1", "4"), Y(19.6), X(25.58), P("R7", "1"))
route("SW1", "F", W_SIG, P("U1", "5"), Y(20.6), X(25.58), P("R10", "1"))
route("SW1", "F", W_SIG, (32.5, 20.6), P("R9", "1"))
route("BTN", "F", W_SIG, P("R10", "2"), (25.58, 37.4))
route("BTN", "F", W_SIG, P("SW1", "1"), X(25.58))      # the button's two pin-1 legs
route("Q1-B", "F", W_SIG, P("R7", "2"), P("Q1", "3"))
route("BZ1+", "F", W_SIG, P("R9", "2"), P("BZ1", "1"))

# RGB LEDs.  Data: D6 on the bottom just in front of the XIAO's pins to the left rear LED, then on the top along
# each column (a step and a 45 deg jog between neighbours) and along the front edge from the left to the right
route("RGB_DIN", "B", W_SIG, P("U1", "7"), Y(21.8), X(LED_L - 0.9), P("D2", "4"))
route("D2-DO", "F", W_SIG, P("D2", "2"), Y(15.305), DX(LED_L - 0.9, -1), P("D3", "4"))
route("D3-DO", "F", W_SIG, P("D3", "2"), Y(8.305), DX(LED_L - 0.9, -1), P("D4", "4"))
route("D4-DO", "F", W_SIG, P("D4", "2"), Y(1.0), X(LED_R + 0.9), P("D5", "4"))
route("D5-DO", "F", W_SIG, P("D5", "2"), Y(7.895), DX(LED_R + 0.9), P("D6", "4"))
route("D6-DO", "F", W_SIG, P("D6", "2"), Y(14.895), DX(LED_R + 0.9), P("D7", "4"))
# supply (VSYS, up to 0.36 A) on the bottom: from the XIAO's 5V pin past its right end to a bar inside the right
# column, across the front half at y 14.5 (behind the caster pin) to a bar inside the left column; short stubs
LB, RB = LED_L + 2.1, LED_R - 2.1                     # the two bars (0.3 mm off the VDD / DO pads)
route("VSYS", "B", W_LEDV, P("U1", "14"), X(81.6), Y(22.0), X(RB), Y(LED_Y[2] - 0.635), P("D5", "3"), c=0.5)
route("VSYS", "B", W_LEDV, (RB, 14.5), X(LB), Y(LED_Y[0] + 0.635), P("D2", "3"), c=0)      # (LB, 14.5) is a T
route("VSYS", "B", W_LEDV, (LB, 14.5), Y(LED_Y[2] + 0.635), P("D4", "3"))
route("VSYS", "B", W_LEDV, (LB, LED_Y[1] + 0.635), P("D3", "3"))
route("VSYS", "B", W_LEDV, (RB, LED_Y[1] - 0.635), P("D6", "3"))
route("VSYS", "B", W_LEDV, (RB, LED_Y[0] - 0.635), P("D7", "3"))
# test pads on short stubs
route("VSYS", "F", W_SIG + 0.15, P("TP3", "1"), X(78.67))
route("LED_K", "F", W_SIG + 0.15, P("Q1", "2"), Y(7.13), DX(28.79), P("TP7", "1"))

# motor inputs: a 4-line bus from the XIAO's rear row to the driver, 1.27 mm between the levels.
# IN2 comes from the front row under the XIAO (it sits 2.5 mm up on its headers) and leaves between D7 and D8.
route("MOT_IN2", "F", W_SIG, P("U1", "6"), Y(36.2), DX(64.70), Y(40.6), X(43.65), P("U2", "7"))
route("MOT_IN1", "F", W_SIG, P("U1", "9"), Y(41.87), X(46.19), P("U2", "6"))
route("MOT_IN3", "F", W_SIG, P("U1", "10"), Y(43.14), X(48.73), P("U2", "5"))
route("MOT_IN4", "F", W_SIG, P("U1", "11"), Y(44.41), X(51.27), P("U2", "4"))
# STBY (D7) has to cross the bus: on the bottom, one 45 deg line (keeps out of the antenna area)
route("MOT_STBY", "B", W_SIG, P("U1", "8"), Y(40.4), X(53.81 + U2_F - 40.4), DX(53.81), P("U2", "3"))

# motors: symmetric 45 deg fan-out; C3 / C4 sit across each pair of parallel diagonals
route("MOT_OUT2", "F", W_PWR, P("U2", "11"), DX(40.5), P("M1", "2"))
route("MOT_OUT1", "F", W_PWR, P("U2", "12"), DX(45.58), P("M1", "1"))
route("MOT_OUT3", "F", W_PWR, P("U2", "13"), DX(54.42), P("M2", "2"))
route("MOT_OUT4", "F", W_PWR, P("U2", "14"), DX(59.5), P("M2", "1"))

# power: VBAT straight from VM to D1's anode, C1 and J1 on short stubs; VSYS: C2+ -> D1's K, 5V pin onto it
route("VBAT", "F", W_PWR, P("U2", "15"), X(80.6), P("D1", "2"))
route("VBAT", "F", W_PWR, (64.8, U2_R), P("C1", "1"))
route("VBAT", "F", W_PWR, (72.8, U2_R), P("J1", "1"))
route("VSYS", "F", W_VSYS, P("C2", "1"), P("D1", "1"))
route("VSYS", "F", W_VSYS, P("U1", "14"), Y(U2_R - 10.16))

# IR LED cathodes: a bus on the bottom right behind the sensors, to Q1's collector
route("LED_K", "B", W_3V3, P("Q1", "2"), Y(6.6), X(59.95), P("PS3", "2"))
route("LED_K", "B", W_3V3, (35.95, 6.6), P("PS1", "2"))
route("LED_K", "B", W_3V3, (47.95, 6.6), P("PS2", "2"))


# ---------------------------------------------------------------- geometry
def _resolve(pts, padpos):
    out = []
    for p in pts:
        if isinstance(p, tuple) and len(p) == 3 and p[0] == "pad":
            out.append(padpos(p[1], p[2]))
        elif isinstance(p, tuple) and len(p) == 4 and p[0] == "padx":
            out.append((padpos(p[1], p[2])[0], p[3]))     # (x of a pad, y)
        elif isinstance(p, tuple) and p and isinstance(p[0], str):
            x0, y0 = out[-1]
            if p[0] == "x":
                out.append((p[1], y0))
            elif p[0] == "y":
                out.append((x0, p[1]))
            elif p[0] == "dx":
                out.append((p[1], y0 + p[2] * abs(p[1] - x0)))
            elif p[0] == "dy":
                out.append((x0 + p[2] * abs(p[1] - y0), p[1]))
            else:
                raise ValueError(p)
        else:
            out.append((float(p[0]), float(p[1])))
    # drop zero-length steps
    clean = [out[0]]
    for q in out[1:]:
        if abs(q[0] - clean[-1][0]) > 1e-6 or abs(q[1] - clean[-1][1]) > 1e-6:
            clean.append(q)
    return clean


def _chamfer(pts, c):
    """45 deg chamfer at every 90 deg corner between a horizontal and a vertical segment."""
    import math
    if len(pts) < 3 or c <= 0:
        return pts
    out = [pts[0]]
    n = len(pts)
    for k in range(1, n - 1):
        a, b, d = out[-1], pts[k], pts[k + 1]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (d[0] - b[0], d[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        ortho = (abs(v1[0]) < 1e-6 or abs(v1[1]) < 1e-6) and (abs(v2[0]) < 1e-6 or abs(v2[1]) < 1e-6)
        perp = abs(v1[0] * v2[0] + v1[1] * v2[1]) < 1e-6
        if not (ortho and perp):
            out.append(b)
            continue
        k1 = 1.0 if k == 1 else 0.5            # the first / last segment may be used up completely
        k2 = 1.0 if k == n - 2 else 0.5
        cc = min(c, l1 * k1 - 0.01, l2 * k2 - 0.01)
        if cc <= 0.05:
            out.append(b)
            continue
        out.append((b[0] - v1[0] / l1 * cc, b[1] - v1[1] / l1 * cc))
        out.append((b[0] + v2[0] / l2 * cc, b[1] + v2[1] / l2 * cc))
    out.append(pts[-1])
    return out


def paths(padpos):
    """[(net, layer, width, [points...])] with the chamfers applied."""
    return [(r["net"], r["layer"], r["w"], _chamfer(_resolve(r["pts"], padpos), r["c"])) for r in ROUTES]


def tracks(padpos):
    segs = []
    for net, layer, w, pts in paths(padpos):
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b, layer, w, net))
    return segs


def vias(padpos):
    return [(x, y) for x, y, _ in VIAS]


def routed_nets():
    """Board net names that are fully hand-routed (the preview hides their ratsnest)."""
    names = {"A1": "Net-(PS1-A)", "A2": "Net-(PS2-A)", "A3": "Net-(PS3-A)", "Q1-B": "Net-(Q1-B)",
             "BZ1+": "Net-(BZ1-+)", "+3V3": "+3V3",
             "D2-DO": "Net-(D2-DO)", "D3-DO": "Net-(D3-DO)", "D4-DO": "Net-(D4-DO)", "D5-DO": "Net-(D5-DO)",
             "D6-DO": "Net-(D6-DO)"}
    return {names.get(r["net"], "/" + r["net"]) for r in ROUTES}


def check_angles(padpos):
    """Every segment must be horizontal, vertical or 45 deg."""
    bad = []
    for a, b, layer, w, net in tracks(padpos):
        dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
        if not (dx < 0.02 or dy < 0.02 or abs(dx - dy) < 0.03):
            bad.append((net, a, b))
    return bad
