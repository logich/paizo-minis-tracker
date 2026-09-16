# Paizo Minis — Print Tracker

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

## Bases

| Size | On hand | Backlog | Notes |
| --- | --- | --- | --- |
| 25mm | 7 | 52 | Brian counted 52+ needed to glue and primer existing minis (2026-09-12), not counting anything printed this week. A floor, not an exact figure |
| 50mm | 0 | 1 | the 6 on P2609-07 are already allocated to older models, not spare |
| 75mm | 0 | 5 | backlog from older models |

## Plates

| ID | Date | Slicer file | Resin | Layer | Exposure | Bottom exp | Bottom layers | Lift | Bases | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2609-23 | 2026-09-16 | 32mm-Paizo_PFQ_Signifer_Corps_A_1_202609160830.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Three reprints on one plate, despite the filename naming only the Signifer: Living Waterfall from the standard true-scale mesh (its 32mm mesh printed too large), Brastlewark Snarecrafter from the 32mm heroic mesh re-supported in SatelLite, and Signifer Corps A re-exported at exactly 114%. Identical in size (125820374 bytes) and header (1697 layers = 50.91mm) to the 20:22 slice screened from sweeps/, re-saved at 08:30 and sent to the printer. Screened clean: 348 islands, none over 1000px2 (largest 401px2 at 17.40mm); largest suction cups 9.3mm3 from 41.04mm, 5.5mm3 from 14.01mm and 4.6mm3 from 37.98mm, all above the raft - worth a look at those heights. Printing 2026-09-16 (Logan) |
| P2609-22 | 2026-09-15 | 32mm-Paizo_PFQ_bastion_A_1_202609152004.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Hellknight Bastions A, B and C on one plate, despite the filename naming only A: vendor meshes exported from Lychee without supports, all three at exactly 114%, re-supported in ELEGOO SatelLite. Identical in size (103035391 bytes), header (1479 layers = 44.37mm) and preview to the 09:30 slice screened from sweeps/, re-saved at 20:04 and sent to the printer. Screened clean: 1488 islands, none over 1000px2 (largest 700px2 at 21.57mm); largest cups above the raft 8.8mm3 from 36.33mm and 6.4mm3 from 32.40mm - worth a look at those heights. The reprint of the too-small first print, and the second comparison of SatelLite supports against the vendor's Lychee ones. Printed and cleaned successfully (Logan, 2026-09-16); not yet with Brian |
| P2609-21 | 2026-09-15 | 32mm-Paizo_PFQ_Augustana_irregulars_ABC_1_202609150905.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Augustana Irregulars A, B and C on one shared raft: vendor meshes exported from Lychee without supports, re-supported in ELEGOO SatelLite, all three at 114%. The comparison against the vendor's Lychee supports. Byte-identical in size, header and preview to the 09:01 slice screened from sweeps/ (1601 layers = 48.03mm; no island over 1000px2). Printed and cleaned successfully (Logan, 2026-09-16); not yet with Brian. The first extras reprint on SatelLite supports, so Brian's verdict on surface quality is the comparison against the vendor's Lychee supports |
| P2609-20 | 2026-09-14 | P0100_Scylla_Tentacles_S2PB_STL_1_202609141610.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Scylla Tentacles and Body on one plate (Body confirmed by Logan, 2026-09-14) - the separate-parts route with new supports, sliced in ELEGOO SatelLite, after the one-piece Full scarred on support removal. Printed to completion and cleaned (Logan, 2026-09-15). Tentacles clean at ~61mm despite the two islands over 1000px2 - "one of the best prints so far" (Logan). Not yet with Brian. Screened before printing: 325 islands, TWO over 1000px2 - 1681px2 at 61.17mm and 1215px2 at 61.08mm, with a third of 996px2 at 61.08mm, all clustered at X~6700-6900 Y~1190-1320, i.e. one under-supported spot on the Tentacles. Largest cup above the raft 6.5mm3 at 55.65mm; 116 layer-0 cups, 2.6mm3 each, 290mm3 total. Logan is running it as sliced on SatelLite's EVO supports, not re-supported (2026-09-14). Support settings per part (Logan): Body on EVO_0-30mm, Tentacles on EVO_60-100mm. That tests the 1000px2 threshold against EVO supports directly; check ~61mm on the Tentacles when it comes off |
| P2609-19 | 2026-09-14 | P0031_Sarglagon_Drowning_Devil_Arm_R_S1P1_STL_1_202609140955.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Sarglagon (Drowning Devil) Arm R reprint, sliced in ELEGOO SatelLite. Printed successfully (Logan, 2026-09-14); not yet with Brian. Screened after printing: 70 islands, none over 1000px2 (largest 917px2 at 16.08mm, then 484px2 at 15.57mm and 368px2 at 26.61mm). 87 suction cups, all at layer 0, 2.6mm3 each, 223mm3 total |
| P2609-18 | 2026-09-13 | P0099_Gutaki_Tentacles_L_S2P3_STL_2_202609132035.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Gutaki Tentacles L at default size, sliced in ELEGOO SatelLite. Printed great (Logan, 2026-09-14); not yet with Brian. Screened after printing: 38 islands, none over 1000px2 (largest 637px2 at 15.27mm; 7 over 300px2 between 14.67 and 20.46mm). 363 suction cups at layer 0, 2.6mm3 each, 931mm3 total. Adhered, where the Lychee-supported P2609-11 did not |
| P2609-17 | 2026-09-13 | P0099_Gutaki_Tentacles_R_S2P3_STL_1_202609131456.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Gutaki Tentacles R at default size, sliced in ELEGOO SatelLite. Printed (Logan, 2026-09-13); outcome not yet judged. Screened after printing: 161 islands, none over 1000px2 (largest 441px2 at 23.31mm). 418 suction cups at layer 0, 2.6mm3 each, 1071mm3 total. It adhered anyway, where the two Lychee-supported attempts (P2609-10.1, -11) did not |
| P2609-16 | 2026-09-12 | P0099_Gutaki_Body_S2P3_STL_3_202609122351.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | Gutaki Body at default size, sliced in ELEGOO SatelLite. Printed successfully off the plate (Logan, 2026-09-13); not yet with Brian. Screened after printing: 150 islands, one over 1000px2 (2326px2 at 22.59mm - check that height on review), largest cup 35.5mm3 at 49.23mm. 220 suction cups at layer 0, 2.6mm3 each, 563mm3 total - more raft vacuum than P2609-15's 380mm3 in cells a quarter the size, and it still printed |
| P2609-15 | 2026-09-12 | P0099_Gutaki_Body_S2P3_STL_0.stl_0.030_2.800_2026_09_12_19_58.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | fail | Gutaki Body, default size, solid, Blueprint auto-orient and auto supports. 1931 layers = 57.9mm, ~1mm support elevation. Screened: 1 island over 1000px2 (1544px2 at 12.45mm) and largest cup 18.9mm3, both far better than the hollowed P2609-14. But 34 suction cups all start at layer 0, ~11.2mm3 each, 380mm3 total - the raft cells sealed by the low elevation. FAILED at about 70% (Logan, 2026-09-13): it adhered, then separated from its supports under pull force. 70% of 1931 layers is about layer 1350 (40.5mm), between the screen's two largest non-raft suction cups (18.9mm3 from 38.88mm, 17.2mm3 from 43.44mm) - a candidate cause, not a confirmed one. This failure is why Logan moved to ELEGOO SatelLite, whose support generation is designed for tilting-vat printers |
| P2609-14 | 2026-09-12 | P0099_Gutaki_Body_S2P3_Blueprint-Supports.stl_0.030_2.800_2026_09_12_19_37.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  |  | CANCELLED before completion. Gutaki Body at default size, hollowed, Blueprint supports. Screening found 47 suction cups, largest 3443mm3 from 23.55mm, against 2mm3 on the solid Scylla - hollowing traded islands for suction. Not run to completion |
| P2609-13 | 2026-09-12 | P0100_Scylla_Full_S2PB_STL.stl_0.030_2.800_2026_09_12_11_10.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | fail | Scylla reprint: manual supports on the raw STL, moved right, 2125 layers = 63.8mm, 2.8s. Screened after starting: suction cups down from 330 to 5, but one island of 11992px2 at 22.92mm - larger than the 8520px2 that failed on P2609-12. Printed to completion, but removing the supports left lots of surface scarring (Logan, 2026-09-14), so Scylla moves to the separate Body + Tentacles route |
| P2609-12 | 2026-09-11 | P0100_Scylla_Full_S2PB_SUP.stl_0.030_3.000_2026_09_11_20_54.goo | Dragon Resin Durable Grey | 0.03mm | 3.0s | 27.0s | 5 |  |  | fail | Scylla one-piece at true scale on vendor Lychee supports, as a whole-model test. Failed: layer defects at 17.03mm and 32.6mm. UVtools finds 318 islands, 330 suction cups and 1175 resin traps; the two largest islands are at 17.13mm and 31.71mm, matching the defects. 92% of island area is in the centre third of the plate |
| P2609-11 | 2026-09-11 | 32mm_P0099_Gutaki_Tentacles_L_S2P3_SUP.stl_#4_0.030_3.000_2026_09_11_08_36.ctb | Dragon Resin Durable Grey | 0.03mm | 3.0s | 27.0s | 5 | 0.03mm @ 0.05 |  | fail | Gutaki Tentacles L only; failed to adhere to the build plate |
| P2609-10.1 | 2026-09-10 | 32mm_P0099_Gutaki_Tentacles_R_S2P3_SUP.stl_#2_0.030_2.800_2026_09_10_21_22.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | fail | Gutaki Tentacles R; bottom parts did not connect to the supports |
| P2609-10 | 2026-09-10 | 32mm_P0099_Gutaki_Body_S2P3_SUP.stl_#1_0.030_2.800_2026_09_09_22_45.goo | Dragon Resin Durable Grey | 0.03mm | 2.9s | 27.0s | 5 |  |  | fail | Gutaki Body reprint at 2.9s set on the printer (file says 2.8s, confirmed from the runlog), new FEP. Printed, but warped during printing |
| P2609-09 | 2026-09-09 | 32mm_P0099_Gutaki_Body_S2P3_SUP.stl_#1_0.030_2.800_2026_09_09_22_45.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | fail | Gutaki Body; large body separated from the supports in the final layers. FEP release film replaced and exposure raised 0.1s to 2.9s before the next attempt |
| P2609-08 | 2026-09-09 | 32mm_P0098_Reefclaw_A_S2P3_SUP.stl_0.030_2.800_2026_09_09_18_41.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | pass | Reefclaw A/B/C |
| P2609-06 | 2026-09-09 | 32mm_P0097_Draugr_ABC_S2P3_SUP.stl_0.030_2.800_2026_09_09_09_33.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  | 3x 25mm | pass | Draugr A/B/C |
| P2609-03 | 2026-09-08 | 32mm_P0095_Rigger_S2P3_SUP.stl_0.030_2.800_2026_09_08_15_54.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  | 12x 25mm | Rigger + Subaquatic Marauder; 1824 layers |  |
| P2609-02 | 2026-09-08 | 32mm_P0094_Athamaru_A_S2P3_PRE.stl_0.030_2.800_2026_09_08_09_53.ctb | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 | 0.03mm @ 0.05 |  | encrypted ctb, decrypted with UVtools |  |
| P2609-01 | 2026-09-07 | 32mm_P0028_Hellknight_Signifer_S1P1_STL.stl_0.030_2.800_2026_09_07_21_29.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | reprint of P0028 after Brian rejected the original |  |
| P2609-07 | 2026-09-05 | 6x-pathfinder_base_50mm.goo | Elegoo 8K Standard Gray | 0.03mm | 1.9s | 27.0s | 4 |  | 6x 50mm | pass | bases only, no minis on this plate |
| P2609-05 | 2026-09-02 | 32mm_P0089_Cheliax_Naval_Officer_S2P2_STL.stl_0.030_1.500_2026_09_02_08_16.goo | Elegoo 8K Standard Gray | 0.03mm | 1.5s | 27.0s | 4 |  |  |  |  |
| P2609-04 | 2026-09-01 | 32mm_P0059_Horned_Dragon_Body_WP4_STL.stl_0.030_1.500_2026_09_01_12_24.goo | Elegoo 8K Standard Gray | 0.03mm | 1.5s | 27.0s | 4 |  |  | re-supported STL; the vendor _SUP mesh detached under peel force |  |
| P2608-01 | 2026-08-30 | Signifer-flotsam-captain-marauder.goo | Elegoo Abs-like 3.0 | 0.03mm | 1.9s | 27.0s | 4 |  |  |  |  |

