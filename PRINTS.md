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

## Plates

| ID | Date | Slicer file | Resin | Layer | Exposure | Bottom exp | Bottom layers | Lift | Bases | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2608-01 | 2026-08-30 | Signifer-flotsam-captain-marauder.goo | Elegoo Abs-like 3.0 | 0.03mm | 1.9s | 27.0s | 4 |  |  |  |  |
| P2609-04 | 2026-09-01 | 32mm_P0059_Horned_Dragon_Body_WP4_STL.stl_0.030_1.500_2026_09_01_12_24.goo | Elegoo 8K Standard Gray | 0.03mm | 1.5s | 27.0s | 4 |  |  | re-supported STL; the vendor _SUP mesh detached under peel force |  |
| P2609-05 | 2026-09-02 | 32mm_P0089_Cheliax_Naval_Officer_S2P2_STL.stl_0.030_1.500_2026_09_02_08_16.goo | Elegoo 8K Standard Gray | 0.03mm | 1.5s | 27.0s | 4 |  |  |  |  |
| P2609-01 | 2026-09-07 | 32mm_P0028_Hellknight_Signifer_S1P1_STL.stl_0.030_2.800_2026_09_07_21_29.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  |  | reprint of P0028 after Brian rejected the original |  |
| P2609-02 | 2026-09-08 | 32mm_P0094_Athamaru_A_S2P3_PRE.stl_0.030_2.800_2026_09_08_09_53.ctb | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 | 0.03mm @ 0.05 |  | encrypted ctb, decrypted with UVtools |  |
| P2609-03 | 2026-09-08 | 32mm_P0095_Rigger_S2P3_SUP.stl_0.030_2.800_2026_09_08_15_54.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  | 12x 25mm | Rigger + Subaquatic Marauder; 1824 layers |  |
| P2609-06 | 2026-09-09 | 32mm_P0097_Draugr_ABC_S2P3_SUP.stl_0.030_2.800_2026_09_09_09_33.goo | Dragon Resin Durable Grey | 0.03mm | 2.8s | 27.0s | 5 |  | 3x 25mm | Draugr A/B/C; in progress |  |

## 202609 September Release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | A | printed | P2609-02 |  |  |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | B | printed | P2609-02 |  |  |
| P0094_Athamaru_S2P3 | Athamaru | 25mm | C | printed | P2609-02 |  |  |
| P0095_Rigger_S2P3 | Rigger | 25mm | main | review | P2609-03 |  |  |
| P0096_Subaquatic_Marauder_S2P3 | Subaquatic Marauder | 25mm | main | review | P2609-03 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | A | sliced | P2609-06 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | B | sliced | P2609-06 |  |  |
| P0097_Draugr_S2P3 | Draugr | 25mm | C | sliced | P2609-06 |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | A | todo |  |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | B | todo |  |  |  |
| P0098_Reefclaw_S2P3 | Reefclaw | 25mm | C | todo |  |  |  |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Body | todo |  |  |  |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Tentacles L | todo |  |  |  |
| P0099_Gutaki_S2P3 | Gutaki | 50mm | Tentacles R | todo |  |  |  |
| P0100_Scylla_S2PB | Scylla | 75mm | Body | todo |  |  |  |
| P0100_Scylla_S2PB | Scylla | 75mm | Full | todo |  |  |  |
| P0100_Scylla_S2PB | Scylla | 75mm | Tentacles | todo |  |  |  |

## 202608 August Release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | A | printed |  | pass |  |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | B | printed |  | pass |  |
| P0088_Cheliax_Marine_S2P2 | Cheliax Marine | 25mm | C | printed |  | pass |  |
| P0089_Cheliax_Naval_Officer_S2P2 | Cheliax Naval Officer | 25mm | main | review | P2609-05 |  |  |
| P0090_Cheliax_Naval_Captain_S2P2 | Cheliax Naval Captain | 25mm | main | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | A | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | B | printed |  | pass |  |
| P0091_Deep_One_S2P2 | Deep One | 25mm | C | printed |  | pass |  |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Arms | printed |  | pass |  |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Body | printed |  | pass |  |
| P0092_Flotsam_Terror_S2P2 | Flotsam Terror | 25mm | Full | printed |  | pass |  |
| P0093_Living_Waterfall_S2P2 | Living Waterfall | 50mm | main | printed |  | pass |  |

