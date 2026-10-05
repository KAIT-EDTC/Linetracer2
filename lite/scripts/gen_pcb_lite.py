#!/usr/bin/env python3
"""Placement for the Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/gen_pcb_lite.py).

Same outline, mounting holes, motor area and power block as the standard board (gen_pcb.py), so
all 3D printed parts (frames, deck, gears, wheels, skid) are shared.  Differences:
  * Pico soldered flat: 1 mm closer to the left edge so the USB plug body clears the board edge
  * 3 sensors at x = 38 / 50 / 62 (12 mm apart, centred)
  * the skid moves from (50, 4) to (50, 11): the centre sensor sits where the skid used to be
  * keep-outs (no tracks / vias) under the steel screw heads and around the skid's snap pin
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
PICO_PIN1 = (2.0, 52.0)          # pin 1 (rear row); Pico edge 0.63 mm and USB socket 0.67 mm past the board edge
# footprint origin = Pico centre; rotation 90 puts the USB end to the left (-x) and pins 1..20 on the rear row
PICO_C = (PICO_PIN1[0] + 24.13, PICO_PIN1[1] - 8.89)

P = G.PLACE
P.clear()
vert, horiz = G.place_r_vertical, G.place_r_horizontal

# sensors (bottom side) + their resistors (left = 100R for the IR LED, right = 10k pull-up)
for i, x in enumerate(SENSOR_X):
    P["PS%d" % (i + 1)] = (x, SENSOR_Y, 0, "B")
# PS1 / PS3: right behind the sensor.  PS2: spread to x 44 / 56 to leave room for the skid at (50, 11)
for i, (xl, xr) in enumerate(((35.46, 40.54), (44.0, 56.0), (59.46, 64.54))):
    vert("R%d" % (i + 1), xl, 18.16)       # 100R : +3V3 -> LED anode
    vert("R%d" % (i + 4), xr, 18.16)       # 10k  : +3V3 -> collector (SENSn)

P["U1"] = (PICO_C[0], PICO_C[1], 90, "F")

# motor driver module + power input: same as the standard board
P["U2"] = (61.0, 43.0, 0, "F")
P["C1"] = (70.25, 33.0, 0, "F")
P["C2"] = (70.25, 42.0, 0, "F")
P["J1"] = (75.0, 53.0, 0, "F")
P["D1"] = (75.0, 48.0, 0, "F")
# motor pads; the 0.1uF caps sit 1 mm further back than on the standard board (Pico pads are longer now)
P["M1"] = (45.58, 61.5, 180, "F")
P["M2"] = (59.5, 61.5, 180, "F")
P["C3"] = (41.79, 58.0, 0, "F")
P["C4"] = (55.71, 58.0, 0, "F")

# button (front-right corner) and the one LED
P["SW1"] = (88.75, 3.25, 0, "F")
P["D2"] = (84.73, 24.0, 0, "F")
vert("R8", 86.0, 37.66)

# IR LED switch (front-left corner)
P["Q1"] = (2.0, 8.0, 0, "F")
horiz("R7", 2.0, 13.0)

# mounting holes: gearbox frames + skid
for _i, (_x, _y) in enumerate(FRAME_HOLES + [SKID_HOLE]):
    P["H%d" % (_i + 1)] = (_x, _y, 0, "F")

# I2C holes (no header in the kit), 2.2 mm behind the Pico pads
P["J2"] = (3.0, 58.6, 90, "F")


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
    # J2 is holes only in the kit: hide its pin-header 3D model so the renders show the real board
    for fp in b.GetFootprints():
        if fp.GetReference() == "J2":
            ms = fp.Models()             # (iterating gives copies: write each one back)
            for i in range(len(ms)):
                m = ms[i]
                m.m_Show = False
                ms[i] = m
    pcbnew.SaveBoard(G.PCB, b)
    print("keep-outs added", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