## 202609 September Release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | A | 32mm |  | ready | P2609-02 |  |  |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | B | 32mm |  | ready | P2609-02 |  |  |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | C | 32mm |  | ready | P2609-02 |  |  |
| P0095_Rigger_S2P3 | Rigger | 25mm | main | 32mm |  | review | P2609-03 |  |  |
| P0096_Subaquatic_Marauder_S2P3 | Subaquatic Marauder | 25mm | main | 32mm |  | review | P2609-03 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | A | 32mm |  | ready | P2609-06 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | B | 32mm |  | ready | P2609-06 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | C | 32mm |  | ready | P2609-06 |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | A | 32mm |  | ready | P2609-08 |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | B | 32mm |  | ready | P2609-08 |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | C | 32mm |  | ready | P2609-08 |  |  |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Body | 32mm |  | printed | P2609-16 |  | P2609-16 printed successfully off the plate (Logan, 2026-09-13); awaiting Brian. Earlier attempts: P2609-15 (Blueprint supports) failed at ~70%, separated from its supports under pull force; P2609-14 cancelled; P2609-10 warped during printing: ridges parallel to X along the rear of the integrated base, at approx rotX 20 - the peel signature of an X-tilted flat base. Reprint tilted about Y instead, with manual supports |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Tentacles L | 32mm |  | printed | P2609-18 |  | P2609-18 printed great (Logan, 2026-09-14); awaiting Brian. Earlier attempts: failed to adhere to the build plate at 3.0s; to be manually supported |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Tentacles R | 32mm |  | printed | P2609-17 |  | P2609-17 printed (Logan, 2026-09-13), not yet judged. Earlier attempts: failed to adhere to the build plate; to be manually supported |
| P0100_Scylla_S2PB | Scylla | 75mm | Body | 32mm |  | ready | P2609-20 |  | sliced on P2609-20 with new supports, after the one-piece Full scarred on support removal (Logan, 2026-09-14) |
| P0100_Scylla_S2PB | Scylla | 75mm | Full | 32mm |  | skipped | P2609-13 | fail | P2609-13 printed, but support removal left lots of surface scarring (Logan, 2026-09-14). Route switched to Body + Tentacles with new supports (P2609-20). Earlier, on P2609-12: layer defects at 17.03mm and 32.6mm, on the back left third OF THE MODEL. UVtools island detection on P2609-12 finds the print's two largest islands at 17.13mm (1196px2) and 31.71mm (8520px2) - the defects sit on them. A support-adequacy problem that travels with the model, not a plate region. Reprinting with manual supports |
| P0100_Scylla_S2PB | Scylla | 75mm | Tentacles | 32mm |  | ready | P2609-20 |  | sliced on P2609-20 with new supports, after the one-piece Full scarred on support removal (Logan, 2026-09-14) |

