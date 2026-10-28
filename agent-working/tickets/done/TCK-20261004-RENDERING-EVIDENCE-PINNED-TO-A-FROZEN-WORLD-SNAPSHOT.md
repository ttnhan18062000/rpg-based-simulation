---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT
phase: done
date: 2026-10-04
tags: [rendering, testing, world, investigation]
---

# TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT

## Title

Six rendering-quality tests now prove things about a frozen snapshot rather than the live corpus —
decide whether to rebaseline onto the real `dungeon_crawl` or keep the fixture deliberately

## Status

OPEN

## Tier

standard

## Type

repair

## Priority

P2

## Request Summary

`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` corrected
`data/worlds/dungeon_crawl/world.yaml` so production finally loads the intended 12-entity, 2-region,
2-faction world instead of the 32-entity world a June fix failed to reach. That correction removed two
world modules, and with them the **subject** of six rendering-quality tests that had pinned the old
`dungeon_crawl` as documented evidence:

- `tests/unit/rendering/` `test_connectivity` (15245 walkable → 12221), `test_density` (CV 0.678 →
  0.283), `test_variants` (TVD 0.2316 → 0.2867, the number recorded as parity entry **INFRA-373**)
- three tests in `test_shape`: two 1116-tile forests, a cave, and a 90-degree rotation — the second
  forest and the cave came from the removed modules, so these three lose their subject entirely, not
  just their numbers

As an interim measure that ticket froze the old `resolved/` snapshot as a test fixture and repointed all
six tests at it, so the suite is green and the evidence stays reproducible. **That decision was taken to
avoid editing another area's documented numbers inside a world-definition bug fix — it is not a
considered answer to what rendering evidence should be measured against.** This ticket is that answer.

The cost of the interim state, stated plainly because it must not stay invisible: **a frozen fixture no
longer detects rendering regressions in the live corpus.** Six tests that look like live guards are now
historical records.

## Scope

- Decide, and record the decision: do these six tests measure the **live corpus** (rebaseline the
  numbers, and find a new subject or retire the three shape tests) or a **deliberately frozen
  reference** (keep the fixture, and rename/redocument the tests so nobody reads them as live guards)?
- Whichever way: make `docs/visual_quality/current_state.md`, `docs/visual_quality/scoring_contract.md`
  and the docstrings in `src/rendering/{variants,density}.py` agree with the answer. They currently cite
  the old numbers, which remain true *of the fixture* — correct but easy to misread.
- Update parity entry **INFRA-373** in `docs/parity_ledger/infrastructure.yaml` to match.
- If the answer is "live corpus": add live rendering coverage for at least one world that genuinely
  carries a forest and a cave, so the shape dimension is not silently dropped.

## Out of Scope

- Re-litigating the `dungeon_crawl` world-definition fix. The 12-entity, 2-region world is correct and
  is backed by a measured 94–97% extinction rate at 32 entities.
- Any change to `src/worldassembly/`, `src/worldgeneration/` or `data/worlds/`.
- The visual-asset / detail-tile program. This is about rendering **metric evidence**, not assets.

## Acceptance Criteria

1. The decision (live corpus vs frozen reference) is recorded with its rationale in
   `docs/visual_quality/scoring_contract.md`, not only in this ticket.
2. All six tests are consistent with the decision, and none of them can be read as a live guard while
   asserting against a frozen fixture — if the fixture stays, the test names or docstrings say so.
3. `docs/visual_quality/{current_state,scoring_contract}.md` and the `src/rendering/{variants,density}.py`
   docstrings cite numbers that match what the tests actually assert, and name the subject.
4. INFRA-373 in `docs/parity_ledger/infrastructure.yaml` has a `status` and `v2_evidence` that match the
   decision.
5. If the fixture is kept, the ticket states what would have to change for the frozen reference to be
   retired. If the live corpus is chosen, the shape dimension has live coverage or its retirement is
   recorded in `docs/guidelines/intentional_divergences.md`.

## Related Tickets

