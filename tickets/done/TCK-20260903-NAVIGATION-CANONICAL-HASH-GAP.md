---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP
phase: done
date: 2026-09-03
tags: [determinism]
---

# TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP

## Title
NavigationComponent's canonical hash covers only 3 of 13 real fields (target, path, moved_recently)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while implementing `TCK-20260902-PLACE-SCHEMA-MIGRATION` (adding `NavigationComponent.place_id`):
`EntityState.to_canonical_dict()`'s `"navigation"` sub-dict (`src/core/state.py`) covers only `target`,
`path`, and `moved_recently` out of `NavigationComponent`'s 13 real fields. Uncovered:
`position`, `movement_mode`, `last_failure_reason`, `wait_count`, `oscillation_count`, `last_position`,
`home_position`, `leash_radius`, `region_id`, `chase_ticks`, `max_chase_ticks`, `returning_home`.

This is the same shape as the Social/Knowledge canonical-hash gaps closed 2026-09-02/03
(`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`, `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`), but larger and
in a third component — not scoped by either of those tickets. `region_id` specifically is notable: it's
a cached back-reference field (`"Phase 3 Hardening: Cache region_id to avoid O(N) scans"`) that entities
are gated on in real movement/routine logic (`src/systems/world_systems/routine.py`), so a same-seed
divergence there could go undetected the same way `source_trust` did before its fix. `position` itself
being uncovered is also notable — an entity's actual spatial location not participating in the
determinism hash at all is a significant gap if true (needs confirming it isn't covered indirectly via
some other path before assuming it's as severe as it looks).

The new `place_id` field added by `TCK-20260902-PLACE-SCHEMA-MIGRATION` was given explicit canonical
coverage specifically so it would NOT inherit this pre-existing gap — see the code comment at its
canonical-dict entry.

## Scope
- Re-verify the exact field list and gap against current `NavigationComponent`
  (`src/core/state.py`) at pickup time (state may have changed since 2026-09-03).
- For each uncovered field, decide: add to the `"navigation"` canonical sub-dict, or document why
  legitimately excluded (e.g. `last_position`/`wait_count`/`oscillation_count` may be purely
  presentation/congestion-recovery bookkeeping with no independent authoritative meaning — needs a real
  per-field decision, not assumed).
- Confirm whether `position` is genuinely uncovered by this specific dict, or covered indirectly by
  some other canonical-dict path before treating it as the most severe finding.
- Check whether any hand-rolled fast-constructor for `NavigationComponent` (e.g.
  `ApplyPath._fast_replace_navigation`, `src/engine/apply.py`) needs updating for any newly-added field —
  this exact class of bug was hit and fixed while adding `place_id` (a hardcoded field list that predated
  the new field, causing an `AttributeError` at runtime under the custom fast-replace path used by
  `src/engine/apply.py`'s tick-apply pipeline).
- Update `docs/parity_ledger/` (likely `combat_movement.yaml` or `substrate.yaml` — confirm the right
  shard) via `tools/parity_ledger_writer.py`.

## Out of Scope
- Any change to `NavigationComponent`'s own field semantics or movement/pathfinding behavior — coverage
  only, same discipline as the Social/Knowledge tickets.
- A general audit of every other component's canonical-hash coverage — this ticket is scoped to
  `NavigationComponent` specifically, found as a direct byproduct of idea 66 work.

## Acceptance Criteria
- [x] All uncovered fields have an explicit, recorded decision (covered or justified-excluded). All 11
      confirmed live via direct grep of every real consumer site and added; none excluded (unlike the
      parallel Knowledge-gap fix's `profile` exclusion — no derived/reconstructable field exists here).
- [x] `position` and `region_id` specifically get resolved with clear reasoning given their apparent
      behavioral significance. `position` was already covered (top-level `to_canonical_dict()` key, not
      the severe gap feared). `region_id` added, plus a dedicated end-to-end test given its confirmed
      real-logic gating role.
- [x] New or updated determinism tests demonstrate the fix catches a divergence in each added field.
      2 new tests: an 11-field per-field divergence sweep, plus a `region_id` end-to-end
      `CanonicalStateHasher.get_hash()` test.
- [x] Existing canonical-hash/replay determinism tests still pass unchanged. 564 passed, 2 skipped
      (pre-existing, unrelated), 0 failed across the scoped sweep; 15 passed, 0 failed on the
      integration determinism/checkpoint/replay suites.
- [x] Any other hand-rolled fast-constructor for `NavigationComponent` is checked/updated for
      consistency with the new field set. `ApplyPath._fast_replace_navigation` checked directly —
      already copies all 16 real fields correctly, no fix needed.
- [x] Parity ledger entry added with real evidence. `COMB-320` added to `combat_movement.yaml` via
      `tools/parity_ledger_writer.py`, index confirmed FRESH.

## Related Tickets
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP (same shape, closed)
- TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP (same shape, closed)
- TCK-20260902-PLACE-SCHEMA-MIGRATION (where this gap was discovered)

## Related Docs
- `docs/core/state.md`
- `docs/parity_ledger/` (shard to be confirmed at pickup)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/state.py` (`EntityState.to_canonical_dict()`, `"navigation"` sub-dict; `NavigationComponent`)
- `src/engine/apply.py` (`ApplyPath._fast_replace_navigation` — the hand-rolled fast-constructor found
  fragile against new fields during this ticket's own discovery)
- `src/engine/checkpoint.py` (`CanonicalStateHasher`)

## Assumptions / Open Questions
- Whether `position` is truly uncovered or covered via some indirect path is the first thing to confirm
  — not assumed here, flagged as the most consequential open question.
- Whether any fields (e.g. congestion-recovery bookkeeping: `wait_count`, `oscillation_count`,
  `last_position`) are legitimately non-authoritative/presentation-only — needs real investigation, not
  a default-include assumption like the Social/Knowledge tickets used (those had no ambiguous cases;
  this component might).

## Implementation Notes
Re-verified against current code first (per the ticket's own note that state may have drifted):
`NavigationComponent` has 16 real fields, not 13 — `place_id` was added by
`TCK-20260902-PLACE-SCHEMA-MIGRATION` since the original finding, and `position` was already covered
(as a separate top-level `to_canonical_dict()` key, `"position": self.navigation.position` — resolving
the ticket's own most-consequential open question: it is NOT the severe uncovered-spatial-location gap
that was feared).

Real gap: 11 fields — `movement_mode`, `last_failure_reason`, `wait_count`, `oscillation_count`,
`last_position`, `home_position`, `leash_radius`, `region_id`, `chase_ticks`, `max_chase_ticks`,
`returning_home`. Checked each field's liveness by grepping its real consumer sites before adding it,
per the ticket's own instruction not to default-include:
- `region_id` (the ticket's flagged highest-risk field): gates `src/domains/memory/phase.py`,
  `src/domains/information/phase.py`, `src/engine/semantic_entity_index.py`,
  `src/engine/pipeline_phases/actions.py` (combat), `src/observability/live/entity_inspector.py`.
- `movement_mode`, `wait_count`, `oscillation_count`, `last_position`: gate congestion-recovery
  replanning and target resolution in `src/engine/movement.py`, `src/engine/candidate_selector.py`,
  `src/engine/pipeline_phases/movement.py`, `src/systems/strategic_systems/work_queue.py`,
  `src/systems/strategic_systems/intelligence.py`.
- `home_position`, `leash_radius`, `chase_ticks`, `max_chase_ticks`, `returning_home`: gate mob-leash
  chase logic in `src/engine/rpg_depth.py`.
- `last_failure_reason`: feeds `StrategicIntelligenceSystem.infer_blockers()` — a real, independent
  input to already-covered `StrategicComponent.blockers`, not a redundant debug string.

All 11 confirmed live; none excluded (unlike the parallel Knowledge-gap fix, which excluded `profile` as
derived — no equivalent derived field exists in `NavigationComponent`).

`ApplyPath._fast_replace_navigation` (`src/engine/apply.py:556-574`) — the exact class of bug hit once
before while adding `place_id` (a stale hardcoded field list causing a runtime `AttributeError`) — was
checked directly and already copies all 16 real fields correctly. No fix needed.

Assessed whether the fix's hash-output change requires regenerating committed
`world_compile_report.json`'s `canonical_state_hash` values across all 21 worlds (added by idea 66's
Stage A, consumes `CanonicalStateHasher`): confirmed no test asserts an exact hash literal against a
committed baseline — every consumer recomputes and compares at test time. No regeneration needed,
consistent with the fixture-staleness pattern already tracked in
`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`.

## Test Summary
- 2 new tests in `tests/unit/core/test_entity_integrity.py`:
  `test_navigation_eleven_newly_covered_fields_participate_in_canonical_hash` (per-field divergence
  sweep, all 11 fields) and `test_navigation_region_id_participates_in_canonical_hash_end_to_end`
  (confirms the fix reaches `CanonicalStateHasher.get_hash()`, the real per-tick/final-run consumer).
- Full scoped sweep: `pytest tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/
  -m "not slow"` → 564 passed, 2 skipped (pre-existing, unrelated), 0 failed.
- Integration sweep: `pytest tests/integration/kernel/test_determinism_suite.py
  tests/integration/kernel/test_checkpoint_reproducibility.py
  tests/integration/kernel/test_replay_fidelity.py -m "not slow"` → 15 passed, 0 failed.

## Files Changed
- `src/core/state.py` — `EntityState.to_canonical_dict()`'s `"navigation"` sub-dict: added 11 fields.
- `tests/unit/core/test_entity_integrity.py` — 2 new tests.
- `docs/parity_ledger/combat_movement.yaml` — new entry `COMB-320`, written via
  `tools/parity_ledger_writer.py`.
- `tickets/todos/TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP.md` → moved to `tickets/done/` (via
  `tickets/inprogress/`).

## Completion Summary
Closed the `NavigationComponent` canonical-hash coverage gap — the last of three same-shaped gaps found
during idea 66 work (Social, Knowledge, and now Navigation). Real gap was 11 fields, not the originally
estimated 12 (the original finding's `position` was already covered indirectly, and `place_id` was added
between the finding and pickup). All 11 confirmed live via direct consumer-site verification and added,
none excluded — `region_id` (the flagged highest-risk field) now participates in the same
`CanonicalStateHasher` per-tick/final-run determinism check `src/engine/kernel.py` uses. Checked
`ApplyPath._fast_replace_navigation` for the exact fast-constructor bug class hit once before; confirmed
already correct, no fix needed. 2 new tests lock in the fix; full existing determinism/replay/
certification suite passes unchanged.