## 202608 August Release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | A | 32mm |  | printed |  | pass |  |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | B | 32mm |  | printed |  | pass |  |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | C | 32mm |  | printed |  | pass |  |
| P0089_Cheliax_Naval_Officer_S2P2 | Cheliax Naval Officer | 25mm | main | 32mm |  | review | P2609-05 |  |  |
| P0090_Cheliax_Naval_Captain_S2P2 | Cheliax Naval Captain | 25mm | main | 32mm |  | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | A | 32mm |  | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | B | 32mm |  | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | C | 32mm |  | printed |  | pass |  |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Arms | 32mm |  | skipped |  |  | printed as the combined Full instead |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Body | 32mm |  | skipped |  |  | printed as the combined Full instead |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Full | 32mm |  | printed |  | pass |  |
| P0093_Living_Waterfall_S2P2 | Living Waterfall | 50mm | main | 32mm |  | sliced | P2609-23 |  | Printed from the 32mm mesh, which for this model is a scaled-up 50mm and comes out too large (Logan, 2026-09-15). Reprinting from the standard true-scale mesh (49.69mm tall), which is the right family for a Large creature. Sliced together on 32mm-Paizo_PFQ_Signifer_Corps_A_1_202609152022.goo (the identical slice, re-saved at 08:30 on 2026-09-16, went to the printer as P2609-23 and is printing): 1697 layers = 50.91mm. Screened before printing: 348 islands, none over 1000px2 (largest 401px2 at 17.40mm); largest suction cups 9.3mm3 from 41.04mm, 5.5mm3 from 14.01mm, 4.6mm3 from 37.98mm |
| P0093_Living_Waterfall_S2P2 | Living Waterfall | 50mm | main | 50mm | extra | todo |  |  | scaled up in Chitubox for use as a monster; kept alongside the 32mm print |

