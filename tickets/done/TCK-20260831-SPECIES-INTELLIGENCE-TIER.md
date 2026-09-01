---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-SPECIES-INTELLIGENCE-TIER
phase: open
date: 2026-08-31
tags: [content]
---

# TCK-20260831-SPECIES-INTELLIGENCE-TIER

## Title
Add intelligence_tier to RaceDefinition (species classification layer)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add an intelligence_tier field to RaceDefinition, anchored via natural_traits containing tool_user (not attribute_tendencies.intelligence, a false friend), so the 13-race roster gets an explicit high/low classification. This is the foundation idea 27's imitation-sophistication scaling later depends on.

## Scope
- Add intelligence_tier: enum(high|low) to RaceDefinition (src/content/schema.py:134-143), pydantic-validated.
- Author explicit intelligence_tier values for all 13 races in data/content/living/races.yaml, using the tool_user-in-natural_traits anchor confirmed correct for 6/13 (human, goblin, orc, elf, dwarf, lizardfolk).
- Explicitly review and justify the dragonkin and spirit edge cases (both have high/medium_high attribute_tendencies.intelligence and cognition_profile=arcane_scholar, same profile as elf, but lack tool_user in natural_traits) rather than mechanically applying the anchor rule.
- Add a regression test asserting each of the 13 races' intelligence_tier matches the documented anchor rule with justified exceptions.
- Decide and document whether this ticket requires at least a stub consumer/predicate given zero real consumers exist today, or leaves wiring fully out of scope.

## Out of Scope
- settlement_capacity — this is idea 44's field, NOT part of M2's scoped idea list (M2 covers ideas 2,4,5,6,8,11,14,23,27,28,30,35,36,37,43,48); the epic's own text incorrectly said this ticket needs it, but that conflict is resolved by exclusion.
- Wiring intelligence_tier into coming-of-age (idea 34, itself unbuilt and gated on idea 32) or into a Progression Planner eligibility gate (none currently exists).

## Acceptance Criteria
- [x] RaceDefinition gains intelligence_tier: enum(high|low), pydantic-validated.
- [x] All 13 races get an explicit authored intelligence_tier derived from the tool_user-in-natural_traits anchor, with dragonkin/spirit exceptions explicitly reviewed and justified in the ticket, not silently mechanized.
- [x] A regression test asserts each of the 13 races' intelligence_tier matches the documented anchor rule with justified exceptions.
- [x] settlement_capacity (idea 44) is explicitly OUT of scope for this ticket.

## Related Tickets
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Related Docs
- docs/mechanics/content_usage_matrix.md
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/content/schema.py
- src/content/repository.py
- data/content/living/races.yaml