## 202608 August extras sale

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030A1 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030A2 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030B1 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030B2 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030C1 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030C2 | printed |  | pass |  |
| PQ0030_Hellknight_Chargers | PQ0030_Hellknight_Chargers | 50mm | PQ0030D | printed |  | pass |  |
| PQ0041_Dread_Zombie | PQ0041_Dread_Zombie | ? | Zombie | printed |  | pass |  |
| PQ0041_Dread_Zombie | PQ0041_Dread_Zombie | ? | Zombie (32mm) | printed |  | pass |  |
| Paizo_Augustana_irregulars_A_Supported | Paizo_Augustana_irregulars_A_Supported | ? | A | printed |  | pass |  |
| Paizo_Augustana_irregulars_A_Supported | Paizo_Augustana_irregulars_A_Supported | ? | B | printed |  | pass |  |
| Paizo_Augustana_irregulars_A_Supported | Paizo_Augustana_irregulars_A_Supported | ? | C | printed |  | pass |  |
| Paizo_Grave_Knight_Supported | Paizo_Grave_Knight_Supported | ? | main | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Paizo_Hellknight_Sharpshooters_Supported | ? | SharpshootersA3 | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Paizo_Hellknight_Sharpshooters_Supported | ? | SharpshootersB3 | printed |  | pass |  |
| Paizo_Hellknight_Sharpshooters_Supported | Paizo_Hellknight_Sharpshooters_Supported | ? | SharpshootersC3 | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Paizo_Ironkettles_wall_Supported | ? | wallA | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Paizo_Ironkettles_wall_Supported | ? | wallB | printed |  | pass |  |
| Paizo_Ironkettles_wall_Supported | Paizo_Ironkettles_wall_Supported | ? | wallC | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Paizo_Merandals_Hawks_Supported | ? | A | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Paizo_Merandals_Hawks_Supported | ? | B | printed |  | pass |  |
| Paizo_Merandals_Hawks_Supported | Paizo_Merandals_Hawks_Supported | ? | C | printed |  | pass |  |
| Paizo_Signifers_Supported | Paizo_Signifers_Supported | ? | A | printed |  | pass |  |
| Paizo_Signifers_Supported | Paizo_Signifers_Supported | ? | B | printed |  | pass |  |
| Paizo_Signifers_Supported | Paizo_Signifers_Supported | ? | C | printed |  | pass |  |
| Paizo_bastions_Supported | Paizo_bastions_Supported | ? | A supp | printed |  | pass |  |
| Paizo_bastions_Supported | Paizo_bastions_Supported | ? | B | printed |  | pass |  |
| Paizo_bastions_Supported | Paizo_bastions_Supported | ? | C | printed |  | pass |  |
| Paizo_cave_bear_Supported | Paizo_cave_bear_Supported | ? | main | printed |  | pass |  |
| Paizo_elk_Supported | Paizo_elk_Supported | ? | main | printed |  | pass |  |
| Paizo_fire_serpent__Supported | Paizo_fire_serpent__Supported | ? | main | printed |  | pass |  |
| Paizo_goblin_spellcaster_Supported | Paizo_goblin_spellcaster_Supported | ? | main | printed |  | pass |  |
| Paizo_orc_malee_Supported | Paizo_orc_malee_Supported | ? | 32mm Paizo PFQ orc malee | printed |  | pass |  |
| Paizo_orc_malee_Supported | Paizo_orc_malee_Supported | ? | Paizo PFQ orc malee Supported | printed |  | pass |  |

## 202607 July release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0055_Alchemist_Fumbus_WP4 | Fumbus, Iconic Alchemist | 25mm | main | printed |  | pass |  |
| P0056_Barbarian_Amiri_WP4 | Amiri, Iconic Barbarian | 25mm | main | printed |  | pass |  |
| P0057_Champion_Seelah_WP4 | Seelah, Iconic Paladin | 25mm | main | printed |  | pass |  |
| P0058_Investigator_Quinn_WP4 | Quinn, Iconic Investigator | 25mm | main | printed |  | pass |  |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | Body | review | P2609-04 |  | vendor pre-supported mesh detached under peel force; re-supported the raw STL and reprinted 2026-09-01 at 1.5s |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | Rocks | printed |  | pass |  |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | WingL | printed |  | pass |  |
| P0059_Horned_Dragon_WP4 | Horned Dragon | 50mm | WingR | printed |  | pass |  |
| P0060_Vrolikai_Demon_WP4 | Vrolikai Demon | 50mm | main | printed |  | pass |  |
| P0061_Goblin_Pyro_WP4 | Goblin Pyro | 25mm | main | printed |  | pass |  |
| P0062_Goblin_Warrior_WP4 | Goblin Warrior | 25mm | main | printed |  | pass |  |
| P0063_Goblin_Commando_WP4 | Goblin Commando | 25mm | Barrel | printed |  | pass |  |
| P0063_Goblin_Commando_WP4 | Goblin Commando | 25mm | main | printed |  | pass |  |
| P0064_Goblin_Chanter_WP4 | Goblin Chanter | 25mm | main | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | A | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | B | printed |  | pass |  |
| P0082_Bosun_S2P1 | Bosun | 25mm | C | printed |  | pass |  |
| P0083_Marine_Marauder_S2P1 | Marine Marauder | 25mm | main | review | P2608-01 |  |  |
| P0084_Ocean_Nomad_S2P1 | Ocean Nomad | 25mm | main | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | A | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | B | printed |  | pass |  |
| P0085_Grindylow_S2P1 | Grindylow | 25mm | C | printed |  | pass |  |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Body | printed |  | pass |  |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Full | printed |  | pass |  |
| P0086_Sea_Hag_S2P1 | Sea Hag | 25mm | Tentacles | printed |  | pass |  |
| P0087_Sargassum_Heap_S2P1 | Sargassum Heap | 50mm | main | printed |  | pass |  |

