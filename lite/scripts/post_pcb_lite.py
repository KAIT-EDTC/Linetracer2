#!/usr/bin/env python3
"""Post-process the routed Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/post_pcb_lite.py prune|silk).

Same steps as post_pcb.py (GND track pruning, kid-friendly silkscreen); only the silkscreen differs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))   # shared modules
import pcbnew  # noqa: E402
import post_pcb as PP  # noqa: E402  (helpers: text, line, rect, set_ref, set_val, prune_gnd)
import gen_pcb as G  # noqa: E402
import gen_pcb_lite as L  # noqa: E402

text, line, rect, set_ref, set_val = PP.text, PP.line, PP.rect, PP.set_ref, PP.set_val


# 3rd colour band of the resistors (all three values are brown-black-?-gold, only the 3rd band differs)
BAND3 = {"100": "ちゃ", "10k": "だいだい", "1k": "あか"}


def pad_xy(fp, num):
    for pad in fp.Pads():
        if pad.GetNumber() == num:
            q = pad.GetPosition()
            return pcbnew.ToMM(q.x) - G.OX, pcbnew.ToMM(q.y) - G.OY
    raise KeyError(num)


def num(b, n, x, y, layer=pcbnew.F_SilkS, r=1.15):
    """Build-order number: a silk circle with the digit inside (stroke font; the CJK font's circled digits are
    too thin for the silkscreen rules)."""
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(G.P(x, y))
    s.SetEnd(G.P(x + r, y))
    s.SetLayer(layer)
    s.SetWidth(G.mm(0.15))
    b.Add(s)
    text(b, str(n), x, y, 1.2 if n < 10 else 0.9, layer=layer)


def hide_fp_texts(fp, words):
    """Move footprint texts from the silkscreen to the fab layer (KiCad does not keep 'hidden' on footprint
    user texts); they stay in the assembly drawing."""
    for item in fp.GraphicalItems():
        if item.GetClass() == "PCB_TEXT":
            item = item.Cast()
            if item.GetText() in words:
                item.SetLayer(pcbnew.F_Fab if item.GetLayer() == pcbnew.F_SilkS else pcbnew.B_Fab)


def silk(b):
    """Kid-friendly silkscreen (lower elementary school): only SYMBOLS on the board - build-order numbers,
    polarity marks, the 3rd colour band of each resistor, short part names.  What the marks mean and the steps
    are in the assembly manual (lite/docs/assembly.md), not on the board.
    Japanese text is 1.3 mm or bigger (smaller kana fail the stroke-width check), symbols like + use the stroke font.
    NOTE: run only once on a freshly routed board (build_pcb.py does this)."""
    PP.FP.clear()
    PP.FP.update({f.GetReference(): f for f in b.GetFootprints()})
    FPS = PP.FP
    F, BL = pcbnew.F_SilkS, pcbnew.B_SilkS

    # ---- references: hidden on the top (the kit's papers use the assembly drawing), sensors on the back ------
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if not ref.startswith(("PS", "H")):
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
    for i, x in enumerate(L.SENSOR_X):
        fp = FPS["PS%d" % (i + 1)]
        f = fp.Reference()
        f.SetPosition(G.P(x - 6.0, G.SENSOR_Y))        # (bottom side) in the gap left of the sensor
        f.SetTextSize(pcbnew.VECTOR2I(G.mm(0.8), G.mm(0.8)))
        f.SetTextThickness(G.mm(0.15))
        fp.Value().SetVisible(False)
    hide_fp_texts(FPS["U2"], ("TC78H653", "VM", "GND"))

    # ---- front edge, transistor ---------------------------------------------------------------------------
    text(b, "▲まえ", 29.6, 2.4, 1.4, jp=True)
    qx = pad_xy(FPS["Q1"], "2")[0]
    num(b, 4, 20.3, 11.6)

    # ---- resistors: the colour of the 3rd band on the body + key (front-right corner) ---------------------------
    for ref in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
        fp = FPS[ref]
        (x1, y1), (x2, y2) = pad_xy(fp, "1"), pad_xy(fp, "2")
        w = BAND3[fp.GetValue()]
        text(b, w, (x1 + x2) / 2, (y1 + y2) / 2, 1.1 if len(w) > 2 else 1.3,
             angle=90 if abs(x1 - x2) < 0.1 else 0, jp=True)
    num(b, 1, 50.0, 25.4)

    # ---- sensors, skid --------------------------------------------------------------------------------------
    for i, x in enumerate(L.SENSOR_X):
        text(b, "S%d" % (i + 1), x, 6.6, 0.8)
    sx, sy = L.SKID_HOLE
    text(b, "スキッド", sx, sy + 4.6, 1.3, jp=True)

    # ---- button --------------------------------------------------------------------------------------------
    swx = pad_xy(FPS["SW1"], "1")[0] + 6.5 / 2
    text(b, "スタート", swx + 10.0, 26.6, 2.0, jp=True)
    num(b, 4, 30.0, 23.6)
    text(b, "Linetracer2 Lite", 34.0, 33.6, 1.5, bold=True)
    text(b, "rev.L2", 34.0, 35.8, 0.8)

    # ---- LED (next to the XIAO) ----------------------------------------------------------------------------
    ax, ay = pad_xy(FPS["D2"], "2")                                 # anode (front pad of the LED)
    text(b, "LED", ax - 8.0, ay - 6.4, 1.2)
    text(b, "+", ax - 2.5, ay, 1.4)
    num(b, 4, ax - 3.5, ay - 6.4)
    # picture of an LED: the LONGER leg is +
    px, py = ax - 8.0, ay - 3.4
    PP.G.add_line(b, px - 1.4, py, px - 1.4, py + 2.0, w=0.15)
    PP.G.add_line(b, px + 1.4, py, px + 1.4, py + 2.0, w=0.15)
    PP.G.add_line(b, px - 1.6, py + 2.0, px + 1.6, py + 2.0, w=0.15)
    a = pcbnew.PCB_SHAPE(b)
    a.SetShape(pcbnew.SHAPE_T_ARC)
    a.SetArcGeometry(G.P(px - 1.4, py), G.P(px, py - 1.4), G.P(px + 1.4, py))
    a.SetLayer(pcbnew.F_SilkS)
    a.SetWidth(G.mm(0.15))
    b.Add(a)
    PP.G.add_line(b, px - 0.6, py + 2.0, px - 0.6, py + 5.4, w=0.15)      # long leg
    PP.G.add_line(b, px + 0.6, py + 2.0, px + 0.6, py + 3.9, w=0.15)      # short leg
    text(b, "+", px - 1.7, py + 4.8, 1.2)

    # ---- capacitors (the hatched half of the outline = the minus stripe of the capacitor) ---------------------
    num(b, 6, 28.6, 41.6)
    num(b, 6, 58.8, 46.7)
    num(b, 3, 47.7, 57.5)

    # ---- diode, battery ---------------------------------------------------------------------------------------
    num(b, 2, 75.7, 51.4)
    jx, jy = pad_xy(FPS["J1"], "1")
    text(b, "でんち", jx + 1.25, jy + 6.0, 1.4, jp=True)
    num(b, 5, jx + 1.25, 47.6)

    # ---- motor driver (labels inside its outline, between the pin rows) -----------------------------------------
    num(b, 7, 30.4, 51.4)
    text(b, "モーター ドライバー", 38.0, 48.6, 1.3, jp=True)

    # ---- microcontroller (labels inside its outline) --------------------------------------------------------------
    ux = 68.8
    num(b, 8, 62.4, 31.2)
    text(b, "マイコン", ux, 31.2, 2.0, jp=True)
    text(b, "XIAO ESP32C6", ux, 34.2, 1.0)
    text(b, "USB", 78.4, 35.0, 1.0)

    # ---- motors (top side, under the frames) -------------------------------------------------------------------
    num(b, 10, 50.0, 61.5)
    my = G.MOTOR_Y
    for sgn in (-1, 1):
        x1, x2 = sorted((50.0 + sgn * 1.0, 50.0 + sgn * 29.5))
        rect(b, max(x1, L.BOARD_X0 + 0.6), my - 10.05, min(x2, L.BOARD_X1 - 0.6), my + 10.05, w=0.12)
    text(b, "M1 ひだり モーター", 35.0, my - 4.0, 1.3, jp=True)
    text(b, "M2 みぎ モーター", 65.0, my - 4.0, 1.3, jp=True)

    # ---- bottom side ----------------------------------------------------------------------------------------
    num(b, 9, 55.6, 21.6, layer=BL)              # (the back is read mirrored: the number shows left of the text)
    text(b, "センサー", 50.0, 21.6, 1.6, layer=BL, jp=True)
    text(b, "スキッド", sx, sy + 5.6, 1.2, layer=BL, jp=True)
    text(b, "Linetracer2 Lite", 50.0, 76.0, 3.0, layer=BL, bold=True)
    text(b, "rev.L2  2026-10  EDTC", 50.0, 80.6, 1.2, layer=BL)
    text(b, "XIAO ESP32C6 + TC78H653FTG + FA-130 x2", 50.0, 83.4, 1.0, layer=BL)
    text(b, "こどもむけ ライントレーサー", 50.0, 87.4, 2.2, layer=BL, jp=True)


def main(step):
    b = pcbnew.LoadBoard(PP.PCB)
    if step == "prune":
        PP.prune_gnd(b)
    else:
        silk(b)
        b.EmbedFonts()
        # 2nd pass: a short GND stub on the LED's cathode survives the first pass (the zones were filled with all
        # the GND tracks still there) and shows up in the DRC as track_dangling.  Pruning again removes it.
        PP.prune_gnd(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PP.PCB, b)
    print("post %s done" % step, flush=True)
    os._exit(0)                      # skip interpreter teardown (SWIG objects)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "silk")
