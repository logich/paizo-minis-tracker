# Paizo minis print tracker

Library of Paizo Printables miniature releases, downloaded from
<https://www.myminifactory.com/library>. Everything is printed at **32 mm** on an
**Elegoo Mars 5 Ultra**, sliced in **Chitubox**. The user prints these for their
Pathfinder game master.

`README.md` is the human-facing version of this. This file is the operating
manual for you.

Python 3 standard library only — nothing to install. Run everything from the
repository root.

## Layout

- `PRINTS.md` — **the tracker, and the source of truth.** Plain Markdown tables.
- `dashboard.html` — generated from `PRINTS.md`. Never edit it; run `build`.
- `tools/ledger.py` — the tool: `scan`, `build`, `status`, `printer`, `plate`,
  `assign`. With no argument it runs `status`.
- `tools/sliced.py` — reads settings out of `.goo` / `.ctb` files. Field offsets
  live here.
- `reference/models.tsv` — base size and creature size per model, captured from
  the Paizo base-size sheet. Joined to model directories on the P-number.
- `README.md`, `CLAUDE.md`, `.gitignore`
- `YYYYMM <name>/` — one directory per release, one subdirectory per model.

Only those tracker files are in git. The models themselves (~18 GB of STLs and
slicer projects) are gitignored. Do not commit unless the user asks.

## The data model

The unit of tracking is a **printable part**, not a model. Athamaru is three rows
(A, B, C); Gutaki is three (Body, Tentacles L, Tentacles R). 94 models currently
expand to **187 parts** — if a command reports a wildly different total,
something is wrong.

Each release is a `## <release name>` section holding one table:

    | Model | Mini | Base | Part | Stage | Plate | Result | Notes |

- `Model` — the directory name, e.g. `P0094_Athamaru_S2P3`
- `Mini`, `Base` — **derived; never hand-edit.** `scan` rewrites them from
  `reference/models.tsv` on every run.
- `Part` — `A`, `Body`, `Tentacles L`, `main`, …
- `Stage` — `todo` → `sliced` → `printed` → `cleaned` → `cured` → `primed` →
  `painted` → `delivered`. Counts as printed from `printed` onward.
- `Result` — blank, `pass`, or `fail`. **Blank means unknown, not success.**
- `Notes` — free text.

Print settings live on a **plate**, not on a part, because minis are batched.
The `## Plates` section holds:

    | ID | Date | Slicer file | Resin | Layer | Exposure | Bottom exp | Bottom layers | Lift | Result | Notes |

Plate IDs are `P<yy><mm>-<nn>` — `P2609-02` is the second plate of September 2026.
`plate` allocates the next free ID automatically.

Releases sort newest-first everywhere, by the `YYYYMM` prefix on the directory
name; anything without one sorts last. Applied in `write_ledger`, so every write
normalises it.

## Updating the tracker when the user reports results

Edit `PRINTS.md` directly, then rebuild. Typical flow:

1. **Log the plate**, if a new print run happened. Prefer reading it from the
   sliced file rather than typing it:

       python3 tools/ledger.py printer                    # see what's on the printer
       python3 tools/ledger.py plate "<filename>"         # record it as a plate row

   This fills in Date, Slicer file, Resin, Layer, Exposure, Bottom exp and
   Bottom layers. `Lift`, `Result` and `Notes` are yours to fill in by hand —
   lift settings are not present in the file (see below).

2. **Attach the parts to the plate and set their stage:**

       python3 tools/ledger.py assign P2609-02 printed P0094_Athamaru_S2P3

   Or edit the rows directly when parts on one plate ended differently — e.g. A
   and C passed but B failed.

3. **Set `Result`** to `pass` or `fail`. On a failure, put what failed in
   `Notes`; a reprint gets a new plate row rather than a rewritten history.

4. **Rebuild:**

       python3 tools/ledger.py build

5. **Check it:** `python3 tools/ledger.py status` and confirm the counts moved
   the way you expect.

### Worked example

