# Producing a rotY sweep in CHITUBOX

**For the browser agent.** The ledger session cannot drive CHITUBOX; you can.
The goal is three or four sliced `.goo` files of one model, identical in every
respect except rotation about **Y**, so the ledger can screen them and pick the
orientation with the least island and peel risk before anything is printed.

## Why Y

The vat hinges at the rear and tilts down toward the front, so the peel line
runs left-right along X and sweeps front-to-rear along Y. Rotating about **Y**
makes each layer's new surface peel progressively; rotating about **X** makes it
release across its full width at once, which is what produced the ridges
parallel to X on the Gutaki and Sarglagon integrated bases. **Do not vary rotX.**

## What to produce

For `rotY` in **0, 15, 30, 45** degrees, one `.goo` each.

Hold everything else identical between them:

- the same source mesh — use the `32mm_*_STL.stl` (unsupported) file, not `_SUP`
- rotX = 0, rotZ = 0
- the same resin profile and the same layer height, exposure, bottom exposure
  and bottom layer count
- supports regenerated fresh at each orientation, with the same support settings
  — the point is to compare orientations, so the support *settings* must not
  change even though the generated supports will differ

If a rotation will not fit the plate (153.36 x 77.76 x 165 mm), skip it and say
so rather than scaling or repositioning to make it fit.

## Naming and delivery

Save each as:

    <model>_rotY00.goo   <model>_rotY15.goo   <model>_rotY30.goo   <model>_rotY45.goo

for example `32mm_P0099_Gutaki_Body_S2P3_rotY30.goo`. Put them in
`sweeps/<model>/` in the shared folder — create the directory, since your side
can create files but not delete them.

Then send a message:

    python3 tools/messages.py send browser ledger request \
      "rotY sweep ready for <model>" "4 files in sweeps/<model>/, settings held constant at ..." \
      --ref sweeps/<model>

State the resin profile, layer height and exposure you used in the body, and
note any rotation you skipped and why.

## What happens next

The ledger session runs `tools/ledger.py screen` on each, compares flat-down
area, peel-exposed area, island count and suction cups, and reports which
orientation to print. The analyses are archived under `forensics/` so the sweep
remains comparable against later ones.