## 202606 June Release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0043_Brastlewark_Snarecrafter_S1P3 | Brastlewark Snarecrafter | 25mm | main | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Arm | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Body | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | A Cape | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | B Arm | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | B Body | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | C Arm | printed |  | pass |  |
| P0044_Order_of_the_Gate_Hellknight_S1P3 | Order of the Gate Hellknight | 25mm | C Body | printed |  | pass |  |
| P0045_Twilight_Talon_S1P3 | Twilight Talon | 25mm | main | printed |  | pass |  |
| P0046_Skeletal_Hellknight_Bonesinger_S1P3 | Skeletal Hellknight Bonesinger | 25mm | Fixed Hand | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | A | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | B | printed |  | pass |  |
| P0047_Strix_S1P3 | Strix | 25mm | C | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | Body | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | WingL | printed |  | pass |  |
| P0048_Nessari_Tyrant_Devil_S1P3 | Nessari (Tyrant Devil) | 50mm | WingR | printed |  | pass |  |
| P0049_Abrogail Adamant_S1PB | Abrogail Adamant | 75mm | Body | printed |  | pass |  |
| P0049_Abrogail Adamant_S1PB | Abrogail Adamant | 75mm | Legs | printed |  | pass |  |
| P0050_Abrogail Thrune_S1PB | Abrogail Thrune | 25mm | main | printed |  | pass |  |

## 202605 May Release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | A | printed |  | pass |  |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | B | printed |  | pass |  |
| 1-P0033_Andoran_Soldier_S1P2 | Andoran Soldier | 25mm | C | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | A | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | B | printed |  | pass |  |
| 1-P0034_Cheliax_Soldier_S1P2 | Chelaxian Soldier | 25mm | C | printed |  | pass |  |
| 1-P0035_Gylou_S1P2 | Gylou (Handmaiden Devil) | 25mm | body | printed |  | pass |  |
| 1-P0035_Gylou_S1P2 | Gylou (Handmaiden Devil) | 25mm | tentacles | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Body | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Horn L | printed |  | pass |  |
| 1-P0036_Phistophilus_S1P2 | Phistophilus (Contract Devil) | 25mm | Horn R | printed |  | pass |  |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | Wing | printed |  | pass |  |
| 2-P0037_Talmandor_S1P2 | Talmandor | 50mm | body | printed |  | pass |  |
| 2-P0038_Balisse_Angel_WP2 | Balisse Angel | 25mm | main | printed |  | pass |  |
| 2-P0039_Hellbreaker_S1P2 | Hellbreaker | 25mm | main | printed |  | pass |  |
| 2-P0040_Leukodaemon_WP2 | Leukodaemon | 50mm | main | printed |  | pass |  |
| 2-P0041_Rekhep_Archon_WP2 | Rekhep Archon | 50mm | main | printed |  | pass |  |
| 3-P0026_Andoran Golden Legionnaire_S1P1 | Andoran Golden Legionnaire | 25mm | main | printed |  | pass |  |
| 3-P0027_Andoran Steel Falcon_S1P1 | Andoran Steel Falcon | 25mm | main | printed |  | pass |  |
| 3-P0028_Hellknight Signifer_S1P1 | Hellknight Signifer | 25mm | main | review | P2609-01 |  | Brian rejected the first print: fingers of the left hand did not print properly. Reprinted 2026-09-07 on P2609-01 |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm L | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm R | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | arm head | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | body | printed |  | pass |  |
| 4-P0032_Arboreal_Warden_WP2 | Arboreal Warden | 50mm | shoulder | printed |  | pass |  |
| 4-P0042_Vidileth_WP2_STL | Vidileth Alghollthu | 50mm | main | printed |  | pass |  |
| 4-P0042_Vidileth_WP2_STL | Vidileth Alghollthu | 50mm | with Base | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | A | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | B | printed |  | pass |  |
| 5-P0029_Ort Druge Devil_S1P1 | Ort (Druge Devil) | 25mm | C | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Arm L | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Arm R | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Body | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Tail | printed |  | pass |  |
| 6-P0031_Sarglagon Drowning Devil_S1P1 | Sarglagon (Drowning Devil) | 50mm | Tail with Base | printed |  | pass |  |

