#!/usr/bin/env python3
"""Whole-robot 3D model: the KiCad board with its parts (VRML export) + the printed / bought mechanical parts
(OpenSCAD STL exports), merged into one STL (for GitHub's 3D viewer, slicers, CAD) and one coloured GLB.

    python3 asm3d.py BOARD.wrl OUT_BASENAME  part.stl:#rrggbb [part.stl:#rrggbb ...]

Coordinates of the output = KiCad's 3D frame (mm): x right, y = towards the FRONT of the robot, z up; origin =
the board's (0, 0) corner, the PCB top at z = 0.  (KiCad: export vrml --units mm --user-origin 100x50mm.)
The OpenSCAD parts use x right, y towards the REAR (= board y), z up from the PCB top - a left-handed frame in the
real world - so they are turned 180 deg about x = 50 on the way in (see main()).  Pure python (no numpy).
"""
import json
import math
import re
import struct
import sys

# ------------------------------------------------------------------ VRML (the subset KiCad writes)
_TOK = re.compile(r'"[^"]*"|[{}\[\]]|[^\s,{}\[\]]+')


def _tokens(text):
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.extend(_TOK.findall(line))
    return out


def _isnum(t):
    try:
        float(t)
        return True
    except ValueError:
        return t in ("TRUE", "FALSE")


class _Parser:
    def __init__(self, toks):
        self.t, self.i, self.defs = toks, 0, {}

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else None

    def next(self):
        self.i += 1
        return self.t[self.i - 1]

    def node(self):
        tok = self.next()
        if tok == "DEF":
            name = self.next()
            n = self.node()
            self.defs[name] = n
            return n
        if tok == "USE":
            return self.defs[self.next()]
        ntype = tok
        assert self.next() == "{", ntype
        fields = {}
        while self.peek() != "}":
            fname = self.next()
            fields[fname] = self.value()
        self.next()
        return {"type": ntype, "f": fields}

    def _starts_node(self):
        p = self.peek()
        return p in ("DEF", "USE") or (p is not None and not _isnum(p) and self.peek(1) == "{")

    def value(self):
        if self.peek() == "[":
            self.next()
            items = []
            while self.peek() != "]":
                if self._starts_node():
                    items.append(self.node())
                else:
                    tok = self.next()
                    items.append(float(tok) if _isnum(tok) and tok not in ("TRUE", "FALSE") else tok)
            self.next()
            return items
        if self._starts_node():
            return self.node()
        vals = []
        while self.peek() is not None and self.peek() not in ("}",) and (_isnum(self.peek()) or self.peek().startswith('"')):
            tok = self.next()
            vals.append(float(tok) if _isnum(tok) and tok not in ("TRUE", "FALSE") else tok)
        return vals


def _mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _ident():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


def _trans(v):
    m = _ident()
    m[0][3], m[1][3], m[2][3] = v
    return m


def _scale(v):
    m = _ident()
    m[0][0], m[1][1], m[2][2] = v
    return m


def _rot(r):
    x, y, z, a = r
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    x, y, z = x / n, y / n, z / n
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0],
            [0, 0, 0, 1]]


def _transform_matrix(f):
    T = _trans(f.get("translation", [0, 0, 0]))
    C = _trans(f.get("center", [0, 0, 0]))
    Ci = _trans([-v for v in f.get("center", [0, 0, 0])])
    R = _rot(f.get("rotation", [0, 0, 1, 0]))
    so = f.get("scaleOrientation", [0, 0, 1, 0])
    SR, SRi = _rot(so), _rot(so[:3] + [-so[3]])
    S = _scale(f.get("scale", [1, 1, 1]))
    m = T
    for x in (C, R, SR, S, SRi, Ci):
        m = _mat_mul(m, x)
    return m


def read_vrml(path):
    """-> {rgb: [triangles]} with triangles ((x,y,z),(x,y,z),(x,y,z))"""
    p = _Parser(_tokens(open(path).read()))
    roots = []
    while p.peek() is not None:
        roots.append(p.node())
    out = {}

    def walk(n, m):
        if n["type"] == "Transform" or n["type"] == "Group":
            mm = _mat_mul(m, _transform_matrix(n["f"])) if n["type"] == "Transform" else m
            for c in n["f"].get("children", []):
                walk(c, mm)
        elif n["type"] == "Shape":
            g = n["f"].get("geometry")
            if not g or g["type"] != "IndexedFaceSet":
                return
            col = (0.6, 0.6, 0.6)
            app = n["f"].get("appearance")
            if app and app["f"].get("material"):
                d = app["f"]["material"]["f"].get("diffuseColor")
                if d:
                    col = tuple(round(v, 3) for v in d)
            pts = g["f"]["coord"]["f"]["point"]
            P = [(pts[k], pts[k + 1], pts[k + 2]) for k in range(0, len(pts) - 2, 3)]
            W = [(m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
                  m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
                  m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3]) for x, y, z in P]
            tris = out.setdefault(col, [])
            face = []
            for v in g["f"].get("coordIndex", []):
                v = int(v)
                if v < 0:
                    for k in range(1, len(face) - 1):
                        tris.append((W[face[0]], W[face[k]], W[face[k + 1]]))
                    face = []
                else:
                    face.append(v)
            for k in range(1, len(face) - 1):
                tris.append((W[face[0]], W[face[k]], W[face[k + 1]]))

    for r in roots:
        walk(r, _ident())
    return out


