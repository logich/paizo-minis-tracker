#!/usr/bin/env python3
"""Print tracker for the Paizo minis collection.

PRINTS.md is the source of truth, meant to be read and edited by hand (or by
Claude in chat). dashboard.html is generated from it and should never be edited.

Usage: python3 tools/ledger.py <command> [args]
       with no command, runs status.

  status                       progress per release, Brian's review and reprint
                               queues, and the bases still to print
  scan                         find printable parts on disk and add rows for
                               anything new, never touching a Stage, Plate,
                               Result or Note already recorded
  build                        render dashboard.html from PRINTS.md, caching
                               each plate's preview to plates/<ID>.png
  printer                      list the sliced files the printer is holding,
                               newest first, with their settings
  plate <file> [id]            record a sliced file as a plate, reading its
                               settings from the file itself
  assign <plate|-> <stage> <target>...
                               set Stage, and Plate unless given "-"
  preview <file> [out] [small|big]
                               write a plate's build-plate preview to a PNG
  photo <code> printed|painted <file>
                               file a photograph into gallery/
  artwork <url>...             download MyMiniFactory logo renders and file
                               them into the right model directory
  merge-reference [file]       merge a browser agent's TSV of MyMiniFactory
                               links, names and artwork into reference/
  screen <file> [plate-id]     UVtools island check on a sliced file, with a
                               verdict — run it on 50mm/75mm models before
                               committing hours to the plate. Give a plate id to
                               archive the analysis under forensics/
  inspected <plate> ["note"]   acknowledge a screen flag: record what you found
                               and drop the plate off the flagged list
  runlog                       settings the printer actually ran with, from its
                               own log — the only place a setting changed by
                               hand on the machine is recorded

Targets for assign are matched against release and model names, or narrowed to
one part with "Model:Part". Quote anything containing spaces.

Stages: todo, reprint, sliced, printed, cleaned, cured, ready, review,
approved, primed, painted, delivered. A part counts as printed from "printed"
onward. "ready" means finished here and waiting for the next delivery;
"approved" means Brian has passed it, and sets Result to pass for you.

Model, Mini and Base columns are derived from reference/models.tsv and refreshed
on every scan, so don't hand-edit those. Base stock lives in the "## Bases"
section and is never inferred.

See README.md for the full guide, CLAUDE.md for the operating rules.
"""

import datetime
import html
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "PRINTS.md"
DASHBOARD = ROOT / "dashboard.html"
PLATE_IMAGES = ROOT / "plates"
BACKLOG = ROOT / "backlog.html"
GALLERY_DIR = ROOT / "gallery"
GALLERY = ROOT / "gallery.html"
FORENSICS = ROOT / "forensics"
REFERENCE = ROOT / "reference" / "models.tsv"

# Directories that hold no miniatures.
SKIP_DIRS = {".git", "bases", "V3_Cones_of_Calibration", "nord_autosave", "tools",
             "reference", "uvtools", "plates"}

# Ordered by how far along a part is. "reprint" ranks below "printed" on
# purpose: Brian rejected it, so it has to go back on a plate and should show up
# in the print queue again.
# Brian de-supports, reviews, then cures — so curing happens on his side after
# approval, not here before delivery. Parts reach him washed but still
# supported and green, which is why a pressure mark from de-supporting is a
# live explanation for a localised defect.
STAGES = ["todo", "reprint", "sliced", "printed", "cleaned",
          "ready", "review", "approved", "cured", "primed", "painted", "delivered",
          # Not a progression step. Some models ship alternative decompositions
          # — Scylla has Body + Tentacles *and* a combined Full — and only one
          # route gets printed. The other is "skipped": excluded from progress
          # totals and from base needs, not counted as done.
          "skipped"]
SKIPPED_STAGE = "skipped"
DONE_STAGE = "printed"      # counts as "off the printer"
READY_STAGE = "ready"       # finished here, waiting for the next delivery
REVIEW_STAGE = "review"     # with Brian
APPROVED_STAGE = "approved"  # Brian approved it
REPRINT_STAGE = "reprint"   # Brian rejected it

COLUMNS = ["Model", "Mini", "Base", "Part", "Scale", "Kind", "Stage", "Plate",
           "Result", "Notes"]
# Kind: blank for the normal print of a model. "extra" marks an additional
# print kept alongside an existing good one rather than replacing it — the
# 50mm Talmandor and Living Waterfall, printed large for use as monsters.
# An extra is never a reprint: nothing about it says the first print was wrong.
EXTRA_KIND = "extra"
# Everything on disk is the 32mm mesh. Other scales are prints the user makes by
# scaling up in Chitubox, so they exist only as rows here — scan must never
# invent them, and must never delete them for having no matching file.
NATIVE_SCALE = "32mm"
# The August extras packs are absent from the base-size sheet and ship no base
# STL, so nothing on disk or in reference/ says what they sit on. They are
# printed at 32mm heroic (114% of the 28mm mesh they ship) on 25mm bases, so
# assume that rather than leaving them uncounted. Override by hand in the row
# where it is wrong — a wall or a bear is not a 25mm mini.
DEFAULT_BASE_MM = "25"
PLATE_COLUMNS = ["ID", "Date", "Slicer file", "Resin", "Layer", "Exposure",
                 "Bottom exp", "Bottom layers", "Lift", "Bases", "Result", "Notes"]
# Filled in from the sliced file by `plate`; the rest are yours to fill in.
PLATE_AUTO = ("Date", "Slicer file", "Layer", "Exposure", "Bottom exp", "Bottom layers")

PRINTER_URL = "http://192.168.1.151:3030/media/mmcblk0p3/"
# The printer's own rolling log. Its "execute:" lines record the parameters the
# machine actually ran with, which is the only place a setting changed by hand
# on the printer shows up — the sliced file still says whatever Chitubox wrote.
PRINTER_LOG = "http://192.168.1.151:3030/media/mmcblk0p2/log"

PNUM = re.compile(r"P(\d{4})(?!\d)")
BASE_STL = re.compile(r"^(Round \d+|pathfinder_base_\d+|[\d]+mm-resized[\w-]*)\.stl$")
# Some models ship a re-cut with a trailing descriptor, e.g.
#   32mm_P0046_..._S1P3_STL Fixed Hand.stl
STL_32MM = re.compile(r"^32mm_(?P<core>.+?)_STL(?P<tag>[ _][^.]*)?\.stl$")
# Supported meshes ship as _SUP, or occasionally _PRE (P0094 Athamaru A).
SUP_32MM = re.compile(r"^32mm_(?P<core>.+?)_(SUP|PRE)(?P<tag>[ _][^.]*)?\.stl$")
STL_PLAIN = re.compile(r"^(?P<core>.+?)_STL(?P<tag>[ _][^.]*)?\.stl$")


# --------------------------------------------------------------------------
# reference data