User says: *"Athamaru A and C came out great on this morning's plate, B lost the
trident tip."*

    python3 tools/ledger.py plate "32mm_P0094_Athamaru_A_S2P3_PRE.stl_0.030_2.800_2026_09_08_09_53.ctb"
    # -> added plate P2609-02

Then edit the three rows in `PRINTS.md`:

    | P0094_Athamaru_S2P3 | Athamaru | 25mm | A | printed | P2609-02 | pass |  |
    | P0094_Athamaru_S2P3 | Athamaru | 25mm | B | printed | P2609-02 | fail | trident tip lost |
    | P0094_Athamaru_S2P3 | Athamaru | 25mm | C | printed | P2609-02 | pass |  |

    python3 tools/ledger.py build

## Never invent results

Only record what the user actually told you. If they say a plate was sliced,
that is `sliced`, not `printed`. If you don't know how a print turned out, leave
`Result` blank and ask. Do not infer a resin or an outcome from a neighbouring
plate's settings — say what's missing and ask for it.

## When a new monthly release is downloaded

1. Unpack into a directory with a `YYYYMM` prefix: `202610 October Release`.
   The prefix drives ordering, and the directory name is the key rows are stored
   under.
2. Add the new models to `reference/models.tsv` from the base-size sheet
   (<https://docs.google.com/spreadsheets/d/136R7lDaQ5BK42xDqrfJR8dN6XYIWq2PyM0_lwJQH2jU>),
   keyed by P-number. Columns: `code`, `name`, `base_mm`, `size`, `pack`.
   Without this the models still track, but with no readable name and no base size.
3. `python3 tools/ledger.py scan` — adds new parts as `todo` and leaves
   everything already recorded untouched.
4. `python3 tools/ledger.py build`

`scan` is safe to run at any time: it is idempotent and never overwrites a
Stage, Plate, Result or Note. It warns about ledger rows whose files have
vanished from disk.

`scan` takes an optional second argument used once during initial seeding
(`scan 202609` marked everything before September as printed). Don't use it
again — it only affects newly added rows, but there's no reason to.

### Renaming a release directory

Rename the `## ` heading in `PRINTS.md` in the same step. `scan` keys rows on
the release name, so renaming only one side orphans every recorded result and
re-adds the parts as `todo`.

## File naming inside a model directory

- `32mm_<code>_STL.stl` — the 32 mm mesh; **this is what gets printed**.
- `32mm_<code>_SUP.stl` — same mesh, pre-supported. Prefer it when it exists.
- `32mm_<code>_PRE.stl` — the same thing under a different name; only P0094
  Athamaru A uses it. Treated as pre-supported too.
- Files without the `32mm_` prefix are the full-size versions — not used here.
- `pathfinder_base_NN.stl` / `Round NN.stl` — the base for that model.
- A trailing descriptor (`..._STL Fixed Hand.stl`) marks a re-cut and becomes
  part of the part name.

Part names are derived by comparing **sibling files to each other** and dropping
the token prefix and suffix they share — not by diffing against the directory
name, because some directories are misnamed (April's
`P0002_Kyra_Iconic_Fighter_WP1` holds files named `..._Kyra_Iconic_Cleric_...`).
A model with a single 32 mm mesh gets the part name `main`.

The extras-sale packs (`Paizo_*`, `PQ*`) ship pre-supported at one scale with no
`32mm_` prefix, and are handled by a separate branch in `scan_disk`.

## Editing the dashboard generator

`dashboard.html` is written by `cmd_build` in `tools/ledger.py`. Three things
there are deliberate and easy to regress:

- It emits a **complete document** — `<!doctype html>`, `<head>`, `<meta
  charset="utf-8">`, `<body>`. This is a standalone file opened over `file://`,
  not an embedded fragment; without the charset declaration browsers guess
  windows-1252 and every `·` and `—` turns into mojibake.
- The file is written as **pure ASCII**, with non-ASCII escaped to numeric
  references (`&#183;`) via `encode("ascii", "xmlcharrefreplace")`. That keeps it
  correct even if served with a wrong `Content-Type`.
- Cards show a thumbnail from `Release_*.jpg` in the model directory. **Only the
  September release ships these** (13 files); older releases have none, so most
  cards have no image. That is expected, not a bug.

A `⚠` on a part chip means no pre-supported 32 mm mesh exists for it and supports
must be added in the slicer. Currently that flags one extras-pack file and
nothing else.

Always run `python3 tools/ledger.py build` after changing the generator, and
open the result to confirm.

## Serving the dashboard

**Live at <http://elite.internal/minis/dashboard.html>**
(`http://elite.internal/minis/` also works). Always use the fully qualified
`elite.internal`, not the bare `elite`: the short name only resolves on the LAN,
the FQDN also resolves over VPN. Point the user at this URL rather than sending
the file when they are on a phone — thumbnails are relative paths and only
resolve when the page is served from the repository root.

`build` writes to the served location directly, so the URL is current the moment
`build` finishes. Nothing needs deploying or copying.

The setup: nginx serves `/var/www/html` on port 80; `/var/www/html/minis` is a
root-owned symlink to this repository, and `index.html` here is a symlink to
`dashboard.html`. The repo is world-readable, so `www-data` needs no permission
changes. nginx is the `default_server` with `server_name _`, so it answers on
any hostname. The server is `192.168.1.201` if DNS fails entirely.

Thumbnail `src` attributes are percent-encoded — release directories contain
spaces, which are fine over `file://` but not valid in an HTTP path. Keep the
`urllib.parse.quote` call in `cmd_build` if you touch the image handling.

## Reading print settings off the printer

The Mars 5 Ultra serves a plain directory index at
<http://192.168.1.151:3030/media/mmcblk0p3/> and honours HTTP Range requests, so
`printer` and `plate` read the ~195 KB header rather than downloading the whole
25–110 MB file. If the printer is off, `printer` reports that it couldn't reach
it and everything else still works.

    python3 tools/ledger.py printer
    python3 tools/ledger.py plate "<file|url|printer-filename>" [plate-id]

### What is and isn't readable

- **`.goo`** — ELEGOO's own format and what the printer runs natively.
  Big-endian, ~195 KB header. Layer height, exposure, bottom exposure, bottom
  layer count, rest times, resolution, plate size and layer count all parse
  cleanly. Verified against files whose filenames encode their own settings:
  4/4 exact.
- **`.ctb`** — Chitubox's format. Every one on this printer is the encrypted
  variant (magic `0x12FD0107`); everything past byte `0x30` is ciphertext. Only
  the layer height and exposure Chitubox writes into the *filename* survive.
- **Lift distance and speed** are not recoverable from either format. Chitubox
  writes four identical placeholder `(0.03, 0.05)` pairs into that region of the
  `.goo` header. The `Lift` column is manual.

So: **export `.goo`, not `.ctb`**, if the settings should stay readable.

### Resin

`.goo` carries the Chitubox **profile name** at offset 156, which in practice
names the resin (`Elegoo Abs-like 3.0`, `Dragon Resin Durable Grey`,
`Elegoo 8K Standard Gray`, `Elegoo ABS-Like V3 Grey 30um`). `plate` fills the
Resin column from it. It records the profile the slice was made with, not proof
of what was in the vat — correct it by hand if they differed.

### A plate holds more than its name says

Chitubox names the file after whichever model was added to the plate **first**.
A file called `32mm_P0094_Athamaru_A_...ctb` may have printed a dozen other minis
alongside it. Never infer a plate's contents from its filename — that is what the
`Plate` column and `assign` are for.

## assign

    python3 tools/ledger.py assign <plate-id|-> <stage> <target>...

Sets `Stage`, and `Plate` unless you pass `-`. Targets are substring-matched
against both release and model names, so `P0094`, `Athamaru` and `202609` all
work, and a whole release can be moved at once.

**Quote release names containing spaces.** Each shell word is a separate target,
so unquoted `202604 Dragons` also matches `202604 April Release` and hits 44
parts instead of 17:

    python3 tools/ledger.py assign - printed "202604 Dragons"

`assign` prints how many parts it changed — always check that number.
