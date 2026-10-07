// Pieces of the assembled robot, one colour each, in assembly position (PCB coordinates, z = 0 on the PCB top).
// Used by scripts/export_assembly.sh to build the whole-robot STL / GLB (the board itself comes from KiCad).
//   openscad -D 'piece="frames"' -D 'LITE=true' -o frames.stl assembly_export.scad
// piece = frames | deck | box | motor_can | motor_cap | motor_terminal | pinion | gear | axle | wheel | tyre
//       | support | support_ball | screws | nuts | none
include <linetracer2_mech.scad>

part = "none";                       // (the included file draws nothing)
piece = "none";
LITE = true;
LITE_SUPPORT = "caster_print";       // Lite: "skid" | "caster_print" | "caster_bead"

module both_sides() { children(); translate([100, 0, 0]) mirror([1, 0, 0]) children(); }

if (piece == "frames") { frame_left(); frame_right(); }
else if (piece == "deck") { if (DECK_VARIANT == "clip") deck_clip(); else deck(); }
else if (piece == "box") battery_box();
else if (piece == "motor_can") both_sides() {
    along_x(CAN_X0, CAN_X1 - CAN_X0) can_profile();
    translate([FRONT_X0, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = BOSS_D, h = BOSS_L);
    translate([SHAFT_TIP_X, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 2, h = FRONT_X0 - SHAFT_TIP_X);
}
else if (piece == "motor_cap") both_sides()
    translate([CAN_X1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 10, h = REAR_BOSS_X1 - CAN_X1);
else if (piece == "motor_terminal") both_sides()
    for (s = [-1, 1]) translate([CAN_X1, MOTOR_Y + s * 9.2 - 0.6, AXIS_Z - 1.5]) cube([3.5, 1.2, 3]);
else if (piece == "pinion") both_sides()
    translate([SHAFT_TIP_X, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = MOD * (PINION_T + 2), h = 4);
else if (piece == "gear") both_sides() translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40();
else if (piece == "axle") both_sides()
    translate([AXLE_END_X - AXLE_L, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 2, h = AXLE_L);
else if (piece == "wheel") both_sides() translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel();
else if (piece == "tyre") both_sides() {
    if (LITE) translate([WHEEL_X1 - WHEEL_W / 2 + 1.7, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) tire_tpu();
    else translate([WHEEL_X1 - (WHEEL_W - 3.5) / 2, AXLE_Y, AXIS_Z]) rotate([0, -90, 0])
        rotate_extrude() translate([(23.7 + 3.5) / 2, 0]) circle(d = 3.5);
}
else if (piece == "support") translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) {
    if (!LITE) skid_clip();
    else if (LITE_SUPPORT == "caster_print") caster_lite_housing();
    else if (LITE_SUPPORT == "caster_bead") caster_lite_bead();
    else skid_clip();
}
else if (piece == "support_ball") translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) {
    if (LITE && LITE_SUPPORT == "caster_print") caster_lite_ball(loaded = true);
    else if (LITE && LITE_SUPPORT == "caster_bead") lite_bead(loaded = true);
}
else if (piece == "screws") {
    for (h = all_holes()) translate([h[0], h[1], -PCB_T]) screw_pan(20);        // M3x20 from the PCB bottom
    for (h = BOX_HOLES) translate([h[0], h[1], DECK_TOP + 1.5]) mirror([0, 0, 1]) screw_flat(8);   // box -> deck
}
else if (piece == "nuts") for (h = all_holes()) translate([h[0], h[1], TOWER_NUT_Z0]) nut();
