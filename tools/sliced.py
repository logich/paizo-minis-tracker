#!/usr/bin/env python3
"""Read print settings out of sliced files, locally or off the printer.

Two formats turn up on the Mars 5 Ultra:

  .goo  ELEGOO's own format, and what the printer runs natively. Big-endian,
        with a ~195 KB header (two preview images) followed by the print
        parameters. Fully readable.
  .ctb  Chitubox's format. The ones this printer holds are the encrypted
        variant (magic 0x12FD0107) — everything past byte 0x30 is ciphertext,
        so nothing but the filename is readable by us directly. UVtools can
        decrypt them, and is used when it is available; see uvtools_properties.

Field offsets below were located empirically and checked against files whose
filenames encode their own layer height and exposure.

The resin is reported as the Chitubox *profile* name, which is what the slicer
recorded rather than proof of what was in the vat.

Lift distance and speed are deliberately not reported: Chitubox writes four
identical placeholder (0.03, 0.05) pairs into that region, so the real motion
settings are not present in the file.
"""

import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

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

# ELEGOO SatelLite names only the time, packed, and no layer or exposure:
# e.g. P0099_Gutaki_Body_S2P3_STL_3_202609122351.goo
FROM_SATELLITE_NAME = re.compile(
    r"_(?P<y>20\d{2})(?P<mo>\d{2})(?P<d>\d{2})(?P<h>\d{2})(?P<mi>\d{2})\.(goo|ctb)$",
    re.IGNORECASE)


# Both hosts share this directory, so each keeps its own build: the Linux bundle
# in uvtools/, the macOS app bundle in uvtools-macos/.
_REPO = Path(__file__).resolve().parent.parent
UVTOOLS = (_REPO / "uvtools-macos" / "UVtools.app" / "Contents" / "MacOS" / "UVtoolsCmd"
           if sys.platform == "darwin" else _REPO / "uvtools" / "UVtoolsCmd")

# UVtools property name -> the name this module uses.
UVTOOLS_FIELDS = {
    "LayerHeight": "layer_height_mm",
    "ExposureTime": "exposure_s",
    "BottomExposureTime": "bottom_exposure_s",
    "BottomLayerCount": "bottom_layers",
    "LayerCount": "total_layers",
    "MaterialName": "resin_profile",
    "MachineName": "printer_name",
    "LiftHeight": "lift_height_mm",
    "LiftSpeed": "lift_speed",
    "RetractSpeed": "retract_speed",
    "PrintTime": "print_time_s",
    "MaterialGrams": "grams",
}


def uvtools_available():
    return UVTOOLS.exists()


def uvtools_properties(local_path):
    """Decrypt a .ctb with UVtools and return the properties we track.

    Needs the whole file locally, unlike the .goo header path — the encrypted
    layout puts what we want behind the ciphertext.
    """
    if not uvtools_available():
        return {}
    # UVtoolsCmd exits 1 even when print-properties succeeds, so judge it by
    # whether the output parses rather than by the return code.
    proc = subprocess.run(
        [str(UVTOOLS), "--no-progress", "print-properties", str(local_path),
         "--partial-mode"],
        capture_output=True, text=True, timeout=300)
    out = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^(\w+): (.*)$", line.strip())
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if key not in UVTOOLS_FIELDS:
            continue
        field = UVTOOLS_FIELDS[key]
        try:
            out[field] = int(raw) if field in ("bottom_layers", "total_layers") else float(raw)
        except ValueError:
            out[field] = raw           # names stay strings
    return out


def uvtools_thumbnail(local_path, out_path, index=0):
    """Write a plate thumbnail out of any file UVtools can open."""
    if not uvtools_available():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [str(UVTOOLS), "--no-progress", "extract", str(local_path), tmp,
             "-c", "Thumbnails"],
            capture_output=True, text=True, timeout=300)
        thumb = Path(tmp) / f"Thumbnail{index}.png"
        if not thumb.exists():
            return None
        shutil.copyfile(thumb, out_path)
        return out_path


# Some CDNs reject urllib's default User-Agent with a 403.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) paizo-minis-tracker"


def download(url, dest):
    """Fetch a whole file — UVtools cannot work from a range request, and
    artwork downloads want the entire image."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as fh:
        shutil.copyfileobj(r, fh)
    return dest


def fetch_head(source, nbytes):
    """Read the first nbytes of a local path or an http URL (via Range)."""
    if str(source).startswith(("http://", "https://")):
        req = urllib.request.Request(str(source),
                                     headers={"Range": f"bytes=0-{nbytes - 1}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 416:
                raise
            # The printer rejects a range longer than the file instead of
            # clamping it, which broke `runlog` once its log rolled over and
            # shrank below the 400 KB tail. A 416 means the file is smaller
            # than the request, so fetching the whole thing is cheap.
            with urllib.request.urlopen(str(source), timeout=60) as r:
                return r.read(nbytes)
    with open(source, "rb") as fh:
        return fh.read(nbytes)


def from_filename(name):
    m = FROM_NAME.search(name)
    out = {}
    if m:
        out = {"layer_height_mm": float(m.group("layer")),
               "exposure_s": float(m.group("exposure"))}
    else:
        m = FROM_SATELLITE_NAME.search(name)
        if not m:
            return {}
    out["sliced"] = (f'{m.group("y")}-{m.group("mo")}-{m.group("d")} '
                     f'{m.group("h")}:{m.group("mi")}')
    return out


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


def read_ctb(source, name=None, allow_download=True):
    head = fetch_head(source, 64)
    magic = struct.unpack("<I", head[0:4])[0]
    out = {"format": "ctb", "encrypted": magic == CTB_ENCRYPTED_MAGIC}
    out.update(from_filename(name or str(source)))
    if out["encrypted"] and uvtools_available() and allow_download:
        # The whole file has to come down for UVtools to decrypt it.
        try:
            if str(source).startswith("http"):
                with tempfile.NamedTemporaryFile(suffix=".ctb", delete=True) as tmp:
                    download(str(source), tmp.name)
                    props = uvtools_properties(tmp.name)
            else:
                props = uvtools_properties(source)
            if props:
                out.update(props)
                out["via"] = "uvtools"
        except Exception:
            pass
    if not out["encrypted"]:
        # Plaintext CTB keeps its parameters in a fixed header.
        head = fetch_head(source, 256)
        for field, off in [("layer_height_mm", 0x20), ("exposure_s", 0x24),
                           ("bottom_exposure_s", 0x28), ("turn_off_s", 0x2C)]:
            out[field] = round(struct.unpack("<f", head[off:off + 4])[0], 4)
        out["bottom_layers"] = struct.unpack("<I", head[0x30:0x34])[0]
    return out


def read(source, name=None, allow_download=True):
    """Read a sliced file's settings.

    allow_download=False keeps this cheap: .goo is always a range request, but
    decrypting a .ctb means pulling the whole 25-110 MB file, which is far too
    slow to do while merely listing what the printer holds.
    """
    label = (name or str(source)).lower()
    if label.endswith(".goo"):
        return read_goo(source, name)
    if label.endswith(".ctb"):
        return read_ctb(source, name, allow_download=allow_download)
    raise ValueError(f"unsupported file type: {name or source}")
