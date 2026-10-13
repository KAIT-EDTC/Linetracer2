#!/usr/bin/env python3
"""Hand routing of the Lite board (from scripts/: LT2_VARIANT=lite ./kpy ../lite/scripts/route_lite.py).

Puts the tracks described in layout_lite.py into the placed board (gen_pcb_lite.py), adds the GND pours on both
sides and fills them.  Deterministic: no autorouter.  GND has no tracks at all - every GND pad is a through-hole
pad and reaches the bottom pour, which only two short signal tracks cut into.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))
import pcbnew  # noqa: E402
import gen_pcb as G  # noqa: E402
import route_pcb as RP  # noqa: E402
import layout_lite as LL  # noqa: E402


def main():
    b = pcbnew.LoadBoard(G.PCB)
    for t in list(b.GetTracks()):
        b.Remove(t)
    for z in list(b.Zones()):
        if not z.GetIsRuleArea():
            b.Remove(z)
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref, num):
        for p in fps[ref].Pads():
            if p.GetNumber() == num:
                return p
        raise KeyError((ref, num))

    def padpos(ref, num):
        q = pad(ref, num).GetPosition()
        return pcbnew.ToMM(q.x) - G.OX, pcbnew.ToMM(q.y) - G.OY

    n_seg = 0
    for r, (name, layer, w, pts) in zip(LL.ROUTES, LL.paths(padpos)):
        nets = {pad(p[1], p[2]).GetNetname() for p in r["pts"] if isinstance(p, tuple) and p and p[0] == "pad"}
        assert len(nets) == 1, (name, nets)
        net = b.FindNet(nets.pop())
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(G.P(x1, y1))
            t.SetEnd(G.P(x2, y2))
            t.SetWidth(G.mm(w))
            t.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
            t.SetNet(net)
            b.Add(t)
            n_seg += 1
    for x, y, netname in LL.VIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(G.P(x, y))
        v.SetDrill(G.mm(0.4))
        v.SetWidth(G.mm(0.8))
        v.SetNet(b.FindNet(netname))
        b.Add(v)
    RP.add_gnd_zones(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(G.PCB, b)
    print("hand routes: %d segments, %d vias" % (n_seg, len(LL.VIAS)), flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