def load_reference():
    ref = {}
    if not REFERENCE.exists():
        return ref
    for line in REFERENCE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("code\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        code, name, base_mm, size, pack = (p.strip() for p in parts[:5])
        mmf = parts[5].strip() if len(parts) > 5 else ""
        if mmf.isdigit():                      # a bare object id is enough
            mmf = f"https://www.myminifactory.com/object/3d-print-{code.lower()}-{mmf}"
        ref[code] = {"name": name, "base_mm": base_mm, "size": size,
                     "pack": pack, "mmf": mmf}
    return ref


# --------------------------------------------------------------------------
# filesystem scan


def part_labels(cores):
    """Name each part by what distinguishes it from its siblings.

    Filenames are not always consistent with their directory name (April's
    P0002_Kyra_Iconic_Fighter_WP1 holds files named ..._Kyra_Iconic_Cleric_...),
    so labels come from comparing the sibling files to each other and dropping
    the token prefix and suffix they all share.

        P0094_Athamaru_{A,B,C}_S2P3          -> A, B, C
        P0099_Gutaki_{Body,Tentacles_L}_S2P3 -> Body, Tentacles L
        a lone file                          -> main
    """
    if len(cores) == 1:
        return ["main"]
    toks = [c.split("_") for c in cores]
    shortest = min(len(t) for t in toks)

    prefix = 0
    while prefix < shortest - 1 and len({t[prefix] for t in toks}) == 1:
        prefix += 1
    def strippable(s):
        # Only strip a shared trailing token while some entry keeps a token of
        # its own; an entry left with nothing is the plain body part.
        if len({t[-1 - s] for t in toks}) != 1:
            return False
        return any(len(t) - prefix - (s + 1) >= 1 for t in toks)

    suffix = 0
    while suffix < shortest - prefix and strippable(suffix):
        suffix += 1

    labels = []
    for core, t in zip(cores, toks):
        middle = t[prefix:len(t) - suffix] if suffix else t[prefix:]
        labels.append(" ".join(middle) if middle else "main")
    return labels


def with_tag(label: str, tag) -> str:
    """Fold a filename's trailing descriptor into the part name."""
    if not tag:
        return label
    tag = tag.strip(" _").replace("_", " ").strip()
    if not tag:
        return label
    return tag if label == "main" else f"{label} ({tag})"


def release_of(rel_path: Path) -> str:
    return rel_path.parts[0]


def scan_disk(ref):
    """Return OrderedDict[release] -> OrderedDict[(model, part)] -> info."""
    found = OrderedDict()

    stl_files = []
    for path in ROOT.rglob("*.stl"):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        stl_files.append((rel, path))

    # Group every STL by its containing directory so we can decide per-model
    # whether a 32mm variant exists or the model ships at a single scale.
    by_dir = {}
    for rel, path in stl_files:
        by_dir.setdefault(rel.parent, []).append(rel.name)

    for dirpath, names in sorted(by_dir.items(), key=lambda kv: str(kv[0])):
        model = dirpath.name
        if not PNUM.search(model) and not model.lower().startswith(("paizo_", "pq")):
            continue  # base packs, loose test prints, etc.

        release = release_of(dirpath)
        thirty2 = [(n, m) for n in names if (m := STL_32MM.match(n))]
        supported = {m.group("core") for n in names if (m := SUP_32MM.match(n))}

        entries = []
        if thirty2:
            matched = sorted(thirty2)
            cores = [m.group("core") for _, m in matched]
            for (name, m), label in zip(matched, part_labels(cores)):
                entries.append({
                    "part": with_tag(label, m.group("tag")),
                    "file": name,
                    "presupported": m.group("core") in supported,
                })
        else:
            # Extras-sale packs ship pre-supported at a single scale, either as
            # _STL/_SUP pairs (PQ*) or as one _Supported.stl per mini (Paizo_*).
            candidates = [n for n in names if not BASE_STL.match(n)]
            pairs = sorted((n, m) for n in candidates if (m := STL_PLAIN.match(n)))
            if pairs:
                cores = [m.group("core") for _, m in pairs]
                for (name, m), label in zip(pairs, part_labels(cores)):
                    entries.append({
                        "part": with_tag(label, m.group("tag")),
                        "file": name,
                        "presupported": any(
                            s.startswith((f'{m.group("core")}_SUP',
                                          f'{m.group("core")}_PRE')) for s in names),
                    })
            else:
                singles = sorted(candidates)
                cores = [n[:-len(".stl")] for n in singles]
                for name, core, label in zip(singles, cores, part_labels(cores)):
                    entries.append({
                        "part": label,
                        "file": name,
                        "presupported": "Supported" in core,
                    })

        # Base size: prefer the base STL shipped alongside the model, fall back
        # to the reference sheet.
        on_disk_base = ""
        for name in names:
            m = (re.match(r"pathfinder_base_(\d+)\.stl$", name)
                 or re.match(r"Round (\d+)\.stl$", name))
            if m:
                on_disk_base = m.group(1)
                break

        pnum = PNUM.search(model)
        meta = ref.get(f"P{pnum.group(1)}") if pnum else None
        if meta is None:
            # Extras packs have no P-number, so they are keyed in
            # reference/models.tsv by their directory name instead.
            meta = ref.get(model)
        base_mm = (meta or {}).get("base_mm") or on_disk_base
        mini = (meta or {}).get("name") or model

        bucket = found.setdefault(release, OrderedDict())
        for entry in entries:
            bucket[(model, entry["part"])] = {
                "model": model,
                "part": entry["part"],
                "mini": mini,
                "base": f"{base_mm}mm" if base_mm else f"{DEFAULT_BASE_MM}mm",
                "size": (meta or {}).get("size", ""),
                "dir": str(dirpath),
                "file": entry["file"],
                "presupported": entry["presupported"],
                "disk_base": on_disk_base,
                "mmf": (meta or {}).get("mmf", ""),
            }
    return found


# --------------------------------------------------------------------------
# ledger parse / render


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_ledger():
    """Return (preamble_lines, plates, sections) from PRINTS.md."""
    preamble, plates, sections = [], [], OrderedDict()
    base_stock = []
    if not LEDGER.exists():
        return preamble, plates, sections, base_stock

    section = None
    in_preamble = True
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_preamble = False
            section = line[3:].strip()
            if section not in ("Plates", "Bases"):
                sections.setdefault(section, OrderedDict())
            continue
        if in_preamble:
            if line.startswith("# "):
                continue  # the H1 is re-emitted by write_ledger
            preamble.append(line)
            continue
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if not cells or cells[0] in ("Model", "ID", "Size") or set("".join(cells)) <= set("-: "):
            continue
        if section == "Bases":
            cells += [""] * (len(BASE_COLUMNS) - len(cells))
            base_stock.append(dict(zip(cells and BASE_COLUMNS, cells[:len(BASE_COLUMNS)])))
        elif section == "Plates":
            cells += [""] * (len(PLATE_COLUMNS) - len(cells))
            plates.append(dict(zip(PLATE_COLUMNS, cells[:len(PLATE_COLUMNS)])))
        elif section:
            cells += [""] * (len(COLUMNS) - len(cells))
            row = dict(zip(COLUMNS, cells[:len(COLUMNS)]))
            row["Scale"] = row.get("Scale") or NATIVE_SCALE
            sections[section][(row["Model"], row["Part"], row["Scale"])] = row
    while preamble and not preamble[0].strip():
        preamble.pop(0)
    while preamble and not preamble[-1].strip():
        preamble.pop()
    return preamble, plates, sections, base_stock


DEFAULT_BASE_STOCK = [
    {"Size": "25mm", "On hand": "", "Backlog": "0", "Notes": ""},
    {"Size": "50mm", "On hand": "", "Backlog": "0", "Notes": ""},
    {"Size": "75mm", "On hand": "", "Backlog": "0", "Notes": ""},
]

DEFAULT_PREAMBLE = """
Print tracker for the Paizo Printables miniature subscription. This file is the
source of truth; `dashboard.html` is generated from it. Ask Claude to update it,
or edit it by hand.

- **Stage** — one of: `todo`, `sliced`, `printed`, `cleaned`, `cured`, `primed`,
  `painted`, `delivered`. A part counts as printed from the `printed` stage on.
- **Plate** — an ID from the Plates table below, which carries the resin and
  exposure settings that print ran with.
- **Result** — blank, `pass`, or `fail`. Log a failure and then a fresh row's
  worth of notes rather than overwriting what went wrong.
- **Model / Mini / Base** — filled in automatically by `tools/ledger.py scan`
  from `reference/models.tsv`; don't hand-edit these.

Regenerate the dashboard after any change:

    python3 tools/ledger.py build
""".strip().splitlines()


def plate_sort_key(plate):
    """Newest plate first, matching the release order.

    A plate whose date could not be determined sorts to the bottom rather than
    the top: an unknown date is "?", which would otherwise outrank every real
    one under a reversed string sort.
    """
    date = plate.get("Date", "")
    return ("" if date == "?" else date, plate.get("ID", ""))


def release_sort_key(name):
    """Newest release first; undated directories (Dragons/) sink to the bottom."""
    m = re.match(r"(\d{4})(\d{2})", name)
    if m:
        return (0, -int(m.group(1) + m.group(2)), name)
    return (1, 0, name)


def render_table(columns, rows):
    out = ["| " + " | ".join(columns) + " |",
           "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return out


def write_ledger(preamble, plates, sections, base_stock):
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))
    lines = ["# Paizo Minis — Print Tracker", ""]
    lines += preamble or DEFAULT_PREAMBLE
    lines += ["", "## Bases", ""]
    lines += render_table(BASE_COLUMNS, base_stock or DEFAULT_BASE_STOCK)
    lines += ["", "## Plates", ""]
    lines += render_table(PLATE_COLUMNS,
                          sorted(plates, key=plate_sort_key, reverse=True))
    for name, rows in sections.items():
        lines += ["", f"## {name}", ""]
        lines += render_table(COLUMNS, rows.values())
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_scan(seed_printed_before=None):
    ref = load_reference()
    disk = scan_disk(ref)
    preamble, plates, sections, base_stock = parse_ledger()

    added = 0
    missing = []
    for release, parts in disk.items():
        section = sections.setdefault(release, OrderedDict())
        for (model, part), info in parts.items():
            key = (model, part, NATIVE_SCALE)
            if key in section:
                row = section[key]
            else:
                stage = "todo"
                if seed_printed_before and release < seed_printed_before:
                    stage = DONE_STAGE
                row = {"Model": info["model"], "Part": info["part"],
                       "Scale": NATIVE_SCALE, "Kind": "", "Stage": stage, "Plate": "",
                       "Result": "pass" if stage != "todo" else "", "Notes": ""}
                section[key] = row
                added += 1
            # derived columns, always refreshed — but only for the native scale;
            # a scaled-up print's base is the user's to state.
            row["Mini"] = info["mini"]
            row["Base"] = info["base"]
        sections[release] = OrderedDict(
            sorted(section.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))
        )

    for release, rows in sections.items():
        for (model, part, scale) in rows:
            if scale != NATIVE_SCALE:
                continue          # scaled-up prints have no file to match
            if (model, part) not in disk.get(release, {}):
                missing.append(f"{release}/{model} [{part}]")

    write_ledger(preamble, plates, sections, base_stock)

    total = sum(len(v) for v in sections.values())
    print(f"scan: {total} parts tracked across {len(sections)} releases ({added} new)")
    if missing:
        print(f"warning: {len(missing)} ledger rows have no matching file on disk:")
        for m in missing:
            print(f"  {m}")


# --------------------------------------------------------------------------
# status


def live_rows(rows):
    """Rows that count toward progress: everything not deliberately skipped."""
    return OrderedDict((k, r) for k, r in rows.items()
                       if r.get("Stage") != SKIPPED_STAGE)


def variant_of(part):
    """The miniature a part belongs to, when a model ships several sculpts.

    Multi-sculpt models label parts by a leading letter — `A`, or `A Body` and
    `A Cape` for one that also comes in pieces. Everything else (`Body`,
    `Tentacles L`, `Wing R`, `main`) is a component of a single miniature.
    Returns "" when the part carries no variant letter.
    """
    head = part.split()[0] if part.split() else ""
    return head if len(head) == 1 and head.isalpha() else ""


def bases_needed(rows):
    """Bases still to print for these rows, counted per miniature.

    One base per assembled mini, not per part: Gutaki's body and two tentacle
    arms make one mini on one 50mm base, while Athamaru A/B/C are three minis
    needing three 25mm bases.
    """
    pending = {}
    for (model, part, scale), r in live_rows(rows).items():
        if not r.get("Base") or r["Base"] == "?":
            continue          # unknown base size cannot be counted
        if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE):
            continue
        # Scale is part of the key: the same model at two scales is two
        # miniatures needing two bases, not one.
        pending.setdefault((model, r.get("Base", "?"), scale), set()).add(variant_of(part))
    out = Counter()
    for (model, base, scale), variants in pending.items():
        named = {v for v in variants if v}
        out[base] += len(named) if named else 1
    return out


BASES_ON_PLATE = re.compile(r"(\d+)\s*x\s*(\d+\s*mm)", re.I)
BASE_COLUMNS = ["Size", "On hand", "Backlog", "Notes"]


def bases_printed(plates):
    """Bases actually produced, from the Bases column of recorded plates.

    Only counts plates in this ledger, so anything printed before tracking
    started is invisible here.
    """
    out = Counter()
    for p in plates:
        for count, size in BASES_ON_PLATE.findall(p.get("Bases", "") or ""):
            out[size.replace(" ", "").lower()] += int(count)
    return out


def parse_base_stock(base_stock):
    """Turn the "## Bases" rows into {size: {on_hand, backlog}}.

    A blank "On hand" means unknown, which is different from zero: unknown
    subtracts nothing and is reported as such.
    """
    out = {}
    for row in base_stock:
        size = (row.get("Size") or "").strip().lower().replace(" ", "")
        if not size:
            continue
        def num(key):
            raw = (row.get(key) or "").strip()
            return int(raw) if raw.isdigit() else None
        out[size] = {"on_hand": num("On hand"), "backlog": num("Backlog") or 0,
                     "notes": (row.get("Notes") or "").strip()}
    return out


