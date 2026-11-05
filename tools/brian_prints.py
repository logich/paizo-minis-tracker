#!/usr/bin/env python3
"""Watch Brian's painted prints on MyMiniFactory and spot new postings.

    https://www.myminifactory.com/users/briansouvey

Brian posts photographs of the minis he has painted to his MyMiniFactory
profile's Prints tab. They are the source of the `_painted.jpg` photographs in
gallery/. Watching that page is the browser agent's job.

**Each print names the object it was printed from, so nothing here is guessed.**
A print lives at /prints/<print_id>, and that page carries a `<!-- Print Info -->`
block holding a JSON payload (`data-component-name="CanvasInfoBlockPage"`) with
the print's title and `date_created`, plus a link to the source object:

    /object/3d-print-fire-serpent-768531

The trailing number is the MyMiniFactory object id, which is already the tail of
the `mmf` column in reference/models.tsv - so the object id joins a photograph to
a code exactly. Do NOT match on his title: he types them by hand and they carry
typos and variants ("Phistophilus Drvil", "Ort's", "Sarglagon - drowned Devil").
The object id matched all 12 of his existing prints to the right code, and the
result was exactly the 12 codes already filed in gallery/ (verified 2026-11-03).

The profile grid is no help on its own: its cards link to a dead
/object/3d-print-0 and read "Untitled Object". The real links are `/prints/<id>`
anchors on the same page, and the print pages are same-origin, so one tab can
fetch all of them without navigating.

Neither shell can fetch anything from the MyMiniFactory CDN - Cloudflare answers
403 to non-browsers, from the mini and the cloud container alike - so the browser
agent scrapes in Chrome and feeds the result in here:

    python3 tools/brian_prints.py diff   scraped.tsv   # report only, change nothing
    python3 tools/brian_prints.py ingest scraped.tsv   # report, then update the snapshot
    python3 tools/brian_prints.py list                 # show the snapshot

scraped.tsv is what Chrome collected, one print per line, no header:

    <print_id>\t<his title>\t<date_created>\t<object path or url>\t<asset path>

where <asset path> is the part after /images/ in the photo's URL,
e.g. 6adf86694cbfa/IMG-5122.6adf86694d83a.jpeg

The snapshot is reference/brian-prints.tsv. Whether a photograph has been filed
is NOT stored - it is read from gallery/ each run, so the snapshot cannot drift
out of step with what is actually on disk. Filing is still done by hand:

    python3 tools/ledger.py photo <code> painted <file>
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
SNAP = REF / "brian-prints.tsv"
PREV = REF / "brian-prints.prev.tsv"
MODELS = REF / "models.tsv"
GALLERY = ROOT / "gallery"
PROFILE = "https://www.myminifactory.com/users/briansouvey"
CDN = "https://images2.myminifactory.com/insecure/plain/https://assets.myminifactory.com/object-images/tmp/images/"
FIELDS = ["print_id", "posted", "code", "object_id", "his_title", "image_url"]
OBJ_ID = re.compile(r"(\d+)\s*$")

HEADER = [
    "# Brian's painted prints, as posted on " + PROFILE,
    "# Written by tools/brian_prints.py (browser agent). One row per print on his Prints tab.",
    "# print_id is the key (/prints/<print_id>). posted is the page's own date_created.",
    "# code is joined from object_id against the mmf column of models.tsv - never from his",
    "#   title, which is hand-typed and carries typos. Blank code = no matching object id.",
    "# Whether a photo is filed is NOT recorded here; it is read from gallery/ on each run.",
]


def models_by_object():
    """object id -> (code, name), from the mmf column of models.tsv."""
    out = {}
    if not MODELS.exists():
        return out
    for ln in MODELS.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) > 5 and f[5].strip():
            m = OBJ_ID.search(f[5].strip())
            if m:
                out[m.group(1)] = (f[0], f[1] if len(f) > 1 else "")
    return out


def filed_codes():
    """Codes that already have a _painted photograph in gallery/."""
    out = set()
    if not GALLERY.exists():
        return out
    for f in GALLERY.iterdir():
        m = re.match(r"^(?P<code>.+?)_painted(?:-\d+)?\.(jpe?g|png|webp)$", f.name, re.I)
        if m:
            out.add(m.group("code"))
    return out


def read_snapshot():
    rows = {}
    if not SNAP.exists():
        return rows
    for ln in SNAP.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = ln.split("\t")
        if f[0] == "print_id":
            continue
        f += [""] * (len(FIELDS) - len(f))
        rows[f[0]] = dict(zip(FIELDS, f))
    return rows


def read_scrape(path, models):
    rows, bad = {}, 0
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = [p.strip() for p in ln.split("\t")]
        if len(f) < 5 or not f[0].isdigit():
            bad += 1
            continue
        pid, title, date, obj, asset = f[0], f[1], f[2], f[3], f[4]
        m = OBJ_ID.search(obj)
        oid = m.group(1) if m else ""
        code = models.get(oid, ("", ""))[0]
        rows[pid] = {"print_id": pid, "posted": date, "code": code, "object_id": oid,
                     "his_title": title, "image_url": CDN + asset if asset else ""}
    if bad:
        print(f"warning: skipped {bad} unparseable line(s) in {path}", file=sys.stderr)
    return rows


def write_snapshot(rows):
    if SNAP.exists():
        PREV.write_text(SNAP.read_text(encoding="utf-8"), encoding="utf-8")
    ordered = sorted(rows.values(), key=lambda r: (r["posted"], r["print_id"]))
    out = HEADER + ["\t".join(FIELDS)] + ["\t".join(r[f] for f in FIELDS) for r in ordered]
    SNAP.write_text("\n".join(out) + "\n", encoding="utf-8")


def describe(r, models, filed):
    name = models.get(r["object_id"], ("", ""))[1]
    if not r["code"]:
        return (f"     !! no models.tsv row has object id {r['object_id'] or '(none)'} - "
                f"his title was {r['his_title']!r}; identify this one by hand")
    mark = "already in gallery/" if r["code"] in filed else "NOT yet in gallery/"
    line = f"     {r['code']}  {name}  [{mark}]"
    if r["code"] not in filed:
        line += (f"\n     file it with:  python3 tools/ledger.py photo {r['code']} painted <file>")
    return line


def report(seen, scraped, models, filed):
    new = sorted((r for k, r in scraped.items() if k not in seen),
                 key=lambda r: (r["posted"], r["print_id"]))
    gone = [r for k, r in seen.items() if k not in scraped]
    print(f"profile: {len(scraped)} print(s); snapshot: {len(seen)}")
    for r in new:
        print(f"  NEW  /prints/{r['print_id']}  posted {r['posted']}")
        print(f"     {r['image_url']}")
        print(describe(r, models, filed))
    for r in gone:
        print(f"  GONE /prints/{r['print_id']}  posted {r['posted']}  ({r['code'] or 'unidentified'})")
    unfiled = [r for r in scraped.values() if r["code"] and r["code"] not in filed]
    unknown = [r for r in scraped.values() if not r["code"]]
    if not new and not gone:
        print("  no change")
    if unfiled:
        print(f"  {len(unfiled)} print(s) on his profile still have no gallery photograph: "
              + ", ".join(sorted(r["code"] for r in unfiled)))
    if unknown:
        print(f"  {len(unknown)} print(s) could not be matched to a code")
    return new, gone


def main(argv):
    if len(argv) < 2 or argv[1] not in ("diff", "ingest", "list"):
        print(__doc__)
        return 2
    cmd = argv[1]
    models, filed = models_by_object(), filed_codes()
    if cmd == "list":
        rows = read_snapshot()
        for r in sorted(rows.values(), key=lambda r: (r["posted"], r["print_id"])):
            mark = "" if r["code"] in filed else "   <- no gallery photo"
            print(f"{r['posted']}  {r['code'] or '(unmatched)':<32}  /prints/{r['print_id']}{mark}")
        print(f"{len(rows)} print(s)")
        return 0
    if len(argv) < 3:
        print(f"usage: {argv[0]} {cmd} scraped.tsv")
        return 2
    seen = read_snapshot()
    scraped = read_scrape(argv[2], models)
    if not scraped:
        print("nothing scraped - refusing to touch the snapshot "
              "(an empty scrape means the page did not load, not that he deleted everything)")
        return 1
    new, gone = report(seen, scraped, models, filed)
    if cmd == "ingest":
        merged = dict(seen)
        for k, r in scraped.items():
            merged[k] = r if k not in merged else {**merged[k], **r}
        write_snapshot(merged)
        print(f"snapshot updated: {len(merged)} print(s), {len(new)} new")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
