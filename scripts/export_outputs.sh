#!/bin/sh
# Export everything needed for fabrication and documentation from the KiCad project.
#   ./export_outputs.sh                      standard board (rev.A1)
#   LT2_VARIANT=lite ./export_outputs.sh     Lite board (rev.L1)
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
  NAME=Linetracer2-Lite; REV=rev.L1
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
