---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL

## Title
Build `SocialShaper` — trust/reputation/contract/group event emission moved to apply-layer push

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 5 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Migrates 10 SOCIAL-pillar
events from `event_extractor.py`'s diffing (`event_extractor.py:565-690`) to a new `SocialShaper`,
under `FeatureMode.SHADOW`.

Direct confirmation this session (`src/core/updates.py:274-299`): `SocialUpdate` already has
typed fields likely matching most of these events — `trust_delta: Dict[int, float]`,
`reputation_set: Optional[float]`, `betrayal_increment: int` — and `StrategicUpdate.
contracts_add_or_update: list[ContractState]` likely covers the 5 contract-lifecycle events
(current code diffs `entity.strategic.contracts` against `prior_ent.strategic.contracts`'
materialized `status` field, but `ContractState` objects in `contracts_add_or_update` presumably
carry their own `status` directly — same "typed record exists, extractor just isn't reading it"
pattern found everywhere else in this phase's audit).

**One genuine unconfirmed gap**, unlike every other event in this phase's audit:
`group_joined`/`group_expelled` (`event_extractor.py:565-582`) reads `entity.group_id` vs
`prior_ent.group_id` — no `group_id_set`-style field was found on any update record checked this
session. This ticket's own Investigate phase must confirm one way or the other (search
`src/core/updates.py` and wherever group membership is mutated, e.g. `src/systems/social_*` or
`src/engine/` group-handling code) — do not assume a field exists without confirming, and do not
assume it's missing without checking either.

## Scope
1. **Investigate first**: confirm `SocialUpdate.trust_delta`/`reputation_set`/`betrayal_increment`
   and `StrategicUpdate.contracts_add_or_update`'s `ContractState.status` field match the current
   diffing code's exact semantics (delta vs. absolute value, threshold comparisons like
   `reputation_delta`'s `abs(delta) > 0.05` gate and `social_memory_created`'s
   `_SOCIAL_MEMORY_THRESHOLD` — confirm these thresholds can still be applied against the typed
   field's value the same way). Separately and explicitly: resolve `group_joined`/
   `group_expelled`'s typed-record status — confirm or deny a matching field exists, don't guess.
