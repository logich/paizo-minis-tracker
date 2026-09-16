# Paizo minis print tracker

Library of Paizo Printables miniature releases, downloaded from
<https://www.myminifactory.com/library>. Everything is printed at **32 mm** on an
**Elegoo Mars 5 Ultra**, sliced in **Chitubox**. The user prints these for their
Pathfinder game master.

`README.md` is the human-facing version of this. This file is the operating
manual for you.

Python 3 standard library only — nothing to install. Run everything from the
repository root.

## Quick reference — recording a print

Most sessions are only this. Everything below is detail for when it is not.

**A job has started or is printing**

    python3 tools/ledger.py printer                    # newest file is at the top
    python3 tools/ledger.py plate "<filename>"         # allocates the next plate ID
    python3 tools/ledger.py assign <plate-id> sliced <target>
    python3 tools/ledger.py build

**A job finished**

    python3 tools/ledger.py assign <plate-id> printed <target>
    python3 tools/ledger.py build

**Brian: handed over, approved, rejected**

    python3 tools/ledger.py assign - ready <target>     # done, waiting for the delivery
    python3 tools/ledger.py assign - review <target>    # handed to Brian
    python3 tools/ledger.py assign - approved <target>  # he passed it; Result set for you
    python3 tools/ledger.py assign - reprint <target>   # and Result = fail, reason in Notes

**Targets** — a model (`P0099_Gutaki_S2P3`), a single part
(`P0099_Gutaki_S2P3:Body`), or a whole release (`"202609 September Release"`,
quoted). `assign` prints how many parts it changed; check that number.

**Five rules that bite**

1. `printed` is not `pass`. Only Brian's approval earns `pass` — otherwise
   leave `Result` blank.
2. A plate holds more than its filename says. Check `plates/<ID>.png`.
3. Never infer base stock from plates. It is stated in the `## Bases` section.
4. Quote release names containing spaces, or each word becomes its own target.
5. Run `build` at the end. Check `python3 tools/messages.py pending <you>`
   at the start of a session and send a message when the other side has to
   act (see *Talking to the other agent*). Commit your own files, by path.

## Layout

- `PRINTS.md` — **the tracker, and the source of truth.** Plain Markdown tables.
- `dashboard.html` — generated from `PRINTS.md`. Never edit it; run `build`.
- `tools/ledger.py` — the tool: `scan`, `build`, `status`, `printer`, `plate`,
  `assign`, `screen`, `inspected`. With no argument it runs `status`.
- `tools/sliced.py` — reads settings out of `.goo` / `.ctb` files. Field offsets
  live here.
- `tools/orient.py` — scores a mesh's orientation for island risk before slicing.
- `tools/base_sheet.py` — snapshots the Google base sheet and diffs it against
  `reference/models.tsv`. Read-only on models.tsv.
- `tools/aon_sizes.py` — cross-checks base sizes against the Archives of Nethys
  export. Runs on the Mac mini only: the database is not on the Linux server.
- `tools/messages.py` — the message channel between the agents: `send`,
  `pending`, `list`, `show`. Writes `reference/messages-from-*.jsonl`.
- `reference/models.tsv` — base size and creature size per model, captured from
  the Paizo base-size sheet. Joined to model directories on the P-number.
- `README.md`, `CLAUDE.md`, `.gitignore`
- `YYYYMM <name>/` — one directory per release, one subdirectory per model.

Only those tracker files are in git. The models themselves (~18 GB of STLs and
slicer projects) are gitignored. Commit your own changes at the end of every
session — the log is the shared record between the two agents and the user.

## The data model

The unit of tracking is a **printable part**, not a model. Athamaru is three rows
(A, B, C); Gutaki is three (Body, Tentacles L, Tentacles R). 94 models currently
expand to **187 parts** — if a command reports a wildly different total,
something is wrong.

Each release is a `## <release name>` section holding one table:

    | Model | Mini | Base | Part | Scale | Stage | Plate | Result | Notes |

- `Model` — the directory name, e.g. `P0094_Athamaru_S2P3`
- `Mini`, `Base` — **derived; never hand-edit.** `scan` rewrites them from
  `reference/models.tsv` on every run.
- `Part` — `A`, `Body`, `Tentacles L`, `main`, …
- `Scale` — `32mm` for everything on disk. Other values are prints made by
  scaling up in Chitubox; see below.
- `Stage` — `todo` → `sliced` → `printed` → `cleaned` → `ready` → `review` →
  `approved` → `cured` → `primed` → `painted` → `delivered`, plus `reprint`
  and `skipped`. Counts as printed from
  `printed` onward.
- `Result` — blank, `pass`, or `fail`. **Blank means unknown, not success.**
  `pass` means *Brian approved it* — see below.
- `Notes` — free text.

Print settings live on a **plate**, not on a part, because minis are batched.
The `## Plates` section holds:

    | ID | Date | Slicer file | Resin | Layer | Exposure | Bottom exp | Bottom layers | Lift | Result | Notes |

Plate IDs are `P<yy><mm>-<nn>` — `P2609-02` is the second plate of September 2026.
`plate` allocates the next free ID automatically.

Releases sort newest-first everywhere, by the `YYYYMM` prefix on the directory
name; anything without one sorts last. Plates sort newest-first too, by `Date`,
with an unknown date (`?`) sorting to the bottom rather than the top. Both are
applied in `write_ledger`, so every write normalises them.

## Bases: what to print

    to print = what the unprinted minis need + backlog - on hand

- **minis** — derived by `bases_needed()` from parts not yet at `printed`.
- **backlog** and **on hand** — stated by the user in the `## Bases` section of
  `PRINTS.md`. They are *not* inferred.

**Never infer base stock from what plates produced.** Most bases were printed
before this tracker existed, and a batch that looks spare is usually already
allocated to older models — the six 50 mm on P2609-07 were exactly that, which
is why an earlier version wrongly reported "5 spare" when one more was needed.
The `Bases` column on a plate is a record of what that plate made, nothing more.

A blank `On hand` means unknown, which is not zero: nothing is subtracted and
`status` prints `?` so the gap is visible rather than silently assumed.

### Models with no stated base size

The August extras packs are absent from the base-size sheet and ship no base
STL, so nothing on disk or in `reference/` says what they sit on. They default
to **25mm** (`DEFAULT_BASE_MM` in `tools/ledger.py`) rather than staying `?` and
being silently excluded from the totals.

**Logan's rule (2026-09-11):** where no size is stated, use **25 mm** unless the
model is obviously Large (**50 mm**) or Huge (**75 mm**) — judged from the
render or the creature itself, not inferred from anything subtler. Record the
choice in `reference/models.tsv` so it is stated, not defaulted.

It is an assumption, so correct it where the real size is known. Extras packs
have no P-number, so `reference/models.tsv` keys them **by directory name**
instead — `Paizo_cave_bear_Supported` rather than a `P` code. The Hellknight
Chargers, cave bear and fire serpent are recorded as 50mm that way. The elk is
25mm by Logan's ruling (2026-09-13): it rears on its hind legs, so it fits the
smaller base. The P0025 Horned Dragon stays at the sheet's 25mm until Logan
measures a successful print, though he thinks it is probably 50mm. The
Ironkettles wall is *three minis in an army defence unit*, not terrain, so it
correctly takes the 25mm default.

These packs also ship a single 28mm mesh with no `32mm_` version, so they are
printed at 32mm heroic by scaling to **114%** in Chitubox (32 ÷ 28). The main
releases ship a real 32mm mesh and need no scaling.

## How "bases still needed" is counted