def bases_outstanding(sections, stock):
    """What still has to be printed, by base size.

        to print = what the unprinted minis need + backlog - on hand

    A part awaiting a reprint still counts. An earlier version skipped them,
    assuming a reprint follows a successful print whose base already exists —
    but a first print can fail outright, as the Gutaki body did, and then no
    base was ever made. Bases already in hand belong in "On hand", not in a
    guess made here.

    Stock is NOT inferred from what plates produced. Most bases were printed
    before this tracker existed, and a batch that looks spare is usually
    already allocated to older models — the six 50mm from P2609-07 were.
    On hand and backlog are stated by the user in the "## Bases" section.
    """
    need = Counter()
    for rows in sections.values():
        need.update(bases_needed(rows))

    sizes = set(need) | set(stock)
    rows = {}
    for size in sizes:
        entry = stock.get(size, {})
        backlog = entry.get("backlog", 0)
        on_hand = entry.get("on_hand")
        total = need.get(size, 0) + backlog
        rows[size] = {
            "need": need.get(size, 0),
            "backlog": backlog,
            "on_hand": on_hand,
            "to_print": total - (on_hand or 0),
            "known": on_hand is not None,
        }
    return rows


def stage_rank(stage):
    try:
        return STAGES.index(stage)
    except ValueError:
        return 0


def cmd_status():
    _, plates, sections, base_stock = parse_ledger()
    print_flagged()
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))
    ref = load_reference()
    disk = scan_disk(ref)
    grand = Counter()
    print(f"{'Release':<32} {'done':>5} {'/':^1} {'all':<5}  bases the remaining minis need")
    print("-" * 78)
    for release, rows in sections.items():
        counted = live_rows(rows)
        done = sum(1 for r in counted.values()
                   if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
        bases = bases_needed(rows)
        grand["done"] += done
        grand["all"] += len(counted)
        base_txt = ", ".join(f"{n}x {b}" for b, n in sorted(bases.items())) or "-"
        print(f"{release:<32} {done:>5} / {len(counted):<5}  {base_txt}")
    print("-" * 78)
    print(f"{'TOTAL':<32} {grand['done']:>5} / {grand['all']:<5}")

    stock = parse_base_stock(base_stock)
    report = bases_outstanding(sections, stock)
    if report:
        print("\nBases to print")
        print(f"  {'size':<6} {'minis':>6} {'backlog':>8} {'on hand':>8} {'to print':>15}")
        for size in sorted(report):
            r = report[size]
            hand = str(r["on_hand"]) if r["known"] else "?"
            gap = r["to_print"]
            verdict = str(gap) if gap > 0 else ("none" if gap == 0 else f"none ({-gap} spare)")
            print(f"  {size:<6} {r['need']:>6} {r['backlog']:>8} {hand:>8} {verdict:>15}")
        if any(not r["known"] for r in report.values()):
            print("  ? = on-hand not recorded; nothing subtracted for that size")
    extras = [r for rows in sections.values() for r in rows.values()
              if r.get("Kind") == EXTRA_KIND]
    if extras:
        print(f"\nAdditional prints: {len(extras)} part(s)")
        for r in extras:
            scale = "" if r["Scale"] == NATIVE_SCALE else f" @{r['Scale']}"
            note = f" — {r['Notes']}" if r.get("Notes") else ""
            print(f"  {r['Model']} [{r['Part']}]{scale} — {r['Stage']}{note}")

    skipped = [r for rows in sections.values() for r in rows.values()
               if r["Stage"] == SKIPPED_STAGE]
    if skipped:
        print(f"\nNot being printed: {len(skipped)} part(s)")
        for r in skipped:
            note = f" — {r['Notes']}" if r.get("Notes") else ""
            print(f"  {r['Model']} [{r['Part']}]{note}")

    for label, stage in (("Ready, awaiting the next delivery", READY_STAGE),
                         ("Awaiting Brian's review", REVIEW_STAGE),
                         ("Needs reprint", REPRINT_STAGE)):
        queued = [r for rows in sections.values() for r in rows.values()
                  if r["Stage"] == stage]
        if queued:
            print(f"\n{label}: {len(queued)} part(s)")
            for r in queued:
                note = f" — {r['Notes']}" if r.get("Notes") else ""
                print(f"  {r['Model']} [{r['Part']}]{note}")

    fails = [(rel, r) for rel, rows in sections.items() for r in rows.values()
             if r.get("Result") == "fail"]
    if fails:
        print(f"\n{len(fails)} recorded failure(s):")
        for rel, r in fails:
            print(f"  {r['Model']} [{r['Part']}] — {r.get('Notes') or 'no notes'}")
    if plates:
        print(f"\n{len(plates)} plate(s) logged; latest: {plates[-1]['ID']} ({plates[-1]['Date']})")


# --------------------------------------------------------------------------
# dashboard


CSS = """
:root{color-scheme:light dark;--bg:#f6f5f3;--card:#fff;--ink:#1b1a18;--muted:#6c6862;
--line:#e2ded8;--accent:#7a4f9e;--ok:#2f7d4f;--fail:#b3403a;--warn:#b1770f;--todo:#c9c4bc;--chip:#efece7}
@media(prefers-color-scheme:dark){:root{--bg:#16151a;--card:#1f1e25;--ink:#eceaf0;
--muted:#9d98a6;--line:#332f3b;--accent:#b48ede;--ok:#67c48d;--fail:#e8837c;--warn:#e0a83c;--todo:#3d3947;--chip:#2a2833}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--muted);margin:0 0 28px;font-size:14px}
.totals{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:32px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 16px;min-width:112px}
.stat b{display:block;font-size:24px;letter-spacing:-.02em}
.stat span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}
section{margin-bottom:38px}
.rel{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.rel h2{font-size:17px;margin:0;letter-spacing:-.01em}
.rel .count{color:var(--muted);font-size:13px}
.bar{height:6px;border-radius:3px;background:var(--todo);overflow:hidden;margin-bottom:14px}
.bar i{display:block;height:100%;background:var(--accent)}
.bases{font-size:12.5px;color:var(--muted);margin-bottom:12px}
.bases b{color:var(--ink);font-weight:600}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(268px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 14px;display:flex;gap:12px}
.card img{width:60px;height:60px;object-fit:cover;border-radius:7px;flex:0 0 60px;
background:var(--chip)}
.card .body{min-width:0;flex:1}
.name{font-weight:600;font-size:14px;margin-bottom:1px}
.name a.mmf{color:inherit;text-decoration:none;border-bottom:1px dotted var(--muted)}
.name a.mmf:hover{border-bottom-color:var(--accent)}
.code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;
color:var(--muted);margin-bottom:7px;word-break:break-all}
.parts{display:flex;flex-wrap:wrap;gap:4px}
.part{font-size:11.5px;padding:2px 7px;border-radius:999px;background:var(--chip);
border:1px solid var(--line);white-space:nowrap}
.part.done{background:color-mix(in srgb,var(--ok) 18%,transparent);
border-color:color-mix(in srgb,var(--ok) 45%,transparent)}
.part.fail,.part.reprint{background:color-mix(in srgb,var(--fail) 18%,transparent);
border-color:color-mix(in srgb,var(--fail) 50%,transparent)}
.part.review{background:color-mix(in srgb,var(--warn) 20%,transparent);
border-color:color-mix(in srgb,var(--warn) 55%,transparent)}
.part.skipped{opacity:.45;text-decoration:line-through}
.part.ready{background:color-mix(in srgb,var(--accent) 16%,transparent);
border-color:color-mix(in srgb,var(--accent) 45%,transparent)}
.badge{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;
background:var(--chip);border:1px solid var(--line);margin-left:6px;color:var(--muted)}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);
border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:640px}
.plateimg{width:64px;height:64px;object-fit:cover;border-radius:6px;background:#000;
display:block}
.noimg{color:var(--muted)}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
font-weight:600}
tr:last-child td{border-bottom:0}
footer{color:var(--muted);font-size:12.5px;margin-top:40px;border-top:1px solid var(--line);
padding-top:14px}
.nav{margin:-18px 0 22px;font-size:13px}
.nav a{color:var(--accent)}
"""


BACKLOG_CSS = """
.q{display:grid;gap:10px;margin-bottom:26px}
.item{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 14px;display:flex;gap:12px;align-items:flex-start}
.item img{width:52px;height:52px;object-fit:cover;border-radius:7px;flex:0 0 52px;
background:var(--chip)}
.item .b{min-width:0;flex:1}
.item .t{font-weight:600;font-size:14px}
.item .t .pt{font-weight:400;color:var(--muted)}
.why{font-size:13px;margin-top:3px}
.meta{font-size:11.5px;color:var(--muted);margin-top:4px;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;
border:1px solid var(--line);background:var(--chip);margin-right:5px}
.tag.rp{background:color-mix(in srgb,var(--fail) 18%,transparent);
border-color:color-mix(in srgb,var(--fail) 50%,transparent)}
.tag.td{background:color-mix(in srgb,var(--accent) 14%,transparent);
border-color:color-mix(in srgb,var(--accent) 40%,transparent)}
.rel2{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
margin:18px 0 8px}
.nav{margin-bottom:22px;font-size:13px}
.nav a{color:var(--accent)}
"""


GALLERY_CSS = """
.gal{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.gcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.gcard h3{font-size:14px;margin:0 0 2px}
.gcard h3 a{color:inherit;text-decoration:none;border-bottom:1px dotted var(--muted)}
.gcard .code{margin-bottom:9px}
.shots{display:flex;gap:8px;flex-wrap:wrap}
.shot{flex:1 1 92px;min-width:92px}
.shot img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:7px;
background:var(--chip);display:block}
.shot span{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin-top:4px;text-align:center}
.shot.paint span{color:var(--ok)}
.missing{border:1px dashed var(--line);border-radius:7px;aspect-ratio:1;display:flex;
align-items:center;justify-content:center;color:var(--muted);font-size:11px}
"""

GALLERY_KINDS = ("printed", "painted")
GALLERY_FILE = re.compile(r"^(?P<code>.+?)_(?P<kind>printed|painted)(?:-\d+)?\.(jpe?g|png|webp)$",
                          re.I)


def gallery_shots():
    """Map code -> {"printed": [paths], "painted": [paths]} from gallery/."""
    out = {}
    if not GALLERY_DIR.exists():
        return out
    for f in sorted(GALLERY_DIR.iterdir()):
        m = GALLERY_FILE.match(f.name)
        if m:
            out.setdefault(m.group("code"), {}).setdefault(m.group("kind").lower(), []).append(f)
    return out


def cmd_photo(code, kind, path):
    """File a photograph into gallery/ under the naming convention."""
    import shutil
    kind = kind.lower()
    if kind not in GALLERY_KINDS:
        print(f"kind must be one of: {', '.join(GALLERY_KINDS)}")
        return
    src = Path(path).expanduser()
    if not src.exists():
        print(f"no such file: {src}")
        return
    if code not in model_dirs_by_code():
        print(f"warning: {code} matches no model directory — filing it anyway")
    GALLERY_DIR.mkdir(exist_ok=True)
    ext = src.suffix.lower() or ".jpg"
    existing = len(gallery_shots().get(code, {}).get(kind, []))
    name = f"{code}_{kind}{'' if not existing else f'-{existing + 1}'}{ext}"
    shutil.copyfile(src, GALLERY_DIR / name)
    print(f"filed gallery/{name} ({(GALLERY_DIR / name).stat().st_size // 1024} KB)")
    print("now run: python3 tools/ledger.py build")


def cmd_gallery(sections, disk, ref, e):
    """Write gallery.html: vendor render, your print, Brian's paint job."""
    shots = gallery_shots()
    dirs = model_dirs_by_code()

    # code -> (display name, mmf link), from whichever row mentions the model
    meta = {}
    for release, rows in sections.items():
        for (model, part, scale), r in rows.items():
            m = PNUM.search(model)
            code = ("P" + m.group(1)) if m and ("P" + m.group(1)) in ref else model
            info = next((disk[release][k] for k in disk.get(release, {}) if k[0] == model), None)
            art = ""
            if info:
                found = (sorted(Path(ROOT / info["dir"]).glob("*.webp"))
                         or sorted(Path(ROOT / info["dir"]).glob("*.avif")))
                if found:
                    art = urllib.parse.quote(found[0].relative_to(ROOT).as_posix())
            meta.setdefault(code, (r.get("Mini") or model, ref.get(code, {}).get("mmf", ""), art))

    out = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>Paizo Minis Gallery</title>",
           f"<style>{CSS}{GALLERY_CSS}</style>", "</head>", "<body>",
           '<div class="wrap">', "<h1>Gallery</h1>",
           '<p class="sub">Finished prints, and Brian\'s paint jobs.</p>',
           '<div class="nav"><a href="dashboard.html">&larr; full dashboard</a> '
           '&middot; <a href="backlog.html">print backlog &rarr;</a></div>']

    painted = sum(len(v.get("painted", [])) for v in shots.values())
    printed = sum(len(v.get("printed", [])) for v in shots.values())
    out += ['<div class="totals">',
            f'<div class="stat"><b>{len(shots)}</b><span>minis pictured</span></div>',
            f'<div class="stat"><b>{printed}</b><span>print photos</span></div>',
            f'<div class="stat"><b>{painted}</b><span>painted by Brian</span></div>',
            "</div>"]

    if not shots:
        out.append('<p class="sub">Nothing here yet. Add photographs with '
                   '<code>tools/ledger.py photo &lt;code&gt; printed|painted &lt;file&gt;</code> '
                   '&mdash; see <code>gallery/README.md</code>.</p>')
    else:
        out.append('<div class="gal">')
        for code in sorted(shots):
            name, mmf, art = meta.get(code, (code, "", ""))
            title = (f'<a href="{e(mmf)}" target="_blank" rel="noreferrer">{e(name)}</a>'
                     if mmf else e(name))
            cells = []
            if art:
                cells.append(f'<div class="shot"><img src="{e(art)}" alt="" loading="lazy">'
                             f'<span>render</span></div>')
            for kind in GALLERY_KINDS:
                files = shots[code].get(kind, [])
                if not files:
                    cells.append(f'<div class="shot"><div class="missing">no {e(kind)}</div>'
                                 f'<span>{e(kind)}</span></div>')
                for f in files:
                    src = urllib.parse.quote(f.relative_to(ROOT).as_posix())
                    cls = "shot paint" if kind == "painted" else "shot"
                    cells.append(f'<div class="{cls}"><a href="{e(src)}" target="_blank">'
                                 f'<img src="{e(src)}" alt="" loading="lazy"></a>'
                                 f'<span>{e(kind)}</span></div>')
            out.append(f'<div class="gcard"><h3>{title}</h3>'
                       f'<div class="code">{e(code)}</div>'
                       f'<div class="shots">{"".join(cells)}</div></div>')
        out.append("</div>")

    out.append('<footer>Photographs live in <code>gallery/</code>, named '
               '<code>&lt;code&gt;_printed</code> or <code>&lt;code&gt;_painted</code>. '
               'Generated by <code>tools/ledger.py build</code>.</footer>')
    out.append("</div></body></html>")
    page = "\n".join(out) + "\n"
    GALLERY.write_text(page.encode("ascii", "xmlcharrefreplace").decode("ascii"), encoding="ascii")
    return len(shots), printed, painted


