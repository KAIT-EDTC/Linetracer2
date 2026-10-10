"""Shared paths/helpers for the Linetracer2 KiCad generator scripts.

Two boards are generated from the same scripts; pick one with the environment variable LT2_VARIANT:
  (unset) / std : standard rev.A1  -> hardware/kicad/        Linetracer2.*
  lite          : Lite (rev.L3)    -> lite/hardware/kicad/   Linetracer2-Lite.*
                  (everything of the Lite board lives under lite/; its generators are in lite/scripts/)
"""
import glob
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARIANT = os.environ.get("LT2_VARIANT", "std") or "std"
if VARIANT not in ("std", "lite"):
    raise SystemExit("LT2_VARIANT must be 'std' or 'lite' (got %r)" % VARIANT)
if VARIANT == "lite":
    HWDIR = os.path.join(ROOT, "lite", "hardware")
    KDIR = os.path.join(HWDIR, "kicad")
    PROJ = "Linetracer2-Lite"
else:
    HWDIR = os.path.join(ROOT, "hardware")
    KDIR = os.path.join(HWDIR, "kicad")
    PROJ = "Linetracer2"
LIBDIR = os.path.join(KDIR, "lib")
LIBNICK = "Linetracer2"          # nickname of the project library (same for both boards)
LITE_SCRIPTS = os.path.join(ROOT, "lite", "scripts")   # gen_schematic_lite.py, gen_pcb_lite.py, post_pcb_lite.py

_NS = uuid.UUID("6c1d7a52-2f0e-4c0b-9d1c-4c2e5b1a7e10")


def uid(key):
    """Deterministic UUID so regenerated files diff cleanly."""
    return str(uuid.uuid5(_NS, key))


def _find(envvar, pattern):
    v = os.environ.get(envvar)
    if v and os.path.isdir(v):
        return v
    hits = sorted(glob.glob(os.path.expanduser(pattern)))
    if hits:
        return hits[-1]
    # inside the KiCad flatpak sandbox
    for p in ("/app/extensions/Library/" + pattern.rsplit("/", 1)[-1],):
        if os.path.isdir(p):
            return p
    raise SystemExit("KiCad library not found (%s). Set %s." % (pattern, envvar))


def sym_dir():
    return _find("KICAD_SYMBOL_DIR",
                 "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/stable/*/files/symbols")


def fp_dir():
    return _find("KICAD_FOOTPRINT_DIR",
                 "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/stable/*/files/footprints")
