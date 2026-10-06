#!/usr/bin/env python3
"""Placement for the Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/gen_pcb_lite.py).

Same mounting holes and motor pads as the standard board (gen_pcb.py), so the 3D printed frames, deck, gears and
wheels are shared.  Differences (rev.L2):
  * a plain 65 x 100 mm board (x 17.5 .. 82.5): the width of the frames at the rear, kept all the way to the front
  * XIAO ESP32C6 soldered flat at the right edge, USB-C to the right (the socket sticks out 0.6 mm); its front row
    (ADC D0..D2 = sensors, button, IR LED enable, IN2, red LED) faces the sensors, its rear row feeds only the
    motor driver behind it (crossing those lines made the autorouter fail)
  * 3 x LBR-127HLD sensors at x = 38 / 50 / 62, their 6 resistors on an even 6 mm grid (3.5 mm between bodies)
  * the skid sits at (50, 11), 7 mm behind the centre sensor (a taller skid lifts the front: the sensor is 5.6 mm tall)
  * motor driver lying across in front of the motor pads (outputs straight back), START button on the left
  * keep-outs (no tracks / vias) under the steel screw heads and around the skid's snap pin;
    the XIAO footprint brings its own (bottom test pads, chip antenna)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))   # shared modules
import pcbnew  # noqa: E402
import gen_pcb as G  # noqa: E402
from kicad_env import VARIANT  # noqa: E402

assert VARIANT == "lite", "run with LT2_VARIANT=lite"

SENSOR_Y = G.SENSOR_Y
SENSOR_X = [38.0, 50.0, 62.0]
SKID_HOLE = (50.0, 11.0)
FRAME_HOLES = G.FRAME_HOLES
# Board outline (rev.L2b): a plain 65 x 100 mm rectangle, x 17.5 .. 82.5 (the width the gearbox frames need at the
# rear).  The wheels, gears and the frames' outer axle walls stay outside it, as they did in the old rear notches.
BOARD_X0, BOARD_X1 = G.NOTCH_X, G.BOARD_W - G.NOTCH_X
# XIAO: rotation 270 = USB-C to the right edge (socket face 12.05 mm from the origin -> 0.6 mm past the edge).
# Front row (facing the sensors), left -> right: D6 D5 D4 D3 D2 D1 D0;  rear row: D7 D8 D9 D10 3V3 GND 5V.
# Pads reach 10.82 mm to the front / rear.  The antenna end (+ its copper keep-out) points to the left.
XIAO_C = (BOARD_X1 + 0.6 - 12.05, 35.0)

P = G.PLACE
P.clear()
vert, horiz = G.place_r_vertical, G.place_r_horizontal

# sensors (bottom side) + their resistors (left = 100R for the IR LED, right = 10k pull-up)
# (rotation 180 after the flip: LED (A, K) on the left next to its 100R, photo transistor (E, C) on the right)
for i, x in enumerate(SENSOR_X):
    P["PS%d" % (i + 1)] = (x, SENSOR_Y, 180, "B")
# resistors on an even 6 mm grid (3.5 mm between the bodies), the skid between PS2's two resistors
R_X = {"R1": 32.0, "R4": 38.0, "R2": 44.0, "R5": 56.0, "R3": 62.0, "R6": 68.0}
for ref, x in R_X.items():
    vert(ref, x, 18.16)                   # pad 1 (+3V3) at the rear, pad 2 (sensor) at y 8.0

# IR LED switch: front-left corner
P["Q1"] = (20.5, 4.5, 0, "F")
vert("R7", 26.0, 18.16)                   # pad 2 (Q1 base) at the front

P["U1"] = (XIAO_C[0], XIAO_C[1], 270, "F")

# motor driver lying across the board in front of the motor pads: inputs (front row) face the XIAO and the
# outputs (rear row: OUT2 OUT1 OUT3 OUT4 VM VM from the left) run straight back to M1 / M2
P["U2"] = (38.0, 50.0, 270, "F")
P["C1"] = (51.5, 51.0, 0, "F")            # VBAT bulk right next to the VM pins
P["J1"] = (62.5, 51.5, 0, "F")            # battery (red = + left); clear of the frame tower at (70, 62)
P["D1"] = (80.8, 48.0, 180, "F")          # K (VSYS) right, next to the XIAO's 5V pin; A (VBAT) left
# motor pads + 0.1uF caps (in the frames' cut-outs)
P["M1"] = (45.58, 61.5, 180, "F")
P["M2"] = (59.5, 61.5, 180, "F")
P["C3"] = (41.79, 57.5, 0, "F")
P["C4"] = (55.71, 57.5, 0, "F")

# left side: START button and the VSYS hold-up cap
P["SW1"] = (20.0, 24.5, 0, "F")
P["C2"] = (21.0, 44.5, 0, "F")
# red LED next to the XIAO (left of the antenna keep-out): LED1 (D6) is a short trace into R8's front pad
P["R8"] = (54.5, 27.5, 270, "F")          # pad 1 (LED1) at the front, pad 2 at y 37.66
P["D2"] = (54.5, 42.5, 90, "F")           # A (pad 2) at y 39.96 next to R8, K at y 42.5

# mounting holes: gearbox frames + skid
for _i, (_x, _y) in enumerate(FRAME_HOLES + [SKID_HOLE]):
    P["H%d" % (_i + 1)] = (_x, _y, 0, "F")


def add_outline_lite(board):
    """Rounded 65 x 100 mm rectangle."""
    r = 2.0
    x0, x1, y0, y1 = BOARD_X0, BOARD_X1, 0.0, G.BOARD_L

    def seg(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(G.P(xa, ya))
        s.SetEnd(G.P(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(G.mm(0.1))
        board.Add(s)

    def arc(cx, cy, sx, sy, ex, ey):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        mx, my = (sx + ex) / 2 - cx, (sy + ey) / 2 - cy
        k = r / math.hypot(mx, my)
        s.SetArcGeometry(G.P(sx, sy), G.P(cx + mx * k, cy + my * k), G.P(ex, ey))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(G.mm(0.1))
        board.Add(s)

    arc(x0 + r, y0 + r, x0, y0 + r, x0 + r, y0)
    seg(x0 + r, y0, x1 - r, y0)
    arc(x1 - r, y0 + r, x1 - r, y0, x1, y0 + r)
    seg(x1, y0 + r, x1, y1 - r)
    arc(x1 - r, y1 - r, x1, y1 - r, x1 - r, y1)
    seg(x1 - r, y1, x0 + r, y1)
    arc(x0 + r, y1 - r, x0 + r, y1, x0, y1 - r)
    seg(x0, y1 - r, x0, y0 + r)


G.add_outline = add_outline_lite


def add_keepout(board, cx, cy, r, layer, name):
    """No tracks / vias inside a circle (copper pour is allowed: it is GND only)."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(layer)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(24):
        a = 2 * math.pi * k / 24
        ol.Append(G.mm(G.OX + cx + r * math.cos(a)), G.mm(G.OY + cy + r * math.sin(a)))
    board.Add(z)


def main():
    G.main()
    b = pcbnew.LoadBoard(G.PCB)
    # steel pan heads (5.5 mm) of the M3x20 sit on the bottom; the snap pin of the skid comes out on the top
    for x, y in FRAME_HOLES:
        add_keepout(b, x, y, 3.5, pcbnew.B_Cu, "screw head")
    add_keepout(b, SKID_HOLE[0], SKID_HOLE[1], 3.6, pcbnew.F_Cu, "skid pin")
    pcbnew.SaveBoard(G.PCB, b)
    print("keep-outs added", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
