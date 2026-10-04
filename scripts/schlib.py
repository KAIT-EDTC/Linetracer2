"""Tiny schematic builder for KiCad (writes KiCad 9 format; kicad-cli upgrades it)."""
import copy
import math
import os

import sexpr
from sexpr import Q
from kicad_env import LIBDIR, PROJ, uid, sym_dir

GRID = 1.27


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def rot_vec(x, y, ang):
    """Rotate a sheet vector (y down) counter-clockwise (as displayed) by ang degrees."""
    a = math.radians(ang)
    c, s = round(math.cos(a)), round(math.sin(a))
    return (x * c + y * s, -x * s + y * c)


DIRS = {(1, 0): "right", (-1, 0): "left", (0, -1): "up", (0, 1): "down"}


class LibCache:
    def __init__(self):
        self.libs = {}

    def _lib(self, lib):
        if lib not in self.libs:
            if lib == PROJ:
                path = os.path.join(LIBDIR, PROJ + ".kicad_sym")
            else:
                path = os.path.join(sym_dir(), lib + ".kicad_sym")
            self.libs[lib] = sexpr.parse(open(path).read())
        return self.libs[lib]

    def symbol(self, lib, name):
        L = self._lib(lib)
        for s in sexpr.find_all(L, "symbol"):
            if s[1] == name:
                ext = sexpr.find(s, "extends")
                if ext is None:
                    return copy.deepcopy(s)
                parent = self.symbol(lib, ext[1])
                new = copy.deepcopy(parent)
                new[1] = Q(name)
                child = {p[1]: p for p in sexpr.find_all(s, "property")}
                for i, x in enumerate(new):
                    if isinstance(x, list) and x and x[0] == "property" and x[1] in child:
                        new[i] = copy.deepcopy(child.pop(x[1]))
                for p in child.values():
                    new.insert(2, copy.deepcopy(p))
                for x in new:
                    if isinstance(x, list) and x and x[0] == "symbol":
                        x[1] = Q(x[1].replace(ext[1], name, 1))
                return new
        raise KeyError("%s:%s" % (lib, name))


def symbol_pins(sym):
    pins = {}

    def walk(n):
        for x in n:
            if isinstance(x, list) and x and x[0] == "pin":
                at = sexpr.find(x, "at")
                num = sexpr.find(x, "number")[1]
                name = sexpr.find(x, "name")[1]
                pins.setdefault(str(num), []).append(
                    (float(at[1]), float(at[2]), float(at[3]), str(name), x[1]))
            elif isinstance(x, list) and x and x[0] == "symbol":
                walk(x)
    walk(sym)
    return pins


class Inst:
    def __init__(self, sch, lib_id, ref, x, y, rot, pins):
        self.sch, self.lib_id, self.ref, self.x, self.y, self.rot = sch, lib_id, ref, x, y, rot
        self._pins = pins

    def pin(self, num):
        px, py, pang, name, kind = self._pins[str(num)][0]
        ox, oy = rot_vec(px, -py, self.rot)
        # outward direction = opposite of pin direction
        a = math.radians(pang + 180)
        dx, dy = round(math.cos(a)), round(-math.sin(a))
        dx, dy = rot_vec(dx, dy, self.rot)
        return (snap(self.x + ox), snap(self.y + oy), (int(dx), int(dy)))


