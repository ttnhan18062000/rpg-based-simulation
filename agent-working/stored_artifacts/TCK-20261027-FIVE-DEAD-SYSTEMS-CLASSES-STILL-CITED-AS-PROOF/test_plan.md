---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF
artifact_type: test_plan
tags: [world, engine]
---

# Test plan (written at close)

| Check | Result |
|---|---|
| `tests/unit/resource/test_loot_live_path.py` (6 tests, live path, positive controls) | pass |
| `tests/integration/economy/test_crafting_live_path.py` (6 tests, each gate positive-controlled) | pass |
| `tests/unit/quest/test_quest_kind.py`, `test_building_interaction_contract.py` negative case | pass |
| Domain suites after the deletions (quest, resource, world, kernel, economy) | 953 passed, 1 skipped |
| `tests/unit/tools` (full dir, serial, under MemoryMax=3G) | 1059 passed |
| `make mechanism-registry-validate`, `mechanism-registry-html-check`, completeness check | OK, up to date, 0 unbound |
| `paired --neutral`, 1000t, 3 worlds, seed 42, base 6e3ffea3f vs 99e2cf394 | IDENTICAL x3 (d81e5b8b4b9ad077, dfb3f9d6f24dd0b5, 8259e502ae1698d0) |
| `tests/tools` full run | not completed locally (MemoryError); file-by-file failures only in knowledge-index and REGISTRY-drift tests; CI is the check |

Proof field: 1000t is accepted because no live runtime path changed (deletions of uncalled code, comment-only edits in three `src` files).
