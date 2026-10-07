#!/usr/bin/env python3
"""One picture per soldering step for the assembly manual (lite/docs/steps/step_NN.png).

The board and every part come from KiCad's VRML export (all 3D models).  Each picture is a flat top view (the
sensors' step: the back, seen from below - like silk_bottom.png): parts of earlier steps are drawn pale, the parts
of THIS step in colour with a yellow halo.  Plain python + PIL (a painter's-algorithm renderer, no OpenGL).

    cd scripts && ./kc pcb export vrml --units mm --user-origin 100x50mm -f -o ../.tmp/asm/board.wrl \
        ../lite/hardware/kicad/Linetracer2-Lite.kicad_pcb
    python3 ../lite/scripts/step_images.py ../.tmp/asm/board.wrl
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import asm3d  # noqa: E402
import layout_lite as LL  # noqa: E402

# build order (= the circled numbers on the board, lite/docs/assembly.md)
STEPS = {1: ["R1", "R2", "R3", "R9"], 2: ["R4", "R5", "R6"], 3: ["R7", "R8", "R10"], 4: ["D1"], 5: ["C3", "C4"],
         6: ["Q1"], 7: ["D2"], 8: ["SW1"], 9: ["BZ1"], 10: ["J1"], 11: ["U2"], 12: ["U1"], 13: ["C1", "C2"],
         14: ["PS1", "PS2", "PS3"]}
S = 11.0                       # px per mm
X0, X1, Y0, Y1 = 17.5, 82.5, 0.0, 68.0          # board area shown (the rear is under the gearbox)
LIGHT = (-0.35, 0.45, 1.0)


def components(wrl):
    """[(bbox_lo, bbox_hi, {rgb: triangles})] per top-level VRML child, board coordinates (y to the rear),
    plus the board layers (index None)."""
    p = asm3d._Parser(asm3d._tokens(open(wrl).read()))
    roots = []
    while p.peek() is not None:
        roots.append(p.node())
    top = roots[0]
    m0 = asm3d._transform_matrix(top["f"])
    out = []
    for k in top["f"].get("children", []):
        groups = asm3d.read_vrml_node(k, m0)
        pts = [q for tris in groups.values() for t in tris for q in t]
        if not pts:
            continue
        lo = [min(q[j] for q in pts) for j in range(3)]
        hi = [max(q[j] for q in pts) for j in range(3)]
        out.append((lo, hi, groups))
    return out


def match_refs(comps):
    """Which VRML child is which part: the smallest box (x/y) that contains the footprint's origin."""
    refs = {}
    for ref, (x, y, rot, side) in LL.PLACE.items():
        if ref.startswith(("H", "M")):
            continue
        best = None
        for i, (lo, hi, _) in enumerate(comps):
            if hi[0] - lo[0] > 50 or hi[2] - lo[2] < 0.2:
                continue
            # VRML: y to the FRONT (= -board y)
            if lo[0] - 0.6 <= x <= hi[0] + 0.6 and lo[1] - 0.6 <= -y <= hi[1] + 0.6:
                area = (hi[0] - lo[0]) * (hi[1] - lo[1])
                if best is None or area < best[0]:
                    best = (area, i)
        if best:
            refs[ref] = best[1]
    return refs


def shade(rgb, n, pale=False):
    lx, ly, lz = LIGHT
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    d = max(0.0, (n[0] * lx + n[1] * ly + n[2] * lz) / ln)
    k = 0.45 + 0.55 * d
    c = [min(1.0, v * k) for v in rgb]
    if pale:
        g = 0.55 * (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) + 0.45 * 0.92
        c = [0.35 * v + 0.65 * g for v in c]
    return tuple(int(255 * v) for v in c)


def render(comps, refs, step, out):
    bottom = step == 14
    W, H = int((X1 - X0) * S), int((Y1 - Y0) * S)
    im = Image.new("RGB", (W, H), (250, 250, 248))
    now = {refs[r] for r in STEPS[step] if r in refs}
    before = {refs[r] for n, rs in STEPS.items() if n < step for r in rs if r in refs}
    if bottom:                                   # the bottom-side parts of earlier steps are all on the top
        before = set()

    def P(q):
        x = (X1 - q[0]) if bottom else (q[0] - X0)      # from below: mirrored, front still at the top
        return (x * S, -q[1] * S)

    tris = []
    halo = []
    for i, (lo, hi, groups) in enumerate(comps):
        is_board = hi[0] - lo[0] > 50 or hi[2] - lo[2] < 0.2     # board body, copper, mask, silk layers
        if not (is_board or i in now or i in before):
            continue
        for rgb, ts in groups.items():
            for t in ts:
                a, b, c = t
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
                n = (n[0] / ln, n[1] / ln, n[2] / ln)
                if bottom:
                    n = (-n[0], n[1], -n[2])
                    if n[2] < 0:
                        n = (-n[0], -n[1], -n[2])
                elif n[2] < 0:
                    n = (-n[0], -n[1], -n[2])            # flat shading of either side (KiCad faces are not oriented)
                z = max(-q[2] for q in t) if bottom else max(q[2] for q in t)
                if not bottom and z < -0.85 and not is_board:
                    continue                             # leads under the board
                tris.append((z, [P(q) for q in t], shade(rgb, n, pale=(i in before))))
        if i in now:
            halo.append((lo, hi))
    # yellow halo under the parts of this step
    hl = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hl)
    for lo, hi in halo:
        xa, ya = P((lo[0], hi[1], 0))
        xb, yb = P((hi[0], lo[1], 0))
        xa, xb = sorted((xa, xb))
        hd.rounded_rectangle([xa - 1.6 * S, ya - 1.6 * S, xb + 1.6 * S, yb + 1.6 * S], radius=int(1.6 * S), fill=255)
    hl = hl.filter(ImageFilter.GaussianBlur(4))
    tris.sort(key=lambda t: t[0])
    d = ImageDraw.Draw(im)
    halo_drawn = False
    for z, pts, col in tris:
        if not halo_drawn and z > 0.9:           # board surface done -> halo -> parts
            im.paste(Image.new("RGB", (W, H), (255, 214, 10)), (0, 0), hl.point(lambda v: int(v * 0.8)))
            d = ImageDraw.Draw(im)
            halo_drawn = True
        d.polygon(pts, fill=col)
    if not halo_drawn:
        im.paste(Image.new("RGB", (W, H), (255, 214, 10)), (0, 0), hl.point(lambda v: int(v * 0.8)))
    im = im.resize((W * 2 // 3, H * 2 // 3), Image.LANCZOS)
    im.save(out, optimize=True)


def main(wrl):
    comps = components(wrl)
    refs = match_refs(comps)
    missing = [r for rs in STEPS.values() for r in rs if r not in refs]
    assert not missing, missing
    os.makedirs(os.path.join(ROOT, "lite", "docs", "steps"), exist_ok=True)
    for step in STEPS:
        out = os.path.join(ROOT, "lite", "docs", "steps", "step_%02d.png" % step)
        render(comps, refs, step, out)
        print("step %2d: %-16s -> %s" % (step, ",".join(STEPS[step]), os.path.relpath(out, ROOT)))


if __name__ == "__main__":
    main(sys.argv[1])
