---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260812-COMMITTED-INTENTION-SEQUENCE
artifact_type: test_plan
tags: [cognition, strategy, progression]
---

# Test Plan — TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Regression Surface

**Unit — `tests/unit/strategic/`** (the primary domain under modification; all must keep passing
unmodified since `evaluate_project_switch()` stays byte-identical and `StrategicComponent`/
`CognitionProfile` only gain new fields, never remove/rename existing ones):
- `test_interruption_resistance.py` (STRAT-005/006, `_make_entity` helper reused across the domain)
- `test_score_normalization.py` — **STRAT-186/STRAT-187's actual `test_path` targets**:
  `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`,
  `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
- `test_adventure_route_materialization.py`, `test_social_contract_materialization.py`,
  `test_region_stabilization_materialization.py` — the three existing per-kind materialization
  branches; must not regress once a fourth (committed-intention) source is appended to the tier-5
  candidate list
- `test_project_continuity.py` (`test_project_lock`, `test_project_continuity_resume_suspended`)
- `test_evaluate_project_switch_state_threading_guard.py` (guards the `state=None` default-path
  byte-identical behavior for the 27 pre-existing direct call sites — must not regress if any new
  call site passes `state`)
- `test_threat_resolved_lock_release.py`, `test_rejection_backoff.py`, `test_goal_hysteresis.py`,
  `test_strategic_reprioritization.py`, `test_strategic_detour_ph6.py`,
  `test_strategic_cognition_regression.py`, `test_strategic_lifecycle_v2.py`,
  `test_strategic_memory_v2.py`, `test_status_hardening.py`, `test_expanded_goals.py`,
  `test_routine_biasing.py`, `test_personality_goal_modifiers.py`,
  `test_project_system_precedence.py`, `test_cognition_immediate_fixes.py`,
  `test_event_interpretation.py`, `test_strategic_social_contracts.py`

**Unit — capacity/builder/serialization plumbing** (must keep passing, and per Investigation's
durable-state gap, are the files this ticket must also touch):
- Any existing capacity-enforcement tests exercising `src/engine/pipeline_phases/
  capacity_enforcement.py` (locate via `grep -rl CapacityEnforcementPhase tests/` at Plan/Implement
  time — not enumerated here since none were found already-scoped to strategic caps beyond the
  files above; Plan should confirm at implementation time)
- Any existing builder tests exercising `V2EntityBuilder.strategic()`

**Integration:**
- `tests/integration/kernel/test_p1_replay_fidelity.py` — exercises
  `StateFingerprinter`/`_strategic_identity()`; must keep passing, and per Investigation's finding,
  should be extended (see New Tests) once `committed_intentions` is added to the fingerprint.
- `tests/integration/pipeline/test_strategic_cadence.py`
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`

**Adventure-domain regression** (arena-combat-adjacent; the `ADVENTURE_ROUTE` per-kind branch is
one of the three existing materialization branches sharing the tier-5 candidate list with the new
committed-intention source):
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`
- `tests/unit/domains/adventure/test_phase3_route_families.py`
- `tests/perf/test_phase3_adventure_decision_budget.py` (perf budget guard — confirms the new
  materialization hook doesn't blow the per-tick cost budget; run if touched, not required for pure
  logic changes)

## New Tests Required

Per AC1-AC7:

1. **`test_committed_intention_dataclass_shape`**
   Category: unit
   Verifies: `CommittedIntention` is frozen, has fields `intention_id, goal_kind, target_hint,
   sequence_index, status` matching Design §2's sketch; `StrategicComponent.committed_intentions`
   defaults to `()` (empty tuple) via `field(default_factory=tuple)`.
   Location: `tests/unit/strategic/test_committed_intention_model.py` (new file)

2. **`test_cognition_profile_max_committed_intentions_default`**
   Category: unit
   Verifies: `CognitionProfile.max_committed_intentions == 3` by default, mirroring
   `max_active_projects`'s pattern.
   Location: `tests/unit/strategic/test_committed_intention_model.py`

3. **`test_committed_intention_head_materializes_as_ordinary_tier5_candidate`**
   Category: unit
   Verifies: with `committed_intentions=(CommittedIntention(..., sequence_index=0,
   status="pending"),)` and no current project, `evaluate_strategic_intent()` produces a
   `StrategicUpdate` that sets `current_project_id` to the materialized project — i.e., the
   committed intention actually wins arbitration and gets committed via the *unmodified*
   `evaluate_project_switch()` path (mirrors `test_active_contract_wins_arbitration_with_no_current_project`
   / `test_active_region_stabilization_wins_arbitration_with_no_current_project`'s existing pattern).
   Location: `tests/unit/strategic/test_committed_intention_materialization.py` (new file, following
   the naming/structure of `test_adventure_route_materialization.py` /
   `test_social_contract_materialization.py` / `test_region_stabilization_materialization.py`)

4. **`test_committed_intention_materializes_with_raw_score_not_utility`**
   Category: unit
   Verifies: the materialized `ProjectState.score` is NOT the normalized tier-5 `utility` value —
   guards against the `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect class
   recurring in a fourth materialization path (mirrors the three existing
   `test_*_winner_materializes_with_raw_score_not_utility` tests).
   Location: `tests/unit/strategic/test_committed_intention_materialization.py`

