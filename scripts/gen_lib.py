#!/usr/bin/env python3
"""Generate the project-local symbol & footprint library (Linetracer2).

Outputs (with LT2_VARIANT=lite: the same files under lite/hardware/kicad/lib/)
  hardware/kicad/lib/Linetracer2.kicad_sym
  hardware/kicad/lib/Linetracer2.pretty/*.kicad_mod

Run:  python3 scripts/gen_lib.py   (then `kicad-cli sym/fp upgrade` is run by build.sh)
"""
import copy
import os

import sexpr
from sexpr import Q
from kicad_env import LIBDIR, uid, sym_dir

FONT = "(effects (font (size 1.27 1.27)))"


# --------------------------------------------------------------------------
# symbols
# --------------------------------------------------------------------------
def pin(kind, x, y, ang, name, num, length=2.54, hidden=False):
    h = " (hide yes)" if hidden else ""
    return ('(pin %s line (at %s %s %d) (length %s)%s (name "%s" %s) (number "%s" %s))'
            % (kind, x, y, ang, length, h, name, FONT, num, FONT))


def prop(name, value, x=0, y=0, hide=False, justify=None):
    h = " (hide yes)" if hide else ""
    j = " (justify %s)" % justify if justify else ""
    return '(property "%s" "%s" (at %s %s 0)%s (effects (font (size 1.27 1.27))%s))' % (
        name, value, x, y, h, j)


def sym_module():
    """Akizuki AE-TC78H653FTG (DIP16-like module). Pin order = physical order."""
    left = [("1", "LARGE", "input"), ("2", "MODE", "input"), ("3", "STBY", "input"),
            ("4", "IN4", "input"), ("5", "IN3", "input"), ("6", "IN1", "input"),
            ("7", "IN2", "input"), ("8", "GND", "power_in")]
    right = [("16", "VM", "power_in"), ("15", "VM", "power_in"), ("14", "OUT4", "output"),
             ("13", "OUT3", "output"), ("12", "OUT1", "output"), ("11", "OUT2", "output"),
             ("10", "GND", "power_in"), ("9", "GND", "power_in")]
    ys = [8.89, 6.35, 3.81, 1.27, -1.27, -3.81, -6.35, -8.89]
    pins = [pin(k, -12.7, y, 0, n, num) for (num, n, k), y in zip(left, ys)]
    pins += [pin(k, 12.7, y, 180, n, num) for (num, n, k), y in zip(right, ys)]
    return """(symbol "AE-TC78H653FTG"
  (pin_names (offset 1.016))
  (exclude_from_sim no) (in_bom yes) (on_board yes)
  %s
  %s
  %s
  %s
  %s
  %s
  (symbol "AE-TC78H653FTG_0_1"
    (rectangle (start -10.16 11.43) (end 10.16 -11.43) (stroke (width 0.254) (type default)) (fill (type background)))
  )
  (symbol "AE-TC78H653FTG_1_1"
    %s
  )
  (embedded_fonts no)
)""" % (
        prop("Reference", "U", 0, 13.97),
        prop("Value", "AE-TC78H653FTG", 0, -13.97),
        prop("Footprint", "Linetracer2:AE-TC78H653FTG", 0, -16.51, hide=True),
        prop("Datasheet", "https://akizukidenshi.com/catalog/g/g114746/", 0, -19.05, hide=True),
        prop("Description", "Akizuki TC78H653FTG dual H-bridge module (1.8-7.5V, 2A/ch small mode). DIP16 pin header", 0, -21.59, hide=True),
        prop("ki_keywords", "motor driver H-bridge TC78H653FTG module", 0, 0, hide=True),
        "\n    ".join(pins))


