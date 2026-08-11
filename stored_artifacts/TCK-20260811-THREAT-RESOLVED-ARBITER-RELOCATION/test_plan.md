---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION
artifact_type: test_plan
tags: [cognition, adventure]
---

# Test Plan — TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION

## Regression Surface

### Unit — strategic (`evaluate_project_switch` / interruption resistance)
Must keep passing byte-identical, unmodified, if the recommended `Optional[AuthoritativeState] =
None` design (see investigation.md, Risks and Open Questions) is adopted — this is the whole point
of that recommendation:
- `tests/unit/strategic/test_score_normalization.py` (6 `evaluate_project_switch()` call sites — lines 52, 73, 110, 140, 173, 181)
- `tests/unit/strategic/test_interruption_resistance.py` (13 call sites — lines 49, 62, 74, 92, 100, 118, 124, 169, 186, 203, 230, 249, 268)
- `tests/unit/strategic/test_project_continuity.py` (5 call sites — lines 47, 55, 76, 83, 88)
- `tests/unit/strategic/test_strategic_reprioritization.py` (1 call site — line 46)
- `tests/unit/systems/test_quest_activation_pathway.py` (2 call sites — lines 228, 283)

If Plan instead chooses option (a) (require `state`), **all 27 of the above call sites become
in-scope edits**, not just regression surface — re-flag this to Plan explicitly since it changes
the blast radius of the whole ticket.