5. **`test_losing_committed_intention_retries_next_eligible_tick`** *(the ticket's explicitly
   required regression test)*
   Category: unit
   Verifies: given a high-lock, high-score current project and a committed intention whose
   synthesized candidate loses that tick's arbitration (via the unmodified
   `evaluate_project_switch()`), the resulting `committed_intentions` state (read back from the
   `StrategicUpdate`, or from `StrategicComponent` after applying it) still has the same entry at
   `sequence_index == 0` with `status` unchanged (not `"abandoned"`/removed) — proving the "stays
   queued, doesn't get discarded" semantics live in the new tracking, not in
   `evaluate_project_switch()`. Should assert across *two* simulated ticks: tick N loses, tick N+1
   (unchanged world state) the same entry is still there and eligible to compete again.
   Location: `tests/unit/strategic/test_committed_intention_materialization.py`

6. **`test_evaluate_project_switch_byte_identical_diff_guard`**
   Category: architecture guard
   Verifies: a structural guard (e.g., hash/AST-compare the `evaluate_project_switch` function body,
   or — simpler and consistent with AC3's own stated verification method — a test that documents and
   asserts the specific line range of `evaluate_project_switch` via `inspect.getsource()` matches a
   golden string/hash captured pre-implementation) that the arbiter function's own body was not
   modified by this ticket. If an AST/source-hash guard is judged too brittle for CI, this can
   instead be a documented manual `git diff --stat` check recorded in the ticket's Implementation
   Notes — Plan should decide which, but the AC's own wording implies an empirical (not just
   citation-based) check is required.
   Location: `tests/unit/strategic/test_committed_intention_materialization.py` or
   `tests/architecture/` if an existing architecture-guard test directory exists (check at
   Plan/Implement time)

