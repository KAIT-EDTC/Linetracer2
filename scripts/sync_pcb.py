#!/usr/bin/env python3
"""Sync the routed board with the current schematic netlist (run with scripts/kpy).

Equivalent to KiCad 'Update PCB from Schematic' for this project: footprint paths, fields
(Akizuki code, notes, description) and pad nets are refreshed; nothing is moved or re-routed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
import gen_pcb as G  # noqa: E402

b = pcbnew.LoadBoard(G.PCB)
comps, pinnet = G.read_netlist()
G.apply_netlist(b, comps, pinnet)
# 3D models of the project footprints (added to footprints placed before the models existed)
for fp in b.GetFootprints():
    name = str(fp.GetFPID().GetLibItemName())
    wrl = os.path.join(G.LIBDIR, "3d", name + ".wrl")
    if str(fp.GetFPID().GetLibNickname()) == G.LIBNICK and os.path.exists(wrl):
        if not any("/lib/3d/" in m.m_Filename for m in fp.Models()):
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = "${KIPRJMOD}/lib/3d/%s.wrl" % name
            fp.Models().push_back(m)
missing = sorted(set(comps) - {f.GetReference() for f in b.GetFootprints()})
print("footprints missing on the board:", missing)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(G.PCB, b)
print("sync done", flush=True)
os._exit(0)