One base per assembled **miniature**, not per part. `bases_needed()` groups a
release's unprinted rows by model and base size, then counts distinct *variants*
within each model:

- A part whose label starts with a single letter (`A`, or `A Body` / `A Cape`
  for a multi-sculpt model that also comes in pieces) belongs to that variant.
  Athamaru A/B/C are three separate minis, so three 25 mm bases.
- Anything else (`Body`, `Tentacles L`, `Wing R`, `main`) is a component of one
  miniature. Gutaki's body and two tentacle arms assemble into a single mini on
  a single 50 mm base.

`variant_of()` implements the rule. `reference/base-sheet.csv` carries the
sheet's "(3 Models)" annotations in a `variants` column, so the check is now
mechanical rather than a hand-kept list — cross-checked 2026-09-12, **72 agree,
0 disagree**. Re-run it after a new release rather than adjusting counts by
hand:

    python3 - <<\'EOF\'
    import csv, sys, collections; sys.path.insert(0,"tools"); import ledger
    sheet = {r["code"]: int(r["variants"] or 1)
             for r in csv.DictReader(open("reference/base-sheet.csv")) if r.get("code")}
    parts = collections.defaultdict(list)
    for ps in ledger.scan_disk(ledger.load_reference()).values():
        for (m, pt), _ in ps.items():
            mm = ledger.PNUM.search(m)
            if mm: parts["P" + mm.group(1)].append(pt)
    for code, n in sheet.items():
        if code in parts:
            mine = len({ledger.variant_of(p) for p in parts[code]} - {""}) or 1
            if mine != n: print(code, "variant_of", mine, "sheet", n)
    EOF

## Brian's approval gates completion

Brian is the game master these are printed for. He has a better eye for print
detail than the user does, so **nothing is complete until he has approved it.**
Never set `Result` to `pass` on the user's say-so that a print finished — that
tells you the stage, not the verdict.

Four stages carry this:

- **`ready`** — washed here and waiting for the next delivery, **still
  supported and uncured**. Deliveries go out roughly weekly, so this is where a
  mini waits in between. It is the difference between "off the printer" and
  "with Brian", which `printed` alone could not express.
- **`review`** — delivered. Brian de-supports it, reviews it, then cures it, in
  that order. So a part is at its softest when he handles it, and a localised
  flat spot or pressure mark is as likely to come from de-supporting green
  resin as from the print itself. Weigh that before blaming a print.
- **`approved`** — Brian passed it. `assign` sets `Result` to `pass` for you,
  since the stage means exactly one thing; no hand-editing needed.
- **`cured`** — comes *after* approval, because Brian cures. It is not a step
  on this side.
- **`reprint`** — Brian rejected it, or it failed on the plate; it has to go
  back on. Put the reason in `Notes` and set `Result` to `fail`. Not
  auto-filled: a reprint is not always a rejection.

`reprint` deliberately ranks *below* `printed` in `STAGES`, so a rejected part
drops out of the done count and reappears in the print queue. It **counts
toward bases** like anything else unprinted: a first print can fail outright, as
the Gutaki body did, in which case no base was ever made. Bases you already hold
belong in `On hand`, not in an assumption made here.

This over-counts on purpose. Reprinting one component of an otherwise finished
mini — Sarglagon's Arm R, where the body, tail and other arm are all printed —
asks for a base that mini already has. **Leave it.** The user has accepted
printing a spare over the alternatives, which are all worse: "needs a base only
if no part has printed yet" stops counting Gutaki, whose body is printed while
its arms are not and whose 50mm base does not exist; and inferring that a base
must exist because a part printed is the reasoning that produced a wrong
"5 spare" earlier. A spare base costs pennies; a base short stops an assembly.

`status` lists both queues — what is sitting with Brian, and what he has sent
back, with his notes.

**A long review queue is normal.** Minis reach Brian in a delivery roughly once
a week, and sometimes a fortnight passes between them, so parts sit in `review`
for a while by design. Do not treat the size of that queue as a problem, and do
not suggest chasing him for a verdict.

**Reprints are not urgent either.** Failures fall into two kinds: the obvious
ones the user spots himself straight off the plate, and one-off failures that
Brian catches, which just need running again whenever it suits. The Signifer
went through several attempts on that basis. So a `reprint` entry is a to-do,
not an incident — do not frame delayed feedback as blocking, or push for a
settings decision that can simply wait for the next attempt.

    python3 tools/ledger.py assign - ready P0094_Athamaru_S2P3     # done, awaiting delivery
    python3 tools/ledger.py assign - review P0094_Athamaru_S2P3    # handed over
    python3 tools/ledger.py assign - approved P0094_Athamaru_S2P3  # he passed it
    python3 tools/ledger.py assign - reprint P0094_Athamaru_S2P3   # he rejected it

When he approves, `assign - approved <target>` records it and the verdict
together; move on to `primed` only when priming actually happens.

## Alternative part decompositions

Some models ship two ways to build the same miniature. Scylla has `Body` +
`Tentacles` **and** a combined `Full`; so do the Sea Hag and the Flotsam
Terror. Only one route gets printed, so **not every part needs to reach
`printed` for the model to be complete.**

Mark the route not taken as **`skipped`**:

    python3 tools/ledger.py assign - skipped "P0100_Scylla_S2PB:Full"
    python3 tools/ledger.py assign - skipped "P0100_Scylla_S2PB:Body" "P0100_Scylla_S2PB:Tentacles"

`skipped` is in `STAGES` so `assign` accepts it, but it is **not a progression
step**. `live_rows()` filters it out of progress totals and `bases_needed()`,
so a skipped part is neither "done" nor outstanding — September reads 12/16 or
12/15 depending on the route, not 12/17. `status` lists them under "Not being
printed" so they stay visible rather than silently vanishing, and the dashboard
strikes the chip through.

### Which route fits the plate

The plate is 153.36 x 77.76 x 165 mm. Measured footprints of Scylla's 32mm
meshes:

    part        mesh      X      Y      Z    footprint fits
    Body        STL    38.7   31.3   29.8    yes
    Body        SUP    44.1   35.5   31.5    yes
    Full        STL   106.0   71.7   84.9    yes
    Full        SUP   109.5   88.4   81.8    NO
    Tentacles   STL   106.0   58.4   84.9    yes
    Tentacles   SUP   113.0   88.6   78.0    NO

**The vendor's pre-supported layouts for `Full` and `Tentacles` overflow the Y
axis** — that is the support raft, not the model. Both routes therefore need
re-supporting from the raw `_STL`, exactly as the Horned Dragon body did. The
raw `Full` fits at 71.7 mm against the 77.76 mm limit, so one-piece *fits*
with your own supports; only `Body` prints as shipped.

**Fitting was not enough.** The one-piece `Full` on manual Chitubox supports
(P2609-13) printed to completion, but removing the supports left lots of surface
scarring (Logan, 2026-09-14). So Scylla moved to `Body` + `Tentacles` with new
supports (P2609-20), and `Full` is now the `skipped` route, with its `fail` kept.
A one-piece model of this size carries far more support contacts on visible
surfaces than its parts do separately.

Measure with a binary-STL bounding box: 80-byte header, `<I` triangle count at
offset 80, then `<12fH` per triangle with the vertices in floats 3-11.

### Additional prints vs reprints

`Kind` distinguishes them. Blank is the normal print of a model; **`extra`**
marks an additional print kept *alongside* an existing good one — the 50 mm
Talmandor and Living Waterfall, scaled up in Chitubox for use as monsters.

