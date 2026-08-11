---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE
artifact_type: test_plan
tags: [testing, cognition, adventure, feature-flags]
---

# Test Plan — TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE

## Regression Surface

Existing tests that must keep passing (none of this ticket's work touches
`phase.py`/`service.py`/`generator.py`/`scoring.py`/`mapper.py`/`adventure_scorer.py`/
`intelligence.py` — read-only shadow comparison only):

**Unit — adventure domain**
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`
- `tests/unit/domains/adventure/test_phase3_route_generator.py`
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`
- `tests/unit/domains/adventure/test_phase3_route_families.py`
- `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`
- `tests/unit/domains/adventure/test_eligibility_cognition_profile.py`
- `tests/unit/domains/adventure/test_depletion_scoring.py`
- `tests/unit/domains/adventure/test_abandonment_rate.py`
- `tests/unit/domains/adventure/test_hero_quest_scoring.py`
- `tests/unit/domains/adventure/test_craft_upgrade_execution.py`
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py`

**Unit — goal scorer (ticket 1's output, must stay green and unmodified)**
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`
- `tests/unit/strategic/test_adventure_route_materialization.py`
- `tests/unit/strategic/test_expanded_goals.py`
- `tests/unit/strategic/test_score_normalization.py`
- `tests/unit/strategic/test_enum_drift.py`

**Integration — adventure domain**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/integration/domains/test_fused_loop.py`

**Integration — scenarios (decide()-level, not touched by this ticket's own new test)**
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`

