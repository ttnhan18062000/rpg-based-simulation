---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT
artifact_type: investigation
tags: [rendering, testing, world, investigation]
---

# Investigation

Measured by `rendering_probe.py` (rows in `rendering_probe_results.jsonl`): the frozen fixture and all 24 `data/worlds` worlds, seed 42, tick 0, on origin/main 3b5fab1e9 plus the batch branch. The relayed numbers in the ticket were re-measured, not trusted.

## The six numbers
| test | frozen fixture (re-measured) | live `dungeon_crawl` (measured) | ticket said |
|---|---|---|---|
| connectivity: walkable tiles | 15245, 1 component | 12221, 1 component | 15245 -> 12221 (reproduced) |
| density CV | 0.678 | 0.283 | 0.678 -> 0.283 (reproduced) |
| TVD(sandbox_world, dungeon_crawl) | 0.2315 | **0.196** | 0.2316 -> **0.2867** (NOT reproduced: I measure 0.196) |
| shape: forests | 2 x 1116 | 1 x 1116 | second forest lost (reproduced) |
| shape: cave | 1 cave | none | lost (reproduced) |
| shape: 90-degree rotation of the two forests | needs two forests | impossible with one forest | lost (reproduced) |
The INFRA-373 text and `docs/visual_quality/*` cite the frozen values (0.2316, 0.6782, ...), which are true of the fixture only. The 0.2867 in the ticket does not match any measurement I took; whoever relied on it should re-derive it (I did not search for what it was computed against).

## UQ-2: is live shape coverage available without authoring content? Yes.
Live worlds carrying both forest and cave: `frontier_extended` (forests 2860+1226, cave 1886), `frontier_living_world` (1226+216, cave 1886), `frontier_marches` (2005+216, 1886), `generated_frontier_3_42` (forest 1116, caves 1865+1271), `simq_routing_test`, `simq_scale_stress_seed42` (two forests, two caves). Two forests plus one cave, like the fixture: `frontier_extended`, `frontier_living_world`, `frontier_marches`. `frontier_living_world` is the world the Campaign path runs, so it is the natural live subject.

## What reads the fixture
`tests/unit/rendering/test_connectivity.py`, `test_density.py`, `test_shape.py` (3 tests), `test_variants.py` through `tests/unit/rendering/frozen_dungeon_crawl.py`; fixture `tests/fixtures/rendering/dungeon_crawl_pre_balance_fix.resolved.yaml` (header says do not regenerate). Docs and docstrings citing the numbers: `docs/visual_quality/current_state.md:28`, `docs/visual_quality/scoring_contract.md:75,88`, `src/rendering/density.py:11-12`, `src/rendering/variants.py:8-9`, ledger INFRA-373, `docs/guidelines/intentional_divergences.md:2655`.