**An extra is never a reprint.** A reprint says the previous print was wrong;
an extra says nothing about it. Marking a wanted second copy as `reprint` both
libels the first print and puts it in the wrong queue. `status` lists extras
under "Additional prints", and `backlog.html` gives them their own block rather
than filing them with parts never printed.

Set it by hand in `PRINTS.md`; `scan` preserves the column and never sets it.

## Scaled-up prints

Rows are keyed by **Model + Part + Scale**. Everything the library ships is
`32mm`, so:

- `scan` only ever creates and refreshes `32mm` rows. It never invents a row at
  another scale, and never reports a non-32mm row as missing from disk — there
  is no file to find, because the scaling happens in Chitubox.
- `Mini` and `Base` are refreshed only on `32mm` rows. A scaled-up print's base
  size is left blank for the user to state, and `bases_needed()` skips any row
  whose base is blank or `?` rather than guessing.
- A scaled-up print is a separate print: its own stage, plate, result and place
  in Brian's queue. `status` lists them under "Scaled-up prints".

Target one with `@scale`, which combines with `Model:Part`:

    python3 tools/ledger.py assign P2610-01 sliced "2-P0037_Talmandor_S1P2@50mm"
    python3 tools/ledger.py assign - printed "2-P0037_Talmandor_S1P2:body@50mm"

A bare target matches `32mm` only, so existing commands never touch a scaled
row by accident.

**Adding a scaled row** means editing `PRINTS.md` by hand: copy the `32mm` row,
set `Scale`, clear `Base`, `Stage` to `todo`, and blank the result.

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
3. `python3 tools/base_sheet.py diff` — compares the sheet snapshot against
   `models.tsv` and writes new or changed rows to `reference/incoming.tsv`.
   **Read what it wrote before merging.** It reports differences, not
   corrections: the P0039 Hellbreaker "pack S1P2 -> S1P1" row is a typo on the
   sheet, and applying it would corrupt `models.tsv`.
4. `python3 tools/aon_sizes.py --release <YYYYMM>` on the mini, to cross-check
   base sizes against Archives of Nethys. Apply its "unstated" suggestions via
   `merge-reference`; hand anything it FLAGS to Logan rather than deciding.
5. `python3 tools/ledger.py scan` — adds new parts as `todo` and leaves
   everything already recorded untouched.
6. `python3 tools/ledger.py build`

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

### Tilting vat: what can and cannot be tuned

UVtools reports `HaveTiltingVat: True`, and the file carries **no tilt
parameters whatsoever**. Every motion value is vestigial:

    LiftHeight 0.03mm   LiftSpeed 0.05     RetractHeight 0.03  RetractSpeed 0.05
    LiftHeight2 0       LiftSpeed2 0       LiftAcceleration 0
    WaitTimeAfterLift 0 WaitTimeAfterCure 0

A 0.03 mm lift at 0.05 mm/min is not a real motion; the peel is done by the vat
tilting, under firmware control, and nothing about it is exposed to the slicer.

**So there is no lift tuning to do here.** The standard straight-lift advice —
raise the lift height, slow the lift speed, add a two-stage lift — has nothing
to act on. Three prints were spent raising exposure 2.8s to 3.0s on the Gutaki
and Scylla for the same reason: the knob being turned was not attached to the
problem.

What is actually available:

- **`WaitTimeBeforeCure`** (1.5 s here, `DelayMode: WaitTime`). With a near-zero
  lift, this rest is what lets resin flow back under the part before the next
  exposure. It is the one timing lever that matters on a large cross-section.
- **Orientation**, to reduce the largest cross-sectional area per layer. The
  failures land on the biggest new areas, which is what `screen` measures.
- **Support density where new area appears**, again per `screen`.
- `TransitionLayerCount` (5) ramps exposure between bottom and normal layers.

Whether Chitubox's support *generator* accounts for tilt is unknown — but since
the format carries nothing tilt-specific, nothing tilt-aware is reaching the
printer either way.

That is exactly where tilt awareness *can* live: in the geometry of the
supports, decided before the file is written. Since 2026-09-12 Logan slices in
**ELEGOO SatelLite** for that reason: its support generation is designed for
tilting-vat printers. See *Vendor supports are Lychee* below for the record.

### The tilt geometry, and what follows from it

**The vat hinges at the rear and tilts down toward the front.** So separation
begins at the front, where the displacement per degree of tilt is greatest, and
the peel line sweeps rearward. The rear separates last and with the least
mechanical advantage, which makes the rear of the plate the high-stress zone.

Two things follow, as *reasoning from the geometry*, not as anything measured
here:

- A wide flat face lying parallel to the hinge — spanning left to right —
  releases along its whole width at once as the peel line reaches it. The same
  face turned to run front-to-back peels progressively. Prefer the latter for
  anything broad and flat.
- Large cross-sections and delicate features are better placed toward the
  **front**, where separation starts and leverage is greatest, leaving the rear
  for small or well-supported geometry.

**This did not cause the failures on record.** Checked against P2609-12's island
data on the front-back axis: both islands that matched the defects sit in the
middle band (Y=1838 and Y=1551 of 4320), not at the rear, and 87% of island area
is mid-plate. Suction-cup volume is likewise spread across all three bands. The
Scylla failures are explained by island size, i.e. support adequacy, on both
axes. Treat the orientation guidance above as a way to avoid *future* trouble,
not as an account of past trouble.

### Choosing an orientation

**The mechanism.** A large island comes from a surface that is nearly parallel
to the plate and facing down: the whole face enters in a single layer, attached
to nothing. Tilt that face and it enters as a sliver that grows layer by layer,
so the island is small and the supports have somewhere to stand. This is why
island *area* tracks failure — area is set by how much new surface arrives at
once.

A suction cup is a downward-facing concavity that traps resin, which must be
pulled through as the layer separates. Tilting changes which concavities face
down and gives the trapped resin an escape path; a drain hole does the same
thing directly.

So the rule is simply: **no significant surface parallel to the plate.** A tilt
of roughly 20-45 degrees in both axes is the usual way there.

**Measuring it cheaply.**

    python3 tools/orient.py <file.stl> [step] [limit]

Scores candidate rotations by the area of downward-facing triangles within 20
degrees of horizontal — "flat-down area", a proxy for island area — in under a
second, against a slice plus five minutes for `screen`. Use it to pick two or
three candidates, then confirm the winner with `screen` on the real slice.

**Observed, on two models: ridges parallel to X on the rear of an integrated
base, at roughly rotX 20.** Seen on the Gutaki body and on the first Sarglagon
body. This is the peel model's exact signature and the best physical evidence
for it:

- A large flat *integrated base* tilted about X presents, at every layer, a
  strip spanning the full width in X.
- Each strip releases in one go as the peel line — which runs along X — reaches
  its Y. Layer after layer of that leaves a periodic ridge **parallel to X**.
- It shows at the **rear** because the rear separates last and with the least
  mechanical advantage, the hinge being there.

So an integrated base is the highest-risk feature on any of these models, and
rotating it about X is the worst thing to do with it. Flat (rotX 0) is no better
— then the entire base releases at once. **Tilt integrated bases about Y.**

**The two axes are not equivalent, and island area is not the only objective.**
The vat hinges at the rear, so the peel line runs left-right along X and sweeps
front-to-rear along Y. Peel force at any instant is proportional to how much
cross-section sits at the Y the peel line has just reached — its width in X. A
sloped face contributes one strip per layer, perpendicular to its in-plane
gradient:

- gradient along **Y** (i.e. rotated about X) -> the strip spans X -> the whole
  width releases the moment the peel line arrives. Worst case.
- gradient along **X** (i.e. rotated about Y) -> the strip runs along Y -> the
  peel line crosses it gradually. Best case.

So `orient` reports both `flat-down` (island risk) and `peel-exposed` (how much
separates simultaneously). On Scylla's 32 mm mesh:

    as modelled   flat-down 1,246   peel-exposed 10,224
    rotX 45       flat-down   921   peel-exposed 10,653   island  74%, peel 104%
    rotY 45       flat-down 1,097   peel-exposed 10,063   island  88%, peel  98%

**Rotating about Y improves both. Rotating about X buys island area by paying
in peel stress.** Prefer Y; reach for X only when island area is the binding
constraint and you accept the trade.

All-down area barely moves under either: tilting converts flat overhangs into
sloped ones rather than removing them, so the support burden stays about the
same. The gain is in *when* the load arrives, not how much of it there is.

**Limits.** It is a proxy from surface normals: it does not detect islands, does
not model supports (which can bridge a small island harmlessly), and cannot see
suction cups, which are topology rather than orientation. `screen` remains the
measurement; `orient` is only a way to pick what to slice.

### Scale depends on creature size

Small and Medium creatures print from the `32mm_` **heroic** mesh. Large and
Huge ones print from the unprefixed **default/true-scale** mesh — Gutaki (Large)
and Scylla (Huge) are both default size on purpose. That is why the Brastlewark
Snarecrafter, a Small creature, was a reprint when it came out at default size,
while Scylla at default size is not.

**The rule cuts both ways, and the `32mm_` mesh is not always the safe choice.**
P0093 Living Waterfall (Large, 50 mm) printed from its `32mm_` mesh and came out
too large: that mesh is 57.15 mm tall against the standard mesh's 49.69 mm, a
scaled-up 50 mm model. It is reprinting from the standard mesh (Logan,
2026-09-15). So on a Large or Huge model, reaching for `32mm_` is the same
mistake as slicing a Small one at default size — measure both meshes first,
and keep to the family the creature size calls for.

**All parts of one model must use the same mesh family.** The Horned Dragon's
rocks and wings do not fit its reprinted body because the body came from the
32 mm mesh and they did not — measured on all four of its parts, its `32mm_`
meshes are **1.150x** the standard ones, so a mixed set is out by 15%.

That set is being reprinted **whole, at standard scale** (Logan, 2026-09-16):
P0059 is Large on a 50 mm base, and the 32 mm body at 84.64 mm tall outgrows
it. Standard measures Body 73.60, Rocks 54.89, WingL 88.19, WingR 74.81 mm.
Slice heights are the cheap check that the right family was used: the body and
rocks slice is 79.59 mm, the 73.60 mm body plus SatelLite's ~6 mm lift, where
the 32 mm body would have given 90.6 mm. Gutaki's earlier attempts
(P2609-09, -10, -10.1, -11) all used `32mm_` meshes while P2609-14 uses the
default, so its tentacle arms must be reprinted at default size too or they will
not fit.

### Support elevation, and why it matters more on this machine

Blueprint's auto supports lifted the Gutaki body about **1 mm** off the plate
(1931 layers = 57.9 mm against a 56.9 mm bare mesh). Screening P2609-15 found
**34 suction cups all starting at layer 0**, each 11.2 mm3 and within 40 px3 of
each other — 380 mm3 in total. That near-identical size is the tell: they are
the raft cells, sealed from above by the model sitting too close to them.

Raising the elevation is the fix, and the reason it matters here more than on a
straight-lift printer is the tilting vat. A straight-lift machine raises the
plate several millimetres each layer and resin floods in from every direction.
Here the lift is 0.03 mm, so **the only escape route for trapped resin is
sideways**, through the gap between raft and model. At 1 mm that gap is a thin
slot with high flow resistance; at 5 mm the same volume drains freely.

It also matters at exactly the wrong layer. Layer 0 is where adhesion is won or
lost, and both Gutaki tentacle arms failed *to adhere to the build plate*. That
was the argument that 380 mm3 of vacuum across 34 cells on the first peels
produces that failure. **The next two prints contradict it.**

Both were sliced in ELEGOO SatelLite, and both printed:

    plate      part          layer-0 cups   each      total      outcome
    P2609-15   Body          34             11.2 mm3    380 mm3  adhered; failed at ~70%
    P2609-16   Body          220             2.6 mm3    563 mm3  printed successfully
    P2609-17   Tentacles R   418             2.6 mm3  1,071 mm3  printed and adhered
    P2609-18   Tentacles L   363             2.6 mm3    931 mm3  printed and adhered
    P2609-19   Sarglagon Arm R 87            2.6 mm3    223 mm3  printed successfully

Tentacles R carried almost three times P2609-15's raft vacuum, on the very part
that had twice failed to adhere on Lychee supports, and it held. So **total
layer-0 cup volume does not predict adhesion failure.** P2609-15, with the
coarse 11.2 mm3 cells, adhered too. It failed at about 70%, separating from
its supports under pull force. So neither total volume nor cell size has
predicted a single adhesion failure, and **the raft-cell argument above is
refuted.** It stays here as the record of a wrong turn.

P2609-15 does point somewhere else. 70% of its 1931 layers is about layer 1350
(40.5 mm, if the printer counts progress by layer). That lies between its two
largest suction cups above the raft: 18.9 mm3 from 38.88 mm and 17.2 mm3 from
43.44 mm. A cup pulling on the part at each peel is a mechanism that would tear
a part off its supports. Treat it as a candidate, not a finding: one print,
and the percentage may be by time rather than layer.

That failure is what moved Logan to **ELEGOO SatelLite**, whose support
generation is designed for tilting-vat printers. All seven of its prints so far
have succeeded: the Gutaki body and both arms, the Sarglagon Arm R reprint, the
Scylla Body + Tentacles, which Logan called one of the best prints so far, and
the Augustana Irregulars and Hellknight Bastions extras reprints. Every one of
them printed and cleaned; none has been through Brian yet.

**Measure rather than assume.** Report layer-0 cups by *size per cell* as well
as by count and total; the total alone has already misled once.

### Hollowing trades islands for suction

Measured on the same tooling, one model each:

    P2609-13  manual Chitubox, solid       311 islands   4 cups   largest    2 mm3
    P2609-14  Blueprint supports, hollow    54 islands  47 cups   largest 3,443 mm3

Hollowing cuts cross-section, which is the right lever against peel force, and
the island count fell sixfold. But a hollow shell traps resin: the largest cup
went up more than a thousandfold. **Hollow only with drain holes sized and
placed so the trapped volume can escape**, and screen afterwards — `screen`
reports cup volume, so the check is cheap.

### Screening a print before running it

    python3 tools/ledger.py screen "<sliced file>"

Downloads the file, runs UVtools island detection and gives a verdict against
thresholds taken from the Scylla failure: the two islands that failed were
**8520 and 1196 px2**, while hundreds under ~300 px2 printed fine. So islands at
or above **1000 px2** predict a defect at that height; 300-1000 is worth a look;
below that, nothing.

**That threshold was set on vendor Lychee supports, and it does not hold on
SatelLite EVO supports.** Two EVO prints have come out clean through islands
the screen marked FIX:

    P2609-16  Gutaki Body       2326 px2 at 22.59 mm              printed successfully
    P2609-20  Scylla Tentacles  1681 + 1215 px2 at ~61 mm         clean at 61 mm, EVO_60-100mm

