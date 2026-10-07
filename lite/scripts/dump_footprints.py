#!/usr/bin/env python3
"""Pad geometry of every footprint in the Lite netlist -> .tmp/fpdump.json, for preview_layout.py.
    cd scripts && LT2_VARIANT=lite ./kpy ../lite/scripts/dump_footprints.py
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import pcbnew, gen_pcb as G
comps, pinnet = G.read_netlist()
os.makedirs(os.path.join(ROOT, ".tmp"), exist_ok=True)
board = pcbnew.NewBoard(os.path.join(ROOT, ".tmp", "x.kicad_pcb"))
out = {}
M = pcbnew.ToMM
for ref, c in comps.items():
    fpn = c["footprint"]
    if fpn in out: continue
    nick, name = fpn.split(":")
    fp = pcbnew.FootprintLoad(G.lib_path(nick), name)
    board.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    pads = []
    for p in fp.Pads():
        q = p.GetPosition(); s = p.GetSize(pcbnew.F_Cu)
        pads.append(dict(num=p.GetNumber(), x=M(q.x), y=M(q.y), sx=M(s.x), sy=M(s.y),
                         shape=str(p.GetShape(pcbnew.F_Cu)), drill=M(p.GetDrillSize().x)))
    lines = []
    for it in fp.GraphicalItems():
        if it.GetClass() != "PCB_SHAPE":
            continue
        L = it.GetLayer()
        tag = {pcbnew.F_Fab: "fab", pcbnew.F_SilkS: "silk", pcbnew.F_CrtYd: "crt"}.get(L)
        if not tag: continue
        sh = it.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            a, b = it.GetStart(), it.GetEnd(); lines.append(["L", M(a.x), M(a.y), M(b.x), M(b.y), tag])
        elif sh == pcbnew.SHAPE_T_CIRCLE:
            c0 = it.GetCenter(); lines.append(["C", M(c0.x), M(c0.y), M(it.GetRadius()), 0, tag])
        elif sh == pcbnew.SHAPE_T_RECT:
            a, b = it.GetStart(), it.GetEnd(); lines.append(["R", M(a.x), M(a.y), M(b.x), M(b.y), tag])
        elif sh == pcbnew.SHAPE_T_ARC:
            a, b, m = it.GetStart(), it.GetEnd(), it.GetArcMid(); lines.append(["A", M(a.x), M(a.y), M(m.x), M(m.y), M(b.x), M(b.y), tag])
        elif sh == pcbnew.SHAPE_T_POLY:
            pts = [(M(v.x), M(v.y)) for v in it.GetPolyPoints()] if hasattr(it, "GetPolyPoints") else []
            lines.append(["P", pts, tag])
    out[fpn] = dict(pads=pads, lines=lines)
json.dump(dict(fps=out, comps={r: c["footprint"] for r, c in comps.items()},
               pinnet={"%s:%s" % k: v for k, v in pinnet.items()}),
          open(os.path.join(ROOT, ".tmp", "fpdump.json"), "w"))
print("%d footprints -> .tmp/fpdump.json" % len(out))
sys.stdout.flush()
os._exit(0)