7. **`test_committed_intentions_participate_in_routine_role_boosting`**
   Category: unit
   Verifies: the synthesized `GoalScore` for a committed intention receives the same
   `RoutineService.get_routine_utility_boost`/`get_role_utility_boost` treatment as any live-scorer
   candidate (confirms injection happens before `intelligence.py:1397`'s comprehension, not after).
   Location: `tests/unit/strategic/test_committed_intention_materialization.py`

8. **`test_duplicate_goal_kind_committed_intention_and_live_scorer_coexist`**
   Category: unit
   Verifies: when a committed intention reuses a `GoalKind` that also has a currently-registered
   live scorer producing a candidate the same tick, both entries appear in the sorted candidate list
   without crashing, and the higher-utility one wins deterministically (re-verifies the design doc's
   traced duplicate-tolerance claim end-to-end, not just by code inspection).
   Location: `tests/unit/strategic/test_committed_intention_materialization.py`

9. **`test_max_committed_intentions_cap_enforced`**
   Category: unit
   Verifies: whatever cap-enforcement mechanism Plan selects for Open Question 1 (recommended:
   `CapacityEnforcementPhase`-style pipeline enforcement, sequence-order-preserving trim — see
   Investigation Risks) actually prevents `committed_intentions` from exceeding
   `profile.max_committed_intentions`.
   Location: `tests/unit/strategic/test_committed_intention_model.py` or
   `tests/unit/engine/pipeline_phases/` (match wherever existing `CapacityEnforcementPhase` tests for
   `max_active_projects` etc. live — locate at Implement time)

10. **`test_committed_intentions_included_in_replay_fingerprint`**
    Category: integration
    Verifies: `StateFingerprinter._strategic_identity()` includes `committed_intentions` in its
    output string, and two otherwise-identical `AuthoritativeState`s with different
    `committed_intentions` produce different `state_hash` values (closing the replay-fidelity gap
    identified in Investigation).
    Location: `tests/integration/kernel/test_p1_replay_fidelity.py` (extend) or
    `tests/unit/replay/` if a unit-level fingerprint test file already exists (check at Implement
    time)

11. **`test_builder_supports_committed_intentions`**
    Category: unit
    Verifies: `V2EntityBuilder.strategic(committed_intentions=...)` round-trips correctly, enabling
    the other new tests above to construct fixtures without hand-building `StrategicComponent`
    directly.
    Location: `tests/unit/core/` (wherever existing `V2EntityBuilder` tests live — check at
    Implement time) or inline setup in `test_committed_intention_materialization.py` if no builder
    test file exists

12. **`test_committed_intention_observability_surface`**
    Category: unit
    Verifies: whatever minimal surface Plan chooses for Open Question 5 (recommended:
    `EntityInspector.strategic_summary["committed_intentions_count"]`, mirroring
    `blockers_count`/`contracts_count`/`leads_count`) is populated correctly.
    Location: wherever existing `EntityInspector` tests live (check at Implement time; none were
    found already covering `strategic_summary` during this Investigate pass — flag as a possible
    net-new test file if so)

**Open-question-resolution tests** (exact test names/locations depend on Plan's actual decisions for
Open Questions 2 and 3 — cannot be fully specified until Plan resolves them, but the *coverage
requirement* is fixed):
- A test proving the chosen mid-sequence-skip abandonment behavior (Open Question 2) — whatever
  Plan decides, it must be asserted, not left implicit.
- A test proving the chosen `target_hint` re-resolution-failure behavior (Open Question 3) —
  recommended precedent-consistent behavior is "no-op this tick, retry next tick, same as a losing
  arbitration," but Plan's actual decision must be the thing under test.

## Scoped Pytest Commands

```
# Primary domain — strategic cognition unit tests
pytest tests/unit/strategic/ -v

# Capacity/builder plumbing (only if those files are touched, per Investigation's durable-state gap)
pytest tests/unit/engine/pipeline_phases/ -v -k "capacity or Capacity"
pytest tests/unit/core/ -v -k "builder or Builder"

# Replay-fidelity guard (only if fingerprint.py is touched)
pytest tests/integration/kernel/test_p1_replay_fidelity.py -v

# Adventure-domain cross-check (tier-5 candidate list is now a 4-source shared list)
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v

# STRAT-185/186/187 specific re-verification (AC6)
pytest tests/unit/strategic/test_score_normalization.py -v
```

Never `pytest tests/`. Scope stays within `tests/unit/strategic/`, the touched plumbing directories,
and the adventure-domain cross-check — this ticket does not touch combat, economy, or world-evolution
subsystems.

## Anti-Drift Test Guards

- **`test_evaluate_project_switch_byte_identical_diff_guard`** (New Test 6) is itself the primary
  anti-drift guard for AC3's "unmodified arbiter" requirement — without it, a future refactor could
  silently reintroduce kind-based special-casing inside `evaluate_project_switch()` and nothing
  would catch it.
- Re-running **`test_adventure_route_materialization.py`**, **`test_social_contract_materialization.py`**,
  **`test_region_stabilization_materialization.py`** unmodified after this ticket lands is itself an
  anti-drift guard: if adding a fourth candidate source to the tier-5 list breaks any of these three
  existing per-kind branches (e.g., via an ordering assumption in `modified_scores.sort()` that a
  new duplicate-kind entry violates), these tests catch it.
- **New Test 8** (duplicate-`GoalKind` coexistence) directly guards against silent regression of the
  design doc's own traced safety claim — this is the one place a future change to `.kind` handling in
  `all_scores`/`modified_scores` (e.g., someone "fixing" the apparent duplicate by de-duping) would be
  caught as a behavior change.
- **New Test 10** (replay fingerprint) guards against the silent replay-fidelity gap identified in
  Investigation — without it, nothing in the existing suite would notice `committed_intentions` is
  invisible to determinism verification.
- Running `test_evaluate_project_switch_state_threading_guard.py` unmodified guards against the
  materialization hook accidentally threading `state` into a code path that changes the 27
  pre-existing `state=None` call sites' behavior.