def sym_reflector(name="LBR-123F", datasheet="https://akizukidenshi.com/goodsaffix/lbr-123f.pdf",
                  descr="Reflective photo sensor (IR LED + NPN phototransistor), Letex LBR-123F (TPR-105F successor)"):
    """Letex reflective photo sensor (LBR-123F, LBR-127HLD: same pin numbers). 1=A 2=K 3=E 4=C."""
    g = """
    (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
    (polyline (pts (xy -5.08 2.54) (xy -2.54 2.54) (xy -2.54 1.016)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy -5.08 -2.54) (xy -2.54 -2.54) (xy -2.54 -0.762)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy -3.556 1.016) (xy -1.524 1.016) (xy -2.54 -0.762) (xy -3.556 1.016)) (stroke (width 0.254) (type default)) (fill (type outline)))
    (polyline (pts (xy -3.556 -0.762) (xy -1.524 -0.762)) (stroke (width 0.254) (type default)) (fill (type none)))
    (polyline (pts (xy -1.016 0.508) (xy 0.762 -0.254)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 0.762 -0.254) (xy 0.254 -0.254) (xy 0.508 0.127) (xy 0.762 -0.254)) (stroke (width 0) (type default)) (fill (type outline)))
    (polyline (pts (xy -1.016 -0.508) (xy 0.762 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 0.762 -1.27) (xy 0.254 -1.27) (xy 0.508 -0.889) (xy 0.762 -1.27)) (stroke (width 0) (type default)) (fill (type outline)))
    (polyline (pts (xy 2.032 1.524) (xy 2.032 -1.524)) (stroke (width 0.3) (type default)) (fill (type none)))
    (polyline (pts (xy 2.032 0.508) (xy 3.81 2.032) (xy 3.81 2.54) (xy 5.08 2.54)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 2.032 -0.508) (xy 3.81 -2.032) (xy 3.81 -2.54) (xy 5.08 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 3.81 -2.032) (xy 3.302 -1.27) (xy 2.921 -1.778) (xy 3.81 -2.032)) (stroke (width 0) (type default)) (fill (type outline)))
"""
    pins = [pin("passive", -7.62, 2.54, 0, "A", "1"), pin("passive", -7.62, -2.54, 0, "K", "2"),
            pin("passive", 7.62, -2.54, 180, "E", "3"), pin("passive", 7.62, 2.54, 180, "C", "4")]
    return """(symbol "%s"
  (pin_names (offset 0.254) (hide yes))
  (exclude_from_sim no) (in_bom yes) (on_board yes)
  %s
  %s
  %s
  %s
  %s
  (symbol "%s_0_1"%s  )
  (symbol "%s_1_1"
    %s
  )
  (embedded_fonts no)
)""" % (
        name,
        prop("Reference", "PS", -5.08, 5.08, justify="left"),
        prop("Value", name, -5.08, -5.08, justify="left"),
        prop("Footprint", "Linetracer2:" + name, 0, -7.62, hide=True),
        prop("Datasheet", datasheet, 0, -10.16, hide=True),
        prop("Description", descr, 0, -12.7, hide=True),
        name, g, name, "\n    ".join(pins))


def sym_xiao():
    """Seeed Studio XIAO ESP32C6 (14 castellated pins). Drawn like the board seen from above with the USB up:
    left 1..7 = D0..D6, right 14..8 = 5V, GND, 3V3, D10..D7.  Names: GPIO number / XIAO name."""
    left = [("1", "GPIO0/A0/D0"), ("2", "GPIO1/A1/D1"), ("3", "GPIO2/A2/D2"), ("4", "GPIO21/D3"),
            ("5", "GPIO22/SDA/D4"), ("6", "GPIO23/SCL/D5"), ("7", "GPIO16/TX/D6")]
    right = [("14", "5V", "power_in"), ("13", "GND", "power_in"), ("12", "3V3", "power_out"),
             ("11", "GPIO18/MOSI/D10", "bidirectional"), ("10", "GPIO20/MISO/D9", "bidirectional"),
             ("9", "GPIO19/SCK/D8", "bidirectional"), ("8", "GPIO17/RX/D7", "bidirectional")]
    ys = [7.62, 5.08, 2.54, 0, -2.54, -5.08, -7.62]
    pins = [pin("bidirectional", -22.86, y, 0, n, num) for (num, n), y in zip(left, ys)]
    pins += [pin(k, 22.86, y, 180, n, num) for (num, n, k), y in zip(right, ys)]
    return """(symbol "XIAO_ESP32C6"
  (pin_names (offset 1.016))
  (exclude_from_sim no) (in_bom yes) (on_board yes)
  %s
  %s
  %s
  %s
  %s
  %s
  (symbol "XIAO_ESP32C6_0_1"
    (rectangle (start -20.32 10.16) (end 20.32 -10.16) (stroke (width 0.254) (type default)) (fill (type background)))
    (rectangle (start -3.81 12.7) (end 3.81 10.16) (stroke (width 0.254) (type default)) (fill (type none)))
  )
  (symbol "XIAO_ESP32C6_1_1"
    %s
  )
  (embedded_fonts no)
)""" % (
        prop("Reference", "U", 0, 15.24),
        prop("Value", "XIAO_ESP32C6", 0, -12.7),
        prop("Footprint", "Linetracer2:XIAO_ESP32C6_DirectSolder", 0, -15.24, hide=True),
        prop("Datasheet", "https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/", 0, -17.78, hide=True),
        prop("Description", "Seeed Studio XIAO ESP32C6 (ESP32-C6, Wi-Fi 6 / BLE 5 / 802.15.4). 5V pin = USB VBUS = power input "
             "(through an external diode), 3V3 = output of the on-board regulator", 0, -20.32, hide=True),
        prop("ki_keywords", "XIAO ESP32C6 Seeed module castellated", 0, 0, hide=True),
        "\n    ".join(pins))


