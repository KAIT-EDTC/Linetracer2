// Interference check: every part on the Lite board vs. the mechanical parts (must be EMPTY, except the positive
// control).  The parts on the board are their bounding boxes from KiCad (board_boxes.scad, written by
// scripts/board_boxes.py), grown by G.  Run by scripts/export_assembly.sh:
//   OPENSCADPATH=<dir of board_boxes.scad> openscad -D 'chk="frames"' -o x.stl check_board_lite.scad
include <linetracer2_mech.scad>
include <board_boxes.scad>

part = "none";
LITE = true;
LITE_SUPPORT = "caster_print";
chk = "frames";      // frames | deck | box | motors | drive | support | screws | positive_control
G = 0.3;             // at least this much air between a part on the board and a mechanical part

module both_drive_sides() { drive_side(); translate([100, 0, 0]) mirror([1, 0, 0]) drive_side(); }
module screws_and_nuts() {
    for (h = all_holes()) translate([h[0], h[1], -PCB_T]) screw_pan(20);
    for (h = all_holes()) translate([h[0], h[1], TOWER_NUT_Z0]) nut();
}

if (chk == "frames") intersection() { board_parts(G); frames(); }
else if (chk == "deck") intersection() { board_parts(G); deck(); }
else if (chk == "box") intersection() { board_parts(G); battery_box(); }
else if (chk == "motors") intersection() { board_parts(G); motors(); }
else if (chk == "drive") intersection() { board_parts(G); both_drive_sides(); }
else if (chk == "support") intersection() { board_parts(G); front_support(); }
else if (chk == "screws") intersection() { board_parts(G); screws_and_nuts(); }
else if (chk == "positive_control") intersection() { board_parts(G); translate([0, -3, 0]) frames(); }  // 3 mm forward
