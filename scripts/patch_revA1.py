#!/usr/bin/env python3
"""rev.A -> rev.A1 board patch (run with scripts/kpy).  Nothing is moved or re-routed.

* BZ1: footprint Buzzer_Beeper:Buzzer_12x9.5RM7.6 -> Linetracer2:Buzzer_12mm_P7.6_P5.0
  (extra GND hole 5.0 mm from pin 1 so the 13 mm Akizuki piezo PKM13EPYH4000-A0, pitch 5.0, fits;
  the new hole is joined to GND by the copper pour, no new tracks)
* values / fields / nets refreshed from the netlist (D4 is now 'LED yellow-green')
* silkscreen revision label rev.A -> rev.A1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
import gen_pcb as G  # noqa: E402

b = pcbnew.LoadBoard(G.PCB)
comps, pinnet = G.read_netlist()
fps = {f.GetReference(): f for f in b.GetFootprints()}

old = fps["BZ1"]
want = comps["BZ1"]["footprint"]
if str(old.GetFPID().GetLibItemName()) != want.split(":")[1]:
    nick, name = want.split(":")
    new = pcbnew.FootprintLoad(G.lib_path(nick), name)
    new.SetFPID(pcbnew.LIB_ID(nick, name))
    new.SetReference("BZ1")
    new.SetValue(comps["BZ1"]["value"])
    new.SetPosition(old.GetPosition())
    new.SetOrientation(old.GetOrientation())
    # keep the hand-placed reference text
    r_old, r_new = old.Reference(), new.Reference()
    r_new.SetPosition(r_old.GetPosition())
    r_new.SetTextSize(r_old.GetTextSize())
    r_new.SetTextThickness(r_old.GetTextThickness())
    r_new.SetVisible(r_old.IsVisible())
    new.Value().SetVisible(old.Value().IsVisible())
    # same 3D body as before (12 mm buzzer, origin = pin 1)
    for m in old.Models():
        mm = pcbnew.FP_3DMODEL()
        mm.m_Filename = m.m_Filename
        mm.m_Offset, mm.m_Rotation, mm.m_Scale = m.m_Offset, m.m_Rotation, m.m_Scale
        new.Models().push_back(mm)
    b.Remove(old)
    b.Add(new)
    print("BZ1 footprint ->", want)

G.apply_netlist(b, comps, pinnet)
for f in b.GetFootprints():
    c = comps.get(f.GetReference())
    if c and f.GetValue() != c["value"]:
        print("value", f.GetReference(), f.GetValue(), "->", c["value"])
        f.SetValue(c["value"])

for d in b.Drawings():
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith("rev.A "):
        d.SetText(d.GetText().replace("rev.A ", "rev.A1 ", 1))
        print("label ->", d.GetText())

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(G.PCB, b)
print("saved", flush=True)
os._exit(0)
