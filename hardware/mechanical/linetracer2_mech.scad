// Linetracer2 - 3D printable mechanical parts (OpenSCAD 2021.01), rev.A1
//
//   part = "frame_left" | "frame_right" | "deck" | "gear40" | "wheel" | "tire_tpu" | "skid" | "skid_clip"
//        | "deck_clip" | "caster_print" | "caster_bead" | "caster_lite_print" | "caster_lite_print45" | "caster_lite_bead" (-D LITE=true)
//        | "assembly" | "check_*" (interference checks, must be empty)
//   assembly: SKID_VARIANT (standard) / LITE_SUPPORT = "caster_print" | "caster_print45" | "caster_bead" | "skid" (Lite)
//   choose the front support.  Gearbox: pinion first, then the motor slides into place (MOTOR_SLIDE, check_motor_*).
// Child safety (2026-10-07): outer vertical edges of frames and deck rounded, wheel rim/hub chamfered, skid sled
// rounded; no interface (holes, axle, gears, snaps, towers, deck heights) changed.  See README "子ども向けの安全".
//   openscad -D 'part="frame_left"' -o frame_left.stl linetracer2_mech.scad
//
// Coordinates = PCB coordinates (mm): x -> right, y -> rear, z = 0 on the PCB TOP surface.
// !! MIRROR WORLD: x right + y to the REAR + z up is LEFT-handed, so everything drawn here (assembly view,
// !! assembly.stl) is the MIRROR IMAGE of the real robot, and an STL exported as drawn prints as the mirror image of
// !! the real part.  That is harmless for parts that are symmetric (deck, gears, wheels) or whose surroundings are
// !! symmetric about x = 50 (skids, casters), but the frames are a left/right pair: the frame drawn on the RIGHT here
// !! (frame_right(), x 51..92) is the real LEFT frame.  So part "frame_left" exports frame_right() (engraved "L") and
// !! part "frame_right" exports frame_left() (engraved "R"); deck_clip (claws not symmetric) is exported mirrored.
// (0,0) is the front-left corner of the board.  Floor is at z = -5.6 (PCB bottom 4.0 mm).
//
// Drive: FA-130RA + Tamiya 8T pinion (m0.5) -> printed 40T spur (m0.5) on a 2 mm axle, 5:1, wheel ~32 mm.
// Everything is held by screws (no tape):
//   4 x M3x20 pan  : from the PCB bottom, through the PCB and the frame towers, into nuts in the deck
//   2 x M3x8  flat : battery box floor -> deck (nuts in the deck)
//   1 x M3x8  flat : skid (from the floor side) -> NYLON nut on the PCB top (next to sensor solder joints)
//
// LITE = true : Lite board (rev.L3: 65 x 100 mm board, 3 x LBR-127HLD, front support in the hole (50,11): ball caster
//   caster_lite_print by default, or the 7.5 mm skid; printed TPU tyres instead of O-rings).
//   openscad -D 'LITE=true' -D 'part="check_skid_sensor"' ...   Frames, deck, gears and wheels are the same for
//   both boards; the Lite needs a TALLER skid (7.5 mm) because the LBR-127HLD is 5.6 mm tall: the front of the
//   robot is lifted and the board leans back about 3 deg (the wheels set the height at the rear).
//   openscad -D 'LITE=true' -o x.echo ...  prints the tilt, the sensor-to-floor gap and the clearances.

part = "assembly";
LITE = false;
$fn = 64;

// ---------------------------------------------------------------- parameters
PCB_T      = 1.6;
FLOOR_Z    = -5.6;          // floor relative to PCB top
AXLE_Y     = 88;            // must match gen_pcb.py
MOTOR_Y    = 76;            // motor shaft line (AXLE_Y - 12)
AXIS_Z     = 10.4;          // wheel radius 16 - 5.6
NOTCH_X    = 17.5;          // PCB edge in the rear notch (left side)
HOLES      = [[30, 62], [30, 96]];   // M3 holes (left frame); right frame = mirrored (70, ..)

// FA-130 (left motor): shaft points to -x
CAN_W = 20.1; CAN_H = 15.0; CAN_R = CAN_W / 2;
CAN_X0 = 20.5; CAN_X1 = 45.3;          // can front face .. rear face
BOSS_D = 6.0; BOSS_L = 1.7;            // front bearing boss
REAR_BOSS_X1 = 49.0;
SHAFT_TIP_X = 11.0;
MOTOR_TOP = AXIS_Z + CAN_H / 2;        // 17.9

// gears m0.5
PINION_T = 8;  SPUR_T = 40;  MOD = 0.5;
GEAR_X0 = 11.5; GEAR_X1 = 15.5;        // spur gear face (outer face on the print bed)
GEAR_HUB_L = 0.8;                      // hub on the inner side (11.5 .. 16.3)
GEAR_BACKLASH = 0.10;                  // tooth thinning for printing (mm on the pitch circle)
CLR = 0.25;                            // printing clearance

// frame
BASE_T   = AXIS_Z - CAN_H / 2;         // 2.9 mm : motor rests on the base
WALL     = 1.8;
FRONT_X0 = CAN_X0 - BOSS_L;            // 18.8 : the boss pocket starts here
PLATE_X0 = 16.8;                       // motor plate is 3.7 mm thick (pinion ends at 15.5)
OUTER_X0 = 8.5; OUTER_X1 = 10.5;       // outer axle wall (hangs in the notch)
OUTER_Y0 = 70.0;                       // its front end (was 73.0: room around the relief hole for the shaft tip)
WALL_RELIEF = true;                    // hole in the outer wall for a long motor shaft (false = positive control)
SHAFT_LONG = 0.9;                      // worst case: shaft 0.5 mm longer than nominal + 0.4 mm end play
HANG_Z   = 0.0;                        // lowest point (flat bottom -> prints without supports)
AXLE_D   = 2.0;
AXLE_L   = 20.0;                       // brass rod, 2 mm
// D-cut (2026-10-09): a press fit of PLA on a smooth 2 mm rod holds only about the motor's stall torque through the
// gear (5 x 4.7 = 24 mN m) and gets weaker as PLA creeps or when a hole prints a little big.  The teacher files a flat
// on the axle (AXLE_FLAT deep, AXLE_FLAT_L long from the outer end; the inner 3 mm stay round in the blind bearing),
// the 40T gear and the wheel have D holes -> they can not slip.  AXLE_FLAT = 0 gives the old round holes.
AXLE_FLAT = 0.3;                       // depth of the flat (1.7 mm across the flat)
AXLE_FLAT_L = 17.0;                    // length of the flat from the outer (wheel) end: wheel hub .. past the gear
AXLE_FLAT_CLR = 0.08;                  // D hole: its flat sits this much further out than the axle's
module axle_hole(d, h) {               // round press-fit hole, with the D flat when AXLE_FLAT > 0
    intersection() {
        cylinder(d = d, h = h);
        if (AXLE_FLAT > 0) translate([-5, -5, -1]) cube([5 + AXLE_D / 2 - AXLE_FLAT + AXLE_FLAT_CLR, 10, h + 2]);
    }
}
module axle_rod() difference() {       // the axle along +z from its outer end (assembly views)
    cylinder(d = AXLE_D, h = AXLE_L);
    if (AXLE_FLAT > 0) translate([AXLE_D / 2 - AXLE_FLAT, -2, -1]) cube([2, 4, AXLE_FLAT_L + 1]);
}
AXLE_END_X = 19.3;                     // blind end of the axle hole (axle pushed in until it stops)
WHEEL_X1 = 7.2;                        // inner face of the wheel (0.3 mm from the spacer boss)
TOWER_D  = 9.6;
TOWER_TOP = 15.0;                      // = deck bottom
TOWER_FRONT_CLIP = 65.6;               // front tower must not reach into the motor can
// Motor insertion (2026-10-07 fix): the pinion is pressed on the shaft FIRST.  The shaft hole in the motor plate is
// PLATE_HOLE_D (was 3.0: the 5 mm pinion could not pass, and with the motor in place the outer wall left only 0.5 mm
// in front of the shaft tip, so the pinion could not be put on either).  The motor is laid into the cradle shifted
// MOTOR_SLIDE mm inward (pinion clear of the plate), then slid outward until the can face stops on the plate; the
// pinion passes the hole and slides axially into mesh with the 40T gear, the front boss enters its pocket.
PLATE_HOLE_D = 5.6;
MOTOR_SLIDE = 10.5;

// deck (battery box carrier, printed upside down)
DECK_TOP  = 20.5;                      // battery box floor
DECK_UNDER = 18.0;                     // underside over the motors (motor top 17.9)
DECK_X0 = 24.5; DECK_X1 = 75.5;
DECK_FRONT = [57.0, 65.5];             // front bar (y)
DECK_REAR  = [87.0, 100.5];            // rear bar (y)
NUT_AF = 5.5; NUT_H = 2.4;
NUT_POCKET_AF = NUT_AF + 0.25;
TOWER_NUT_Z0 = 15.8;                   // nut for the M3x20 sits on this floor (screw tip ends at 18.4)

// battery box BH-331-3ASTH-150MM: 58 x 48.3 x 17, two 3.5 mm holes (90 deg countersink) 30 mm apart
BOX_L = 58.0; BOX_W = 48.3; BOX_H = 17.0;
BOX_C = [50, 76];
BOX_HOLES = [[50, 61], [50, 91]];

// skid at H5 (50,4): between the bodies of PS3 (x <= 45.35) and PS4 (x >= 54.65)
// Lite: H5 = (50,11), 7 mm behind the centre sensor (its body ends at y = 5.7, the skid starts at y = 6.7)
SKID_XY = LITE ? [50, 11] : [50, 4];
SENSOR_XS = LITE ? [38, 50, 62] : [20, 32, 44, 56, 68, 80];
// sensor body on the PCB bottom: LBR-123F 2.7 x 3.4 x 1.5 (standard), LBR-127HLD 8.7 x 4.5 x 5.6 (Lite)
SENSOR_BODY = LITE ? [8.7, 4.5, 5.6] : [2.7, 3.4, 1.5];
SENSOR_Y = 4;
// = PCB bottom .. floor under the skid (standard: print 3.5 / 4.0 / 4.5; Lite: 7.0 / 7.5 / 8.0 to tune the sensor height)
SKID_H = LITE ? 7.5 : 4.0;
TYRE_R = LITE ? 15.6 : 15.7;           // TPU tyre 31.2 mm / O-ring P-24 about 31.4 mm
SKID_D = 8.6;

