# Resin test log: Siraya Fast + Tenacious blend (Mars 5 Ultra)

Recorded: 2026-10-10 (from a Claude chat session, not the ledger session).
Printer: Elegoo Mars 5 Ultra (9K, tilting vat). Layer height: 30 um.
Also saved in the claude.ai Project "Resin Printing" as claude/resin-fast-tenacious-blend-test.md.

## Goal
Find a more easily sourced alternative to Dragon Resin "Durable Grey" for tabletop minis. Compare printed minis across resins. The same mini set was already printed in Dragon and in straight Fast.

## Reference: Dragon Durable Grey (target)
Tensile yield 45 MPa / break 36 MPa, elongation 35%, Shore 83D, modulus 2090 MPa, Izod 41 J/m, HDT 52C, viscosity 450 cPs. Dragon's own Mars 5 profile (AA off, turbo): ~2.5-3.0 s at 30 um, bottom 25-30 s, 5 bottom layers. Different resin, so only a rough baseline.

## Current mix (as measured by Logan)
- Siraya Tech Fast (grey): ~181 g
- Siraya Tech Tenacious: ~31 g
- Total ~212 g; Tenacious is ~14.6% by weight (about 15%, not the 10% first planned).
- Fills the Mars 5 Ultra vat about half way.
- Mixed by weight. Warm, stir thoroughly, let bubbles settle before printing.

## Known baseline
- Straight Fast at 30 um: calibrated optimal layer exposure = 1.9 s (Logan's own calibration).
- Siraya's published Fast guide (50 um, Creality printers): 2.25-2.5 s normal, 33-35 s bottom, 5 bottom layers. Fast Navy Grey needs ~20% longer exposure.

## Planned calibration (cones of calibration)
Estimate only (no published data for this blend): Tenacious is softer, so the blend probably needs ~10-30% more exposure than straight Fast (~2.1-2.5 s), but could land near 1.9 s.

Six test exposures (s): 1.9, 2.1, 2.3, 2.5, 2.7, 2.9
- Pick the shortest exposure with sharp cone tips, then refine in 0.1 s steps.
- Overexposure: bloated tips, lost fine detail. Underexposure: missing/soft tips, weak adhesion.
- Raise bottom exposure ~10-15% vs straight Fast; use slow lift speeds (blend is more viscous).
- Keep the vat above ~20C.

## Results
Recorded 2026-10-10 from Logan's report after the cones-of-calibration test on the ~15% Tenacious mix (181 g Fast + 31 g Tenacious), Mars 5 Ultra, 30 um.

- **Preferred exposure for this blend: 2.1 s.** Best cone result.
- 1.9 s was also very good (Logan: "2.1 was the best but 1.9 was also very good").
- Not recorded: results for 2.3, 2.5, 2.7, 2.9 s (Logan gave none), cone-tip detail, temperature. Fill these in only from Logan's statements.
- Logan's note: variance on pure Fast is small. The ledger has straight-Fast plates at 1.8 s while Logan's own calibration said 1.9 s; treat that gap as within normal variance, not an error.
- 2.1 s is ~10% above straight Fast (1.9 s), the low end of the predicted 10-30% increase. The blend is not very sensitive to exposure between 1.9 and 2.1 s.

Decided (Logan, 2026-10-10): blend plates use 5 bottom layers, matching the Dragon plates (the Fast plates used 2).

Decided (Logan, 2026-10-10): slicer profile name is "Fast + 15% Tenacious" (the ledger takes the resin from the profile name in the sliced file). Bottom exposure is 27 s, same as the Dragon plates.

Blend plate settings, 30 um: 2.1 s normal, 27 s bottom, 5 bottom layers.

## Comparison plan
- Print the same mini set as before (Dragon, straight Fast) with the same orientation, supports, wash and post-cure.
- Possibly also an Elegoo 8K Standard run (currently in the vat): print it first, then clean vat and film with IPA before the blend so the blend is not contaminated.
- Log per resin: exposure, temperature, failures, breakage on thin parts, handling feel.

## Notes and corrections
- Siraya's own Fast user guide lists: Shore 75D, tensile 31 MPa, elongation 7%, modulus 1100 MPa, Izod 25 J/m, HDT 65C, shrinkage 6% by volume. It says Fast is not a tough resin and suggests mixing with Blu/Tenacious for impact resistance. A retailer listing (MatterHackers) showed softer values (65D, 24 MPa, 50% elongation); these conflict, so treat the Siraya guide as more reliable. Fast is likely more brittle than Dragon.
- Other Dragon substitutes considered: Siraya Magna Durable Grey (42 MPa yield, 65% elongation, 74D), Siraya Blu Nylon Mecha (82D, 58 MPa, 37%; sold in white), Elegoo ABS-Like 3.0 (~24% elongation, ~86-88D, 72.4 J/m), Elegoo 8K Standard (~9.4% elongation, brittle).
- Some specs come from secondary sources; verify against current datasheets before buying.
