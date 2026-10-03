---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
artifact_type: test_plan
tags: [social, cognition, progression]
---

# Test Plan — TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING

## Regression Surface

Existing tests that must keep passing regardless of which option (1 or 2) Plan selects:

**Unit — commitment domain**
- `tests/unit/domains/commitment/test_phase15_reputation_update.py` — 14 lines, 1 test
  (`test_reputation_update_service`); asserts label deltas per `event_kind` in isolation. Must keep
  passing unmodified — this ticket does not change `ReputationUpdateService`'s internal delta logic,
  only adds a real caller.
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- `tests/unit/domains/commitment/test_phase15_commitment_pressure.py`
- `tests/unit/domains/commitment/test_phase15_route_impact.py`

**Integration — commitment/reputation scenarios**
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` — 55 lines, 2 tests
  (`test_accepted_escort_prevents_minor_loot_switch`, `test_abandoning_party_changes_future_partner_selection`).
  Neither currently calls `ReputationUpdateService.process_witnessed_event()` directly (confirmed by
  file size/structure) — must keep passing; if either test's setup happens to construct a quest that
  transitions to COMPLETED (Option 1) or a party that transitions to MEMBER_ABANDONING (Option 2),
  verify no unintended `cognition_bundle_set` side effect changes its existing assertions.

**Quest-kind stability (only if Option 1 / QuestKind.ESCORT is chosen)**
- No dedicated `tests/unit/engine/test_quests*.py` file exists today (confirmed — `tests/unit/engine/`
  has no quest-kind file; the ticket's own AC wording naming this path is aspirational/approximate).
  The real existing quest-kind regression surface is:
  - `tests/unit/quest/test_quest_system.py` — constructs `QuestState` with `QuestKind.EXPLORE`/`BOUNTY`
    directly; must keep passing (enum append is non-breaking to existing members).
  - `tests/unit/quest/test_quest_generation.py`, `test_quest_lifecycle.py`, `test_quest_rewards.py`,
    `test_quest_transactions.py`, `test_quest_relation_projection.py`
  - `tests/unit/worldbuilding/test_world_compiler.py::test_helper_enum_mappers` (lines 552-563) —
    asserts `get_quest_kind("hunt")==HUNT`, `("gather")==GATHER`, `("explore")==EXPLORE`. Does **not**
    currently assert on `"escort"` — confirmed gap, this is where the new assertion belongs.
  - `tests/unit/worldbuilding/test_quest_definition.py` — schema-level `QuestDefinition.type` tests.
  - `tests/arena/test_arena_quests.py` — end-to-end quest exercise in arena scenarios; must keep
    passing since `QuestResolutionSystem.enforce()` is touched.
  - `tests/unit/systems/test_quest_activation_pathway.py`

**Cooperation domain (only if Option 2 / CooperationLearningService activation is chosen)**
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` (cited in
  `docs/simulation/social_systems_contract.md`'s Regression tests section) — full contract lifecycle
  including party dissolution/abandonment; must keep passing since it exercises
  `CooperationPhase.execute()` and `PartyCohesionService.evaluate()`.
- Any test exercising `CooperationPhase.execute()`'s `MEMBER_ABANDONING`/`LEADER_LOST` trust
  decrement — locate via `grep -rl "MEMBER_ABANDONING\|PartyCohesionService" tests/` at
  implementation time and re-run; not enumerated here since the branch touched depends on Plan's
  exact insertion point.

**Merge-safety regression (both options)**
- `tests/unit/domains/memory/` (path pattern; locate via `grep -rl "MemoryUpdatePhase"
  tests/unit/domains/memory/` at implementation time) — must keep passing to confirm
  `MemoryUpdatePhase`'s causal/spatial writes are not clobbered by the new `cognition_bundle_set`
  writer, per the merge-safety hazard documented in investigation.md.
- `tests/integration/pipeline/` near-death-hardening tests (the existing precedent this ticket's
  merge pattern must match) — confirm they still pass unmodified, proving the pattern itself is not
  disturbed.

## New Tests Required

Per Acceptance Criteria, assuming Option 1 (Plan may adjust names if Option 2 is selected instead —
see investigation.md's recommendation and rationale):

1. **`test_successful_escort_completion_updates_reputation`**
   - Category: integration (arena-combat adjacent / pipeline-level)
   - Verifies: an entity with an active `QuestState(quest_kind=QuestKind.ESCORT, quest_status=ACTIVE)`
     that transitions to `COMPLETED` via `QuestResolutionSystem.enforce()` in a real
     `AuthoritativeApplyPipeline` run produces an `EntityUpdate.cognition_bundle_set` whose
     `relationships.public_reputation.labels["reliable"]` increased by the documented +0.1 (capped
     1.0) relative to the pre-tick value, and that the change survives `apply()` into
     `state.entities[id].cognition.relationships.public_reputation`.
   - Where: `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` (new test
     function, alongside the existing 2) or a new
     `tests/integration/pipeline/test_reputation_witnessed_event_wiring.py` if Plan prefers isolation
     from the existing Phase 15 scenario file — Plan's call.

2. **`test_quest_completion_non_escort_kind_does_not_touch_reputation`**
   - Category: unit or integration
   - Verifies: a HUNT/GATHER/EXPLORE/LIBERATE/BOUNTY quest reaching `is_newly_completed` does **not**
     call `ReputationUpdateService` / does not set `cognition_bundle_set` for reputation reasons —
     guards against the new branch being accidentally unconditional.
   - Where: `tests/unit/quest/test_quest_rewards.py` or alongside test 1.

3. **`test_quest_reward_phase_preserves_memory_update_cognition_writes`**
   - Category: architecture guard
   - Verifies: when both `MemoryUpdatePhase` (causal/spatial memory write) and the new reputation
     wiring fire for the same entity in the same tick, the resulting `cognition_bundle_set` contains
     **both** the memory changes and the reputation change — not just the later writer's value. This
     is the direct regression test for the merge-safety hazard documented in investigation.md; it
     must construct a scenario where both phases have real work to do for the same entity_id in one
     tick.
   - Where: new test in `tests/integration/pipeline/` (or alongside test 1), asserting on
     `entity.cognition.memory.causal.entries` (non-empty/updated) AND
     `entity.cognition.relationships.public_reputation.labels["reliable"]` (updated) simultaneously
     post-apply.

4. **`test_compiler_maps_escort_to_escort_quest_kind`**
   - Category: unit
   - Verifies: `get_quest_kind("escort") == QuestKind.ESCORT` (currently falls through to EXPLORE —
     this test would fail today and must pass after the fix).
   - Where: `tests/unit/worldbuilding/test_world_compiler.py::test_helper_enum_mappers` (extend the
     existing test with one more assertion, matching its existing style for `"hunt"`/`"gather"`/`"explore"`).

5. **`test_quest_kind_escort_enum_value_is_new_member_only`**
   - Category: architecture guard / regression
   - Verifies: `QuestKind.ESCORT` exists, `list(QuestKind)` still contains all 5 original members
     unchanged, and `QuestState.quest_kind` still defaults to `QuestKind.HUNT` (unaffected default).
     Guards against accidentally reordering the enum (which would be safe today given `.name`-only
     serialization, but the guard makes the safety explicit and regression-proof).
   - Where: `tests/unit/quest/test_quest_system.py`.

6. **`test_reputation_parity_entry_has_passing_test_path`** (meta-test, if the repo's parity-ledger
   test-path validation pattern requires an explicit test asserting the cited path runs — check
   `tests/tools/test_parity_index_baseline.py`-style patterns at implementation time; only add if a
   comparable existing pattern requires it, otherwise the new parity entry's `test_path` field
   pointing at test 1 above is sufficient and this entry is not needed as a separate test).

## Scoped Pytest Commands

```
pytest tests/unit/domains/commitment/ -v
pytest tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py -v
pytest tests/unit/quest/ -v
pytest tests/unit/worldbuilding/test_world_compiler.py -v
pytest tests/arena/test_arena_quests.py -v
pytest tests/unit/systems/test_quest_activation_pathway.py -v
```

If Option 2 is selected instead of Option 1, additionally scope:

```
pytest tests/unit/domains/cooperation/ -v
pytest tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -v
```

Never `pytest tests/` — per Testing Rule, always scoped to the domains this ticket actually touches
(commitment, quests/worldbuilding for Option 1, or cooperation for Option 2), plus the merge-safety
memory-phase regression tests identified above.

## Anti-Drift Test Guards

- **Merge-safety guard (test 3 above) is mandatory regardless of which option is chosen** — it is
  the direct regression test for the confirmed `MemoryUpdatePhase`-clobbering hazard, and must exist
  before this ticket can be considered done; a passing implementation without this test would only
  prove the happy path, not the actual risk this investigation surfaced.
- **Test 2 (non-escort quest kinds untouched)** guards against the new conditional branch in
  `QuestResolutionSystem.enforce()` becoming unconditional by a future refactor, which would corrupt
  reputation labels for unrelated quest completions (HUNT/GATHER/EXPLORE/LIBERATE/BOUNTY).
- **Test 4 (compiler mapping) must be scoped to `"escort"` only** — do not silently extend it to also
  fix `"fetch"`/`"defend"`/`"investigate"` in the same pass; those remain a separate, out-of-scope
  gap per investigation.md's Anti-Drift Hazards. A test asserting all 6 literal schema values map
  correctly would itself be scope creep and should be flagged in review if it appears.
- **If Option 2 is chosen, a guard test must assert `ReputationUpdateService.process_witnessed_event`
  is called with `event_kind="betrayal"` only from a genuinely new, distinct detection condition** —
  not from the existing `MEMBER_ABANDONING`/`-0.25` trust-decrement site as-is. A test that would
  pass by wiring the existing abandonment site directly to the betrayal event_kind should be treated
  as a red flag during Verify, per investigation.md's mislabeling concern — the guard test should
  explicitly construct an ordinary (non-betrayal) party abandonment and assert it does NOT emit a
  `"betrayal"` witnessed event.
- **Parity ledger test**: whatever new test is designated as the `SOC-252` entry's `test_path` must
  actually exist and pass before ticket close — do not cite a hypothetical/aspirational test path,
  per the Authoritative Mechanics Rule and this ticket's own AC #4.
