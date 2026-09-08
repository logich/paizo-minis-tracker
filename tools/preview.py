#!/usr/bin/env python3
"""Extract the plate preview images embedded in a .goo file.

The header carries two rendered thumbnails of the build plate, which is the
only way to see what a plate actually held — Chitubox names the file after
whichever model was added first, so the name tells you almost nothing.

Layout, big-endian, confirmed by the fact that TotalLayers lands exactly at
195310 immediately after the second image:

    194     small preview   116 x 116  RGB565
    27108   big preview     290 x 290  RGB565
    195310  TotalLayers

PNG is written with zlib and struct so there is no dependency to install.
"""

import struct
import sys
import zlib

SMALL = (194, 116, 116)
BIG = (27108, 290, 290)


def rgb565_to_rgb(data, width, height):
    """Unpack big-endian RGB565 into rows of 8-bit RGB."""
    rows = []
    for y in range(height):
        row = bytearray()
        base = y * width * 2
        for x in range(width):
            (v,) = struct.unpack_from(">H", data, base + x * 2)
            r, g, b = (v >> 11) & 0x1F, (v >> 5) & 0x3F, v & 0x1F
            row += bytes(((r * 255) // 31, (g * 255) // 63, (b * 255) // 31))
        rows.append(bytes(row))
    return rows


def write_png(path, rows, width, height):
    def chunk(tag, payload):
        c = tag + payload
        return struct.pack(">I", len(payload)) + c + struct.pack(">I", zlib.crc32(c))

    raw = b"".join(b"\x00" + r for r in rows)          # filter byte 0 per scanline
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return path


def extract(header, out_path, which="big"):
    offset, width, height = BIG if which == "big" else SMALL
    need = offset + width * height * 2
    if len(header) < need:
        raise ValueError(f"header too short: {len(header)} < {need}")
    rows = rgb565_to_rgb(header[offset:need], width, height)
    return write_png(out_path, rows, width, height)


if __name__ == "__main__":
    import sliced
    if len(sys.argv) < 3:
        print("usage: preview.py <file|url|printer-filename> <out.png> [small|big]")
        sys.exit(2)
    src, out = sys.argv[1], sys.argv[2]
    which = sys.argv[3] if len(sys.argv) > 3 else "big"
    if not src.startswith("http"):
        import os, urllib.parse
        if not os.path.exists(src):
            src = ("http://192.168.1.151:3030/media/mmcblk0p3/"
                   + urllib.parse.quote(src))
    head = sliced.fetch_head(src, sliced.GOO_HEADER_BYTES)
    print(extract(head, out, which))