def cmd_backlog(sections, base_stock, disk, e):
    """Write backlog.html: everything still to print, and why.

    A working queue rather than a progress view — the dashboard already covers
    progress. Reprints lead, because their Notes carry the reason and that is
    what decides how to approach the next attempt.
    """
    def art(model, release):
        info = next((disk[release][k] for k in disk.get(release, {}) if k[0] == model), None)
        if not info:
            return ""
        found = (sorted(Path(ROOT / info["dir"]).glob("*.webp"))
                 or sorted(Path(ROOT / info["dir"]).glob("*.avif")))
        if not found:
            return ""
        src = urllib.parse.quote(found[0].relative_to(ROOT).as_posix())
        return f'<img src="{e(src)}" alt="" loading="lazy">'

    reprints, todo, extras = [], [], []
    for release, rows in sections.items():
        for (model, part, scale), r in rows.items():
            if r["Stage"] == REPRINT_STAGE:
                reprints.append((release, model, part, scale, r))
            elif r["Stage"] in ("todo", "sliced"):
                # An additional print is wanted work, not outstanding work, so
                # it is listed apart from things never printed at all.
                (extras if r.get("Kind") == EXTRA_KIND else todo).append(
                    (release, model, part, scale, r))

    report = bases_outstanding(sections, parse_base_stock(base_stock))
    to_print = {k: v for k, v in report.items() if v["to_print"] > 0}

    out = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>Paizo Minis Print Backlog</title>",
           f"<style>{CSS}{BACKLOG_CSS}</style>", "</head>", "<body>",
           '<div class="wrap">', "<h1>Print Backlog</h1>",
           '<p class="sub">What still has to go on the plate, and why.</p>',
           '<div class="nav"><a href="dashboard.html">&larr; full dashboard</a></div>',
           '<div class="totals">',
           f'<div class="stat"><b>{len(reprints)}</b><span>to reprint</span></div>',
           f'<div class="stat"><b>{len(todo)}</b><span>never printed</span></div>']
    for size, r in sorted(to_print.items()):
        out.append(f'<div class="stat"><b>{r["to_print"]}</b><span>{e(size)} bases</span></div>')
    out.append("</div>")

    def block(title, items, cls, show_reason):
        if not items:
            return
        out.append(f"<h2>{e(title)}</h2>")
        seen_rel = None
        out.append('<div class="q">')
        for release, model, part, scale, r in items:
            if release != seen_rel:
                out.append(f'</div><div class="rel2">{e(release)}</div><div class="q">')
                seen_rel = release
            mini = r.get("Mini") or model
            pt = "" if part == "main" else f' <span class="pt">{e(part)}</span>'
            sc = "" if scale == NATIVE_SCALE else f'<span class="tag">@{e(scale)}</span>'
            why = (f'<div class="why">{e(r["Notes"])}</div>'
                   if show_reason and r.get("Notes") else "")
            meta = [f'{e(model)}']
            if r.get("Base"):
                meta.append(f'{e(r["Base"])} base')
            if r.get("Plate"):
                meta.append(f'failed on {e(r["Plate"])}' if show_reason
                            else f'plate {e(r["Plate"])}')
            if r["Stage"] == "sliced":
                meta.append("sliced, on the printer")
            out.append(
                f'<div class="item">{art(model, release)}<div class="b">'
                f'<div class="t"><span class="tag {cls}">{e(r["Stage"])}</span>'
                f'{sc}{e(mini)}{pt}</div>{why}'
                f'<div class="meta">{" &middot; ".join(meta)}</div></div></div>')
        out.append("</div>")

    flags = flagged_plates()
    if flags:
        out.append("<h2>Plates flagged by screening</h2>")
        out.append('<p class="sub">Unresolved screen verdicts. Clear one with '
                   "<code>ledger.py inspected &lt;plate&gt; \"what you found\"</code>.</p>")
        out.append('<div class="q">')
        for v in flags:
            lvl = "FIX" if v.get("level") == "fix" else "look"
            out.append(
                f'<div class="item"><div class="b"><div class="t">'
                f'<span class="tag rp">{e(lvl)}</span>{e(v["plate"])}</div>'
                f'<div class="why">{e(flag_detail(v))}</div>'
                f'<div class="meta">{e(v.get("file", ""))}</div></div></div>')
        out.append("</div>")

    block("Needs reprinting", reprints, "rp", True)
    block("Never printed", todo, "td", False)
    block("Additional prints", extras, "td", True)

    if to_print:
        out.append("<h2>Bases to print</h2><div class=\"tablewrap\"><table><thead><tr>"
                   "<th>Size</th><th>Remaining minis</th><th>Backlog</th>"
                   "<th>On hand</th><th>To print</th></tr></thead><tbody>")
        for size, r in sorted(to_print.items()):
            hand = str(r["on_hand"]) if r["known"] else "?"
            out.append(f"<tr><td>{e(size)}</td><td>{r['need']}</td><td>{r['backlog']}</td>"
                       f"<td>{e(hand)}</td><td><b>{r['to_print']}</b></td></tr>")
        out.append("</tbody></table></div>")

    out.append('<footer>Generated by <code>tools/ledger.py build</code> from '
               '<code>PRINTS.md</code>. Reprint reasons come from each part\'s Notes.</footer>')
    out.append("</div></body></html>")
    page = "\n".join(out) + "\n"
    BACKLOG.write_text(page.encode("ascii", "xmlcharrefreplace").decode("ascii"),
                       encoding="ascii")
    return len(reprints), len(todo)


