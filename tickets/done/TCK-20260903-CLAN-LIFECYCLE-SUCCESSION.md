---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION
phase: done
date: 2026-09-03
tags: [social]
---

# TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Title
Clan lifecycle — joining, leaving, and succession-on-death

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 40 — build Clan lifecycle mechanics (joining, leaving, succession) on the Party Formation & Lifecycle precedent (party_lifecycle.py). Investigation found party_lifecycle.py's SOC-228 check_leadership does NOT fire on death (pure sociability-margin comparison, no leader-liveness check) — the death/succession path must be built fresh rather than assumed to piggyback on SOC-228. groups.py's dissolve-on-dead-leader (SOC-176/SOC-189) is a separate code path for Groups and stays unmodified. This ticket wires ClanState (schema-only since TCK-20260831-CLAN-STATE-SCHEMA) into the authoritative mutation pipeline for the first time, resolving docs/guidelines/intentional_divergences.md §2.48's deferred succession-on-death divergence. Idea 68 (Inter-Clan Relations) is explicitly out of scope.

## Scope
- Clan joining routes through SocialAppraisalSystem.appraise_contract() (or a new dedicated ContractKind-based method), following the TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT direct ContractKind+appraise_contract() pattern (no shared generic ProposalState base class); adds entity to member_entity_ids via typed StateUpdate/ClanUpdate.
- Clan leaving removes entity from member_entity_ids via typed StateUpdate/ClanUpdate and emits a Clan-specific event.
- Clan succession: on dead/inactive leader, promote highest-sociability surviving member to leader_entity_id, no 0.2-margin election gate.
- Clan dissolution: set dissolved_tick only when member_entity_ids and an asset/institutional-footprint measure are BOTH empty simultaneously.
- Wire ClanState into AuthoritativeState/StateUpdate/apply.py (first-time wiring).
- Update docs/guidelines/intentional_divergences.md §2.48 Verification field, flip Status DEFERRED→RATIFIED.
- Add a dedicated parity ledger entry for the new lifecycle logic (not reuse of SOC-166/228/230/256).
- Update tests/unit/domains/faction/test_clan_state.py's test_clan_state_does_not_touch_authoritative_state, which becomes stale once wired.

## Out of Scope
- Idea 68 (Inter-Clan Relations) — any tension_level interaction beyond what joining/leaving naturally touches.
- Group's (non-Clan) dissolve-on-dead-leader path (groups.py SOC-176/SOC-189) — unmodified.
- Personal inheritance / heir assignment (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT) — distinct scope, not Clan leadership succession.
- Any new asset/institutional-footprint mechanic beyond the minimum needed for the "zero assets" dissolution AC — if out of reach this ticket, defer explicitly as an open question, never silently invent.