// snap-in skid (default since 2026-10-05: no screw, no nylon nut)
CLIP_X0 = -1.2;                        // print face; the pin is flattened 0.3 mm here. body x = -1.2 .. 3.8
CLIP_PIN_D = 3.0; CLIP_BARB_D = 3.75;  // PCB hole is 3.2 mm (drilled)
CLIP_SLIT = 0.8; CLIP_POCKET_D = 4.2; CLIP_ROOT = 2.2;

// claw deck (option): holds the battery box with 4 claws instead of 2 screws
BOX_SHOULDER_H = 15.0;                 // height of the box's long wall at the claws (datasheet 15.0 +-0.5) - MEASURE YOUR BOX
BOX_UCUT = [20.8, 36.6]; BOX_UCUT_H = 7.0;   // finger cut in the long walls (from the left end of the box)
CLAW_X = [31, 65];                     // on the box "shoulders" (not on the U-cut, not over J1)
CLAW_T = 1.4; CLAW_W = 6; CLAW_GAP = 0.15; CLAW_LIP = 0.7; CLAW_ROOT_Z = 16.5;
PEG_D = 3.2; PEG_H = 1.2;              // pegs drop into the box's floor holes (3.5 mm) and locate it

// ---------------------------------------------------------------- helpers
module can_profile(r = CAN_R, h = CAN_H) {     // FA-130 cross-section in the y-z plane
    intersection() { circle(r = r); square([2 * r + 2, h], center = true); }
}

