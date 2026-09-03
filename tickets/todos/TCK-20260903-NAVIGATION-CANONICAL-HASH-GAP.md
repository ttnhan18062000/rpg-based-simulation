---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP
phase: open
date: 2026-09-03
tags: [determinism]
---

# TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP

## Title
NavigationComponent's canonical hash covers only 3 of 13 real fields (target, path, moved_recently)

## Status
OPEN

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
- [ ] All uncovered fields have an explicit, recorded decision (covered or justified-excluded).
- [ ] `position` and `region_id` specifically get resolved with clear reasoning given their apparent
      behavioral significance.
- [ ] New or updated determinism tests demonstrate the fix catches a divergence in each added field.
- [ ] Existing canonical-hash/replay determinism tests still pass unchanged.
- [ ] Any other hand-rolled fast-constructor for `NavigationComponent` is checked/updated for
      consistency with the new field set.
- [ ] Parity ledger entry added with real evidence.

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

## Test Summary

## Files Changed

## Completion Summary
