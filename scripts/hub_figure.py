#!/usr/bin/env python3
"""Figures of the wheel drive (hardware/mechanical/hex_hub.png, hex_hub_parts.png) from linetracer2_mech.scad.

hex_hub.png: (1) cut through the axle, seen from the rear: wheel with its hex hub and printed stub axle, outer wall,
40T gear, motor plate; (2) the outer wall seen from the wheel side with the wheel taken off (pointed "teardrop"
bearing hole); (3) the wheel as it is printed (outer face on the bed, hub and axle up).
hex_hub_parts.png: wheel and gear apart, from outside and from inside.
The scad frame is left-handed, so the renders are mirror images; the cut is flipped back (outside on the left).
Run from scripts/:   python3 hub_figure.py
"""
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MECH = os.path.join(ROOT, "hardware", "mechanical")
TMP = os.path.join(ROOT, ".tmp", "hub_fig")
SCAD = os.path.expanduser("~/.local/opt/openscad-2021/AppRun")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
TAN = 0.198912                       # tan(22.5 deg / 2): OpenSCAD's field of view, also used for --projection=o
BG = (248, 248, 248)
MIRROR_CUT = 1                       # +1: wheel already on the left of the render, -1: flip

VIEWS = """include <linetracer2_mech.scad>
part = "none";
LITE = true;
view = "cut";
gap = 0;
module keep_rear() translate([-50, AXLE_Y, -50]) cube([300, 100, 200]);     // keep y >= axle line
module wheel_at(dx = 0) translate([WHEEL_X1 - dx, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel();
module spur(dx = 0) translate([GEAR_X0 + dx, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40();
module tyre() translate([WHEEL_X1 - WHEEL_W / 2 + 1.7, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) tire_tpu();
if (view == "cut") {
    color("orange") render() intersection() { frame_left(lbl = false); keep_rear(); }
    color("white") render() intersection() { spur(); keep_rear(); }
    color("gold") render() intersection() { wheel_at(); keep_rear(); }
    color("dimgray") render() intersection() { tyre(); keep_rear(); }
}
// the outer wall only (x <= 11.3), turned so that the camera of the front view looks at it from the wheel side
if (view == "wall") rotate([0, 0, 90]) translate([0, -AXLE_Y, -AXIS_Z])
    color("orange") render() intersection() { frame_left(lbl = false); translate([-50, 0, -50]) cube([50 + GEAR_X0 - 0.2, 200, 200]); }
if (view == "print") color("gold") translate([0, 0, WHEEL_W]) mirror([0, 0, 1]) wheel();
if (view == "parts") {
    color("gold") wheel_at(gap);
    color("white") spur(gap);
}
"""

# view: (image size, camera, projection, extra -D)
CUT_C, CUT_S = (10.0, 10.4), 34.0                  # model centre (x, z) and px/mm of the cut
JOBS = {
    "cut": ((1000, 760), f"{CUT_C[0]},88,{CUT_C[1]},90,0,0,{760 / (2 * TAN * CUT_S):.2f}", "o", []),
    "wall": ((440, 440), f"0,9,0,90,0,0,{440 / (2 * TAN * 30):.2f}", "o", []),
    "print": ((440, 440), "0,0,7,55,0,25,95", "p", []),
    "out": ((900, 620), "8,88,10.4,70,0,300,120", "p", ["-D", "gap=14"]),
    "in": ((900, 620), "10,88,10.4,75,0,150,80", "p", ["-D", "gap=12"]),
}
SCAD_VIEW = {"cut": "cut", "wall": "wall", "print": "print", "out": "parts", "in": "parts"}


def render(view):
    (w, h), cam, proj, extra = JOBS[view]
    png = os.path.join(TMP, f"{view}.png")
    cmd = [SCAD, "-o", png, f"--imgsize={w},{h}", f"--camera={cam}", f"--projection={proj}",
           "--colorscheme=Tomorrow", "-D", f'view="{SCAD_VIEW[view]}"'] + extra + [os.path.join(TMP, "views.scad")]
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, OPENSCADPATH=MECH))
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    return view, Image.open(png).convert("RGB")


def whiten(im):
    """Tomorrow's background -> the page background."""
    bg = im.getpixel((2, 2))
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == bg:
                px[x, y] = BG
    return im