module along_x(x0, len) {                      // extrude a y-z profile along +x, centred on the motor axis
    translate([x0, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) rotate([0, 0, 90]) linear_extrude(len) children();
}

module motor_left() {
    color("silver") along_x(CAN_X0, CAN_X1 - CAN_X0) can_profile();
    color("white") translate([CAN_X1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0])
        cylinder(d = 10, h = REAR_BOSS_X1 - CAN_X1);
    // terminals on the rounded sides of the end cap
    color("gold") for (s = [-1, 1]) translate([CAN_X1, MOTOR_Y + s * 9.2 - 0.6, AXIS_Z - 1.5]) cube([3.5, 1.2, 3]);
    color("silver") translate([FRONT_X0, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = BOSS_D, h = BOSS_L);
    color("gray") translate([SHAFT_TIP_X, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 2, h = FRONT_X0 - SHAFT_TIP_X);
}

module gear_disc(teeth, x0, x1, y, col) {
    color(col) translate([x0, y, AXIS_Z]) rotate([0, 90, 0])
        cylinder(d = MOD * (teeth + 2), h = x1 - x0);
}

// box with rounded VERTICAL edges (child safety: no pointed corners; prints without supports because the
// rounding is in the x-y plane).  Same size as cube(s) at p.
module rbox(p, s, r) {
    translate(p) hull() for (i = [r, s[0] - r], j = [r, s[1] - r]) translate([i, j, 0]) cylinder(r = r, h = s[2], $fn = 24);
}

module m3_hole(h = 40) { translate([0, 0, -h / 2]) cylinder(d = 3.3, h = h); }
module nut_pocket(depth) { cylinder(d = NUT_POCKET_AF / cos(30), h = depth, $fn = 6); }

// ---------------------------------------------------------------- involute spur gear (2D)
function inv_deg(a) = (tan(a) - a * PI / 180) * 180 / PI;     // involute function, degrees in / out
function pol(R, a) = [R * cos(a), R * sin(a)];

module gear2d(m, z, pa = 20, b = 0.1, steps = 8) {
    r  = m * z / 2;
    rb = r * cos(pa);
    ra = r + m;
    rf = r - 1.25 * m;
    hp = ((PI * m / 2 - b) / (2 * r)) * 180 / PI;              // half tooth angle on the pitch circle
    function hal(R) = hp + inv_deg(pa) - inv_deg(acos(rb / max(R, rb)));
    pts = [ for (i = [0 : z - 1])
              let (c = i * 360 / z)
              each concat(
                  [ for (k = [0 : steps]) let (R = rb + (ra - rb) * k / steps) pol(R, c - hal(R)) ],
                  [ for (k = [steps : -1 : 0]) let (R = rb + (ra - rb) * k / steps) pol(R, c + hal(R)) ],
                  [ pol(rf, c + hal(rb)), pol(rf, c + 360 / z - hal(rb)) ]) ];
    polygon(pts);
}

// ---------------------------------------------------------------- frame (left)
module tower(h) {
    translate([h[0], h[1], 0]) intersection() {
        cylinder(d = TOWER_D, h = TOWER_TOP);
        translate([-TOWER_D, -TOWER_D, -1])
            cube([2 * TOWER_D, (h[1] < MOTOR_Y ? TOWER_FRONT_CLIP - h[1] : 100.5 - h[1]) + TOWER_D, TOWER_TOP + 2]);
    }
}

// "L" / "R" engraved 0.4 mm into the top of the base plate (rear corner, free of the motor and the towers), so
// children can match the frames with "MOTOR L" / "MOTOR R" on the board.  Engraving on a top face: no supports.
// The letter is the side the PRINTED part goes on (see MIRROR WORLD above): frame_left() here prints as the real
// right frame -> "R"; frame_right() prints as the real left frame -> "L".  The text itself is never mirrored.
FRAME_LABEL_XY = [40.5, 94.5];
module frame_label(t, x) translate([x, FRAME_LABEL_XY[1], BASE_T - 0.4]) linear_extrude(1)
    text(t, size = 6, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");

module frame_left(lbl = true) {
    difference() {
        union() {
            // base plate on the PCB
            rbox([NOTCH_X + 0.5, 58.0, 0], [CAN_X1 + 0.7 - (NOTCH_X + 0.5), 100.5 - 58.0, BASE_T], 1.5);
            // cradle walls that hug the can (snap fit, 2.2 mm above the axis)
            translate([CAN_X0 + 0.5, 0, 0]) difference() {
                rbox([0, MOTOR_Y - CAN_R - WALL, 0], [CAN_X1 - CAN_X0 - 1.0, CAN_W + 2 * WALL, AXIS_Z + 2.2], 0.9);
                translate([-1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) rotate([0, 0, 90])
                    linear_extrude(CAN_X1 - CAN_X0 + 2) offset(delta = 0.1) can_profile();
                // open top so the motor can be pressed in
                translate([-1, MOTOR_Y - CAN_R + 0.45, AXIS_Z + 2.2 - 0.01]) cube([CAN_X1, CAN_W - 0.9, 20]);
            }
            // motor face plate (boss goes into it) + inner axle bearing
            rbox([PLATE_X0, 64.0, 0], [CAN_X0 - PLATE_X0, 100.5 - 64.0, AXIS_Z + 9], 1.0);
            translate([NOTCH_X - 0.5, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = FRONT_X0 - NOTCH_X + 0.5);
            // outer axle wall (in the wheel notch) with spacer bosses on both faces
            rbox([OUTER_X0, OUTER_Y0, HANG_Z], [OUTER_X1 - OUTER_X0, 100.5 - OUTER_Y0, AXIS_Z + 4 - HANG_Z], 0.9);
            translate([WHEEL_X1 + 0.3, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = OUTER_X0 - WHEEL_X1 - 0.3 + 0.01);
            translate([OUTER_X1 - 0.01, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = GEAR_X0 - 0.2 - OUTER_X1 + 0.01);
            // lower front bar under the pinion, rear bar behind the spur gear
            rbox([OUTER_X0, 72.5, HANG_Z], [FRONT_X0 - OUTER_X0, 4.5, 6.0 - HANG_Z], 1.0);
            rbox([OUTER_X0, 99.0, HANG_Z], [FRONT_X0 + BOSS_L - OUTER_X0, 1.5, AXIS_Z + 9 - HANG_Z], 0.7);
            // towers: the M3x20 screws go through them; the deck sits on top
            for (h = HOLES) tower(h);
        }
        // the PCB itself (frame parts in the notch hang below z = 0)
        translate([NOTCH_X, 0, -PCB_T]) cube([100, 120, PCB_T]);
        // motor can, boss, shaft, terminals
        along_x(CAN_X0 - 0.01, CAN_X1 - CAN_X0 + 10) offset(delta = 0.1) can_profile();
        // no snap interference next to the front tower (the tower makes the wall stiff there)
        along_x(HOLES[0][0] - TOWER_D / 2 - 0.5, TOWER_D + 1) offset(delta = 0.3) can_profile();
        translate([FRONT_X0 - 1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = BOSS_D + 0.3, h = BOSS_L + 2);
        translate([0, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 3.0, h = 30);
        translate([PLATE_X0 - 1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = PLATE_HOLE_D, h = FRONT_X0 - PLATE_X0 + 1);   // pinion passes
        // axle hole (2.0 mm axle -> 2.15 mm hole), blind at AXLE_END_X
        translate([-1, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = AXLE_D + 0.15, h = AXLE_END_X + 1);
        // room for pinion and spur gear between the walls
        translate([OUTER_X1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0])
            cylinder(d = MOD * (PINION_T + 2) + 2 * CLR + 1, h = PLATE_X0 - 0.5 - OUTER_X1);
        // ... and through the outer wall: FA-130 shaft = 9.5 +-0.5 mm from the can face + 0.05..0.4 mm end play, so
        // the tip (and the pinion pressed flush with it) can reach 0.9 mm past the nominal 11.0 - the wall face is at
        // 10.5.  The wheel covers this hole from the outside.
        if (WALL_RELIEF) translate([OUTER_X0 - 1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0])
            cylinder(d = MOD * (PINION_T + 2) + 2 * CLR + 1, h = OUTER_X1 - OUTER_X0 + 2);
        translate([GEAR_X0 - 0.2, AXLE_Y, AXIS_Z]) rotate([0, 90, 0])
            cylinder(d = MOD * (SPUR_T + 2) + 2 * CLR + 1, h = PLATE_X0 - (GEAR_X0 - 0.2));
        // motor pads M1 (+ relief holes) and C5 must stay free
        translate([37.5, 57.0, -1]) cube([12, 10.5, 10]);
        // M3 screw holes (screw from the PCB bottom; the nut is in the deck)
        for (h = HOLES) translate([h[0], h[1], 0]) m3_hole();
        if (lbl) frame_label("R", FRAME_LABEL_XY[0]);       // printed, this part is the real RIGHT frame
    }
}

module frame_right() difference() {
    translate([100, 0, 0]) mirror([1, 0, 0]) frame_left(lbl = false);
    frame_label("L", 100 - FRAME_LABEL_XY[0]);                // printed, this part is the real LEFT frame
}

// ---------------------------------------------------------------- deck (battery box carrier)
// Sits on the 4 towers.  Bars (front/rear) carry the nuts; the thin plate clears the motors by 0.1 mm
// and keeps them in their cradles.  Print UPSIDE DOWN (the battery side on the bed).
function all_holes() = [for (h = HOLES) h, for (h = HOLES) [100 - h[0], h[1]]];

// motor stop: a rib under the deck that drops into the 2 mm gap between the two motors' rear bosses (x 49 / 51).
// The motors are slid OUTWARD into mesh (pinion first, see check_motor_slide) and only the snap's friction held
// them there; with the deck on, neither motor can creep back toward the centre (0.5 mm air each side).
MOTOR_STOP_W = 1.0;                    // rib thickness (x): 0.5 mm air to each rear boss (FA-130 overall 38.0 +-0.1)
MOTOR_STOP_Z = 8.5;                    // rib bottom (the rear bosses are d10 around z 10.4)
MOTOR_STOP_CH = 0.3;                   // 45 deg lead-in on both sides of the bottom edge: a motor that sits up to
                                       // 0.8 mm too far in is pushed back into its seat as the deck goes down
module motor_stop() hull() {
    translate([50 - MOTOR_STOP_W / 2, MOTOR_Y - 4.5, MOTOR_STOP_Z + MOTOR_STOP_CH])
        cube([MOTOR_STOP_W, 9, DECK_UNDER - MOTOR_STOP_Z - MOTOR_STOP_CH + 0.01]);
    translate([50 - MOTOR_STOP_W / 2 + MOTOR_STOP_CH, MOTOR_Y - 4.5, MOTOR_STOP_Z])
        cube([MOTOR_STOP_W - 2 * MOTOR_STOP_CH, 9, 0.01]);
}

module deck_body() {
    intersection() {                   // child safety: the 4 outer corners are rounded (r 2, vertical edges)
        union() {
            translate([DECK_X0, DECK_FRONT[0], DECK_UNDER]) cube([DECK_X1 - DECK_X0, DECK_REAR[1] - DECK_FRONT[0], DECK_TOP - DECK_UNDER]);
            for (yy = [DECK_FRONT, DECK_REAR])
                translate([DECK_X0, yy[0], TOWER_TOP]) cube([DECK_X1 - DECK_X0, yy[1] - yy[0], DECK_TOP - TOWER_TOP]);
        }
        rbox([DECK_X0, DECK_FRONT[0], TOWER_TOP - 1], [DECK_X1 - DECK_X0, DECK_REAR[1] - DECK_FRONT[0], DECK_TOP - TOWER_TOP + 2], 2.0);
    }
    motor_stop();
}

module deck_common_cuts() {
    // M3x20 from below: lead-in cone, hole, nut pocket opening on the top (under the battery box)
    for (h = all_holes()) translate([h[0], h[1], 0]) {
        m3_hole();
        translate([0, 0, TOWER_TOP - 0.01]) cylinder(d1 = 5.0, d2 = 3.3, h = 0.85);
        translate([0, 0, TOWER_NUT_Z0]) nut_pocket(DECK_TOP - TOWER_NUT_Z0 + 1);
    }
    // windows over the motors (lighter, the motors can be seen)
    for (x = [37, 56]) translate([x, 70, DECK_UNDER - 1]) cube([7, 12, 5]);
    // "FRONT" arrow, engraved on the underside
    translate([40, 62.5, TOWER_TOP - 0.01]) linear_extrude(0.6) polygon([[-2.5, 0], [2.5, 0], [0, -3]]);
}

module deck() {
    difference() {
        deck_body();
        deck_common_cuts();
        // battery box screws (M3x8 flat from inside the box): hole + nut pocket from below
        for (h = BOX_HOLES) translate([h[0], h[1], 0]) {
            m3_hole();
            translate([0, 0, TOWER_TOP - 1]) nut_pocket(1 + NUT_H + 0.2);
        }
    }
}

// ---------------------------------------------------------------- claw deck (option, print RIGHT SIDE UP)
// The box is located by 2 pegs in its floor holes and held down by 4 claws on its long walls.
BOX_FRONT_Y = BOX_C[1] - BOX_W / 2;     // 51.85
BOX_REAR_Y  = BOX_C[1] + BOX_W / 2;     // 100.15
function claw_lip_z() = DECK_TOP + BOX_SHOULDER_H + 0.6;   // box may lift 0.6 mm at most (pegs are 1.2 mm)

module claw(x, face_y, dir) {          // dir = -1: in front of the box, +1: behind it
    y_in = face_y + dir * CLAW_GAP;
    y0 = dir < 0 ? y_in - CLAW_T : y_in;
    zl = claw_lip_z();
    // vertical edges rounded (child safety: the claws stand up 22 mm); thickness, lip and gap unchanged
    rbox([x - CLAW_W / 2, y0, TOWER_TOP], [CLAW_W, CLAW_T, zl + 1.4 - TOWER_TOP], 0.5);       // arm
    hull() {                                                                           // lip with lead-in slope
        rbox([x - CLAW_W / 2, y0, zl], [CLAW_W, CLAW_T, 1.4], 0.5);
        rbox([x - CLAW_W / 2, dir < 0 ? y_in : y_in - CLAW_LIP, zl], [CLAW_W, CLAW_LIP, 0.3], 0.3);
    }
}

module deck_clip() {
    difference() {
        union() {
            deck_body();
            for (x = CLAW_X) {
                // front tab: supports the box front and carries the front claw root
                translate([x - CLAW_W / 2, BOX_FRONT_Y - CLAW_GAP - CLAW_T, TOWER_TOP])
                    cube([CLAW_W, DECK_FRONT[0] - (BOX_FRONT_Y - CLAW_GAP - CLAW_T) + 0.01, DECK_TOP - TOWER_TOP]);
                // rear root
                translate([x - CLAW_W / 2, DECK_REAR[0], TOWER_TOP])
                    cube([CLAW_W, BOX_REAR_Y + CLAW_GAP + CLAW_T - DECK_REAR[0], CLAW_ROOT_Z - TOWER_TOP]);
            }
            for (h = BOX_HOLES) translate([h[0], h[1], DECK_TOP - 0.01])
                cylinder(d1 = PEG_D, d2 = PEG_D - 0.6, h = PEG_H + 0.01);
        }
        deck_common_cuts();
        // free length of the claw arms (0.3 mm slot between arm and deck above the root)
        for (x = CLAW_X) {
            translate([x - CLAW_W / 2 - 1, BOX_FRONT_Y - 3, CLAW_ROOT_Z]) cube([CLAW_W + 2, 3 + 0.15, 30]);
            translate([x - CLAW_W / 2 - 1, BOX_REAR_Y - 0.15, CLAW_ROOT_Z]) cube([CLAW_W + 2, 5, 30]);
        }
    }
    for (x = CLAW_X) { claw(x, BOX_FRONT_Y, -1); claw(x, BOX_REAR_Y, 1); }
}

// ---------------------------------------------------------------- 40T spur gear (printed)
// m0.5, 40 teeth, pressure angle 20 deg.  Outer face on the bed, hub on top.  Press fit on the 2 mm axle.
module gear40() {
    difference() {
        union() {
            linear_extrude(GEAR_X1 - GEAR_X0) gear2d(MOD, SPUR_T, 20, GEAR_BACKLASH);
            cylinder(d = 7, h = GEAR_X1 - GEAR_X0 + GEAR_HUB_L);
        }
        translate([0, 0, -1]) axle_hole(AXLE_D - 0.05, 20);
        for (a = [0 : 60 : 359]) rotate(a) translate([6.0, 0, -1]) cylinder(d = 3.4, h = 10);
    }
}

// ---------------------------------------------------------------- wheel (O-ring tyre)
// JIS P24 O-ring (ID 23.7, CS 3.5)  ->  tyre OD about 31.4 mm
WHEEL_W = 7;
module wheel() {
    GROOVE_D = 24.4; RIM_D = 29.6; GROOVE_W = 3.7;
    difference() {
        union() {
            // rim with 0.5 mm chamfers on both outer edges (child safety; the tyre groove is not touched)
            rotate_extrude() polygon([[0, 0], [RIM_D / 2 - 0.5, 0], [RIM_D / 2, 0.5], [RIM_D / 2, WHEEL_W - 0.5],
                                      [RIM_D / 2 - 0.5, WHEEL_W], [0, WHEEL_W]]);
            cylinder(d = 8, h = WHEEL_W + 2 - 0.5);               // hub (outer side), chamfered end
            translate([0, 0, WHEEL_W + 2 - 0.5]) cylinder(d1 = 8, d2 = 7, h = 0.5);
        }
        translate([0, 0, (WHEEL_W - GROOVE_W) / 2]) difference() {
            cylinder(d = RIM_D + 1, h = GROOVE_W);
            translate([0, 0, -1]) cylinder(d = GROOVE_D, h = GROOVE_W + 2);
        }
        translate([0, 0, -1]) axle_hole(AXLE_D - 0.1, WHEEL_W + 4);   // press fit on the 2 mm axle (D flat)
        for (a = [0:60:359]) rotate([0, 0, a]) translate([7.5, 0, -1]) cylinder(d = 4.5, h = WHEEL_W + 2);
    }
}

// optional tyre printed in TPU 95A instead of the O-ring (same groove)
module tire_tpu() {
    difference() {
        hull() {
            translate([0, 0, 0.4]) cylinder(d = 31.2, h = 2.6);
            cylinder(d = 30.4, h = 3.4);
        }
        translate([0, 0, -1]) cylinder(d = 24.0, h = 6);
    }
}

// ---------------------------------------------------------------- skid
// z = 0 on the PCB bottom, floor at z = SKID_H.  M3x8 flat-head screw from the floor side,
// head 0.7 mm above the floor, NYLON nut on the PCB top.  Contact = rounded ring around the head.
module skid(H = SKID_H) {
    R = SKID_D / 2;
    difference() {
        rotate_extrude($fn = 64) polygon(concat(
            [[0, 0], [R, 0], [R, H - 1.8]],
            [for (a = [0 : 10 : 90]) [R - 1.0 + 1.0 * cos(a), H - 1.8 + 1.8 * sin(a)]],
            [[0, H]]));
        translate([0, 0, -1]) cylinder(d = 3.3, h = H + 2);
        translate([0, 0, H - 0.5]) cylinder(d = 6.2, h = 1);                 // recess for the head
        translate([0, 0, H - 0.5 - 1.3]) cylinder(d1 = 3.3, d2 = 5.9, h = 1.3 + 0.001);   // 90 deg countersink
    }
}

// ---------------------------------------------------------------- skid with a snap pin (default)
// Same coordinates as skid(): z = 0 on the PCB bottom, floor at z = H, the pin goes to -z (up through the PCB).
// A sled (rounded in y = driving direction) with a split pin + barb that snaps through the 3.2 mm hole.
// Print LYING ON ITS SIDE (part "skid_clip"): the prongs then bend along the layers (strong).
module skid_clip(H = SKID_H) {
    T = PCB_T + 0.15;                  // barb starts 0.15 mm above the PCB top
    R = 8;                             // sled radius (contact right under the hole = sensor line)
    difference() {
        union() {
            skid_clip_sled(H, R);
            translate([0, 0, -T]) cylinder(d = CLIP_PIN_D, h = T + CLIP_ROOT + 0.01);
            translate([0, 0, -T - 1.3]) cylinder(d1 = 2.5, d2 = CLIP_BARB_D, h = 1.3);
        }
        difference() {                 // pocket so the pin halves can bend inside the body
            translate([0, 0, -0.01]) cylinder(d = CLIP_POCKET_D, h = CLIP_ROOT + 0.01);
            translate([0, 0, -1]) cylinder(d = CLIP_PIN_D, h = CLIP_ROOT + 2);
        }
        translate([-2.2, -CLIP_SLIT / 2, -T - 2]) cube([4.4, CLIP_SLIT, T + 2 + CLIP_ROOT]);   // slit
        translate([CLIP_X0 - 10, -10, -10]) cube([10, 20, 20]);                                 // print face
    }
}

// sled body of skid_clip(): y-z profile extruded along x (5 mm).  Child safety: profile corners rounded (r 0.6),
// edges of the print-top face (x = CLIP_X0 + 5) chamfered 0.5 mm.  The contact point (y = 0, z = H) is unchanged.
module skid_clip_sled(H, R = 8) {
    module prof(d) offset(r = 0.6) offset(delta = -0.6 - d)
        polygon(concat([[-3.5, 0], [4.5, 0]], [for (yy = [4.5 : -0.25 : -3.5]) [yy, H - (R - sqrt(R * R - yy * yy))]]));
    hull() {                           // the profile is convex, so hull() only adds the 45 deg chamfer
        translate([CLIP_X0, 0, 0]) rotate([90, 0, 90]) linear_extrude(4.5) prof(0);
        translate([CLIP_X0, 0, 0]) rotate([90, 0, 90]) linear_extrude(5.0) prof(0.5);
    }
}

// ---------------------------------------------------------------- ball caster (trial, instead of the skid)
// STANDARD BOARD (hole (50, 4)); the Lite has its own caster below (caster_lite_*).
// Same mount as skid_clip() (split pin in the 3.2 mm hole), same coordinates (z = 0 PCB bottom, floor z = H).
// NOTE: the ball centre here is for the ball in the MIDDLE of its cavity.  Under the robot's weight the ball is
// pushed up by BALL_CLR (0.35), so the board sits about 0.35 mm lower and the housing is closer to the floor than
// the README numbers (print: 0.55 -> about 0.2 mm).  The Lite caster below is designed for the loaded state.
// A ball plus its housing does not fit between the PCB and the floor (4.0 mm), so the ball sits just IN FRONT of
// the board edge; a sled-shaped arm under the PCB carries the pin.
//   caster_print(): 4 mm ball printed in place inside the housing (one part).  The housing stays below the PCB top
//                   and inside the 5 mm width of the snap skid (contact 1.5 mm ahead of the edge).
//   caster_bead():  housing only, a DAISO pearl-like bead (6 mm) is pressed in from the floor side
//                   (contact 3.5 mm ahead of the edge, the housing is 1.6 mm higher than the PCB top).
// Both print LYING ON THEIR SIDE like skid_clip (the pin prongs and the bead finger bend along the layers).
// The ball touches the bed through a 0.25 mm flat, so the housing has a small window on the bed side.
PRINT_BALL_D = 4.0;                    // printed ball
PRINT_LIP = 0.3;                       // its floor-side opening = 3.7 mm (the ball sticks out 0.55 mm)
BALL_D    = 6.0;                       // bead diameter - MEASURE YOUR BEADS (calipers) and set this
BALL_LIP  = 0.4;                       // the bead's floor-side opening is BALL_D - BALL_LIP (keeps it in)
BALL_CLR  = 0.35;                      // gap ball .. housing (print-in-place: 0.35 -> about 0.27 mm of air in the G-code)
BALL_FLAT = 0.25;                      // printed ball: flat on the bed (also sets the housing position)
BALL_TOP_CLR = 0.2;                    // extra gap above the ball in the print direction (+x): the roof sags a little
CASTER_WALL = 0.8;
EDGE_Y   = -4.0;                       // PCB front edge in these coordinates (hole at PCB y = 4; standard board only)
EDGE_GAP = 0.3;                        // housing .. PCB edge
ARM_W = 5.0;                           // sled under the PCB: x = CLIP_X0 .. +5 (fits between PS3 and PS4)
ARM_CLEAR = 1.0;                       // sled .. floor at its rear end
ARM_Y1 = 3.0;                          // rear end of the sled
BEAD_SLIT = 0.8;                       // slit that frees the front half of the lip (bead version)

function caster_rc(D) = D / 2 + BALL_CLR;
function caster_zc(H, D) = H - D / 2;                                     // ball centre (below the PCB bottom)
function caster_xb(D) = CLIP_X0 + D / 2 - BALL_FLAT;
function caster_yb(H, D) = EDGE_Y - EDGE_GAP
    - (caster_zc(H, D) <= 0 ? caster_rc(D) : sqrt(pow(caster_rc(D), 2) - pow(caster_zc(H, D), 2)));  // cavity clears the edge
function caster_zl(H, D, lip) = caster_zc(H, D) + sqrt(pow(caster_rc(D), 2) - pow((D - lip) / 2, 2));  // housing bottom

module caster_housing(H = SKID_H, D = PRINT_BALL_D, lip = PRINT_LIP, slit = false) {
    xb = caster_xb(D); yb = caster_yb(H, D); zc = caster_zc(H, D); zl = caster_zl(H, D, lip);
    ro = caster_rc(D) + CASTER_WALL;
    T = PCB_T + 0.15;
    RR = 1.2;                                                   // rounded rear edge of the sled
    difference() {
        union() {
            intersection() {
                union() {
                    translate([xb, yb, zc]) sphere(r = ro, $fn = 48);
                    hull() {                                    // sled: blends the ball housing into the arm
                        intersection() {
                            translate([xb, yb, zc]) sphere(r = ro, $fn = 48);
                            translate([CLIP_X0, -50, -50]) cube([ARM_W, 100, 100]);
                        }
                        translate([CLIP_X0, ARM_Y1 - 0.01, 0]) cube([ARM_W, 0.01, 0.01]);
                        translate([CLIP_X0, ARM_Y1 - RR, H - ARM_CLEAR - RR]) rotate([0, 90, 0]) cylinder(r = RR, h = ARM_W, $fn = 32);
                    }
                }
                union() {
                    translate([CLIP_X0, -50, 0]) cube([50, 100, zl]);                      // under the PCB level
                    translate([CLIP_X0, -50, -50]) cube([50, 50 + EDGE_Y - EDGE_GAP, 50]); // above it: only in front of the edge
                }
            }
            translate([0, 0, -T]) cylinder(d = CLIP_PIN_D, h = T + CLIP_ROOT + 0.01);
            translate([0, 0, -T - 1.3]) cylinder(d1 = 2.5, d2 = CLIP_BARB_D, h = 1.3);
        }
        hull() for (dx = [0, BALL_TOP_CLR]) translate([xb + dx, yb, zc]) sphere(r = caster_rc(D), $fn = 48);
        difference() {                 // pin pocket + slit: same as skid_clip()
            translate([0, 0, -0.01]) cylinder(d = CLIP_POCKET_D, h = CLIP_ROOT + 0.01);
            translate([0, 0, -1]) cylinder(d = CLIP_PIN_D, h = CLIP_ROOT + 2);
        }
        translate([-2.2, -CLIP_SLIT / 2, -T - 2]) cube([4.4, CLIP_SLIT, T + 2 + CLIP_ROOT]);
        translate([CLIP_X0 - 10, -10, -10]) cube([10, 20, 20]);                    // print face (pin)
        // bead version: free the front half of the lip so it can bend forward (in the layer plane) when the bead
        // is pushed in from below.  The rear half is stiff (it is joined to the arm).
        if (slit) translate([CLIP_X0 - 1, yb - BEAD_SLIT / 2, zc - D / 4]) cube([20, BEAD_SLIT, 20]);
    }
}

module caster_ball(H = SKID_H, D = PRINT_BALL_D) {
    intersection() {
        translate([caster_xb(D), caster_yb(H, D), caster_zc(H, D)]) sphere(d = D, $fn = 48);
        translate([CLIP_X0, -50, -50]) cube([100, 100, 100]);                           // the flat on the bed
    }
}
module bead(H = SKID_H) translate([caster_xb(BALL_D), caster_yb(H, BALL_D), caster_zc(H, BALL_D)]) sphere(d = BALL_D);

module caster_print(H = SKID_H) { caster_housing(H); caster_ball(H); }
module caster_bead(H = SKID_H)  { caster_housing(H, BALL_D, BALL_LIP, slit = true); }

// ---------------------------------------------------------------- axle filing jig (teacher)
// The 20 mm axle goes in from the guard end until it stops at the wall; AXLE_FLAT of it sticks up over the open part
// (AXLE_FLAT_L long).  File it with a flat metal file until the file runs on the plastic, turn the jig over for the
// next one.  The guard (1.5 mm higher) keeps the file off the 3 mm that must stay round.  Prints flat, groove up.
module axle_jig() {
    L0 = 2; L1 = L0 + AXLE_FLAT_L; L2 = L0 + AXLE_L + 1; T = 6;
    difference() {
        union() {
            rbox([0, -6, 0], [L2, 12, T], 1.5);
            rbox([0, -6, 0], [L0, 12, T + 1.5], 0.5);                    // stop wall
            rbox([L1, -6, 0], [L2 - L1, 12, T + 1.5], 0.5);             // guard over the round end
        }
        translate([L0, 0, T + AXLE_FLAT - AXLE_D / 2]) rotate([0, 90, 0]) cylinder(d = AXLE_D + 0.15, h = L2, $fn = 32);
        translate([L0 + 3, -4.0, T - 0.4]) linear_extrude(1) text("1.7", size = 2.5, halign = "left", valign = "center",
                                                                   font = "Liberation Sans:style=Bold");   // across the flat
    }
}

// ---------------------------------------------------------------- Lite ball caster (rev.L3 default, in the skid hole (50, 11))
// The Lite board is 7.5 mm above the floor at the skid hole, so the ball fits UNDER the board.  Same split pin as
// skid_clip(), same coordinates (z = 0 PCB bottom, z = H floor under the hole, y = PCB y - 11), printed LYING ON ITS
// SIDE like skid_clip (pin flat and ball flat on the bed, x = CLIP_X0).
//   * PCB layout agreement (2026-10-07): on the PCB bottom the caster stays inside LITE_ZONE (no pads / copper there,
//     >= 0.3 mm from the centre sensor), on the PCB top the barb stays within LITE_TOP_R of the hole.
//   * Ball centre for the LOADED state: the robot's weight pushes the ball up against the roof of its cavity (it moves
//     up by the clearance).  The ball then touches the same floor line as a skid of height H (same tilt, same sensor
//     gap; uses tilt()).  As printed, the ball is in the middle of the cavity (clr all round).
//   * The bottom of the housing is a flat cone around the floor normal (tilted with the robot), so the gap between
//     housing and floor is the same all round: r - clr - sqrt((r + clr)^2 - (r - lip / 2)^2) (bigger ball -> bigger gap).
//   caster_lite_print  (default): ball BEHIND the pin (yb > 0), as big as the zone allows: 6.0 (H 7.5 / 8.0), 5.5 (7.0).
//                      The housing is cut flat at x = LC_XTOP (zone edge); there the cavity has a small window
//                      (narrower than the ball), so the ball stays captive.  Housing .. floor about 0.9 mm.
//   caster_lite_print45: ball UNDER the pin (yb = 0): roof between pin pocket (z <= CLIP_ROOT) and cavity >= CASTER_WALL
//                      -> D = H - 3.0: 4.0 / 4.5 / 5.0.  Smaller footprint (y <= 14.7), housing .. floor about 0.37 mm.
//   caster_lite_bead   (teacher only): 4 mm ball pushed in from the floor side, under the pin.
LITE_ZONE  = [45.0, 55.0, 6.5, 21.0];    // x0, x1, y0, y1 allowed on the PCB bottom (PCB coordinates)
LITE_TOP_R = 2.4;                         // pin / barb on the PCB top: within this radius of the hole
LITE_BEAD_D = 4.0;                        // bead version: 4 mm ball (bearing steel ball or bead) - MEASURE IT
LITE_BEAD_CLR = 0.25;                     // bead version: not printed in place, so a smaller gap is enough
LC_TOP = [CLIP_X0, CLIP_X0 + 5.0, -3.3, 3.3];   // contact face on the PCB bottom (x0, x1, y0, y1), local: 5 x 6.6 mm
                                          // (>= 0.7 mm wall around the pin pocket under the 0.5 mm chamfer)
LC_XTOP = LITE_ZONE[1] - SKID_XY[0] - 0.7;      // big-ball version: flat print top, 0.7 mm inside the zone edge
LC_YB_MARGIN = 0.1;                       // extra distance cavity .. pin pocket (on top of CASTER_WALL)
LC_ROOT_Z = CLIP_ROOT + CASTER_WALL + 0.3;      // big-ball version: solid block around the pin pocket down to here
LC_DEBUG_ROT = 0;                         // checks only: turn the caster about the pin (180 = put in the wrong way)
LC_DEBUG_SHIFT = [0, 0, 0];               // checks only: move the caster (positive controls)
LC_DEBUG_MIRROR = false;                  // checks only: true = the caster as PRINTED (mirror image, see MIRROR WORLD)

function lc_zb(H, D, yb = 0) = let (t = tilt(H)) H - (D / 2 + sin(t) * yb) / cos(t);    // loaded ball centre
function lc_zc(H, D, clr, yb = 0) = lc_zb(H, D, yb) + clr;          // cavity centre = ball centre as printed
function lc_roof(H, D) = lc_zb(H, D) - D / 2 - CLIP_ROOT;           // under the pin: pocket bottom .. cavity top
function lc_print_d(H) = [for (d = [6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0]) if (lc_roof(H, d) >= CASTER_WALL - 0.01) d][0];
function lc_dopen(D, clr, lip) = sqrt(pow(D / 2 + clr, 2) - pow((D - lip) / 2, 2));     // cavity centre .. opening
function lc_floor_gap(H, D, clr, lip) = D / 2 - clr * cos(tilt(H)) - lc_dopen(D, clr, lip);   // housing .. floor
function lc_xmax(D, clr) = caster_xb(D) + BALL_TOP_CLR + D / 2 + clr + CASTER_WALL;
// ball behind the pin: smallest yb with CASTER_WALL (+ margin) between cavity and pin pocket (3 fixed-point steps)
function lc_ybreq(H, D, clr, yb) = let (zc = lc_zc(H, D, clr, yb), w = D / 2 + clr + CASTER_WALL + LC_YB_MARGIN,
    dz = max(0, zc - CLIP_ROOT), dh = CLIP_POCKET_D / 2 + sqrt(max(0, w * w - dz * dz)), xb = caster_xb(D))
    sqrt(max(0, dh * dh - xb * xb));
function lc_yb(H, D, clr = BALL_CLR) = lc_ybreq(H, D, clr, lc_ybreq(H, D, clr, lc_ybreq(H, D, clr, 5)));
// the big ball fits if: roof to the PCB >= CASTER_WALL, inside the zone (y), and the window at LC_XTOP keeps the ball
function lc_big_ok(H, D, clr = BALL_CLR) = let (yb = lc_yb(H, D, clr), rc = D / 2 + clr,
    dx = LC_XTOP - caster_xb(D) - BALL_TOP_CLR)
    lc_zb(H, D, yb) - D / 2 >= CASTER_WALL - 0.01 && SKID_XY[1] + yb + rc + CASTER_WALL <= LITE_ZONE[3] - 0.2
    && (dx >= rc + CASTER_WALL || (dx <= rc - 0.3 && sqrt(rc * rc - dx * dx) <= D / 2 - 0.3));
function lc_big_d(H) = [for (d = [6.0, 5.5, 5.0]) if (lc_big_ok(H, d)) d][0];

module caster_lite_housing(H = SKID_H, D = lc_print_d(SKID_H), clr = BALL_CLR, lip = PRINT_LIP, yb = 0, xtop = 99,
                           slit = false) {
    xb = caster_xb(D); zc = lc_zc(H, D, clr, yb);
    rc = D / 2 + clr; ro = rc + CASTER_WALL; a = (D - lip) / 2;
    T = PCB_T + 0.15;
    y1 = yb == 0 ? LC_TOP[3] : yb + 1.5;
    // (the rectangles start 1.5 mm beyond the bed plane, so the bed side is cut flat and not chamfered)
    module top_face(d) translate([0, 0, d]) linear_extrude(0.01) offset(r = 1.0) offset(delta = -1.0 - (0.5 - d))
        translate([LC_TOP[0] - 1.5, LC_TOP[2]]) square([LC_TOP[1] - LC_TOP[0] + 1.5, y1 - LC_TOP[2]]);
    difference() {
        union() {
            intersection() {
                hull() {               // rounded block: flat face on the PCB (0.5 mm chamfer) down to the ball housing
                    top_face(0); top_face(0.5);
                    for (dx = [0, BALL_TOP_CLR]) translate([xb + dx, yb, zc]) sphere(r = ro, $fn = 48);
                    if (yb > 0)        // ball behind the pin: keep a solid block around the pin pocket (>= 0.7 mm wall)
                        translate([0, 0, LC_ROOT_Z]) linear_extrude(0.01) offset(r = 1.0) offset(delta = -1.4)
                            translate([LC_TOP[0] - 1.5, LC_TOP[2]]) square([LC_TOP[1] - LC_TOP[0] + 1.5, LC_TOP[3] - LC_TOP[2]]);
                }
                // bottom: flat cone around the floor normal (robot tilted by tilt(H)), rising 30 deg outward from the
                // ball opening (radius a): same gap to the floor all round, blunt outer edge
                translate([xb, yb, zc]) rotate([-tilt(H), 0, 0]) translate([0, 0, lc_dopen(D, clr, lip)]) mirror([0, 0, 1])
                    cylinder(h = 30, r1 = a, r2 = a + 30 / tan(30));
                translate([CLIP_X0 - 1, -50, -50]) cube([xtop - CLIP_X0 + 1, 100, 100]);           // flat print top
            }
            translate([0, 0, -T]) cylinder(d = CLIP_PIN_D, h = T + CLIP_ROOT + 0.01);       // pin + barb: as skid_clip
            translate([0, 0, -T - 1.3]) cylinder(d1 = 2.5, d2 = CLIP_BARB_D, h = 1.3);
        }
        lc_cavity(H, D, clr, yb);
        difference() {                 // pin pocket + slit: same as skid_clip()
            translate([0, 0, -0.01]) cylinder(d = CLIP_POCKET_D, h = CLIP_ROOT + 0.01);
            translate([0, 0, -1]) cylinder(d = CLIP_PIN_D, h = CLIP_ROOT + 2);
        }
        translate([-2.2, -CLIP_SLIT / 2, -T - 2]) cube([4.4, CLIP_SLIT, T + 2 + CLIP_ROOT]);
        translate([CLIP_X0 - 10, -10, -10]) cube([10, 40, 30]);                    // print face (pin + ball flats)
        // bead version: a slit splits the lower half of the housing into a front and a rear finger, which bend apart
        // (in the layer plane) when the bead is pushed in from the floor side
        if (slit) translate([CLIP_X0 - 1, yb - BEAD_SLIT / 2, zc - D / 4]) cube([20, BEAD_SLIT, 20]);
        // ball behind the pin -> the part has a front: arrow (0.3 mm deep) on the face that touches the PCB, pointing
        // to the pin = to the front of the robot (like "▲まえ" on the board).  Turned 180 deg the housing would hit the
        // centre sensor; turned 90 deg it would leave the agreed zone.
        if (yb > 0) translate([1.3, 0, -0.01]) linear_extrude(0.31) polygon([[0, 2.7], [1.5, 4.2], [0.6, 4.2], [0.6, yb + 0.6],
                                                                             [-0.6, yb + 0.6], [-0.6, 4.2], [-1.5, 4.2]]);
    }
}
module lc_cavity(H, D, clr, yb, grow = 0)          // grow > 0: the cavity plus a wall (pocket-wall check)
    hull() for (dx = [0, BALL_TOP_CLR]) translate([caster_xb(D) + dx, yb, lc_zc(H, D, clr, yb)]) sphere(r = D / 2 + clr + grow, $fn = 48);

// ball: loaded = pushed up against the roof (assembly, floor checks); otherwise as printed (centre of the cavity)
module caster_lite_ball(H = SKID_H, D = lc_print_d(SKID_H), clr = BALL_CLR, yb = 0, loaded = false) {
    intersection() {
        translate([caster_xb(D), yb, loaded ? lc_zb(H, D, yb) : lc_zc(H, D, clr, yb)]) sphere(d = D, $fn = 48);
        translate([CLIP_X0, -50, -50]) cube([100, 100, 100]);                     // the flat on the bed
    }
}
// default: big ball behind the pin
module caster_lite_print_housing(H = SKID_H)
    caster_lite_housing(H, lc_big_d(H), BALL_CLR, PRINT_LIP, lc_yb(H, lc_big_d(H)), LC_XTOP);
module caster_lite_print_ball(H = SKID_H, loaded = false)
    caster_lite_ball(H, lc_big_d(H), BALL_CLR, lc_yb(H, lc_big_d(H)), loaded);
module caster_lite_print(H = SKID_H) { caster_lite_print_housing(H); caster_lite_print_ball(H); }
// small: ball under the pin
module caster_lite_print45_housing(H = SKID_H) caster_lite_housing(H, lc_print_d(H));
module caster_lite_print45_ball(H = SKID_H, loaded = false) caster_lite_ball(H, lc_print_d(H), loaded = loaded);
module caster_lite_print45(H = SKID_H) { caster_lite_print45_housing(H); caster_lite_print45_ball(H); }
// teacher-only bead version (under the pin)
module caster_lite_bead(H = SKID_H) { caster_lite_housing(H, LITE_BEAD_D, LITE_BEAD_CLR, BALL_LIP, slit = true); }
module lite_bead(H = SKID_H, loaded = false)
    translate([caster_xb(LITE_BEAD_D), 0, loaded ? lc_zb(H, LITE_BEAD_D) : lc_zc(H, LITE_BEAD_D, LITE_BEAD_CLR)])
        sphere(d = LITE_BEAD_D, $fn = 48);
// DAISO pearl-like bead 6 mm (BALL_D, the same beads as the standard board's caster_bead), pressed in from the
// floor side, BEHIND the pin like caster_lite_print (same housing, with the slit lips of the bead versions).
LB6_CLR = LITE_BEAD_CLR;
function lb6_yb(H) = lc_yb(H, BALL_D, LB6_CLR);
module caster_lite_bead6(H = SKID_H)
    caster_lite_housing(H, BALL_D, LB6_CLR, BALL_LIP, lb6_yb(H), LC_XTOP, slit = true);
module lite_bead6(H = SKID_H, loaded = false)
    translate([caster_xb(BALL_D), lb6_yb(H), loaded ? lc_zb(H, BALL_D, lb6_yb(H)) : lc_zc(H, BALL_D, LB6_CLR, lb6_yb(H))])
        sphere(d = BALL_D, $fn = 48);
// all the Lite casters (for the zone / sensor / pcb checks)
module caster_lite_all() { caster_lite_print(); caster_lite_print45(); caster_lite_bead(); lite_bead();
                           caster_lite_bead6(); lite_bead6(); }

// ---------------------------------------------------------------- simple models for the assembly / checks
module battery_box() {
    x0 = BOX_C[0] - BOX_L / 2;
    color("dimgray", 0.7) difference() {
        translate([x0, BOX_FRONT_Y, DECK_TOP]) cube([BOX_L, BOX_W, BOX_H]);
        for (s = [-1, 0, 1]) translate([x0 + 1.5, BOX_C[1] + s * 15.3, DECK_TOP + 1.5 + 7.25])
            rotate([0, 90, 0]) cylinder(d = 14.6, h = BOX_L - 3);
        // long walls: 15.0 mm "shoulders" between the corner posts, 7.0 mm finger cut in the middle
        for (yy = [BOX_FRONT_Y - 1, BOX_REAR_Y - 3]) {
            translate([x0 + 4.2, yy, DECK_TOP + BOX_SHOULDER_H]) cube([BOX_L - 8.3, 4, 10]);
            translate([x0 + BOX_UCUT[0], yy, DECK_TOP + BOX_UCUT_H]) cube([BOX_UCUT[1] - BOX_UCUT[0], 4, 20]);
        }
        for (h = BOX_HOLES) translate([h[0], h[1], DECK_TOP - 1]) cylinder(d = 3.5, h = 4);
    }
}

module sensors() {                 // sensor bodies on the PCB bottom, PS1..PS6 (Lite: PS1..PS3)
    for (x = SENSOR_XS)
        color("black") translate([x - SENSOR_BODY[0] / 2, SENSOR_Y - SENSOR_BODY[1] / 2, -PCB_T - SENSOR_BODY[2]])
            cube(SENSOR_BODY);
}

// ---------------------------------------------------------------- floor contact (side view, y-z plane)
// The robot stands on the two tyres (axle line) and on the skid.  The floor is a line through the skid contact
// at distance TYRE_R from the axle; tilt > 0 = nose up.  gap(p) = height of point p = [y, z] above the floor.
function tilt(H = SKID_H) = let (a = AXLE_Y - SKID_XY[1], b = AXIS_Z + PCB_T + H)
    acos(TYRE_R / sqrt(a * a + b * b)) - atan2(a, b);
function gap(p, H = SKID_H) = let (t = tilt(H))
    -sin(t) * (p[0] - SKID_XY[1]) + cos(t) * (p[1] + PCB_T + H);
echo(str("floor: skid ", SKID_H, " mm, tilt ", round(tilt() * 100) / 100, " deg, sensor lens ",
         round(gap([SENSOR_Y, -PCB_T - SENSOR_BODY[2]]) * 100) / 100, " mm above the floor, PCB front edge ",
         round(gap([0, -PCB_T]) * 100) / 100, " mm, rear screw heads (y 96) ",
         round(gap([96, -PCB_T - 2.1]) * 100) / 100, " mm"));

// floor as a solid (everything below the floor line), PCB coordinates; up > 0 raises it (positive controls)
CHECK_FLOOR_UP = 0;
module floor_below(up = 0, H = SKID_H)
    translate([0, SKID_XY[1], -PCB_T - H]) rotate([tilt(H), 0, 0]) translate([-100, -300, -30 + up]) cube([300, 600, 30]);

// Lite caster in place (PCB coordinates).  LC_DEBUG_* only for the positive controls of the checks.
module lc_at() translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) translate(LC_DEBUG_SHIFT) rotate([0, 0, LC_DEBUG_ROT])
    mirror([LC_DEBUG_MIRROR ? 1 : 0, 0, 0]) children();
// everything outside the area agreed with the PCB layout (LITE_ZONE under the board, r = LITE_TOP_R above it)
module lite_zone_outside() difference() {
    translate([-50, -50, -60]) cube([200, 200, 100]);
    translate([LITE_ZONE[0], LITE_ZONE[2], -60]) cube([LITE_ZONE[1] - LITE_ZONE[0], LITE_ZONE[3] - LITE_ZONE[2], 60 - PCB_T + 0.01]);
    translate([SKID_XY[0], SKID_XY[1], -PCB_T - 0.01]) cylinder(r = LITE_TOP_R, h = 30);
}
module sensors_grown(g) for (x = SENSOR_XS)     // sensor bodies + keep-out distance g
    translate([x - SENSOR_BODY[0] / 2 - g, SENSOR_Y - SENSOR_BODY[1] / 2 - g, -PCB_T - SENSOR_BODY[2] - g])
        cube(SENSOR_BODY + [2 * g, 2 * g, g]);

// independent check of the floor contact of a ball: common tangent of the tyre circle and the ball circle (side view)
function tilt_ball(yb, zb, r) = let (a = AXLE_Y - yb, b = AXIS_Z - zb)
    acos((TYRE_R - r) / sqrt(a * a + b * b)) - atan2(a, b);
function gap_ball(p, yb, zb, r) = let (t = tilt_ball(yb, zb, r)) -sin(t) * (p[0] - yb) + cos(t) * (p[1] - zb) + r;
function r2(v) = round(v * 100) / 100;
if (LITE) {
    // name, D, clr, lip, yb, xtop
    for (v = [["caster_lite_print", lc_big_d(SKID_H), BALL_CLR, PRINT_LIP, lc_yb(SKID_H, lc_big_d(SKID_H)), LC_XTOP],
              ["caster_lite_print45", lc_print_d(SKID_H), BALL_CLR, PRINT_LIP, 0, 99],
              ["caster_lite_bead", LITE_BEAD_D, LITE_BEAD_CLR, BALL_LIP, 0, 99],
              ["caster_lite_bead6", BALL_D, LB6_CLR, BALL_LIP, lb6_yb(SKID_H), LC_XTOP]])
        let (d = v[1], clr = v[2], lip = v[3], yb = v[4], zb = lc_zb(SKID_H, d, yb), ro = d / 2 + clr + CASTER_WALL,
             roof = yb == 0 ? lc_roof(SKID_H, d) : zb - d / 2,
             x1 = max(min(v[5], lc_xmax(d, clr)), caster_xb(d) + d / 2, LC_TOP[1]),
             y1 = max(yb + ro, yb == 0 ? LC_TOP[3] : yb + 1.5), yB = SKID_XY[1] + yb, zB = -PCB_T - zb)
        echo(str(v[0], " (H ", SKID_H, "): ball ", d, " mm, ", r2(yb), " mm behind the pin, roof ", r2(roof),
                 " mm, housing above the floor ", r2(lc_floor_gap(SKID_H, d, clr, lip)), " mm; check by tangent: tilt ",
                 r2(tilt_ball(yB, zB, d / 2)), " deg, sensor lens ",
                 r2(gap_ball([SENSOR_Y, -PCB_T - SENSOR_BODY[2]], yB, zB, d / 2)), " mm; on the PCB bottom x ",
                 r2(SKID_XY[0] + CLIP_X0), " .. ", r2(SKID_XY[0] + x1), ", y ",
                 r2(SKID_XY[1] + min(LC_TOP[2], yb - ro)), " .. ", r2(SKID_XY[1] + y1)));
}

module pcb() {                     // standard: 100 x 100 with the rear notches; Lite: 65 x 100 rectangle (x 17.5 .. 82.5)
    color("darkgreen", 0.8) translate([0, 0, -PCB_T]) linear_extrude(PCB_T) difference() {
        if (LITE)
            translate([NOTCH_X, 0]) offset(r = 2) offset(delta = -2) square([100 - 2 * NOTCH_X, 100]);
        else difference() {
            offset(r = 2) offset(delta = -2) square([100, 100]);
            translate([-1, 70]) square([NOTCH_X + 1, 31]);
            translate([100 - NOTCH_X, 70]) square([NOTCH_X + 1, 31]);
        }
        for (h = concat(all_holes(), [SKID_XY])) translate(h) circle(d = 3.2);
    }
}

module drive_side() {              // left side: gears, axle, wheel, tyre
    color("gold") pinion8();                                    // Tamiya 8T, outer face flush with the shaft tip
    color("white") translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40();
    color("goldenrod") translate([AXLE_END_X - AXLE_L, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) axle_rod();
    color("orange") translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel();
    if (LITE)                      // TPU tyre, centred in the groove
        color("black") translate([WHEEL_X1 - WHEEL_W / 2 + 1.7, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) tire_tpu();
    else
        color("black") translate([WHEEL_X1 - (WHEEL_W - 3.5) / 2, AXLE_Y, AXIS_Z]) rotate([0, -90, 0])
            rotate_extrude() translate([(23.7 + 3.5) / 2, 0]) circle(d = 3.5);
}

DECK_VARIANT = "screw";                // "screw" | "clip"
SKID_VARIANT = "clip";                 // standard board: "clip" | "caster_print" | "caster_bead"  (front support)
LITE_SUPPORT = "caster_print";         // Lite board:     "caster_print" (default, rev.L3) | "caster_print45" | "caster_bead" | "caster_bead6" | "skid"
module front_support() {
    assert(SKID_VARIANT == "clip" || !LITE, "Lite: choose the front support with LITE_SUPPORT");
    if (LITE) translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) {      // balls shown pushed up (loaded)
        if (LITE_SUPPORT == "caster_print") { color("white") caster_lite_print_housing(); color("orange") caster_lite_print_ball(loaded = true); }
        else if (LITE_SUPPORT == "caster_print45") { color("white") caster_lite_print45_housing(); color("orange") caster_lite_print45_ball(loaded = true); }
        else if (LITE_SUPPORT == "caster_bead") { color("white") caster_lite_bead(); color("silver") lite_bead(loaded = true); }
        else if (LITE_SUPPORT == "caster_bead6") { color("white") caster_lite_bead6(); color("ivory") lite_bead6(loaded = true); }
        else color("white") skid_clip();
    }
    else translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) {
        if (SKID_VARIANT == "caster_print") { color("white") caster_housing(); color("orange") caster_ball(); }
        else if (SKID_VARIANT == "caster_bead") {
            color("white") caster_bead();
            color("ivory") bead();
        }
        else color("white") skid_clip();
    }
}
module assembly() {
    pcb();
    color("orange") frame_left();
    color("orange") frame_right();
    motor_left();
    translate([100, 0, 0]) mirror([1, 0, 0]) motor_left();
    drive_side();
    translate([100, 0, 0]) mirror([1, 0, 0]) drive_side();
    if (DECK_VARIANT == "clip") color("deepskyblue") deck_clip(); else color("deepskyblue") deck();
    battery_box();
    front_support();
    sensors();
}

module screw_pan(L) { color("silver") { cylinder(d = 3, h = L); translate([0, 0, -2.1]) cylinder(d = 5.5, h = 2.1); } }
module screw_flat(L) { color("silver") { cylinder(d = 3, h = L - 1.65); translate([0, 0, L - 1.65]) cylinder(d1 = 3, d2 = 5.5, h = 1.65); } }
module nut(c = "silver") { color(c) difference() { cylinder(d = 6.35, h = 2.4, $fn = 6); translate([0, 0, -1]) cylinder(d = 3, h = 5); } }

// exploded view for the assembly guide (normal orientation, parts pulled apart upwards)
EX = [0, 28, 56, 80];
module exploded() {
    pcb(); sensors();
    color("white") translate([SKID_XY[0], SKID_XY[1], -PCB_T - 8]) mirror([0, 0, 1]) skid_clip();
    translate([0, 0, EX[1]]) {
        color("orange") frame_left(); color("orange") frame_right();
        motors(); drive_side(); translate([100, 0, 0]) mirror([1, 0, 0]) drive_side();
    }
    translate([0, 0, EX[2] - TOWER_TOP]) {
        color("deepskyblue") deck();
        for (h = all_holes()) translate([h[0], h[1], DECK_TOP + 3]) nut();
        for (h = BOX_HOLES) translate([h[0], h[1], TOWER_TOP - 6]) nut();
    }
    translate([0, 0, EX[3] - DECK_TOP]) battery_box();
    for (h = BOX_HOLES) translate([h[0], h[1], EX[3] + BOX_H + 14]) mirror([0, 0, 1]) screw_flat(8);
    for (h = all_holes()) translate([h[0], h[1], -PCB_T - 16]) screw_pan(20);
    // guide lines
    for (h = all_holes()) color("gray", 0.5) translate([h[0], h[1], -PCB_T - 16]) cylinder(d = 0.4, h = EX[2] + 10);
}

// ---------------------------------------------------------------- interference checks (should be empty)
module motors() { motor_left(); translate([100, 0, 0]) mirror([1, 0, 0]) motor_left(); }
module frames() { frame_left(); frame_right(); }

// motor insertion (left side; the right frame is the mirror image).  dx = shift along +x (inward) from the final place.
PIN_MARGIN = 0.1;                      // pinion OD 5.0 + this margin in the sweep checks
PINION_PHASE = 22.5;                   // half a tooth: a pinion tooth SPACE faces the 40T tooth on the mesh line
SLIDE_END = 0;                         // positive control: < 0 pushes the motor past its stop
module motor_parts(dx = 0, pin_d = MOD * (PINION_T + 2) + PIN_MARGIN) translate([dx, 0, 0]) {
    along_x(CAN_X0, CAN_X1 - CAN_X0) can_profile();                                                    // can
    translate([CAN_X1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 10, h = REAR_BOSS_X1 - CAN_X1);  // rear boss
    for (s = [-1, 1]) translate([CAN_X1, MOTOR_Y + s * 9.2 - 0.6, AXIS_Z - 1.5]) cube([3.5, 1.2, 3]);       // terminals
    motor_front(0, pin_d);
}
module motor_front(dx = 0, pin_d = MOD * (PINION_T + 2) + PIN_MARGIN) translate([dx, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) {
    translate([0, 0, FRONT_X0]) cylinder(d = BOSS_D, h = BOSS_L);                                         // front boss
    translate([0, 0, SHAFT_TIP_X]) cylinder(d = 2, h = FRONT_X0 - SHAFT_TIP_X);                           // shaft
    translate([0, 0, SHAFT_TIP_X]) cylinder(d = pin_d, h = 4);                                            // pinion (round)
}
// each part swept along x between dx0 and dx1 (all parts are convex, so hull() is the swept volume)
module motor_slide_sweep(dx0, dx1) {
    hull() { along_x(CAN_X0 + dx0, CAN_X1 - CAN_X0) can_profile(); along_x(CAN_X0 + dx1, CAN_X1 - CAN_X0) can_profile(); }
    hull() for (d = [dx0, dx1]) translate([CAN_X1 + d, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 10, h = REAR_BOSS_X1 - CAN_X1);
    for (s = [-1, 1]) hull() for (d = [dx0, dx1]) translate([CAN_X1 + d, MOTOR_Y + s * 9.2 - 0.6, AXIS_Z - 1.5]) cube([3.5, 1.2, 3]);
    hull() for (d = [dx0, dx1]) translate([d, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) translate([0, 0, FRONT_X0]) cylinder(d = BOSS_D, h = BOSS_L);
    hull() for (d = [dx0, dx1]) translate([d, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) translate([0, 0, SHAFT_TIP_X]) cylinder(d = MOD * (PINION_T + 2) + PIN_MARGIN, h = 4);
}
// laying the motor into the cradle at dx = MOTOR_SLIDE: everything dropped from 25 mm above.  The only contact allowed
// is the snap: the cradle walls above the motor axis (they open 0.14 mm per side), so they are left out of the check.
module motor_drop_sweep() {
    hull() for (z = [0, 25]) translate([0, 0, z]) motor_front(MOTOR_SLIDE);
    hull() for (z = [0, 25]) translate([MOTOR_SLIDE, 0, z]) along_x(CAN_X0, CAN_X1 - CAN_X0) can_profile();
    hull() for (z = [0, 25]) translate([MOTOR_SLIDE, MOTOR_Y, AXIS_Z + z]) rotate([0, 90, 0]) translate([0, 0, CAN_X1]) cylinder(d = 10, h = REAR_BOSS_X1 - CAN_X1);
    for (s = [-1, 1]) hull() for (z = [0, 25]) translate([CAN_X1 + MOTOR_SLIDE, MOTOR_Y + s * 9.2 - 0.6, AXIS_Z - 1.5 + z]) cube([3.5, 1.2, 3]);
}
module snap_lips() translate([CAN_X0 + 0.5 - 0.01, MOTOR_Y - CAN_R - WALL - 0.01, AXIS_Z]) cube([CAN_X1 - CAN_X0 - 1.0 + 0.02, CAN_W + 2 * WALL + 0.02, 2.2 + 0.01]);
module pinion_round(dx) translate([SHAFT_TIP_X + dx, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = MOD * (PINION_T + 2) + PIN_MARGIN, h = 4);
// the 8T pinion as it sits on the motor shaft (assembly views): tooth shape, turned so that it meshes with the 40T
module pinion8() translate([SHAFT_TIP_X, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) rotate(PINION_PHASE)
    difference() { linear_extrude(4) gear2d(MOD, PINION_T, 20, 0); translate([0, 0, -1]) cylinder(d = 1.9, h = 6); }
// 8T pinion (tooth shape, right phase) swept from its final place over the whole slide, against the printed 40T gear
module pinion_slide_teeth() translate([SHAFT_TIP_X, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) rotate(PINION_PHASE)
    linear_extrude(4 + MOTOR_SLIDE) gear2d(MOD, PINION_T, 20, 0);

// real left frame = the one drawn on the right in this mirror world (see the top of the file)
if (part == "frame_left") frame_right();
else if (part == "frame_right") frame_left();
else if (part == "deck") translate([0, 0, DECK_TOP]) mirror([0, 0, 1]) deck();      // upside down for printing
else if (part == "gear40") gear40();
else if (part == "wheel") wheel();
else if (part == "tire_tpu") tire_tpu();
else if (part == "skid") skid();
else if (part == "skid_clip") translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) skid_clip();   // lying on its side
else if (part == "caster_print") translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_print();  // lying on its side
else if (part == "caster_bead") translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_bead();
// check_caster_* test the caster of the board that is selected: standard -> caster_print/_bead at (50, 4),
// LITE=true -> caster_lite_print/_bead at (50, 11) (same as the check_caster_lite_* below)
else if (part == "check_caster_sensor" && LITE) intersection() { lc_at() caster_lite_all(); sensors_grown(0.3); }
else if (part == "check_caster_pcb" && LITE) intersection() { translate([0, 0, -0.01]) lc_at() caster_lite_all(); pcb(); }
else if (part == "check_caster_ball" && LITE) intersection() { caster_lite_print_housing(); caster_lite_print_ball(); }
else if (part == "check_casterbead_ball" && LITE) intersection() { caster_lite_bead(); lite_bead(); }
else if (part == "check_caster_sensor") intersection() { translate([50, 4, -PCB_T]) mirror([0, 0, 1]) caster_print(); sensors(); }
else if (part == "check_caster_pcb") intersection() { translate([50, 4, -PCB_T - 0.01]) mirror([0, 0, 1]) caster_print(); pcb(); }
else if (part == "check_caster_ball") intersection() { caster_housing(); caster_ball(); }
else if (part == "check_casterbead_ball") intersection() { caster_bead(); bead(); }
// Lite ball caster (run with -D LITE=true).  sensor: 0.3 mm keep-out around the sensor bodies.
else if (part == "caster_lite_print") { assert(LITE, "run with -D LITE=true"); translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_lite_print(); }
else if (part == "caster_lite_print45") { assert(LITE, "run with -D LITE=true"); translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_lite_print45(); }
else if (part == "caster_lite_bead") { assert(LITE, "run with -D LITE=true"); translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_lite_bead(); }
else if (part == "caster_lite_bead6") { assert(LITE, "run with -D LITE=true"); assert(lc_big_ok(SKID_H, BALL_D, LB6_CLR), "bead does not fit");
    translate([0, 0, -CLIP_X0]) rotate([0, -90, 0]) caster_lite_bead6(); }
else if (part == "axle_jig") axle_jig();
else if (part == "check_caster_lite_bead6_sensor") intersection() { lc_at() { caster_lite_bead6(); lite_bead6(); } sensors_grown(0.3); }
else if (part == "check_caster_lite_bead6_ball") intersection() { caster_lite_bead6(); lite_bead6(); }
else if (part == "check_caster_lite_bead6_floor") intersection() { lc_at() caster_lite_bead6(); floor_below(CHECK_FLOOR_UP); }
else if (part == "check_axle_dflat") intersection() {     // the filed axle clears the D flats of gear and wheel
    union() {
        gear40();
        translate([0, 0, 30]) wheel();
    }
    union() {
        translate([0, 0, AXLE_END_X - AXLE_L - GEAR_X0]) axle_rod();                    // in the gear's frame
        translate([0, 0, 30 + WHEEL_X1 - (AXLE_END_X - AXLE_L)]) mirror([0, 0, 1]) axle_rod();   // in the wheel's
    }
    // only the strip in front of the flat (|y| < 0.6, x > 0.5): there the round press fit (r >= 0.975) is not involved
    translate([0.5, -0.6, -20]) cube([5, 1.2, 80]);
}
else if (part == "check_caster_lite_sensor") intersection() { lc_at() { caster_lite_print(); caster_lite_print45(); } sensors_grown(0.3); }
else if (part == "check_caster_lite_bead_sensor") intersection() { lc_at() { caster_lite_bead(); lite_bead(); } sensors_grown(0.3); }
else if (part == "check_caster_lite_pcb") intersection() { translate([0, 0, -0.01]) lc_at() caster_lite_all(); pcb(); }
else if (part == "check_caster_lite_ball") intersection() { caster_lite_print_housing(); caster_lite_print_ball(); }
else if (part == "check_caster_lite45_ball") intersection() { caster_lite_print45_housing(); caster_lite_print45_ball(); }
else if (part == "check_caster_lite_bead_ball") intersection() { caster_lite_bead(); lite_bead(); }
else if (part == "check_caster_lite_pocketwall") intersection() {    // cavity + (CASTER_WALL - 0.05) must not reach the pin pocket
    let (D = lc_big_d(SKID_H)) lc_cavity(SKID_H, D, BALL_CLR, lc_yb(SKID_H, D), CASTER_WALL - 0.05);
    translate([0, 0, -0.01]) cylinder(d = CLIP_POCKET_D, h = CLIP_ROOT + 0.01); }
else if (part == "check_caster_lite_pocketroot") difference() {      // pin pocket + 0.6 mm wall must be inside the part
    intersection() { translate([0, 0, 0.01]) cylinder(r = CLIP_POCKET_D / 2 + 0.6, h = CLIP_ROOT + 0.6);
                     translate([CLIP_X0 + 0.01, -10, -1]) cube([10, 20, 10]); }          // (the bed side is open, as skid_clip)
    caster_lite_print_housing(); translate([0, 0, -1]) cylinder(d = CLIP_POCKET_D + 0.02, h = CLIP_ROOT + 1.01);
    translate([-2.3, -CLIP_SLIT / 2 - 0.01, -1]) cube([4.6, CLIP_SLIT + 0.02, CLIP_ROOT + 1.01]); }   // pin slit (as skid_clip)
else if (part == "check_caster_lite_floor") intersection() { lc_at() caster_lite_print_housing(); floor_below(CHECK_FLOOR_UP); }
else if (part == "check_caster_lite45_floor") intersection() { lc_at() caster_lite_print45_housing(); floor_below(CHECK_FLOOR_UP); }
else if (part == "check_caster_lite_bead_floor") intersection() { lc_at() caster_lite_bead(); floor_below(CHECK_FLOOR_UP); }
else if (part == "check_caster_lite_ballfloor") intersection() {      // loaded balls do not go below the floor
    lc_at() { caster_lite_print_ball(loaded = true); caster_lite_print45_ball(loaded = true); lite_bead(loaded = true);
              lite_bead6(loaded = true); }
    floor_below(CHECK_FLOOR_UP - 0.02); }
else if (part == "check_caster_lite_zone") intersection() { lc_at() caster_lite_all(); lite_zone_outside(); }
else if (part == "check_skidclip_lite_zone") intersection() { lc_at() skid_clip(); lite_zone_outside(); }
else if (part == "deck_clip")              // right side up; mirrored in y so the PRINTED claws are at x 31 / 65 (clear of J1)
    translate([0, DECK_FRONT[0] + DECK_REAR[1], -TOWER_TOP]) mirror([0, 1, 0]) deck_clip();
else if (part == "check_skidclip_sensor") intersection() { translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) skid_clip(); sensors(); }
else if (part == "check_skidclip_pcb") intersection() { translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) skid_clip(); pcb(); }
else if (part == "check_deckclip_motor") intersection() { deck_clip(); motors(); }
else if (part == "check_deckclip_frame") intersection() { deck_clip(); translate([0, 0, -0.01]) frames(); }
else if (part == "check_deckclip_box") intersection() { deck_clip(); translate([0, 0, 0.01]) battery_box(); }
else if (part == "check_deck_box") intersection() { deck(); translate([0, 0, 0.01]) battery_box(); }
else if (part == "check_deck_motor") intersection() { deck(); motors(); }
else if (part == "check_deck_frame") intersection() { deck(); translate([0, 0, -0.01]) frames(); }
else if (part == "check_frame_motor") intersection() { frames(); motors(); }
else if (part == "check_box_frame") intersection() { battery_box(); union() { frames(); motors(); } }
else if (part == "check_skid_sensor") intersection() { translate([SKID_XY[0], SKID_XY[1], -PCB_T]) mirror([0, 0, 1]) skid(); sensors(); }
else if (part == "check_gear_frame") intersection() { translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40(); frame_left(); }
else if (part == "check_pinion_plate") intersection() { frame_left(); hull() for (d = [SLIDE_END, MOTOR_SLIDE]) pinion_round(d); }
else if (part == "check_motor_slide") intersection() { frame_left(); motor_slide_sweep(SLIDE_END, MOTOR_SLIDE); }
else if (part == "check_motor_drop") intersection() { difference() { frame_left(); snap_lips(); } motor_drop_sweep(); }
else if (part == "check_shaft_wall") intersection() {    // the longest allowed shaft (+ pinion flush with its tip)
    frame_left();
    translate([-SHAFT_LONG, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) {
        translate([0, 0, SHAFT_TIP_X]) cylinder(d = 2, h = FRONT_X0 - SHAFT_TIP_X);
        translate([0, 0, SHAFT_TIP_X]) cylinder(d = MOD * (PINION_T + 2) + 0.1, h = 4);
    }
}
else if (part == "check_pinion_spur") intersection() { translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40(); pinion_slide_teeth(); }
else if (part == "check_wheel_frame") intersection() { translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel(); frame_left(); }
else if (part == "exploded") exploded();
else if (part == "none") { }                    // for include <> from other files
else assembly();