def sym_pico():
    """Copy of KiCad MCU_Module:RaspberryPi_Pico, AGND made passive (it is tied to GND)."""
    lib = sexpr.parse(open(os.path.join(sym_dir(), "MCU_Module.kicad_sym")).read())
    src = None
    for s in sexpr.find_all(lib, "symbol"):
        if s[1] == "RaspberryPi_Pico":
            src = copy.deepcopy(s)
    assert src is not None

    def walk(n):
        for x in n:
            if isinstance(x, list) and x and x[0] == "pin":
                name = sexpr.find(x, "name")[1]
                if name == "AGND":
                    x[1] = "passive"
            elif isinstance(x, list):
                walk(x)
    walk(src)
    src[1] = Q("RaspberryPi_Pico_THT")
    for x in src:
        if isinstance(x, list) and x and x[0] == "symbol":
            x[1] = Q(x[1].replace("RaspberryPi_Pico", "RaspberryPi_Pico_THT", 1))
    fp = sexpr.get_prop(src, "Footprint")
    fp[2] = Q("Module:RaspberryPi_Pico_Common_THT")
    d = sexpr.get_prop(src, "Description")
    if d is not None:
        d[2] = Q("Raspberry Pi Pico / Pico 2 (through-hole, soldered with 2.54mm pin headers). AGND set to passive.")
    return sexpr.dump(src, 1)


def write_symbols():
    txt = "(kicad_symbol_lib\n\t(version 20241209)\n\t(generator \"linetracer2_gen\")\n\t(generator_version \"9.0\")\n"
    lbr127 = sym_reflector("LBR-127HLD", "https://akizukidenshi.com/goodsaffix/lbr127hld.pdf",
                           "Reflective photo sensor (IR LED + NPN phototransistor), Letex LBR-127HLD, body 8.7 x 4.5 x 5.6 mm")
    for s in (sym_module(), sym_reflector(), lbr127, sym_xiao()):
        node = sexpr.parse(s)
        txt += sexpr.dump(node, 1) + "\n"
    txt += sym_pico() + "\n)\n"
    path = os.path.join(LIBDIR, "Linetracer2.kicad_sym")
    open(path, "w").write(txt)
    print("wrote", path)