## 202608 August extras sale

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030A1 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030A2 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030B1 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030B2 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030C1 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030C2 | 32mm |  | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | Hellknight Chargers | 50mm | PQ0030D | 32mm |  | printed |  | pass |  |
| PQ0041_Dread_Zombie | Dread Zombie | 25mm | Zombie | 32mm |  | printed |  | pass |  |
| PQ0041_Dread_Zombie | Dread Zombie | 25mm | Zombie (32mm) | 32mm |  | printed |  | pass |  |
| Paizo_Augustana_irregulars_A_Supported | Augustana Irregulars | 25mm | A | 32mm |  | ready | P2609-21 |  | Reprint reason, from Logan's recollection (not certain): the first print was probably too small. Planned reprint (2026-09-14): vendor mesh exported from Lychee without supports and supported in ELEGOO SatelLite, to compare against the vendor's Lychee supports. First exports measured A at 100% (28mm) and B/C at 112%. Re-exported together as 32mm-Paizo_PFQ_Augustana_irregulars_ABC.stl (2026-09-15): all three measure exactly 114% of the vendor mesh, and it is sliced as 32mm-Paizo_PFQ_Augustana_irregulars_ABC_1_202609150901.goo (the identical slice, re-saved at 09:05, went to the printer as P2609-21). Screened before printing: 407 islands, none over 1000px2 (largest 756px2 at 28.20mm; 10 over 300px2), largest suction cups the 2.6mm3 raft cells |
| Paizo_Augustana_irregulars_A_Supported | Augustana Irregulars | 25mm | B | 32mm |  | ready | P2609-21 |  | Reprint reason, from Logan's recollection (not certain): the first print was probably too small. Planned reprint (2026-09-14): vendor mesh exported from Lychee without supports and supported in ELEGOO SatelLite, to compare against the vendor's Lychee supports. First exports measured A at 100% (28mm) and B/C at 112%. Re-exported together as 32mm-Paizo_PFQ_Augustana_irregulars_ABC.stl (2026-09-15): all three measure exactly 114% of the vendor mesh, and it is sliced as 32mm-Paizo_PFQ_Augustana_irregulars_ABC_1_202609150901.goo (the identical slice, re-saved at 09:05, went to the printer as P2609-21). Screened before printing: 407 islands, none over 1000px2 (largest 756px2 at 28.20mm; 10 over 300px2), largest suction cups the 2.6mm3 raft cells |
| Paizo_Augustana_irregulars_A_Supported | Augustana Irregulars | 25mm | C | 32mm |  | ready | P2609-21 |  | Reprint reason, from Logan's recollection (not certain): the first print was probably too small. Planned reprint (2026-09-14): vendor mesh exported from Lychee without supports and supported in ELEGOO SatelLite, to compare against the vendor's Lychee supports. First exports measured A at 100% (28mm) and B/C at 112%. Re-exported together as 32mm-Paizo_PFQ_Augustana_irregulars_ABC.stl (2026-09-15): all three measure exactly 114% of the vendor mesh, and it is sliced as 32mm-Paizo_PFQ_Augustana_irregulars_ABC_1_202609150901.goo (the identical slice, re-saved at 09:05, went to the printer as P2609-21). Screened before printing: 407 islands, none over 1000px2 (largest 756px2 at 28.20mm; 10 over 300px2), largest suction cups the 2.6mm3 raft cells |
| Paizo_Grave_Knight_Supported | Graveknight | 25mm | main | 32mm |  | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Hellknight Sharpshooters | 25mm | SharpshootersA3 | 32mm |  | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Hellknight Sharpshooters | 25mm | SharpshootersB3 | 32mm |  | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Hellknight Sharpshooters | 25mm | SharpshootersC3 | 32mm |  | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Ironkettle's Wall | 25mm | wallA | 32mm |  | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Ironkettle's Wall | 25mm | wallB | 32mm |  | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Ironkettle's Wall | 25mm | wallC | 32mm |  | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Merandal's Hawks | 25mm | A | 32mm |  | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Merandal's Hawks | 25mm | B | 32mm |  | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Merandal's Hawks | 25mm | C | 32mm |  | printed |  | pass |  |
| Paizo_Signifers_Supported | Hellknight Signifers | 25mm | A | 32mm |  | sliced | P2609-23 |  | Reprint reason (Logan, 2026-09-15): printed too small, the 114% scale-up missed, the same as the Augustana Irregulars and Bastions. Re-exported from Lychee without supports as 32mm-Paizo_PFQ_Signifer_Corps_A.stl, measured at exactly 114% of the vendor mesh, and re-supported in ELEGOO SatelLite. Sliced together on 32mm-Paizo_PFQ_Signifer_Corps_A_1_202609152022.goo (the identical slice, re-saved at 08:30 on 2026-09-16, went to the printer as P2609-23 and is printing): 1697 layers = 50.91mm. Screened before printing: 348 islands, none over 1000px2 (largest 401px2 at 17.40mm); largest suction cups 9.3mm3 from 41.04mm, 5.5mm3 from 14.01mm, 4.6mm3 from 37.98mm |
| Paizo_Signifers_Supported | Hellknight Signifers | 25mm | B | 32mm |  | printed |  | pass | Flag, not a verdict (2026-09-15): A was reprinted for being too small from a missed 114% scale-up, so B and C may have the same problem. Check their size before treating them as good; stage and Result left as they were |
| Paizo_Signifers_Supported | Hellknight Signifers | 25mm | C | 32mm |  | printed |  | pass | Flag, not a verdict (2026-09-15): A was reprinted for being too small from a missed 114% scale-up, so B and C may have the same problem. Check their size before treating them as good; stage and Result left as they were |
| Paizo_bastions_Supported | Hellknight Bastions | 25mm | A supp | 32mm |  | ready | P2609-22 |  | Reprint reason, from Logan (2026-09-14, a best guess): the first print was probably too small, most likely not scaled up from the 28mm mesh. Check the scale before slicing the reprint. Reprint prepared 2026-09-15 the same way as the Augustana Irregulars: vendor meshes exported from Lychee without supports (32mm-Paizo_PFQ_bastion_A/B/C.stl) and supported in ELEGOO SatelLite. All three exports measure exactly 114% of the vendor mesh. Sliced as 32mm-Paizo_PFQ_bastion_ABC_1_202609150930.goo (the identical slice, re-saved at 20:04, went to the printer as P2609-22): 1479 layers = 44.37mm, which is B at 114% (38.38mm) plus the 6mm lift. Screened before printing: 1488 islands, none over 1000px2 (largest 700px2 at 21.57mm; 6 over 300px2). Largest suction cups above the raft 8.8mm3 from 36.33mm and 6.4mm3 from 32.40mm - worth a look at those heights, about half the cups that bracketed P2609-15's failure |
| Paizo_bastions_Supported | Hellknight Bastions | 25mm | B | 32mm |  | ready | P2609-22 |  | Reprint reason, from Logan (2026-09-14, a best guess): the first print was probably too small, most likely not scaled up from the 28mm mesh. Check the scale before slicing the reprint. Reprint prepared 2026-09-15 the same way as the Augustana Irregulars: vendor meshes exported from Lychee without supports (32mm-Paizo_PFQ_bastion_A/B/C.stl) and supported in ELEGOO SatelLite. All three exports measure exactly 114% of the vendor mesh. Sliced as 32mm-Paizo_PFQ_bastion_ABC_1_202609150930.goo (the identical slice, re-saved at 20:04, went to the printer as P2609-22): 1479 layers = 44.37mm, which is B at 114% (38.38mm) plus the 6mm lift. Screened before printing: 1488 islands, none over 1000px2 (largest 700px2 at 21.57mm; 6 over 300px2). Largest suction cups above the raft 8.8mm3 from 36.33mm and 6.4mm3 from 32.40mm - worth a look at those heights, about half the cups that bracketed P2609-15's failure |
| Paizo_bastions_Supported | Hellknight Bastions | 25mm | C | 32mm |  | ready | P2609-22 |  | Reprint reason, from Logan (2026-09-14, a best guess): the first print was probably too small, most likely not scaled up from the 28mm mesh. Check the scale before slicing the reprint. Reprint prepared 2026-09-15 the same way as the Augustana Irregulars: vendor meshes exported from Lychee without supports (32mm-Paizo_PFQ_bastion_A/B/C.stl) and supported in ELEGOO SatelLite. All three exports measure exactly 114% of the vendor mesh. Sliced as 32mm-Paizo_PFQ_bastion_ABC_1_202609150930.goo (the identical slice, re-saved at 20:04, went to the printer as P2609-22): 1479 layers = 44.37mm, which is B at 114% (38.38mm) plus the 6mm lift. Screened before printing: 1488 islands, none over 1000px2 (largest 700px2 at 21.57mm; 6 over 300px2). Largest suction cups above the raft 8.8mm3 from 36.33mm and 6.4mm3 from 32.40mm - worth a look at those heights, about half the cups that bracketed P2609-15's failure |
| Paizo_cave_bear_Supported | Cave Bear | 50mm | main | 32mm |  | printed |  | pass |  |
| Paizo_elk_Supported | Elk | 25mm | main | 32mm |  | printed |  | pass |  |
| Paizo_fire_serpent__Supported | Fire Serpent | 50mm | main | 32mm |  | printed |  | pass |  |
| Paizo_goblin_spellcaster_Supported | Goblin Spellcaster (Pathfinder Quest) | 25mm | main | 32mm |  | printed |  | pass |  |
| Paizo_orc_malee_Supported | Orc Melee (Pathfinder Quest) | 25mm | 32mm Paizo PFQ orc malee | 32mm |  | printed |  | pass |  |
| Paizo_orc_malee_Supported | Orc Melee (Pathfinder Quest) | 25mm | Paizo PFQ orc malee Supported | 32mm |  | printed |  | pass |  |