def cmd_build():
    ref = load_reference()
    disk = scan_disk(ref)
    _, plates, sections, base_stock = parse_ledger()
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))

    total = sum(len(live_rows(r)) for r in sections.values())
    done = sum(1 for rows in sections.values() for r in live_rows(rows).values()
               if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
    fails = sum(1 for rows in sections.values() for r in rows.values()
                if r.get("Result") == "fail")
    in_review = sum(1 for rows in sections.values() for r in rows.values()
                    if r["Stage"] == REVIEW_STAGE)
    ready = sum(1 for rows in sections.values() for r in rows.values()
                if r["Stage"] == READY_STAGE)
    to_reprint = sum(1 for rows in sections.values() for r in rows.values()
                     if r["Stage"] == REPRINT_STAGE)
    report = bases_outstanding(sections, parse_base_stock(base_stock))
    remaining_bases = Counter({size: r["to_print"] for size, r in report.items()
                               if r["to_print"] > 0})

    e = html.escape
    # A standalone file, not an embedded fragment: it needs a real document
    # head, or a browser opening it over file:// guesses windows-1252 and
    # mangles every non-ASCII character.
    out = ["<!doctype html>", '<html lang="en">', "<head>",
           '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>Paizo Minis Print Tracker</title>", f"<style>{CSS}</style>",
           "</head>", "<body>",
           '<div class="wrap">', "<h1>Paizo Minis — Print Tracker</h1>",
           f'<p class="sub">32&nbsp;mm prints for the Pathfinder game · '
           f'Elegoo Mars 5 Ultra · generated from PRINTS.md</p>',
           '<div class="nav"><a href="backlog.html">print backlog &rarr;</a> &middot; <a href="gallery.html">gallery &rarr;</a></div>',
           '<div class="totals">',
           f'<div class="stat"><b>{done}/{total}</b><span>parts printed</span></div>',
           f'<div class="stat"><b>{total - done}</b><span>remaining</span></div>',
           f'<div class="stat"><b>{ready}</b><span>ready to deliver</span></div>',
           f'<div class="stat"><b>{in_review}</b><span>awaiting Brian</span></div>',
           f'<div class="stat"><b>{to_reprint}</b><span>to reprint</span></div>',
           f'<div class="stat"><b>{fails}</b><span>failures</span></div>']
    for base, n in sorted(remaining_bases.items()):
        out.append(f'<div class="stat"><b>{n}</b><span>{e(base)} bases to print</span></div>')
    out.append("</div>")

    for release, rows in sections.items():
        counted = live_rows(rows)
        r_done = sum(1 for r in counted.values()
                     if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
        pct = round(100 * r_done / len(counted)) if counted else 0
        bases = bases_needed(rows)
        out.append("<section>")
        out.append(f'<div class="rel"><h2>{e(release)}</h2>'
                   f'<span class="count">{r_done} of {len(counted)} parts · {pct}%</span></div>')
        out.append(f'<div class="bar"><i style="width:{pct}%"></i></div>')
        if bases:
            txt = " · ".join(f"<b>{n}</b>&times; {e(b)}" for b, n in sorted(bases.items()))
            out.append(f'<div class="bases">Bases still needed: {txt}</div>')

        # group parts by model
        models = OrderedDict()
        for (model, part, scale), row in rows.items():
            models.setdefault(model, []).append(row)

        out.append('<div class="grid">')
        for model, parts in models.items():
            info = next((disk[release][(model, p["Part"])] for p in parts
                         if (model, p["Part"]) in disk.get(release, {})), None)
            mini = parts[0].get("Mini") or model
            base = parts[0].get("Base", "")
            thumb = ""
            if info:
                # webp first: 1000x1000 at ~11 KB, against avif's 720x720 at
                # ~40 KB and the jpg's ~122 KB. Higher resolution and a quarter
                # the size, and it is the easiest one to grab each month.
                # Filenames vary ("1000X1000-P0094_..._Logo.webp",
                # "1000X1000-P0100_Scylla_S2PB.webp"), so glob by extension.
                model_dir = Path(ROOT / info["dir"])
                art = (sorted(model_dir.glob("*.webp"))
                       or sorted(model_dir.glob("*.avif"))
                       or sorted(model_dir.glob("Release_*.jpg")))
                if art:
                    # Percent-encode: these paths contain spaces, which are fine
                    # over file:// but not valid in an HTTP request path.
                    src = urllib.parse.quote(art[0].relative_to(ROOT).as_posix())
                    thumb = f'<img src="{e(src)}" alt="" loading="lazy">'
            chips = []
            for p in sorted(parts, key=lambda r: r["Part"]):
                cls = "part"
                if p["Stage"] == REPRINT_STAGE:
                    cls += " reprint"
                elif p["Stage"] == REVIEW_STAGE:
                    cls += " review"
                elif p["Stage"] == READY_STAGE:
                    cls += " ready"
                elif p["Stage"] == SKIPPED_STAGE:
                    cls += " skipped"
                elif p.get("Result") == "fail":
                    cls += " fail"
                elif stage_rank(p["Stage"]) >= stage_rank(DONE_STAGE):
                    cls += " done"
                d = disk.get(release, {}).get((model, p["Part"]))
                if p.get("Scale", NATIVE_SCALE) != NATIVE_SCALE:
                    d = None          # no file on disk for a scaled-up print
                # No pre-supported file means supports have to be added in the slicer.
                warn = "" if (d is None or d["presupported"]) else " ⚠"
                scale = p.get("Scale", NATIVE_SCALE)
                suffix = "" if scale == NATIVE_SCALE else f' @{e(scale)}'
                label = f'{e(p["Part"])}{suffix} · {e(p["Stage"])}{warn}'
                title = " ".join(x for x in [p.get("Plate", ""), p.get("Notes", ""),
                                             "needs supports" if warn else ""] if x)
                chips.append(f'<span class="{cls}" title="{e(title)}">{label}</span>')
            link = info["mmf"] if info else ""
            name_html = (f'<a class="mmf" href="{e(link)}" target="_blank" '
                         f'rel="noreferrer">{e(mini)}</a>' if link else e(mini))
            out.append(
                f'<div class="card">{thumb}<div class="body">'
                f'<div class="name">{name_html}<span class="badge">{e(base)}</span></div>'
                f'<div class="code">{e(model)}</div>'
                f'<div class="parts">{"".join(chips)}</div></div></div>')
        out.append("</div></section>")

    if plates:
        out.append("<section><h2>Plates</h2>")
        out.append('<div class="tablewrap"><table><thead><tr><th>Plate</th>'
                   + "".join(f"<th>{e(c)}</th>" for c in PLATE_COLUMNS)
                   + "</tr></thead><tbody>")
        for p in sorted(plates, key=plate_sort_key, reverse=True):
            img = ensure_plate_preview(p)
            if img:
                src = urllib.parse.quote(img.relative_to(ROOT).as_posix())
                cell = (f'<a href="{e(src)}" target="_blank">'
                        f'<img class="plateimg" src="{e(src)}" alt="" loading="lazy"></a>')
            else:
                cell = '<span class="noimg">—</span>'
            cells = [f"<td>{cell}</td>"]
            cells += [f"<td>{e(p.get(c, ''))}</td>" for c in PLATE_COLUMNS]
            out.append("<tr>" + "".join(cells) + "</tr>")
        out.append("</tbody></table></div></section>")

    out.append('<footer>Generated by <code>tools/ledger.py build</code> from '
               '<code>PRINTS.md</code>. Base sizes cross-checked against the '
               'Paizo Printables reference sheet. \u26a0 marks a part with no '
               'pre-supported 32\u202fmm file \u2014 add supports in Chitubox.</footer>')
    out.append("</div>")
    out.append("</body></html>")
    # Escape every non-ASCII character as a numeric reference so the page also
    # survives being served with a wrong Content-Type.
    page = "\n".join(out) + "\n"
    DASHBOARD.write_text(page.encode("ascii", "xmlcharrefreplace").decode("ascii"),
                         encoding="ascii")
    print(f"build: wrote {DASHBOARD.relative_to(ROOT)} ({done}/{total} parts printed)")
    nr, nt = cmd_backlog(sections, base_stock, disk, e)
    print(f"build: wrote {BACKLOG.relative_to(ROOT)} "
          f"({nr} to reprint, {nt} never printed)")
    ng, np_, na = cmd_gallery(sections, disk, ref, e)
    print(f"build: wrote {GALLERY.relative_to(ROOT)} "
          f"({ng} minis, {np_} print photos, {na} painted)")



# --------------------------------------------------------------------------
# sliced files


def printer_index(base=PRINTER_URL):
    """Map each sliced file the printer holds to its modification time.

    Files named by hand ("Signifer-flotsam-captain-marauder.goo") carry no date
    in the filename, so the index's mtime is the only thing that dates them.
    """
    with urllib.request.urlopen(base, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    out = {}
    for href, mtime in re.findall(r'<a href="([^"]+)">[^<]*</a></td><td name=(-?\d+)>', page):
        name = urllib.parse.unquote(href)
        if name.lower().endswith((".goo", ".ctb")):
            out[name] = int(mtime)
    return out


def printer_files(base=PRINTER_URL):
    """List the sliced files the printer is holding."""
    return list(printer_index(base))


def describe(source, name, allow_download=True):
    import sliced
    try:
        return sliced.read(source, name=name, allow_download=allow_download)
    except Exception as exc:
        return {"format": "?", "error": str(exc)}


def mtime_date(source, name):
    """Fall back to the file's modification time when the name has no date."""
    try:
        if str(source).startswith("http"):
            stamp = printer_index().get(urllib.parse.unquote(name))
            if stamp is None:
                return ""
        else:
            stamp = Path(source).stat().st_mtime
        return datetime.date.fromtimestamp(stamp).isoformat()
    except Exception:
        return ""


def next_plate_id(plates, date):
    """P2609-01 — year, month, and a sequence within that month."""
    stem = f"P{date[2:4]}{date[5:7]}"
    used = [int(m.group(1)) for p in plates
            if (m := re.match(rf"{stem}-(\d+)$", p.get("ID", "")))]
    return f"{stem}-{max(used, default=0) + 1:02d}"


def cmd_printer():
    """Show what the printer is holding, newest first, with its settings."""
    try:
        names = printer_files()
    except Exception as exc:
        print(f"could not reach the printer at {PRINTER_URL}: {exc}")
        return
    rows = []
    for name in names:
        # Listing only: never pull whole ctb files just to tabulate them.
        info = describe(PRINTER_URL + urllib.parse.quote(name), name,
                        allow_download=False)
        rows.append((info.get("sliced", ""), name, info))
    rows.sort(reverse=True)

    print(f"{'sliced':<17} {'layer':>6} {'exp':>6} {'bot':>6} {'fmt':<4} file")
    print("-" * 100)
    for when, name, info in rows:
        layer = info.get("layer_height_mm", "")
        exp = info.get("exposure_s", "")
        bot = info.get("bottom_exposure_s", "")
        fmt = info["format"] + ("*" if info.get("encrypted") else "")
        print(f"{when or '—':<17} {layer:>6} {exp:>6} {bot if bot != '' else '—':>6} "
              f"{fmt:<4} {name[:58]}")
    print("-" * 100)
    print("* encrypted ctb — only the filename's layer/exposure is readable.")
    print("Chitubox names a file after the FIRST model added to the plate, so the")
    print("name does not tell you everything the plate holds — see the Plate column.")
    print("Lift distance and speed are not recoverable from either format.")


def ensure_plate_preview(plate):
    """Cache a plate's build-plate preview as plates/<ID>.png.

    Extracted once and kept: the .goo it comes from is eventually deleted off
    the printer, so this ends up being the only record of what a plate held.
    Never fails the caller — a missing preview just means no thumbnail.
    """
    plate_id, name = plate.get("ID", ""), plate.get("Slicer file", "")
    if not plate_id or not name.lower().endswith((".goo", ".ctb")):
        return None
    out = PLATE_IMAGES / f"{plate_id}.png"
    if out.exists():
        return out
    url = PRINTER_URL + urllib.parse.quote(name)
    try:
        import preview as preview_mod
        import sliced
        PLATE_IMAGES.mkdir(exist_ok=True)
        if name.lower().endswith(".goo"):
            head = sliced.fetch_head(url, sliced.GOO_HEADER_BYTES)
            preview_mod.extract(head, str(out), "big")
            return out
        # Encrypted ctb: only UVtools can get at the thumbnail, and it needs
        # the whole file.
        if not sliced.uvtools_available():
            return None
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".ctb") as tmp:
            sliced.download(url, tmp.name)
            # uvtools_thumbnail returns the str path it was given; keep this
            # function's contract as "a Path, or None".
            return out if sliced.uvtools_thumbnail(tmp.name, str(out)) else None
    except Exception:
        return None


EXECUTE_LINE = re.compile(r"execute: (.*)")


def cmd_runlog(tail_bytes=400_000):
    """Report the settings the printer actually ran with, from its own log.

    A setting changed on the printer never reaches the sliced file, so this is
    the authority for what a run really used. The log is a rolling buffer with
    no filenames in it, so treat this as "the most recent run", not as history.
    """
    import sliced
    try:
        raw = sliced.fetch_head(PRINTER_LOG, tail_bytes).decode("utf-8", "replace")
    except Exception as exc:
        print(f"could not read the printer log: {exc}")
        return

    seen = OrderedDict()
    for line in raw.splitlines():
        m = EXECUTE_LINE.search(line)
        if not m:
            continue
        fields = re.findall(r"(\w+) (-?[\d.]+)", m.group(1))
        # lift_position/drop_position change every layer; the rest is the recipe
        recipe = tuple((k, v) for k, v in fields
                       if k not in ("lift_position", "drop_position"))
        seen[recipe] = seen.get(recipe, 0) + 1

    if not seen:
        print("no execute lines in the log tail — is a print running?")
        return
    print(f"{len(seen)} distinct parameter set(s) in the last {tail_bytes // 1024} KB:\n")
    for recipe, layers in seen.items():
        d = dict(recipe)
        exposure = float(d.get("exposure_time", 0)) / 1000
        print(f"  {layers:>5} layers   exposure {exposure:.2f}s"
              f"   lift {d.get('lift_distance', '?')}mm @ {d.get('lift_speed', '?')}"
              f"   rest before/after {float(d.get('rest_time_before_lift', 0))/1000:.1f}s"
              f"/{float(d.get('rest_time_after_drop', 0))/1000:.1f}s")


def cmd_plate(source, plate_id=None, resin=None, notes=None):
    """Record a plate in PRINTS.md from a sliced file (local path or URL)."""
    name = source.rsplit("/", 1)[-1]
    if not source.startswith("http") and not Path(source).exists():
        # bare filename -> look for it on the printer
        source = PRINTER_URL + urllib.parse.quote(name)
    info = describe(source, urllib.parse.unquote(name))
    if "error" in info:
        print(f"could not read {name}: {info['error']}")
        return

    preamble, plates, sections, base_stock = parse_ledger()
    date = (info.get("sliced") or "")[:10]
    if not date:
        date = mtime_date(source, name)
    date = date or "?"
    row = {c: "" for c in PLATE_COLUMNS}
    row["ID"] = plate_id or next_plate_id(plates, date if date != "?" else "2026-01")
    row["Date"] = date
    row["Slicer file"] = urllib.parse.unquote(name)
    row["Layer"] = f'{info["layer_height_mm"]}mm' if "layer_height_mm" in info else ""
    row["Exposure"] = f'{info["exposure_s"]}s' if "exposure_s" in info else ""
    row["Bottom exp"] = f'{info["bottom_exposure_s"]}s' if "bottom_exposure_s" in info else ""
    row["Bottom layers"] = str(info.get("bottom_layers", ""))
    row["Resin"] = resin or info.get("resin_profile", "")
    if "lift_height_mm" in info:
        row["Lift"] = f'{info["lift_height_mm"]}mm @ {info["lift_speed"]}'
    if notes:
        row["Notes"] = notes
    elif info.get("via") == "uvtools":
        row["Notes"] = "encrypted ctb, decrypted with UVtools"
    elif info.get("encrypted"):
        row["Notes"] = "settings from encrypted ctb filename only (UVtools unavailable)"
    else:
        row["Notes"] = ""
    if any(p["ID"] == row["ID"] for p in plates):
        print(f"plate {row['ID']} already exists — pick another id")
        return
    plates.append(row)
    if ensure_plate_preview(row):
        print(f"cached the build-plate preview to plates/{row['ID']}.png")
    write_ledger(preamble, plates, sections, base_stock)
    print(f"added plate {row['ID']}: {row['Layer']} / {row['Exposure']} "
          f"(bottom {row['Bottom exp']} x{row['Bottom layers']}) from {row['Slicer file']}")
    print("Fill in Resin, Lift and Result, set the Plate column on the parts it "
          "printed, then run: python3 tools/ledger.py build")



def cmd_assign(plate, stage, targets):
    """Set Stage (and optionally Plate) on every part matching `targets`.

    A plate usually holds several models, and Chitubox names the file after
    whichever model was added first, so which parts were on a plate has to be
    recorded rather than inferred. Pass "-" as the plate to leave it alone.

    Targets are matched as substrings against both the release name and the
    model name, so "Dragons", "202604 Dragons" and "P0009" all work.

        ledger.py assign P2609-02 sliced P0094_Athamaru_S2P3
        ledger.py assign P2609-09 sliced P0099_Gutaki_S2P3:Body
        ledger.py assign - printed Dragons
    """
    if stage not in STAGES:
        print(f"unknown stage {stage!r}; expected one of: {', '.join(STAGES)}")
        return
    preamble, plates, sections, base_stock = parse_ledger()
    if plate != "-" and not any(p["ID"] == plate for p in plates):
        print(f"no plate {plate!r} in the Plates table")
        return

    def matches(target, release, model, part, scale):
        # "Model:Part" narrows to one part, "@50mm" to one scale; a bare target
        # takes whole models at the native scale.
        want_scale = NATIVE_SCALE
        if "@" in target:
            target, want_scale = target.rsplit("@", 1)
            want_scale = want_scale.strip()
        if scale.lower() != want_scale.lower():
            return False
        if ":" in target:
            want_model, want_part = target.rsplit(":", 1)
            return (want_model.lower() in model.lower()
                    and want_part.strip().lower() == part.lower())
        return target.lower() in release.lower() or target.lower() in model.lower()

    changed = []
    for release, rows in sections.items():
        for (model, part, scale), row in rows.items():
            hit = any(matches(t, release, model, part, scale) for t in targets)
            if not hit:
                continue
            row["Stage"] = stage
            if stage == APPROVED_STAGE and not row.get("Result"):
                # "approved" means exactly one thing; no need to hand-edit it.
                row["Result"] = "pass"
            if stage == SKIPPED_STAGE:
                # A route not taken was never printed, so it cannot have passed.
                row["Result"] = ""
            if plate != "-":
                row["Plate"] = plate
            label = f"{model} [{part}]"
            changed.append(label if scale == NATIVE_SCALE else f"{label} @{scale}")
    if not changed:
        print(f"nothing matched {targets}")
        return
    write_ledger(preamble, plates, sections, base_stock)
    print(f"set {len(changed)} part(s) to stage {stage}"
          + (f" on plate {plate}" if plate != "-" else ""))
    for c in changed[:6]:
        print(f"  {c}")
    if len(changed) > 6:
        print(f"  ... and {len(changed) - 6} more")


def cmd_preview(source, out_path=None, which="big"):
    """Write the plate preview embedded in a .goo to a PNG.

    The only reliable way to see what a plate actually held, since the filename
    names just the first model added to it.
    """
    import preview as preview_mod
    name = source.rsplit("/", 1)[-1]
    if not source.startswith("http") and not Path(source).exists():
        source = PRINTER_URL + urllib.parse.quote(name)
    import sliced
    is_goo = name.lower().endswith(".goo")
    if not is_goo and not sliced.uvtools_available():
        print("ctb previews need UVtools in ./uvtools; only .goo works without it")
        return
    out_path = out_path or re.sub(r"[^\w.-]", "_", name)[:60] + ".png"
    try:
        if is_goo:
            head = sliced.fetch_head(source, sliced.GOO_HEADER_BYTES)
            print("wrote", preview_mod.extract(head, out_path, which))
            return
        # Encrypted ctb: the GOO offsets would decode ciphertext into noise, so
        # hand it to UVtools, which needs the whole file.
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".ctb") as tmp:
            sliced.download(source, tmp.name)
            if sliced.uvtools_thumbnail(tmp.name, out_path):
                print("wrote", out_path)
            else:
                print(f"UVtools could not extract a thumbnail from {name}")
    except Exception as exc:
        print(f"could not extract a preview from {name}: {exc}")


def model_dirs_by_code():
    """Map both a P-number and a directory name to that model's directory.

    Extras packs have no P-number and are keyed by directory name, the same way
    reference/models.tsv keys them.
    """
    ref = load_reference()
    out = {}
    for parts in scan_disk(ref).values():
        for info in parts.values():
            out[info["model"]] = info["dir"]
            m = PNUM.search(info["model"])
            if m:
                out.setdefault("P" + m.group(1), info["dir"])
    return out


def artwork_filename(url):
    """Local filename for an artwork URL.

    The CDN serves through imgproxy, so URLs end in the *source* extension plus
    the delivered format: "..._Ezren.png@webp" is a webp. Save it as what it
    actually is, or browsers and the dashboard's glob both get it wrong.
    """
    stem = urllib.parse.unquote(url.rsplit("/", 1)[-1]).split("?")[0]
    fmt = "webp"
    if "@" in stem:
        stem, fmt = stem.rsplit("@", 1)
    stem = re.sub(r"\.(png|jpe?g|webp|avif)$", "", stem, flags=re.I)
    if fmt.lower() not in ("webp", "avif", "png", "jpg", "jpeg"):
        fmt = "webp"
    return f"{stem}.{fmt.lower()}"


def save_artwork(code, url, dirs):
    """Download one artwork file into the directory for `code`."""
    import sliced
    target_dir = dirs.get(code)
    if not target_dir:
        return None, f"{code}: no model directory on disk"
    out = ROOT / target_dir / artwork_filename(url)
    try:
        sliced.download(url, out)
        return out, None
    except Exception as exc:
        return None, f"{code}: download failed — {exc}"


def cmd_artwork(urls, codes=None):
    """Download artwork and file it by model.

    `codes` pairs one code per URL — that is how merge-reference calls it, and
    it is the reliable path: the vendor's image filenames do not all carry a
    P-number (April's are "1000X1000-april2026__0036_Ezren.png@webp"), so
    deriving the model from the URL alone silently skips about half the library.
    Bare URLs pasted into chat still fall back to that derivation.
    """
    dirs = model_dirs_by_code()
    saved, failed = 0, []
    for i, url in enumerate(urls):
        if codes:
            code = codes[i]
        else:
            m = PNUM.search(urllib.parse.unquote(url.rsplit("/", 1)[-1]))
            if not m:
                failed.append(f"no P-number in {url.rsplit('/', 1)[-1]} — pass a code")
                continue
            code = "P" + m.group(1)
        out, err = save_artwork(code, url, dirs)
        if err:
            failed.append(err)
        else:
            saved += 1
            print(f"  {code:<40} {out.stat().st_size // 1024:>4} KB  {out.name}")
    print(f"artwork: saved {saved}, {len(failed)} problem(s)")
    for f in failed[:10]:
        print(f"  {f}")


def cmd_merge_reference(path=None):
    """Merge a browser agent's findings into reference/models.tsv.

    Expects a TSV with a header naming its columns; `code` is required, and any
    of `mmf`, `name`, `base_mm`, `size` may accompany it. Artwork URLs under an
    `artwork` column are downloaded into the model directory.

    Written for handoff from an agent that has a logged-in browser: this session
    cannot reach MyMiniFactory (object pages 403 scripted requests), and that
    agent cannot reach this filesystem or the printer.
    """
    src = Path(path) if path else INCOMING
    if not src.exists():
        print(f"nothing to merge: {src} does not exist")
        return

    rows, header = [], None
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = [c.strip() for c in line.split("\t")]
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    if not rows or "code" not in (header or []):
        print("expected a tab-separated file with a 'code' column")
        return

    # rewrite models.tsv, updating matched codes in place
    ref_path = ROOT / "reference" / "models.tsv"
    lines = ref_path.read_text(encoding="utf-8").splitlines()
    by_code = {r["code"]: r for r in rows}
    updated, artwork = 0, []
    out = []
    for line in lines:
        if line.startswith("#") or not line.strip() or line.startswith("code\t"):
            out.append(line)
            continue
        cells = line.split("\t")
        incoming = by_code.get(cells[0].strip())
        if not incoming:
            out.append(line)
            continue
        cells += [""] * (6 - len(cells))
        for idx, key in ((1, "name"), (2, "base_mm"), (3, "size"), (5, "mmf")):
            if incoming.get(key):
                cells[idx] = incoming[key]
        out.append("\t".join(cells[:6]).rstrip("\t"))
        updated += 1
        if incoming.get("artwork"):
            artwork.append((cells[0].strip(), incoming["artwork"]))

    unknown = [c for c in by_code if c not in
               {l.split("\t")[0].strip() for l in lines if l and not l.startswith("#")}]
    ref_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"merged {updated} row(s) into reference/models.tsv")
    if unknown:
        print(f"  {len(unknown)} code(s) not in models.tsv, skipped: {', '.join(unknown[:5])}")
    if artwork:
        print(f"  downloading {len(artwork)} artwork file(s)")
        cmd_artwork([u for _, u in artwork], codes=[c for c, _ in artwork])
    print("now run: python3 tools/ledger.py scan && python3 tools/ledger.py build")


