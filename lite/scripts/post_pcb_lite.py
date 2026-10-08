#!/usr/bin/env python3
"""Kid-friendly silkscreen of the routed Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/post_pcb_lite.py silk).

Only SYMBOLS on the board (lower elementary school): build-order numbers, +/- and polarity pictures, the 3rd colour
band of each resistor, short part names.  What they mean and the steps are in the assembly manual
(lite/docs/assembly.md).  Build order (one kind of part per step, lowest parts first):
   1 ちゃ resistors (100) x4   2 だいだい resistors (10k) x3   3 あか resistors (1k) x2   4 diode   5 0.1uF caps x3
   6 transistor   7 button   8 buzzer   9 battery connector   10 motor driver   11 XIAO
   12 full-colour LEDs x5 (8.7 mm tall)   13 470uF caps (the tallest: last, so they do not get in the way of the
   XIAO's joints)   14 sensors (bottom)   15 motors (after the frames are on)
Japanese text is 1.3 mm or bigger (smaller kana fail the stroke-width check); symbols use the stroke font.
NOTE: run only once on a freshly routed board (build_pcb.py does this).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))   # shared modules
import pcbnew  # noqa: E402
import post_pcb as PP  # noqa: E402  (helpers: text, line, rect, set_ref, set_val, prune_gnd)
import gen_pcb as G  # noqa: E402
import layout_lite as LL  # noqa: E402

text, line, rect = PP.text, PP.line, PP.rect
F, BL = pcbnew.F_SilkS, pcbnew.B_SilkS

# 3rd colour band of the resistors (all three values are brown-black-?-gold, only the 3rd band differs)
BAND3 = {"100": "ちゃ", "10k": "だいだい", "1k": "あか"}
STEP = {"100": 1, "10k": 2, "1k": 3}


def pad_xy(fp, num):
    for pad in fp.Pads():
        if pad.GetNumber() == num:
            q = pad.GetPosition()
            return pcbnew.ToMM(q.x) - G.OX, pcbnew.ToMM(q.y) - G.OY
    raise KeyError(num)


def circle(b, x, y, r, layer=F, w=0.15, fill=False):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(G.P(x, y))
    s.SetEnd(G.P(x + r, y))
    s.SetLayer(layer)
    s.SetWidth(G.mm(w))
    if fill:
        s.SetFilled(True)
    b.Add(s)


def poly(b, pts, layer=F):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyPoints([G.P(x, y) for x, y in pts])
    s.SetLayer(layer)
    s.SetWidth(G.mm(0.1))
    s.SetFilled(True)
    b.Add(s)


def num(b, n, x, y, layer=F, r=None):
    """Build-order number: a silk circle with the digit inside (stroke font; the CJK font's circled digits are
    too thin for the silkscreen rules).  Two-digit numbers get a bigger circle so that they stay readable."""
    if r is None:
        r = 1.15 if n < 10 else 1.35
    circle(b, x, y, r, layer)
    text(b, str(n), x, y, 1.2 if n < 10 else 1.0, layer=layer)


def hide_fp_texts(fp, words):
    """Move footprint texts from the silkscreen to the fab layer (KiCad does not keep 'hidden' on footprint
    user texts); they stay in the assembly drawing."""
    for item in fp.GraphicalItems():
        if item.GetClass() == "PCB_TEXT":
            item = item.Cast()
            if item.GetText() in words and item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                item.SetLayer(pcbnew.F_Fab if item.GetLayer() == pcbnew.F_SilkS else pcbnew.B_Fab)


GRAVEYARD = []                       # removed footprint items stay referenced (avoids SWIG double frees)


def fp_frame(fp):
    o = fp.GetPosition()
    return pcbnew.ToMM(o.x) - G.OX, pcbnew.ToMM(o.y) - G.OY, math.radians(fp.GetOrientationDegrees())


def fp_xy(frame, lx, ly):
    """footprint-local (top side) -> board coordinates"""
    ox, oy, a = frame
    return ox + lx * math.cos(a) + ly * math.sin(a), oy - lx * math.sin(a) + ly * math.cos(a)


def electrolytic(b, fp, plus_outside=True):
    """CP_Radial_D8.0mm: the hatched (black) half is the minus side, like the stripe on the can.  Redraw the hatch
    with two white "-" bars left open in it (the real stripe has minus signs too) and put two big "+" in the white
    half."""
    frame = fp_frame(fp)
    ox, oy, a = frame
    hatch = []
    for item in fp.GraphicalItems():
        if item.GetClass() == "PCB_SHAPE" and item.GetLayer() == pcbnew.F_SilkS:
            item = item.Cast()
            if item.GetShape() != pcbnew.SHAPE_T_SEGMENT:
                continue
            s, e = item.GetStart(), item.GetEnd()
            dxs, dys = pcbnew.ToMM(s.x) - G.OX - ox, pcbnew.ToMM(s.y) - G.OY - oy
            dxe, dye = pcbnew.ToMM(e.x) - G.OX - ox, pcbnew.ToMM(e.y) - G.OY - oy
            lx = dxs * math.cos(a) - dys * math.sin(a)           # inverse rotation
            lxe = dxe * math.cos(a) - dye * math.sin(a)
            if lx > 1.7 and abs(lx - lxe) < 0.01:
                hatch.append(item)                                # a hatch line (vertical, minus half)
            elif lx < -1.5 and lxe < -1.5:
                hatch.append(item)                                # KiCad's small "+" outside the circle
    for item in hatch:
        fp.Remove(item)
        GRAVEYARD.append(item)
    # new hatch in BOARD coordinates, so the "-" gaps stay horizontal whatever the rotation:
    # chords perpendicular to u (centre -> pad 2), minus a circle around pad 2 and two horizontal bars
    R = 4.08
    cx, cy = fp_xy(frame, 1.75, 0)
    p2x, p2y = fp_xy(frame, 3.5, 0)
    ux, uy = (p2x - cx) / 1.75, (p2y - cy) / 1.75
    vx, vy = -uy, ux
    # bars: on both sides of pad 2, across u (for C1 left/right of the pad, for C2 above/below it)
    side = (vx * 2.55, vy * 2.55)
    bars = []
    for sg in (-1, 1):
        bx, by = p2x + sg * side[0], p2y + sg * side[1]
        bars.append((bx - 0.85, by - 0.33, bx + 0.85, by + 0.33))

    def clip(x0, y0, x1, y1, r):
        """t-interval of the segment p0->p1 inside the axis-aligned rect r (Liang-Barsky)"""
        t0, t1 = 0.0, 1.0
        dx, dy = x1 - x0, y1 - y0
        for p, q in ((-dx, x0 - r[0]), (dx, r[2] - x0), (-dy, y0 - r[1]), (dy, r[3] - y0)):
            if abs(p) < 1e-12:
                if q < 0:
                    return None
            else:
                t = q / p
                if p < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        return (t0, t1) if t0 < t1 else None

    sstep = 0.07
    while sstep < R - 0.05:
        h = math.sqrt(R * R - sstep * sstep) - 0.12
        ax, ay = cx + ux * sstep - vx * h, cy + uy * sstep - vy * h
        bx2, by2 = cx + ux * sstep + vx * h, cy + uy * sstep + vy * h
        cuts = []
        d = abs(sstep - 1.75)
        if d < 1.0:                                   # pad 2: mask opening r 0.8 + 0.2
            w = math.sqrt(1.0 - d * d) / (2 * h)
            cuts.append((0.5 - w, 0.5 + w))
        for r in bars:
            c = clip(ax, ay, bx2, by2, r)
            if c:
                cuts.append(c)
        segs = [(0.0, 1.0)]
        for c0, c1 in cuts:
            segs = [q for s0, s1 in segs for q in ((s0, min(s1, c0)), (max(s0, c1), s1)) if q[1] - q[0] > 0.01]
        for s0, s1 in segs:
            line(b, ax + (bx2 - ax) * s0, ay + (by2 - ay) * s0, ax + (bx2 - ax) * s1, ay + (by2 - ay) * s1, w=0.12)
        sstep += 0.1
    for sg in (-1, 1):                                # two big "+" in the white half, beside pad 1
        px, py = fp_xy(frame, 0, 0)
        text(b, "+", px + sg * side[0] - ux * 0.1, py + sg * side[1] - uy * 0.1, 1.6, bold=True)
    # the can (8 mm) covers the circle once it is soldered: a "-" (and a "+") OUTSIDE the outline keep the
    # direction checkable afterwards
    text(b, "-", cx + ux * (R + 1.0), cy + uy * (R + 1.0), 1.6, bold=True)
    if plus_outside:
        text(b, "+", cx - ux * (R + 1.0), cy - uy * (R + 1.0), 1.6, bold=True)


def led_picture(b, px, py):
    """an LED: the LONGER leg is +"""
    line(b, px - 1.4, py, px - 1.4, py + 2.0)
    line(b, px + 1.4, py, px + 1.4, py + 2.0)
    line(b, px - 1.6, py + 2.0, px + 1.6, py + 2.0)
    a = pcbnew.PCB_SHAPE(b)
    a.SetShape(pcbnew.SHAPE_T_ARC)
    a.SetArcGeometry(G.P(px - 1.4, py), G.P(px, py - 1.4), G.P(px + 1.4, py))
    a.SetLayer(F)
    a.SetWidth(G.mm(0.15))
    b.Add(a)
    line(b, px - 0.6, py + 2.0, px - 0.6, py + 5.4)      # long leg
    line(b, px + 0.6, py + 2.0, px + 0.6, py + 3.9)      # short leg
    text(b, "+", px - 1.7, py + 4.8, 1.2)


def resistor_key(b, x0, y0):
    """Front-right corner: a resistor with its four bands, the 3rd band drawn solid, and the key
    1 = ちゃ, 2 = だいだい, 3 = あか (the step number and the colour of the 3rd band)."""
    line(b, x0, y0, x0 + 1.2, y0)                         # leads
    line(b, x0 + 8.2, y0, x0 + 9.4, y0)
    rect(b, x0 + 1.2, y0 - 1.0, x0 + 8.2, y0 + 1.0)
    for bx in (x0 + 2.2, x0 + 3.2):                        # bands 1, 2 (thin)
        line(b, bx, y0 - 1.0, bx, y0 + 1.0, w=0.3)
    poly(b, [(x0 + 3.9, y0 - 1.0), (x0 + 4.7, y0 - 1.0), (x0 + 4.7, y0 + 1.0), (x0 + 3.9, y0 + 1.0)])  # 3rd
    line(b, x0 + 7.0, y0 - 1.0, x0 + 7.0, y0 + 1.0, w=0.3)                       # gold band
    poly(b, [(x0 + 4.3, y0 + 1.35), (x0 + 3.8, y0 + 2.15), (x0 + 4.8, y0 + 2.15)])   # arrow to the 3rd band
    for i, (n, w) in enumerate(((1, "ちゃ"), (2, "だいだい"), (3, "あか"))):
        y = y0 + 4.3 + 2.9 * i
        num(b, n, x0 + 1.4, y)
        text(b, w, x0 + 3.0, y, 1.3, jp=True, just="left")


def silk(b):
    PP.FP.clear()
    PP.FP.update({f.GetReference(): f for f in b.GetFootprints()})
    FPS = PP.FP

    # ---- references / values: all hidden (the kit's papers use the assembly drawing); sensors S1..S3 on the back
    for fp in b.GetFootprints():
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
    for i, x in enumerate(LL.SENSOR_X):
        text(b, "S%d" % (i + 1), x - 6.0, LL.SENSOR_Y, 0.9, layer=BL)    # in the gap beside the sensor body
    hide_fp_texts(FPS["U2"], ("TC78H653", "VM", "GND"))   # (the footprint's VM / GND sit on C4: drawn below instead)
    hide_fp_texts(FPS["D1"], ("K",))

    # ---- front edge ----------------------------------------------------------------------------------------
    text(b, "▲まえ", 30.8, 2.2, 1.4, jp=True)
    num(b, 14, 28.6, 5.7)                                   # the sensors go on the BACK
    text(b, "うら", 31.7, 5.7, 1.3, jp=True)
    for i, x in enumerate(LL.SENSOR_X):
        text(b, "S%d" % (i + 1), x, 6.7, 0.8)

    # ---- resistors: colour of the 3rd band on the body; the key in the front-right corner -----------------------
    for ref in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R9", "R10"):
        fp = FPS[ref]
        (x1, y1), (x2, y2) = pad_xy(fp, "1"), pad_xy(fp, "2")
        w = BAND3[fp.GetValue()]
        text(b, w, (x1 + x2) / 2, (y1 + y2) / 2, 1.1 if len(w) > 2 else 1.5,
             angle=90 if abs(x1 - x2) < 0.1 else 0, jp=True)
    resistor_key(b, 70.4, 2.1)

    # ---- small parts ---------------------------------------------------------------------------------------
    num(b, 4, 80.9, 42.2)                                   # diode
    num(b, 5, 50.0, 58.6)                                   # 0.1uF (C3 / C4 on the motor tracks ...
    num(b, 5, 36.0, 36.4)                                   # ... and C5 beside the full-colour LEDs)
    num(b, 6, 21.2, 9.6)                                    # transistor
    sp = [p.GetPosition() for p in FPS["SW1"].Pads()]
    cx = sum(pcbnew.ToMM(q.x) for q in sp) / len(sp) - G.OX     # centre of the 4 legs
    cy = sum(pcbnew.ToMM(q.y) for q in sp) / len(sp) - G.OY
    num(b, 7, cx, cy)                                       # in the middle of the button
    text(b, "スタート", cx + 0.1, cy + 5.7, 1.7, jp=True)     # under the button

    # ---- buzzer ------------------------------------------------------------------------------------------------
    bx, by = pad_xy(FPS["BZ1"], "1")                        # + (front pad)
    text(b, "+", bx - 2.3, by, 1.6, bold=True)
    num(b, 8, bx + 3.6, by + 2.5)
    text(b, "ブザー", bx, by + 7.6, 1.5, jp=True)

    # ---- battery connector, big capacitors ---------------------------------------------------------------------
    jx, jy = pad_xy(FPS["J1"], "1")
    hide_fp_texts(FPS["J1"], ("+", "-"))                    # (the footprint's own +/- would hit C1 and D1)
    text(b, "+", jx, jy - 3.25, 1.0, bold=True)
    text(b, "-", jx + 2.5, jy - 3.25, 1.0, bold=True)
    text(b, "でんち", jx + 1.25, jy + 2.3, 1.3, jp=True)
    num(b, 9, jx + 5.5, jy + 4.7)
    # the 470 uF cans are the tallest parts: soldered LAST (13), after the driver (10), the XIAO (11) and the LEDs (12)
    for ref, (nx, ny), po in (("C1", (62.0, 47.0), True), ("C2", (69.7, 48.4), False)):
        electrolytic(b, FPS[ref], plus_outside=po)
        num(b, 13, nx, ny)

    # ---- modules --------------------------------------------------------------------------------------------
    num(b, 10, 41.6, LL.U2_Y)
    text(b, "モーター", 50.6, LL.U2_Y - 1.05, 1.3, jp=True)
    text(b, "ドライバー", 50.6, LL.U2_Y + 1.15, 1.3, jp=True)
    text(b, "VM", 57.7, LL.U2_R - 1.9, 1.1, bold=True)    # same word as on the module, next to its VM pins
    ux, uy = LL.XIAO_C
    num(b, 11, ux - 7.4, uy - 3.0)
    text(b, "マイコン", ux - 0.6, uy - 3.0, 2.0, jp=True)
    text(b, "XIAO ESP32C6", ux - 0.6, uy + 0.4, 1.0)
    text(b, "USB", ux + 7.6, uy + 4.0, 1.0)
    # full-colour LEDs: the footprint brings the outline and the dot at the GND hole (= the longest leg)
    num(b, 12, 49.5, 22.3)
    text(b, "Linetracer2 Lite rev.L3", 46.0, 39.3, 1.0)

    # ---- motors: pads in the frames' cut-outs ---------------------------------------------------------------
    num(b, 15, 50.0, 64.0)
    text(b, "ひだり", 43.04, 66.7, 1.3, jp=True)
    text(b, "みぎ", 56.96, 66.7, 1.3, jp=True)

    # ---- bottom side ----------------------------------------------------------------------------------------
    num(b, 14, 56.8, 21.0, layer=BL)              # (the back is read mirrored: the number shows left of the text)
    text(b, "センサー", 50.0, 21.0, 1.6, layer=BL, jp=True)
    text(b, "キャスター", 50.0, 17.6, 1.2, layer=BL, jp=True)
    text(b, "Linetracer2 Lite", 50.0, 74.0, 3.0, layer=BL, bold=True)
    text(b, "rev.L3  2026-10  EDTC", 50.0, 78.6, 1.2, layer=BL)
    text(b, "XIAO ESP32C6 + TC78H653FTG + FA-130 x2", 50.0, 81.4, 1.0, layer=BL)
    text(b, "こどもむけ ライントレーサー", 50.0, 85.4, 2.2, layer=BL, jp=True)


def main(step):
    b = pcbnew.LoadBoard(PP.PCB)
    if step == "silk":
        silk(b)
        b.EmbedFonts()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PP.PCB, b)
    print("post %s done" % step, flush=True)
    os._exit(0)                      # skip interpreter teardown (SWIG objects)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "silk")
