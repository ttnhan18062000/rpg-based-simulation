---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING
phase: done
date: 2026-08-30
tags: [social, simulation-quality]
---

# TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING

## Title
Cooperation Offers Have No Retry Cooldown — Same Entity Re-Offers Every Tick After Expiry

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed from `TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE`'s due-diligence check on
`highland_traverse_seed42_200t`'s SOCIAL-pillar score decrease. That ticket's own investigation
confirmed (via direct code read of the entire `src/domains/cooperation/` package plus real
event-trace evidence) a genuine tuning gap: `src/domains/cooperation/phase.py`/`services.py` has
no cooldown or backoff after a cooperation offer expires unaccepted — the same entity fires
`contract_expired_offer` on **20-23 literally consecutive ticks**, immediately re-proposing a new
offer every tick right after the previous one lapses.

This linear accumulation of `offer_dead`-weighted `contract_expired_offer` events
(`src/simulation_quality/scorers/social.py:28,99-100`) is what drags `highland_traverse_seed42_200t`'s
SOCIAL score down enough to fail its grade-anchor band check even after the corpus-wide
re-baseline — it was deliberately left un-rebaselined and disclosed rather than silently
re-anchored, since a rapidly-repeating identical rejection is a real behavioral gap (missing
retry throttling), not a one-time legitimate signal like the rest of the corpus's SOCIAL drift.

## Scope
- Add a retry cooldown/backoff to cooperation-offer proposal logic so the same entity does not
  immediately re-propose a cooperation offer to the same (or any) target on the tick right after
  a prior offer expired unaccepted.
