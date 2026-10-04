#!/usr/bin/env python3
"""Regenerate the PCB and keep the best of N autorouter runs.
    python3 build_pcb.py 6                     # standard board
    LT2_VARIANT=lite python3 build_pcb.py 6    # Lite board

placement -> route signals (GND excluded) -> lock -> route GND -> GND pours -> post (silk etc.) -> DRC
Freerouting is not deterministic; each attempt is scored (must be fully connected with no
clearance errors; then shortest total track length + 2 mm per via + 20 mm per dangling-track warning wins).
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kicad_env import KDIR, PROJ, VARIANT  # noqa: E402

PCB = os.path.join(KDIR, PROJ + ".kicad_pcb")
RPT = os.path.join(KDIR, "reports", "drc.rpt")
SUFFIX = "_lite" if VARIANT == "lite" else ""      # gen_pcb_lite.py / post_pcb_lite.py for the Lite board


def run(*cmd, quiet=True):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if not quiet:
        print(out)
    return out


def score():
    out = run("./kpy", "-c", """
import pcbnew
b = pcbnew.LoadBoard(%r)
L = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
V = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
print('SCORE', round(L, 1), V)
""" % PCB)
    m = re.search(r"SCORE ([\d.]+) (\d+)", out)
    return float(m.group(1)), int(m.group(2))


def attempt(i):
    run("./kpy", "gen_pcb%s.py" % SUFFIX)
    run("./kpy", "route_pcb.py", "export")
    o1 = run("python3", "route_pcb.py", "autoroute", "60", "--strip-gnd")
    run("./kpy", "route_pcb.py", "import", "--no-pour")
    run("./kpy", "route_pcb.py", "export", "--keep")
    o2 = run("python3", "route_pcb.py", "autoroute", "60")
    run("./kpy", "route_pcb.py", "import")
    for step in ("prune", "silk"):
        out = run("./kpy", "post_pcb%s.py" % SUFFIX, step)
        if "post %s done" % step not in out:
            print("post_pcb %s failed:" % step, out.strip().splitlines()[-3:])
    run("./kc", "pcb", "drc", "--severity-all", "--refill-zones", "-o", RPT, PCB)
    rpt = open(RPT).read()
    unc = len(re.findall(r"^\[unconnected_items\]", rpt, re.M))
    err = len(re.findall(r"^\[(clearance|shorting_items|tracks_crossing|hole_clearance|copper_edge_clearance|"
                         r"items_not_allowed)\]", rpt, re.M))
    dang = len(re.findall(r"^\[track_dangling\]", rpt, re.M))
    L, V = score()
    print("attempt %d: unconnected=%d errors=%d length=%.1fmm vias=%d dangling=%d" % (i, unc, err, L, V, dang))
    return unc, err, L + 2 * V + 20 * dang


def main(n):
    best = None
    for i in range(1, n + 1):
        unc, err, cost = attempt(i)
        if unc == 0 and err == 0 and (best is None or cost < best[0]):
            best = (cost, i)
            shutil.copy(PCB, PCB + ".best")
            shutil.copy(RPT, RPT + ".best")
    if best is None:
        sys.exit("no clean attempt")
    shutil.copy(PCB + ".best", PCB)
    shutil.copy(RPT + ".best", RPT)
    os.remove(PCB + ".best")
    os.remove(RPT + ".best")
    print("best attempt", best[1], "cost", round(best[0], 1))
    print(open(RPT).read().split("** Found")[0][-200:])


if __name__ == "__main__":
    run("python3", "gen_project.py")
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