## 202607 July release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0055_Alchemist_Fumbus_WP4 | Fumbus, Iconic Alchemist | 25mm | main | 32mm |  | printed |  | pass |  |
| P0056_Barbarian_Amiri_WP4 | Amiri, Iconic Barbarian | 25mm | main | 32mm |  | printed |  | pass |  |
| P0057_Champion_Seelah_WP4 | Seelah, Iconic Paladin | 25mm | main | 32mm |  | printed |  | pass |  |
| P0058_Investigator_Quinn_WP4 | Quinn, Iconic Investigator | 25mm | main | 32mm |  | printed |  | pass |  |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | Body | 32mm |  | reprint | P2609-04 | fail | reprinted 2026-09-01 at 1.5s from the 32mm heroic mesh; Brian reports the rocks and wings do not fit it. Whole set being reprinted with manual supports. Reprint from the STANDARD (true-scale) mesh, not the 32mm one (Logan, 2026-09-16): the whole set goes standard so the dragon is not larger than its 50mm base. On this model the 32mm meshes measure 1.150x the standard ones on all four parts, which is exactly the mismatch that stopped these fitting. Sliced 2026-09-16 on P0059_Horned_Dragon_Body_Rock_WP4_STL_2_202609160848.goo (in sweeps/, not yet on the printer): 2653 layers = 79.59mm, which is the 73.60mm standard body plus a ~6mm lift, confirming the standard family. SCREENED before printing, verdict FIX: one island of 1132px2 at 74.49mm, about 68.5mm up the body once the lift is subtracted, near its top. 747 islands in all; the next largest are 680px2 at 26.79mm and 648px2 at 67.38mm. Cups are unremarkable, the largest 6.3mm3 at 42.87mm, below the 15mm3 flag. The 1000px2 threshold came from Lychee supports and has since been printed through twice on SatelLite EVO supports (P2609-16, P2609-20), so treat 74.49mm as a height to inspect rather than a predicted failure. NOT in the flagged queue: the slice has no plate yet, so no verdict.tsv was written |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | Rocks | 32mm |  | reprint |  | fail | does not fit the reprinted 32mm heroic body, so this was likely printed full size while the body was not. Reprint from the STANDARD (true-scale) mesh, not the 32mm one (Logan, 2026-09-16): the whole set goes standard so the dragon is not larger than its 50mm base. On this model the 32mm meshes measure 1.150x the standard ones on all four parts, which is exactly the mismatch that stopped these fitting. Sliced 2026-09-16 on P0059_Horned_Dragon_Body_Rock_WP4_STL_2_202609160848.goo (in sweeps/, not yet on the printer): 2653 layers = 79.59mm, which is the 73.60mm standard body plus a ~6mm lift, confirming the standard family. SCREENED before printing, verdict FIX: one island of 1132px2 at 74.49mm, about 68.5mm up the body once the lift is subtracted, near its top. 747 islands in all; the next largest are 680px2 at 26.79mm and 648px2 at 67.38mm. Cups are unremarkable, the largest 6.3mm3 at 42.87mm, below the 15mm3 flag. The 1000px2 threshold came from Lychee supports and has since been printed through twice on SatelLite EVO supports (P2609-16, P2609-20), so treat 74.49mm as a height to inspect rather than a predicted failure. NOT in the flagged queue: the slice has no plate yet, so no verdict.tsv was written |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | WingL | 32mm |  | reprint |  | fail | does not fit the reprinted 32mm heroic body; likely printed full size while the body was not. Reprint from the STANDARD (true-scale) mesh, not the 32mm one (Logan, 2026-09-16): the whole set goes standard so the dragon is not larger than its 50mm base. On this model the 32mm meshes measure 1.150x the standard ones on all four parts, which is exactly the mismatch that stopped these fitting. Sliced 2026-09-16 on P0059_Horned_Dragon_Wing_L_R_WP4_STL_1_202609160850.goo (in sweeps/, not yet on the printer): 3108 layers = 93.24mm against the 88.19mm standard WingL, confirming the standard family. SCREENED before printing, verdict FIX on BOTH counts. Suction cups are the serious one, measured over four detection runs: ONE dominant pocket of ~135mm3 spanning 42.51-58.6mm, footprint 23.6x23.2mm at plate X 85.7-109.3 Y 16.4-39.6, holding about 60% of the 223mm3 trapped above the raft on this plate. Runs B and D agree to 0.6% (136.0 and 135.2mm3, same start and footprint); the first run through `screen` split that one cavity into pieces and reported 115.5mm3 from 46.50mm, so treat the screen's per-cup list as indicative and its totals as solid. For scale, above the raft: everything that printed successfully here tops out at 102.4mm3 (P2609-16, largest cup 35.5mm3), and the P2609-15 failure had 48.2mm3. This plate is 2.2x the former and its single pocket is 4x the largest cup ever recorded. Note the classes overlap - P2609-16 printed fine with twice P2609-15's trapped volume - so this is "far outside anything on record", not a predicted failure. Also one island of 1033px2 at 68.67mm (about 62.7mm up the part) among 510, and 2280 resin traps. Islands have printed through twice on EVO supports, but no support recipe drains a trapped pocket: consider drain holes or a different orientation before running this. NOT in the flagged queue: the slice has no plate yet, so no verdict.tsv was written |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | WingR | 32mm |  | reprint |  | fail | does not fit the reprinted 32mm heroic body; likely printed full size while the body was not. Reprint from the STANDARD (true-scale) mesh, not the 32mm one (Logan, 2026-09-16): the whole set goes standard so the dragon is not larger than its 50mm base. On this model the 32mm meshes measure 1.150x the standard ones on all four parts, which is exactly the mismatch that stopped these fitting. Sliced 2026-09-16 on P0059_Horned_Dragon_Wing_L_R_WP4_STL_1_202609160850.goo (in sweeps/, not yet on the printer): 3108 layers = 93.24mm against the 88.19mm standard WingL, confirming the standard family. SCREENED before printing, verdict FIX on BOTH counts. Suction cups are the serious one, measured over four detection runs: ONE dominant pocket of ~135mm3 spanning 42.51-58.6mm, footprint 23.6x23.2mm at plate X 85.7-109.3 Y 16.4-39.6, holding about 60% of the 223mm3 trapped above the raft on this plate. Runs B and D agree to 0.6% (136.0 and 135.2mm3, same start and footprint); the first run through `screen` split that one cavity into pieces and reported 115.5mm3 from 46.50mm, so treat the screen's per-cup list as indicative and its totals as solid. For scale, above the raft: everything that printed successfully here tops out at 102.4mm3 (P2609-16, largest cup 35.5mm3), and the P2609-15 failure had 48.2mm3. This plate is 2.2x the former and its single pocket is 4x the largest cup ever recorded. Note the classes overlap - P2609-16 printed fine with twice P2609-15's trapped volume - so this is "far outside anything on record", not a predicted failure. Also one island of 1033px2 at 68.67mm (about 62.7mm up the part) among 510, and 2280 resin traps. Islands have printed through twice on EVO supports, but no support recipe drains a trapped pocket: consider drain holes or a different orientation before running this. NOT in the flagged queue: the slice has no plate yet, so no verdict.tsv was written |
| P0060_Vrolikai_Demon_WP4 | Vrolikai Demon | 50mm | main | 32mm |  | printed |  | pass |  |
| P0061_Goblin_Pyro_WP4 | Goblin Pyro | 25mm | main | 32mm |  | printed |  | pass |  |
| P0062_Goblin_Warrior_WP4 | Goblin Warrior | 25mm | main | 32mm |  | printed |  | pass |  |
| P0063_Goblin_Commando_WP4 | Goblin Commando | 25mm | Barrel | 32mm |  | printed |  | pass |  |
| P0063_Goblin_Commando_WP4 | Goblin Commando | 25mm | main | 32mm |  | printed |  | pass |  |
| P0064_Goblin_Chanter_WP4 | Goblin Chanter | 25mm | main | 32mm |  | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | A | 32mm |  | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | B | 32mm |  | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | C | 32mm |  | printed |  | pass |  |
| P0083_Marine_Marauder_S2P1 | Marine Marauder | 25mm | main | 32mm |  | review | P2608-01 |  |  |
| P0084_Ocean_Nomad_S2P1 | Ocean Nomad | 25mm | main | 32mm |  | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | A | 32mm |  | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | B | 32mm |  | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | C | 32mm |  | printed |  | pass |  |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Body | 32mm |  | printed |  | pass |  |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Full | 32mm |  | skipped |  |  | printed as Body + Tentacles instead |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Tentacles | 32mm |  | printed |  | pass |  |
| P0087_Sargassum_Heap_S2P1 | Sargassum Heap | 50mm | main | 32mm |  | printed |  | pass |  |

