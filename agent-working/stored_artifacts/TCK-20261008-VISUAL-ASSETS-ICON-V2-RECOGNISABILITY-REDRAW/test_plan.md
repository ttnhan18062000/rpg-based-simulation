---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW

- `test_icon_compliance.py`: the committed redrawn icons meet every spec row; a parametric sword fails the right row for a short blade, a grip wider than the guard, no pommel, a narrow guard and a wrong height and passes when built to the spec; a square and an 8 px bead fail the round and size rows; a boot-like sloping wall fails the U-shape row and a U-shaped wall passes it; the table is markdown with spec and measured value on every row.
- `test_icon_specs.py` / `test_icon_recognition.py`: the guide's generated table and the seven process-rule steps in order; the distractor check shares the whole-word rule with the scoring; a longbow counts for the ranger and a crossbow does not.
- `test_icon_v2_draft_set.py` and the fixture guard stay green on the refreshed `icondraft_v2/`. Mutants A to D (mutant_proof.txt). Evidence runs: compliance tables, look-alike report, two blind rounds on all 36.
