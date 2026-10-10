#!/bin/sh
# Export everything needed for fabrication and documentation from the KiCad project.
#   ./export_outputs.sh                      standard board (rev.A1)
#   LT2_VARIANT=lite ./export_outputs.sh     Lite board (rev.L3)
#
#                    standard                                   Lite
#   Gerber + drill   hardware/gerber/  (+ zip in hardware/)     lite/hardware/gerber/  (+ zip in lite/hardware/)
#   BOM csv          hardware/kicad/bom/                        lite/hardware/kicad/bom/
#   ERC / DRC        hardware/kicad/reports/                    lite/hardware/kicad/reports/
#   PDFs             docs/                                      lite/docs/
#   3D renders       docs/images/                               lite/docs/
#   3D STEP          hardware/kicad/Linetracer2_pcb.step        lite/hardware/kicad/Linetracer2-Lite_pcb.step
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
KC="$ROOT/scripts/kc"
if [ "${LT2_VARIANT:-std}" = "lite" ]; then
  NAME=Linetracer2-Lite; REV=rev.L3
  HW="$ROOT/lite/hardware"; DOCS="$ROOT/lite/docs"; IMG="$ROOT/lite/docs"
else
  NAME=Linetracer2; REV=rev.A1
  HW="$ROOT/hardware"; DOCS="$ROOT/docs"; IMG="$ROOT/docs/images"
fi
K="$HW/kicad"
PCB="$K/$NAME.kicad_pcb"
SCH="$K/$NAME.kicad_sch"
G="$HW/gerber"
ZIP="${NAME}_${REV}_gerber.zip"
mkdir -p "$G" "$K/bom" "$K/reports" "$DOCS" "$IMG"
rm -f "$G"/*

echo "== ERC / DRC"
$KC sch erc --severity-all -o "$K/reports/erc.rpt" "$SCH" | tail -1
$KC pcb drc --severity-all --refill-zones --schematic-parity -o "$K/reports/drc.rpt" "$PCB" | tail -1

echo "== Gerber / drill"
$KC pcb export gerbers -o "$G" \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" "$PCB" | tail -1
$KC pcb export drill -o "$G/" --format excellon --excellon-units mm \
    --excellon-zeros-format decimal --drill-origin absolute --excellon-separate-th --generate-map --map-format pdf "$PCB" | tail -1
(cd "$G" && rm -f "../$ZIP" && zip -q "../$ZIP" *.g* *.drl)
ls -la "$HW/$ZIP"

echo "== BOM"
$KC sch export bom -o "$K/bom/${NAME}_bom.csv" \
    --fields 'Reference,Value,Footprint,Akizuki,Note,${QUANTITY}' \
    --labels 'Refs,Value,Footprint,Akizuki,Note,Qty' --group-by 'Value,Footprint' "$SCH" | tail -1

echo "== PDFs"
$KC sch export pdf -o "$DOCS/${NAME}_schematic.pdf" "$SCH" | tail -1
# assembly drawings: silkscreen + fab outlines + pad sketches, black on white
$KC pcb export pdf -o "$DOCS/${NAME}_assembly_top.pdf" --mode-single --black-and-white \
    --sketch-pads-on-fab-layers --layers "F.Fab,Edge.Cuts" --include-border-title "$PCB" | tail -1
$KC pcb export pdf -o "$DOCS/${NAME}_assembly_bottom.pdf" --mode-single --black-and-white --mirror \
    --sketch-pads-on-fab-layers --layers "B.Fab,Edge.Cuts" --include-border-title "$PCB" | tail -1

if [ "${LT2_VARIANT:-std}" = "lite" ] && command -v pdftoppm >/dev/null; then
  echo "== silkscreen pictures (what the kids read: top, and the back seen from below)"
  T=$(mktemp -d "$HOME/.cache/lt2silk.XXXXXX")
  $KC pcb export pdf -o "$T/top.pdf" --mode-single --black-and-white \
      --layers "F.Silkscreen,F.Mask,Edge.Cuts" "$PCB" >/dev/null
  $KC pcb export pdf -o "$T/bot.pdf" --mode-single --black-and-white --mirror \
      --layers "B.Silkscreen,B.Mask,Edge.Cuts" "$PCB" >/dev/null
  for s in top bot; do pdftoppm -r 200 -png -cropbox -singlefile "$T/$s.pdf" "$T/$s"; done
  python3 - "$T" "$IMG" <<'PYEOF'
import sys
from PIL import Image, ImageOps
t, out = sys.argv[1], sys.argv[2]
for s, name in (("top", "silk_top.png"), ("bot", "silk_bottom.png")):
    im = Image.open("%s/%s.png" % (t, s)).convert("L")
    bb = ImageOps.invert(im).getbbox()
    im.crop((bb[0] - 20, bb[1] - 20, bb[2] + 20, bb[3] + 20)).save("%s/%s" % (out, name))
PYEOF
  echo "== schematic picture, routing picture (tracks only: the GND pours are left out so the tracks show)"
  pdftoppm -r 110 -png -singlefile "$DOCS/${NAME}_schematic.pdf" "$IMG/schematic"
  "$ROOT/scripts/kpy" -c "
import pcbnew
b = pcbnew.LoadBoard('$PCB')
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)
pcbnew.SaveBoard('$K/reports/nozone.kicad_pcb', b)
import os; os._exit(0)
" >/dev/null 2>&1
  $KC pcb export pdf -o "$T/route.pdf" --mode-single --layers "F.Cu,B.Cu,Edge.Cuts,F.Fab" \
      "$K/reports/nozone.kicad_pcb" >/dev/null
  rm -f "$K/reports/nozone.kicad_pcb" "$K/reports/nozone.kicad_prl" "$K/reports/nozone.kicad_pro"
  pdftoppm -r 420 -png -cropbox -singlefile "$T/route.pdf" "$T/route"
  python3 - "$T" "$IMG" <<'PYEOF'
import sys
from PIL import Image, ImageOps
t, out = sys.argv[1], sys.argv[2]
im = Image.open("%s/route.png" % t).convert("RGB")
bb = ImageOps.invert(im.convert("L")).getbbox()
im = im.crop((bb[0] - 20, bb[1] - 20, bb[2] + 20, bb[3] + 20))
im.crop((0, 0, im.width, int(im.height * 0.70))).save("%s/routing.png" % out)   # the rear 30 mm has no tracks
PYEOF
  rm -rf "$T"
fi

echo "== 3D STEP (board with parts, for CAD)"
$KC pcb export step --no-dnp --force -o "$K/${NAME}_pcb.step" "$PCB" 2>&1 | tail -1

echo "== 3D renders"
for side in top bottom; do
  $KC pcb render -o "$IMG/pcb_$side.png" --side $side --width 1600 --height 1200 \
      --quality high --background opaque "$PCB" 2>&1 | tail -1 || true
done
$KC pcb render -o "$IMG/pcb_iso.png" --rotate "-45,0,30" --zoom 0.9 --width 1600 --height 1200 \
    --quality high --background opaque --perspective "$PCB" 2>&1 | tail -1 || true
echo done
