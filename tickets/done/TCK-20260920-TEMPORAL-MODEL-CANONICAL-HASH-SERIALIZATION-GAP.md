---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260920-TEMPORAL-MODEL-CANONICAL-HASH-SERIALIZATION-GAP
phase: done
date: 2026-09-20
tags: [architecture, testing]
---

# TCK-20260920-TEMPORAL-MODEL-CANONICAL-HASH-SERIALIZATION-GAP

## Title
`TemporalModel.to_canonical_dict()` never converted `deadlines`/`cooldowns`/`stale_facts` map
entries to plain dicts — a determinism-hashing gap invisible because nothing ever populated them

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while building a real differential scenario for `TCK-20260920-MECHANISM-COGNITION-
DIFFERENTIAL-RUNTIME-VERIFICATION`'s `temporal_pressure` mechanism, per direct peer instruction to
give it its own traceable ticket rather than let it ride along inside a verification PR as an
incidental — this changes canonical-state hashing, and determinism is a hard rule in this repo, so
the fix needs to be findable on its own by anyone investigating a determinism question later.

`src/core/cognition.py::TemporalModel.to_canonical_dict()` built its `deadlines`/`cooldowns`/
`stale_facts` output via `dict(sorted(self.deadlines.items()))` etc. — this puts the raw
`DeadlineEntry`/`CooldownEntry`/`StalenessEntry` dataclass instances directly into the dict passed
to `json.dumps()`, which cannot serialize them (`TypeError: Object of type DeadlineEntry is not
JSON serializable`). `Kernel.shutdown()` calls `CanonicalStateHasher.get_hash()` unconditionally at
end-of-run, so any real state carrying a populated `deadlines`/`cooldowns`/`stale_facts` map would
have crashed a normal Kernel run at shutdown, not just this scenario's own test.

**Why this was invisible until now, itself a real signal**: nothing in `src/` had ever populated
any of these three `TemporalModel` fields in a real run before this scenario staged one directly —
confirmed by the fact that this defect has clearly existed since the fields were added (`urgency`,
the one field that *is* real-populated via `TemporalPressureService.calculate_urgencies()`, was
correctly hashable — a scalar float map, not a nested dataclass) and nothing tripped it. This is a
small piece of independent evidence corroborating `temporal_pressure`'s own `TCK-20260920-
MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` finding: essentially nothing has exercised
the temporal-deadline/cooldown/staleness half of the cognition model in a real run to date.

## Scope
Fix `TemporalModel.to_canonical_dict()` to serialize `deadlines`/`cooldowns`/`stale_facts` entries
as plain dicts of their own real fields, matching this file's own established curated-field pattern
elsewhere (e.g. `PerceptionModel.to_canonical_dict()`'s `{"salience": round(v.salience, 4)}` shape).

## Out of Scope
- `delay_risks` (a 5th `TemporalModel` field) is also omitted entirely from `to_canonical_dict()`'s
  output — a separate, pre-existing gap, not touched here (not required to unblock the scenario
  this fix was found for; flagged here for visibility, not filed as its own ticket since it isn't
  yet blocking anything real).
- Any change to `temporal_pressure`'s own registry state/verdict — handled in
  `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` itself.

## Acceptance Criteria
1. `TemporalModel.to_canonical_dict()` produces a JSON-serializable dict when `deadlines`/
   `cooldowns`/`stale_facts` are populated with real entries.
2. `Kernel.shutdown()`'s canonical hash computation succeeds against a state carrying real entries
   in all three fields, confirmed by a real scenario test doing exactly that.
3. No existing test asserted the old (broken) output shape — confirmed before changing it.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — where this was found,
  batch 2 wave 1 (`temporal_pressure`)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required per this repo's own tier routing rule.

## Related Code Areas
- `src/core/cognition.py::TemporalModel.to_canonical_dict()`
- `src/engine/checkpoint.py::CanonicalStateHasher` (the consumer that would have crashed)
- `tests/mechanic_scenarios/test_temporal_pressure_gated_dormancy.py` (the real scenario that hit
  this and now exercises the fix as a side effect of its own staging)

## Assumptions / Open Questions
None.

## Implementation Notes
Changed `deadlines`/`cooldowns`/`stale_facts` construction in `to_canonical_dict()` from
`dict(sorted(self.X.items()))` (raw dataclass values) to a dict comprehension extracting each
entry's own real fields (`target_id`/`expiry_tick` for `DeadlineEntry`, `target_id`/`ready_tick` for
`CooldownEntry`, `fact_id`/`last_verified_tick` for `StalenessEntry`) — the same curated,
explicit-field style already used by every other `to_canonical_dict()` in this file for a
`Mapping[str, <dataclass>]` field, not a generic `dataclasses.asdict()` walk.

Checked directly before changing: no existing test in `tests/` asserted the old (broken) output
shape for these three fields — searched all files referencing `to_canonical_dict`/`TemporalModel`,
none exercise a populated `deadlines`/`cooldowns`/`stale_facts` map, consistent with this being
genuinely never-hit code before this pass.

## Test Summary
Exercised as a side effect of `tests/mechanic_scenarios/test_temporal_pressure_gated_dormancy.py`
(3 tests, all passing — a real `Kernel.tick_once()` + `shutdown()` cycle against a state with a
real populated `deadlines` entry, which would have crashed before this fix). Full regression:
`tests/unit/core/ tests/unit/entity/ tests/unit/domains/time/ tests/integration/domains/memory/
tests/mechanic_scenarios/` (323 tests) and `tests/unit/tools/` (276 tests, registry/generator
suite) — all passing.

## Files Changed
- `src/core/cognition.py`

## Completion Summary
DONE. Fixed a real, previously-unhit determinism-hashing gap: `TemporalModel.to_canonical_dict()`
now correctly serializes `deadlines`/`cooldowns`/`stale_facts` entries. No behavior change to any
mechanism — purely a serialization-path fix, landed as its own hotfix-tier ticket per explicit
instruction, separate from the verification-program PR it was found inside, so it's independently
findable by a future determinism investigation. The fact that this was never hit before is itself
recorded as corroborating evidence for `temporal_pressure`'s own dormancy finding.
