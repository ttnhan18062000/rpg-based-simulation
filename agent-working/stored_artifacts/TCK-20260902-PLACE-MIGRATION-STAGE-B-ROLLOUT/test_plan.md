---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

**Normal flow:** `hero_guild_routing` compiles with all 4 region kinds correctly represented (CITY,
CAMP, RUIN, empty wilderness), verified against the real content on disk.

**Edge cases:** a region with zero Places declared alongside sibling regions that do have them (mixed
per-region outcomes within one world); a wildlife/ecology region that superficially resembles a LAIR
candidate but correctly gets no Place.

**Failure modes:** the batch resolve+compile pass across all 21 worlds — any single-world failure would
have blocked the whole migration; confirmed 21/21 succeeded with no exceptions.

**Regression-prone paths:** isolation verified at 3 different entity-count scales (16, 31, 59), not just
the smallest pilot world, to catch any scale-dependent bug the Stage A single-world check might have
missed.

**Scope command (used):**
`pytest tests/unit/worldbuilding/test_place_wiring.py -v -m "not slow"` — 7 passed (1 new).
Full regression: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"`
— 895 passed, 2 skipped (pre-existing, unrelated), 0 failed.
`pytest tests/tools/test_corpus_registry.py tests/unit/worldassembly/test_corpus_diversity.py tests/unit/lab/test_lab_result_store.py -m "not slow"`
— 76 passed.