## 202606 June Release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0043_Brastlewark_Snarecrafter_S1P3 | Brastlewark Snarecrafter | 25mm | main | 32mm |  | sliced | P2609-23 |  | printed too small: sliced from the full-size (true scale) mesh instead of the 32mm heroic one. Reprint from 32mm_P0043_Brastlewark_Snarecrafter_S1P3_SUP.stl Reprint prepared 2026-09-15: the 32mm heroic mesh re-supported in ELEGOO SatelLite (Logan). Sliced together on 32mm-Paizo_PFQ_Signifer_Corps_A_1_202609152022.goo (the identical slice, re-saved at 08:30 on 2026-09-16, went to the printer as P2609-23 and is printing): 1697 layers = 50.91mm. Screened before printing: 348 islands, none over 1000px2 (largest 401px2 at 17.40mm); largest suction cups 9.3mm3 from 41.04mm, 5.5mm3 from 14.01mm, 4.6mm3 from 37.98mm |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Arm | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Body | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Cape | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | B Arm | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | B Body | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | C Arm | 32mm |  | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | C Body | 32mm |  | printed |  | pass |  |
| P0045_Twilight_Talon_S1P3 | Twilight Talon | 25mm | main | 32mm |  | printed |  | pass |  |
| P0046_Skeletal_Hellknight_Bonesinger_S1P3 | Skeletal Hellknight Bonesinger | 25mm | Fixed Hand | 32mm |  | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | A | 32mm |  | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | B | 32mm |  | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | C | 32mm |  | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | Body | 32mm |  | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | WingL | 32mm |  | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | WingR | 32mm |  | printed |  | pass |  |
| P0049_Abrogail Adamant_S1PB | Abrogail Adamant | 75mm | Body | 32mm |  | printed |  | pass |  |
| P0049_Abrogail Adamant_S1PB | Abrogail Adamant | 75mm | Legs | 32mm |  | printed |  | pass |  |
| P0050_Abrogail Thrune_S1PB | Abrogail Thrune | 25mm | main | 32mm |  | printed |  | pass |  |