# Thresholds from the Scylla failure (P2609-12): the two islands that failed
# were 8520 and 1196 px2, while hundreds under ~300 px2 printed fine. Island
# AREA predicts failure; island count does not.
ISLAND_FAIL = 1000
ISLAND_WATCH = 300
# A suction cup this big above the raft goes on the action list. Grounded in the
# record: P2609-15 tore off its supports between cups of 18.9 and 17.2mm3, while
# P2609-22's 8.8mm3 and P2609-23's 9.3mm3 printed and cleaned fine. Raft cells at
# layer 0 are excluded - they have never predicted a failure.
CUP_FLAG_MM3 = 15.0
# 153.36/8520 x 77.76/4320 x 0.03 on the Mars 5 Ultra; used when a plate's own
# properties are missing.
DEFAULT_VOXEL_MM3 = 9.72e-6
# Islands in the raft and support-transition region are reported separately.
# Everything sitting on the raft reads as unconnected there, so the thresholds
# above — derived from mid-print islands — produce false alarms: the Scylla
# reprint showed seven islands over 29,000px2 at layer 100 and none of them is
# comparable to the 8,520px2 mid-print island that actually failed.
BASE_LAYERS = 150
ISSUE_LINE = re.compile(
    r"(\w+), ([\d-]+)(?:\s+\(\d+\))?, (\d+)px[\u00b2\u00b3], \{X=(\d+),Y=(\d+)")


