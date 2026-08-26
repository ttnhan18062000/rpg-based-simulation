---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
phase: done
date: 2026-08-24
tags: [social]
---

# TCK-20260824-DEFAULT-HEIR-ASSIGNMENT

## Title
Assign Heirs Automatically from Existing Relationship Data

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`heir_entity_id`'s transfer mechanic is fully wired and confirmed live, but nothing ever assigns a heir. The author wants default heir assignment built using `RelationshipService`'s existing per-pair `SocialBond` data.

## Scope
- When an active entity dies (OLD_AGE/COMBAT) with `heir_entity_id==None` and at least one bond to a living entity, add a death-path step in `LifecycleSystem` that assigns a heir via `LifecycleUpdate.heir_entity_id_set` (never direct field mutation)
- Define and document a concrete, deterministic default-heir selection rule from `RelationshipService`'s `SocialBond` data (familiarity/sentiment/last_interaction_tick), with an explicit documented tie-break formula (no hash-order dependence)
- Ensure the heir's `resource_transfers` receives inventory/heirlooms in the same tick, matching the already-proven manual-heir-set behavior in `test_succession_and_heirloom_transfer`
- Preserve the existing None-guard: zero bonds or all bonded targets dead/missing results in no heir assigned, no exception
- Add a new Mechanics Bible subsection or `docs/guidelines/intentional_divergences.md` entry documenting the default-selection rule and exact tie-break formula
- Add a determinism/replay-parity regression test proving heir selection is deterministic given identical bond data

## Out of Scope
- Reviving the superseded V1 `HeroLifecycleSystem`/`SuccessorRegistry` design -- confirmed superseded, cited as prior intent only

## Acceptance Criteria
- [x] When an active entity dies with `heir_entity_id==None` and at least one bond to a living entity, a heir is assigned and `resource_transfers` occur in the same tick, matching the proven manual-heir test
- [x] When zero bonds or all bonded targets are dead/missing, no heir is assigned and no exception is raised
- [x] Heir selection is deterministic given identical bond data, with an explicit documented tie-break rule, covered by a new determinism/replay-parity regression test
- [x] The default-selection rule is documented in `docs/mechanics/` or `intentional_divergences.md` with the exact tie-break formula matching code

## Related Tickets
- TCK-20260409-PH4-STG2-SUCCESSION-LOGIC
- TCK-20260409-PH1-STG13-14
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Related Docs
- docs/engine/authoritative_mutation_pipeline_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/systems/lifecycle.py
- src/systems/social_systems/relationships.py
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- 'Strongest bond' and 'default heir' are undefined by the original concern -- `SocialBond` has no kinship field, only familiarity/sentiment/last_interaction_tick; the selection rule is a genuine open design question this ticket must answer
- Whether heir selection runs inline inside `LifecycleSystem.resolve_lifecycle`'s death branch or as a separate earlier phase (given `resolve_lifecycle` currently reads only baseline `heir_entity_id`, not pending `entity_updates` from earlier in the tick) is an open implementation decision
- `layer: systems` was chosen because the primary changed code (`src/systems/lifecycle_systems/`, `src/systems/social_systems/`) lives under the `systems` layer directory; no `social` layer is registered in `registries/layer_registry.jsonl`

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260824-DEFAULT-HEIR-ASSIGNMENT/plan.md`'s 6 steps exactly
(see plan.md's "Deviations" section: None).

- Added `LifecycleSystem._select_default_heir(state, deceased) -> Optional[int]` as a new
  `@staticmethod` on `LifecycleSystem` (`src/systems/lifecycle_systems/lifecycle.py`), scoring live
  bonded candidates (`state.entities.get(target_id)` exists AND `.lifecycle.active is True`) with
  `score = 0.6 * familiarity + 0.4 * ((sentiment + 1.0) / 2.0)`, tie-broken by
  `(-score, -last_interaction_tick, target_id)`.
- Rewired `resolve_lifecycle`'s succession block: a `heir_id` local variable now reads
  `entity.lifecycle.heir_entity_id`, falling back to `_select_default_heir` when `None`. A
  freshly-selected default heir is recorded durably via `LifecycleUpdate.heir_entity_id_set` on the
  dying entity's existing `EntityUpdate` (merged via `dataclasses.replace`, never a direct field
  mutation). The existing manual-heir `if heir:` liveness check (existence-only, not `.active`) is
  byte-identical for the manually-set-heir path — verified by
  `test_manual_heir_entity_id_transfers_even_if_heir_inactive` and the pre-existing
  `test_succession_and_heirloom_transfer`.
- Added 8 new tests to `tests/unit/progression/test_lifecycle.py` (the 7 listed in plan.md Step 3
  plus the anti-drift manual-heir-with-inactive-target regression test, confirmed missing from
  existing coverage before adding). The 6 pre-existing tests are unchanged.
- Ran the full regression surface from plan.md Step 4
  (`tests/unit/progression/test_lifecycle.py`, `tests/unit/social/test_social_bonds.py`,
  `test_relationships.py`, `test_party_composition.py`, and
  `tests/unit/progression/ tests/unit/social/ -m "not slow"`): all green — 14/14 in
  `test_lifecycle.py`, 258 passed / 1 deselected across the broader suite.
- Inserted `### Succession — Default Heir Assignment` into `docs/mechanics/05_world_evolution.md`
  between `Birth/Death Law` and `Migration Law`, verbatim per plan.md Step 5.
- Appended `SOC-245` (`P1`, `status: verified`) to `docs/parity_ledger/social_narrative.yaml`
  immediately after `SOC-244`, verbatim per plan.md Step 6; YAML parses (266 total entries).

## Test Summary
- `pytest tests/unit/progression/test_lifecycle.py -v` — 14 passed (6 pre-existing unchanged, 8 new).
- `pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_relationships.py tests/unit/social/test_party_composition.py -v` — 28 passed.
- `pytest tests/unit/progression/ tests/unit/social/ -v -m "not slow"` — 258 passed, 1 deselected.
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/social_narrative.yaml'))"` — parses cleanly, 266 entries, last id `SOC-245`.
- `python3 tools/validate_frontmatter.py` on the ticket and all three staging artifacts — all OK, no violations.

## Files Changed
- `src/systems/lifecycle_systems/lifecycle.py`
- `tests/unit/progression/test_lifecycle.py`
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/social_narrative.yaml`
- `staging_artifacts/TCK-20260824-DEFAULT-HEIR-ASSIGNMENT/plan.md` (Deviations section added: "None.")
- `tickets/inprogress/TCK-20260824-DEFAULT-HEIR-ASSIGNMENT.md` (this file)

## Completion Summary
Added deterministic default-heir selection to `LifecycleSystem.resolve_lifecycle`: when an active
entity dies with `heir_entity_id is None`, a new `_select_default_heir` staticmethod scores the
deceased's live `SocialBond` candidates (`0.6*familiarity + 0.4*normalized_sentiment`, tie-broken by
recency then entity id) and records the result via `LifecycleUpdate.heir_entity_id_set`, feeding the
same tick's existing heirloom-transfer logic. The pre-existing manual-heir-set path and its
existence-only liveness check are untouched. Documented in a new `docs/mechanics/05_world_evolution.md`
subsection and a new `P1` parity ledger entry `SOC-245`, with 8 new unit tests covering selection,
tie-breaking, no-candidate, determinism, and non-override-of-manual-heir behavior — all passing
alongside the full progression/social regression suite (258 passed, 1 deselected).
