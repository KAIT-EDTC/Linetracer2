#!/usr/bin/env python3
"""Post-process the routed board (run with scripts/kpy after route_pcb.py import).

1. remove GND tracks/vias that the GND pours make redundant
2. silkscreen: reference positions, kid-friendly labels (EN + JP), assembly outlines
3. embed the Japanese font, refill zones, save
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
from kicad_env import KDIR, PROJ  # noqa: E402
import gen_pcb as G  # noqa: E402  (geometry constants + helpers)

PCB = os.path.join(KDIR, PROJ + ".kicad_pcb")
JP = "Noto Sans CJK JP"
P, mm = G.P, G.mm


def unconnected(b, filler):
    filler.Fill(b.Zones())
    b.BuildConnectivity()
    return b.GetConnectivity().GetUnconnectedCount(False)


GRAVEYARD = []


def prune_gnd(b):
    filler = pcbnew.ZONE_FILLER(b)
    base = unconnected(b, filler)
    gnd = b.FindNet("GND").GetNetCode()
    items = [t for t in b.GetTracks() if t.GetNetCode() == gnd]
    items.sort(key=lambda t: -(t.GetLength() if t.GetClass() == "PCB_TRACK" else 0))
    removed = 0
    for t in items:
        b.Remove(t)
        GRAVEYARD.append(t)          # keep python refs alive (avoids SWIG double free)
        if unconnected(b, filler) > base:
            b.Add(t)
        else:
            removed += 1
    print("GND items removed: %d of %d (unconnected=%d)" % (removed, len(items), unconnected(b, filler)))


def text(b, s, x, y, size=1.0, layer=pcbnew.F_SilkS, angle=0, jp=False, bold=False, just=None):
    t = G.add_text(b, s, x, y, size=size, layer=layer, angle=angle, bold=bold,
                   mirror=(layer == pcbnew.B_SilkS), just=just)
    if jp:
        t.SetFontProp(JP)
        t.SetBold(True)
        t.SetTextThickness(mm(0.15))
    return t


def line(b, x1, y1, x2, y2, layer=pcbnew.F_SilkS, w=0.15):
    G.add_line(b, x1, y1, x2, y2, layer=layer, w=w)


def rect(b, x1, y1, x2, y2, layer=pcbnew.F_SilkS, w=0.15):
    for a in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
        line(b, *a, layer=layer, w=w)


FP = {}


def set_ref(b, ref, x=None, y=None, size=1.0, angle=0, visible=True):
    fp = FP[ref]
    f = fp.Reference()
    f.SetVisible(visible)
    if x is not None:
        f.SetPosition(P(x, y))
    f.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    f.SetTextThickness(mm(max(0.15, size * 0.15)))
    f.SetTextAngleDegrees(angle)
    return f


def set_val(b, ref, x=None, y=None, size=None, visible=True, text_=None):
    fp = FP[ref]
    f = fp.Value()
    f.SetVisible(visible)
    if x is not None:
        f.SetPosition(P(x, y))
    if size:
        f.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    if text_:
        f.SetText(text_)
    return f


def silk(b):
    # NOTE: run only once on a freshly routed board (build_pcb.py does this).
    FP.clear()
    FP.update({f.GetReference(): f for f in b.GetFootprints()})
    # ---- references --------------------------------------------------------
    set_ref(b, "Q1", 10.4, 6.6, 0.8)
    set_ref(b, "R15", visible=False)
    set_ref(b, "BZ1", 6.6, 29.0, 0.8)
    set_ref(b, "U2", 49.5, 25.3, 1.0)
    set_ref(b, "C4", 35.6, 22.8, 0.8, angle=90)
    set_ref(b, "U1", 6.0, 37.0, 1.0)
    set_ref(b, "U3", 61.0, 47.5, 1.0, angle=90)
    set_ref(b, "C1", 76.0, 29.6, 0.8)
    set_ref(b, "C2", 76.0, 38.6, 0.8)
    set_ref(b, "J1", 70.4, 55.0, 0.8)
    set_ref(b, "C3", 90.5, 47.4, 0.8)
    for ref, lab, x in (("D4", "PWR", 80.0), ("D2", "LED1", 86.0), ("D3", "LED2", 92.0)):
        set_ref(b, ref, visible=False)
        text(b, "%s:%s" % (ref, lab), x, 21.3, 0.8)
    set_ref(b, "SW1", 92.0, 1.3, 0.8)
    set_ref(b, "SW2", 92.0, 11.2, 0.8)
    set_ref(b, "J2", 6.8, 54.8, 0.8)
    set_ref(b, "J3", 63.77, 19.6, 0.8)
    set_ref(b, "M1", 43.0, 67.0, 1.0)
    set_ref(b, "M2", 57.0, 67.0, 1.0)
    set_ref(b, "C5", 39.8, 57.0, 0.8, angle=90)
    set_ref(b, "C6", 53.7, 57.0, 0.8, angle=90)
    set_val(b, "D1", 80.1, 45.9, 0.8, text_="1N5819")
    for i in range(6):
        fp = FP["PS%d" % (i + 1)]
        f = fp.Reference()
        f.SetPosition(P(G.SENSOR_X[i], G.SENSOR_Y + 3.2))
        f.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        f.SetTextThickness(mm(0.15))
        fp.Value().SetVisible(False)

    # ---- top side labels -----------------------------------------------------
    for i, x in enumerate(G.SENSOR_X):
        text(b, "S%d" % (i + 1), x, 6.35, 0.8)
    text(b, "FRONT", 50.0, 8.6, 0.8)
    text(b, "まえ", 50.0, 10.6, 1.4, jp=True)
    text(b, "START", 85.8, 5.5, 0.8, angle=90)
    text(b, "SELECT", 85.8, 15.5, 0.8, angle=90)
    text(b, "スタート", 92.0, 10.0, 1.4, jp=True)
    text(b, "せんたく", 92.0, 19.8, 1.3, jp=True)
    text(b, "USB", 2.3, 45.0, 0.8, angle=90)
    text(b, "Raspberry Pi Pico", 27.0, 43.0, 1.2)
    text(b, "(Pico 2 OK)", 27.0, 45.2, 0.8)
    text(b, "BAT 3xAA", 76.25, 58.7, 0.8)
    text(b, "でんち", 76.25, 60.5, 1.4, jp=True)
    text(b, "I2C", 15.0, 57.0, 0.8)
    for k, s in enumerate(("G", "V", "C", "D")):
        text(b, s, 3.0 + 2.54 * k, 59.2, 0.8)
    text(b, "EXT", 63.8, 29.6, 0.8)
    # module pin hints
    text(b, "M1 LEFT", 43.0, 68.8, 0.8)
    text(b, "M2 RIGHT", 57.0, 68.8, 0.8)
    text(b, "ひだり", 35.0, 74.6, 1.4, jp=True)
    text(b, "みぎ", 65.0, 74.6, 1.4, jp=True)

    # ---- motor outlines (assembly guide, top side) ---------------------------
    my, ay = G.MOTOR_Y, G.AXLE_Y
    for sgn in (-1, 1):
        # motor body 28.5 x 20.1 (rear end-cap at the centre, front face 29.5 mm out)
        x1, x2 = sorted((50.0 + sgn * 1.0, 50.0 + sgn * 29.5))
        rect(b, x1, my - 10.05, x2, my + 10.05, w=0.12)
    text(b, "MOTOR L (FA-130)", 35.0, my - 4.0, 0.9)
    text(b, "MOTOR R (FA-130)", 65.0, my - 4.0, 0.9)
    text(b, "AXLE (gear + wheel in the notch)", 50.0, ay, 0.8)
    line(b, 19.0, ay, 30.0, ay, w=0.12)
    line(b, 70.0, ay, 81.0, ay, w=0.12)
    text(b, "Gearbox frame: M3 x4  (see docs)", 50.0, 92.6, 0.8)
    text(b, "Battery box sits on top of the motors", 50.0, 94.6, 0.8)

    # ---- bottom side ----------------------------------------------------------
    BL = pcbnew.B_SilkS
    text(b, "Linetracer2", 50.0, 80.0, 3.0, layer=BL, bold=True)
    text(b, "rev.A1  2026-10  EDTC", 50.0, 84.5, 1.2, layer=BL)
    text(b, "Raspberry Pi Pico + TC78H653FTG + FA-130 x2", 50.0, 87.5, 1.0, layer=BL)
    text(b, "子ども向けライントレーサー教材", 50.0, 92.0, 2.6, layer=BL, jp=True)
    text(b, "SENSOR SIDE: LBR-123F x6  (lens to the floor)", 50.0, 11.5, 0.9, layer=BL)
    text(b, "センサーはこちらの面に付ける", 50.0, 14.2, 1.6, layer=BL, jp=True)
    text(b, "SKID", 50.0, 7.6, 0.8, layer=BL)


def main(step):
    b = pcbnew.LoadBoard(PCB)
    if step == "prune":
        prune_gnd(b)
    else:
        silk(b)
        b.EmbedFonts()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("post %s done" % step, flush=True)
    os._exit(0)                      # skip interpreter teardown (SWIG objects)


if __name__ == "__main__":
    # run as two separate processes: "prune" then "silk"
    main(sys.argv[1] if len(sys.argv) > 1 else "silk")