# --------------------------------------------------------------------------
# footprints
# --------------------------------------------------------------------------
class FP:
    def __init__(self, name, descr, tags, attr="through_hole"):
        self.name = name
        self.items = []
        self.descr = descr
        self.tags = tags
        self.attr = attr
        self.n = 0
        self.tail = []          # raw items written after everything else (zones, STEP models)

    def _u(self):
        self.n += 1
        return uid("fp/%s/%d" % (self.name, self.n))

    def line(self, x1, y1, x2, y2, layer="F.SilkS", w=0.12):
        self.items.append('(fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s") (uuid "%s"))'
                          % (x1, y1, x2, y2, w, layer, self._u()))

    def rect(self, x1, y1, x2, y2, layer="F.SilkS", w=0.12):
        self.items.append('(fp_rect (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill no) (layer "%s") (uuid "%s"))'
                          % (x1, y1, x2, y2, w, layer, self._u()))

    def circle(self, cx, cy, r, layer="F.SilkS", w=0.12, fill=False):
        self.items.append('(fp_circle (center %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill %s) (layer "%s") (uuid "%s"))'
                          % (cx, cy, cx + r, cy, w, "yes" if fill else "no", layer, self._u()))

    def arc(self, sx, sy, mx, my, ex, ey, layer="F.SilkS", w=0.12):
        self.items.append('(fp_arc (start %s %s) (mid %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s") (uuid "%s"))'
                          % (sx, sy, mx, my, ex, ey, w, layer, self._u()))

    def text(self, s, x, y, layer="F.SilkS", size=1.0, thick=0.15, justify=None, rot=0):
        j = " (justify %s)" % justify if justify else ""
        self.items.append('(fp_text user "%s" (at %s %s %s) (layer "%s") (uuid "%s") (effects (font (size %s %s) (thickness %s))%s))'
                          % (s, x, y, rot, layer, self._u(), size, size, thick, j))

    def pad(self, num, x, y, shape, sx, sy, drill, kind="thru_hole", offset=None):
        if kind == "np_thru_hole":
            self.items.append('(pad "" np_thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (uuid "%s"))'
                              % (x, y, sx, sy, drill, self._u()))
            return
        extra = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
        # offset: the pad shape is shifted from the hole (hole stays at x, y)
        dr = "(drill %s (offset %s %s))" % (drill, offset[0], offset[1]) if offset else "(drill %s)" % drill
        self.items.append('(pad "%s" thru_hole %s (at %s %s) (size %s %s) %s (layers "*.Cu" "*.Mask")%s (uuid "%s"))'
                          % (num, shape, x, y, sx, sy, dr, extra, self._u()))

    def keepout(self, name, layers, x1, y1, x2, y2, pads=False):
        """Rectangular rule area inside the footprint: no tracks, vias or copper pour (pads only if pads=True)."""
        self.tail.append(
            '(zone (layers %s) (uuid "%s") (name "%s") (hatch full 0.5) (connect_pads (clearance 0)) '
            '(min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads %s) '
            '(copperpour not_allowed) (footprints allowed)) (placement (enabled no) (sheetname "")) '
            '(fill (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 0)) '
            '(polygon (pts (xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s))))'
            % (" ".join('"%s"' % la for la in layers), self._u(), name, "allowed" if pads else "not_allowed",
               x1, y1, x2, y1, x2, y2, x1, y2))

    def write(self, ref_xy, val_xy, ref_layer="F.SilkS"):
        out = ['(footprint "%s"' % self.name,
               '(version 20241229)', '(generator "linetracer2_gen")', '(generator_version "9.0")',
               '(layer "F.Cu")', '(descr "%s")' % self.descr, '(tags "%s")' % self.tags,
               '(property "Reference" "REF**" (at %s %s 0) (layer "%s") (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))'
               % (ref_xy[0], ref_xy[1], ref_layer, self._u()),
               '(property "Value" "%s" (at %s %s 0) (layer "F.Fab") (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))'
               % (self.name, val_xy[0], val_xy[1], self._u()),
               '(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1.27 1.27) (thickness 0.15))))' % self._u(),
               '(property "Description" "%s" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1.27 1.27) (thickness 0.15))))' % (self.descr, self._u()),
               '(attr %s)' % self.attr]
        out += self.items
        out += self.tail
        if os.path.exists(os.path.join(LIBDIR, "3d", self.name + ".wrl")):
            out.append('(model "${KIPRJMOD}/lib/3d/%s.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
                       % self.name)
        out.append("(embedded_fonts no)")
        out.append(")")
        node = sexpr.parse("\n".join(out))
        d = os.path.join(LIBDIR, "Linetracer2.pretty")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, self.name + ".kicad_mod")
        open(path, "w").write(sexpr.dump(node) + "\n")
        print("wrote", path)


