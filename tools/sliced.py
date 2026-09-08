#!/usr/bin/env python3
"""Read print settings out of sliced files, locally or off the printer.

Two formats turn up on the Mars 5 Ultra:

  .goo  ELEGOO's own format, and what the printer runs natively. Big-endian,
        with a ~195 KB header (two preview images) followed by the print
        parameters. Fully readable.
  .ctb  Chitubox's format. The ones this printer holds are the encrypted
        variant (magic 0x12FD0107) — everything past byte 0x30 is ciphertext,
        so only what the slicer put in the filename can be recovered.

Field offsets below were located empirically and checked against files whose
filenames encode their own layer height and exposure.

The resin is reported as the Chitubox *profile* name, which is what the slicer
recorded rather than proof of what was in the vat.

Lift distance and speed are deliberately not reported: Chitubox writes four
identical placeholder (0.03, 0.05) pairs into that region, so the real motion
settings are not present in the file.
"""

import re
import struct
import urllib.request

GOO_HEADER_BYTES = 195_500          # enough to cover every field we read
GOO_MAGIC = b"V3.0"

# Null-terminated ASCII fields near the front of the .goo header.
GOO_TEXT = {
    "software":     (12, 32),
    "printer_name": (92, 32),
    "printer_type": (124, 32),
    "resin_profile": (156, 32),   # the Chitubox resin profile, e.g. "Elegoo Abs-like 3.0"
}

# Offsets into the .goo header, big-endian.
GOO = {
    "total_layers":     (195310, ">I"),
    "resolution_x":     (195314, ">H"),
    "resolution_y":     (195316, ">H"),
    "plate_x_mm":       (195320, ">f"),
    "plate_y_mm":       (195324, ">f"),
    "plate_z_mm":       (195328, ">f"),
    "layer_height_mm":  (195332, ">f"),
    "exposure_s":       (195336, ">f"),
    "turn_off_s":       (195341, ">f"),
    "bottom_rest_s":    (195353, ">f"),
    "rest_after_s":     (195365, ">f"),
    "bottom_exposure_s": (195369, ">f"),
    "bottom_layers":    (195373, ">I"),
}

CTB_ENCRYPTED_MAGIC = 0x12FD0107

# e.g. 32mm_P0094_Athamaru_A_S2P3_PRE.stl_0.030_2.800_2026_09_08_09_53.ctb
FROM_NAME = re.compile(
    r"_(?P<layer>\d\.\d{3})_(?P<exposure>\d\.\d{3})_"
    r"(?P<y>\d{4})_(?P<mo>\d{2})_(?P<d>\d{2})_(?P<h>\d{2})_(?P<mi>\d{2})\.(goo|ctb)$",
    re.IGNORECASE)


def fetch_head(source, nbytes):
    """Read the first nbytes of a local path or an http URL (via Range)."""
    if str(source).startswith(("http://", "https://")):
        req = urllib.request.Request(str(source),
                                     headers={"Range": f"bytes=0-{nbytes - 1}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    with open(source, "rb") as fh:
        return fh.read(nbytes)


def from_filename(name):
    m = FROM_NAME.search(name)
    if not m:
        return {}
    return {
        "layer_height_mm": float(m.group("layer")),
        "exposure_s": float(m.group("exposure")),
        "sliced": f'{m.group("y")}-{m.group("mo")}-{m.group("d")} '
                  f'{m.group("h")}:{m.group("mi")}',
    }


def read_goo(source, name=None):
    head = fetch_head(source, GOO_HEADER_BYTES)
    if head[:4] != GOO_MAGIC:
        raise ValueError(f"not a GOO v3.0 file (magic {head[:4]!r})")
    out = {"format": "goo"}
    for field, (off, size) in GOO_TEXT.items():
        out[field] = head[off:off + size].split(b"\x00")[0].decode("ascii", "replace").strip()
    for field, (off, fmt) in GOO.items():
        size = struct.calcsize(fmt)
        out[field] = struct.unpack(fmt, head[off:off + size])[0]
    for k in list(out):
        if isinstance(out[k], float):
            out[k] = round(out[k], 4)
    out.update({k: v for k, v in from_filename(name or str(source)).items()
                if k == "sliced"})
    return out


def read_ctb(source, name=None):
    head = fetch_head(source, 64)
    magic = struct.unpack("<I", head[0:4])[0]
    out = {"format": "ctb", "encrypted": magic == CTB_ENCRYPTED_MAGIC}
    out.update(from_filename(name or str(source)))
    if not out["encrypted"]:
        # Plaintext CTB keeps its parameters in a fixed header.
        head = fetch_head(source, 256)
        for field, off in [("layer_height_mm", 0x20), ("exposure_s", 0x24),
                           ("bottom_exposure_s", 0x28), ("turn_off_s", 0x2C)]:
            out[field] = round(struct.unpack("<f", head[off:off + 4])[0], 4)
        out["bottom_layers"] = struct.unpack("<I", head[0x30:0x34])[0]
    return out


def read(source, name=None):
    label = (name or str(source)).lower()
    if label.endswith(".goo"):
        return read_goo(source, name)
    if label.endswith(".ctb"):
        return read_ctb(source, name)
    raise ValueError(f"unsupported file type: {name or source}")