2. Add `SocialShaper` implementing all 10 events: `social_memory_created`, `reputation_delta`,
   `group_joined`, `group_expelled`, `contract_offer_created`, `contract_offer_accepted`,
   `contract_completed`, `contract_lapsed`, `contract_expired_offer`,
   `contract_milestone_completed`. If `group_joined`/`group_expelled` turns out to genuinely lack
   a typed field, defer those 2 specifically with a named reason (matching this epic's "defer, not
   skip" mandate) rather than blocking the other 8.
3. Register under `FeatureMode.SHADOW`.
4. Add unit tests per event, including the reap-path variant of `contract_expired_offer`
   (`event_extractor.py:675-684`, contract removed entirely rather than status-transitioned).
5. Verify via real kernel run against `urban_political` (per `event_type_coverage.md`, the world
   with confirmed non-zero `cooperation_event`/`contract_expired_offer` hits under
   `ENABLE_SOCIAL_COOPERATION=ON`).
6. Update `docs/parity_ledger/social_narrative.yaml`.

## Out of Scope
- `cooperation_event` — already covered by `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY` (child 2),
  since it's implemented in that same contiguous `property_updates`-reading code block, not this
  ticket's contracts/trust/group code region.
- Delivering live — SHADOW only, cutover is child 8.

## Acceptance Criteria
- [x] `investigation.md` confirms each event's exact field mapping with file:line citations, and
      explicitly resolves `group_joined`/`group_expelled`'s typed-record status — confirmed
      present, `EntityUpdate.group_id_set` with a `-1` sentinel for "left," traced to
      `patches.py:210-211`
- [x] `SocialShaper` implements all 10 events; none deferred
- [x] Unit tests cover every event's fire condition + non-firing case, plus the contract reap-path
      variant and a regression test for the real double-firing bug found this ticket (20 tests)
- [x] Real kernel run confirms correctly-shaped SHADOW output; found and fixed a real
      `contract_expired_offer` double-firing bug (~2x mismatch → within run-to-run noise post-fix)
- [x] `docs/parity_ledger/social_narrative.yaml` updated (`SOC-240`)
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY (sibling — owns `cooperation_event`)
- TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION (DONE — Phase 1's pattern for a shaper covering
  multiple event-lifecycle-transition types from one typed list field, closest precedent to this
  ticket's contract-lifecycle work)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §1.1, §3.8
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL/`
during implementation.

## Related Code Areas
- `src/observability/event_shapers.py`
- `src/observability/event_extractor.py` (lines 565-690)
- `src/core/updates.py` (`SocialUpdate`, `StrategicUpdate.contracts_add_or_update`)

## Assumptions / Open Questions
- `group_joined`/`group_expelled`'s typed-record status is the one genuinely open question in this
  entire Phase 2 audit — resolve in Investigate, do not assume either outcome here.

## Implementation Notes
- Resolved the epic's one previously-unconfirmed field: `EntityUpdate.group_id_set` uses a `-1`
  sentinel for "left the group" (`None` = untouched this tick), confirmed by tracing the real
  materialization code (`src/engine/patches.py:210-211`), not assumed.
- `contract_milestone_completed` needed the same full-reconstruction pattern already established
  for `belief_stale`/`progression_plateau_detected` — the 3rd confirmed instance of this recurring
  shape, not a one-off.
- **Real bug found and fixed via real-kernel verification**: `contract_expired_offer` double-fired
  (~2x mismatch, 1991 vs 996) when a contract was both status-transitioned to `EXPIRED`
  (`contracts_add_or_update`) and reaped (`contracts_remove`) in the same tick — traced to two
  independent mutation functions (`check_expirations()`, `reap_expired_offers()` in
  `src/systems/social_systems/contracts.py`) both firing for the same expiring `OFFERED` contract.
  The old extractor is naturally immune (single materialized dict); a shaper reading the two raw
  update lists independently is not. Fixed by having the status-transition loop skip any contract
  ID also present in that tick's `contracts_remove`. Post-fix: 1019 vs 1022 (within normal
  run-to-run noise), `contract_offer_created` matched exactly (1049/1049).

## Test Summary
- `pytest tests/unit/observability/test_event_shapers_social.py -q`: 20 passed (new), including a
  direct regression test for the double-firing bug.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1031 passed, 6 skipped, 3 deselected (was 1011/6/3 after Child 4 — +20 matches exactly).
- Real kernel run (`urban_political_seed42_500t`, `ENABLE_SOCIAL_COOPERATION=ON`): before/after
  fix counts documented above. `SHADOW` mode confirmed 0 SOCIAL-specific deliveries.

## Files Changed
- `src/observability/event_shapers.py` — `SocialShaper`, registered in
  `PHASE2_SHAPER_REGISTRY["social"]`.
- `src/engine/kernel.py` — `SocialShaper.reset_run_state()` wired into `__init__`.
- `tests/unit/observability/test_event_shapers_social.py` (new, 20 tests).
- `docs/parity_ledger/social_narrative.yaml` (`SOC-240`).

## Completion Summary
Built `SocialShaper` covering all 10 SOCIAL events, resolving the epic's one previously-
unconfirmed field (`group_id_set`'s `-1` sentinel) by tracing real mutation code rather than
guessing. Found and fixed a real, non-trivial double-firing bug via real-kernel verification —
two independent mutation-pipeline functions producing overlapping signals for the same contract
in the same tick, invisible to the old extractor's single-materialized-view design but not to a
shaper reading raw update records directly. This is the 3rd confirmed instance of the
`belief_stale`-style full-reconstruction pattern, reinforcing it as a genuinely recurring
architectural shape for Phase 2's remaining domains to watch for. SHADOW-only, as scoped;
cutover is a separate, later ticket.
