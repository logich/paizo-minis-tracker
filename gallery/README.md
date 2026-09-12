# Gallery

Photographs of finished minis. Two kinds per model:

    <code>_printed.jpg     your print, cleaned and cured
    <code>_painted.jpg     Brian's paint job

`<code>` is the same key used everywhere else — a P-number (`P0094`) or an
extras directory name (`Paizo_cave_bear_Supported`). Add `-2`, `-3` and so on
for more than one of a kind: `P0094_printed-2.jpg`.

`.jpg`, `.jpeg`, `.png` and `.webp` all work. File them with:

    python3 tools/ledger.py photo P0094 printed ~/Downloads/athamaru.jpg

`build` renders `gallery.html` from whatever is here, alongside each model's
vendor render. These are committed — GitHub Pages can only show what is in the
repo — so keep them a sensible size; a phone photo scaled to ~1200px is plenty.
