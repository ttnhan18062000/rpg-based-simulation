---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND
phase: open
date: 2026-08-29
tags: [combat, observability]
---

# TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND

## Title
`event_extractor.py`'s wound/scar diff blocks are `isinstance(x, list)`-gated, but the real apply
path always commits tuples -- no `wound_sustained`/`wound_healed`/`scar_gained` event has ever
fired through a real `Kernel.tick_once()` run

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found live during `TCK-20260824-WOUND-HEALING-DECISION` (`m1-quick-wins` batch), while attempting
to prove via a real `Kernel.tick_once()` run that wound-related events fire correctly.
`src/observability/event_extractor.py:280-281,302-303` gate the wound and scar diff-extraction
blocks with `entity.combat.wounds if isinstance(entity.combat.wounds, list) else []` (and the
matching pattern for `.scars`). But `WoundPatch.apply()` (`src/engine/patches.py:638`) always
commits via `replace(new_com, wounds=tuple(new_wounds), scars=tuple(new_scars))`, and
`AuthoritativeState`'s freeze logic (`src/core/state.py:846`) explicitly coerces both fields to
`tuple` if they aren't already. So `isinstance(entity.combat.wounds, list)` is **always `False`** on
real, frozen, authoritative state -- `entity_wounds`/`prior_wounds`/`entity_scars`/`prior_scars` are
always `[]`, and the `wound_sustained`, `wound_healed`, and `scar_gained` event-emission blocks
(lines ~282-307) never produce a single event, regardless of real wound/scar state changes. The same
file already uses the correct `isinstance(x, (list, tuple))` pattern elsewhere (confirmed at lines
~1499, ~1583), confirming this is an inconsistency/bug in this one spot, not an intentional
list-only contract.

## Scope
- Fix the `isinstance(x, list)` checks at `event_extractor.py:280-281,302-303` to
  `isinstance(x, (list, tuple))`, matching the pattern already used correctly elsewhere in the same
  file
- Add a real, non-mocked `Kernel.tick_once()` regression test proving `wound_sustained` fires when a
  wound is inflicted in a real tick (this is the exact proof `TCK-20260824-WOUND-HEALING-DECISION`'s
  plan needed and could not produce because of this bug)
- Correct `docs/parity_ledger/combat_movement.yaml` COMB-296 and `docs/event_ledger/entity.yaml`
  ENTITY-018 to reflect the real, now-fixed producer status for `wound_sustained` (this ticket's own
  fix) -- coordinate with `TCK-20260824-WOUND-HEALING-DECISION`'s own correction of the same two
  entries for `wound_healed`'s zero-producer status (wounds are permanent, so `wound_healed` stays
  correctly zero-producer; only `wound_sustained`/`scar_gained` become real via this fix) so the two
  tickets' edits to the same entries don't conflict -- whichever lands second should read the other's
  landed state first

## Out of Scope
- The wound-healing-permanence decision itself (owned by `TCK-20260824-WOUND-HEALING-DECISION`,
  already decided: wounds are permanent, no healing)
- The `should_inflict_wound()` 40% threshold dead-code decision (owned by
  `TCK-20260824-WOUND-THRESHOLD-DECISION`)

## Acceptance Criteria
- [ ] `event_extractor.py`'s wound/scar diff blocks use `isinstance(x, (list, tuple))`, matching the
      pattern already correct elsewhere in the file
- [ ] A real, non-mocked `Kernel.tick_once()` test proves `wound_sustained` fires when a wound is
      inflicted in a real tick
- [ ] COMB-296/ENTITY-018 are corrected to reflect the real producer status post-fix, coordinated
      with `TCK-20260824-WOUND-HEALING-DECISION`'s own edits to the same entries

## Related Tickets
- TCK-20260824-WOUND-HEALING-DECISION (where this was found live; also edits COMB-296/ENTITY-018)
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (already landed; wounds now carry real severity-scaled
  penalties, making this event-visibility bug more consequential than before)

## Related Docs
- docs/parity_ledger/combat_movement.yaml
- docs/event_ledger/entity.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/event_extractor.py
- src/engine/patches.py
- src/core/state.py

## Assumptions / Open Questions
None -- self-evident intent, minimal targeted fix (a 2-line isinstance widening, matching an
existing correct pattern in the same file) plus a real regression test.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
