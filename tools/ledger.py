#!/usr/bin/env python3
"""Print tracker for the Paizo minis collection.

PRINTS.md is the source of truth and is meant to be read and edited by hand
(or by Claude in chat). This tool only ever does two things to it:

  scan   discover printable parts on disk and add rows for anything new,
         never touching the Stage/Plate/Result/Notes you have recorded
  build  render dashboard.html from PRINTS.md

Model/Mini/Base columns are derived from reference/models.tsv and are
refreshed on every scan, so don't hand-edit those.
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
REFERENCE = ROOT / "reference" / "models.tsv"

# Directories that hold no miniatures.
SKIP_DIRS = {".git", "bases", "V3_Cones_of_Calibration", "nord_autosave", "tools",
             "reference", "uvtools", "plates"}

# Ordered by how far along a part is. "reprint" ranks below "printed" on
# purpose: Brian rejected it, so it has to go back on a plate and should show up
# in the print queue again.
STAGES = ["todo", "reprint", "sliced", "printed", "cleaned", "cured",
          "review", "primed", "painted", "delivered"]
DONE_STAGE = "printed"     # counts as "off the printer"
REVIEW_STAGE = "review"    # cleaned and cured, waiting on Brian
REPRINT_STAGE = "reprint"  # Brian rejected it

COLUMNS = ["Model", "Mini", "Base", "Part", "Stage", "Plate", "Result", "Notes"]
PLATE_COLUMNS = ["ID", "Date", "Slicer file", "Resin", "Layer", "Exposure",
                 "Bottom exp", "Bottom layers", "Lift", "Result", "Notes"]
# Filled in from the sliced file by `plate`; the rest are yours to fill in.
PLATE_AUTO = ("Date", "Slicer file", "Layer", "Exposure", "Bottom exp", "Bottom layers")

PRINTER_URL = "http://192.168.1.151:3030/media/mmcblk0p3/"

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
        ref[code] = {"name": name, "base_mm": base_mm, "size": size, "pack": pack}
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
        base_mm = (meta or {}).get("base_mm") or on_disk_base
        mini = (meta or {}).get("name") or model

        bucket = found.setdefault(release, OrderedDict())
        for entry in entries:
            bucket[(model, entry["part"])] = {
                "model": model,
                "part": entry["part"],
                "mini": mini,
                "base": f"{base_mm}mm" if base_mm else "?",
                "size": (meta or {}).get("size", ""),
                "dir": str(dirpath),
                "file": entry["file"],
                "presupported": entry["presupported"],
                "disk_base": on_disk_base,
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
    if not LEDGER.exists():
        return preamble, plates, sections

    section = None
    in_preamble = True
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_preamble = False
            section = line[3:].strip()
            if section != "Plates":
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
        if not cells or cells[0] in ("Model", "ID") or set("".join(cells)) <= set("-: "):
            continue
        if section == "Plates":
            cells += [""] * (len(PLATE_COLUMNS) - len(cells))
            plates.append(dict(zip(PLATE_COLUMNS, cells[:len(PLATE_COLUMNS)])))
        elif section:
            cells += [""] * (len(COLUMNS) - len(cells))
            row = dict(zip(COLUMNS, cells[:len(COLUMNS)]))
            sections[section][(row["Model"], row["Part"])] = row
    while preamble and not preamble[0].strip():
        preamble.pop(0)
    while preamble and not preamble[-1].strip():
        preamble.pop()
    return preamble, plates, sections


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


def write_ledger(preamble, plates, sections):
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))
    lines = ["# Paizo Minis — Print Tracker", ""]
    lines += preamble or DEFAULT_PREAMBLE
    lines += ["", "## Plates", ""]
    lines += render_table(PLATE_COLUMNS,
                          sorted(plates, key=lambda p: (p.get("Date", ""), p.get("ID", ""))))
    for name, rows in sections.items():
        lines += ["", f"## {name}", ""]
        lines += render_table(COLUMNS, rows.values())
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_scan(seed_printed_before=None):
    ref = load_reference()
    disk = scan_disk(ref)
    preamble, plates, sections = parse_ledger()

    added = 0
    missing = []
    for release, parts in disk.items():
        section = sections.setdefault(release, OrderedDict())
        for key, info in parts.items():
            if key in section:
                row = section[key]
            else:
                stage = "todo"
                if seed_printed_before and release < seed_printed_before:
                    stage = DONE_STAGE
                row = {"Model": info["model"], "Part": info["part"], "Stage": stage,
                       "Plate": "", "Result": "pass" if stage != "todo" else "", "Notes": ""}
                section[key] = row
                added += 1
            # derived columns, always refreshed
            row["Mini"] = info["mini"]
            row["Base"] = info["base"]
        # keep sections ordered the way disk order presents them
        sections[release] = OrderedDict(
            sorted(section.items(), key=lambda kv: (kv[0][0], kv[0][1]))
        )

    for release, rows in sections.items():
        for key in rows:
            if key not in disk.get(release, {}):
                missing.append(f"{release}/{key[0]} [{key[1]}]")

    write_ledger(preamble, plates, sections)

    total = sum(len(v) for v in sections.values())
    print(f"scan: {total} parts tracked across {len(sections)} releases ({added} new)")
    if missing:
        print(f"warning: {len(missing)} ledger rows have no matching file on disk:")
        for m in missing:
            print(f"  {m}")


# --------------------------------------------------------------------------
# status


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
    for (model, part), r in rows.items():
        if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE):
            continue
        if r["Stage"] == REPRINT_STAGE:
            # It printed once, so its base already exists; only the mini needs
            # running again.
            continue
        pending.setdefault((model, r.get("Base", "?")), set()).add(variant_of(part))
    out = Counter()
    for (model, base), variants in pending.items():
        named = {v for v in variants if v}
        out[base] += len(named) if named else 1
    return out


def stage_rank(stage):
    try:
        return STAGES.index(stage)
    except ValueError:
        return 0


def cmd_status():
    _, plates, sections = parse_ledger()
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))
    ref = load_reference()
    disk = scan_disk(ref)
    grand = Counter()
    print(f"{'Release':<32} {'done':>5} {'/':^1} {'all':<5}  bases still to print")
    print("-" * 78)
    for release, rows in sections.items():
        done = sum(1 for r in rows.values() if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
        bases = bases_needed(rows)
        grand["done"] += done
        grand["all"] += len(rows)
        base_txt = ", ".join(f"{n}x {b}" for b, n in sorted(bases.items())) or "-"
        print(f"{release:<32} {done:>5} / {len(rows):<5}  {base_txt}")
    print("-" * 78)
    print(f"{'TOTAL':<32} {grand['done']:>5} / {grand['all']:<5}")
    for label, stage in (("Awaiting Brian's review", REVIEW_STAGE),
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
"""


