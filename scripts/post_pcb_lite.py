#!/usr/bin/env python3
"""Post-process the routed Lite board (LT2_VARIANT=lite scripts/kpy post_pcb_lite.py prune|silk).

Same steps as post_pcb.py (GND track pruning, kid-friendly silkscreen); only the silkscreen differs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
import post_pcb as PP  # noqa: E402  (helpers: text, line, rect, set_ref, set_val, prune_gnd)
import gen_pcb as G  # noqa: E402
import gen_pcb_lite as L  # noqa: E402

text, line, rect, set_ref, set_val = PP.text, PP.line, PP.rect, PP.set_ref, PP.set_val


def silk(b):
    # NOTE: run only once on a freshly routed board (build_pcb.py does this).
    PP.FP.clear()
    PP.FP.update({f.GetReference(): f for f in b.GetFootprints()})
    # ---- references --------------------------------------------------------
    set_ref(b, "Q1", 10.4, 6.6, 0.8)
    set_ref(b, "R7", visible=False)
    set_ref(b, "U1", 33.0, 28.6, 1.0)
    set_ref(b, "U2", 61.0, 47.5, 1.0, angle=90)
    set_ref(b, "C1", 76.0, 29.6, 0.8)
    set_ref(b, "C2", 76.0, 38.6, 0.8)
    set_ref(b, "J1", 70.4, 55.0, 0.8)
    set_ref(b, "D2", visible=False)
    text(b, "D2:LED1", 86.0, 21.3, 0.8)
    set_ref(b, "SW1", 92.0, 1.3, 0.8)
    set_ref(b, "J2", 14.2, 57.4, 0.8)
    set_ref(b, "M1", 43.0, 67.0, 1.0)
    set_ref(b, "M2", 57.0, 67.0, 1.0)
    set_ref(b, "C3", 39.8, 58.0, 0.8, angle=90)
    set_ref(b, "C4", 53.7, 58.0, 0.8, angle=90)
    set_val(b, "D1", 80.1, 45.9, 0.8, text_="1N5819")
    for i, x in enumerate(L.SENSOR_X):
        fp = PP.FP["PS%d" % (i + 1)]
        f = fp.Reference()
        f.SetPosition(G.P(x + 4.3, G.SENSOR_Y))        # beside the sensor (behind it is the skid)
        f.SetTextSize(pcbnew.VECTOR2I(G.mm(0.8), G.mm(0.8)))
        f.SetTextThickness(G.mm(0.15))
        fp.Value().SetVisible(False)

    # ---- top side labels -----------------------------------------------------
    for i, x in enumerate(L.SENSOR_X):
        text(b, "S%d" % (i + 1), x, 6.35, 0.8)
    text(b, "FRONT", 24.0, 4.0, 0.8)
    text(b, "まえ", 24.0, 6.2, 1.4, jp=True)
    sx, sy = L.SKID_HOLE
    text(b, "SKID", sx, sy + 5.4, 0.8)
    text(b, "START", 85.8, 5.5, 0.8, angle=90)
    text(b, "スタート", 92.0, 10.0, 1.4, jp=True)
    text(b, "<USB", 3.0, 29.0, 0.8)
    text(b, "Raspberry Pi Pico (Pico 2 OK): no pin header", 18.0, 23.4, 0.9)
    text(b, "じかに はんだづけ", 18.0, 26.2, 1.4, jp=True)      # (katakana like ピンヘッダ fail the stroke check)
    text(b, "Linetracer2 Lite", 77.5, 12.0, 1.5, bold=True)
    text(b, "rev.L1", 77.5, 14.6, 0.8)
    text(b, "BAT 3xAA", 76.25, 58.7, 0.8)
    text(b, "でんち", 76.25, 60.5, 1.4, jp=True)
    text(b, "I2C", 14.2, 59.4, 0.8)
    for k, s in enumerate(("G", "V", "C", "D")):
        text(b, s, 3.0 + 2.54 * k, 60.6, 0.8)
    text(b, "M1 LEFT", 43.0, 68.8, 0.8)
    text(b, "M2 RIGHT", 57.0, 68.8, 0.8)
    text(b, "ひだり", 35.0, 74.6, 1.4, jp=True)
    text(b, "みぎ", 65.0, 74.6, 1.4, jp=True)

    # ---- motor outlines (assembly guide, top side) ---------------------------
    my, ay = G.MOTOR_Y, G.AXLE_Y
    for sgn in (-1, 1):
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
    text(b, "Linetracer2 Lite", 50.0, 80.0, 3.0, layer=BL, bold=True)
    text(b, "rev.L1  2026-10  EDTC", 50.0, 84.5, 1.2, layer=BL)
    text(b, "Raspberry Pi Pico + TC78H653FTG + FA-130 x2", 50.0, 87.5, 1.0, layer=BL)
    text(b, "子ども向けライントレーサー教材", 50.0, 92.0, 2.6, layer=BL, jp=True)
    text(b, "SENSOR SIDE: LBR-123F x3  (lens to the floor)", 50.0, 21.6, 0.9, layer=BL)
    text(b, "センサーはこちらの面に付ける", 50.0, 24.3, 1.6, layer=BL, jp=True)
    text(b, "SKID", sx, sy + 5.6, 0.8, layer=BL)


def main(step):
    b = pcbnew.LoadBoard(PP.PCB)
    if step == "prune":
        PP.prune_gnd(b)
    else:
        silk(b)
        b.EmbedFonts()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PP.PCB, b)
    print("post %s done" % step, flush=True)
    os._exit(0)                      # skip interpreter teardown (SWIG objects)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "silk")