So on an EVO-supported slice, read FIX as "look at that height when it comes
off", not as "re-support before printing". Screening is still worth doing, and
the verdict text in `cmd_screen` is unchanged. No EVO defect has been recorded
yet, so there is no EVO threshold to replace it with.

### screen records its own plate, matched by content hash

`screen` used to write a verdict only when handed a plate id, and no plate
existed until the file reached the printer — so a screen run *before* upload
could never raise a flag, and the same detection had to be run twice. Since
2026-09-16 it does this itself:

    python3 tools/ledger.py screen "<file|printer-filename>"   records a plate
    python3 tools/ledger.py screen "<file>" P2609-24           forces a plate id
    python3 tools/ledger.py screen "<file>" -                  no plate, no archive

It hashes the slice (SHA-256, free next to the download and the detection),
reuses the plate already screened from those exact bytes, and records a new one
otherwise. **Matching is on content, not filename**: re-saving a slice keeps the
bytes and changes the name, which is how the Augustana plate nearly became two
— `..._202609150901.goo` and `..._202609150905.goo` were the same file four
minutes apart.

Use `-` for throwaway candidates, such as an orientation sweep, so they do not
each mint a plate row.

The hash lives in `forensics/<plate>/verdict.tsv` as `sha256`, so the Plates
table is unchanged.

**When no hash matches, the slicer filename is the fallback.** Verdicts written
before hashing existed carry none — 11 of 12 — and hashing those slices again
would mean re-downloading them from the printer, the very waste this change
exists to avoid. So `screen` looks for a plate already recorded under that
filename, reuses it, and writes the hash into its verdict. The index heals
itself the first time each is re-screened, and no duplicate plate row is ever
created. Only when both lookups miss does it record a new plate.

Hash first, name second, and not the other way round: the same bytes under a new
name are the same plate, while the same name could in principle be a different
slice.

### A flagged plate stays visible until someone clears it

A screen verdict used to exist only in the terminal and in whatever chat message
carried it, so a warning was lost as soon as the conversation moved on — which
is exactly what happened to P2609-16's 2326 px2 island. Now `screen` writes
`forensics/<plate>/verdict.tsv`, and anything flagged **leads `status`** and gets
its own block on `backlog.html` until it is acknowledged:

    python3 tools/ledger.py inspected P2609-23 "clean at 17.40mm"

That records what was found in the verdict file, appends it to the plate's
Notes, and drops the plate off the list. Nothing clears itself: a print
finishing is not evidence that anyone looked at the flagged height.

What raises a flag:

- **fix** — an island at or above `ISLAND_FAIL` (1000 px2) above the raft, or a
  suction cup of `CUP_FLAG_MM3` (15 mm3) or more above layer 0.
- **look** — an island between `ISLAND_WATCH` (300) and 1000 px2.
- **clear** — anything less. A clear verdict never enters the list.

The cup threshold comes from the record: P2609-15 tore off its supports at a
height bracketed by cups of 18.9 and 17.2 mm3, while P2609-22's 8.8 mm3 and
P2609-23's 9.3 mm3 printed and cleaned fine. Raft cells at layer 0 are excluded
— they have never predicted a failure, as the refuted argument above shows.

**Measured across every archived plate (2026-09-16), and the threshold is weak.**
Excluding raft cells, trapped volume above the raft against outcome:

    P2609-17/18/19/21   0.0-0.4 mm3    printed fine
    P2609-20            10.6 mm3       printed, clean at 61mm
    P2609-22            20.7 mm3       printed and cleaned
    P2609-23            24.7 mm3       printing
    P2609-15            48.2 mm3       FAILED at ~70%, tore off its supports
    P2609-16           102.4 mm3       printed successfully
    P2609-14         5,443.8 mm3       cancelled on its own screen

**The classes overlap**: P2609-16 printed through twice the trapped volume of
the plate that failed. So a cup flag catches P2609-15 and false-alarms on
P2609-16 — treat it as "worth a look", never as a prediction. Raw totals are
useless without excluding the raft: P2609-17 reads 1,071 mm3 in total and
0.0 mm3 above it.

**Run-to-run variance is real but bounded.** On a model with one large
interconnected cavity, the segmentation wobbles: the Horned Dragon wings gave
23 vs 24 cups across runs, and one pocket read 21.7 mm3 in one run and 136.0 mm3
in another. Totals held to ~1%, and a model with small isolated cavities
(the body and rocks slice) reproduced exactly. So trust the total, and confirm
any single-cup figure with a second run before acting on it.

Verdicts were back-filled for every plate screened before this existed, and the
ten whose outcome was already on record were closed with that outcome. Keep it
that way: a list where everything is flagged hides the one plate that matters.

### Solidify is the fix for resin traps, not drain holes

UVtools' Solidify fills every enclosed void in a layer, so it removes suction
cups wholesale without touching the mesh or leaving a visible hole. Logan ran it
on both Horned Dragon slices (2026-09-16):

    plate            cups          resin traps    islands     largest island
    wings            23 -> 0       2280 -> 134    510 -> 482  unchanged
    body + rocks      6 -> 0       2155 ->  199   747 -> 725  unchanged

**The island lists came back identical line for line**, which is the check that
it only filled interiors: had the outer contours moved, the islands would have
moved with them. 223 mm3 of trapped resin on the wings went to nothing, so the
drain-hole and reorientation questions never had to be answered.

The CLI reproduces the GUI **byte for byte** (same SHA-256), so it can be
scripted. Parameter names come from `OperationSolidify.cs`:

    UVtoolsCmd run <file>.goo Solidify -p LayerIndexStart=300 -o <out>.goo

`LayerIndexStart` skips the raft and support transition, where filling cells
would be wrong.

**Two traps of its own.**

- **It rewrites the motion values, and you cannot undo it.** Saving through
  UVtools turns `LiftHeight`, `LiftSpeed`, `RetractHeight`, `RetractSpeed` and
  the Bottom equivalents from **0 to 0.05**. `set-properties` will not fix it:
  `RetractHeight` is read-only, and the settable ones clamp back to 0.05 on
  save — verified per layer (7,959 properties set, all 0.05 on read-back) as
  well as globally.

  **This is very likely harmless**, and the alarm is mine to own: P2609-02 came
  out of Chitubox carrying `0.03mm @ 0.05` and printed the Athamaru set
  normally, P2609-11 carried the same and failed only on plate adhesion, and
  the runlog reports `lift 0.000000mm @ 0.000000` whatever the file holds —
  which is what the tilting-vat section above already says. Check `runlog` on
  the opening layers of the first solidified print, and stop worrying about it
  after that.
- **`compare` diffs parameters only.** It reports no pixel, image or area
  differences at all, so it cannot tell you what a fill changed; screening
  before and after is what answers that. It also throws `Invalid file`
  spuriously when several UVtools processes run at once — retry before
  believing it.

**Which models are worth screening.** Every print failure so far has been on a
**50 mm or 75 mm** model — Sarglagon, Gutaki, Scylla, and the Horned Dragon
before them. None of the 73 models on a 25 mm base has failed a print. There are
21 on 50/75 mm; screen those, skip the rest.

It costs a full download plus about five minutes, against four to eight hours on
the plate, so it only pays on the large ones.

### Proactive measures, in order of evidence

1. **Screen 50/75 mm models after slicing, before printing.** It named both
   Scylla defect heights in advance on Lychee supports. On SatelLite EVO
   supports its FIX verdicts have twice printed clean, so there it points at
   heights to inspect rather than predicting failure.
