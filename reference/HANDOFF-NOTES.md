# Notes from the browser agent

Messages left for the ledger session. Newest first; delete an entry once it is
dealt with.

## 2026-09-11 — first full library capture

`reference/incoming.tsv` is ready for `merge-reference`: 93 rows — every
numbered model in `models.tsv` (83) plus the 10 August extras directories —
each with `mmf` and `artwork`. `reference/mmf-links.tsv` is the full 113-object
dump of the Paizo Printables library (PDFs, discount posts, bases sets too), in
case anything else is wanted.

Things to know before merging:

1. **`cmd_artwork` will skip 45 of the 93 rows as written.** It looks for a
   P-number in the URL filename, but 35 numbered models (all of April: assets
   are named `april2026__0036_Ezren.png`, `Horned Dragon.png`, etc.) and every
   extras pack have none. Key the download on the incoming `code` column
   instead of the URL stem — `merge-reference` already has the code in hand.
   It also saves everything as `.avif`; these URLs serve webp (`@webp` suffix),
   so the extension should follow the URL, or the dashboard's `*.webp`-first
   lookup will miss them.

2. **Artwork URL form.** `https://images2.myminifactory.com/insecure/plain/<asset>@webp`
   returns the 1000x1000 render; all 93 were load-tested at that size in the
   browser. Drop `@webp` for the raw png/jpg, or use `@avif`.

3. **Duplicate names resolved by hand:** P0025 Horned Dragon → object 779538
   (April WP1); P0059 Horned Dragon → 816627 (July WP4). P0028 Hellknight
   Signifer → 779547; the extras "Hellknight Signifers" pack is 768556
   (`Paizo_Signifers_Supported`).

4. **No base sizes for the extras.** The object pages say nothing — the
   description, Technical Information and Object Parts sections carry no size —
   so `name` is filled for the ten extras but `base_mm` is deliberately absent.
   The 25 mm default stands unless the user states otherwise.

5. Shells on both machines are blocked from `images2.myminifactory.com`
   (proxy 403), so the verification above was done in the browser, not with
   curl. Your User-Agent workaround may still work from the ledger session.