### Unit — adventure domain (existing `_threat_resolved` / lock-release coverage)
- `tests/unit/systems/test_spawn_lock_condition.py` — all 4 test classes
  (`TestLockEarlyRelease`, `TestLockHeldWhenThreatActive`, `TestLockExpiryByTime`). This is
  STRAT-236's current `test_path` and exercises `_threat_resolved` indirectly via
  `AdventureDecisionPhase.apply()` (`phase.py:151`'s own gate, untouched by this ticket) — must
  keep passing unmodified after the relocation, since `phase.py:151` still calls whatever
  `_threat_resolved` resolves to (either a relocated import from `intelligence.py`, or — if
  relocation removes the `phase.py` symbol entirely — `phase.py`'s import statement must be
  updated to import from the new location; either way the *behavior* this test asserts is
  unchanged).
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` — both tests
  (`test_apply_commit_branch_does_not_construct_strategic_update_directly`,
  `test_apply_module_imports_strategic_intelligence_system`). Confirmed via full read: AST-matches
  on callee name only, not arguments — adding `state` to the `phase.py:192` call site does not
  require any change to this file's assertions. Included here as regression surface specifically
  to catch an accidental behavioral change to the call shape that *would* break these guards (e.g.
  someone starts constructing `StrategicUpdate(...)` directly at the `phase.py:192` site instead of
  passing through `evaluate_project_switch`).

### Architecture / integration
- `tests/tools/test_parity_ledger_scan.py` — generic schema/structure validator for all
  `docs/parity_ledger/*.yaml` files, including `strategic_cognition.yaml`. Must keep passing after
  STRAT-236's `text`/`v2_evidence` edit (AC4) — confirms the YAML stays well-formed and
  schema-conformant, not that the content is semantically correct (that's this ticket's own
  responsibility, verified by hand/parity-updater agent, not by this scanner).
- `tests/integrity/test_parity_guards.py` — broader parity/integrity guard suite; scope only if it
  touches `strategic_cognition.yaml` content (verify at Implement time; included here defensively
  since it's cheap to include in the scoped run).

## New Tests Required

### AC1 — signature gains `state`, all 3 real production call sites thread it, no raw/unlocked-path behavior change

- **Test name**: `test_evaluate_project_switch_signature_accepts_state_kwarg`
  **Category**: unit
  **Verifies**: `evaluate_project_switch(entity, candidate, current_tick, state=state)` is a valid
  call (signature accepts the new param) and, separately, that calling it with the recommended
  `Optional[...] = None` default and no `state` arg still succeeds (backward-compat smoke test for
  the 27 untouched call sites' calling convention).
  **Location**: `tests/unit/strategic/test_interruption_resistance.py` (co-located with the other
  direct-call tests of this function).

- **Test name**: `test_evaluate_project_switch_unlocked_path_identical_with_and_without_state`
  **Category**: unit (regression guard)
  **Verifies**: for an *unlocked* current project (`current.lock_until_tick <= current_tick`), the
  raw comparison result (`candidate_project.score > effective_current_score`) is byte-identical
  whether `state` is passed or omitted — proves the new param cannot leak into the unlocked path,
  which AC1 explicitly requires to be unaffected.
  **Location**: `tests/unit/strategic/test_interruption_resistance.py`.

- **Test name**: `test_three_production_call_sites_thread_state_argument`
  **Category**: architecture guard (AST-based, mirroring `test_phase3_project_switch_routing_guard.py`'s
  existing pattern)
  **Verifies**: via `ast.parse`/`ast.walk` over `inspect.getsource(AdventureDecisionPhase.apply)`
  and `inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent)`, every
  `Call` node whose callee resolves to `evaluate_project_switch` carries a `state` argument
  (either positional-4th or an explicit `state=` keyword) — fails loudly if a future edit adds a
  4th call site that forgets to thread `state`, or if one of the 3 known sites regresses.
  **Location**: new file `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py`
  (new dedicated architecture-guard file, following this repo's existing `test_phase3_project_switch_routing_guard.py`
  naming/structure convention rather than overloading an unrelated existing file).

### AC2 — locked + HP>80% + no hostile within radius 10.0 → lock treated as expired, falls to raw comparison, byte-identical to today's adventure-only behavior

- **Test name**: `test_evaluate_project_switch_locked_project_released_when_threat_resolved`
  **Category**: unit
  **Verifies**: directly at the `evaluate_project_switch()` level (not via `AdventureDecisionPhase`)
  — a locked current project (`lock_until_tick > current_tick`), entity `combat.hp/max_hp > 0.8`,
  no hostile entity in `state.entities` within radius 10.0 of `hero.navigation.position` → the
  locked-branch percentage/urgency-floor gate is skipped entirely and the raw comparison
  (`candidate_project.score > effective_current_score`) alone determines the outcome. Construct
  both a candidate that would fail the *old* percentage gate but pass the *raw* comparison, to
  prove the short-circuit is real and not accidentally equivalent to the pre-existing gate.
  **Location**: `tests/unit/strategic/test_interruption_resistance.py`.

- **Regression confirmation (no new test, but explicit re-run required)**:
  `tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles`
  must still pass unmodified post-relocation — this is the "byte-identical to today's
  AdventureDecisionPhase-only behavior for adventure-originated projects" half of AC2, already
  covered by existing coverage; do not weaken or rewrite this test to make the relocation pass.

### AC3 — COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure (System B) system, threat resolved → now also early-released (the ticket's headline new regression test)

- **Test name**: `test_combat_retreat_project_locked_via_system_b_early_released_when_threat_resolved`
  **Category**: unit (new behavior regression — this is the test that proves the
  STRAT-236-documented-but-never-wired gap is closed)
  **Verifies**: construct an entity with a current `ProjectState(kind=GoalKind.COMBAT_RETREAT, ...)`
  (or `GoalKind.RECOVER` — use the actual enum member from `src/core/strategic.py:129-130`, not the
  raw string, per `_score_scale_max`'s class-identity classification) locked via a direct call
  (i.e. never routed through `AdventureDecisionPhase` — the point of this test is that the caller
  is *not* the adventure domain), `lock_until_tick > current_tick`, entity HP > 80%, no hostile in
  `state.entities`. Call `StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate,
  current_tick, state=state)` directly with a candidate scored to clearly win the raw comparison.
  Assert the result is a `StrategicUpdate` that suspends the current project and sets
  `current_project_id_set` to the candidate — i.e. genuinely released, not just "not blocked."
  **Location**: new file `tests/unit/strategic/test_threat_resolved_lock_release.py` (dedicated
  file — this is the relocated function's own generalized-scope test surface, distinct from
  `test_spawn_lock_condition.py`'s adventure-domain-specific coverage, which stays as-is per
  Anti-Drift Hazards).

- **Test name**: `test_combat_retreat_project_locked_via_system_b_retained_when_threat_still_active`
  **Category**: unit (contrast/negative case — proves the check is genuinely conditional)
  **Verifies**: same setup as above but with HP ≤ 80% (or a hostile placed within radius 10.0) —
  the lock is still enforced, the locked-branch percentage/urgency-floor gate still runs, and (for
  a candidate that would fail that gate) the result is `None`. Prevents the AC3 test from being
  satisfied by a change that makes `_threat_resolved` always return `True` by accident.
  **Location**: `tests/unit/strategic/test_threat_resolved_lock_release.py` (same new file).

### AC4 — STRAT-236 `text` and `v2_evidence` both updated to cite the new location/scope

No new pytest test is required or meaningful here — this is a documentation-content correctness
requirement, verified by direct review of the YAML diff (parity-updater agent / Finalize review),
not by an automated assertion on prose content. The existing `tests/tools/test_parity_ledger_scan.py`
(regression surface, above) confirms the edited YAML stays schema-valid; it does not and should not
assert on `text`/`v2_evidence` semantic content.

## Scoped Pytest Commands

```bash
# Primary scoped regression + new-test run (strategic + adventure-domain + parity-scan surfaces)
pytest tests/unit/strategic/ tests/unit/systems/test_spawn_lock_condition.py tests/unit/systems/test_quest_activation_pathway.py tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py tests/tools/test_parity_ledger_scan.py -v

# If AC3's new file is added as tests/unit/strategic/test_threat_resolved_lock_release.py it is
# already covered by the tests/unit/strategic/ glob above -- no separate invocation needed.
```

Do not run `pytest tests/` — scope is strategic cognition + the adventure-domain lock-release path
+ the parity ledger scan, per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- `test_three_production_call_sites_thread_state_argument` (AC1, above) — the primary guard against
  scope creep or silent regression: catches both a missed call site and an accidentally-added 4th
  call site that forgets `state`.
- `test_evaluate_project_switch_unlocked_path_identical_with_and_without_state` (AC1, above) —
  catches the specific failure mode where `state` threading accidentally perturbs the unlocked raw
  comparison (e.g. an errant early-return or an accidental read of `state` before the lock check).
- The full existing `tests/unit/strategic/` regression surface (27 call sites across 5 files) is
  itself the anti-drift guard for the require-vs-default `state` design decision: if Plan/Implement
  picks option (a) without updating all 27, this suite fails immediately and loudly with
  `TypeError: evaluate_project_switch() missing 1 required positional argument: 'state'` — a clear,
  unambiguous signal rather than a silent behavior change.
- `test_apply_commit_branch_does_not_construct_strategic_update_directly`
  (`test_phase3_project_switch_routing_guard.py`, regression surface above) — guards against a
  future edit reintroducing a direct `StrategicUpdate(...)` construction at the `phase.py:192` site
  instead of routing through `evaluate_project_switch()`, which would silently bypass the new
  `_threat_resolved` check for adventure-originated projects specifically.
- `test_combat_retreat_project_locked_via_system_b_retained_when_threat_still_active` (AC3, above) —
  guards against the new check being implemented as an unconditional pass-through (e.g. a stray
  `not False` or a misplaced `or True`) that would make *every* locked project releasable
  regardless of actual threat state — the single highest-risk silent-behavior-change failure mode
  for this specific ticket.
