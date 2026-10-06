#!/usr/bin/env python3
"""Very simple VRML (.wrl) 3D models for the project footprints (boxes only).
KiCad reads .wrl in units of 0.1 inch: every box is written as an IndexedFaceSet whose corner points are
converted from mm (/2.54).  (A "Transform { scale 0.3937 }" around "Transform { translation }" does NOT work:
KiCad scales the box sizes but not the translations, so off-centre parts landed 2.54 x too close to the origin.)
KiCad 3D axes: x right, y = towards the TOP of the footprint (footprint -y), z up."""
import os
from kicad_env import LIBDIR

OUT = os.path.join(LIBDIR, "3d")


def box(cx, cy, cz, sx, sy, sz, rgb):
    """Box centred on (cx, cy) in x/y, standing on z = cz, sizes sx/sy/sz (all mm)."""
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz, cz + sz
    pts = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    faces = "0 2 3 1 -1 4 5 7 6 -1 0 1 5 4 -1 2 6 7 3 -1 0 4 6 2 -1 1 3 7 5 -1"
    return ("Shape { appearance Appearance { material Material { diffuseColor %.2f %.2f %.2f specularColor 0.2 0.2 0.2 } } "
            "geometry IndexedFaceSet { coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n"
            % (rgb[0], rgb[1], rgb[2], ", ".join("%.4f %.4f %.4f" % (x / 2.54, y / 2.54, z / 2.54) for x, y, z in pts),
               faces))


def write(name, shapes):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".wrl"), "w") as f:
        f.write("#VRML V2.0 utf8\n")
        f.write("".join(shapes))
    print("wrote", name)


BLACK, GOLD, GREEN, WHITE = (0.08, 0.08, 0.08), (0.85, 0.7, 0.2), (0.1, 0.45, 0.25), (0.92, 0.92, 0.88)

# Akizuki AE-TC78H653FTG (origin = module centre, pin rows at x = +-3.81)
m = [box(sx * 3.81, 0, 0, 2.54, 20.32, 2.5, BLACK) for sx in (-1, 1)]
m += [box(sx * 3.81, -8.89 + 2.54 * i, -3.0, 0.64, 0.64, 7.5, GOLD) for sx in (-1, 1) for i in range(8)]   # 1 mm above the module
m += [box(0, 0, 2.5, 10.0, 20.0, 1.0, GREEN), box(0, -0.6, 3.5, 3.0, 3.0, 0.9, BLACK),
      box(0, 6.2, 3.5, 3.2, 1.6, 1.6, (0.75, 0.6, 0.4)), box(0, 3.6, 3.5, 1.0, 0.5, 0.5, (0.75, 0.6, 0.4))]
write("AE-TC78H653FTG", m)

# LBR-123F: body 2.7 x 3.4 x 1.5, two lens windows on the far side
s = [box(0, 0, 0, 2.7, 3.4, 1.5, BLACK), box(0, -0.9, 1.5, 1.6, 1.3, 0.05, (0.3, 0.0, 0.0)),
     box(0, 0.9, 1.5, 1.6, 1.3, 0.05, (0.15, 0.15, 0.2))]
s += [box(sx * 1.6, sy * 0.9, -3.0, 0.5, 0.15, 3.0, GOLD) for sx in (-1, 1) for sy in (-1, 1)]
write("LBR-123F", s)

# LBR-127HLD: body 8.7 x 4.5 x 5.6, lens windows (d 2.9) at x = +-1.8 (LED right, photo transistor left)
s = [box(0, 0, 0, 8.7, 4.5, 5.6, BLACK), box(1.8, 0, 5.6, 2.6, 2.6, 0.05, (0.3, 0.0, 0.0)),
     box(-1.8, 0, 5.6, 2.6, 2.6, 0.05, (0.15, 0.15, 0.2))]
s += [box(sx * 2.05, sy * 1.27, -3.0, 0.5, 0.5, 3.0, GOLD) for sx in (-1, 1) for sy in (-1, 1)]
write("LBR-127HLD", s)

# Seeed XIAO ESP32C6 lying flat on the board (footprint origin = pin pattern centre, USB at footprint -y).
# Positions from Seeed's KiCad design; 3D y = -footprint y.
SILVER, KHAKI, BLUE = (0.78, 0.78, 0.8), (0.76, 0.69, 0.5), (0.12, 0.16, 0.3)
x = [box(0, 0.06, 0, 17.8, 20.98, 1.0, BLUE),
     box(0, 8.4, 1.0, 8.94, 7.3, 3.2, SILVER),          # USB-C receptacle, 1.5 mm past the module end
     box(2.93, -1.56, 1.0, 5.0, 5.0, 0.85, BLACK),      # ESP32-C6
     box(3.12, -9.26, 1.0, 5.2, 2.0, 1.1, KHAKI)]       # chip antenna
x += [box(sx * 8.5, -7.62 + 2.54 * i, 0, 0.8, 1.3, 1.02, GOLD) for sx in (-1, 1) for i in range(7)]   # castellations
write("XIAO_ESP32C6_DirectSolder", x)

# JST XH 2P (B2B-XH-A) at pins (0,0) and (2.5,0); body y from -2.45 .. +3.3 in footprint coords
x = [box(1.25, -0.425, 0, 7.4, 5.75, 7.0, WHITE)]
x += [box(px, 0, -3.0, 0.64, 0.64, 9.5, GOLD) for px in (0, 2.5)]
write("BatteryXH_2P", x)