2. **Support 50/75 mm models yourself; SatelLite is the current choice.**
   Vendor Lychee supports have failed on the Gutaki body and both arms, the
   Horned Dragon body and Scylla; manual Chitubox supports are what finally
   printed the Horned Dragon. Blueprint's auto supports failed on the Gutaki
   body (P2609-15). SatelLite slices have printed 7 for 7: the Gutaki body and
   both arms, the Sarglagon Arm R reprint, the Scylla Body + Tentacles, and the
   Augustana Irregulars and Hellknight Bastions extras reprints.
3. **Fix the islands `screen` names** rather than raising exposure. Scylla's
   defects survived 2.8s, 2.9s and 3.0s and a new FEP, because exposure was never
   the problem.
4. **Watch the suction cups it reports, above the raft.** Scylla carried 330.
   Layer-0 raft cells have not predicted a failure (see *Support elevation*).
   A large cup mid-model may: P2609-15 tore off its supports at about the height
   of its two largest.

### Vendor supports are Lychee, ours are Chitubox

The vendor supports in Lychee Slicer, not Chitubox — the library ships **125
`.lys` project files**, 104 of them named `*_PRE.lys`, which is what the `_PRE`
suffix means: pre-supported, Lychee's own project alongside the baked mesh.

The two generators differ in tip diameter, contact depth, branching and raft
style, and the vendor tuned theirs for an unknown machine. The Mars 5 Ultra has
a **tilting vat**, whose peel mechanics differ from a straight-lift printer, so
supports adequate elsewhere may be under-specified here.

The record so far is consistent with that, but **confounded**: every
vendor-supported failure is also a large model, so support origin and footprint
co-vary and neither is yet isolated.

- Vendor `_SUP` (Lychee): Gutaki body warped on the plate, both tentacle arms
  failed to adhere, across 2.8s, 2.9s and 3.0s and a new FEP.
- Manual Chitubox supports: the Horned Dragon body printed only after being
  re-supported from the raw `_STL`, having failed on the vendor mesh. The
  Scylla `Full` (P2609-13) printed to completion but scarred badly when the
  supports came off. So these supports held, but left marks, which is a
  different failure from detaching.
- HeyGears Blueprint auto supports: Gutaki body hollow (P2609-14) cancelled on
  its screen; solid (P2609-15) adhered but separated from its supports at
  about 70% under pull force.
- ELEGOO SatelLite, tilt-aware supports, in use since 2026-09-12: Gutaki body
  (P2609-16) printed successfully; Tentacles R (P2609-17) printed and adhered;
  Tentacles L (P2609-18), which twice failed to adhere on Lychee, printed
  great. All three Gutaki parts are default size. Sarglagon Arm R (P2609-19),
  rejected earlier for a flat spot, reprinted successfully. None has been
  reviewed by Brian yet.
- **EVO support test, settled:** Scylla Body + Tentacles (P2609-20).
  Screened before printing with two islands over 1000px2 at about 61 mm on the
  Tentacles, and deliberately run as sliced, not re-supported, to see how EVO
  supports handle it. The supports use SatelLite presets chosen per part:
  **Body on `EVO_0-30mm`, Tentacles on `EVO_60-100mm`**. The preset is not in
  the `.goo`, so record it in plate Notes whenever Logan names one. **Result
  (Logan, 2026-09-15): the Tentacles are clean at 61 mm, and the print is "one
  of the best prints so far".** With P2609-16 printing through a 2326px2 island,
  the 1000px2 threshold from the Lychee-supported Scylla failure does not
  transfer to EVO supports. See *Screening a print before running it*. Neither
  part has been reviewed by Brian yet.

Treat it as an open variable rather than a settled cause. It is also not the
only one — Scylla's defects are confined to one region of the plate, which
points at the machine rather than at either support style.

## File naming inside a model directory

- `32mm_<code>_STL.stl` — the 32 mm mesh; **this is what gets printed**.
- `32mm_<code>_SUP.stl` — same mesh, pre-supported by the vendor. Usually the
  one to print, but not always: the Horned Dragon body detached under peel
  force on the `_SUP` mesh and only printed once it was re-supported from the
  raw `_STL`. A slicer filename ending `_STL` generally means exactly that.
- `32mm_<code>_PRE.stl` — pre-supported too; `PRE` is the vendor's own label
  for it, matching the `*_PRE.lys` Lychee projects they ship. Only P0094
  Athamaru A has one at 32 mm.
- Files without the `32mm_` prefix are the **full-size** meshes — full size
  meaning true scale, not physically larger. The `32mm_` ones are **heroic
  scale**, which is both the chunkier tabletop proportion and physically bigger:
  about 1.12x, measured on the Brastlewark Snarecrafter at 33.6 mm against
  29.9 mm. Slicing a full-size mesh by mistake gives a mini that reads
  undersized next to the rest of the collection, which is why the Brastlewark
  had to be reprinted. Scaling one up ~112% reaches heroic scale — the same
  correction the extras packs need at ~114%.
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

### The backlog page

`build` also writes `backlog.html` — a working queue rather than a progress
view. Reprints lead, each with the reason from its `Notes` and the plate it
failed on; then parts never printed; then bases still to make. The two pages
link to each other.

**The reason comes from the part's `Notes`.** A reprint with an empty Notes
shows a bare row, which is why recording why something failed matters. Every
reprint now carries a reason. The six extras parts that had none, the Augustana
Irregulars and the Hellknight Bastions, were both probably too small (Logan,
2026-09-14): most likely printed without the scale-up from the 28mm mesh. So
**check the scale of any extras mesh before slicing**, including anything
exported from Lychee: an unscaled one prints at 28mm and reads undersized.

### The gallery page

`build` also writes `gallery.html` from photographs in `gallery/`: the vendor
render, the user's print, and Brian's paint job side by side.

    gallery/<code>_printed.jpg     the print, cleaned and cured
    gallery/<code>_painted.jpg     Brian's paint job

`<code>` is the usual key — a P-number or an extras directory name. Add `-2`,
`-3` for more than one of a kind. File them with the `photo` command rather
than copying by hand, so the naming stays right:

    python3 tools/ledger.py photo P0094 printed ~/Downloads/athamaru.jpg

The photographs are committed, since GitHub Pages can only serve what is in the
repo; `.gitignore` has an exception for `gallery/`. Keep them a sensible size.

### Plate previews on the dashboard

`build` caches each plate's preview to `plates/<ID>.png` and shows it as a
thumbnail in the Plates table, linking to the full image. Extraction happens
once and the PNG is committed, deliberately: the `.goo` it came from is
eventually deleted off the printer, so the cached image ends up being the only
record of what that plate held. `.gitignore` therefore has an exception for
`plates/*.png`.

If the printer is unreachable when a new plate is recorded, the thumbnail is
just missing and the build still succeeds; a later `build` backfills it while
the file is still on the printer. `.ctb` plates get one via UVtools, at the cost of downloading the whole file.

## Division of labour with the browser agent

A separate Claude Cowork agent has a logged-in browser and computer access. The
split follows from what each side can actually reach, and neither can do the
other's half:

**The browser agent does** — anything needing MyMiniFactory or a logged-in
session: collecting object page URLs, finding artwork URLs, reading the
base-size sheet, gathering names and sizes for packs absent from it. This
session **cannot**: object pages return 403 to scripted requests, from both
curl and WebFetch, and there is no browser here.

Driving the slicer is **not part of this split at present.** The browser agent
can see and control applications on the Mac mini, so reading CHITUBOX or ELEGOO
SatelLite back is technically possible, but it is not in use and should not be
asked for unless Logan says otherwise. What reached the printer is already
readable here from the `.goo`/`.ctb` header (`printer`, `plate`) and from the
printer's own log (`runlog`), which is the authority for what actually ran.

