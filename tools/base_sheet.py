#!/usr/bin/env python3
"""Track the Paizo Printables base-size sheet and turn changes into a handoff.

    https://docs.google.com/spreadsheets/d/136R7lDaQ5BK42xDqrfJR8dN6XYIWq2PyM0_lwJQH2jU

The sheet has one tab per season (GIDS below). Each tab is a CSV with columns
  Miniature Name, Base Size, Mini Size, Release, Release Code, File Name
plus section-heading rows with only the first cell filled. The P-number in
File Name is the key everything else in this repo joins on.

    python3 tools/base_sheet.py fetch                 # download every tab -> reference/base-sheet.csv (needs Google reachable)
    python3 tools/base_sheet.py ingest a.csv [b.csv]  # same, from CSVs someone else downloaded (browser agent / WebFetch)
    python3 tools/base_sheet.py diff                  # snapshot vs models.tsv -> report + reference/incoming.tsv rows

`fetch`/`ingest` keep the previous snapshot as reference/base-sheet.prev.csv
and print what changed between snapshots. `diff` never edits models.tsv: it
writes the differences to reference/incoming.tsv for merge-reference.

Only the browser agent or a session with Google access can fetch; the mini's
shell is proxy-blocked. Chrome on the mini can, once docs.google.com is allowed
in the Claude in Chrome extension.
"""
import csv, io, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
SNAP, PREV, INCOMING = REF / "base-sheet.csv", REF / "base-sheet.prev.csv", REF / "incoming.tsv"
SHEET_ID = "136R7lDaQ5BK42xDqrfJR8dN6XYIWq2PyM0_lwJQH2jU"
# tab name -> gid. Add tabs here as the sheet grows; 0 is the welcome packs.
GIDS = {"welcome-packs": 0, "season-2": 1034510204, "season-1": 1967321255}
PNUM = re.compile(r"P(\d{4})(?!\d)")
FIELDS = ["code", "name", "base_mm", "size", "pack", "release", "file_name", "variants"]


def parse(text):
    """Rows keyed by P-number. Two layouts exist: the welcome-pack tab has a
    separate File Name column; the season tabs put the file name in Release
    Code. So the P-number is taken from whichever cell carries it, and the pack
    (WP1, S2P3, ...) from the token after the last underscore of that cell, or
    from Release Code when that is a bare pack. Names drop the sheet's
    "(3 Models)" annotation, which is kept in `variants` instead. Rows with no
    P-number yet (a month whose names Paizo has not filled in) are skipped."""
    rows = {}
    for r in csv.reader(io.StringIO(text)):
        r = [c.strip() for c in r] + [""] * 6
        if r[0] in ("Miniature Name", "") and not any(PNUM.search(c) for c in r):
            continue
        file_cell = next((c for c in r[:6] if PNUM.search(c)), "")
        if not file_cell:
            continue
        code = "P" + PNUM.search(file_cell).group(1)
        m = re.search(r"_([A-Z]+\d*[A-Z]*\d*)$", file_cell)
        pack = m.group(1) if m else r[4]
        name = r[0]
        v = re.search(r"\s*\((\d+) Models?\)\s*$", name, re.I)
        variants = v.group(1) if v else ""
        name = re.sub(r"\s*\(\d+ Models?\)\s*$", "", name, flags=re.I)
        rows[code] = dict(code=code, name=name, base_mm=re.sub(r"\D", "", r[1]), size=r[2],
                          pack=pack, release=r[3], file_name=file_cell, variants=variants)
    return rows


def read_snapshot(path=SNAP):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return {r["code"]: r for r in csv.DictReader(f)}


def write_snapshot(rows):
    if SNAP.exists():
        PREV.write_text(SNAP.read_text(encoding="utf-8"), encoding="utf-8")
    with SNAP.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for code in sorted(rows): w.writerow(rows[code])


def report_snapshot_change(old, new):
    added = [c for c in new if c not in old]
    removed = [c for c in old if c not in new]
    changed = [c for c in new if c in old and any(new[c][k] != old[c][k] for k in ("name", "base_mm", "size", "pack"))]
    print(f"snapshot: {len(new)} rows; {len(added)} new, {len(changed)} changed, {len(removed)} gone since last time")
    for c in added: print(f"  new      {c} {new[c]['name']} {new[c]['base_mm']}mm {new[c]['size']} {new[c]['pack']}")
    for c in changed:
        diffs = ", ".join(f"{k}: {old[c][k]} -> {new[c][k]}" for k in ("name", "base_mm", "size", "pack") if new[c][k] != old[c][k])
        print(f"  changed  {c} {new[c]['name']}: {diffs}")
    for c in removed: print(f"  gone     {c} {old[c]['name']}")


