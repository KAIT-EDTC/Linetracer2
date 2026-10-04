#!/usr/bin/env python3
"""Very simple VRML (.wrl) 3D models for the project footprints (boxes only).
KiCad reads .wrl in units of 0.1 inch, so everything is written in mm and scaled by 1/2.54.
KiCad 3D axes: x right, y = towards the TOP of the footprint (footprint -y), z up."""
import os
from kicad_env import LIBDIR

OUT = os.path.join(LIBDIR, "3d")


def box(cx, cy, cz, sx, sy, sz, rgb):
    return ("Transform { translation %.4f %.4f %.4f children [ Shape { appearance Appearance { material Material "
            "{ diffuseColor %.2f %.2f %.2f specularColor 0.2 0.2 0.2 } } geometry Box { size %.4f %.4f %.4f } } ] }\n"
            % (cx, cy, cz + sz / 2, rgb[0], rgb[1], rgb[2], sx, sy, sz))


def write(name, shapes):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".wrl"), "w") as f:
        f.write("#VRML V2.0 utf8\nTransform { scale %.6f %.6f %.6f children [\n" % ((1 / 2.54,) * 3))
        f.write("".join(shapes))
        f.write("] }\n")
    print("wrote", name)


BLACK, GOLD, GREEN, WHITE = (0.08, 0.08, 0.08), (0.85, 0.7, 0.2), (0.1, 0.45, 0.25), (0.92, 0.92, 0.88)

# Akizuki AE-TC78H653FTG (origin = module centre, pin rows at x = +-3.81)
m = [box(sx * 3.81, 0, 0, 2.54, 20.32, 2.5, BLACK) for sx in (-1, 1)]
m += [box(sx * 3.81, -8.89 + 2.54 * i, -3.0, 0.64, 0.64, 11.5, GOLD) for sx in (-1, 1) for i in range(8)]
m += [box(0, 0, 2.5, 10.0, 20.0, 1.0, GREEN), box(0, -0.6, 3.5, 3.0, 3.0, 0.9, BLACK),
      box(0, 6.2, 3.5, 3.2, 1.6, 1.6, (0.75, 0.6, 0.4)), box(0, 3.6, 3.5, 1.0, 0.5, 0.5, (0.75, 0.6, 0.4))]
write("AE-TC78H653FTG", m)

# LBR-123F: body 2.7 x 3.4 x 1.5, two lens windows on the far side
s = [box(0, 0, 0, 2.7, 3.4, 1.5, BLACK), box(0, -0.9, 1.5, 1.6, 1.3, 0.05, (0.3, 0.0, 0.0)),
     box(0, 0.9, 1.5, 1.6, 1.3, 0.05, (0.15, 0.15, 0.2))]
s += [box(sx * 1.6, sy * 0.9, -3.0, 0.5, 0.15, 3.0, GOLD) for sx in (-1, 1) for sy in (-1, 1)]
write("LBR-123F", s)

# JST XH 2P (B2B-XH-A) at pins (0,0) and (2.5,0); body y from -2.45 .. +3.3 in footprint coords
x = [box(1.25, -0.425, 0, 7.4, 5.75, 7.0, WHITE)]
x += [box(px, 0, -3.0, 0.64, 0.64, 9.5, GOLD) for px in (0, 2.5)]
write("BatteryXH_2P", x)
