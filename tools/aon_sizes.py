#!/usr/bin/env python3
"""Cross-check base sizes in reference/models.tsv against Logan's Archives of
Nethys export (lacunafex.sqlite), by creature name.

The export keeps each creature's size class in its `traits` column
("Animal, Large"). This maps Tiny/Small/Medium -> 25, Large -> 50, Huge -> 75,
Gargantuan -> 100 and compares with the stated base. It is a read-only
cross-check: it never edits models.tsv. Rows that disagree are printed as
FLAGGED for Logan to rule on; per his rule, no stated size means 25 mm unless
the model is obviously Large or Huge.

    python3 tools/aon_sizes.py                   # every model, writes reference/aon-sizes.tsv
    python3 tools/aon_sizes.py --release 202610  # only models under directories with that prefix
    python3 tools/aon_sizes.py --blank           # only rows whose base_mm is unstated
    python3 tools/aon_sizes.py P0101 P0102       # specific codes
    python3 tools/aon_sizes.py --db /path/to/lacunafex.sqlite

The database is found from $AON_DB, then the ledger machine's path, then the
browser agent's mount. Read-only, immutable open: safe while the exporter is
rebuilding it.
"""
import os, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "reference" / "models.tsv"
OUT = ROOT / "reference" / "aon-sizes.tsv"
DB_CANDIDATES = [
    os.environ.get("AON_DB"),
    "/Users/lcb/work/archives-of-nethys-viewer-ios/AoNDataExporter/lacunafex.sqlite",
    str(Path.home() / "mnt" / "AoNDataExporter" / "lacunafex.sqlite"),
]
SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
BASE_OF = {"Tiny": 25, "Small": 25, "Medium": 25, "Large": 50, "Huge": 75, "Gargantuan": 100}

# Sheet name -> the name AoN uses. Add to this when a new release's name
# does not match; a wrong match is worse than none.
ALIAS = {
    "Ort (Druge Devil)": "Druge", "Vordine (Infantry Devil)": "Vordine",
    "Sarglagon (Drowning Devil)": "Sarglagon", "Gylou (Handmaiden Devil)": "Gylou",
    "Phistophilus (Contract Devil)": "Phistophilus", "Nessari (Tyrant Devil)": "Nessari",
    "Vidileth Alghollthu": "Vidileth", "Zolgran, Kobold Boss": "Zolgran",
    "Hellknight Chargers": "Hellknight", "Goblin Chanter": "Goblin War Chanter",
    "Lem, Iconic Bard": "",   # a bare "Lem" matches "Golem"; iconics have no creature entry
    "Twilight Talon": "",     # only hit is a Gargantuan troop; the mini is one agent
}

# Stated bases Logan has confirmed even though the AoN size class disagrees.
# code -> reason. These print as "accepted", never FLAGGED.
ACCEPTED = {
    "P0025": "base sheet lists the WP1 Horned Dragon as Medium (Logan, 2026-09-11)",
}


def find_db(explicit=None):
    for p in ([explicit] if explicit else []) + DB_CANDIDATES:
        if p and Path(p).exists():
            return p
    sys.exit("lacunafex.sqlite not found — pass --db or set AON_DB")


def load_models():
    rows = []
    for line in MODELS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("code\t"):
            continue
        cells = line.split("\t") + [""] * 6
        rows.append({"code": cells[0].strip(), "name": cells[1].strip(), "base": cells[2].strip()})
    return rows


def search_key(name):
    if name in ALIAS:
        return ALIAS[name]
    if "Iconic" in name:
        return name.split(",")[0]
    return re.sub(r"\s*\(.*?\)", "", name).strip()


def lookup(con, key):
    if not key:
        return []
    for pat in (key, key + "%", "%" + key + "%"):
        rows = con.execute(
            "select name, traits, level, primarySource from documents "
            "where category='creature' and name like ? collate nocase "
            "order by length(name) limit 4", (pat,)).fetchall()
        if rows:
            return rows
    return []


def release_dirs(prefix):
    dirs = set()
    for rel in ROOT.iterdir():
        if rel.is_dir() and rel.name.startswith(prefix):
            for d in rel.iterdir():
                if d.is_dir():
                    dirs.add(d.name)
    return dirs


def main(argv):
    db = None; release = None; blank = False; codes = []; write = True
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--db": db = argv[i + 1]; i += 2
        elif a == "--release": release = argv[i + 1]; i += 2
        elif a == "--blank": blank = True; i += 1
        elif a == "--no-write": write = False; i += 1
        else: codes.append(a); i += 1

    con = sqlite3.connect(f"file:{find_db(db)}?mode=ro&immutable=1", uri=True)
    models = load_models()
    if release:
        dirs = release_dirs(release)
        pnums = {m.group(0) for d in dirs for m in [re.search(r"P\d{4}", d)] if m}
        models = [m for m in models if m["code"] in pnums or m["code"] in dirs]
        if not models:
            sys.exit(f"no models.tsv rows for release {release}: add them first (see CLAUDE.md)")
    if blank:
        models = [m for m in models if not m["base"]]
    if codes:
        models = [m for m in models if m["code"] in codes]

    out, flagged, matched = [], [], 0
    for m in models:
        hits = lookup(con, search_key(m["name"]))
        sizes = sorted({s for r in hits for s in SIZES if s in (r[1] or "").split(", ")}, key=SIZES.index)
        suggested = "/".join(str(BASE_OF[s]) for s in sizes)
        if hits: matched += 1
        flag = ""
        if m["base"] and suggested and m["base"] not in suggested.split("/"):
            if m["code"] in ACCEPTED:
                flag = "accepted: " + ACCEPTED[m["code"]]
            else:
                flag = "FLAGGED"; flagged.append(m)
        elif not m["base"] and suggested:
            flag = "unstated"
        detail = "; ".join(f"{r[0]} [{r[1]}] L{r[2]} ({r[3]})" for r in hits[:3])
        out.append([m["code"], m["name"], m["base"], suggested, flag, detail])

    if write and not (codes or release or blank):
        with OUT.open("w", encoding="utf-8") as f:
            f.write("# Size classes from the Archives of Nethys export, matched by creature name (tools/aon_sizes.py).\n")
            f.write("# Read-only cross-check; models.tsv stays the source of truth. base_suggested: Tiny/Small/Medium=25, Large=50, Huge=75, Gargantuan=100.\n")
            f.write("code\tname\tbase_stated\tbase_suggested\tflag\taon_matches\n")
            for r in out: f.write("\t".join(r) + "\n")

    for r in out:
        print("\t".join(r[:5]))
    print(f"\n{matched} of {len(out)} matched a creature entry", end="")
    print(f"; wrote {OUT.relative_to(ROOT)}" if write and not (codes or release or blank) else "")
    if flagged:
        print(f"{len(flagged)} FLAGGED — stated base disagrees with the size class; for Logan to rule on:")
        for m in flagged: print(f"  {m['code']} {m['name']}: stated {m['base']}")
    unstated = [r for r in out if r[4] == "unstated"]
    if unstated:
        print(f"{len(unstated)} unstated with an AoN size — suggested values above; state them in models.tsv via merge-reference")


if __name__ == "__main__":
    main(sys.argv[1:])