**This session does** — anything needing the machine: the repository and git,
the ledger tooling, the printer at `192.168.1.151` (LAN-only), plate previews,
UVtools and the dashboard build. Since 2026-09-13 the ledger session runs on
the **Mac mini**. nginx and the served dashboard stay on the **Linux home
server** (`elite.internal`), which serves this same shared repository, so a
`build` on the Mac is live the moment it finishes. None of this is the browser
agent's to do, whichever machine it runs on, and git in particular is off
limits to it (see *Commits*).

### The handoff

The agent produces a tab-separated file with a header row. `code` is required —
a P-number or an extras directory name — and any of `mmf`, `name`, `base_mm`,
`size`, `artwork` may accompany it:

    code	mmf	artwork
    P0100	https://www.myminifactory.com/object/3d-print-scylla-837920	https://images2.myminifactory.com/...

Then:

    python3 tools/ledger.py merge-reference reference/incoming.tsv
    python3 tools/ledger.py scan && python3 tools/ledger.py build

`merge-reference` updates matched rows in `reference/models.tsv` in place,
reports any code it does not recognise rather than inventing a row, and
downloads anything in an `artwork` column into the right model directory.

Tell the other side the file is ready, and anything it needs to know before
merging, with `tools/messages.py send` (see *Talking to the other agent*).
`reference/HANDOFF-NOTES.md` is the pre-channel version of the same thing;
it stays for the record but nothing new goes there.

**URLs are enough — files are not needed.** The image CDN serves fine from here
once a User-Agent is set, so the agent need only report links. Pasting them into
chat works just as well as a file; `ledger.py artwork <url>...` takes them
directly.

## Talking to the other agent

Two agents and the user share this repository and never share a session. The
browser agent's side of the folder can create and append to files but cannot
delete them, which rules out anything that needs a lock file or an unlink: git
commits fail there (`index.lock` cannot be cleared), and so do SQLite's default
and WAL journal modes. Appending to a file needs neither, so the channel is two
append-only files with one writer each:

    reference/messages-from-browser.jsonl    written only by the browser agent
    reference/messages-from-ledger.jsonl     written only by the ledger session

One JSON object per line, never edited or reordered; `tools/messages.py` is the
only thing that should write them. A record:

    {"id": "browser-20260911-2", "ts": "2026-09-11T14:04:31-04:00",
     "from": "browser", "to": "ledger", "type": "request",
     "subject": "Fix cmd_artwork keying before merge-reference",
     "body": "...", "refs": ["tools/ledger.py"], "re": null}

- `to` — `ledger`, `browser` or `user`.
- `type` — `request` (recipient must act; open until a `done` names it),
  `question` (open until an `answer` names it), `done`, `answer`, `info`
  (nothing to do). A `done` or `answer` carries the id it closes in `re`.
- `refs` — repository paths the reader should look at.
- The user speaks as `from: user` and picks a file with `--via`.

### Every session

Start by reading what is addressed to you, and end by saying what the other
side now has to do:

    python3 tools/messages.py pending ledger        # or browser, or user
    python3 tools/messages.py list 20               # recent traffic, both files
    python3 tools/messages.py show <id>

    python3 tools/messages.py send ledger browser request "Grab October's links" \
        "Release lands 1 Oct; incoming.tsv format as before." --ref reference/incoming.tsv
    python3 tools/messages.py send ledger browser done "Merged 93 rows, artwork filed" --re browser-20260911-2

Rules that keep it honest:

- **Close what you finish.** A `request` stays in the other side's `pending`
  until a `done` names it. If you only did part of it, say which part in the
  `done` and send a fresh `request` for the rest.
- **A message to the user is not a conversation with the user.** He does not
  read the files routinely. Send `to: user` for the record, and also say it
  to him in chat.
- **Put facts in the body, not just in the subject**, and put the paths in
  `refs`. The reader may be a fresh session with none of your context.
- **Never write the other side's file.** Not to fix a typo, not to mark
  something done — send a message instead.
- **Both files are committed** whenever the ledger session commits, so the
  history is in git even though the browser agent cannot commit.

### Commits

The git log is the durable record; the channel is how the two sides find
each other's work. Whoever can commit does so at the end of every session that
changed tracked files, staging only their own files by path (never `git add
-A`; the tree usually carries mode-only noise from the mount). Message form:

    <agent>: <what changed, one line>

    <why, counts, caveats — written for whoever reads the log a month on>

**The browser agent must not run git at all beyond `git log` and
`git --no-optional-locks status`.** Even a plain `git status` refreshes the
index by writing a new one and renaming it into place; on the browser side's
mount that rename cannot complete and it corrupted `.git/index` once
(2026-09-11). `--no-optional-locks` stops `status` from writing. Anything
that stages, commits, resets or checks out is the ledger session's job.

The browser agent cannot commit from its side. It leaves its files in place,
writes the intended message to `reference/COMMIT-MSG-browser.txt`, and sends
the ledger session a `request` to land it:

    git add <paths> && git commit --author="Browser agent <browser@paizo-minis>" -F reference/COMMIT-MSG-browser.txt

Stay on the current branch: no new branches, rebases, amends of commits you
did not make, force of any kind, or pushing unless asked.

### Who owns what

Each file has one writer. Ledger session: `PRINTS.md`, `reference/models.tsv`,
`tools/ledger.py`, `tools/sliced.py`, `tools/preview.py`, `plates/`,
`dashboard.html`, `README.md`, `reference/messages-from-ledger.jsonl`. Browser
agent: `reference/incoming.tsv`, `reference/mmf-links.tsv`,
`reference/HANDOFF-NOTES.md`, `reference/COMMIT-MSG-browser.txt`,
`reference/messages-from-browser.jsonl`. `tools/messages.py` and `CLAUDE.md`
are shared: change them only for the part that concerns you, and say so in a
message. Leave the other side's uncommitted files alone — they are mid-task.

## Linking a model to its MyMiniFactory page

Nothing in the downloaded packs references MyMiniFactory — no id, no URL, no
metadata file — and the object pages return 403 to scripted requests, so the
link cannot be derived or scraped. It has to be recorded by hand.

`reference/models.tsv` takes an optional sixth column, `mmf`, holding either the
full object URL or just the numeric object id from the end of it
(`.../3d-print-scylla-837920` -> `837920`). When present, the dashboard turns
the mini's name into a link to it.

    P0100	Scylla	75	Huge	S2PB	https://www.myminifactory.com/object/3d-print-scylla-837920

The slug differs from anything we hold (`3d-print-scylla`, not `P0100_Scylla_S2PB`),
so a bare id only reconstructs correctly when the slug happens to match the
code — prefer pasting the whole URL.

## Mini artwork on the dashboard

Cards use the vendor's logo render from the model directory: `*.webp` first,
then `*.avif`, then `Release_*.jpg`. **Save the webp** — it is 1000x1000 at
~11 KB, against avif's 720x720 at ~40 KB and the jpg's ~122 KB, so it is both
the sharpest and the smallest.

Filenames vary (`1000X1000-P0094_Athamaru_S2P3_Logo.webp`,
`1000X1000-P0100_Scylla_S2PB.webp`), so the lookup globs by extension rather
than matching a name.

Save one per model directory each month, straight from the model's
MyMiniFactory page. These are not gitignored: GitHub Pages can only show images
that are in the repo, while the STLs and `Release_*.jpg` stay out.
`ledger.py artwork <url>...` will download and file them by P-number if you
have the links instead.

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

