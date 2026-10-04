#!/bin/sh
# Export everything needed for fabrication and documentation from the KiCad project.
#   hardware/gerber/            Gerber + drill  (zip: hardware/Linetracer2_rev.A1_gerber.zip)
#   hardware/kicad/bom/         BOM csv
#   hardware/kicad/reports/     ERC / DRC reports
#   docs/                       schematic PDF, assembly PDFs, 3D renders
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
KC="$ROOT/scripts/kc"
K="$ROOT/hardware/kicad"
PCB="$K/Linetracer2.kicad_pcb"
SCH="$K/Linetracer2.kicad_sch"
G="$ROOT/hardware/gerber"
mkdir -p "$G" "$K/bom" "$K/reports" "$ROOT/docs/images"
rm -f "$G"/*

echo "== ERC / DRC"
$KC sch erc --severity-all -o "$K/reports/erc.rpt" "$SCH" | tail -1
$KC pcb drc --severity-all --refill-zones --schematic-parity -o "$K/reports/drc.rpt" "$PCB" | tail -1

echo "== Gerber / drill"
$KC pcb export gerbers -o "$G" \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" "$PCB" | tail -1
$KC pcb export drill -o "$G/" --format excellon --excellon-units mm \
    --excellon-zeros-format decimal --drill-origin absolute --excellon-separate-th --generate-map --map-format pdf "$PCB" | tail -1
(cd "$G" && rm -f ../Linetracer2_rev.A1_gerber.zip && zip -q ../Linetracer2_rev.A1_gerber.zip *.g* *.drl)
ls -la "$ROOT/hardware/Linetracer2_rev.A1_gerber.zip"

echo "== BOM"
$KC sch export bom -o "$K/bom/Linetracer2_bom.csv" \
    --fields 'Reference,Value,Footprint,Akizuki,Note,${QUANTITY}' \
    --labels 'Refs,Value,Footprint,Akizuki,Note,Qty' --group-by 'Value,Footprint' "$SCH" | tail -1

echo "== PDFs"
$KC sch export pdf -o "$ROOT/docs/Linetracer2_schematic.pdf" "$SCH" | tail -1
# assembly drawings: silkscreen + fab outlines + pad sketches, black on white
$KC pcb export pdf -o "$ROOT/docs/Linetracer2_assembly_top.pdf" --mode-single --black-and-white \
    --sketch-pads-on-fab-layers --layers "F.Fab,Edge.Cuts" --include-border-title "$PCB" | tail -1
$KC pcb export pdf -o "$ROOT/docs/Linetracer2_assembly_bottom.pdf" --mode-single --black-and-white --mirror \
    --sketch-pads-on-fab-layers --layers "B.Fab,Edge.Cuts" --include-border-title "$PCB" | tail -1

echo "== 3D renders"
for side in top bottom; do
  $KC pcb render -o "$ROOT/docs/images/pcb_$side.png" --side $side --width 1600 --height 1200 \
      --quality high --background opaque "$PCB" 2>&1 | tail -1 || true
done
$KC pcb render -o "$ROOT/docs/images/pcb_iso.png" --rotate "-45,0,30" --zoom 0.9 --width 1600 --height 1200 \
    --quality high --background opaque --perspective "$PCB" 2>&1 | tail -1 || true
echo done
