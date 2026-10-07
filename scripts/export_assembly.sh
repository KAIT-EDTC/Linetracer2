#!/bin/sh
# Whole Lite robot as one 3D model: the KiCad board with all its parts + frames, motors, gears, wheels, tyres, deck,
# battery box, caster, screws (OpenSCAD).  Run from scripts/:   ./export_assembly.sh
#
#   lite/hardware/Linetracer2-Lite_assembly.stl   one mesh (GitHub shows it in a 3D viewer; slicers / CAD import it)
#   lite/hardware/Linetracer2-Lite_assembly.glb   the same with colours (Windows 3D Viewer, Blender, online glTF viewers)
#   lite/docs/assembly_*.png                     pictures (OpenSCAD renders of the same pieces)
#   lite/docs/steps/step_NN.png                  one picture per soldering step (for lite/docs/assembly.md)
#
# Coordinates: KiCad's 3D frame (x right, y to the FRONT, z up, PCB top at z = 0, origin = the board's (0, 0)).
set -e
cd "$(dirname "$0")"
ROOT=$(cd .. && pwd)
SCAD="$HOME/.local/opt/openscad-2021/AppRun"
MECH="$ROOT/hardware/mechanical"
T="$ROOT/.tmp/asm"                      # inside the repo: the KiCad flatpak can not write to /tmp
OUT="$ROOT/lite/hardware/Linetracer2-Lite_assembly"
IMG="$ROOT/lite/docs"
SUPPORT=${LITE_SUPPORT:-caster_print}
mkdir -p "$T"

echo "== board (KiCad VRML, all parts)"
./kc pcb export vrml --units mm --user-origin 100x50mm -f -o "$T/board.wrl" \
    "$ROOT/lite/hardware/kicad/Linetracer2-Lite.kicad_pcb" | tail -1

echo "== one picture per soldering step (lite/docs/steps/)"
python3 "$ROOT/lite/scripts/step_images.py" "$T/board.wrl" | tail -1

echo "== mechanical pieces (OpenSCAD, LITE_SUPPORT=$SUPPORT)"
# piece:colour (sRGB hex)
PIECES="frames:#f08c28 deck:#3fa9f5 box:#4d4d4d motor_can:#c8c8cc motor_cap:#f2f2f2 motor_terminal:#d9a620
pinion:#d9a620 gear:#f5f5f5 axle:#b8860b wheel:#ffd23f tyre:#1a1a1a support:#f5f5f5 support_ball:#ff7f00
screws:#b0b0b8 nuts:#b0b0b8"
ARGS=""
for pc in $PIECES; do
  p=${pc%%:*}
  "$SCAD" -D "piece=\"$p\"" -D 'LITE=true' -D "LITE_SUPPORT=\"$SUPPORT\"" -o "$T/$p.stl" "$MECH/assembly_export.scad" \
      >"$T/$p.log" 2>&1 || { echo "openscad failed for $p"; tail -5 "$T/$p.log"; exit 1; }
  if [ -s "$T/$p.stl" ] && grep -q facet "$T/$p.stl"; then ARGS="$ARGS $T/$p.stl:${pc#*:}"; fi
  printf '  %-16s %s\n' "$p" "$(grep -c facet "$T/$p.stl" 2>/dev/null || echo 0) facets"
done

echo "== merge"
mkdir -p "$T/split"
ASM_SPLIT_DIR="$T/split" python3 asm3d.py "$T/board.wrl" "$OUT" $ARGS
ls -la "$OUT.stl" "$OUT.glb"

echo "== interference: every part on the board (KiCad bounding boxes + 0.3 mm) vs. the mechanical parts"
python3 board_boxes.py "$T/board.wrl" "$T/board_boxes.scad"
for c in frames deck box motors drive support screws positive_control; do
  if OPENSCADPATH="$T" "$SCAD" -D "chk=\"$c\"" -D "LITE_SUPPORT=\"$SUPPORT\"" -o "$T/chk_$c.stl" \
      "$MECH/check_board_lite.scad" 2>&1 | grep -q "Current top level object is empty"; then r=empty; else r="NOT EMPTY"; fi
  printf '  %-18s %s\n' "$c" "$r"
done
echo "  (all must be empty, only positive_control must find the overlap)"

echo "== pictures"
# camera: translate x,y,z, rotate x,y,z, distance  (model: x right, y front, z up)
for v in "iso:50,-50,12,58,0,215,290" "rear:50,-50,12,60,0,330,300" "side:50,-50,5,90,0,90,300" \
         "top:50,-50,0,0,0,0,330" "bottom:50,-50,0,180,0,180,330"; do
  name=${v%%:*}
  "$SCAD" -o "$IMG/assembly_$name.png" --imgsize=1600,1200 --camera="${v#*:}" --colorscheme=Tomorrow \
      --projection=p "$T/split/scene.scad" >"$T/png_$name.log" 2>&1 || tail -3 "$T/png_$name.log"
done
ls -la "$IMG"/assembly_*.png