def fp_module():
    f = FP("AE-TC78H653FTG",
           "Akizuki AE-TC78H653FTG motor driver module, 2x8 pin header, row spacing 7.62mm, origin at module centre",
           "TC78H653FTG motor driver module DIP16")
    for i in range(8):
        y = round(-8.89 + 2.54 * i, 3)
        f.pad(str(i + 1), -3.81, y, "rect" if i == 0 else "circle", 1.8, 1.8, 1.0)
        f.pad(str(16 - i), 3.81, y, "circle", 1.8, 1.8, 1.0)
    # module outline (10 x 20 mm) with notch on pin-1 end (same as the module's own silk)
    f.line(-5, -10.1, -1.2, -10.1)
    f.line(1.2, -10.1, 5, -10.1)
    f.arc(-1.2, -10.1, 0, -8.9, 1.2, -10.1)
    f.line(-5, -10.1, -5, 10.1)
    f.line(5, -10.1, 5, 10.1)
    f.line(-5, 10.1, 5, 10.1)
    f.text("1", -5.9, -8.89, size=0.8, thick=0.15)
    f.text("VM", 6.2, -7.62, size=0.8, thick=0.15, rot=90)
    f.text("GND", 6.2, 7.62, size=0.8, thick=0.15, rot=90)
    f.text("TC78H653", 0, 0, size=0.8, thick=0.15, rot=90)
    f.rect(-5, -10, 5, 10, layer="F.Fab", w=0.1)
    f.rect(-5.4, -10.5, 5.4, 10.5, layer="F.CrtYd", w=0.05)
    f.write((0, -11.5), (0, 11.5))


def fp_reflector():
    """LBR-123F. Drawn as seen from the component side = sensing face.
    Place this footprint on the BOTTOM side so the lens looks at the floor."""
    f = FP("LBR-123F",
           "Letex LBR-123F / TPR-105F reflective sensor, leads 3.7mm x 1.8mm. Mount on bottom side (lens to floor)",
           "photo reflector line sensor LBR-123F TPR-105")
    f.pad("1", -1.85, 0.9, "rect", 1.6, 1.15, 0.7)     # A  (LED)
    f.pad("2", 1.85, 0.9, "oval", 1.6, 1.15, 0.7)      # K
    f.pad("3", -1.85, -0.9, "oval", 1.6, 1.15, 0.7)    # E  (photo transistor)
    f.pad("4", 1.85, -0.9, "oval", 1.6, 1.15, 0.7)     # C
    # body 2.7 x 3.4 (silk only above/below the pads)
    f.line(-1.35, -2.0, 1.35, -2.0)
    f.line(-0.95, 2.0, 1.35, 2.0)
    f.line(-1.35, 1.6, -0.95, 2.0)        # chamfer = pin-1 corner (datasheet "c0.4")
    f.circle(-3.4, 1.6, 0.15, w=0.3)     # pin-1 dot
    f.rect(-1.35, -1.7, 1.35, 1.7, layer="F.Fab", w=0.1)
    f.text("LED", 0, 0.9, layer="F.Fab", size=0.5, thick=0.08)
    f.text("PT", 0, -0.9, layer="F.Fab", size=0.5, thick=0.08)
    f.rect(-2.95, -2.3, 2.95, 2.3, layer="F.CrtYd", w=0.05)
    f.write((0, -3.2), (0, 3.2))


def fp_lbr127hld():
    """LBR-127HLD.  Drawn as seen from the lens face (datasheet "Top View"): photo transistor left
    (3 = E, 4 = C), LED right (1 = A, 2 = K), corner chamfer c0.5 next to pin 1.
    Leads 0.5 mm square, 4.1 mm (x) x 2.54 mm (y).  Place this footprint on the BOTTOM side."""
    f = FP("LBR-127HLD",
           "Letex LBR-127HLD reflective sensor, body 8.7 x 4.5 x 5.6 mm, leads 4.1 x 2.54 mm. Mount on bottom side (lens to floor)",
           "photo reflector line sensor LBR-127HLD")
    f.pad("1", 2.05, -1.27, "rect", 1.6, 1.6, 0.9)      # A  (LED)
    f.pad("2", 2.05, 1.27, "circle", 1.6, 1.6, 0.9)     # K
    f.pad("3", -2.05, -1.27, "circle", 1.6, 1.6, 0.9)   # E  (photo transistor)
    f.pad("4", -2.05, 1.27, "circle", 1.6, 1.6, 0.9)    # C
    # body 8.7 x 4.5 with the c0.5 chamfer at the pin-1 corner
    f.line(-4.35, -2.25, 3.85, -2.25)
    f.line(3.85, -2.25, 4.35, -1.75)
    f.line(4.35, -1.75, 4.35, 2.25)
    f.line(4.35, 2.25, -4.35, 2.25)
    f.line(-4.35, 2.25, -4.35, -2.25)
    f.circle(5.0, -1.27, 0.15, w=0.3)    # pin-1 dot
    f.rect(-4.35, -2.25, 4.35, 2.25, layer="F.Fab", w=0.1)
    for x in (-1.8, 1.8):
        f.circle(x, 0, 1.45, layer="F.Fab", w=0.1)     # lens windows (diameter 2.9)
    f.text("PT", -1.8, 0, layer="F.Fab", size=0.6, thick=0.1)
    f.text("LED", 1.8, 0, layer="F.Fab", size=0.6, thick=0.1)
    f.rect(-4.6, -2.5, 4.6, 2.5, layer="F.CrtYd", w=0.05)
    f.write((0, -3.4), (0, 3.4))


