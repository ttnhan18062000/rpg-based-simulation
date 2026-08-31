---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-READINESS-SPEED-FORMULA
phase: open
date: 2026-08-31
tags: [combat, progression]
---

# TCK-20260831-READINESS-SPEED-FORMULA

## Title
Give readiness_speed a real agility-derived formula

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
readiness_speed is confirmed flat 10.0 for everyone; give it a real formula. Investigation found this isn't fully standalone — the idea's full scope (agility term plus agi_apt-modulated multiplier) has an optional dependency on idea 1/Genetics, though the base agility-only formula can ship standalone. readiness_speed is a parity-ledger-verified P1 combat-legality-gating mechanism (COMB-298), and a prior dedicated ticket explicitly ruled out rebalancing it without corpus-verified evidence.

## Scope
- Modify LevelingService.recalculate_combat_stats() (src/progression/leveling.py:76-184) to derive readiness_speed from agility (base + agility*k) instead of always the flat default.
- Ensure backward compatibility: an entity at reference/baseline agility still yields readiness_speed==10.0 so existing hardcoded test fixtures remain valid.
- Add a new regression test asserting the formula's output for >=2 distinct agility values.
- Update docs/mechanics/02_combat_laws.md §7 and parity entry COMB-298 (or a new entry) in the same session.
- State explicitly in Scope that only the base agility-only formula ships now; the full agi_apt-modulation half is deferred until idea 1/Genetics lands, not silently assumed available.
- Corpus-validate the change (e.g. via the metamorphic lab's directional pattern) before/after, rather than shipping as a bare unit-tested formula swap.

## Out of Scope
- The agi_apt-modulated multiplier half of the formula — deferred until idea 1/Genetics (M1 Quick Wins) lands.
- Any rebalancing of readiness_speed pacing beyond the agility-derivation itself — current flat pacing was confirmed intentional design by TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK.

## Acceptance Criteria
- [ ] recalculate_combat_stats() derives readiness_speed from agility (base + agility*k) instead of always the flat default — two entities with different agility produce different readiness_speed.
- [ ] Backward-compatible: an entity at reference/baseline agility still yields readiness_speed==10.0 so existing hardcoded test fixtures remain valid.
- [ ] A new regression test asserts the formula's output for >=2 distinct agility values.
- [ ] docs/mechanics/02_combat_laws.md §7 and parity entry COMB-298 (or a new entry) updated in the same session.
- [ ] Ticket scope explicitly states the base formula ships now, full agi_apt modulation deferred until idea 1/Genetics lands (not silently assumed available).

## Related Tickets
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
- TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/leveling.py
- src/core/state.py
- src/engine/apply.py
- src/engine/rpg_depth.py

## Assumptions / Open Questions
- A prior dedicated ticket explicitly ruled out rebalancing readiness_speed without corpus-verified evidence — this ticket must corpus-validate, not just unit-test.
- Availability of the full agi_apt modulation depends on idea 1/Genetics's own timing, which this ticket does not control.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