# ------------------------------------------------------------------ STL in / out
def read_stl(path):
    data = open(path, "rb").read()
    tris = []
    if data[:5] == b"solid" and b"facet" in data[:512]:
        v = [tuple(map(float, l.split()[1:4])) for l in data.decode(errors="ignore").splitlines() if l.strip().startswith("vertex")]
        tris = [(v[k], v[k + 1], v[k + 2]) for k in range(0, len(v) - 2, 3)]
    else:
        n = struct.unpack("<I", data[80:84])[0]
        for k in range(n):
            f = struct.unpack("<12f", data[84 + 50 * k: 84 + 50 * k + 48])
            tris.append((f[3:6], f[6:9], f[9:12]))
    return tris


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"Linetracer2 Lite assembly".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            nx, ny, nz = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            f.write(struct.pack("<12fH", nx / ln, ny / ln, nz / ln, *a, *b, *c, 0))


def write_glb(path, groups):
    """groups: [(rgb, triangles)] -> binary glTF, one primitive per colour, flat shading."""
    buf = bytearray()
    accessors, views, meshes_prims, materials = [], [], [], []
    for gi, (rgb, tris) in enumerate(groups):
        if not tris:
            continue
        verts = [p for t in tris for p in t]
        pos = struct.pack("<%df" % (3 * len(verts)), *[c for p in verts for c in p])
        while len(buf) % 4:
            buf.append(0)
        views.append({"buffer": 0, "byteOffset": len(buf), "byteLength": len(pos), "target": 34962})
        buf += pos
        mn = [min(p[k] for p in verts) for k in range(3)]
        mx = [max(p[k] for p in verts) for k in range(3)]
        accessors.append({"bufferView": len(views) - 1, "componentType": 5126, "count": len(verts), "type": "VEC3",
                          "min": mn, "max": mx})
        materials.append({"pbrMetallicRoughness": {"baseColorFactor": [rgb[0], rgb[1], rgb[2], 1.0],
                                                   "metallicFactor": 0.1, "roughnessFactor": 0.7},
                          "doubleSided": True})
        meshes_prims.append({"attributes": {"POSITION": len(accessors) - 1}, "material": len(materials) - 1})
    gl = {"asset": {"version": "2.0", "generator": "Linetracer2 asm3d.py"},
          "scene": 0, "scenes": [{"nodes": [0]}],
          # glTF is y-up: rotate our z-up model -90 deg about x
          "nodes": [{"mesh": 0, "rotation": [-0.7071068, 0, 0, 0.7071068]}],
          "meshes": [{"primitives": meshes_prims}],
          "materials": materials, "accessors": accessors, "bufferViews": views,
          "buffers": [{"byteLength": len(buf)}]}
    js = json.dumps(gl).encode()
    while len(js) % 4:
        js += b" "
    while len(buf) % 4:
        buf.append(0)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(buf), 0x004E4942) + bytes(buf))


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[k:k + 2], 16) / 255.0 for k in (0, 2, 4))


def main(argv):
    wrl, outbase = argv[0], argv[1]
    board = read_vrml(wrl)
    # KiCad centres the 1.6 mm board on z = 0: move it down 0.8 mm so that the PCB top is z = 0, like the OpenSCAD parts
    groups = [(rgb, [tuple((p[0], p[1], p[2] - 0.8) for p in t) for t in tris]) for rgb, tris in board.items()]
    print("board: %d colours, %d triangles" % (len(groups), sum(len(t) for _, t in groups)))
    for spec in argv[2:]:
        path, col = spec.rsplit(":", 1)
        tris = read_stl(path)
        # OpenSCAD frame (board coordinates: y to the rear, z up) -> KiCad 3D frame (y to the front, z up).
        # The OpenSCAD frame is left-handed in the real world, so a printed STL is the MIRROR IMAGE of the part as
        # drawn in the scad assembly.  Turning every piece 180 deg about the robot's centre line (x = 50) instead of
        # mirroring it shows the parts as they really come off the printer: the drawn left frame lands on the right,
        # which is where that printed part fits (symmetric parts look the same either way).
        tris = [((100 - a[0], -a[1], a[2]), (100 - b[0], -b[1], b[2]), (100 - c[0], -c[1], c[2])) for a, b, c in tris]
        groups.append((hexrgb(col), tris))
        print("%-40s %7d triangles" % (path.split("/")[-1], len(tris)))
    allt = [t for _, tris in groups for t in tris]
    write_stl(outbase + ".stl", allt)
    write_glb(outbase + ".glb", groups)
    print("wrote %s.stl / .glb: %d triangles" % (outbase, len(allt)))
    split = __import__("os").environ.get("ASM_SPLIT_DIR")
    if split:                     # one STL per colour + an OpenSCAD scene that shows them coloured (for pictures)
        lines = []
        for k, (rgb, tris) in enumerate(groups):
            write_stl("%s/g%02d.stl" % (split, k), tris)
            lines.append('color([%.3f, %.3f, %.3f]) import("g%02d.stl");' % (rgb[0], rgb[1], rgb[2], k))
        open(split + "/scene.scad", "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
