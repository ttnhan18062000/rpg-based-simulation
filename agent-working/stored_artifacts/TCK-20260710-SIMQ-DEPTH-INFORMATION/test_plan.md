---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-INFORMATION
artifact_type: test_plan
tags: [simulation-quality, information, world, corpus, calibration]
---

# Test Plan — TCK-20260710-SIMQ-DEPTH-INFORMATION

## Scope note

Investigation resolved UQ-1 definitively: **zero legitimate, tier-appropriate INFORMATION candidates
remain in the corpus** (see `investigation.md`'s "UQ-1 Resolution"). This ticket therefore makes no
content, schema, compiler, resolver, or calibration-profile changes. This test plan is accordingly
**verification-of-no-regression only** — its job is to prove the investigation's conclusion did not
require (and its documentation-only closure does not cause) any behavior change, not to validate new
INFORMATION content. Most of the ticket's Acceptance Criteria items are conditioned on "IF legitimate
candidates exist," which this investigation found false — those items are N/A by the ticket's own
phrasing, not skipped.

## Regression Surface

No code or content changes are planned, so the regression surface is a confirmation pass, not a
protection pass against a diff. Existing tests that establish the 9 currently-covered worlds' behavior
and must remain passing after any doc-only edits (Plan phase will touch `eval_matrix_results.md`,
`corpus_tier_taxonomy.md`, possibly `docs/parity_ledger/infrastructure.yaml`'s prose only):

**Unit:**
- `tests/unit/worldbuilding/test_world_compiler.py` — `InformationSourceProfile` construction from
  `WorldSpec.information_source_profiles` (`INFRA-256`'s cited test path).
- `tests/unit/worldassembly/test_assembly.py` — `WorldAssemblyResolver.assemble()` passthrough
  (`INFRA-256`'s cited test path).
- `tests/unit/worldassembly/test_corpus_diversity.py` — `test_population_stability` for all 17
  corpus worlds, including the 8 non-candidates (`dungeon_crawl`, `wilderness_survival`,
  `crowded_frontier`, `resource_dense_basin`, `simq_routing_test`, `hero_guild_routing`,
  `unit_faction_tension`, `unit_selfmodel_pilot`) — must remain green since none of their
  `world.yaml`/profile files change.

**Integration:**
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — Branch A reachability
  scenarios (`INFRA-256`/`INFRA-257`'s cited test path); must remain green, exercises
  `urban_political` and related fixtures, none of which change.
- `tests/integration/worldassembly/test_e2e_smoke.py`,
  `tests/integration/worldassembly/test_real_content_world_modules.py`,
  `tests/integration/worldassembly/test_real_content_world_compositions.py` — reference
  `survivor_camp_shelter`/other modules touched during this investigation's read-only inspection;
  confirm they still pass unmodified since no module file was edited.

**Grade regression (calibration corpus-wide):**
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`) — all 17 worlds' existing
  anchor entries (including the 9 INFORMATION-covered worlds' `belief_assimilated`-driven B grades
  and the 8 non-candidates' stable C grades) must be unchanged, since `grade_anchors.json` is not
  edited by this ticket.

## New Tests Required

None. No acceptance-criteria item that would require a new test (content seeding, router-scope
validation, compile-warning check, population-alive floor, grade-anchor addition) applies, because
Investigate found zero worlds to select for content authoring. Per the ticket's own Acceptance
Criteria phrasing ("IF legitimate candidates exist: ..."), those items are correctly N/A rather than
failed or skipped.

The one Acceptance Criteria item that **does** apply regardless of the zero-candidate outcome:

- **Test name:** N/A (documentation verification, not a pytest-level test)
- **Category:** manual/doc-review guard
- **What it verifies:** "IF Investigate confirms zero legitimate candidates: the ticket is closed or
  re-scoped with that finding documented (not silently abandoned)." Verified by Plan/Finalize phases
  adding a mirrored "INFORMATION Coverage Closure — Phase 3" table to
  `docs/simulation_quality/eval_matrix_results.md` (matching the FACTION sibling's precedent at
  `eval_matrix_results.md:1994-2023`) and updating `docs/plans/simq_development_roadmap.md`'s Phase 3
  section closure record, plus this ticket's own Completion Summary.
- **Where it lives:** `docs/simulation_quality/eval_matrix_results.md`,
  `docs/plans/simq_development_roadmap.md`, `tickets/done/TCK-20260710-SIMQ-DEPTH-INFORMATION.md`.

## Scoped Pytest Commands

Since this ticket makes no source/content changes, a scoped confirmation run (not a full corpus
`make evaluate`) is sufficient to prove nothing regressed as a side effect of the investigation's
read-only inspection or the Plan phase's doc-only edits:

```
pytest tests/unit/worldbuilding/test_world_compiler.py \
       tests/unit/worldassembly/test_assembly.py \
       tests/unit/worldassembly/test_corpus_diversity.py \
       tests/integration/scenarios/test_phase5_information_belief_scenarios.py \
       -v
```

```
pytest tests/simulation_quality/test_grade_regression.py -v
```

Do **not** run `make evaluate`/`make evaluate-full` as a required gate for this ticket — the
Acceptance Criteria's "`make evaluate` exits 0 with 0 regressions" item is conditioned on selecting
candidates and recalibrating; with zero candidates and zero content changes there is nothing new to
regress, and a full corpus sweep's cost is not justified by a documentation-only change. If Plan
disagrees and wants a confirmatory full sweep anyway (belt-and-suspenders given the ticket's explicit
"not silently abandoned" requirement), scope it to `--dry-run` first.

Never: `pytest tests/` (unscoped).

## Anti-Drift Test Guards

- **`tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability`** (parametrized
  over all 17 worlds) — guards against any accidental `world.yaml` edit during Plan-phase doc updates
  bleeding into content files. Should show zero diff in test collection/parametrization before and
  after this ticket's doc-only changes land.
- **`tests/simulation_quality/test_grade_regression.py`** (`FAST_ANCHOR_KEYS`, all 17 worlds) —
  guards against any of the 9 already-covered worlds' INFORMATION/COGNITION grades silently drifting
  if a future session mistakenly touches `config/simulation_quality/profiles/*.yaml` or
  `data/worlds/*/world.yaml` while working this ticket's doc-closure tasks.
- **Manual grep re-check** (not a pytest test, but a repeatable guard): re-running the two sweep
  commands from `investigation.md`'s Coverage Re-Verification section —
  `grep -c "information_source_profiles\|pending_information_responses" data/worlds/*/world.yaml`
  and `grep -rn "ENABLE_BELIEF_ASSIMILATION" config/simulation_quality/profiles/*.yaml` — after Plan
  phase's doc edits land, to confirm the two independent signals still agree on exactly the same
  9-world set (catches any accidental content edit disguised as a "doc-only" change).
- **Guard against scope creep into Branch B or the paid-information marketplace:** no test in this
  ticket's regression surface exercises `ENABLE_SELF_MODEL_COGNITION` or
  `InformationNeedDetector`/`PaidInformationTransactionSystem` — if a future diff for this ticket
  touches either, that is out-of-scope drift per the ticket's own Out of Scope section and this test
  plan's Regression Surface, and should be rejected or split into a separate ticket.
