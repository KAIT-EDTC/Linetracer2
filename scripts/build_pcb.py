#!/usr/bin/env python3
"""Regenerate the PCB (Lite board rev.L3).
    python3 build_pcb.py

placement (gen_pcb_lite.py) -> hand-drawn routes (route_lite.py, from layout_lite.py) -> silkscreen
(post_pcb_lite.py silk) -> DRC.  Deterministic: no autorouter.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))

from kicad_env import KDIR, PROJ  # noqa: E402

PCB = os.path.join(KDIR, PROJ + ".kicad_pcb")
RPT = os.path.join(KDIR, "reports", "drc.rpt")


def run(*cmd):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    return r.stdout + r.stderr


def main():
    for cmd in (("./kpy", "gen_pcb_lite.py"), ("./kpy", "route_lite.py"), ("./kpy", "post_pcb_lite.py", "silk")):
        out = run(*cmd)
        print(out.strip().splitlines()[-1] if out.strip() else "(no output)")
    run("./kc", "pcb", "drc", "--severity-all", "--refill-zones", "--schematic-parity", "-o", RPT, PCB)
    print(open(RPT).read().split("** Ignored")[0][-200:])


if __name__ == "__main__":
    run("python3", "gen_project.py")
    main()
