#!/usr/bin/env python3
"""Placement for the Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/gen_pcb_lite.py).

The positions themselves are in layout_lite.py (shared with the hand routing in route_lite.py).
Same mounting holes and motor pads as the standard board (gen_pcb.py), so the 3D printed frames, deck, gears and
wheels are shared.  This file adds the board outline and the keep-outs:
  * no tracks / vias under the steel screw heads (bottom) and around the caster's snap pin (top);
    the XIAO footprint brings its own (chip antenna)
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

import layout_lite as LL  # noqa: E402  (placement + routes, pure data)

SENSOR_Y = LL.SENSOR_Y
SENSOR_X = LL.SENSOR_X
SKID_HOLE = LL.SKID_HOLE
FRAME_HOLES = LL.FRAME_HOLES
# Board outline: a plain 65 x 100 mm rectangle, x 17.5 .. 82.5 (the width the gearbox frames need at the rear).
# The wheels, gears and the frames' outer axle walls stay outside it.
BOARD_X0, BOARD_X1 = G.NOTCH_X, G.BOARD_W - G.NOTCH_X
XIAO_C = LL.XIAO_C

P = G.PLACE
P.clear()
P.update(LL.PLACE)


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
    for kind, x, y, r, layer in LL.KEEPOUTS:
        add_keepout(b, x, y, r, pcbnew.B_Cu if layer == "B" else pcbnew.F_Cu,
                    "screw head" if layer == "B" else "caster pin")
    pcbnew.SaveBoard(G.PCB, b)
    print("keep-outs added", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
