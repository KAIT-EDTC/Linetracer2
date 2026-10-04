// Linetracer2 - 3D printable mechanical parts (OpenSCAD 2021.01), rev.A1
//
//   part = "frame_left" | "frame_right" | "deck" | "gear40" | "wheel" | "tire_tpu" | "skid"
//        | "assembly" | "check_*" (interference checks, must be empty)
//   openscad -D 'part="frame_left"' -o frame_left.stl linetracer2_mech.scad
//
// Coordinates = PCB coordinates (mm): x -> right, y -> rear, z = 0 on the PCB TOP surface.
// (0,0) is the front-left corner of the board.  Floor is at z = -5.6 (PCB bottom 4.0 mm).
//
// Drive: FA-130RA + Tamiya 8T pinion (m0.5) -> printed 40T spur (m0.5) on a 2 mm axle, 5:1, wheel ~32 mm.
// Everything is held by screws (no tape):
//   4 x M3x20 pan  : from the PCB bottom, through the PCB and the frame towers, into nuts in the deck
//   2 x M3x8  flat : battery box floor -> deck (nuts in the deck)
//   1 x M3x8  flat : skid (from the floor side) -> NYLON nut on the PCB top (next to sensor solder joints)

part = "assembly";
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
HANG_Z   = 0.0;                        // lowest point (flat bottom -> prints without supports)
AXLE_D   = 2.0;
AXLE_L   = 20.0;                       // brass rod, 2 mm
AXLE_END_X = 19.3;                     // blind end of the axle hole (axle pushed in until it stops)
WHEEL_X1 = 7.2;                        // inner face of the wheel (0.3 mm from the spacer boss)
TOWER_D  = 9.6;
TOWER_TOP = 15.0;                      // = deck bottom
TOWER_FRONT_CLIP = 65.6;               // front tower must not reach into the motor can

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
SKID_H = 4.0;                          // = PCB bottom .. floor  (print 3.5 / 4.0 / 4.5 to tune sensor height)
SKID_D = 8.6;

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