## 202605 May Release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | A | 32mm |  | printed |  | pass |  |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | B | 32mm |  | printed |  | pass |  |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | C | 32mm |  | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | A | 32mm |  | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | B | 32mm |  | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | C | 32mm |  | printed |  | pass |  |
| 1-P0035_Gylou_S1P2 | Gylou (Handmaiden Devil) | 25mm | body | 32mm |  | printed |  | pass |  |
| 1-P0035_Gylou_S1P2 | Gylou (Handmaiden Devil) | 25mm | tentacles | 32mm |  | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Body | 32mm |  | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Horn L | 32mm |  | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Horn R | 32mm |  | printed |  | pass |  |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | Wing | 32mm |  | printed |  | pass |  |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | Wing | 50mm | extra | todo |  |  | scaled up in Chitubox for use as a monster; kept alongside the 32mm print |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | body | 32mm |  | printed |  | pass |  |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | body | 50mm | extra | todo |  |  | scaled up in Chitubox for use as a monster; kept alongside the 32mm print |
| 2-P0038_Balisse_Angel_WP2 | Balisse Angel | 25mm | main | 32mm |  | printed |  | pass |  |
| 2-P0039_Hellbreaker_S1P2 | Hellbreaker | 25mm | main | 32mm |  | printed |  | pass |  |
| 2-P0040_Leukodaemon_WP2 | Leukodaemon | 50mm | main | 32mm |  | printed |  | pass |  |
| 2-P0041_Rekhep_Archon_WP2 | Rekhep Archon | 50mm | main | 32mm |  | printed |  | pass |  |
| 3-P0026_Andoran Golden Legionnaire_S1P1 | Andoran Golden Legionnaire | 25mm | main | 32mm |  | printed |  | pass |  |
| 3-P0027_Andoran Steel Falcon_S1P1 | Andoran Steel Falcon | 25mm | main | 32mm |  | printed |  | pass |  |
| 3-P0028_Hellknight Signifer_S1P1 | Hellknight Signifer | 25mm | main | 32mm |  | review | P2609-01 |  | Brian rejected the first print: fingers of the left hand did not print properly. Reprinted 2026-09-07 on P2609-01 |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm L | 32mm |  | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm R | 32mm |  | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm head | 32mm |  | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | body | 32mm |  | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | shoulder | 32mm |  | printed |  | pass |  |
| 4-P0042_Vidileth_WP2_STL | Vidileth Alghollthu | 50mm | main | 32mm |  | printed |  | pass |  |
| 4-P0042_Vidileth_WP2_STL | Vidileth Alghollthu | 50mm | with Base | 32mm |  | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | A | 32mm |  | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | B | 32mm |  | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | C | 32mm |  | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Arm L | 32mm |  | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Arm R | 32mm |  | printed | P2609-19 |  | P2609-19 reprint printed successfully (Logan, 2026-09-14); awaiting Brian. Rejected earlier for: flat spot on one tentacle |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Body | 32mm |  | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Tail | 32mm |  | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Tail with Base | 32mm |  | printed |  | pass |  |