- Confirm the fix actually reduces `contract_expired_offer` event density for
  `highland_traverse_seed42_200t` (re-run the real corpus trial, don't assume).
- Once the fix holds, re-baseline `highland_traverse_seed42_200t`'s SOCIAL anchor entry in
  `tests/simulation_quality/fixtures/grade_anchors.json` to reflect the corrected (real) score —
  this ticket both fixes the behavior and closes out the one anchor entry the rebaseline ticket
  deliberately left open.

## Out of Scope
- Any other SOCIAL/cooperation scoring or weighting change — this is specifically about the
  missing retry cooldown, not a broader cooperation-system tuning pass.
- Re-litigating any other run_key's anchor value — only `highland_traverse_seed42_200t` is in
  scope here.

## Acceptance Criteria
- Cooperation offers have a real cooldown/backoff after expiry (implementer's judgment on the
  right mechanism — a per-entity or per-pair tick-based cooldown consistent with how other
  proposal-throttling exists elsewhere in the codebase, if any precedent exists).
- `test_grade_within_anchor_band[highland_traverse_seed42_200t]` passes after the anchor is
  updated to reflect the fixed behavior.
- A regression test confirms an entity does not re-propose a cooperation offer on the tick
  immediately following a prior expiry.

## Related Tickets
- TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE (filing ticket, disclosed this finding)

## Related Docs
- docs/testing/regression_policy.md

## Related Code Areas
- src/domains/cooperation/phase.py
- src/domains/cooperation/services.py
- src/domains/cooperation/postures.py
- src/simulation_quality/scorers/social.py
- tests/simulation_quality/fixtures/grade_anchors.json

## Assumptions / Open Questions
Exact cooldown duration/mechanism (fixed tick count vs. relationship-state-based) to be decided
during implementation, informed by whatever precedent exists elsewhere in the cooperation/social
domain for similar throttling.

## Implementation Notes
Implemented all 7 steps of `staging_artifacts/TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING/plan.md`.
Steps 1-5 (code + tests) were done during the Implement phase; Steps 6-7 (real corpus trial and the
`grade_anchors.json` anchor update) were completed by the orchestrator immediately after, once
Steps 1-5's code fix was confirmed merged into the working tree — per the plan's own dependency
ordering (Step 6 requires the fix to already be present; Step 7 requires Step 6's real output).

- **Step 1** (`src/systems/social_systems/contracts.py`): added module-level constant
  `COOPERATION_OFFER_COOLDOWN_TICKS = 15`; added `IdentityUpdate` to the existing
  `from src.core.updates import ...` line. In `ContractService.reap_expired_offers()`, inside the
  existing per-entity `expired_ids` collection loop, also detect whether any reaped contract has
  `kind == ContractKind.RECRUITMENT` (`expired_recruitment` flag). Inside the existing
  `if expired_ids:` block, when `expired_recruitment` is true, set
  `identity=IdentityUpdate(cooldown_updates={"cooperation_offer_retry": current_tick + COOPERATION_OFFER_COOLDOWN_TICKS})`
  merged alongside the existing `strategic=replace(strat_up, contracts_remove=...)` write in the
  same `replace(ent_upd, ...)` call. `SocialContractSystem.check_expirations()` (the distinct,
  separate status-transition expiry path) was not touched. Confirmed `ContractService` (not
  `SocialContractSystem`) is the correct owning class for `reap_expired_offers()` before editing.
- **Step 2** (`src/domains/cooperation/services.py`): in `CooperationDecisionService.select()`,
  added `on_offer_cooldown = state.tick < entity.identity.cooldowns.get("cooperation_offer_retry", 0)`
  immediately after the `if not help_needs:` early return. Changed `if best_report:` to
  `if best_report and not on_offer_cooldown:` — the sole change to that branch. While on cooldown,
  execution falls through unchanged to the existing SOLO/DEFER_NO_PARTNER fallback logic.
  `CooperationIntentBridge.map_decision()` and `phase.py` were not touched.
- **Step 3**: added `test_cooperation_offer_retry_blocked_within_cooldown_window` and
  `test_cooperation_offer_retry_allowed_after_cooldown_expires` to
  `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`, adjacent to
  `test_risky_objective_selects_request_help_when_good_partner_exists`, reusing its exact fixture
  shape with `V2EntityBuilder(1)....identity(cooldowns={"cooperation_offer_retry": <tick>})`. Added
  `test_reap_expired_recruitment_offer_sets_retry_cooldown` and
  `test_reap_expired_loan_offer_does_not_set_cooperation_cooldown` to
  `tests/unit/social/test_contract_lifecycle_phase7.py`, adapted from the sibling
  `test_offer_expiration_logic` pattern, calling `ContractService.reap_expired_offers(state, StateUpdate())`
  directly (no prior test in the repo exercised this function directly, confirmed by investigation.md).
- **Step 4**: added `test_cooperation_phase_no_immediate_reoffer_after_expiry_tick` to
  `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`, built on the existing
  `test_scenario_7_1_risky_objective_creates_help_request`-style fixture (from
  `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`, read first to confirm
  the harness). Drives tick T (entity A's RECRUITMENT offer to trusted ally B expires and is reaped
  via `ContractService.reap_expired_offers()`), then manually constructs entity A's tick T+1 state
  by applying the reap's own returned `EntityUpdate` (contract removed from `strategic.contracts`,
  `identity.cooldowns["cooperation_offer_retry"]` set) via `dataclasses.replace` — no full
  `AuthoritativeApplyPipeline`/`ApplyPath` import was needed since the test only needs to exercise
  the check-point (`CooperationPhase.execute()` → `CooperationDecisionService.select()`), not the
  apply machinery itself. Asserts no `RECRUITMENT`-kind contract appears in entity A's
  `strategic.contracts_add_or_update` at tick T+1, and that the decision posture is neither
  `REQUEST_HELP` nor `HIRE_SUPPORT`, with the same eligible partner B still present.
- **Step 5**: ran all 5 scoped pytest commands from `test_plan.md`/`plan.md`'s Step 5 — all passed
  with zero regressions (36 + 234 + 28 + 74 + 1 = 373 tests total across the 5 commands). The
  orchestrator later re-scoped this to the whole `tests/unit/domains/` directory (not just the
  `cooperation/` subdirectory) to satisfy the structural test-scope-coverage backstop
  (`tools/gate_checks/test_scope_coverage_static.py`, which requires the bare parent test directory
  for any changed `src/domains/*` file, not a narrower subdirectory) — re-run as 1091 passed, 0
  failed, 2 deselected (slow).
- **Step 6** (real post-fix corpus trial): ran `python3 tools/evaluate_simq.py --scenario
  highland_traverse_seed42_200t` against the merged Steps 1-5 code fix. Fresh
  `data/calibration/highland_traverse_seed42_200t/quality_report.json` shows SOCIAL
  `normalized_score` improved from the pre-fix 5.045 to **5.636363636363637** (grade `S`),
  `event_count` down to 399. Per-entity trace analysis of the raw run
  (`simulation_events.jsonl`) confirms the specific reported symptom is fixed: every entity that
  hit the cooldown (e.g. entity 7, `contract_offer_created` at ticks 19-29) creates **zero** new
  `RECRUITMENT` offers after its first `contract_expired_offer` fires and the cooldown activates —
  the observed same-tick-window `contract_expired_offer` runs (e.g. ticks 29-39) are exclusively
  the pre-cooldown backlog of offers already created before the first one ever expired, draining on
  their own pre-set 10-tick schedule, not new re-proposals. This matches the AC's literal wording
  ("does not immediately re-propose ... on the tick right after a prior offer expired") — no new
  offer is ever created on any tick following an expiry once the cooldown is active. Pre-fix, the
  same entities showed unbounded, indefinite retry (20-23+ consecutive ticks with no end within the
  observation window); post-fix, retry is bounded to a one-time initial-burst-then-hard-stop
  pattern, with any later resumption only after the 15-tick cooldown clears and (for entities that
  did resume, e.g. entity 13) with a much smaller second burst (2 offers vs. the initial 11-13).
  **Disclosed, not fixed** (explicitly out of this ticket's scope — see Out of Scope: "any other
  SOCIAL/cooperation scoring or weighting change"): the initial multi-tick burst itself (up to
  ~10-13 simultaneous pending offers to the same/different targets before the first one has a
  chance to expire and set the cooldown) is a separate, pre-existing characteristic of
  `CooperationDecisionService.select()`/`CooperationIntentBridge.map_decision()` creating a new
  offer every tick a decision persists, without ever checking for an already-PENDING (not yet
  expired) offer to the same target. This ticket's cooldown only gates re-proposing *after* an
  expiry, not preventing multiple simultaneous un-expired offers stacking up beforehand. A
  candidate follow-up ticket, if desired.
- **Step 7** (anchor update, depends on Step 6): updated only the `highland_traverse_seed42_200t`
  top-level entry's `SOCIAL` block in `tests/simulation_quality/fixtures/grade_anchors.json`
  (`score: 6.875` → `score: 5.636363636363637`, `grade` unchanged at `S`) — no other pillar in that
  entry and no other run_key's entry touched (confirmed via `git diff`, a single-line change).
  `test_grade_within_anchor_band[highland_traverse_seed42_200t]` independently re-run and confirmed
  PASSING. Note: informationally, `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  (the SOCIAL-related test named in this ticket's filing context) was checked but explicitly NOT
  touched — its current failure spans COMBAT/ECONOMY/PROGRESSION (unrelated known tick-budget
  issues) in addition to SOCIAL, and re-anchoring it is out of this ticket's scope (owned by
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`).