module frame_left() {
    difference() {
        union() {
            // base plate on the PCB
            translate([NOTCH_X + 0.5, 58.0, 0]) cube([CAN_X1 + 0.7 - (NOTCH_X + 0.5), 100.5 - 58.0, BASE_T]);
            // cradle walls that hug the can (snap fit, 2.2 mm above the axis)
            translate([CAN_X0 + 0.5, 0, 0]) difference() {
                translate([0, MOTOR_Y - CAN_R - WALL, 0])
                    cube([CAN_X1 - CAN_X0 - 1.0, CAN_W + 2 * WALL, AXIS_Z + 2.2]);
                translate([-1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0]) rotate([0, 0, 90])
                    linear_extrude(CAN_X1 - CAN_X0 + 2) offset(delta = 0.1) can_profile();
                // open top so the motor can be pressed in
                translate([-1, MOTOR_Y - CAN_R + 0.45, AXIS_Z + 2.2 - 0.01]) cube([CAN_X1, CAN_W - 0.9, 20]);
            }
            // motor face plate (boss goes into it) + inner axle bearing
            translate([PLATE_X0, 64.0, 0]) cube([CAN_X0 - PLATE_X0, 100.5 - 64.0, AXIS_Z + 9]);
            translate([NOTCH_X - 0.5, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = FRONT_X0 - NOTCH_X + 0.5);
            // outer axle wall (in the wheel notch) with spacer bosses on both faces
            translate([OUTER_X0, 73.0, HANG_Z]) cube([OUTER_X1 - OUTER_X0, 100.5 - 73.0, AXIS_Z + 4 - HANG_Z]);
            translate([WHEEL_X1 + 0.3, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = OUTER_X0 - WHEEL_X1 - 0.3 + 0.01);
            translate([OUTER_X1 - 0.01, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 6, h = GEAR_X0 - 0.2 - OUTER_X1 + 0.01);
            // lower front bar under the pinion, rear bar behind the spur gear
            translate([OUTER_X0, 72.5, HANG_Z]) cube([FRONT_X0 - OUTER_X0, 4.5, 6.0 - HANG_Z]);
            translate([OUTER_X0, 99.0, HANG_Z]) cube([FRONT_X0 + BOSS_L - OUTER_X0, 1.5, AXIS_Z + 9 - HANG_Z]);
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
        // axle hole (2.0 mm axle -> 2.15 mm hole), blind at AXLE_END_X
        translate([-1, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = AXLE_D + 0.15, h = AXLE_END_X + 1);
        // room for pinion and spur gear between the walls
        translate([OUTER_X1, MOTOR_Y, AXIS_Z]) rotate([0, 90, 0])
            cylinder(d = MOD * (PINION_T + 2) + 2 * CLR + 1, h = PLATE_X0 - 0.5 - OUTER_X1);
        translate([GEAR_X0 - 0.2, AXLE_Y, AXIS_Z]) rotate([0, 90, 0])
            cylinder(d = MOD * (SPUR_T + 2) + 2 * CLR + 1, h = PLATE_X0 - (GEAR_X0 - 0.2));
        // motor pads M1 (+ relief holes) and C5 must stay free
        translate([37.5, 57.0, -1]) cube([12, 10.5, 10]);
        // M3 screw holes (screw from the PCB bottom; the nut is in the deck)
        for (h = HOLES) translate([h[0], h[1], 0]) m3_hole();
    }
}

module frame_right() { translate([100, 0, 0]) mirror([1, 0, 0]) frame_left(); }

// ---------------------------------------------------------------- deck (battery box carrier)
// Sits on the 4 towers.  Bars (front/rear) carry the nuts; the thin plate clears the motors by 0.1 mm
// and keeps them in their cradles.  Print UPSIDE DOWN (the battery side on the bed).
function all_holes() = [for (h = HOLES) h, for (h = HOLES) [100 - h[0], h[1]]];

module deck() {
    difference() {
        union() {
            translate([DECK_X0, DECK_FRONT[0], DECK_UNDER]) cube([DECK_X1 - DECK_X0, DECK_REAR[1] - DECK_FRONT[0], DECK_TOP - DECK_UNDER]);
            for (yy = [DECK_FRONT, DECK_REAR])
                translate([DECK_X0, yy[0], TOWER_TOP]) cube([DECK_X1 - DECK_X0, yy[1] - yy[0], DECK_TOP - TOWER_TOP]);
        }
        // M3x20 from below: lead-in cone, hole, nut pocket opening on the top (under the battery box)
        for (h = all_holes()) translate([h[0], h[1], 0]) {
            m3_hole();
            translate([0, 0, TOWER_TOP - 0.01]) cylinder(d1 = 5.0, d2 = 3.3, h = 0.85);
            translate([0, 0, TOWER_NUT_Z0]) nut_pocket(DECK_TOP - TOWER_NUT_Z0 + 1);
        }
        // battery box screws (M3x8 flat from inside the box): hole + nut pocket from below
        for (h = BOX_HOLES) translate([h[0], h[1], 0]) {
            m3_hole();
            translate([0, 0, TOWER_TOP - 1]) nut_pocket(1 + NUT_H + 0.2);
        }
        // windows over the motors (lighter, the motors can be seen)
        for (x = [37, 56]) translate([x, 70, DECK_UNDER - 1]) cube([7, 12, 5]);
        // "FRONT" arrow, engraved on the underside (visible when printing upside down)
        translate([40, 62.5, TOWER_TOP - 0.01]) linear_extrude(0.6) polygon([[-2.5, 0], [2.5, 0], [0, -3]]);
    }
}

// ---------------------------------------------------------------- 40T spur gear (printed)
// m0.5, 40 teeth, pressure angle 20 deg.  Outer face on the bed, hub on top.  Press fit on the 2 mm axle.
module gear40() {
    difference() {
        union() {
            linear_extrude(GEAR_X1 - GEAR_X0) gear2d(MOD, SPUR_T, 20, GEAR_BACKLASH);
            cylinder(d = 7, h = GEAR_X1 - GEAR_X0 + GEAR_HUB_L);
        }
        translate([0, 0, -1]) cylinder(d = AXLE_D - 0.05, h = 20);
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
            cylinder(d = RIM_D, h = WHEEL_W);
            cylinder(d = 8, h = WHEEL_W + 2);                     // hub (outer side)
        }
        translate([0, 0, (WHEEL_W - GROOVE_W) / 2]) difference() {
            cylinder(d = RIM_D + 1, h = GROOVE_W);
            translate([0, 0, -1]) cylinder(d = GROOVE_D, h = GROOVE_W + 2);
        }
        translate([0, 0, -1]) cylinder(d = AXLE_D - 0.1, h = WHEEL_W + 4);   // press fit on 2 mm axle
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

// ---------------------------------------------------------------- simple models for the assembly / checks
module battery_box() {
    color("dimgray", 0.7) difference() {
        translate([BOX_C[0] - BOX_L / 2, BOX_C[1] - BOX_W / 2, DECK_TOP]) cube([BOX_L, BOX_W, BOX_H]);
        for (s = [-1, 0, 1]) translate([BOX_C[0] - BOX_L / 2 + 1.5, BOX_C[1] + s * 15.3, DECK_TOP + 1.5 + 7.25])
            rotate([0, 90, 0]) cylinder(d = 14.6, h = BOX_L - 3);
    }
}

module sensors() {                 // LBR-123F bodies on the PCB bottom (2.7 x 3.4 x 1.5), PS1..PS6
    for (x = [20, 32, 44, 56, 68, 80])
        color("black") translate([x - 1.35, 4 - 1.7, -PCB_T - 1.5]) cube([2.7, 3.4, 1.5]);
}

module pcb() {
    color("darkgreen", 0.8) translate([0, 0, -PCB_T]) linear_extrude(PCB_T) difference() {
        offset(r = 2) offset(delta = -2) square([100, 100]);
        translate([-1, 70]) square([NOTCH_X + 1, 31]);
        translate([100 - NOTCH_X, 70]) square([NOTCH_X + 1, 31]);
        for (h = concat(all_holes(), [[50, 4]])) translate(h) circle(d = 3.2);
    }
}

module drive_side() {              // left side: gears, axle, wheel, tyre
    gear_disc(PINION_T, SHAFT_TIP_X, SHAFT_TIP_X + 4, MOTOR_Y, "gold");
    color("white") translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40();
    color("goldenrod") translate([AXLE_END_X - AXLE_L, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) cylinder(d = 2, h = AXLE_L);
    color("orange") translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel();
    color("black") translate([WHEEL_X1 - (WHEEL_W - 3.5) / 2, AXLE_Y, AXIS_Z]) rotate([0, -90, 0])
        rotate_extrude() translate([(23.7 + 3.5) / 2, 0]) circle(d = 3.5);
}

module assembly() {
    pcb();
    color("orange") frame_left();
    color("orange") frame_right();
    motor_left();
    translate([100, 0, 0]) mirror([1, 0, 0]) motor_left();
    drive_side();
    translate([100, 0, 0]) mirror([1, 0, 0]) drive_side();
    color("deepskyblue") deck();
    battery_box();
    color("white") translate([50, 4, -PCB_T]) mirror([0, 0, 1]) skid();
    sensors();
}

module screw_pan(L) { color("silver") { cylinder(d = 3, h = L); translate([0, 0, -2.1]) cylinder(d = 5.5, h = 2.1); } }
module screw_flat(L) { color("silver") { cylinder(d = 3, h = L - 1.65); translate([0, 0, L - 1.65]) cylinder(d1 = 3, d2 = 5.5, h = 1.65); } }
module nut(c = "silver") { color(c) difference() { cylinder(d = 6.35, h = 2.4, $fn = 6); translate([0, 0, -1]) cylinder(d = 3, h = 5); } }

// exploded view for the assembly guide (normal orientation, parts pulled apart upwards)
EX = [0, 28, 56, 80];
module exploded() {
    pcb(); sensors();
    color("white") translate([50, 4, -PCB_T - 6]) mirror([0, 0, 1]) skid();
    translate([50, 4, -PCB_T - 13]) mirror([0, 0, 1]) screw_flat(8);
    translate([50, 4, 3]) nut("white");
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

if (part == "frame_left") frame_left();
else if (part == "frame_right") frame_right();
else if (part == "deck") translate([0, 0, DECK_TOP]) mirror([0, 0, 1]) deck();      // upside down for printing
else if (part == "gear40") gear40();
else if (part == "wheel") wheel();
else if (part == "tire_tpu") tire_tpu();
else if (part == "skid") skid();
else if (part == "check_deck_motor") intersection() { deck(); motors(); }
else if (part == "check_deck_frame") intersection() { deck(); translate([0, 0, -0.01]) frames(); }
else if (part == "check_frame_motor") intersection() { frames(); motors(); }
else if (part == "check_box_frame") intersection() { battery_box(); union() { frames(); motors(); } }
else if (part == "check_skid_sensor") intersection() { translate([50, 4, -PCB_T]) mirror([0, 0, 1]) skid(); sensors(); }
else if (part == "check_gear_frame") intersection() { translate([GEAR_X0, AXLE_Y, AXIS_Z]) rotate([0, 90, 0]) gear40(); frame_left(); }
else if (part == "check_wheel_frame") intersection() { translate([WHEEL_X1, AXLE_Y, AXIS_Z]) rotate([0, -90, 0]) wheel(); frame_left(); }
else if (part == "exploded") exploded();
else assembly();