def voxel_mm3(props, layer_height=0.03):
    """mm3 per pixel-layer, from the plate's own resolution and display size."""
    def num(key):
        m = re.search(rf"^{key}:\s*([\d.]+)", props or "", re.MULTILINE)
        return float(m.group(1)) if m else None
    w, h, rx, ry = num("DisplayWidth"), num("DisplayHeight"), num("ResolutionX"), num("ResolutionY")
    lh = num("LayerHeight") or layer_height
    if w and h and rx and ry and lh:
        return (w / rx) * (h / ry) * lh
    return DEFAULT_VOXEL_MM3


def verdict_path(plate_id):
    return FORENSICS / plate_id / "verdict.tsv"


def write_verdict(plate_id, name, islands, cups, props, layer_height=0.03):
    """Persist a screen verdict so status and backlog.html can surface it.

    The verdict used to live only in the terminal, which meant a flagged plate
    was only as durable as the message it appeared in.
    """
    vox = voxel_mm3(props, layer_height)
    body = [r for r in islands if r[1] >= BASE_LAYERS]
    fix = [r for r in body if r[2] >= ISLAND_FAIL]
    watch = [r for r in body if ISLAND_WATCH <= r[2] < ISLAND_FAIL]
    big_cups = [r for r in cups if r[1] > 0 and r[2] * vox >= CUP_FLAG_MM3]
    level = "fix" if (fix or big_cups) else "watch" if watch else "clear"

    def isl(rows):
        return ";".join(f"{r[2]}px2@{r[1] * layer_height:.2f}mm" for r in rows[:6])

    def cup(rows):
        return ";".join(f"{r[2] * vox:.1f}mm3@{r[1] * layer_height:.2f}mm" for r in rows[:6])

    fields = [("plate", plate_id), ("file", name),
              ("screened", datetime.date.today().isoformat()), ("level", level),
              ("islands_fix", isl(fix)), ("islands_watch", isl(watch)),
              ("cups_flagged", cup(big_cups)), ("cups_largest", cup(cups[:3])),
              ("resolved", ""), ("resolution", "")]
    path = verdict_path(plate_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{k}\t{v}" for k, v in fields) + "\n", encoding="utf-8")
    return level


def read_verdicts():
    """Every archived screen verdict, oldest plate first."""
    out = []
    for path in sorted(FORENSICS.glob("*/verdict.tsv")) if FORENSICS.exists() else []:
        rec = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("\t")
            if k.strip():
                rec[k.strip()] = v.strip()
        rec.setdefault("plate", path.parent.name)
        out.append(rec)
    return out


def flagged_plates():
    """Verdicts that asked for action and have not been acknowledged."""
    return [v for v in read_verdicts()
            if v.get("level") in ("fix", "watch") and not v.get("resolved")]


def flag_detail(v, limit=3):
    """The worst few entries, worst first. The full lists stay in verdict.tsv.

    Printing every island turns the queue into a wall of numbers, which is the
    same way a warning gets lost that this list exists to prevent.
    """
    items = []
    for field in ("islands_fix", "cups_flagged", "islands_watch"):
        items += [b for b in (v.get(field) or "").split(";") if b]
    shown = "; ".join(items[:limit])
    return f"{shown} (+{len(items) - limit} more)" if len(items) > limit else shown


def print_flagged():
    """Lead `status` with anything screening flagged, so it cannot be missed."""
    flags = flagged_plates()
    if not flags:
        return
    fix = [v for v in flags if v.get("level") == "fix"]
    watch = [v for v in flags if v.get("level") == "watch"]
    bar = "!" * 78
    print(bar)
    print(f"PLATES FLAGGED BY SCREENING — {len(fix)} to act on, {len(watch)} to look at")
    for v in fix + watch:
        mark = "FIX " if v.get("level") == "fix" else "look"
        print(f"  {mark}  {v['plate']:<11} {flag_detail(v)}")
        if v.get("file"):
            print(f"        {v['file']}")
    print('  clear one with: python3 tools/ledger.py inspected <plate> "what you found"')
    print(bar)


def cmd_inspected(plate_id, note=None):
    """Acknowledge a screen flag: record what was found and drop it off the list."""
    path = verdict_path(plate_id)
    if not path.exists():
        print(f"no screen verdict archived for {plate_id}")
        return
    rec, order = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("\t")
        if k.strip():
            rec[k.strip()] = v.strip()
            order.append(k.strip())
    if rec.get("resolved"):
        print(f"{plate_id} was already cleared on {rec['resolved']}: {rec.get('resolution', '')}")
        return
    rec["resolved"] = datetime.date.today().isoformat()
    rec["resolution"] = note or "inspected, nothing to report"
    path.write_text("\n".join(f"{k}\t{rec.get(k, '')}" for k in order) + "\n",
                    encoding="utf-8")

    preamble, plates, sections, base_stock = parse_ledger()
    for p in plates:
        if p.get("ID") == plate_id:
            add = f"Screen flag inspected {rec['resolved']}: {rec['resolution']}"
            p["Notes"] = f"{p['Notes'].rstrip().rstrip('.')}. {add}" if p.get("Notes") else add
            write_ledger(preamble, plates, sections, base_stock)
            break
    else:
        print(f"note: no plate row {plate_id} in PRINTS.md, verdict cleared anyway")
    print(f"{plate_id} cleared: {rec['resolution']}")
    print("run: python3 tools/ledger.py build")


def archive_forensics(plate_id, name, rows, props, preview_src, layer_height=0.03):
    """Keep the analysis of a print, not the print file.

    A .goo is 100-360 MB and gets deleted off the printer; the analysis is about
    125 KB and is what forensics actually needs. Archiving it at slice time means
    a failure can still be investigated months later, which is not true today —
    the Sarglagon Arm R flat spot cannot be diagnosed because its file is gone.
    """
    out = FORENSICS / plate_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "slicer-file.txt").write_text(name + "\n", encoding="utf-8")
    (out / "issues.txt").write_text(
        "\n".join(f"{k},{lay},{a},{x},{y}" for k, lay, a, x, y in rows) + "\n",
        encoding="ascii")
    if props:
        (out / "properties.txt").write_text(props, encoding="utf-8", errors="replace")
    if preview_src and Path(preview_src).exists():
        import shutil
        shutil.copyfile(preview_src, out / "preview.png")

    islands = sorted([r for r in rows if r[0] == "Island"], key=lambda r: -r[2])
    body = [r for r in islands if r[1] >= BASE_LAYERS]
    cups = sorted([r for r in rows if r[0] == "SuctionCup"], key=lambda r: -r[2])
    lines = [f"# {plate_id}", "", f"file: {name}", "",
             f"islands: {len(islands)} ({len(body)} above layer {BASE_LAYERS})",
             f"suction cups: {len(cups)}",
             f"resin traps: {sum(1 for r in rows if r[0] == 'ResinTrap')}", ""]
    if body:
        lines.append("largest islands above the base region:")
        for r in body[:10]:
            lines.append(f"  layer {r[1]:>5} = {r[1]*layer_height:6.2f} mm  {r[2]:>8} px2  "
                         f"X={r[3]} Y={r[4]}")
    if cups:
        lines.append("")
        lines.append("largest suction cups:")
        for r in cups[:6]:
            lines.append(f"  from layer {r[1]:>5} = {r[1]*layer_height:6.2f} mm  {r[2]:>10} px3  "
                         f"X={r[3]} Y={r[4]}")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    level = write_verdict(plate_id, name, islands, cups, props, layer_height)
    if level != "clear":
        print(f"\nflagged {plate_id} as {level.upper()} — it will stay at the top of `status` until\n  you run: python3 tools/ledger.py inspected {plate_id} \"what you found\"")
    size = sum(f.stat().st_size for f in out.iterdir())
    print(f"\narchived to forensics/{plate_id}/ ({size // 1024} KB)")