## Acceptance Criteria
- [x] A dead or inactive Clan leader results in promotion of the highest-sociability surviving member to leader_entity_id, with no 0.2 sociability-margin gate (unlike Group's living-leader election, party_lifecycle.py SOC-228).
- [x] A Clan's dissolved_tick is set only when member_entity_ids is empty AND the Clan's asset/institutional-footprint measure is also empty/zero, simultaneously — either alone does not dissolve the Clan.
- [x] Joining a Clan routes through SocialAppraisalSystem.appraise_contract() (or an equivalent dedicated typed-contract method), never silent auto-composition; the shared trust hard-cancel prelude (appraisal.py lines 48-54) remains unmodified.
- [x] Leaving a Clan removes the entity from member_entity_ids via a typed StateUpdate/ClanUpdate (never direct field mutation) and emits a Clan-specific event.
- [x] docs/guidelines/intentional_divergences.md §2.48's Verification field is updated with the landed test path, and Status flips DEFERRED→RATIFIED.
- [x] tests/unit/domains/faction/test_clan_state.py's test_clan_state_does_not_touch_authoritative_state is updated/replaced to reflect ClanState is now wired (not left contradicting reality).
- [x] A new dedicated parity ledger entry (docs/parity_ledger/social_narrative.yaml) is added for Clan lifecycle logic, distinct from SOC-166/228/230/256.

## Related Tickets
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
- TCK-20260619-E41B-LEADERSHIP
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
- TCK-20260831-TRUST-GATED-TEACHING

## Related Docs
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/party_lifecycle.py
- src/systems/world_systems/groups.py
- src/core/state.py
- src/core/strategic.py
- src/systems/social_systems/appraisal.py
- tests/unit/social/test_party_lifecycle.py
- tests/unit/social/test_groups.py
- tests/unit/domains/faction/test_clan_state.py

## Assumptions / Open Questions
- Whether the "zero assets" dissolution rule requires a new ClanState schema field (no assets/institutional-footprint concept exists today) is an open Plan-phase question — may need a schema addition, or the AC may need scoping down to member_entity_ids-only with assets deferred to a follow-up ticket. Do not silently invent a field.
- Wiring ClanState into AuthoritativeState/StateUpdate/apply.py for the first time is architecturally larger than a typical "add a service function" change — size Plan accordingly.
- No registered "social" layer exists (20 layers total); predecessor TCK-20260831-CLAN-STATE-SCHEMA used layer: core — follow the same choice unless a new layer is registered.

## Implementation Notes
Implemented staging_artifacts/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION/plan.md's 11 steps in order,
with one placement deviation (documented in that plan.md's Deviations section): the new Mechanics
Bible section landed as **§10** "Clan Lifecycle Law", not §9 — by the time this ticket implemented,
a different, unrelated §9 ("Coming of Age Archetype-Choice Roll", idea 34) had already landed in
`docs/mechanics/04_strategic_cognition.md` after the plan was written, so §9 was taken. Content and
subsection shape (Gate/Direction/Durable record/Succession/Dissolution/Out of scope/Source) mirror
§8 Marriage Proposal Law exactly, as instructed; only the section number differs from the plan's
literal text.

Key implementation points:
- `ClanState.asset_ids: Tuple[int, ...] = ()` added (Step 1) with round-trip serialization; no
  mutator, no producer/consumer anywhere else in the codebase — deliberately inert, per the
  architecture-review's additional instruction. This inertness is stated explicitly in both the new
  Mechanics Bible §10 ("It is currently always empty in every real run...") and SOC-264's `text`/
  `divergence_note` fields (parity ledger), not merely implied.
- `AuthoritativeState.clans` / `StateUpdate.clan_updates` / `apply.py`'s clan-merge block mirror
  `FactionState`'s 6-touch-point pattern exactly (Steps 2-4).
- `ContractKind.CLAN` + `SocialAppraisalSystem._appraise_clan()` (Step 5) reuse the shared trust
  prelude only — lines 47-54 of appraisal.py were read but not modified (confirmed via full-suite
  regression pass on tests/unit/social/test_appraisal_logic.py).
- `ClanLifecycleService` (Step 7, `src/systems/social_systems/clan_lifecycle.py`) is a fresh module
  with zero imports from `party_lifecycle.py`/`groups.py`, verified by a new architecture-guard test
  (`test_clan_lifecycle_service_does_not_import_group_lifecycle`, AST-based). `process_succession`
  re-implements the same-tick is_alive/is_active pattern locally (not imported from groups.py).
- Two-phase join/leave design (Step 8) exactly as the plan specified: `CoreActions.execute_join_clan`/
  `execute_leave_clan` decide ACCEPTED/CANCELLED only (routed through `ActionRouter`, gated by the
  existing readiness check); the new `ClanLifecyclePhase`
  (`src/engine/pipeline_phases/clan_lifecycle.py`), wired into `pipeline.py` immediately after the
  `groups` phase, reads the SUCCESS/FAILURE outcome annotated onto `task.payload_set` by
  `ActionRoutingPhase.route()` and performs the actual `ClanUpdate` write plus the succession/
  dissolution passes over `state.clans`.
- `docs/guidelines/intentional_divergences.md` §2.48 flipped DEFERRED → RATIFIED with the real
  landed test paths (Step 9).
- SOC-264 added via `tools/parity_ledger_writer.py` (never hand-edited YAML), after confirming its
  own `test_path` passes (Step 11). The writer's `write_entry()` also rebuilt
  `tools/parity_index.py`'s derived SQLite index in-process.
- `make knowledge-index-update` run after the docs/ edits (intentional_divergences.md,
  04_strategic_cognition.md) per the project's After-Work rule — incremental, 25 files re-embedded.

## Test Summary
New test files: `tests/unit/domains/faction/test_clan_succession.py` (14 tests),
`tests/unit/domains/faction/test_clan_lifecycle.py` (3 tests), `tests/unit/social/test_clan_appraisal.py`
(9 tests). Extended `tests/unit/domains/faction/test_clan_state.py` (replaced the stale
`test_clan_state_does_not_touch_authoritative_state` with `test_clan_state_is_wired_into_authoritative_state`,
plus new wiring tests mirroring `test_faction_state.py` 1:1, plus an idea-68 scope-creep guard).

Ran (all passing):
- `pytest tests/unit/domains/faction/test_clan_state.py tests/unit/domains/faction/test_clan_succession.py tests/unit/domains/faction/test_clan_lifecycle.py tests/unit/social/test_clan_appraisal.py -x -v` — 36 passed.
- `pytest tests/unit/domains/faction/ tests/unit/social/ -v` — 408 passed (full regression, proves Faction/Group/Marriage/Teach paths untouched).
- `pytest tests/integration/scenarios/test_faction_campaign.py -v` — 3 passed (Faction apply-path regression).
- `pytest tests/unit/engine/ -m "not slow"` — 182 passed, 1 skipped (pipeline wiring regression).
- Combined: `pytest tests/unit/domains/faction/ tests/unit/social/ tests/unit/engine/ tests/integration/scenarios/test_faction_campaign.py -m "not slow" -q` — 589 passed, 1 skipped, 7 deselected.

## Files Changed
**Post-hoc note (merge with `origin/main`, after this ticket's own Finalize):** this ticket's
parity ledger entry was originally written as `SOC-263`. Merging `origin/main` into the M4 branch
surfaced a real ID collision — an unrelated concurrent session (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`)
had independently used `SOC-263` for a different entry first, and it landed on `main` before this
branch merged. Resolved by keeping the concurrent session's entry as `SOC-263` (already live) and
re-adding this ticket's entry under the next real free ID, `SOC-264`, via `tools/parity_ledger_writer.py`
— every reference to the old ID in this ticket, `docs/mechanics/04_strategic_cognition.md` §10, and
`docs/guidelines/intentional_divergences.md` §2.48 was updated to `SOC-264` accordingly.

- `src/core/state.py` — `ClanState.asset_ids` field + canonical dict/from_dict; `AuthoritativeState.clans` field + `to_readonly()` wiring.
- `src/core/updates.py` — `ClanUpdate` dataclass; `StateUpdate.clan_updates` field + `is_noop()`/`merge_many()` wiring.
- `src/engine/apply.py` — clan-merge block in `apply_partial`/`apply_generation`'s constructor path; `ClanState` import.
- `src/core/strategic.py` — `ContractKind.CLAN`.
- `src/core/enums.py` — `ReasonCode.CLAN_JOIN_ACCEPTED`/`CLAN_JOIN_DECLINED`.
- `src/systems/social_systems/appraisal.py` — `CLAN` dispatch branch + `_appraise_clan()`.
- `src/systems/social_systems/clan_lifecycle.py` (new) — `ClanLifecycleService` (process_leave/process_succession/process_dissolution).
- `src/observability/events.py` — `ClanMemberLeftEvent`, `ClanSuccessionEvent`.
- `src/engine/domain/core_actions.py` — `CoreActions.execute_join_clan`/`execute_leave_clan`.
- `src/engine/domain/action_router.py` — `JOIN_CLAN`/`LEAVE_CLAN` dispatch.
- `src/engine/pipeline_phases/clan_lifecycle.py` (new) — `ClanLifecyclePhase`.
- `src/engine/pipeline.py` — `clan_lifecycle` phase wired after `groups`; `_resolve_clan_lifecycle`.
- `tests/unit/domains/faction/test_clan_state.py` — replaced stale test, added wiring tests.
- `tests/unit/domains/faction/test_clan_succession.py` (new) — succession + dissolution tests.
- `tests/unit/domains/faction/test_clan_lifecycle.py` (new) — leave-service tests.
- `tests/unit/social/test_clan_appraisal.py` (new) — join/leave action-handler + appraisal-dispatch tests.
- `docs/guidelines/intentional_divergences.md` — §2.48 Verification field + Status DEFERRED→RATIFIED.
- `docs/mechanics/04_strategic_cognition.md` — new §10 "Clan Lifecycle Law".
- `docs/parity_ledger/social_narrative.yaml` — new SOC-264 entry (via `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/combat_movement.yaml` — Parity phase: fixed COMB-318's line citation into `src/engine/apply.py`, shifted by this ticket's own +18-line insertion (via `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/infrastructure.yaml` — Parity phase: fixed INFRA-324's line citation into `src/engine/apply.py` for the same reason (via `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/progression.yaml` — Parity phase: fixed PROG-024's line citation into `src/engine/apply.py` for the same reason (via `tools/parity_ledger_writer.py`).
- `staging_artifacts/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION/plan.md` — Deviations section added (Mechanics Bible section number §9→§10).
- `staging_artifacts/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION/investigation.md`, `staging_artifacts/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION/test_plan.md` — pre-existing from this run's Investigate/Plan phases (unchanged by Implement).
- `tickets/inprogress/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION.md` — this file (Implementation Notes/Test Summary/Files Changed/Completion Summary/Status/AC checkboxes).

## Completion Summary
Implemented Clan lifecycle (joining via `ContractKind.CLAN`/`appraise_contract()`, unconditional
leaving, margin-free succession-on-death, dual-gated dissolution) and wired `ClanState` into the
authoritative mutation pipeline (`AuthoritativeState`/`StateUpdate`/`apply.py`) for the first time,
mirroring `FactionState`'s 6-touch-point pattern. Membership writes go through a new two-phase
design (`CoreActions.execute_join_clan`/`execute_leave_clan` decide via `ActionRouter`;
`ClanLifecyclePhase` commits the typed `ClanUpdate`), required because `ActionRouter.execute_action`
is locked to `Dict[int, EntityUpdate]`. `docs/guidelines/intentional_divergences.md` §2.48 was
ratified and a new parity ledger entry SOC-264 was added via the schema-validating writer tool. All
36 new/changed tests pass, plus a 589-test regression pass across faction/social/engine/integration
confirms no Faction, Group, Marriage, or Teach behavior regressed.