def cmd_fetch(_):
    rows = {}
    for tab, gid in GIDS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")
        except Exception as exc:
            sys.exit(f"could not fetch tab {tab} (gid {gid}): {exc}\n"
                     "Google is not reachable from here; have the browser agent download the CSVs and run `ingest`.")
        got = parse(text); print(f"{tab}: {len(got)} models")
        rows.update(got)
    old = read_snapshot(); write_snapshot(rows); report_snapshot_change(old, rows)


def cmd_ingest(paths):
    if not paths: sys.exit("usage: ingest <csv> [<csv> ...]")
    rows = {}
    for p in paths:
        got = parse(Path(p).read_text(encoding="utf-8-sig")); print(f"{p}: {len(got)} models"); rows.update(got)
    old = read_snapshot(); write_snapshot(rows); report_snapshot_change(old, rows)


def load_models():
    out = {}
    for line in (REF / "models.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("code\t"): continue
        c = line.split("\t") + [""] * 6
        out[c[0].strip()] = dict(name=c[1].strip(), base_mm=c[2].strip(), size=c[3].strip(), pack=c[4].strip())
    return out


def cmd_diff(_):
    sheet = read_snapshot()
    if not sheet: sys.exit("no snapshot yet: run fetch or ingest first")
    models = load_models()
    new, changed = [], []
    for code, s in sorted(sheet.items()):
        m = models.get(code)
        if not m:
            new.append(s); continue
        d = {k: s[k] for k in ("name", "base_mm", "size", "pack") if s[k] and s[k] != m[k]}
        if d: changed.append((s, d))
    numbered = [c for c in models if re.fullmatch(r"P\d{4}", c)]   # extras packs are keyed by directory name and are not on the sheet
    not_on_sheet = [c for c in numbered if c not in sheet]
    print(f"sheet {len(sheet)} models, models.tsv {len(numbered)} numbered")
    for s in new: print(f"  NEW on sheet, not in models.tsv: {s['code']} {s['name']} {s['base_mm']}mm {s['size']} {s['pack']}")
    for s, d in changed: print(f"  CHANGED {s['code']} {s['name']}: " + ", ".join(f"{k} {models[s['code']][k]!r} -> {s[k]!r}" for k in d))
    if not_on_sheet: print(f"  in models.tsv but not on the sheet — names/codes not filled in there yet, or a tab missing from GIDS: {', '.join(not_on_sheet)}")
    if not new and not changed:
        print("models.tsv matches the sheet; nothing to hand off"); return
    target = INCOMING
    try:
        f = INCOMING.open("w", encoding="utf-8")
    except OSError:                      # browser side with stale handles: leave a .tmp beside it
        target = INCOMING.with_name(INCOMING.name + ".tmp"); f = target.open("w", encoding="utf-8")
    with f:
        f.write("# from tools/base_sheet.py diff — sheet rows new or changed vs models.tsv. merge-reference applies matched codes;\n")
        f.write("# NEW codes are reported as unknown by merge-reference: add them to models.tsv first (see CLAUDE.md), then re-run.\n")
        f.write("code\tname\tbase_mm\tsize\tpack\n")
        for s in new: f.write("\t".join([s["code"], s["name"], s["base_mm"], s["size"], s["pack"]]) + "\n")
        for s, d in changed: f.write("\t".join([s["code"], d.get("name", ""), d.get("base_mm", ""), d.get("size", ""), d.get("pack", "")]) + "\n")
    print(f"wrote {len(new) + len(changed)} row(s) to {target.relative_to(ROOT)}")
    if target != INCOMING: print("  (could not open incoming.tsv for writing; mv the .tmp over it from a shell that can)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "diff"
    {"fetch": cmd_fetch, "ingest": cmd_ingest, "diff": cmd_diff}.get(cmd, lambda a: sys.exit(__doc__))(sys.argv[2:])