def fp_battery_xh():
    f = FP("BatteryXH_2P",
           "Battery input, JST XH 2P (B2B-XH-A) header OR direct wire soldering. Symmetric silk: orient by wire colour (red=+)",
           "battery JST XH B2B-XH-A")
    f.pad("1", 0, 0, "rect", 1.8, 2.2, 1.0)
    f.pad("2", 2.5, 0, "oval", 1.8, 2.2, 1.0)
    f.rect(-2.45, -2.45, 4.95, 3.3)
    f.text("+", -3.4, 0, size=1.5, thick=0.3)
    f.text("-", 5.9, 0, size=1.5, thick=0.3)
    f.text("RED", 0, 4.4, size=0.8, thick=0.15)
    f.text("BLK", 2.5, 4.4, size=0.8, thick=0.15)
    f.rect(-2.45, -2.45, 4.95, 3.3, layer="F.Fab", w=0.1)
    f.rect(-2.95, -2.95, 5.45, 3.8, layer="F.CrtYd", w=0.05)     # body + 0.5 mm (the +/- and RED/BLK texts may overhang)
    f.write((1.25, -3.6), (1.25, 6.2))


def fp_motor_pads():
    f = FP("MotorPads_2P_Relief",
           "Motor wire solder pads, pitch 5.08mm, with strain-relief holes (pass the wire through the small hole first)",
           "motor wire solder pad relief")
    f.pad("1", 0, 0, "rect", 2.3, 2.3, 1.1)
    f.pad("2", 5.08, 0, "circle", 2.3, 2.3, 1.1)
    f.pad("", 0, -3.4, None, 1.7, 1.7, 1.7, kind="np_thru_hole")
    f.pad("", 5.08, -3.4, None, 1.7, 1.7, 1.7, kind="np_thru_hole")
    f.text("+", -2.3, 1.9, size=1.2, thick=0.25)
    f.text("-", 7.3, 1.9, size=1.2, thick=0.25)
    f.rect(-1.8, -4.8, 6.9, 1.8, layer="F.CrtYd", w=0.05)
    f.write((2.54, 2.9), (2.54, 4.4))


def fp_buzzer():
    """Passive piezo sounder, two pin pitches sharing pin 1:
    13 mm Murata PKM13EPYH4000-A0 (Akizuki 104118, pitch 5.0) -> holes 1 + middle
    12 mm generic (pitch 7.6)                                  -> holes 1 + right
    The 13 mm body overhangs the board edge by about 1 mm (R18 is too close on the other side)."""
    f = FP("Buzzer_P5.0_P7.6",
           "Passive piezo sounder: 13mm PKM13EPYH4000-A0 (pitch 5.0: pin 1 + middle hole) or 12mm (pitch 7.6: pin 1 + right hole)",
           "buzzer piezo PKM13EPYH4000")
    f.pad("1", 0, 0, "rect", 1.8, 1.8, 1.0)
    f.pad("2", 5.0, 0, "circle", 1.8, 1.8, 1.0)
    f.pad("2", 7.6, 0, "circle", 1.8, 1.8, 1.0)
    f.circle(3.8, 0, 6.1)                        # 12 mm body (silk, as the KiCad stock footprint)
    f.circle(2.5, 0, 6.3, layer="F.Fab", w=0.1)  # 13 mm body
    f.circle(3.8, 0, 6.0, layer="F.Fab", w=0.1)
    f.text("+", 1.7, -2.0, size=1.2, thick=0.25)
    f.text("13", 5.0, 1.9, size=0.8, thick=0.15)
    f.text("12", 7.6, 1.9, size=0.8, thick=0.15)
    f.circle(3.0, 0, 7.05, layer="F.CrtYd", w=0.05)
    f.write((3.8, -7.4), (3.8, 7.6))


