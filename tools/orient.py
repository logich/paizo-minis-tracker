#!/usr/bin/env python3
"""Score a mesh's orientation for island and support risk, without slicing.

An island is a region of a layer with no connection to the layer below. The
large ones come from surfaces that are *nearly parallel to the plate and facing
down*: the whole face appears in one layer. Tilt the same face and it enters as
a thin sliver that grows layer by layer, so the island becomes small and the
supports have somewhere to stand.

So the metric is the area of downward-facing triangles within a few degrees of
horizontal — "flat-down area". Minimising it over candidate rotations is a good
proxy for minimising island area, and it costs a dot product per triangle
rather than a slice plus five minutes of UVtools.

Downward-facing area at any angle is reported too: that is roughly the support
burden, and a shallow overhang that is not flat still needs holding up.
"""

import math
import struct
import sys
from pathlib import Path


def triangles(path, stride=1):
    """Yield (normal, area) per triangle, computed from the vertices."""
    data = Path(path).read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    body = data[84:84 + n * 50]
    out = []
    for i, t in enumerate(struct.iter_unpack("<12fH", body)):
        if i % stride:
            continue
        ax, ay, az, bx, by, bz, cx, cy, cz = t[3:12]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag == 0:
            continue
        out.append((nx / mag, ny / mag, nz / mag, mag / 2.0))
    return out


def rotate_normal(n, rx, ry):
    """Rotate a normal by rx about X then ry about Y, both in degrees."""
    x, y, z = n
    a = math.radians(rx)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    b = math.radians(ry)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    return x, y, z


def score(tris, rx, ry, flat_deg=20.0):
    """Flat-down and total-down area for one orientation, in mm^2."""
    flat_cos = math.cos(math.radians(flat_deg))
    flat = down = 0.0
    for nx, ny, nz, area in tris:
        _, _, z = rotate_normal((nx, ny, nz), rx, ry)
        if z < 0:                      # faces downward
            down += area
            if -z >= flat_cos:         # and is within flat_deg of horizontal
                flat += area
    return flat, down


def search(path, stride=8, step=15, limit=45):
    tris = triangles(path, stride)
    scale = stride                     # sampled, so scale the totals back up
    results = []
    for rx in range(0, limit + 1, step):
        for ry in range(0, limit + 1, step):
            flat, down = score(tris, rx, ry)
            results.append((flat * scale, down * scale, rx, ry))
    return sorted(results), len(tris) * stride


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: orient.py <file.stl> [step] [limit]")
        sys.exit(2)
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    res, ntri = search(sys.argv[1], step=step, limit=limit)
    print(f"  {ntri:,} triangles, sampled 1 in 8\n")
    print(f"  {'rotX':>5} {'rotY':>5} {'flat-down mm2':>15} {'all-down mm2':>14}   island risk")
    base = next(r for r in res if r[2] == 0 and r[3] == 0)
    for flat, down, rx, ry in res[:8]:
        rel = flat / base[0] if base[0] else 1
        tag = "  <- as modelled" if (rx, ry) == (0, 0) else f"  {rel:.0%} of flat"
        print(f"  {rx:>5} {ry:>5} {flat:>15,.0f} {down:>14,.0f}{tag}")
    print(f"\n  as modelled (0,0): flat-down {base[0]:,.0f} mm2")
    best = res[0]
    print(f"  best of those tried: rotX={best[2]} rotY={best[3]}, "
          f"flat-down {best[0]:,.0f} mm2 "
          f"({best[0]/base[0]:.0%} of flat) ")
