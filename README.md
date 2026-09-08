# Paizo Minis Print Tracker

Tracks which Pathfinder miniatures from the [Paizo Printables](https://www.myminifactory.com/library)
monthly subscription have been printed, on what settings, and how they turned out.

Everything prints at **32 mm** on an **Elegoo Mars 5 Ultra**, sliced in **Chitubox**.

The tracker is a plain Markdown file. A small Python tool keeps it in sync with
what's actually on disk and renders it to a dashboard. There is no database, no
service to run, and nothing to back up beyond the repository itself.

---

## What's here

| Path | What it is |
|---|---|
| `PRINTS.md` | **The tracker. Source of truth.** Plain Markdown tables — edit by hand or ask Claude. |
| `dashboard.html` | Generated from `PRINTS.md`. Open it in a browser or serve the repo root. Never edit. |
| `tools/ledger.py` | The tool. Six subcommands, described below. |
| `tools/sliced.py` | Reads print settings out of `.goo` / `.ctb` files. |
| `reference/models.tsv` | Base size and creature size per model, from the Paizo base-size sheet. |
| `CLAUDE.md` | Instructions for Claude, so chat updates follow the same conventions. |
| `NNNNNN <Month> Release/` | The downloaded models — one directory per release, one subdirectory per model. |

Only the tracker files are in git. The models themselves (~18 GB of STLs and
slicer projects) are gitignored, so history stays small and every commit is a
readable diff of what changed.

Python 3 standard library only — no dependencies to install.

---

## The unit of tracking is a part, not a model

Athamaru ships as three sculpts (A, B, C). Gutaki ships as a body and two
tentacle arms. Each of those is a separate row, because each is a separate thing
you put on a build plate. 94 models currently expand to **187 printable parts**.

Each row records:

| Column | Meaning |
|---|---|
| `Model` | The directory name, e.g. `P0094_Athamaru_S2P3` |
| `Mini` | Readable name, filled in automatically |
| `Base` | Base size needed, filled in automatically |
| `Part` | Which sculpt or component — `A`, `Body`, `Tentacles L`, `main` |
| `Stage` | `todo` → `sliced` → `printed` → `cleaned` → `cured` → `primed` → `painted` → `delivered` |
| `Plate` | Which plate it printed on — see below |
| `Result` | Blank, `pass`, or `fail` |
| `Notes` | Whatever's worth remembering |

A part counts as printed from the `printed` stage onward.

**Don't hand-edit `Mini` or `Base`** — `scan` regenerates them from
`reference/models.tsv`.

### Plates

Print settings live on a **plate**, not on each part, because you batch several
minis per print. The `## Plates` table records the resin, layer height, exposure,
bottom exposure and bottom layer count once; each part just references the plate
ID (`P2609-01`).

Plate IDs are `P<yy><mm>-<nn>` — `P2609-02` is the second plate of September 2026.

---

## Everyday use

Show progress and what bases are still needed:

```bash
python3 tools/ledger.py status
```

Rebuild the dashboard after any edit to `PRINTS.md`:

```bash
python3 tools/ledger.py build
```

Record a plate from a sliced file — reads the settings out of the file itself:

```bash
python3 tools/ledger.py plate "32mm_P0094_Athamaru_A_S2P3_PRE.stl_0.030_2.800_2026_09_08_09_53.ctb"
```

Mark what was on that plate:

```bash
python3 tools/ledger.py assign P2609-02 printed P0094_Athamaru_S2P3
```

`assign <plate-id|-> <stage> <target>...` sets the stage, and the plate unless
you pass `-`. Pass `-` when there's no plate involved:

```bash
python3 tools/ledger.py assign - printed "202604 Dragons"
```

**Quote release names that contain spaces.** Targets are substring-matched
against both release and model names, and each word becomes its own target, so
unquoted `202604 Dragons` matches `202604 April Release` as well and hits 44
parts instead of 17. `assign` always prints how many parts it changed — check
that number before moving on.

Matching on a substring is deliberate: `P0094`, `Athamaru`, `Draugr` and
`202609` are all valid targets, so you can act on one model or a whole release.

See what the printer is holding:

```bash
python3 tools/ledger.py printer
```

Then fill in `Resin`, `Lift`, `Result` and any notes by hand, and run `build`.

Or just describe what happened to Claude — "Athamaru A and B printed fine on
today's plate, C had a failed base" — and it will edit `PRINTS.md` and rebuild.

---

## Serving it on the home server

**The dashboard is live at <http://elite/minis/dashboard.html>.**

That is the URL to open from a phone or any other machine on the network —
thumbnails only render when the page is served from the repository root, so a
copy of the file on its own will show empty cards. <http://elite/minis/> also
works, via the `index.html` symlink.

The setup, for reference: nginx runs on this box with `root /var/www/html` and
an `index index.html` directive, so a single symlink was enough — no nginx
config change and no restart.

```bash
sudo ln -s /pool/Work/paizo-minis /var/www/html/minis
```

`index.html` in the repository is a symlink to `dashboard.html`, which is what
makes the bare directory URL work. If `elite` ever stops resolving, the server
is at `192.168.1.201`.

This exposes the whole repository over the LAN. Directory listing is off
(`try_files $uri $uri/ =404`), so nobody can browse it, but the STLs are
reachable by anyone who guesses a path. On a home network that is usually fine;
if it isn't, serve a directory containing only `dashboard.html` and the
thumbnails instead.

Image paths are percent-encoded, since release directories contain spaces.

## When a new month is released

1. **Download and unpack** into a directory named with a `YYYYMM` prefix:
   `202610 October Release`. The prefix is how releases are sorted, and the
   directory name is the key rows are stored under, so get it right up front —
   see *Renaming* below.

2. **Add the new models to `reference/models.tsv`** from the
   [base-size sheet](https://docs.google.com/spreadsheets/d/136R7lDaQ5BK42xDqrfJR8dN6XYIWq2PyM0_lwJQH2jU),
   keyed by P-number. Columns are `code`, `name`, `base_mm`, `size`, `pack`.
   Skip this and the models still track fine, but they'll have no readable name
   and no base size.

3. **Scan.** New parts are added as `todo`; anything already recorded is left
   exactly as it is.

   ```bash
   python3 tools/ledger.py scan
   ```

4. **Build.**

   ```bash
   python3 tools/ledger.py build
   ```

`scan` is safe to run any time — it never overwrites a stage, plate, result or
note. It also warns about rows whose files have disappeared from disk.

### Renaming a release directory

Rename the `## ` heading in `PRINTS.md` to match, in the same step. `scan` keys
rows on the release name, so renaming only one side orphans every recorded result
and re-adds the parts as `todo`.

---

## Reading settings off the printer

The Mars 5 Ultra serves a directory index at
<http://192.168.1.151:3030/media/mmcblk0p3/> and honours HTTP Range requests, so
`plate` and `printer` read the ~195 KB header of a sliced file rather than
downloading all 25–110 MB of it.

What survives in each format:

| | `.goo` | `.ctb` |
|---|---|---|
| Layer height, exposure | yes | filename only |
| Bottom exposure, bottom layers | yes | no |
| Resin profile | yes | no |
| Rest times, resolution, plate size, layer count | yes | no |
| Lift distance and speed | no | no |

**Export `.goo`, not `.ctb`.** Every `.ctb` this printer holds is the encrypted
variant (magic `0x12FD0107`) — everything past byte `0x30` is ciphertext, so only
the layer height and exposure that Chitubox writes into the *filename* can be
recovered. `.goo` is what the printer runs natively anyway, and it keeps the
record self-describing.

Resin comes from the Chitubox **profile name**, which records what the slice was
made with rather than proof of what was in the vat. Correct it by hand if they
differed.

Lift settings aren't in either format — Chitubox writes four identical
placeholder `(0.03, 0.05)` pairs into that region of the `.goo` header. That
column is manual.

### A plate holds more than its name says

Chitubox names the file after whichever model was added to the plate **first**.
A file called `32mm_P0094_Athamaru_A_...ctb` may well have printed a dozen other
minis alongside it. Never infer a plate's contents from its filename — that's
what the `Plate` column and `assign` are for.

---

## Conventions in the model files

Inside a model directory:

- `32mm_<code>_STL.stl` — the 32 mm mesh. **This is what gets printed.**
- `32mm_<code>_SUP.stl` — same mesh, pre-supported. Prefer it when it exists.
- `32mm_<code>_PRE.stl` — same thing under a different name; only P0094 Athamaru A
  uses it.
- Files without the `32mm_` prefix are the full-size versions, unused here.
- `pathfinder_base_NN.stl` / `Round NN.stl` — the base for that model.
- A trailing descriptor (`..._STL Fixed Hand.stl`) marks a re-cut and becomes part
  of the part name.

Part names are derived by comparing sibling files to each other, not by matching
against the directory name — some directories are misnamed (April's
`P0002_Kyra_Iconic_Fighter_WP1` contains files named `..._Kyra_Iconic_Cleric_...`).

Base sizes in `reference/models.tsv` were cross-checked against the base STL
shipped in each model directory: 80/80 agreed.