## 202604 April Release

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0001_Ezren_Iconic_Wizard_WP1 | Ezren, Iconic Wizard | 25mm | main | printed |  | pass |  |
| P0002_Kyra_Iconic_Fighter_WP1 | Kyra, Iconic Cleric | 25mm | main | printed |  | pass |  |
| P0003_Merisiel_Iconic_Rogue_WP1 | Merisiel, Iconic Rogue | 25mm | main | printed |  | pass |  |
| P0004_Valeros_Iconic_Fighter_WP1 | Valeros, Iconic Fighter | 25mm | main | printed |  | pass |  |
| P0005_Lem_Iconic_Bard_WP1 | Lem, Iconic Bard | 25mm | main | printed |  | pass |  |
| P0006_Lini_Iconic_Druid_with_Droogami_WP1 | Lini, Iconic Druid (with Droogami) | 25mm | Droogami | printed |  | pass |  |
| P0006_Lini_Iconic_Druid_with_Droogami_WP1 | Lini, Iconic Druid (with Droogami) | 25mm | main | printed |  | pass |  |
| P0007_Harsk_Iconic_Ranger_WP1 | Harsk, Iconic Ranger | 25mm | main | printed |  | pass |  |
| P0008_Feiya_Iconic_Witch_with_Daji_WP1 | Feiya, Iconic Witch (with Daji) | 25mm | Fox | printed |  | pass |  |
| P0008_Feiya_Iconic_Witch_with_Daji_WP1 | Feiya, Iconic Witch (with Daji) | 25mm | main | printed |  | pass |  |
| P0012_Boggard Warrior_WP1 | Boggard Warrior | 25mm | main | printed |  | pass |  |
| P0013_Boggard Swampseer_WP1 | Boggard Swampseer | 25mm | main | printed |  | pass |  |
| P0014_Boggard Scout_WP1 | Boggard Scout | 25mm | main | printed |  | pass |  |
| P0015_Rain in Cloudy Day_WP1 | Rain in Cloudy Day | 25mm | main | printed |  | pass |  |
| P0016_Giant Rat_WP1 | Giant Rat | 25mm | main | printed |  | pass |  |
| P0017_Giant Spider_WP1 | Giant Spider | 25mm | main | printed |  | pass |  |
| P0018_Skeleton Guard_WP1 | Skeleton Guard | 25mm | main | printed |  | pass |  |
| P0019_Kobold Warrior_WP1 | Kobold Warrior | 25mm | main | printed |  | pass |  |
| P0020_Kobold Trapmaster_WP1 | Kobold Trapmaster | 25mm | main | printed |  | pass |  |
| P0021_Kobold Scout_WP1 | Kobold Scout | 25mm | main | printed |  | pass |  |
| P0022_Cinder Rat_WP1 | Cinder Rat | 25mm | main | printed |  | pass |  |
| P0023_Xulgath Warrior_WP1 | Xulgath Warrior | 25mm | main | printed |  | pass |  |
| P0024_Zolgran Kobold Boss_WP1 | Zolgran, Kobold Boss | 25mm | main | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | A | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | B | printed |  | pass |  |
| P0030_Vordine Infantry Devil_S1P1 | Vordine (Infantry Devil) | 25mm | C | printed |  | pass |  |
| Paizo_lurker_in_light__Supported | Paizo_lurker_in_light__Supported | ? | main | printed |  | pass |  |

## 202604 Dragons

| Model | Mini | Base | Part | Stage | Plate | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Base | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Body | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Head | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Wing L | printed |  |  |  |
| P0009_Mirage Dragon_WP1 | Mirage Dragon | 75mm | Wing R | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Body | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Head | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Wing L | printed |  |  |  |
| P0010_Diabolic Dragon_WP1 | Diabolic Dragon | 75mm | Wing R | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Body | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Head | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Tail | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Wing L | printed |  |  |  |
| P0011_Empyreal Dragon_WP1 | Empyreal Dragon | 50mm | Wing R | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Body | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Wing L | printed |  |  |  |
| P0025_Horned_Dragon_WP1 | Horned Dragon | 25mm | Wing R | printed |  |  |  |
