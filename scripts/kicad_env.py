"""Shared paths/helpers for the Linetracer2 KiCad generator scripts."""
import glob
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.join(ROOT, "hardware", "kicad")
LIBDIR = os.path.join(KDIR, "lib")
PROJ = "Linetracer2"

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
