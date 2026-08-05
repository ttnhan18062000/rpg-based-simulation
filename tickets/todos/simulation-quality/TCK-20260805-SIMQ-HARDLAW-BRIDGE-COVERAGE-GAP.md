---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP
phase: open
date: 2026-08-05
tags: [simulation-quality, observability, world]
---

# TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP

## Title
6 of 7 real HardLawMonitor laws have no SimQ translation; 2 wired scorer signals wait for law_id prefixes no real law uses

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While re-examining SimQ's "engine-correctness bridge" extension axis, found the real picture is
more concrete than previously documented. `src/simulation_quality/quality_hub.py::_translate_invariant()`
is the dispatcher that turns raw `InvariantViolation` events into SimQ-scorable event types. It has
exactly 3 branches:

```python
if law_id.startswith("COMBAT"): return "combat_hard_law_violation"
if law_id.startswith("CONSERVATION"): return "conservation_law_violated"
if law_id.startswith("LAW-SPAWN-OCCUPANCY"): return "spawn_occupancy_violation"
return env.event_type  # unknown violation — no translation
```

`docs/observability/hard_law_monitor.md` lists the 7 real, currently-enforced laws:
`LAW-HP-NONNEGATIVE`, `LAW-READINESS-NONNEGATIVE`, `LAW-GOLD-NONNEGATIVE`,
`LAW-STAMINA-NONNEGATIVE`, `LAW-POSITION-FINITE`, `LAW-OCCUPANCY-COLLISION`,
`LAW-SPAWN-OCCUPANCY`. **None of the first 6 start with "COMBAT" or "CONSERVATION"** — so:

- **6 of 7 real, currently-firing laws fall through to `return env.event_type`** (raw
  `"InvariantViolation"`), which no scorer's `EVENT_TYPES` includes (confirmed via grep across
  `src/simulation_quality/scorers/`) — these violations are completely invisible to SimQ today.
- **2 scorer signals are fully wired and ready, but dead**: `combat_hard_law_violation`
  (`CombatScorer`, COMBAT pillar) and `conservation_law_violated` (`EconomyScorer`, ECONOMY
  pillar) both exist in their respective scorers' `EVENT_TYPES` and `score()` methods, but nothing
  ever produces a `COMBAT-*` or `CONSERVATION-*` `law_id` to trigger them. `docs/plans/
  idea_placement_legality_check.md` (an unrelated prior investigation) independently noticed the
  `CONSERVATION` branch specifically and speculated a law was "once planned... and never actually
  implemented" — consistent with what's found here.
- Only `LAW-SPAWN-OCCUPANCY` is actually bridged (`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`, routes to
  WORLD DYNAMICS pillar as `spawn_occupancy_violation`) — the one case
  `docs/simulation_quality/extension_points.md`'s original axis 9 write-up cited as "the existing
  bridge." This ticket is about the other 6 laws and the 2 dormant dispatch branches.

## Scope
- For each of the 6 untranslated laws, determine (a) whether it's a good candidate for a SimQ
  frequency bridge at all (per the established precedent's own reasoning: SimQ scores *how often*
  something occurs, not whether one instance is legal — a correctness/frequency-gradient
  distinction, not "any violation deserves a signal"), and (b) if so, which pillar should own it
  (HP/READINESS-NONNEGATIVE are combat-adjacent → COMBAT is a plausible owner, matching the
  already-wired but dormant `combat_hard_law_violation` signal; GOLD-NONNEGATIVE is
  economy-adjacent → ECONOMY, matching the already-wired `conservation_law_violated` signal;
  STAMINA-NONNEGATIVE is biological; POSITION-FINITE and OCCUPANCY-COLLISION are
  world/movement-adjacent — these three have no obvious existing dormant signal to reuse).
- Decide whether to extend `_translate_invariant()`'s existing `COMBAT`/`CONSERVATION` prefix
  branches to also match the real law_ids that semantically fit (e.g. does `LAW-HP-NONNEGATIVE`
  starting with `"LAW-"` not `"COMBAT"` mean the dormant branch was written for a naming convention
  that was never adopted — should the real law_ids be renamed, or should the dispatcher match on
  something other than a literal prefix?), versus adding new dedicated branches/pillar signals for
  laws that don't fit the existing dormant branches.
- Implement whichever bridges are justified by the investigation, following the exact,
  already-established pattern from `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (translate → add to
  scorer's `EVENT_TYPES` → add one pillar contract table row → recalibrate anchors for any world
  where the new signal now fires).
- Update `docs/simulation_quality/extension_points.md`'s axis 9 with the precise, corrected picture
  from this ticket (currently understates the gap as "not yet exercised beyond this one case").

## Out of Scope
- Any change to `HardLawMonitor` itself, the 7 laws' detection logic, or their severity/mode-gating
  behavior — this ticket only concerns whether/how their violations reach SimQ, not whether the
  laws themselves are correct.
- The separate, already-known `LONG_RUN` mode gap noted in `hard_law_monitor.md` (violations
  persisted but neither logged nor raised in `LONG_RUN` mode) — unrelated to SimQ translation,
  already documented as a known gap in that file; out of scope here unless a future investigation
  finds it's actually the same root cause (not assumed).
- A hypothetical future 8th law — this ticket is scoped to the 7 that exist today.

## Acceptance Criteria
1. Each of the 6 currently-untranslated laws has an explicit, documented decision (bridge it, to
   which pillar, or explicitly decline with reasoning) — not silently left as-is without a written
   rationale.
2. Any new bridge implemented follows the existing `_translate_invariant()` → scorer `EVENT_TYPES`
   → pillar contract table pattern exactly, with anchors recalibrated for any affected world.
3. The 2 currently-dormant `COMBAT`/`CONSERVATION` dispatch branches are either connected to a real
   law (if AC1 decides HP/READINESS/GOLD-NONNEGATIVE etc. should feed them) or explicitly
   documented as intentionally dormant with reasoning (not left unexplained).
4. `docs/simulation_quality/extension_points.md`'s axis 9 is updated to reflect whatever the final
   state is after this ticket, replacing the current understated "not yet exercised" framing.

## Related Tickets
- `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` — established the exact pattern this ticket reuses; the
  only law currently bridged.
- `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` — confirmed no 11th pillar is needed; this ticket's
  bridges route to existing pillars only, consistent with that finding.

## Related Docs
- `docs/observability/hard_law_monitor.md` — the 7 real laws, their scope and severity.
- `docs/simulation_quality/extension_points.md` §9 (Engine-correctness bridge) — needs correction
  per this ticket's findings.
- `docs/plans/idea_placement_legality_check.md` — independently noticed the dormant `CONSERVATION`
  branch; not this ticket's dependency, but corroborating context.

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `src/simulation_quality/quality_hub.py` (`_translate_invariant()`)
- `src/simulation_quality/scorers/combat.py`, `economy.py` (dormant `EVENT_TYPES` entries)
- `src/observability/hard_law_monitor.py` (7 real laws — read-only reference, not modified)

## Assumptions / Open Questions
- Whether the `COMBAT`/`CONSERVATION` prefix branches were ever meant to match real law_ids under
  a different naming scheme, or were speculative/aspirational additions with no real law ever
  planned to match them, is not resolved here — the investigation phase must determine this (e.g.
  via git blame / commit history on `_translate_invariant()`) before deciding whether to repurpose
  them or add new branches alongside them.

## Implementation Notes
(fill during implementation)

## Test Summary
(fill during implementation)

## Files Changed
(fill during implementation)

## Completion Summary
(fill during implementation)
