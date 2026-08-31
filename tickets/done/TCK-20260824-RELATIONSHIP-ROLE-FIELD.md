---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-RELATIONSHIP-ROLE-FIELD
phase: done
date: 2026-08-24
tags: [social]
---

# TCK-20260824-RELATIONSHIP-ROLE-FIELD

## Title
Add Relationship Roles Alongside Relationship Scores, with a Real Consumer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
SocialBond has exactly three fields today; the author wants a role concept added as an additive field. A real risk (from the Merit Scorecard) is that a label with no consumer is invisible -- this codebase has a track record of adding fields nothing ever reads. The author wants the consumer scoped alongside the field, not as a follow-up.

## Scope
- Add an additive role field (enum, NEUTRAL/UNSET default) to SocialBond, named distinctly from the existing unrelated PartyRole enum (party_composition.py's TANK/HEALER/DPS/SUPPORT combat role) -- e.g. RelationshipRole/BondRole
- Extend SocialBondUpdate/RelationshipService.process_update() so role can only be set through the authoritative SocialUpdate path (per SOC-217)
- Wire one real consumer (PartyCompositionScorer or SocialAppraisalSystem.appraise_contract()) to produce a measurably different score for two otherwise-identical bonds differing only in role, with a new test asserting this using fixed familiarity/sentiment
- Add a new SOC-### parity_ledger entry and a docs/mechanics/04_strategic_cognition.md section documenting the formula -- not schema-only with docs deferred

## Out of Scope
- Wiring additional consumers beyond the one chosen for this ticket's AC (PartnerFitEvaluator and others noted as explicit out-of-scope follow-ons)
- Deepening PartnerFitEvaluator's existing pre-existing direct read of social.bonds -- not a new violation to fix here, and not license to add further coupling

## Acceptance Criteria
- [x] SocialBond gains an additive role field (enum, NEUTRAL/UNSET default); existing construction/serialization continues to work unmodified when omitted
- [x] SocialBondUpdate/RelationshipService.process_update() support setting role only through the authoritative path
- [x] A real consumer produces a measurably different score for two otherwise-identical bonds differing only in role, asserted by a new test with fixed familiarity/sentiment
- [x] docs/mechanics/04_strategic_cognition.md and social_narrative.yaml gain a new SOC-### entry documenting the formula

## Related Tickets
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/social_systems_contract.md
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/models/social.py
- src/core/updates.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/party_composition.py
- src/systems/social_systems/appraisal.py
- src/domains/cooperation/evaluators.py
- src/systems/world_systems/groups.py
- src/engine/tactical.py
- src/engine/combat.py
- src/core/state.py
- src/domains/adventure/generator.py

## Assumptions / Open Questions
- Which role values are wanted, and which single consumer to wire for initial AC, is a real design decision this ticket must make explicit
- The new field/enum name must avoid collision with the existing unrelated PartyRole enum, and must be reconciled against the existing but distinct nemesis_ids concept if a 'rival' role value is added

## Implementation Notes

Implemented Steps 1-5 of `staging_artifacts/TCK-20260824-RELATIONSHIP-ROLE-FIELD/plan.md` exactly
as specified. Step 6 (docs + parity ledger) was completed in the pipeline's later Document-Update
and Parity phases (this note originally said "deferred" before those phases ran; both have since
completed — see below).

- **Step 6 — Document-Update** (`docs/mechanics/04_strategic_cognition.md` §7.3,
  `docs/simulation/social_systems_contract.md`): added the Role-Affinity Adjustment subsection
  documenting the `RelationshipRole` enum, the `ROLE_AFFINITY_WEIGHT=0.10` formula, and the
  independence from `nemesis_ids`/`grudge_history`; updated the Social bonds and
  `PartyCompositionScorer` sections of the social systems contract to describe the new `role` field
  and scoring term. Doc-staleness gate: PASS (2 docs/ paths present for a behavior-changing diff).
- **Step 6 — Parity** (`docs/parity_ledger/social_narrative.yaml`): added `SOC-247`
  (`status: verified`, `priority: P1`, matching sibling `SOC-244`), citing `v2_evidence` for the
  `SocialBond.role` field, `SocialBondUpdate.role_set`, the `process_update()` set-if-provided
  clause, and `PartyCompositionScorer.score()`'s new term, with `test_path` pointing at
  `test_party_composition_score_reflects_candidate_role`. Ledger diff verified as a clean full-shard
  rewrite (267→268 entries, only `SOC-247` added, zero existing entries altered) and the
  cross-reference gate (`cross_reference_touched`) confirmed all 4 changed `src/` files map cleanly
  to the touched `social_narrative.yaml` shard.

- **Step 1** (`src/core/models/social.py`): added `RelationshipRole(str, Enum)` (`NEUTRAL`/`FRIEND`/
  `RIVAL`, `NEUTRAL` default) directly above `SocialBond`, and a trailing `role: RelationshipRole =
  RelationshipRole.NEUTRAL` field on `SocialBond`. Purely additive; all 28 existing keyword-only
  `SocialBond(...)` call sites unaffected.
- **Step 2** (`src/core/updates.py`): added `role_set: Optional[RelationshipRole] = None` as the
  trailing field on `SocialBondUpdate`, importing `RelationshipRole` directly from
  `src.core.models.social` (the defining module — `state.py`'s existing `SocialBond`/`SocialComponent`
  re-export was not a usable import path for a *new* symbol, since `state.py` doesn't yet re-export
  `RelationshipRole`; no other symbol in `updates.py` referenced `SocialBond`/`SocialComponent`
  directly for a precedent import path to mirror).
- **Step 3** (`src/systems/social_systems/relationships.py`): added
  `role=b_upd.role_set if b_upd.role_set is not None else bond.role` to the existing `replace(bond,
  ...)` call in `process_update()`, mirroring `last_interaction_tick_set`'s set-if-provided semantics
  exactly. No read/lookup method added to `RelationshipService`.
- **Step 4** (nemesis-independence guard test): added to
  `tests/unit/social/test_social_memory_service.py` instead of the two files plan.md named as
  candidates (`test_social_memory.py`/`test_groups.py`) — neither actually contains a
  `nemesis_ids`/`grudge_history`-threshold test; `test_social_memory_service.py` (not surveyed by
  plan.md/investigation.md) is the real, closest-matching file, already covering
  `SocialMemoryService.check_nemesis_promotion()`'s `grudge_history >= 3.0` threshold directly. See
  Deviations in plan.md.
- **Step 5** (`src/systems/social_systems/party_composition.py`): added `ROLE_AFFINITY_WEIGHT: float =
  0.10` class constant, `_candidate_role_value()`/`score_role_affinity()` static methods mirroring
  `_candidate_trust_value()`/`score_trust_bonds()`'s shape exactly, and a third additive term in
  `score()`: `base_score + TRUST_BONUS_WEIGHT * trust_term + ROLE_AFFINITY_WEIGHT * role_term`,
  clamped `[0.0, 1.0]`. Also updated the module docstring's "Score combines" list and Logic ID header
  (added `SOC-247`) for internal consistency — this is a source-file docstring edit within Step 5's
  own file, not a `docs/`-directory change, so it is not part of the deferred Step 6.
  `TRUST_BONUS_WEIGHT`/`ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT` untouched.

All scope guards honored: no touch to `PartyRole`/`EntityRole`/`IdentityUpdate.role_set`/
`GroupRecord.roles`, no read/lookup method added to `RelationshipService`, no direct
`dataclasses.replace(bond, role=...)` outside `process_update()`, no touch to
`nemesis_ids`/`grudge_history`/nemesis-promotion logic, no touch to `generator.py`'s FORM_PARTY
confidence formula or `scoring.py`/STRAT-227, no deepening of `PartnerFitEvaluator`'s existing
`social.bonds` read.

## Test Summary

7 new tests, all passing:
- `tests/unit/social/test_social_bonds.py::test_social_bond_role_defaults_to_neutral`
- `tests/unit/social/test_social_bonds.py::test_social_bond_role_canonical_dict_serializes_as_plain_string`
- `tests/unit/social/test_relationships.py::test_social_bond_role_set_via_authoritative_update_only`
- `tests/unit/social/test_relationships.py::test_process_update_role_set_none_preserves_existing_role`
- `tests/unit/social/test_party_composition.py::test_party_composition_score_reflects_candidate_role`
- `tests/unit/social/test_party_composition.py::test_party_composition_score_role_term_is_zero_for_all_neutral_pool`
- `tests/unit/social/test_party_composition.py::test_party_composition_score_role_term_requires_actor`
- `tests/unit/social/test_social_memory_service.py::test_check_nemesis_promotion_rival_role_below_grudge_threshold_not_promoted`
  (Step 4's nemesis-independence guard test)

Regression run (all passing, no changes needed), via the pipeline's formal Test phase
(`test-scoper` agent dispatch): initial scoped run —
`tests/unit/social/ tests/unit/ai/goals/test_social_contract_goal_scorer.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/progression/test_lifecycle.py tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -m "not slow"`
— 251 passed. The structural test-scope-coverage backstop (`tools/gate_checks/test_scope_coverage_static.py`)
then flagged a real gap: `src/core/models/social.py` changed but `tests/unit/core/` was not in the
scoped command. Test phase was re-scoped to a strict superset adding `tests/unit/core/`; final run —
**476 passed, 0 failed** (1 deselected as `slow`). Coverage-gap check re-verified: PASS. Run via
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest` (bare `python3` lacks
`pydantic` in this sandbox).

## Files Changed

- `src/core/models/social.py` — added `RelationshipRole` enum + `SocialBond.role` field (Step 1)
- `src/core/updates.py` — added `SocialBondUpdate.role_set` field + import (Step 2)
- `src/systems/social_systems/relationships.py` — apply `role_set` in `process_update()` (Step 3)
- `src/systems/social_systems/party_composition.py` — `ROLE_AFFINITY_WEIGHT` term + docstring (Step 5)
- `tests/unit/social/test_social_bonds.py` — 2 new tests (Step 1 verification)
- `tests/unit/social/test_relationships.py` — 2 new tests (Step 3 verification)
- `tests/unit/social/test_party_composition.py` — 3 new tests (Step 5 verification)
- `tests/unit/social/test_social_memory_service.py` — 1 new test (Step 4, nemesis-independence guard)
- `docs/mechanics/04_strategic_cognition.md` — added §7.3 Role-Affinity Adjustment subsection
  documenting the `RelationshipRole` enum and the `ROLE_AFFINITY_WEIGHT=0.10` formula (Step 6)
- `docs/simulation/social_systems_contract.md` — updated Social bonds and `PartyCompositionScorer`
  sections to describe the new `role` field and scoring term (Step 6)
- `docs/parity_ledger/social_narrative.yaml` — added `SOC-247` entry (`status: verified`,
  `priority: P1`) citing v2_evidence and `test_path` for the role field/scoring term (Step 6)
- `staging_artifacts/TCK-20260824-RELATIONSHIP-ROLE-FIELD/plan.md` — added Deviations section
- `tickets/inprogress/TCK-20260824-RELATIONSHIP-ROLE-FIELD.md` — this file (status, AC checkboxes,
  Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary

All 6 steps of the approved plan are implemented. `SocialBond` gained an additive `role`
(`RelationshipRole`: `NEUTRAL`/`FRIEND`/`RIVAL`, `NEUTRAL` default) field, settable only through the
authoritative `SocialBondUpdate.role_set` -> `RelationshipService.process_update()` path, and
`PartyCompositionScorer.score()` gained a new `ROLE_AFFINITY_WEIGHT = 0.10` additive term so a
`FRIEND`/`RIVAL`-tagged bond produces a strictly ordered, measurably different score
(`FRIEND` > `NEUTRAL` > `RIVAL`) for otherwise-identical candidate pools. A dedicated test proves
`RelationshipRole.RIVAL` stays independent of `nemesis_ids`/`grudge_history`-driven nemesis
promotion. Documentation and parity are in place: `docs/mechanics/04_strategic_cognition.md` §7.3
documents the Role-Affinity Adjustment formula, `docs/simulation/social_systems_contract.md` reflects
the new field and scoring term, and `docs/parity_ledger/social_narrative.yaml` gained `SOC-247`
(`status: verified`) citing the source evidence and test path. All 7 specified new tests plus the
nemesis-independence guard test pass (8 new tests total), and the full scoped regression run —
`tests/unit/social/`, `tests/unit/core/`, adjacent AI-goals/strategic/progression suites, and the
phase7 social-cooperation integration scenarios — passes at 476 passed, 0 failed (1 deselected as
`slow`), with the structural test-scope-coverage backstop re-verified as PASS after the `tests/unit/core/`
gap it originally flagged was closed.