def cmd_screen(source, plate_id=None, layer_height=0.03):
    """Run UVtools island detection on a sliced file and give a verdict.

    Worth doing on 50mm and 75mm models before starting a long print: every
    print failure so far has been on one, and none on a 25mm model. Costs a
    full download plus about five minutes, against hours on the plate.
    """
    import sliced, subprocess, tempfile
    if not sliced.uvtools_available():
        print("needs UVtools in ./uvtools")
        return
    name = source.rsplit("/", 1)[-1]
    local = Path(source)
    tmp = None
    if source.startswith("http") or not local.exists():
        url = source if source.startswith("http") else PRINTER_URL + urllib.parse.quote(name)
        tmp = tempfile.NamedTemporaryFile(suffix=Path(name).suffix, delete=False)
        print(f"downloading {name} ...")
        sliced.download(url, tmp.name)
        local = Path(tmp.name)

    print("detecting issues (several minutes) ...")
    proc = subprocess.run([str(sliced.UVTOOLS), "--no-progress", "print-issues", str(local)],
                          capture_output=True, text=True, timeout=3600)
    props = ""
    preview_tmp = None
    if plate_id:
        props = subprocess.run(
            [str(sliced.UVTOOLS), "--no-progress", "print-properties", str(local),
             "--partial-mode"], capture_output=True, text=True, timeout=600).stdout
        preview_tmp = str(Path(tempfile.gettempdir()) / f"{plate_id}-preview.png")
        try:
            if name.lower().endswith(".goo"):
                import preview as preview_mod
                preview_mod.extract(local.read_bytes()[:sliced.GOO_HEADER_BYTES],
                                    preview_tmp, "big")
            else:
                sliced.uvtools_thumbnail(str(local), preview_tmp)
        except Exception:
            preview_tmp = None
    rows = []
    for line in proc.stdout.splitlines():
        m = ISSUE_LINE.match(line.strip())
        if m:
            kind, lay, area, x, y = m.groups()
            rows.append((kind, int(lay.split("-")[0]), int(area), int(x), int(y)))
    if plate_id and rows:
        archive_forensics(plate_id, name, rows, props, preview_tmp, layer_height)
    if tmp:
        Path(tmp.name).unlink(missing_ok=True)
    if not rows:
        print("no issues parsed — UVtools may have failed; check the file")
        return

    islands = sorted([r for r in rows if r[0] == "Island"], key=lambda r: -r[2])
    cups = sorted([r for r in rows if r[0] == "SuctionCup"], key=lambda r: -r[2])
    traps = [r for r in rows if r[0] == "ResinTrap"]
    print(f"\n{len(islands)} islands, {len(cups)} suction cups, {len(traps)} resin traps\n")

    base = [r for r in islands if r[1] < BASE_LAYERS]
    body = [r for r in islands if r[1] >= BASE_LAYERS]
    bad = [r for r in body if r[2] >= ISLAND_FAIL]
    watch = [r for r in body if ISLAND_WATCH <= r[2] < ISLAND_FAIL]
    if base:
        big = max(r[2] for r in base)
        print(f"  {len(base)} island(s) below layer {BASE_LAYERS} (raft and support transition), "
              f"largest {big:,} px2 — not counted in the verdict; check these by eye in the slicer")
    if body:
        print("  largest islands above the base region:")
        for r in body[:8]:
            flag = ("  <-- FIX" if r[2] >= ISLAND_FAIL
                    else "  <-- watch" if r[2] >= ISLAND_WATCH else "")
            print(f"    layer {r[1]:>5} = {r[1]*layer_height:>6.2f} mm  {r[2]:>7} px2{flag}")
    if cups:
        print("\n  largest suction cups:")
        for r in cups[:4]:
            print(f"    from layer {r[1]:>5} = {r[1]*layer_height:>6.2f} mm  {r[2]:>9} px3")

    print()
    if bad:
        print(f"VERDICT: {len(bad)} island(s) at or above {ISLAND_FAIL}px2 — expect defects at "
              f"{', '.join(f'{r[1]*layer_height:.2f}mm' for r in bad)}.")
        print("         Add supports there before printing.")
    elif watch:
        print(f"VERDICT: nothing above {ISLAND_FAIL}px2, but {len(watch)} island(s) over "
              f"{ISLAND_WATCH}px2 worth a look.")
    else:
        print(f"VERDICT: no island above {ISLAND_WATCH}px2. Nothing here predicts a failure.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "scan":
        seed = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_scan(seed)
    elif cmd == "build":
        cmd_build()
    elif cmd == "status":
        cmd_status()
    elif cmd == "assign":
        if len(sys.argv) < 5:
            print("usage: ledger.py assign <plate-id|-> <stage> <model-or-release>...")
            sys.exit(2)
        cmd_assign(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif cmd == "preview":
        if len(sys.argv) < 3:
            print("usage: ledger.py preview <file|url|printer-filename> [out.png] [small|big]")
            sys.exit(2)
        cmd_preview(sys.argv[2],
                    sys.argv[3] if len(sys.argv) > 3 else None,
                    sys.argv[4] if len(sys.argv) > 4 else "big")
    elif cmd == "merge-reference":
        cmd_merge_reference(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "photo":
        if len(sys.argv) < 5:
            print("usage: ledger.py photo <code> printed|painted <file>")
            sys.exit(2)
        cmd_photo(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "artwork":
        if len(sys.argv) < 3:
            print("usage: ledger.py artwork <url>...")
            sys.exit(2)
        cmd_artwork(sys.argv[2:])
    elif cmd == "screen":
        if len(sys.argv) < 3:
            print("usage: ledger.py screen <file|printer-filename>")
            sys.exit(2)
        cmd_screen(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "inspected":
        if len(sys.argv) < 3:
            print('usage: ledger.py inspected <plate-id> ["what you found"]')
            sys.exit(2)
        cmd_inspected(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "runlog":
        cmd_runlog()
    elif cmd == "printer":
        cmd_printer()
    elif cmd == "plate":
        if len(sys.argv) < 3:
            print("usage: ledger.py plate <file|url|printer-filename> [plate-id]")
            sys.exit(2)
        cmd_plate(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
    else:
        print(f"unknown command: {cmd}\n")
        print(__doc__)
        sys.exit(2)