**Kernel / state-purity precedent (must still pass; confirms `CanonicalStateHasher`/frozen-dataclass
assumptions this ticket's new test relies on)**
- `tests/integration/kernel/test_snapshot_integrity.py`
- `tests/integration/pipeline/test_no_hidden_mutation.py`

**Known pre-existing failures (unrelated, do not re-fix here — tracked separately)**
- `tests/integration/domains/adventure/test_harvest_to_event.py` — both tests fail on base branch
  per TCK-20260811-ADVENTURE-GOAL-SCORER's Test Summary; tracked by
  TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION. Confirm still isolated to this file only
  (re-verify with `git stash` if in doubt), do not let it block this ticket.

## New Tests Required

New file: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`
(reuses the `_state(entities)` builder pattern from `test_phase3_adventure_decision_phase.py` in the
same directory — see investigation.md's scenario-corpus resolution).

1. **`test_shadow_scenario_neither_path_mutates_state`**
   - Category: integration (state-purity / architecture guard)
   - Verifies: AC1's mutation guarantee. Construct one `AuthoritativeState` scenario (single hero,
     `resource_nodes`/self-model set up so `generate()` yields a non-trivial candidate set). Capture
     `hash_before = CanonicalStateHasher.get_hash(state)`. Call
     `AdventureDecisionPhase.apply(state, factions=state.factions)` (discard the returned
     `StateUpdate` — only checking `state` itself) and separately
     `AdventureGoalScorer().score(hero, state)`. Assert
     `CanonicalStateHasher.get_hash(state) == hash_before` after each call, and additionally assert
     `state.entities[hero.id] == snapshot_of_entity_before` (dataclass equality, cheap extra check)
     as defense-in-depth alongside the hash check.
   - Lives in: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

2. **`test_shadow_parity_recover_family`**,
   **`test_shadow_parity_buy_upgrade_family`**,
   **`test_shadow_parity_craft_upgrade_family`**,
   **`test_shadow_parity_gather_resource_family`**,
   **`test_shadow_parity_ask_information_family`**,
   **`test_shadow_parity_form_party_family`**
   - Category: integration (cross-path equivalence)
   - Verifies: AC2, for the 6 route families `AdventureRouteGenerator.generate()` can actually
     produce from a real `AuthoritativeState` (see investigation.md's Critical Finding). Each test
     builds a scenario engineered to make that family the natural winner (e.g. low-HP entity with no
     opportunities → RECOVER; entity with a `buy_item` opportunity and sufficient gold → BUY_UPGRADE;
     etc. — mirror the existing per-family scenario shapes already used in
     `test_phase3_route_generator.py`'s `test_low_hp_generates_recover_route` /
     `test_weak_weapon_and_shop_item_generates_buy_upgrade_route` / etc., but wrapped in a full
     `AuthoritativeState` via `_state()` instead of calling `generate()` standalone). Runs
     `AdventureDecisionPhase.apply(state, factions=state.factions)` and reads
     `result.entity_updates[hero.id].strategic.projects_add_or_update[0]` for the committed
     family/score (family via the `ObjectiveState`/`ProjectState.kind` → `RouteToProjectMapper.
     get_kinds()` reverse-check, or simpler: assert on `entity_updates[hero.id].property_updates[
     "last_routing_family"]` which phase.py already writes verbatim, `phase.py:179`) and separately
     calls `AdventureGoalScorer().score(hero, state)`, asserting
     `result.metadata["route_family"].value == entity_update.property_updates[
     "last_routing_family"]` and `result.metadata["raw_score"] == <the score AdventureDecisionPhase
     committed>` (read `property_updates` or the trace's `score` field, `phase.py:185`, for the
     phase-side raw score to compare against `AdventureDecisionService.decide()`'s own
     `selected.score` — both must trace back to the identical `AdventureRouteOption.score` since both
     paths call the same `decide()`).
   - Live in: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

3. **`test_shadow_parity_mapper_level_all_15_families`**
   - Category: integration (mapper-level parity, explicitly scoped narrower than #2 — the honest
     resolution for the 9 currently-unreachable families per investigation.md)
   - **STALE-AS-WRITTEN NOTICE (superseded by plan.md's Plan-phase correction, resolved during this
     ticket's Implement pass — text below now matches the actual, final Step 3 shape; the previous
     single-call/`project.score == 1.7` bare-equality description this paragraph used to carry was an
     architecture-reviewer-flagged gap: it violated the ticket's own Scope text requiring an itemized
     diff report, not a single pass/fail assert, for the family comparisons):**
   - Verifies: AC2's "for each of the 15 route families" at the level that *is* provably true today —
     both `AdventureDecisionService.decide()` (via `RouteToProjectMapper.map_to_states()` inside it,
     `service.py:141-148`) and `AdventureGoalScorer`'s materialization
     (`RouteToProjectMapper.map_to_states()` called directly, mirroring `intelligence.py:1450-1457`)
     route through the **same** `RouteToProjectMapper.map_to_states()` function. Parametrize over all
     15 `_MAP` keys; for each, call `RouteToProjectMapper.map_to_states(family=f, entity_id=1, tick=5,
     score=1.7, target="t", target_pos=(1.0, 2.0))` **twice** with identical arguments — one call
     standing in for what `AdventureDecisionService.decide()` does, one for what the scorer-side
     materialization branch does — then diff the two `(ProjectState, ObjectiveState)` results through
     the same shared `_diff_routes()` helper defined in Step 1 (`family_mismatches`/
     `raw_score_mismatches` asserted empty), plus retain a `get_kinds()` schema check as an additional
     dimension `_diff_routes()` does not cover (`project.kind`/`obj.kind` must match
     `RouteToProjectMapper.get_kinds(f)`). Routing through `_diff_routes()` even though both calls are
     guaranteed to match today (same function, same args) gives a real itemized artifact instead of a
     silent `AssertionError` if a future change makes `map_to_states()` non-deterministic or
     caller-order-sensitive — the exact design-doc §4 defect shape reintroduced at mapper scale. This
     is the only parity claim that's actually exercisable for the 9 generator-unreachable families.
     Test name/docstring must say explicitly "mapper-level only for families not reachable via
     generate()" so this isn't mistaken for end-to-end coverage.
   - Lives in: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

4. **`test_shadow_diff_report_separates_raw_score_from_utility_mismatches`**
   - Category: unit (diff-report shape)
   - Verifies: AC3. Construct two synthetic cases directly against a small diff-report helper (added
     in this same test file or a small `_diff_routes(phase_result, scorer_result)` helper function,
     not new production code under `src/`): one where `raw_score` differs between the two paths
     (should appear under a `raw_score_mismatches` key/list) and one where only `utility` would differ
     if (hypothetically) compared (should appear under a separate `utility_mismatches` key/list, kept
     empty in the passing case since AC2 never compares utility for the committed decision — this test
     exists specifically to prove the report *shape* keeps the two categories apart, catching a future
     regression where someone conflates them, which is the literal scale-mismatch bug shape design
     doc §4 describes).
   - Lives in: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

5. **`test_delete_adventure_decision_phase_ac1_already_encodes_the_gate`**
   - Category: architecture guard (ticket-text, not code — verifies AC4 without requiring a code
     change)
   - Verifies: AC4. Reads `tickets/todos/adventure-cognition-merge/
     TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md` from disk and asserts its Acceptance Criteria
     section contains the literal substring "TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4)" and
     "both in tickets/done/" — a cheap regression guard so a future edit to that ticket file can't
     silently drop the hard-dependency gate this ticket's own AC4 depends on. Not a claim that this
     ticket edits that file (per investigation.md, it doesn't need to — the gate already exists); this
     test only guards against accidental removal.
   - Lives in: `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py` (or a
     small dedicated `tests/tools/test_epic_gate_dependencies.py` if the repo prefers ticket-text
     assertions kept out of domain test directories — match whichever convention
     `tools/registry_query.py`'s own test file, if any, already uses; default to co-locating with the
     other shadow tests if no such precedent exists)

## Scoped Pytest Commands

```
pytest tests/unit/domains/adventure/ tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/integration/domains/adventure/ tests/integration/domains/test_fused_loop.py tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py tests/integration/kernel/test_snapshot_integrity.py tests/integration/pipeline/test_no_hidden_mutation.py -v
```

Never `pytest tests/` — this command is scoped to the adventure domain, the goal-scorer subsystem
this ticket shadow-tests against, and the state-purity infrastructure (`CanonicalStateHasher`,
frozen-dataclass guards) the new test depends on.

## Exact `/simq-audit` invocation for AC5

This ticket's own AC5 ("Migration step 4 is scoped as 'invoke /simq-audit mode=full (or mode=slow)
as pre-cutover gate and report its verdict' -- AC asserts the audit was run and its verdict recorded,
not that new SimQ infrastructure was built") is a **manual verification step recorded in the ticket,
not a pytest test**. Concretely, at or near the end of this ticket's Implement/Verify phase:

1. Run `/simq-audit mode=full` (per `.claude/skills/simq-audit/SKILL.md` — `mode=full` re-runs the
   engine for all fast <=500t scenarios first, then diffs against `grade_anchors.json`; `mode=slow`
   additionally runs the 1000t/2000t tier if a deeper pre-cutover check is wanted, at the cost of the
   longer wall-clock time noted in `docs/simulation_quality/audit_workflow.md` §4).
2. The workflow's Report phase (step 7 of the 7-phase pipeline) returns one of exactly 4 terminal
   statuses: `DONE_NO_TICKET` (verdict `no_regression` — every flagged item was `EXPECTED_DRIFT`/
   `NO_ACTION`), `NEEDS_TICKET` (verdict `regression` or `needs_da_decision` — a new ticket ID is
   returned along with a `/implement-ticket ticket_id=...` hand-off instruction), `ANCHORS_STILL_
   FAILING` (Update Anchors phase gate failed), or `BLOCKED` (Verify phase found a DoD-style gap).
3. **"Report its verdict"** means: record the exact returned status string plus the underlying
   Classify Drift `verdict` (`no_regression`/`regression`/`needs_da_decision`) in this ticket's own
   `Implementation Notes`/`Completion Summary` sections verbatim, along with the `runId`
   (`SIMQ-AUDIT-<timestamp>`) for traceability. If the result is `NEEDS_TICKET`, `ANCHORS_STILL_
   FAILING`, or `BLOCKED`, **do not treat that as this ticket's own failure to route around** — per
   CLAUDE.md's rule against editing to make a gate pass, a non-`DONE_NO_TICKET` verdict is correct
   information to report as this ticket's pre-cutover finding, not an obstacle to silently resolve
   inside this ticket's own scope (fixing a genuine regression found by `/simq-audit` is out of this
   ticket's Scope/Out-of-Scope boundary — "Reimplementing /simq-audit's ... machinery" is explicitly
   excluded, and fixing a regression it finds is a different kind of overreach again).
4. This ticket's AC5 is satisfied once the invocation happened and its verdict is recorded — it does
   **not** require the verdict to be `no_regression`/`DONE_NO_TICKET` to close this ticket, since the
   *design*'s migration step 4 is a gate for the *later* `DELETE-ADVENTURE-DECISION-PHASE` cutover,
   not for this ticket's own shadow-test-landing. (Re-confirm this reading against the ticket's own
   AC5 wording at Plan time — "report its verdict" does not literally require a passing verdict.)

## Anti-Drift Test Guards

- **`test_shadow_parity_mapper_level_all_15_families` must never silently start passing more broadly
  than it can prove** — if a future change to `generator.py` extends `kind_map` to cover more
  families, the corresponding family should graduate from test #3 (mapper-level) into test #2
  (end-to-end), and the diff-report scope note in investigation.md should be updated in the same
  change. A stale "9 unreachable" claim would itself become a drift bug.
- **`test_shadow_scenario_neither_path_mutates_state` must call the real
  `CanonicalStateHasher.get_hash()`**, not a hand-rolled hash or `repr(state)` string comparison —
  guards against a future "simplification" that silently drops dict-order-insensitivity and produces
  false negatives (two structurally-identical states with different insertion order reporting as
  "mutated").
- **`test_shadow_parity_*_family` tests must read the phase-side raw score from
  `property_updates`/trace fields that `phase.py` itself already writes** (`last_routing_family`,
  trace `score`), never re-derive it by calling `AdventureDecisionService.decide()` a second time
  independently — re-deriving would trivially always match (both call the same function) and silently
  stop testing the actual wrapping-parity risk this ticket exists to catch.
- **Guard against the `factions=None` vs `factions=state.factions` coincidence silently becoming load-
  bearing** (investigation.md Risk #3): the shadow test must call
  `AdventureDecisionPhase.apply(state, factions=state.factions)` explicitly, not rely on the default.
  If a reviewer ever "simplifies" this call back to `AdventureDecisionPhase.apply(state)`, a future
  change to `AdventureRouteScorer.score()`'s escort branch could introduce a real, silent divergence
  with no test failure until much later.