## UVtools

UVtools 6.2.0 decrypts Chitubox `.ctb` files, extracts plate thumbnails from
any format it understands, and does the island detection behind `screen`.
Both hosts share this directory, so each keeps its own build, and
`sliced.UVTOOLS` picks by platform:

    Linux server   ./uvtools/UVtoolsCmd                                    linux-x64
    Mac mini       ./uvtools-macos/UVtools.app/Contents/MacOS/UVtoolsCmd   osx-arm64

The ledger session moved to the Mac mini on 2026-09-13; the macOS build was
installed then from the v6.2.0 GitHub release. Both are **gitignored**, since
a 100-270 MB bundle is a tool we run, not something this repo carries. A fresh
clone will not have one, and everything degrades to the `.goo`-only path
without it.

Don't point it at the UVtools bundled inside ELEGOO SatelLite: that one is
x86-64 and crashes with SIGBUS when SatelLite runs it.

Two quirks worth knowing:

- `UVtoolsCmd print-properties` **exits 1 even on success.** Judge it by whether
  its output parses, never by the return code.
- Global flags such as `--no-progress` go *before* the subcommand; `--partial-mode`
  goes after the input file and makes loading nearly instant.

    ./uvtools/UVtoolsCmd --no-progress print-properties <file> --partial-mode
    ./uvtools/UVtoolsCmd --no-progress extract <file> <dir> -c Thumbnails

## Reading print settings off the printer

The Mars 5 Ultra serves a plain directory index at
<http://192.168.1.151:3030/media/mmcblk0p3/> and honours HTTP Range requests, so
`printer` and `plate` read the ~195 KB header rather than downloading the whole
25–110 MB file. If the printer is off, `printer` reports that it couldn't reach
it and everything else still works.

    python3 tools/ledger.py printer
    python3 tools/ledger.py plate "<file|url|printer-filename>" [plate-id]

Two slicers now name files differently, and `from_filename` reads both:

    Chitubox    <mesh>.stl_0.030_2.800_2026_09_12_19_58.goo   layer, exposure, time
    SatelLite   <mesh>_STL_3_202609122351.goo                 time only

ELEGOO SatelLite came into use on 2026-09-12 for the Gutaki reprints
(P2609-16, P2609-17). Its names carry no layer height or exposure, so for a
`.goo` those come from the header, as they always did.

### The printer's control interface, and why we don't use it

Mapped on 2026-09-16 from the printer's own log while Logan sent a file, then
confirmed by probing. **Sending files is deliberately NOT automated** — Logan
sends them from SatelLite by hand — but knowing the interface explains what the
log is showing, and the read-only parts are already used.

    UDP 3000, payload "M99999"   discovery: replies with MachineName,
                                 MainboardID, protocol and firmware version
    ws://<ip>:3030/websocket     SDCP control channel (bare HTTP gets 426)
    POST /uploadFile/upload      chunked file upload, with an MD5 field;
                                 a 170 MB file logged 163 chunks
    GET  /media/mmcblk0p3/       the file listing `printer` already reads
    GET  /media/mmcblk0p2/log    the rolling log `runlog` already reads

Commands go over the websocket as JSON on topic `sdcp/request/<MainboardID>`:

    Cmd 128  {"Filename":"/local/<name>.goo","StartLayer":0}   start a print
    Cmd 258  {"Url":"/local/"}                                 list files
    Cmd 320 / 0 / 1                                            status polls

This machine is `0384c72b7e610100`, a Mars 5 Ultra on protocol V3.0.0,
firmware V1.5.0. During a transfer the file appears briefly as
`<uuid>_<name>.goo` before taking its plain name, and the printer renders a
preview to `/media/mmcblk0p1/file_info/<name>_goo.bmp`.

**Never send `Cmd 128` on your own initiative.** Starting a print commits resin
and hours of machine time, and nothing in a chat log is worth that; it needs
Logan asking for that file, in that moment.

## Settings changed on the printer itself

A setting changed on the machine never reaches the sliced file: the filename and
header still say whatever Chitubox wrote. The printer's own rolling log records
what actually executed, so it is the authority for a run:

    python3 tools/ledger.py runlog

It reads the `execute:` lines from `/media/mmcblk0p2/log` and reports exposure,
lift and rest times — the Gutaki reprint shows `exposure 2.90s` while its file
says 2.8s. The log has no filenames in it and rolls over, so treat it as "the
run happening now", not as history.

**Record what ran, not what was sliced.** Put the real value in the plate's
`Exposure` and say in `Notes` that it was set on the printer and where the value
came from. Otherwise the ledger quietly disagrees with the machine, and a later
comparison of exposures across plates is wrong.

**`runlog` reports settings, not outcomes.** The printer has no sensor for bed
adhesion or print failure, so nothing in the log distinguishes a good run from a
detached one — the `execute:` lines are identical either way. Never suggest
watching it to catch a failure early. A failure to adhere only becomes visible
when the build plate rises clear of the resin, at roughly 25-30% of the run, and
only by looking at it.

### What is and isn't readable

- **`.goo`** — ELEGOO's own format and what the printer runs natively.
  Big-endian, ~195 KB header. Layer height, exposure, bottom exposure, bottom
  layer count, rest times, resolution, plate size and layer count all parse
  cleanly. Verified against files whose filenames encode their own settings:
  4/4 exact.
- **`.ctb`** — Chitubox's format, and every one on this printer is the encrypted
  variant (magic `0x12FD0107`): everything past byte `0x30` is ciphertext, so we
  cannot read it directly. **UVtools decrypts it**, and `plate` uses UVtools
  automatically when `./uvtools/UVtoolsCmd` is present, recovering the same
  fields as `.goo` plus lift, print time and resin weight. Without UVtools only
  the filename's layer height and exposure survive.
- **Lift height and speed** are stored in both formats and read the same in
  both: `0.03mm @ 0.05`. These are not placeholders, as previously assumed —
  UVtools reports the identical values from the encrypted ctb, and the Mars 5
  Ultra has a tilting vat (`HaveTiltingVat: True`), where peeling is done by
  tilting rather than by a long lift.

`.goo` is still much cheaper to read: its header comes down in a 195 KB range
request, while UVtools needs the whole 25–110 MB file on disk. Prefer `.goo`
when exporting; UVtools is the fallback that makes old `.ctb` files legible.

### Resin

`.goo` carries the Chitubox **profile name** at offset 156, which in practice
names the resin (`Elegoo Abs-like 3.0`, `Dragon Resin Durable Grey`,
`Elegoo 8K Standard Gray`, `Elegoo ABS-Like V3 Grey 30um`). `plate` fills the
Resin column from it. It records the profile the slice was made with, not proof
of what was in the vat — correct it by hand if they differed.

## Seeing what a plate actually held

`.goo` files embed two rendered previews of the build plate — 116x116 and
290x290, RGB565, big-endian, at offsets 194 and 27108. This is the only
reliable way to tell what a plate held, since Chitubox names the file after
whichever model was added first.

    python3 tools/ledger.py preview "<file|url|printer-filename>" [out.png] [small|big]

`tools/preview.py` does the decoding and writes the PNG with zlib and struct,
so there is nothing to install. Read the PNG to check a plate's contents before
recording them; it settles questions the filename cannot.

`.ctb` files carry a preview too, but only UVtools can get at it, and it needs
the whole file — so a ctb preview costs a full download (~30s) where a goo one
costs a 195 KB range request.

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
