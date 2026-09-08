---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE
phase: done
date: 2026-09-07
tags: [determinism, engine, architecture]
---

# TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE

## Title
6 CampaignState-bridge fields added by the Dormant Mechanism Closure epic are absent from the canonical determinism state hash

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
An independent review of PR #144 (Dormant Mechanism Closure epic, `rpg-feature-planning` session)
raised a determinism-coverage question about `information_source_profiles`'s new persistence
semantics (`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`), citing a precedent
of a prior real bug class (an unsorted-set serialization bug the reviewer recalled from PR #128 —
not independently re-verified by this ticket, cited as the reviewer's own stated precedent, not a
confirmed fact of this repo's history).

The orchestrating session independently traced `CanonicalStateHasher.to_canonical_data()`
(`src/engine/checkpoint.py`) — the real function behind `final_state_hash`, the deterministic
proof used for replay/certification — and confirmed the underlying concern is real, and broader
than just the one field the reviewer flagged: **none** of the 6 `AuthoritativeState` fields the
Dormant Mechanism Closure epic added participate in the canonical hash at all:
- `region_loyalty_pressure` (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`)
- `region_culture_states`, `entity_legend_facts` (`TCK-20260907-ROUTE-BIAS-SCORING-
  INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`)
- `information_source_profiles` (`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`,
  now persistent rather than Bounded/single-fire)
- `entity_belief_institutions`, `event_fidelity` (`TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`)

`CanonicalStateHasher.to_canonical_data()` enumerates included fields explicitly (scalars,
entities, regions, places, local_scars, resource_nodes, buildings, corpses, ground_items, chests,
groups, home_storage, camps, global_resources, periodic_due_ticks, work_debt, blocked_tiles,
town_tiles, building_tiles, rng_checkpoint) — none of the 6 fields above are in that list.

## Scope
- Confirm during Investigate whether this is a real determinism gap in practice (i.e., could two
  replay runs diverge in one of these 6 fields' content while producing an identical state hash?)
  or whether downstream mutation (these fields feed into `personality_bias`, which affects
  entity-level decisions that ARE hashed) makes any real divergence still detectable indirectly —
  do not assume either answer, verify with a real test.
- If a real gap exists: add the 6 fields to `CanonicalStateHasher.to_canonical_data()`, following
  the same sorted/deterministic-iteration discipline the existing fields already use (see
  `regions`/`places`/etc.'s own `sorted(...)` calls).
- Confirm no performance regression from the addition — `CanonicalStateHasher.get_hash()` is
  budget-rate-limited (`BudgetedCanonicalHasher`) for a reason; these fields are typically small
  (bounded by entity/region count), but verify against a real large-world calibration run.

## Out of Scope
- Redesigning the state-hash mechanism itself.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [x] A real determination is made (with test evidence) of whether missing these 6 fields is a
      genuine determinism-verification gap or a benign omission, and the reasoning is recorded.
      **Determination: genuine gap.** See Implementation Notes.
- [x] If genuine: all 6 fields are added to the canonical hash, with a real test proving two
      differently-seeded-but-otherwise-identical states (differing only in one of these fields)
      now produce different hashes, and identical states still produce identical hashes.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic — source of all 6 fields)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`,
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`, `TCK-20260907-INFORMATION-SOURCE-PROFILES-
  PERSISTENCE-DECISION`, `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (all `tickets/done/` —
  each added one or more of the 6 fields)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/engine/checkpoint.py` (`CanonicalStateHasher.to_canonical_data()`)
- `src/core/state.py` (`AuthoritativeState`)

## Assumptions / Open Questions
- Whether the omission is a real gap or benign (fields' effects are always indirectly captured
  elsewhere in the hash) is not resolved here — genuine investigation work for whoever picks this
  up.

## Implementation Notes

### Determination: genuine gap, not a benign omission (2026-09-08)

**Direct reproduction, before any fix.** Constructed two `AuthoritativeState`s identical in every
hashed field (`tick=0, seed=42, entities={}`) and differing ONLY in one bridge field at a time,
then compared `CanonicalStateHasher.get_hash()`:

| Field varied | Hashes equal (pre-fix) |
|---|---|
| `region_loyalty_pressure` | **True** (gap) |
| `information_source_profiles` | **True** (gap) |
| `event_fidelity` | **True** (gap) |

All three collapsed to byte-identical hashes — the hash literally cannot distinguish these states.
The remaining 3 fields (`region_culture_states`, `entity_legend_facts`,
`entity_belief_institutions`) are absent from `to_canonical_data()` by the same omission, so they
behave identically.

**Why the "downstream mutation catches it anyway" argument does not hold.** The counter-argument
worth taking seriously is that these 6 fields feed `AdventureRouteScorer.score()`'s
`personality_bias`, which affects entity decisions, and entity state *is* hashed — so any real
divergence would surface indirectly. That argument fails on a real mechanism, not a hypothetical:
`personality_bias` is an **additive** contribution among several inputs into a route-family argmax.
A divergence in one of these fields changes the bias term, but is not guaranteed to flip the
selected `RouteFamily` on the tick it diverges — a small delta can leave the same route selected
and therefore leave every hashed entity field byte-identical. Because these fields are *persisted*
(carried forward per tick by `ApplyPath.apply_generation()`), a divergence can sit latent in state
across a certification/replay checkpoint while `final_state_hash` reports "identical". That is
precisely a false negative for the use case the hash exists to serve. Fixed rather than accepted.

**Fix.** Added a section 5 to `CanonicalStateHasher.to_canonical_data()` covering all 6 fields with
the same sorted/deterministic-iteration discipline the pre-existing collections use:
- `region_loyalty_pressure`, `event_fidelity` — `dict(sorted(...))`, matching `global_resources`.
- `region_culture_states`, `entity_legend_facts` — sorted by key, values via their own `to_dict()`.
- `entity_belief_institutions` — `Dict[int, Tuple[BeliefInstitution, ...]]`; sorted by int key
  (stringified for JSON, matching the `entities` convention), and each per-entity tuple internally
  sorted by `(origin_event_id, clan_id)` so tuple ordering can't perturb the hash.
- `information_source_profiles` — a `List` with no natural key, so sorted by
  `(source_id, source_kind)` to make the hash insertion-order-independent. Serialized via
  `dataclasses.asdict()` (added `import dataclasses`): unlike `CultureState`/`LegendFact`/
  `BeliefInstitution`, `InformationSourceProfile` is a frozen `slots=True` dataclass with no
  `to_dict()` of its own and no `__dict__` to fall back on.

**Parity ledger**: new entry `INFRA-413` (`docs/parity_ledger/infrastructure.yaml`), written via
`tools/parity_ledger_writer.py::write_entry()` (the sanctioned, schema-validating path — not a hand
edit). Produced a clean additive +33-line diff; `tools/parity_index.py health` reports zero
findings against the new entry, entry_count 2182 → 2183.

## Test Summary
New: `tests/unit/engine/test_campaign_bridge_fields_state_hash_coverage.py` — 8 tests, all passing.
Covers: identical states still hash identically (no false-positive divergence); each of the 6
fields individually changes the hash when it differs; and `information_source_profiles`'
insertion-order independence (two semantically-identical lists in different order hash the same).

Regression: `pytest tests/unit/engine/ tests/unit/replay/ tests/unit/kernel/
tests/integration/kernel/ tests/unit/domains/progression/test_progression_decision_canonical_hash.py
-m "not slow"` → **362 passed, 1 skipped, 0 failed**.

Performance (ticket Scope explicitly required checking this, since `get_hash()` is budget-rate-limited
via `BudgetedCanonicalHasher`): real calibration run `tools/calibrate_simq.py --name urban_political
--seed 42 --ticks 200` completed in **7.99s**, `overall_grade=S`, pillar profile unchanged. The added
work is `sorted()` over collections bounded by entity/region count — negligible against the existing
per-entity serialization the hash already does.

## Files Changed
- `src/engine/checkpoint.py` (`import dataclasses`; new section 5 in `to_canonical_data()`)
- `tests/unit/engine/test_campaign_bridge_fields_state_hash_coverage.py` (new, 8 tests)
- `docs/parity_ledger/infrastructure.yaml` (new entry `INFRA-413`)

## Completion Summary
Investigated the open question this ticket was filed to answer and found it is a **real
determinism-verification gap**, not a benign omission — proven by direct reproduction (states
differing only in a bridge field hashed identically) plus a concrete mechanism argument for why the
indirect-observability counter-argument fails (`personality_bias` is additive and need not flip a
route-family argmax on the diverging tick, while the fields themselves persist across ticks). Fixed
by adding all 6 fields to `CanonicalStateHasher.to_canonical_data()` with the same deterministic
sort discipline the existing collections use, including insertion-order-independence for the one
unkeyed `List` field. 8 new tests, 362-test regression sweep clean, no performance regression on a
real calibration run, parity entry `INFRA-413` recorded via the sanctioned writer.