class Sch:
    def __init__(self, title, paper="A3"):
        self.root = uid("sch/root")
        self.cache = LibCache()
        self.libsyms = {}
        self.items = []
        self.title = title
        self.paper = paper
        self.n = 0
        self.npwr = 0
        self.nflg = 0
        self.points = []   # label points for sanity

    def _u(self, key=None):
        self.n += 1
        return uid("sch/%s/%d" % (key or "item", self.n))

    # ------------------------------------------------------------------ symbols
    def _ensure(self, lib_id):
        if lib_id not in self.libsyms:
            lib, name = lib_id.split(":", 1)
            s = self.cache.symbol(lib, name)
            s[1] = Q(lib_id)
            self.libsyms[lib_id] = s
        return self.libsyms[lib_id]

    def place(self, lib_id, ref, value, x, y, rot=0, footprint=None, fields=None,
              hide_ref=False, hide_val=False, in_bom=True, ref_off=None, val_off=None, just="left"):
        s = self._ensure(lib_id)
        pins = symbol_pins(s)
        x, y = snap(x), snap(y)
        u = uid("sym/" + ref)
        props = []
        libprops = {p[1]: p for p in sexpr.find_all(s, "property")}

        # KiCad toggles field orientation for symbols rotated 90/270, so store 90
        # there to get horizontal (readable) text on the sheet.
        fang = 90 if rot in (90, 270) else 0
        # ...and it mirrors the justification for 90/180, so ask for "right" to get left-aligned text
        if just == "center":
            jtxt = ""
        else:
            fj = {"left": "right", "right": "left"}[just] if rot in (90, 180) else just
            jtxt = " (justify %s)" % fj

        def ptext(name, val, dx, dy, hide):
            h = "(hide yes)" if hide else ""
            return '(property "%s" "%s" (at %s %s %d) %s (effects (font (size 1.27 1.27))%s))' % (
                name, val.replace('"', "'"), snap(x + dx), snap(y + dy), fang, h, jtxt)

        # reference/value offsets: default to the right of the symbol
        if ref_off is None or val_off is None:
            lp = libprops.get("Reference")
            rx, ry = (float(lp[3][1]), -float(lp[3][2])) if lp else (2.54, -1.27)
            lv = libprops.get("Value")
            vx, vy = (float(lv[3][1]), -float(lv[3][2])) if lv else (2.54, 1.27)
            if ref_off is None:
                ref_off = rot_vec(rx, ry, rot)
            if val_off is None:
                val_off = rot_vec(vx, vy, rot)
        props.append(ptext("Reference", ref, ref_off[0], ref_off[1], hide_ref))
        props.append(ptext("Value", value, val_off[0], val_off[1], hide_val))
        fp = footprint if footprint is not None else (libprops["Footprint"][2] if "Footprint" in libprops else "")
        props.append(ptext("Footprint", fp, 0, 0, True))
        ds = libprops["Datasheet"][2] if "Datasheet" in libprops else ""
        props.append(ptext("Datasheet", ds, 0, 0, True))
        de = libprops["Description"][2] if "Description" in libprops else ""
        props.append(ptext("Description", de, 0, 0, True))
        for k, v in (fields or {}).items():
            props.append(ptext(k, v, 0, 0, True))
        pin_entries = " ".join('(pin "%s" (uuid "%s"))' % (num, uid("pin/%s/%s" % (ref, num)))
                               for num in sorted(pins, key=lambda t: (len(t), t)))
        txt = ('(symbol (lib_id "%s") (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp no) (uuid "%s") %s %s '
               '(instances (project "%s" (path "/%s" (reference "%s") (unit 1)))))'
               % (lib_id, x, y, rot, "yes" if in_bom else "no", u, " ".join(props), pin_entries, PROJ, self.root, ref))
        self.items.append(sexpr.parse(txt))
        return Inst(self, lib_id, ref, x, y, rot, pins)

    def power(self, kind, x, y, out_dir):
        """kind: 'GND', '+3V3', 'PWR_FLAG'. out_dir: direction the symbol should point."""
        if kind == "GND":
            rot = {"down": 0, "right": 90, "left": 270, "up": 180}[out_dir]
        else:
            rot = {"up": 0, "left": 90, "right": 270, "down": 180}[out_dir]
        if kind == "PWR_FLAG":
            self.nflg += 1
            ref = "#FLG%02d" % self.nflg
        else:
            self.npwr += 1
            ref = "#PWR%02d" % self.npwr
        lib_id = "power:" + kind
        if out_dir in ("up", "down"):
            off, j = (0.0, -3.81 if out_dir == "up" else 3.81), "center"
        elif out_dir == "left":
            off, j = (-3.81, 0.0), "right"
        else:
            off, j = (3.81, 0.0), "left"
        return self.place(lib_id, ref, kind, x, y, rot, hide_ref=True, val_off=off, ref_off=(0, 0), just=j)

    # ------------------------------------------------------------------ wiring
    def wire(self, x1, y1, x2, y2):
        if (x1, y1) == (x2, y2):
            return
        self.items.append(sexpr.parse(
            '(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'
            % (snap(x1), snap(y1), snap(x2), snap(y2), self._u("w"))))

    def path(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.wire(a[0], a[1], b[0], b[1])

    def junction(self, x, y):
        self.items.append(sexpr.parse('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
                                      % (snap(x), snap(y), self._u("j"))))

    def label(self, name, x, y, direction="right"):
        ang = {"right": 0, "left": 180, "up": 90, "down": 270}[direction]
        just = "left" if direction in ("right", "up") else "right"
        self.items.append(sexpr.parse(
            '(label "%s" (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
            % (name, snap(x), snap(y), ang, just, self._u("l"))))

    def nc(self, inst, num):
        x, y, _ = inst.pin(num)
        self.items.append(sexpr.parse('(no_connect (at %s %s) (uuid "%s"))' % (x, y, self._u("nc"))))

    def text(self, s, x, y, size=1.27, bold=False):
        b = " (bold yes)" if bold else ""
        s = s.replace('"', "'")
        self.items.append(sexpr.parse(
            '(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) (justify left bottom)) (uuid "%s"))'
            % (s, snap(x), snap(y), size, size, b, self._u("t"))))

    def rect(self, x1, y1, x2, y2):
        self.items.append(sexpr.parse(
            '(rectangle (start %s %s) (end %s %s) (stroke (width 0.2) (type dash)) (fill (type none)) (uuid "%s"))'
            % (snap(x1), snap(y1), snap(x2), snap(y2), self._u("r"))))

    # high level helpers -------------------------------------------------------
    def stub_end(self, inst, num, length=2.54):
        x, y, (dx, dy) = inst.pin(num)
        ex, ey = x + dx * length, y + dy * length
        self.wire(x, y, ex, ey)
        return ex, ey, DIRS[(dx, dy)]

    def lab(self, inst, num, name, length=2.54):
        ex, ey, d = self.stub_end(inst, num, length)
        self.label(name, ex, ey, d)

    def pwr(self, inst, num, kind, length=2.54):
        ex, ey, d = self.stub_end(inst, num, length)
        self.power(kind, ex, ey, d)

    def connect(self, a, an, b, bn, corner="hv"):
        x1, y1, _ = a.pin(an)
        x2, y2, _ = b.pin(bn)
        if x1 == x2 or y1 == y2:
            self.wire(x1, y1, x2, y2)
        elif corner == "hv":
            self.path((x1, y1), (x2, y1), (x2, y2))
        else:
            self.path((x1, y1), (x1, y2), (x2, y2))

    # ------------------------------------------------------------------ output
    def save(self, path, date="2026-10-04", rev="A", company="EDTC", comments=()):
        tb = '(title_block (title "%s") (date "%s") (rev "%s") (company "%s")' % (self.title, date, rev, company)
        for i, c in enumerate(comments):
            tb += ' (comment %d "%s")' % (i + 1, c)
        tb += ")"
        head = ('(kicad_sch (version 20250610) (generator "eeschema") (generator_version "9.99") '
                '(uuid "%s") (paper "%s") %s)' % (self.root, self.paper, tb))
        node = sexpr.parse(head)
        node.append(["lib_symbols"] + list(self.libsyms.values()))
        node.extend(self.items)
        node.append(sexpr.parse('(sheet_instances (path "/" (page "1")))'))
        node.append(["embedded_fonts", "no"])
        open(path, "w").write(sexpr.dump(node) + "\n")
        print("wrote", path)