## Assumptions / Open Questions
- dragonkin and spirit are genuine mechanical edge cases against the tool_user anchor rule and require an explicit design review, not silent mechanization.
- settlement_capacity epic-doc-vs-atlas-schema-doc conflict is resolved by excluding it from this ticket.
- intelligence_tier will land with zero real production consumers today — the ticket must decide whether a stub predicate is required.
- layer assigned as `world` (species/race content data lives under data/content/living/ and src/content/, closest registered fit to worldbuilding content; no dedicated `content` layer exists in registries/layer_registry.jsonl).

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/plan.md`'s 4
renumbered steps, no deviations.

**Step 1 — schema field (`src/content/schema.py:134-151`):** Added `intelligence_tier: str =
Field(...)` (required, no default) to `RaceDefinition`, placed after `drive_profile` and before
`natural_traits`, plus `@field_validator("intelligence_tier")` validating against
`{"high", "low"}` — copied exactly from the `FactionDefinition.legacy_engine_bucket` /
`RoleDefinition.legacy_engine_role` precedent shape (`str` + validator, no `Enum`/`Literal`), with
no `.upper()` normalization since the AC's enum values are lowercase and there is no
legacy-engine-name case precedent forcing uppercase here.

**Step 2 — fixture patch (`tests/unit/content/test_layered_catalog.py`):** Added
`"intelligence_tier": "low"` to `test_layered_catalog_validation_errors`'s `"broken_race"` fixture
dict (after `"cognition_profile": "missing_cognition",`) and `"intelligence_tier": "high"` to
`test_phase23_reference_graph_and_dead_active_data`'s `"human"` fixture dict (after
`"cognition_profile": "practical_human",`). This was required because Step 1's new field is
required-no-default, and `CatalogRepository.load_all()` silently drops any record that fails
pydantic construction (`try/except Exception: continue`, `src/content/repository.py:318-327`) —
without this patch both fixtures would be silently excluded from `repo.races`, regressing this
file from 3 passed to 2 failed / 1 passed (confirmed empirically, matching both architecture-review
verification runs — see plan.md's Step 2 Background).

**Step 3 — races.yaml authoring (`data/content/living/races.yaml`):** Added one
`intelligence_tier` key to each of the 13 race records, placed immediately after
`cognition_profile` and before `drive_profile` on every record, per the plan's table. No other key
on any record was touched (verified by re-reading the full file after all edits — `natural_traits`
and `compatible_roles` list contents/ordering are unchanged on every race).

**Dragonkin/spirit classification decision (AC #2 — explicitly reviewed, not silently
mechanized):** Both `dragonkin` and `spirit` are classified `"high"`, diverging from the raw
`tool_user`-in-`natural_traits` anchor rule that correctly classifies the other 11 races. Evidence
reviewed:
- Both races use `cognition_profile: "arcane_scholar"` (`races.yaml:112`/`251`,
  `cognition_profiles.yaml:63-72`) — the single most cognitively capable profile in the entire
  catalog (`tool_reasoning: "high"` is unique to it; every other non-`instinctive_animal`/
  `undead_fixated` profile tops out at `tool_reasoning: "medium"`). The only other race using
  `arcane_scholar` is `elf`, one of the 6 confirmed-clean `tool_user` "high" races.
- Neither race has `tool_user` in `natural_traits` (dragonkin: `races.yaml:214`, spirit:
  `races.yaml:253`), and their body models (`winged_reptilian`, `spirit_body`) both carry
  `equipment_slots: ["trinket"]` only — no `"tool"` slot, unlike every real `tool_user` race's body
  model. This is the counter-signal that makes these two genuine edge cases against the anchor.
- `compatible_roles` (both carry agency/leadership roles: dragonkin
  `["dragon_champion", "mage", "leader"]`, spirit `["guardian", "healer", "leader"]`) was checked
  and downweighted as a discriminator — `troll` and `undead`, both unambiguous clean-`"low"` races,
  also carry `"leader"`, proving a leadership role does not by itself imply high tier in this
  dataset.
- Spirit's `attribute_tendencies` (`races.yaml:255-258`) omits every physical attribute
  (`strength`/`agility`/`endurance`/`instinct`/`charisma`), confirming spirit has no physical body
  at all (`spirit_body`'s `movement_modes: ["float"]`) — its missing `tool_user`/tool-slot is a
  fact about having no hands to lack a tool with, not about cognitive capacity.
- **Why cognition wins for these two races specifically:** the field's own stated downstream
  purpose (idea 27 / `TCK-20260831-ROLE-MODEL-IMITATION`) is to modulate imitation-sophistication
  *scaling* — a cognitive-capacity gate, not a physical-dexterity/item-equip gate. The `tool_user`
  anchor is an excellent *observable proxy* for cognitive sophistication for 11/13 races, where
  trait presence and cognitive-profile sophistication co-occur perfectly. For dragonkin and spirit
  the proxy and the underlying signal it stands in for diverge: both lack the literal trait but are
  authored with the catalog's single most cognitively sophisticated profile — a more direct signal
  of what `intelligence_tier` is meant to capture than the absence of a body-model equipment slot,
  which governs a separate axis (combat/inventory item-equip compatibility), not reasoning
  capacity. Given the conflict is specific to these two races and the field's purpose maps onto the
  cognition axis, both resolve to `"high"`. They arrive at the same answer for asymmetric reasons:
  dragonkin has a physical body that structurally lacks tool manipulation; spirit has no physical
  body at all. Neither asymmetry changes the cognition-axis conclusion.

**Step 4 — regression tests (`tests/unit/content/test_catalog.py`):** Added
`RaceDefinition` to the module's existing schema import line, then added 3 tests co-located with
the `hazard_immunities` precedent tests:
1. `test_race_definition_intelligence_tier_field_round_trips` — constructs `RaceDefinition`
   directly for `"high"` and `"low"`, asserts both round-trip; asserts omitting the field raises
   `pydantic.ValidationError` (required, no default); asserts an out-of-set value (`"medium"`)
   raises `ValidationError` via the field validator.
2. `test_all_13_races_have_documented_intelligence_tier` — loads the real catalog, asserts
   `set(EXPECTED_INTELLIGENCE_TIER) == set(repo.races.keys())` (module-level dict hardcoding the
   plan's 13-race table) and each race's authored value matches; additionally asserts the
   executable anchor-rule invariant `("tool_user" in race.natural_traits) == (race.intelligence_tier
   == "high")` for the 11 unambiguous races (dragonkin/spirit excluded as the documented
   exceptions).
3. `test_race_catalog_loads_with_intelligence_tier_authored` — asserts the real catalog loads
   without raising and `len(repo.races) == 13`, catching an authoring typo as a load failure.

**Stub consumer:** none added, per the plan's explicit decision — this ticket ships an unconsumed,
fully-typed field only (mirrors the `TCK-20260831-CLAN-STATE-SCHEMA` precedent).

**Docs / parity ledger (updated after this Implement step; see Files Changed):** the plan's own
semantic-search conclusion of "no docs/parity change needed" held for content-behavior purposes,
but two later phases each found a real, narrower gap the plan didn't anticipate: Document-Update
found and fixed a stale, contradicted claim in the M2 epic plan doc (conflating this field with
idea 44's unrelated `settlement_capacity`); Parity's deterministic `cross_reference_touched` gate
found `src/content/schema.py` is a pre-existing candidate shard the plan's content-similarity
search didn't surface, and added a new `INFRA-400` entry to close it. Neither changes this
ticket's scope or the field's zero-consumer status — both are documentation/traceability
corrections layered on after Implement.

## Test Summary

- `tests/unit/content/test_layered_catalog.py -v` — **3 passed** (all 3 tests, including the two
  the architecture reviewer confirmed regress without Step 2:
  `test_layered_catalog_validation_errors` and `test_phase23_reference_graph_and_dead_active_data`).
  Matches both prior architecture-review empirical verification runs.
- `tests/unit/content/test_catalog.py -v` — **15 passed** (12 pre-existing + 3 new:
  `test_race_definition_intelligence_tier_field_round_trips`,
  `test_all_13_races_have_documented_intelligence_tier`,
  `test_race_catalog_loads_with_intelligence_tier_authored`).
- `tests/unit/content/` full sweep — **244 passed**, 0 failed.
- `tests/unit/content/test_resolvers.py` — **102 passed** (spot-checked separately since it reads
  race data indirectly via `LivingDefaultsResolver`; no direct `RaceDefinition` construction found
  in this file, confirmed via grep, so no fixture patch was needed there).
- Grep sweep confirmed no other construction site builds a `RaceDefinition` or a
  `races.yaml`-shaped fixture dict anywhere in `src/` or `tests/` beyond the two patched in Step 2
  and the new ones added in Step 4 — Step 2's fixture patch scope is complete.

## Files Changed

- `src/content/schema.py` — added `intelligence_tier` field + `@field_validator` to
  `RaceDefinition`.
- `data/content/living/races.yaml` — authored `intelligence_tier` on all 13 race records.
- `tests/unit/content/test_layered_catalog.py` — patched `"broken_race"` and `"human"` synthetic
  fixtures with `intelligence_tier`.
- `tests/unit/content/test_catalog.py` — added `RaceDefinition` import + 3 new regression tests.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-400` entry (Parity phase, after Implement):
  `src/content/schema.py` turned out to already be a pre-existing candidate shard (cited by
  `INFRA-184`/`SOC-257`/`STRAT-164`) that the plan's semantic search over existing entry *content*
  missed, since none of those entries described `intelligence_tier` specifically — the
  `cross_reference_touched` gate correctly caught this as a real gap (FAIL before the fix, PASS
  after) even though no existing entry needed content changes. `INFRA-400` documents the new field
  (`status: verified`, `v2_evidence` citing `schema.py`/`races.yaml`, `test_path` pointing at
  `test_all_13_races_have_documented_intelligence_tier`).
