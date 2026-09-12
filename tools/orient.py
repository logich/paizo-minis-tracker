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
    """Return (flat_down, all_down, peel_exposed) in mm^2 for one orientation.

    peel_exposed weights down-facing area by how much of it separates at once.
    The vat hinges at the rear, so the peel line runs left-right (along X) and
    sweeps front-to-rear (along Y). A sloped face contributes one strip per
    layer, running perpendicular to its in-plane gradient:

      gradient along Y -> strip spans X -> the full width releases the instant
                          the peel line arrives.  Worst case.
      gradient along X -> strip runs along Y -> the peel line crosses it
                          gradually.  Best case.

    So rotating about Y lowers both metrics, while rotating about X lowers
    island area but raises peel stress. They are not the same objective.
    """
    flat_cos = math.cos(math.radians(flat_deg))
    flat = down = peel = 0.0
    for nx, ny, nz, area in tris:
        x, y, z = rotate_normal((nx, ny, nz), rx, ry)
        if z >= 0:
            continue
        down += area
        if -z >= flat_cos:
            flat += area
        g = math.hypot(x, y)
        peel += area if g < 1e-9 else area * (abs(y) / g)
    return flat, down, peel


def search(path, stride=8, step=15, limit=45):
    tris = triangles(path, stride)
    scale = stride                     # sampled, so scale the totals back up
    results = []
    for rx in range(0, limit + 1, step):
        for ry in range(0, limit + 1, step):
            flat, down, peel = score(tris, rx, ry)
            results.append((flat * scale, down * scale, peel * scale, rx, ry))
    return sorted(results), len(tris) * stride


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: orient.py <file.stl> [step] [limit]")
        sys.exit(2)
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    res, ntri = search(sys.argv[1], step=step, limit=limit)
    print(f"  {ntri:,} triangles, sampled 1 in 8\n")
    base = next(r for r in res if r[3] == 0 and r[4] == 0)
    print(f"  {'rotX':>5} {'rotY':>5} {'flat-down':>11} {'peel-exposed':>14}"
          f"  vs as-modelled")
    for flat, down, peel, rx, ry in res[:10]:
        fi = flat / base[0] if base[0] else 1
        pe = peel / base[2] if base[2] else 1
        tag = "  <- as modelled" if (rx, ry) == (0, 0) else \
              f"  island {fi:>4.0%}, peel {pe:>4.0%}"
        print(f"  {rx:>5} {ry:>5} {flat:>11,.0f} {peel:>14,.0f}{tag}")
    both = [r for r in res if r[0] <= base[0] and r[2] <= base[2] and (r[3], r[4]) != (0, 0)]
    print()
    if both:
        b = min(both, key=lambda r: r[0] / base[0] + r[2] / base[2])
        print(f"  best that improves BOTH: rotX={b[3]} rotY={b[4]} "
              f"— island {b[0]/base[0]:.0%}, peel {b[2]/base[2]:.0%} of as-modelled")
    else:
        print("  no rotation tried improves both; island area and peel stress trade off here")
    print("  rotating about Y lowers both; about X lowers island area but raises peel")
