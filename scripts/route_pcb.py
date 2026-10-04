#!/usr/bin/env python3
"""Routing pipeline.

  scripts/kpy route_pcb.py export      # (KiCad python) board -> Linetracer2.dsn
  python3      route_pcb.py autoroute   # (host) strip GND from DSN, run Freerouting -> .ses
  scripts/kpy route_pcb.py import      # (KiCad python) .ses -> board, add GND pours, fill, save

GND is not autorouted: both copper layers get a GND pour instead.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_env import KDIR, PROJ  # noqa: E402

PCB = os.path.join(KDIR, PROJ + ".kicad_pcb")
DSN = os.path.join(KDIR, "reports", PROJ + ".dsn")
DSN_R = os.path.join(KDIR, "reports", PROJ + "_route.dsn")
SES = os.path.join(KDIR, "reports", PROJ + ".ses")
JAVA = os.path.expanduser("~/.local/opt/jre25/bin/java")
JAR = os.path.expanduser("~/.local/opt/freerouting-2.4.1.jar")
OX, OY = 100.0, 50.0


def export(keep=False):
    """keep=False: clean start.  keep=True: lock existing tracks (2nd pass for GND)."""
    import pcbnew
    b = pcbnew.LoadBoard(PCB)
    for z in list(b.Zones()):
        b.Remove(z)
    for t in list(b.GetTracks()):
        if keep:
            t.SetLocked(True)
        else:
            b.Remove(t)
    pcbnew.SaveBoard(PCB, b)
    ok = pcbnew.ExportSpecctraDSN(b, DSN)
    print("export DSN", ok, DSN)


def _strip_net(txt, net):
    # remove "(net NAME (pins ...))" block from the network section
    i = txt.find("(net %s\n" % net)
    if i < 0:
        i = txt.find("(net %s " % net)
    if i < 0:
        return txt
    depth, j = 0, i
    while True:
        c = txt[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    txt = txt[:i] + txt[j + 1:]
    # remove from class net lists
    txt = re.sub(r"(\(class [^\n]*?)\s%s(?=[\s)])" % re.escape(net), r"\1", txt)
    return txt


def autoroute(passes=40, strip_gnd=False):
    txt = open(DSN).read()
    if strip_gnd:
        txt = _strip_net(txt, "GND")
    open(DSN_R, "w").write(txt)
    if os.path.exists(SES):
        os.remove(SES)
    cmd = [JAVA, "-Djava.awt.headless=true", "-jar", JAR, "-de", DSN_R, "-do", SES,
           "-mp", str(passes), "--gui.enabled=false"]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    tail = (r.stdout + r.stderr).strip().splitlines()[-25:]
    print("\n".join(tail))
    print("SES exists:", os.path.exists(SES))


def add_gnd_zones(board):
    import pcbnew
    gnd = board.FindNet("GND")
    for layer, prio in ((pcbnew.B_Cu, 0), (pcbnew.F_Cu, 0)):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNetCode(gnd.GetNetCode())
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((-1, -1), (101, -1), (101, 101), (-1, 101)):
            ol.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetThermalReliefGap(pcbnew.FromMM(0.5))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(prio)
        z.SetZoneName("GND_%s" % ("B" if layer == pcbnew.B_Cu else "F"))
        board.Add(z)


def do_import(pour=True):
    import pcbnew
    b = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ImportSpecctraSES(b, SES)
    print("import SES", ok)
    for t in b.GetTracks():
        t.SetLocked(False)
    for z in list(b.Zones()):
        b.Remove(z)
    if pour:
        add_gnd_zones(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    n_tr = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_TRACK")
    n_via = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print("tracks", n_tr, "vias", n_via)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "export":
        export(keep="--keep" in sys.argv)
    elif cmd == "autoroute":
        autoroute(int(sys.argv[2]) if len(sys.argv) > 2 else 40, strip_gnd="--strip-gnd" in sys.argv)
    elif cmd == "import":
        do_import(pour="--no-pour" not in sys.argv)