## 202604 April Release

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0001_Ezren_Iconic_Wizard_WP1 | Ezren, Iconic Wizard | 25mm | main | 32mm |  | printed |  | pass |  |
| P0002_Kyra_Iconic_Fighter_WP1 | Kyra, Iconic Cleric | 25mm | main | 32mm |  | printed |  | pass |  |
| P0003_Merisiel_Iconic_Rogue_WP1 | Merisiel, Iconic Rogue | 25mm | main | 32mm |  | printed |  | pass |  |
| P0004_Valeros_Iconic_Fighter_WP1 | Valeros, Iconic Fighter | 25mm | main | 32mm |  | printed |  | pass |  |
| P0005_Lem_Iconic_Bard_WP1 | Lem, Iconic Bard | 25mm | main | 32mm |  | printed |  | pass |  |
| P0006_Lini_Iconic_Druid_with_Droogami_WP1 | Lini, Iconic Druid (with Droogami) | 25mm | Droogami | 32mm |  | printed |  | pass |  |
| P0006_Lini_Iconic_Druid_with_Droogami_WP1 | Lini, Iconic Druid (with Droogami) | 25mm | main | 32mm |  | printed |  | pass |  |
| P0007_Harsk_Iconic_Ranger_WP1 | Harsk, Iconic Ranger | 25mm | main | 32mm |  | printed |  | pass |  |
| P0008_Feiya_Iconic_Witch_with_Daji_WP1 | Feiya, Iconic Witch (with Daji) | 25mm | Fox | 32mm |  | printed |  | pass |  |
| P0008_Feiya_Iconic_Witch_with_Daji_WP1 | Feiya, Iconic Witch (with Daji) | 25mm | main | 32mm |  | printed |  | pass |  |
| P0012_Boggard Warrior_WP1 | Boggard Warrior | 25mm | main | 32mm |  | printed |  | pass |  |
| P0013_Boggard Swampseer_WP1 | Boggard Swampseer | 25mm | main | 32mm |  | printed |  | pass |  |
| P0014_Boggard Scout_WP1 | Boggard Scout | 25mm | main | 32mm |  | printed |  | pass |  |
| P0015_Rain in Cloudy Day_WP1 | Rain in Cloudy Day | 25mm | main | 32mm |  | printed |  | pass |  |
| P0016_Giant Rat_WP1 | Giant Rat | 25mm | main | 32mm |  | printed |  | pass |  |
| P0017_Giant Spider_WP1 | Giant Spider | 25mm | main | 32mm |  | printed |  | pass |  |
| P0018_Skeleton Guard_WP1 | Skeleton Guard | 25mm | main | 32mm |  | printed |  | pass |  |
| P0019_Kobold Warrior_WP1 | Kobold Warrior | 25mm | main | 32mm |  | printed |  | pass |  |
| P0020_Kobold Trapmaster_WP1 | Kobold Trapmaster | 25mm | main | 32mm |  | printed |  | pass |  |
| P0021_Kobold Scout_WP1 | Kobold Scout | 25mm | main | 32mm |  | printed |  | pass |  |
| P0022_Cinder Rat_WP1 | Cinder Rat | 25mm | main | 32mm |  | printed |  | pass |  |
| P0023_Xulgath Warrior_WP1 | Xulgath Warrior | 25mm | main | 32mm |  | printed |  | pass |  |
| P0024_Zolgran Kobold Boss_WP1 | Zolgran, Kobold Boss | 25mm | main | 32mm |  | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | A | 32mm |  | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | B | 32mm |  | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | C | 32mm |  | printed |  | pass |  |
| Paizo_lurker_in_light__Supported | Paizo_lurker_in_light__Supported | 25mm | main | 32mm |  | printed |  | pass |  |

## 202604 Dragons

| Model | Mini | Base | Part | Scale | Kind | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Base | 32mm |  | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Body | 32mm |  | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Head | 32mm |  | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Wing L | 32mm |  | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Wing R | 32mm |  | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Body | 32mm |  | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Head | 32mm |  | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Wing L | 32mm |  | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Wing R | 32mm |  | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Body | 32mm |  | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Head | 32mm |  | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Tail | 32mm |  | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Wing L | 32mm |  | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Wing R | 32mm |  | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Body | 32mm |  | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Wing L | 32mm |  | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Wing R | 32mm |  | printed |  |  |  |
