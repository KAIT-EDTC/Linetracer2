#!/usr/bin/env python3
"""Gearbox review figure (hardware/mechanical/gearbox_review.png) from linetracer2_mech.scad.

Three OpenSCAD views of the left gearbox, labelled in Japanese:
  1. cut at the shaft height, seen from above (front at the top)
  2. from the wheel side with the wheel taken off: the relief hole in the outer wall, the pinion inside
  3. cut through both motor axes: the deck rib between the two motors' rear ends

The scad frame (x right, y = board y to the rear, z up) is left-handed, so every OpenSCAD render is a mirror
image of the real robot; views 1 and 2 are flipped back here (view 3 is symmetric).
Run from scripts/:   python3 gearbox_figure.py
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MECH = os.path.join(ROOT, "hardware", "mechanical")
TMP = os.path.join(ROOT, ".tmp", "gearbox_fig")
OUT = os.path.join(MECH, "gearbox_review.png")
SCAD = os.path.expanduser("~/.local/opt/openscad-2021/AppRun")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
TAN = 0.198912                       # tan(22.5 deg / 2): OpenSCAD's field of view, also used for --projection=o

VIEWS = """include <linetracer2_mech.scad>
part = "none";
LITE = true;
view = "top";
module below() translate([-50, -50, -50]) cube([300, 300, 50 + AXIS_Z]);     // keep z <= shaft height
module behind() translate([-50, MOTOR_Y, -50]) cube([300, 100, 200]);        // keep y >= motor axis
module axle() translate([AXLE_END_X - AXLE_L, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 2, h = AXLE_L);
module spur() translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40();
if (view == "top") {
    color("orange") render() intersection() { frame_left(lbl = false); below(); }
    color("silver") render() intersection() { motor_left(); below(); }
    color("gold") render() intersection() { pinion8(); below(); }
    color("white") render() intersection() { spur(); below(); }
    color("peru") render() intersection() { axle(); below(); }
    color("yellow") render() intersection() { translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel(); below(); }
    color("dimgray") render() intersection() { translate([WHEEL_X1 - WHEEL_W / 2 + 1.7, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) tire_tpu(); below(); }
    color("deepskyblue") render() intersection() { motor_stop(); below(); }
}
if (view == "side") {
    color("orange") frame_left(lbl = false);
    color("silver") motor_left();
    color("gold") pinion8();
    color("white") spur();
    color("peru") axle();
}
if (view == "front") {
    color("orange") render() intersection() { frames(); behind(); }
    color("silver") render() intersection() { motors(); behind(); }
    color("deepskyblue") render() intersection() { deck(); behind(); }
    color("darkgreen") render() intersection() { translate([NOTCH_X, 50, -PCB_T]) cube([100 - 2 * NOTCH_X, 60, PCB_T]); behind(); }
}
"""

# view: (image size, camera, projection, px/mm for ortho views, model centre)
A_SIZE, A_C, A_S = (1056, 800), (25.0, 81.0), 16.0
C_SIZE, C_C, C_S = (640, 440), (50.0, 9.45), 19.1
B_SIZE = (640, 440)


def dist(h_px, s):
    return h_px / (2 * TAN * s)


JOBS = {
    "top": (A_SIZE, f"{A_C[0]},{A_C[1]},0,0,0,0,{dist(A_SIZE[1], A_S):.2f}", "o"),
    "side": (B_SIZE, "9.5,77,10.4,72,0,250,48", "p"),
    "front": (C_SIZE, f"{C_C[0]},0,{C_C[1]},90,0,0,{dist(C_SIZE[1], C_S):.2f}", "o"),
}


def render(view):
    (w, h), cam, proj = JOBS[view]
    png = os.path.join(TMP, f"{view}.png")
    r = subprocess.run([SCAD, "-o", png, f"--imgsize={w},{h}", f"--camera={cam}", f"--projection={proj}",
                        "--colorscheme=Tomorrow", "-D", f'view="{view}"', os.path.join(TMP, "views.scad")],
                       env=dict(os.environ, OPENSCADPATH=MECH), capture_output=True, text=True)
    if r.returncode or not os.path.exists(png):
        sys.exit(f"openscad failed for {view}:\n{r.stderr[-2000:]}")
    return Image.open(png).convert("RGB")


def font(size):
    return ImageFont.truetype(FONT, size, index=0)          # index 0 = Noto Sans CJK JP


def label(d, text, at, anchor=None, size=22, fill=(20, 20, 20), box=(255, 255, 255)):
    """Text with a white box at `at` (top-left); an optional leader line from the box to `anchor`."""
    f = font(size)
    lines = text.split("\n")
    wid = max(d.textlength(t, font=f) for t in lines)
    hgt = len(lines) * (size + 4)
    x0, y0, x1, y1 = at[0] - 4, at[1] - 2, at[0] + wid + 4, at[1] + hgt + 2
    if anchor:
        cx = min(max(anchor[0], x0), x1)
        cy = min(max(anchor[1], y0), y1)
        d.line([(cx, cy), anchor], fill=(200, 30, 30), width=3)
        d.ellipse([anchor[0] - 4, anchor[1] - 4, anchor[0] + 4, anchor[1] + 4], fill=(200, 30, 30))
    if box:
        d.rectangle([x0, y0, x1, y1], fill=box)
    for i, t in enumerate(lines):
        d.text((at[0], at[1] + i * (size + 4)), t, font=f, fill=fill)


def titled(img, title):
    out = Image.new("RGB", (img.width, img.height + 44), "white")
    out.paste(img, (0, 44))
    d = ImageDraw.Draw(out)
    d.text((10, 6), title, font=font(24), fill=(20, 20, 20))
    d.line([(0, 43), (img.width, 43)], fill=(180, 180, 180), width=2)
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    with open(os.path.join(TMP, "views.scad"), "w") as fh:
        fh.write(VIEWS)
    with ThreadPoolExecutor(3) as ex:
        top, side, front = ex.map(render, ["top", "side", "front"])

    # 1: flipped top-bottom -> real top view of the LEFT gearbox, front at the top
    top = ImageOps.flip(top)
    pad_t, pad_b, pad_r = 40, 70, 150
    a = Image.new("RGB", (A_SIZE[0] + pad_r, A_SIZE[1] + pad_t + pad_b), (248, 248, 248))
    a.paste(top, (0, pad_t))
    d = ImageDraw.Draw(a)

    def fa(x, y):
        return (A_SIZE[0] / 2 + (x - A_C[0]) * A_S, pad_t + A_SIZE[1] / 2 + (y - A_C[1]) * A_S)

    label(d, "モーター FA-130", (560, fa(0, 79)[1]), box=None, size=26)
    label(d, "ピニオン 8T", (40, 110), fa(13.0, 74.0))
    label(d, "外かべの にげ穴 φ6.5\n（軸が長くても当たらない）", (20, 190), fa(9.5, 73.0))
    label(d, "平歯車 40T", (300, 850), fa(13.5, 97.0))
    label(d, "車軸 φ2", (470, 600), fa(18.5, 88.0))
    label(d, "車輪・タイヤ", (20, 850), fa(3.7, 102.0))
    label(d, "モーターの板", (290, 95), fa(18.6, 64.5))
    label(d, "デッキの\nリブ", (990, 420), fa(50.5, 78.0))
    d.text((1060, 52), "▲ まえ", font=font(28), fill=(20, 20, 20))
    a = titled(a, "① 左のギヤボックスを上から（軸の高さで切った断面）")

    # 2: flipped left-right -> the real left gearbox seen from outside, front on the left
    side = ImageOps.mirror(side)
    d = ImageDraw.Draw(side)
    label(d, "にげ穴 φ6.5\n（中にピニオン）", (16, 300), (300, 222))
    label(d, "車軸", (560, 395), (545, 345))
    label(d, "平歯車 40T", (470, 12), (520, 70))
    label(d, "外かべ", (380, 395), (420, 330))
    d.text((16, 12), "← まえ", font=font(24), fill=(20, 20, 20))
    b = titled(side, "② 外から（車輪を外したところ）")

    # 3: symmetric, no flip
    d = ImageDraw.Draw(front)

    def fc(x, z):
        return (C_SIZE[0] / 2 + (x - C_C[0]) * C_S, C_SIZE[1] / 2 - (z - C_C[1]) * C_S)

    label(d, "リブ 1 mm\nすき間 0.5 ずつ", (250, 318), fc(50, 8.6), size=20)
    label(d, "デッキ", (12, 14), box=None, size=22, fill=(255, 255, 255))
    label(d, "モーターの うしろ", (20, 190), box=None, size=22)
    label(d, "モーターの うしろ", (452, 190), box=None, size=22)
    label(d, "基板", (12, 404), box=None, size=20, fill=(255, 255, 255))
    c = titled(front, "③ 2 つのモーターの間（軸で切った断面）")

    W = a.width + b.width
    H = max(a.height, b.height + c.height)
    out = Image.new("RGB", (W, H), "white")
    out.paste(a, (0, 0))
    out.paste(b, (a.width, 0))
    out.paste(c, (a.width, b.height))
    ImageDraw.Draw(out).line([(a.width, 0), (a.width, H)], fill=(180, 180, 180), width=2)
    out.save(OUT, optimize=True)
    print("wrote", os.path.relpath(OUT, ROOT), out.size)


if __name__ == "__main__":
    main()