- `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` — created this situation;
  authored the frozen fixture
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — established `data/worlds/<id>/world.yaml` as
  the single source of a world definition (PR #328)
- `TCK-20260821-VISUAL-SHAPE-METRIC`, `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`,
  `TCK-20260821-VISUAL-VARIANTS-METRIC`, `TCK-20260820-EPIC-WORLD-RENDERING-CORE` — authored the
  evidence being re-decided here; all closed Aug 2026
- `TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION` — the same measurement-validity
  failure in a different place

## Related Docs

- `docs/visual_quality/current_state.md`, `docs/visual_quality/scoring_contract.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-373)
- `docs/architecture/world_repository_layout.md` §1 — the single-source law
- `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` — §3: `infrastructure.yaml` is assigned
  to neither implementer lane, which is why this needed a planner ruling

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION/`
  — the AC-5 sweep and the fixture's provenance

## Related Code Areas

- `tests/unit/rendering/` — `test_connectivity.py`, `test_density.py`, `test_variants.py`,
  `test_shape.py`, and the frozen snapshot fixture
- `src/rendering/variants.py`, `src/rendering/density.py` — docstrings citing the old numbers
- `docs/visual_quality/` — both pages

## Assumptions / Open Questions

- **UQ-1:** is rendering-metric evidence meant to track the live corpus at all? If these metrics exist to
  detect rendering-code regressions, a frozen reference world is arguably *better* — it isolates the
  renderer from world-content churn. If they exist to describe what players would see, it must be live.
  This is the question; it is not assumed.
- **UQ-2:** does any world in the corpus currently carry both a forest and a cave, i.e. is live shape
  coverage even available without authoring content for it?
- Assumption: the six numbers quoted above are the post-fix measurements reported by
  `rpg-implementer-2`. Re-measure before relying on them — they were relayed, not independently taken.

## Implementation Notes
Decision: option C (keep the frozen reference, add live coverage). Ruling by rpg-planner (u24), relayed via lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu on 2026-10-28; NOT an owner approval. Word for word:
"For rpg-planner-ubuntu, U3 t3 values: OK as proposed.
- Q1, exact pins vs tolerance: exact pins are OK (TVD to 4 places, CV to 3, counts and fills exact). The compile is deterministic, since two runs gave identical results, and a tolerance band would hide a real layout change. Any data/worlds release that moves them is rebaselined by me, as the dated comment says.
- Q2, the live subject: frontier_living_world is right. It is an M1 gate world, and only my data/worlds release can change it.
- INFRA-373: the text is OK as written (status verified, test_path unchanged).
- Stale-figure corrections (a) and (b): OK, with the reason stated.
- Rotation and seed-invariance: both stay frozen-only and on live dungeon_crawl respectively, as proposed. Commit when ready."
- The six frozen tests are renamed `test_frozen_reference_*` with a docstring naming the fixture; four live tests on frontier_living_world (seed 42) pin walkable 17058 / 1 component / 100.0, CV 0.659, TVD vs sandbox_world 0.2645, cave 1886 (1.0) and forests 1226 (0.515) / 216 (0.675).
- UQ-1/UQ-2 answered: the frozen reference isolates the renderer from content churn; live worlds with forest + cave exist (frontier_extended, frontier_living_world, frontier_marches). The ticket's 0.2867 does not reproduce (live dungeon_crawl TVD 0.196, no known origin) and is dropped.
- Corrections (a) 0.23161981243456373 -> 0.23153614062704975 (D72 bucket merge) in INFRA-373, current_state.md, scoring_contract.md, variants.py; (b) CV 0.6782405727873148 labelled frozen (live dungeon_crawl 0.283) in density.py and scoring_contract.md.
- Decision recorded in docs/visual_quality/scoring_contract.md section 6. INFRA-373 text rewritten and INFRA-370/371/372 test_path repointed through parity_ledger_writer.py in one pass (rpg-planner-ubuntu OK'd the three repoints); diff shows only those four rows changed.
- The frozen reference can be retired when the renderer no longer needs a fixed-world regression anchor.

_(to be filled during implementation)_

## Test Summary
tests/unit/rendering 99 passed.

_(to be filled during implementation)_

## Files Changed
tests/unit/rendering/test_{connectivity,density,shape,variants}.py, docs/visual_quality/{current_state,scoring_contract}.md, src/rendering/{variants,density}.py (docstrings), docs/parity_ledger/infrastructure.yaml (INFRA-370..373).

_(to be filled during implementation)_

## Completion Summary
Frozen tests renamed and documented as reference, live coverage added on frontier_living_world, numbers and parity rows corrected.

_(to be filled during implementation)_
