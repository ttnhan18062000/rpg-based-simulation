---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE
artifact_type: investigation
tags: [architecture, testing, live-map]
---

# Investigation — TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

- Draft previews are 128 x 128 nearest-neighbour 8x copies; the loader asserts every 8 x 8 block is one colour, then samples one pixel per block.
- Forest has no draft in terrain-v1; its adopted slots come from the committed pilot runtime export (`__fixtures__/pilot`).
- The baseline reproduces the earlier scratch run: 30 failing pair-visions of 1012 under the approved rule (S1 FAIL, S2 holds for every tile and vision, wording "worse"). Worst margin -7.97 (dungeon_entrance/floor, protan).
- Finding for the planner: forest `bush` and `tree` (adopted, never redrawn, not in the verdict) are within 1.3 to 3.8 dE of another terrain's tile mean under protan/deutan (min dE to others: bush protan 1.81, tree protan 1.27). Informational only.
- `stored_artifacts/**/*.json` is gitignored, so the baseline is stored as `baseline_terrain_v1.txt` (JSON text).