**Doc-line correction applied during the Document-Update phase:** investigation.md's "Docs
Requiring Update" section originally cited `docs/engine/authoritative_pipeline.md` "phase 8's
`contracts`/`expired_offers` row (line 28...)" — this line reference was wrong. Architecture review
during Review confirmed the real target is the `expired_offers` phase, **phase 38, line 58** of
`authoritative_pipeline.md`. The doc-updater agent updated that row, not line 28/phase 8.

## Test Summary
5 new unit/integration tests added (2 in `test_phase7_cooperation_decision_service.py`, 2 in
`test_contract_lifecycle_phase7.py`, 1 in `test_phase7_cooperation_phase.py`), all passing. Full
scoped regression pass, re-scoped to the whole `tests/unit/domains/` directory per the structural
test-scope-coverage backstop, run and green: **1091 passed, 0 failed, 2 deselected (slow)**
(`pytest tests/unit/domains/ tests/integration/domains/cooperation/
tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py tests/unit/social/
tests/unit/strategic/test_strategic_social_contracts.py tests/unit/progression/test_rpg_advancement.py
tests/integration/pipeline/test_combat_legality_matrix.py
tests/unit/observability/test_event_extractor_identity.py
tests/unit/observability/test_event_extractor_social_faction.py
tests/unit/observability/test_event_shapers_social.py
tests/perf/test_phase7_social_cooperation_budget.py tests/unit/core/test_p1_semantic_hardening.py
-m "not slow" -q`). Additionally, `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[highland_traverse_seed42_200t]`
independently re-run and confirmed **PASSING** after the real post-fix corpus trial (Step 6) and
anchor update (Step 7) — this is the AC-named test.

