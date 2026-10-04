#!/usr/bin/env python3
"""Write Linetracer2.kicad_pro (design rules + net classes) and the project lib tables."""
import json
import os

from kicad_env import KDIR, PROJ, uid


def netclass(name, track, clearance, via_d, via_drill, prio):
    return {
        "name": name, "bus_width": 12, "clearance": clearance, "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",
        "priority": prio, "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": track,
        "via_diameter": via_d, "via_drill": via_drill, "wire_width": 6,
    }


pro = {
    "board": {
        "3dviewports": [],
        "design_settings": {
            "defaults": {
                "board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "other_line_width": 0.1,
                "silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                "silk_text_thickness": 0.15, "zones": {"min_clearance": 0.3},
            },
            "rules": {
                "min_clearance": 0.2, "min_connection": 0.0, "min_copper_edge_clearance": 0.3,
                "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2,
                "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0,
                "min_text_height": 0.8, "min_text_thickness": 0.12, "min_through_hole_diameter": 0.3,
                "min_track_width": 0.2, "min_via_annular_width": 0.13, "min_via_diameter": 0.5,
                "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True,
            },
            "rule_severities": {
                "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                "silk_edge_clearance": "warning", "silk_over_copper": "warning", "silk_overlap": "warning",
                "text_height": "warning", "text_thickness": "warning", "courtyards_overlap": "warning",
                "missing_courtyard": "ignore", "footprint_type_mismatch": "ignore",
            },
            "track_widths": [0.0, 0.3, 0.5, 0.8, 1.0, 1.5],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.7, "drill": 0.35},
                               {"diameter": 1.0, "drill": 0.5}],
            "teardrop_options": [{"td_onpadsmd": True, "td_onroundshapesonly": False,
                                  "td_ontrackend": False, "td_onvia": True}],
        },
        "ipc2581": {}, "layer_presets": [], "viewports": [],
    },
    "boards": [],
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": PROJ + ".kicad_pro", "version": 3},
    "net_settings": {
        "classes": [
            netclass("Default", 0.3, 0.2, 0.7, 0.35, 2147483647),
            netclass("Power", 0.6, 0.25, 0.9, 0.45, 1),
            netclass("Motor", 1.0, 0.25, 1.0, 0.5, 0),
            netclass("Ground", 0.3, 0.2, 0.7, 0.35, 3),
        ],
        "meta": {"version": 4},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [
            {"netclass": "Motor", "pattern": "/VBAT"},
            {"netclass": "Ground", "pattern": "GND"},
            {"netclass": "Motor", "pattern": "/MOT_OUT*"},
            {"netclass": "Power", "pattern": "/VSYS"},
            {"netclass": "Power", "pattern": "+3V3"},
            {"netclass": "Power", "pattern": "/LED_K"},
        ],
    },
    "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "gerber/", "pos_files": "",
                              "specctra_dsn": "", "step": "", "svg": "", "vrml": ""}, "page_layout_descr_file": ""},
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[uid("sch/root"), "Root"]],
    "text_variables": {},
}

os.makedirs(KDIR, exist_ok=True)
with open(os.path.join(KDIR, PROJ + ".kicad_pro"), "w") as f:
    json.dump(pro, f, indent=2)
with open(os.path.join(KDIR, "sym-lib-table"), "w") as f:
    f.write('(sym_lib_table\n  (version 7)\n  (lib (name "Linetracer2")(type "KiCad")'
            '(uri "${KIPRJMOD}/lib/Linetracer2.kicad_sym")(options "")(descr "Linetracer2 project symbols"))\n)\n')
with open(os.path.join(KDIR, "fp-lib-table"), "w") as f:
    f.write('(fp_lib_table\n  (version 7)\n  (lib (name "Linetracer2")(type "KiCad")'
            '(uri "${KIPRJMOD}/lib/Linetracer2.pretty")(options "")(descr "Linetracer2 project footprints"))\n)\n')
print("wrote project files in", KDIR)
