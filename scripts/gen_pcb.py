#!/usr/bin/env python3
"""Build hardware/kicad/Linetracer2.kicad_pcb from the netlist (run with scripts/kpy).

Stage 1 (this file): outline, placement, mounting holes, silkscreen.
Routing is done by route_pcb.py (Freerouting) afterwards.

Board coordinates: x -> right, y -> rear.  (0,0) = front-left corner of the board.
The robot drives towards -y (up on the screen).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
import sexpr  # noqa: E402
from kicad_env import KDIR, LIBDIR, LIBNICK, PROJ  # noqa: E402

OX, OY = 100.0, 50.0            # board origin on the KiCad page
FPLIB = "/app/extensions/Library/footprints"
PCB = os.path.join(KDIR, PROJ + ".kicad_pcb")
NET = os.path.join(KDIR, "reports", PROJ + ".net")

# ---------------------------------------------------------------- geometry
BOARD_W, BOARD_L = 100.0, 100.0
NOTCH_X = 17.5         # rear notch from each side: wheel (x -1..7) + outer axle wall + 40T gear (Ø21)
NOTCH_Y = 70.0         # notch starts here (wheel dia 32, axle y=88)
AXLE_Y = 88.0
MOTOR_Y = 76.0         # motor shaft line (axle - 12 mm, 8T->40T m0.5)
SENSOR_Y = 4.0
SENSOR_X = [20.0 + 12.0 * i for i in range(6)]
FRAME_HOLES = [(30.0, 62.0), (30.0, 96.0), (70.0, 62.0), (70.0, 96.0)]
SKID_HOLE = (50.0, SENSOR_Y)


def mm(v):
    return pcbnew.FromMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def lib_path(nick):
    if nick == LIBNICK:
        return os.path.join(LIBDIR, LIBNICK + ".pretty")
    return os.path.join(FPLIB, nick + ".pretty")


# ---------------------------------------------------------------- netlist
def read_netlist():
    n = sexpr.parse(open(NET).read())
    comps = {}
    for c in sexpr.find_all(sexpr.find(n, "components"), "comp"):
        ref = sexpr.find(c, "ref")[1]
        fields = {}
        fl = sexpr.find(c, "fields")
        for f in sexpr.find_all(fl, "field") if fl else []:
            name = sexpr.find(f, "name")[1]
            if name not in ("Footprint", "Datasheet") and len(f) > 2 and not isinstance(f[2], list):
                fields[name] = f[2]
        d = sexpr.find(c, "description")
        if d is not None:
            fields["Description"] = d[1]
        ds = sexpr.find(c, "datasheet")
        if ds is not None and len(ds) > 1:
            fields["Datasheet"] = ds[1]
        flags = {sexpr.find(p, "name")[1] for p in sexpr.find_all(c, "property")}
        comps[ref] = {
            "dnp": "dnp" in flags,
            "no_bom": "exclude_from_bom" in flags,
            "value": sexpr.find(c, "value")[1],
            "footprint": sexpr.find(c, "footprint")[1],
            "tstamp": sexpr.find(c, "tstamps")[1],
            "fields": fields,
        }
    pinnet = {}
    for net in sexpr.find_all(sexpr.find(n, "nets"), "net"):
        name = sexpr.find(net, "name")[1]
        for node in sexpr.find_all(net, "node"):
            pinnet[(sexpr.find(node, "ref")[1], sexpr.find(node, "pin")[1])] = name
    return comps, pinnet


# ---------------------------------------------------------------- placement
# ref: (x, y, rotation_deg, side)   x/y = footprint origin in board coordinates
PLACE = {}


def place_r_vertical(ref, x, y_rear):
    """Axial resistor/diode, pad1 at the rear (y_rear), pad2 10.16 mm in front."""
    PLACE[ref] = (x, y_rear, 90, "F")


def place_r_horizontal(ref, x_left, y, flip_dir=False):
    """pad1 at x_left, pad2 at x_left + 10.16 (or reversed when flip_dir)."""
    if flip_dir:
        PLACE[ref] = (x_left + 10.16, y, 180, "F")
    else:
        PLACE[ref] = (x_left, y, 0, "F")


# sensors (bottom side) + their resistors
for i, x in enumerate(SENSOR_X):
    PLACE["PS%d" % (i + 1)] = (x, SENSOR_Y, 0, "B")
    place_r_vertical("R%d" % (i + 1), x - 2.54, 18.16)      # 100R  : +3V3 -> LED anode
    place_r_vertical("R%d" % (i + 7), x + 2.54, 18.16)      # 10k   : +3V3 -> collector

# analog mux: rotation 90 -> rear row pins 1..8 (left->right), front row pins 16..9
PLACE["U2"] = (40.64, 29.12, 90, "F")
PLACE["C4"] = (37.6, 21.5, 270, "F")          # VDD bypass, next to pin 16

# Raspberry Pi Pico: USB to the left edge, pin 1 at bottom-left
PLACE["U1"] = (3.0, 52.0, 90, "F")

# motor driver module (origin = module centre)
PLACE["U3"] = (61.0, 43.0, 0, "F")
PLACE["C1"] = (70.25, 33.0, 0, "F")           # 470uF VBAT bulk next to VM pins (+ pad left)
# motor pads in front of the motors, between the gearbox feet
PLACE["M1"] = (45.58, 61.5, 180, "F")      # relief holes behind (towards the motor)
PLACE["M2"] = (59.5, 61.5, 180, "F")
PLACE["C5"] = (41.79, 57.0, 0, "F")
PLACE["C6"] = (55.71, 57.0, 0, "F")

# power input (right side, close to the motor driver)
PLACE["J1"] = (75.0, 53.0, 0, "F")
PLACE["D1"] = (75.0, 48.0, 0, "F")           # pad1 = K (VSYS) left, pad2 = A (VBAT) right
PLACE["C2"] = (70.25, 42.0, 0, "F")           # VSYS hold-up
place_r_vertical("R13", 94.0, 51.16)          # VBAT -> VBAT_SENSE
place_r_vertical("R14", 97.0, 51.16)          # VBAT_SENSE -> GND
PLACE["C3"] = (90.5, 43.0, 270, "F")

# LEDs (power / LED1 / LED2) + resistors, buttons in the front-right corner
PLACE["D4"] = (78.73, 24.0, 0, "F")
PLACE["D2"] = (84.73, 24.0, 0, "F")
PLACE["D3"] = (90.73, 24.0, 0, "F")
place_r_vertical("R19", 80.0, 37.66)
place_r_vertical("R16", 86.0, 37.66)
place_r_vertical("R17", 92.0, 37.66)
PLACE["SW1"] = (88.75, 3.25, 0, "F")
PLACE["SW2"] = (88.75, 13.25, 0, "F")

# LED switch + buzzer (front-left corner)
PLACE["Q1"] = (2.0, 8.0, 0, "F")
place_r_horizontal("R15", 2.0, 13.0)
PLACE["BZ1"] = (2.8, 24.5, 0, "F")
place_r_vertical("R18", 14.4, 30.4)

# mounting holes (in the schematic as H1..H5): gearbox frames + front skid
for _i, (_x, _y) in enumerate(FRAME_HOLES + [SKID_HOLE]):
    PLACE["H%d" % (_i + 1)] = (_x, _y, 0, "F")

# expansion headers
PLACE["J2"] = (3.0, 57.0, 90, "F")            # I2C, left rear strip (OLED order GND VCC SCL SDA)
PLACE["J3"] = (62.5, 22.0, 0, "F")           # EXT 2x3, between mux and C1          # EXT, left rear strip


def add_outline(board):
    r = 2.0

    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1))
        s.SetEnd(P(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(cx, cy, sx, sy, ex, ey):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        mx = cx + (((sx + ex) / 2 - cx) / math.hypot((sx + ex) / 2 - cx, (sy + ey) / 2 - cy)) * r
        my = cy + (((sy + ey) / 2 - cy) / math.hypot((sx + ex) / 2 - cx, (sy + ey) / 2 - cy)) * r
        s.SetArcGeometry(P(sx, sy), P(mx, my), P(ex, ey))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    W, L, nx, ny = BOARD_W, BOARD_L, NOTCH_X, NOTCH_Y
    # front edge with rounded corners
    arc(r, r, 0, r, r, 0)
    seg(r, 0, W - r, 0)
    arc(W - r, r, W - r, 0, W, r)
    seg(W, r, W, ny - r)
    arc(W - r, ny - r, W, ny - r, W - r, ny)          # outer corner before notch
    seg(W - r, ny, W - nx, ny)
    seg(W - nx, ny, W - nx, L - r)
    arc(W - nx - r, L - r, W - nx, L - r, W - nx - r, L)
    seg(W - nx - r, L, nx + r, L)
    arc(nx + r, L - r, nx + r, L, nx, L - r)
    seg(nx, L - r, nx, ny)
    seg(nx, ny, r, ny)
    arc(r, ny - r, r, ny, 0, ny - r)
    seg(0, ny - r, 0, r)


def add_text(board, txt, x, y, size=1.2, layer=None, angle=0, bold=False, thick=None, mirror=False, just=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(P(x, y))
    t.SetLayer(layer if layer is not None else pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick if thick else max(0.15, size * 0.15)))
    t.SetTextAngleDegrees(angle)
    if bold:
        t.SetBold(True)
    if mirror:
        t.SetMirrored(True)
    if just == "left":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif just == "right":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    board.Add(t)
    return t


def add_line(board, x1, y1, x2, y2, layer=None, w=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x1, y1))
    s.SetEnd(P(x2, y2))
    s.SetLayer(layer if layer is not None else pcbnew.F_SilkS)
    s.SetWidth(mm(w))
    board.Add(s)


def style_fields(fp, ref):
    """Kid friendly silkscreen: values printed for R/C/LED, refs for the rest."""
    refl, val = fp.Reference(), fp.Value()
    for f in (refl, val):
        f.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        f.SetTextThickness(mm(0.15))
    kind = "".join(ch for ch in ref if ch.isalpha())
    rot = fp.GetOrientationDegrees()
    c = fp.GetBoundingBox(False).GetCenter()
    if kind == "R" or (kind == "D" and ref == "D1"):
        # value printed on the body, reference hidden (see assembly drawing)
        val.SetLayer(pcbnew.F_SilkS)
        val.SetVisible(True)
        val.SetPosition(c)
        val.SetTextAngleDegrees(90 if abs(rot) in (90, 270) else 0)
        val.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9)))
        refl.SetVisible(False)
        if ref == "D1":
            val.SetText("1N5819")
            val.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    else:
        val.SetVisible(False)


def apply_netlist(board, comps, pinnet, nets=None):
    """Like 'Update PCB from Schematic' (without moving anything): value, path, fields, pad nets."""
    if nets is None:
        nets = {}
        for name in sorted(set(pinnet.values())):
            ni = board.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, name)
                board.Add(ni)
            nets[name] = ni
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = comps.get(ref)
        if c is None:
            continue
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
        if c["dnp"]:
            fp.SetDNP(True)
        if c["no_bom"]:
            fp.SetExcludedFromBOM(True)
        for k, v in c["fields"].items():
            fp.SetField(k, v)
            fp.GetField(k).SetVisible(False)
        for pad in fp.Pads():
            n = pinnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(nets[n])
    return nets


def main():
    comps, pinnet = read_netlist()
    if os.path.exists(PCB):
        os.remove(PCB)
    board = pcbnew.NewBoard(PCB)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))

    nets = {}
    for name in sorted(set(pinnet.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    missing = [r for r in comps if r not in PLACE]
    assert not missing, "no placement for %s" % missing

    fps = {}
    for ref, c in sorted(comps.items()):
        nick, name = c["footprint"].split(":")
        fp = pcbnew.FootprintLoad(lib_path(nick), name)
        assert fp is not None, c["footprint"]
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
        board.Add(fp)
        x, y, rot, side = PLACE[ref]
        fp.SetPosition(P(x, y))
        if side == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            n = pinnet.get((ref, pad.GetNumber()))
            if n and n in nets:
                pad.SetNet(nets[n])
        style_fields(fp, ref)
        fps[ref] = fp

    apply_netlist(board, comps, pinnet, nets)
    for ref, fp in fps.items():
        if ref.startswith("H"):
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
    add_outline(board)
    pcbnew.SaveBoard(PCB, board)

    # report pad positions of a few parts for sanity
    for ref in [r for r in ("PS1", "U2", "U1", "U3", "Q1") if r in fps]:
        fp = fps[ref]
        pads = sorted(fp.Pads(), key=lambda p: int(p.GetNumber()) if p.GetNumber().isdigit() else 0)
        print(ref, [(p.GetNumber(), round(pcbnew.ToMM(p.GetPosition().x) - OX, 2),
                     round(pcbnew.ToMM(p.GetPosition().y) - OY, 2), p.GetNetname()) for p in pads[:8]])
    print("saved", PCB)


if __name__ == "__main__":
    main()