def cmd_build():
    ref = load_reference()
    disk = scan_disk(ref)
    _, plates, sections = parse_ledger()
    sections = OrderedDict(sorted(sections.items(),
                                  key=lambda kv: release_sort_key(kv[0])))

    total = sum(len(r) for r in sections.values())
    done = sum(1 for rows in sections.values() for r in rows.values()
               if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
    fails = sum(1 for rows in sections.values() for r in rows.values()
                if r.get("Result") == "fail")
    in_review = sum(1 for rows in sections.values() for r in rows.values()
                    if r["Stage"] == REVIEW_STAGE)
    to_reprint = sum(1 for rows in sections.values() for r in rows.values()
                     if r["Stage"] == REPRINT_STAGE)
    remaining_bases = Counter()
    for rows in sections.values():
        remaining_bases.update(bases_needed(rows))

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
           '<div class="totals">',
           f'<div class="stat"><b>{done}/{total}</b><span>parts printed</span></div>',
           f'<div class="stat"><b>{total - done}</b><span>remaining</span></div>',
           f'<div class="stat"><b>{in_review}</b><span>awaiting Brian</span></div>',
           f'<div class="stat"><b>{to_reprint}</b><span>to reprint</span></div>',
           f'<div class="stat"><b>{fails}</b><span>failures</span></div>']
    for base, n in sorted(remaining_bases.items()):
        out.append(f'<div class="stat"><b>{n}</b><span>{e(base)} bases left</span></div>')
    out.append("</div>")

    for release, rows in sections.items():
        r_done = sum(1 for r in rows.values()
                     if stage_rank(r["Stage"]) >= stage_rank(DONE_STAGE))
        pct = round(100 * r_done / len(rows)) if rows else 0
        bases = bases_needed(rows)
        out.append("<section>")
        out.append(f'<div class="rel"><h2>{e(release)}</h2>'
                   f'<span class="count">{r_done} of {len(rows)} parts · {pct}%</span></div>')
        out.append(f'<div class="bar"><i style="width:{pct}%"></i></div>')
        if bases:
            txt = " · ".join(f"<b>{n}</b>&times; {e(b)}" for b, n in sorted(bases.items()))
            out.append(f'<div class="bases">Bases still needed: {txt}</div>')

        # group parts by model
        models = OrderedDict()
        for (model, part), row in rows.items():
            models.setdefault(model, []).append(row)

        out.append('<div class="grid">')
        for model, parts in models.items():
            info = next((disk[release][(model, p["Part"])] for p in parts
                         if (model, p["Part"]) in disk.get(release, {})), None)
            mini = parts[0].get("Mini") or model
            base = parts[0].get("Base", "")
            thumb = ""
            if info:
                jpgs = sorted(Path(ROOT / info["dir"]).glob("Release_*.jpg"))
                if jpgs:
                    # Percent-encode: these paths contain spaces, which are fine
                    # over file:// but not valid in an HTTP request path.
                    src = urllib.parse.quote(jpgs[0].relative_to(ROOT).as_posix())
                    thumb = f'<img src="{e(src)}" alt="" loading="lazy">'
            chips = []
            for p in sorted(parts, key=lambda r: r["Part"]):
                cls = "part"
                if p["Stage"] == REPRINT_STAGE:
                    cls += " reprint"
                elif p["Stage"] == REVIEW_STAGE:
                    cls += " review"
                elif p.get("Result") == "fail":
                    cls += " fail"
                elif stage_rank(p["Stage"]) >= stage_rank(DONE_STAGE):
                    cls += " done"
                d = disk.get(release, {}).get((model, p["Part"]))
                # No pre-supported file means supports have to be added in the slicer.
                warn = "" if (d is None or d["presupported"]) else " ⚠"
                label = f'{e(p["Part"])} · {e(p["Stage"])}{warn}'
                title = " ".join(x for x in [p.get("Plate", ""), p.get("Notes", ""),
                                             "needs supports" if warn else ""] if x)
                chips.append(f'<span class="{cls}" title="{e(title)}">{label}</span>')
            out.append(
                f'<div class="card">{thumb}<div class="body">'
                f'<div class="name">{e(mini)}<span class="badge">{e(base)}</span></div>'
                f'<div class="code">{e(model)}</div>'
                f'<div class="parts">{"".join(chips)}</div></div></div>')
        out.append("</div></section>")

    if plates:
        out.append("<section><h2>Plates</h2>")
        out.append('<div class="tablewrap"><table><thead><tr><th>Plate</th>'
                   + "".join(f"<th>{e(c)}</th>" for c in PLATE_COLUMNS)
                   + "</tr></thead><tbody>")
        for p in sorted(plates, key=lambda r: (r.get("Date", ""), r.get("ID", ""))):
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

    preamble, plates, sections = parse_ledger()
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
    write_ledger(preamble, plates, sections)
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
        ledger.py assign - printed Dragons
    """
    if stage not in STAGES:
        print(f"unknown stage {stage!r}; expected one of: {', '.join(STAGES)}")
        return
    preamble, plates, sections = parse_ledger()
    if plate != "-" and not any(p["ID"] == plate for p in plates):
        print(f"no plate {plate!r} in the Plates table")
        return

    changed = []
    for release, rows in sections.items():
        for (model, part), row in rows.items():
            hit = any(t.lower() in release.lower() or t.lower() in model.lower()
                      for t in targets)
            if not hit:
                continue
            row["Stage"] = stage
            if plate != "-":
                row["Plate"] = plate
            changed.append(f"{model} [{part}]")
    if not changed:
        print(f"nothing matched {targets}")
        return
    write_ledger(preamble, plates, sections)
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
    if not name.lower().endswith(".goo") and not sliced.uvtools_available():
        print("ctb previews need UVtools in ./uvtools; only .goo works without it")
        return
    out_path = out_path or re.sub(r"[^\w.-]", "_", name)[:60] + ".png"
    try:
        head = __import__("sliced").fetch_head(source, __import__("sliced").GOO_HEADER_BYTES)
        print("wrote", preview_mod.extract(head, out_path, which))
    except Exception as exc:
        print(f"could not extract a preview from {name}: {exc}")


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
    elif cmd == "printer":
        cmd_printer()
    elif cmd == "plate":
        if len(sys.argv) < 3:
            print("usage: ledger.py plate <file|url|printer-filename> [plate-id]")
            sys.exit(2)
        cmd_plate(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
        sys.exit(2)