## Files Changed
- `src/systems/social_systems/contracts.py`
- `src/domains/cooperation/services.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
- `tests/unit/social/test_contract_lifecycle_phase7.py`
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`
- `tests/simulation_quality/fixtures/grade_anchors.json` (`highland_traverse_seed42_200t`'s `SOCIAL`
  block only: `score` 6.875 → 5.636363636363637)
- `docs/mechanics/04_strategic_cognition.md` (new Cooperation Offer Retry Cooldown subsection)
- `docs/engine/authoritative_pipeline.md` (phase 38 `expired_offers` row annotated)
- `docs/parity_ledger/social_narrative.yaml` (new entry `SOC-253`)
- `staging_artifacts/TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING/plan.md` (Deviations section)

## Completion Summary
Implemented a per-entity, tick-based retry cooldown (`identity.cooldowns["cooperation_offer_retry"]`,
15 ticks, reusing the existing skill-cooldown mechanism) that stops a cooperation offer from being
re-proposed the tick immediately after a prior RECRUITMENT offer expires unaccepted. The cooldown
is set in `ContractService.reap_expired_offers()` when a reaped `OFFERED` contract's
`kind == ContractKind.RECRUITMENT`, and checked in `CooperationDecisionService.select()` to gate
the "good partner exists" branch, falling through unchanged to the existing SOLO/DEFER_NO_PARTNER
logic while on cooldown. 5 new tests cover the set point, check point, and the full tick-to-tick
cooperation-phase path; the full scoped regression pass (1091 tests) is green. A real post-fix
corpus trial (`tools/evaluate_simq.py --scenario highland_traverse_seed42_200t`) confirmed the fix
measurably reduces `contract_expired_offer` density and, critically, converts the reported
unbounded/indefinite retry loop into a bounded one-time burst followed by a hard cooldown-enforced
stop — SOCIAL `normalized_score` improved from 5.045 to 5.636363636363637. The
`highland_traverse_seed42_200t` SOCIAL anchor in `grade_anchors.json` was updated to that real,
measured score, and `test_grade_within_anchor_band[highland_traverse_seed42_200t]` now passes.
`docs/mechanics/04_strategic_cognition.md`, `docs/engine/authoritative_pipeline.md`, and
`docs/parity_ledger/social_narrative.yaml` (new entry SOC-253) were updated to reflect the new
mechanic. One finding disclosed but intentionally not fixed (out of scope): a pre-existing
characteristic where an entity can create several simultaneous un-expired offers to a target before
the first one ever expires (since offer creation isn't gated on an already-pending offer, only
post-expiry retry is) — a candidate follow-up ticket if desired.
