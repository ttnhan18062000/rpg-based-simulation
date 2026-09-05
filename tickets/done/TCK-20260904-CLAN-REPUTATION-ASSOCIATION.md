---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
phase: done
date: 2026-09-04
tags: [social]
---

# TCK-20260904-CLAN-REPUTATION-ASSOCIATION

## Title
Idea 54 — Guilt by Association (ClanState.clan_reputation)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 54 (Guilt by Association) is gated on M2's idea 36 (Clan) existing as real state — confirmed satisfied: TCK-20260831-CLAN-STATE-SCHEMA is DONE and fully wired into the authoritative pipeline via TCK-20260903-CLAN-LIFECYCLE-SUCCESSION (also DONE). Investigation (2026-09-04) found the concern's own framing (inherited from the epic doc's paraphrase — "one member's act propagating to clan-mates") does not match the real idea-54 schema card: the actual proposal is a NEW ClanState.clan_reputation: float field, tracked independently the same way an individual's own public_reputation is, read by strangers judging an unfamiliar member — not a mechanism that mutates every clan-mate's own SocialComponent.public_reputation. This ticket must scope from the real schema card, not the epic doc's inaccurate paraphrase. Confirmed: ClanState (src/core/state.py:751-766) has member_entity_ids: Tuple[int,...] but no entity_id -> clan_id reverse lookup exists anywhere — any trigger logic needs either an O(n_clans) scan or a new index, a real open scoping question. This ticket depends on TCK-20260904-REPUTATION-LOCALITY-SCOPE (idea 60) landing first, per the epic's own sequencing constraint, though idea 60 and idea 54 write to structurally distinct fields (SocialComponent.public_reputation vs. the new ClanState.clan_reputation) — this ticket's Plan phase must independently re-confirm whether that dependency is load-bearing or just a hedge, since the two fields may not actually interact.

## Scope
- Add a new ClanState.clan_reputation: float field (src/core/state.py) — the clan's own aggregate score, tracked independently from any individual member's SocialComponent.public_reputation, following the Durable State Rule (typed model, stable AuthoritativeState location, defined lifecycle, tests) already satisfied by TCK-20260903-CLAN-LIFECYCLE-SUCCESSION's wiring for the rest of ClanState.
- Wire real, already-detected reputation-affecting events to also produce a ClanUpdate adjusting the acting entity's clan's clan_reputation: contract betrayal (src/systems/social_systems/contracts.py, notoriety_delta=0.5/betrayal_increment=1) and party defection (src/systems/social_systems/party_lifecycle.py:196, notoriety_delta=2.0). Apply only through apply.py's existing clan_updates path — never a direct ClanState mutation. Do NOT wire through ReputationUpdateService/QuestResolutionSystem — that touches the wrong (unrelated) field.
- Resolve the entity_id -> clan_id lookup gap: either add a real reverse index or explicitly accept an O(n_clans) scan over state.clans.values() — a Plan-phase decision, not resolved by investigation.
- Extend the stranger-judgment read path (SocialAppraisalSystem or equivalent, src/systems/social_systems/appraisal.py) so an observer with no direct personal trust/familiarity history toward a given clan member blends that member's clan's clan_reputation into their caution/trust prior, distinguishably different from how the same observer judges a member they do have direct history with.
- Any propagation/aggregation logic touching ClanState.member_entity_ids must iterate in a fixed sorted order (never raw tuple iteration) for determinism.

## Out of Scope
- Per-member reputation propagation to clan-mates' own SocialComponent.public_reputation — the epic doc's original framing was inaccurate; this ticket does not mutate individual members' own reputation fields.
- Wiring through ReputationUpdateService, PublicReputationProfile, or QuestResolutionSystem's quest-completion path — a structurally separate, unrelated field/system.
- Idea 60's public_reputation locality-scoping change or idea 53's birth-seed write — sibling/prerequisite child tickets of the same epic.

## Acceptance Criteria
- ClanState gains a clan_reputation: float field with to_canonical_dict()/from_dict() round-trip test coverage, mirroring the existing test_clan_state_serialization_round_trip pattern.
- A contract-betrayal or party-defection event that produces a SocialUpdate reputation delta on the acting entity also produces a measurable ClanUpdate change to clans[clan_id].clan_reputation, applied only through apply.py's clan_updates path, verified by a new test.
- A stranger entity with no personal trust/familiarity history toward a given clan member reads a caution/trust prior that incorporates that member's clan's clan_reputation, distinguishably different from how the same stranger judges a member they do have direct history with, verified by a new test.
- Any propagation/aggregation over member_entity_ids produces bit-identical ClanUpdate output across repeated runs, verified by a determinism test.
- This ticket introduces zero writes to any individual member's own SocialComponent.public_reputation — verified by a source-text guard test, confirming the scope correction (clan-level field, not member-propagation) actually held.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260904-REPUTATION-LOCALITY-SCOPE
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/rpg_feature_atlas.html
- docs/guidelines/intentional_divergences.md
- docs/mechanics/04_strategic_cognition.md
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Related Stored Artifacts
None

## Related Code Areas
- src/core/state.py
- src/core/models/social.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/contracts.py
- src/systems/social_systems/party_lifecycle.py
- src/systems/social_systems/clan_lifecycle.py
- src/systems/social_systems/appraisal.py

## Assumptions / Open Questions
- reputation_weight_on_stranger_judgment (the schema card's second proposed field) has no proposed formula/anchor in the source card — an open design question for Plan phase.
- Whether to add a real entity->clan reverse index or accept an O(n_clans) scan is undecided — Plan-phase decision.
- ClanState is not currently referenced in replay/fingerprint.py, so clan_reputation likely doesn't need canonical-hash coverage — this must be explicitly re-confirmed during Investigate/Plan, not assumed.
- Whether this ticket's dependency on idea 60 landing first is load-bearing (the two fields are structurally distinct) should be independently re-confirmed by this ticket's own Plan phase rather than inherited unquestioned from the epic doc's blanket sequencing note.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260904-CLAN-REPUTATION-ASSOCIATION/plan.md`
(Steps 1-9, recommended order 1 -> 6 -> 3 -> 2 -> 4 -> 5 -> 7 -> 8 -> 9), no deviations:

- **Step 1** — Added `ClanState.clan_reputation: float = 1.0` (`src/core/state.py`), wired into
  `to_canonical_dict()`/`from_dict()` alongside `tension_level`.
- **Step 2** — Extended `test_clan_state_no_new_idea68_fields` (`tests/unit/domains/faction/
  test_clan_state.py`) with `clan_reputation`/`clan_reputation_delta`.
- **Step 3** — Added `ClanUpdate.clan_reputation_delta: float = 0.0` (`src/core/updates.py`),
  folded into `is_noop()`. `apply.py`'s clan-merge block now computes
  `new_reputation = max(0.0, min(2.0, existing.clan_reputation + cu.clan_reputation_delta))` and
  passes it into the `replace(existing, ...)` call, mirroring `FactionState.tension_level`'s
  additive-clamp pattern.
- **Step 6** — Added `CLAN_REPUTATION_MISCONDUCT_DELTA: float = -0.25` as a module-level constant
  in `src/systems/social_systems/clan_lifecycle.py`, imported by both the party-defection hook
  (`groups.py`) and the contract-betrayal hook (`contracts.py`).
- **Step 4** — Added `ClanLifecycleService.find_clan_id_for_entity()` (sorted O(n_clans) scan,
  `clan_lifecycle.py`). Wired into `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py`):
  when a member's `check_defection()` call produces an `entity_upd` (defection occurred), the
  member's clan (if any) is looked up and a `ClanUpdate(clan_reputation_delta=
  CLAN_REPUTATION_MISCONDUCT_DELTA)` is appended to a `new_clan_updates` list seeded from
  `update.clan_updates`; the final `return replace(...)` now also passes
  `clan_updates=new_clan_updates`.
- **Step 5** — Added `ContractService.compute_betrayal_clan_reputation_update()` as a new, separate
  static method in `contracts.py` (does not touch `resolve_contract_outcome`'s 2-tuple return
  signature). Confirmed, as the plan discloses, that `process_active_contracts()` never passes
  `betrayal=True`/`betrayer_id` today, so this method has no live pipeline caller — deliberately
  left that way per the plan's explicit, re-confirmed scope decision.
- **Step 7** — `appraise_contract()`'s no-bond branch (`appraisal.py`) now computes `clan_trust`
  via `find_clan_id_for_entity()` and applies the corrected additive-delta formula: `trust_score =
  (public_trust * 0.7) + (history_trust * 0.3) + (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` with
  `CLAN_INFLUENCE_WEIGHT = 0.2`. The `if bond:` branch is untouched. Verified algebraically and by
  test that `tests/unit/social/test_parity_soc_134.py` (P0, SOC-134) passes unmodified — the delta
  term is exactly `0.0` at the no-clan/neutral-clan case.
- **Step 8** — Added `test_clan_reputation_aggregation_is_deterministic` (new file
  `tests/unit/domains/faction/test_clan_reputation_association.py`), asserting
  `find_clan_id_for_entity()` output is independent of `state.clans` dict insertion order.
- **Step 9** — Added `test_no_writes_to_member_public_reputation_from_clan_reputation_code` (new
  file `tests/architecture/test_clan_reputation_write_paths.py`), using `inspect.getsource()` on
  the four new/modified functions to guard against a `public_reputation=` write leaking in.

All five Acceptance Criteria are satisfied: (1) round-trip test added; (2) both trigger types
produce a `ClanUpdate` applied only through `apply.py`'s `clan_updates` path (party-defection
verified end-to-end through the live pipeline; contract-betrayal verified at the pure-function +
apply.py level, with its pipeline unreachability explicitly disclosed in the new test's docstring,
per the plan's re-confirmed AC2 interpretation); (3) stranger-judgment blend verified
distinguishable from the bond-present (clan-blind) branch; (4) determinism test added; (5) source-
text guard test added, zero `public_reputation=` writes found.

**Process disclosures (not silently omitted):**
- **Architecture-review NEEDS_CHANGES cycle.** The pre-Implement Review phase's first pass found a
  real, blocking P0 parity regression: Step 7's originally-proposed re-weighted three-term blend
  (`public_trust*0.5 + clan_trust*0.2 + history_trust*0.3`) would have flipped a P0-pinned test
  outcome in `SOC-134`/`test_parity_soc_134.py::test_zero_public_reputation_source_rejected`
  (`0.0*0.7+0.5*0.3=0.15<0.2` under the old formula vs. `0.0*0.5+0.5*0.2+0.5*0.3=0.25>=0.2` under
  the rejected formula). The plan was revised to the additive-delta formula actually implemented
  above (Step 7), and the revised plan was independently re-reviewed and APPROVED, including an
  independent bit-for-bit algebraic re-verification of the SOC-134 neutral-case reduction. Full
  history in `staging_artifacts/TCK-20260904-CLAN-REPUTATION-ASSOCIATION/plan.md`'s Deviations
  section.
- **Document-Update/Parity phase-boundary overlap.** During this run, the Document-Update phase
  (which per `implement-ticket.js`'s own phase description should stay outside
  `docs/parity_ledger/`) used `tools/parity_ledger_writer.py::write_entry` to update SOC-134's
  `v2_evidence` text (status/test_path unchanged) and add a new entry (originally SOC-268,
  renumbered to SOC-272 during the PR merge — a cascade from PR #123's concurrent SOC-265
  collision) for `ClanState.clan_reputation`. This is a one-time process/phase-boundary deviation, not a substance
  problem: the subsequent Parity phase independently re-verified both entries against the live code
  and both tests, found them accurate and complete, and made no further ledger writes (no duplicate
  entry created).

## Test Summary

Initial scoped run used `pytest tests/unit/domains/faction/ tests/unit/social/
tests/architecture/test_social_write_paths.py tests/architecture/test_clan_reputation_write_paths.py
tests/unit/core/test_p1_semantic_hardening.py -q` -> 448 passed. The orchestrator's structural
test-scope-coverage backstop then FAILed on this command (a cherry-picked single file inside
`tests/unit/core/` instead of the bare directory, even though `src/core/state.py` changed) — fixed
by re-scoping to the full bare directory and re-running:
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
tests/unit/domains/faction/ tests/unit/social/ tests/architecture/test_social_write_paths.py
tests/architecture/test_clan_reputation_write_paths.py tests/unit/core/
tests/unit/strategic/test_strategic_social_contracts.py
tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`
-> **695 passed**, 0 failed (final, coverage-verified run). `tests/unit/social/test_parity_soc_134.py`'s
two P0-pinned tests pass unmodified (file not touched, independently re-run standalone twice more
during Parity and Verify). `tests/architecture/test_social_write_paths.py`'s existing tests pass
unmodified (file not touched). Ran `graphify update .` after the `src/`/`tests/` changes (34743
nodes, 100704 edges, 1238 communities).

## Files Changed

- `src/core/state.py` — `ClanState.clan_reputation` field + serialization
- `src/core/updates.py` — `ClanUpdate.clan_reputation_delta` field + `is_noop()`
- `src/engine/apply.py` — clan-merge block additive-clamp branch for `clan_reputation`
- `src/engine/pipeline_phases/groups.py` — party-defection `ClanUpdate` live wiring
- `src/systems/social_systems/clan_lifecycle.py` — `find_clan_id_for_entity()` +
  `CLAN_REPUTATION_MISCONDUCT_DELTA`
- `src/systems/social_systems/contracts.py` — `ContractService.compute_betrayal_clan_reputation_update()`
- `src/systems/social_systems/appraisal.py` — stranger-judgment additive-delta blend + `CLAN_INFLUENCE_WEIGHT`
- `tests/unit/domains/faction/test_clan_state.py` — new round-trip test + idea-68 guard update
- `tests/unit/domains/faction/test_clan_reputation_association.py` — new file (party-defection
  live-wiring tests, determinism test)
- `tests/unit/social/test_appraisal_logic.py` — new stranger-judgment/bond-regression tests
- `tests/unit/social/test_contract_lifecycle.py` — new contract-betrayal `ClanUpdate` tests
- `tests/architecture/test_clan_reputation_write_paths.py` — new AC5 source-text guard test
- `staging_artifacts/TCK-20260904-CLAN-REPUTATION-ASSOCIATION/investigation.md`,
  `plan.md`, `test_plan.md` — pre-existing artifacts from this ticket's earlier Investigate/Plan
  phases (read, not modified, during this Implement run)
- `docs/mechanics/04_strategic_cognition.md` — new §10a "Clan Reputation & Guilt-by-Association Law"
- `docs/parity_ledger/social_narrative.yaml` — new entry, originally SOC-268, renumbered to SOC-272 during the PR merge; revised SOC-134 `v2_evidence` text
  (status/test_path unchanged)
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` — status annotation for idea 54;
  corrected the idea-60/idea-54 "same field" sequencing claim

## Completion Summary

Added `ClanState.clan_reputation: float` (default `1.0`, clamped `[0.0, 2.0]`) as new durable
state, written only through `ClanUpdate.clan_reputation_delta` applied in `apply.py`'s clan-merge
block. Wired a `CLAN_REPUTATION_MISCONDUCT_DELTA = -0.25` clan-reputation penalty into the live
party-defection pipeline path (`GroupPhase.resolve()`) and, at the pure-function level only (a
disclosed, pre-existing pipeline-reachability gap left as found), into contract betrayal
(`ContractService.compute_betrayal_clan_reputation_update()`). Extended
`SocialAppraisalSystem.appraise_contract()`'s stranger-judgment (no-bond) branch with an additive
`(clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` term that reduces to exactly the pre-existing formula
at the neutral/no-clan case, preserving the P0 parity entry SOC-134 and its pinned test unmodified.
All new logic is reachable only through the typed `ClanUpdate`/apply-path route; zero writes to
individual members' own `SocialComponent.public_reputation`, confirmed by both the existing repo-
wide architecture guard and a new dedicated source-text guard test. 448 scoped tests pass.
