#!/usr/bin/env python3
"""Layout preview of the Lite board (plain python + PIL, no KiCad): placement from layout_lite.py, the hand-drawn
routes (red = top, blue = bottom), the ratsnest of everything not routed yet, keep-outs and the mechanical zones.
Much faster than a KiCad round trip while moving parts / drawing routes.
    cd scripts && LT2_VARIANT=lite ./kpy ../lite/scripts/dump_footprints.py     # once, or when footprints change
    python3 lite/scripts/preview_layout.py out.png [--norats] [--crop=x0,y0,x1,y1]
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout_lite as LL  # noqa: E402

D = json.load(open(os.path.join(ROOT, ".tmp", "fpdump.json")))
S = 12.0           # px per mm
MX, MY = 40, 40    # margins px
X0 = 17.5


def px(x, y):
    return (MX + (x - X0) * S, MY + y * S)


def xform(ref, lx, ly):
    x, y, rot, side = LL.PLACE[ref]
    if side == "B":
        ly = -ly
    a = math.radians(rot)
    return x + lx * math.cos(a) + ly * math.sin(a), y - lx * math.sin(a) + ly * math.cos(a)


def pads():
    out = []
    for ref, fpn in D["comps"].items():
        if ref not in LL.PLACE:
            continue
        for p in D["fps"][fpn]["pads"]:
            x, y = xform(ref, p["x"], p["y"])
            out.append(dict(ref=ref, num=p["num"], x=x, y=y, sx=p["sx"], sy=p["sy"], drill=p["drill"],
                            net=D["pinnet"].get("%s:%s" % (ref, p["num"]), "")))
    return out


def mst(pts):
    if len(pts) < 2:
        return []
    inn, edges = {0}, []
    while len(inn) < len(pts):
        best = None
        for i in inn:
            for j in range(len(pts)):
                if j in inn:
                    continue
                d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                if best is None or d < best[0]:
                    best = (d, i, j)
        inn.add(best[2])
        edges.append((pts[best[1]], pts[best[2]]))
    return edges


def main(out, show_rats=True):
    W = int(2 * MX + 65 * S)
    H = int(2 * MY + 100 * S)
    im = Image.new("RGB", (W, H), (30, 34, 30))
    d = ImageDraw.Draw(im, "RGBA")
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    # board
    d.rounded_rectangle([px(17.5, 0), px(82.5, 100)], radius=int(2 * S), fill=(40, 70, 45), outline=(220, 220, 0))
    # mechanical zones (top side): towers, deck front bar, motor cans
    for (x, y) in ((30, 62), (70, 62), (30, 96), (70, 96)):
        d.ellipse([px(x - 4.8, y - 4.8), px(x + 4.8, y + 4.8)], outline=(255, 150, 0), width=2)
        d.ellipse([px(x - 1.6, y - 1.6), px(x + 1.6, y + 1.6)], fill=(0, 0, 0))
    d.rectangle([px(24.5, 57), px(75.5, 65.5)], outline=(255, 150, 0, 120))
    for x0, x1 in ((20.5, 49.0), (51.0, 79.5)):
        d.rectangle([px(x0, 66), px(x1, 86)], outline=(200, 200, 200, 120))
    # keep-outs
    for k in LL.KEEPOUTS:
        if k[0] == "circle":
            _, x, y, r, lay = k
            d.ellipse([px(x - r, y - r), px(x + r, y + r)], outline=(255, 60, 255), width=1)
        else:
            _, x0, y0, x1, y1, lay = k
            d.rectangle([px(x0, y0), px(x1, y1)], outline=(255, 60, 255), width=1)
    # bottom zones (caster / sensors bodies) dashed-ish
    for z in LL.BOTTOM_ZONES:
        _, x0, y0, x1, y1 = z
        d.rectangle([px(x0, y0), px(x1, y1)], outline=(120, 160, 255), width=1)
    # footprint graphics
    for ref, fpn in D["comps"].items():
        if ref not in LL.PLACE:
            continue
        side = LL.PLACE[ref][3]
        col = (230, 230, 230) if side == "F" else (140, 170, 255)
        for l in D["fps"][fpn]["lines"]:
            tag = l[-1]
            c = {"silk": col, "fab": (150, 150, 150), "crt": (255, 0, 255, 90)}[tag]
            if tag == "fab":
                continue
            if l[0] == "L":
                d.line([px(*xform(ref, l[1], l[2])), px(*xform(ref, l[3], l[4]))], fill=c, width=1)
            elif l[0] == "R":
                pts = [(l[1], l[2]), (l[3], l[2]), (l[3], l[4]), (l[1], l[4]), (l[1], l[2])]
                d.line([px(*xform(ref, a, b)) for a, b in pts], fill=c, width=1)
            elif l[0] == "C":
                cx, cy = xform(ref, l[1], l[2])
                r = l[3]
                d.ellipse([px(cx - r, cy - r), px(cx + r, cy + r)], outline=c, width=1)
        x, y, rot, side = LL.PLACE[ref]
        d.text(px(x + 0.3, y - 1.6), ref, fill=(255, 255, 120), font=font)
    P = pads()
    # tracks
    for t in LL.tracks(lambda r, n: next((p["x"], p["y"]) for p in P if p["ref"] == r and p["num"] == n)):
        (x1, y1), (x2, y2), layer, w, net = t
        c = (220, 60, 50, 230) if layer == "F" else (60, 120, 255, 200)
        d.line([px(x1, y1), px(x2, y2)], fill=c, width=max(1, int(w * S)))
        r = w / 2
        for (x, y) in ((x1, y1), (x2, y2)):
            d.ellipse([px(x - r, y - r), px(x + r, y + r)], fill=c)
    for (x, y) in LL.vias(lambda r, n: next((p["x"], p["y"]) for p in P if p["ref"] == r and p["num"] == n)):
        d.ellipse([px(x - 0.45, y - 0.45), px(x + 0.45, y + 0.45)], fill=(200, 200, 200))
        d.ellipse([px(x - 0.2, y - 0.2), px(x + 0.2, y + 0.2)], fill=(0, 0, 0))
    # pads
    for p in P:
        x, y, r = p["x"], p["y"], max(p["sx"], p["sy"]) / 2
        if p["net"] == "" and p["num"] == "":
            d.ellipse([px(x - r, y - r), px(x + r, y + r)], fill=(0, 0, 0), outline=(120, 120, 120))
            continue
        d.ellipse([px(x - r, y - r), px(x + r, y + r)], fill=(200, 170, 60))
        dr = p["drill"] / 2
        d.ellipse([px(x - dr, y - dr), px(x + dr, y + dr)], fill=(30, 30, 30))
    # ratsnest of unrouted connections
    if show_rats:
        nets = {}
        for p in P:
            if p["net"] and p["net"] != "GND":
                nets.setdefault(p["net"], []).append((p["x"], p["y"]))
        routed = LL.routed_nets()
        for n, pts in nets.items():
            if n in routed:
                continue
            for a, b in mst(pts):
                d.line([px(*a), px(*b)], fill=(255, 255, 255, 160), width=1)
        # net labels at pads (short)
        for p in P:
            if p["net"] and p["net"] != "GND":
                lab = p["net"].replace("/", "").replace("Net-(", "").replace(")", "")[:7]
                d.text(px(p["x"] + 0.6, p["y"] + 0.4), lab, fill=(150, 255, 150), font=ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8) if os.path.exists(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") else font)
    # grid ticks every 10 mm
    for gx in range(20, 83, 10):
        d.text(px(gx - 0.5, -3.0), str(gx), fill=(200, 200, 200), font=font)
    for gy in range(0, 101, 10):
        d.text(px(14.0, gy - 0.5), str(gy), fill=(200, 200, 200), font=font)
    padf = lambda r, n: next((p["x"], p["y"]) for p in P if p["ref"] == r and p["num"] == n)
    print("bad angles:", LL.check_angles(padf))
    if CROP:
        x0, y0, x1, y1 = CROP
        im = im.crop((int(px(x0, y0)[0]), int(px(x0, y0)[1]), int(px(x1, y1)[0]), int(px(x1, y1)[1])))
        im = im.resize((im.width * 2, im.height * 2))
    im.save(out)
    print("saved", out)


CROP = None
if __name__ == "__main__":
    for a in sys.argv:
        if a.startswith("--crop="):
            CROP = [float(v) for v in a[7:].split(",")]
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, ".tmp", "preview.png"), show_rats="--norats" not in sys.argv)