def label(d, font, xy, text, to=None):
    """Text with a white box; optional thin red line from the box to the point `to`."""
    x, y = xy
    l, t, r, b = d.textbbox((x, y), text, font=font)
    if to:
        d.line([((l + r) // 2, (t + b) // 2), to], fill=(200, 30, 30), width=2)
    d.rectangle([l - 6, t - 4, r + 6, b + 4], fill=(255, 255, 255))
    d.text((x, y), text, font=font, fill=(20, 20, 20))


def main():
    os.makedirs(TMP, exist_ok=True)
    with open(os.path.join(TMP, "views.scad"), "w") as f:
        f.write(VIEWS)
    with ThreadPoolExecutor(5) as ex:
        im = dict(ex.map(render, JOBS))
    im = {k: whiten(v) for k, v in im.items()}
    big = ImageFont.truetype(FONT, 28)
    small = ImageFont.truetype(FONT, 22)

    # ---- hex_hub.png: cut + wall + print
    cut = im["cut"] if MIRROR_CUT == 1 else ImageOps.mirror(im["cut"])   # outside (wheel) on the left
    W, H = 1000 + 440 + 30, 820 + 50
    page = Image.new("RGB", (W, H), BG)
    page.paste(cut, (0, 50))
    page.paste(im["wall"], (1000 + 30, 50))
    page.paste(im["print"], (1000 + 30, 50 + 440 - 20 + 20))
    d = ImageDraw.Draw(page)
    d.text((14, 6), "① 車軸を通る面で切った断面（前から）", font=big, fill=(20, 20, 20))
    d.text((1000 + 40, 6), "② 外かべ（車輪を外して外から）", font=big, fill=(20, 20, 20))
    d.text((1000 + 40, 50 + 440 + 6), "③ 車輪を印刷する向き", font=big, fill=(20, 20, 20))

    def cx(x_mm):                                      # model x (mm) -> page px in the (mirrored) cut
        return int(500 + MIRROR_CUT * (x_mm - CUT_C[0]) * CUT_S)

    def cz(z_mm):
        return int(50 + 380 - (z_mm - CUT_C[1]) * CUT_S)

    label(d, small, (40, 90), "車輪", (cx(3.5), cz(16)))
    label(d, small, (300, 130), "外かべ（丸い穴が軸受け）", (cx(9.5), cz(14.6)))
    label(d, small, (520, 760), "平歯車（六角の穴）", (cx(13.5), cz(4)))
    label(d, small, (600, 90), "モーターの板（奥が止まり穴の軸受け）", (cx(18.6), cz(17)))
    label(d, small, (60, 760), "ハブ φ5.0（丸）→ 六角 4.0 → 車軸 φ3.5（ぜんぶ車輪と一体で印刷）", None)
    page.save(os.path.join(MECH, "hex_hub.png"))

    # ---- hex_hub_parts.png: wheel and gear apart, outside / inside
    page = Image.new("RGB", (900, 1340), BG)
    page.paste(ImageOps.mirror(im["out"]), (0, 50))
    page.paste(ImageOps.mirror(im["in"]), (0, 50 + 620 + 50))
    d = ImageDraw.Draw(page)
    d.text((14, 6), "① 外から見たところ（ばらした図）", font=big, fill=(20, 20, 20))
    d.text((14, 50 + 620 + 6), "② 内側から見たところ", font=big, fill=(20, 20, 20))
    label(d, small, (470, 120), "平歯車の六角の穴", (352, 300))
    label(d, small, (430, 790), "車軸 φ3.5 → モーターの板の止まり穴", (395, 1012))
    label(d, small, (330, 1100), "六角 4.0 → 平歯車の六角の穴", (300, 1020))
    label(d, small, (40, 1190), "ハブ φ5.0 → 外かべの丸い穴", (225, 1005))
    d.text((14, 1300), "車輪・ハブ・六角・車軸は 1 つの部品（真鍮の車軸は使わない）", font=small, fill=(20, 20, 20))
    page.save(os.path.join(MECH, "hex_hub_parts.png"))
    print("wrote hex_hub.png, hex_hub_parts.png")


if __name__ == "__main__":
    main()