- `docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md` — corrected (Document-Update
  phase, after Implement) a stale bullet that conflated this ticket's `intelligence_tier` field
  with idea 44's unrelated `settlement_capacity` field and implied the latter shipped here; now
  records `intelligence_tier` as implemented (11/13-clean-anchor + dragonkin/spirit summary,
  pointing at this ticket's Implementation Notes for the full reasoning) and states
  `settlement_capacity` remains explicitly out of scope and unstarted.
- `tickets/inprogress/TCK-20260831-SPECIES-INTELLIGENCE-TIER.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, AC checkboxes, Status).
- `staging_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/investigation.md` — created during
  this run's Investigate phase (untracked/new; not authored by the implementer step).
- `staging_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/plan.md` — created during this run's
  Plan phase (untracked/new; not authored by the implementer step) — the approved spec this
  implementation followed exactly.
- `staging_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/test_plan.md` — created during this
  run's Plan phase (untracked/new; not authored by the implementer step).

## Completion Summary

Added a required, `str`-typed, validator-enforced `intelligence_tier` field (`"high"`/`"low"`) to
`RaceDefinition`, authored an explicit value for all 13 races in `data/content/living/races.yaml`
per the `tool_user`-in-`natural_traits` anchor rule (clean for 11/13), and resolved the two
edge-case races (dragonkin, spirit) as `"high"` based on their shared `arcane_scholar`
cognition profile outweighing their missing `tool_user` trait — full reasoning above and in
`staging_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/plan.md`. Patched two pre-existing
synthetic test fixtures that would otherwise have been silently dropped by the catalog loader's
fail-soft record handling, and added 3 new regression tests. No consumer changes were needed —
this ships as inert, fully-typed, catalog-validated scaffolding, mirroring the `CLAN-STATE-SCHEMA`
precedent. A `docs/parity_ledger/infrastructure.yaml` entry (`INFRA-400`) and a correction to the
M2 epic plan doc were added post-Implement (see Files Changed) to close a real cross-reference gap
and a real stale-claim gap respectively — neither changes the field's scope or zero-consumer
status. All acceptance criteria are satisfied.