def fp_xiao_direct():
    """Seeed Studio XIAO ESP32C6 soldered FLAT on the board without pin headers (Lite board).

    Origin = centre of the pin pattern, USB at the top (-y), pin 1 (D0) top-left.
    Each pin is ONE through-hole pad: the hole sits under the XIAO's own header hole (7.62 mm from the
    centre, a pin header still fits), and the copper is stretched outwards to 1.9 mm past the module's
    edge (8.9 mm), so the iron touches the board pad and the castellated half-hole at the same time.
    Positions measured in Seeed's KiCad design of the XIAO ESP32C6 (v1.0, 2026-01-14):
      * bare test pads on the XIAO's bottom (BAT+ / GND, 3V3, BOOT, EN, JTAG MTMS/MTDI/MTCK/MTDO) all lie
        within x +-1.9, y -9.2 .. +6.6  -> F.Cu keep-out (no tracks / vias / pour may touch them)
      * USB-C shell legs (soldered through the XIAO) at x +-4.3, y -9.48 / -5.28 -> clearance holes
      * ceramic chip antenna at the far end (x 0.5 .. 5.7, y 8.3 .. 10.3) -> no copper on either layer
        from y 8.75 up to 4 mm past the module end (keeps the 2.4 GHz antenna working for Wi-Fi / BLE)"""
    f = FP("XIAO_ESP32C6_DirectSolder",
           "Seeed Studio XIAO ESP32C6 soldered flat (no pin header): one THT pad per pin, copper stretched 1.9 mm past "
           "the module edge for castellation soldering. Keep-outs under the bottom test pads and the chip antenna",
           "Seeed XIAO ESP32C6 castellated direct solder no header")
    PITCH, X, PAD_L, PAD_W, OFF = 2.54, 7.62, 4.0, 1.7, 1.2     # pad spans 6.82 .. 10.82 from the centre
    for i in range(7):
        y = round(-7.62 + PITCH * i, 3)
        f.pad(str(i + 1), -X, y, "roundrect" if i == 0 else "oval", PAD_L, PAD_W, 1.0, offset=(-OFF, 0))
        f.pad(str(14 - i), X, y, "oval", PAD_L, PAD_W, 1.0, offset=(OFF, 0))
    for x in (-4.3, 4.3):                                       # USB-C shell legs
        for y in (-9.48, -5.28):
            f.pad("", x, y, None, 1.8, 1.8, 1.8, kind="np_thru_hole")
    f.keepout("XIAO bottom test pads", ["F.Cu"], -2.9, -9.8, 2.9, 7.1, pads=True)
    f.keepout("XIAO antenna", ["F.Cu", "B.Cu"], -8.9, 8.75, 8.9, 14.4)
    # module 17.8 x 21.0 (pin pattern centre 0.06 mm towards the antenna end) + USB-C receptacle 1.5 mm out.
    # The USB end lies on the board edge, so the silkscreen shows the antenna end and the pin-1 mark only.
    f.rect(-8.9, -10.55, 8.9, 10.43, layer="F.Fab", w=0.1)
    f.rect(-4.47, -12.05, 4.47, -4.75, layer="F.Fab", w=0.1)
    f.rect(0.5, 8.3, 5.7, 10.3, layer="F.Fab", w=0.1)
    f.text("ANT", 3.1, 9.3, layer="F.Fab", size=0.6, thick=0.1)
    f.line(-8.9, 10.43, 8.9, 10.43)
    f.line(-8.9, 8.75, -8.9, 10.43)
    f.line(8.9, 8.75, 8.9, 10.43)
    f.text("1", -12.0, -7.62, size=1.0, thick=0.15)
    f.rect(-11.1, -12.3, 11.1, 10.7, layer="F.CrtYd", w=0.05)
    f.write((0, 12.0), (0, 13.5))


def write_footprints():
    fp_xiao_direct()
    fp_buzzer()
    fp_module()
    fp_reflector()
    fp_lbr127hld()
    fp_battery_xh()
    fp_motor_pads()


if __name__ == "__main__":
    os.makedirs(LIBDIR, exist_ok=True)
    write_symbols()
    write_footprints()
