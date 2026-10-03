---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST
phase: done
date: 2026-08-30
tags: [simulation-quality, social]
---

# TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST

## Title
Cooperation-Offer Creation Not Gated on an Already-Pending Offer (Multi-Offer Burst Before First
Expiry)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Filed from `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s implementation. That ticket
added a post-expiry retry cooldown (`COOPERATION_OFFER_COOLDOWN_TICKS = 15`,
`src/systems/social_systems/contracts.py`) that correctly bounds the previously-unbounded
re-offer loop. However, real trial evidence from that ticket's own corpus run
(`highland_traverse_seed42_200t`) showed an initial multi-tick burst of several simultaneous
un-expired offers from the same entity BEFORE the first offer ever expires — offer *creation* in
`CooperationDecisionService.select()` (`src/domains/cooperation/services.py`) is not gated on
whether the entity already has a pending (`ContractStatus.OFFERED`) `RECRUITMENT` contract, only
post-expiry retry is now throttled.

This is a smaller, secondary gap than the one already fixed — the unbounded indefinite retry loop
is gone — but it's still a real duplicate-offer burst worth closing for correctness.

## Scope
- Gate cooperation-offer creation in `CooperationDecisionService.select()` on whether the entity
  already has a pending `OFFERED`/`RECRUITMENT` contract to the same (or any) candidate, similar
  in spirit to the cooldown check `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` added.
- Confirm via a real corpus trial that the initial-burst pattern is gone.
- Add a regression test.

## Out of Scope
- Any change to the post-expiry retry cooldown itself (already correctly fixed).
- Any other SOCIAL/cooperation scoring or weighting change.
- Re-anchoring any `grade_anchors.json` entries unless this fix measurably changes a real trial's
  score enough to require it (check before assuming).

## Acceptance Criteria
- An entity does not create a second simultaneous `RECRUITMENT` offer while one is already
  `OFFERED` and unexpired.
- A regression test confirms this.
- Existing cooperation/contract tests still pass.

## Related Tickets
- TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING (filing ticket, disclosed this finding)

## Related Code Areas
- src/domains/cooperation/services.py
- src/systems/social_systems/contracts.py

## Assumptions / Open Questions
None yet.

## Implementation Notes
- **`src/domains/cooperation/services.py`**: in `CooperationDecisionService.select()`, immediately
  after the existing `on_offer_cooldown` computation, added
  `has_pending_recruitment_offer = any(c.kind == ContractKind.RECRUITMENT and c.status ==
  ContractStatus.OFFERED and (c.expiry_tick <= 0 or c.expiry_tick > state.tick) for c in
  entity.strategic.contracts.values())` — a read-only scan of the entity's own already-materialized
  `strategic.contracts` map (no mutation). The `expiry_tick > state.tick` boundary (strict, not
  `>=`) deliberately mirrors `ContractService.reap_expired_offers()`'s own reap condition (`0 <
  contract.expiry_tick <= current_tick`), so this gate never disagrees with the reaper about when a
  contract stops counting as pending. Changed the existing gate from `if best_report and not
  on_offer_cooldown:` to `if best_report and not on_offer_cooldown and not
  has_pending_recruitment_offer:` — the sole change to that branch. While gated, execution falls
  through unchanged to the existing SOLO/DEFER_NO_PARTNER fallback, identical to the cooldown case.
  `CooperationIntentBridge.map_decision()` and `phase.py` were not touched.
- Added 2 regression tests to
  `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
  (`test_cooperation_offer_creation_blocked_while_pending_offer_unexpired`,
  `test_cooperation_offer_creation_allowed_once_pending_offer_expired`), adjacent to the existing
  cooldown tests, reusing their exact fixture shape with
  `V2EntityBuilder(1)....strategic(contracts={...}).build()`.
- **Real corpus trial** (`tools/evaluate_simq.py --scenario highland_traverse_seed42_200t`,
  deterministic seed 42, A/B via `git stash`): pre-fix, every one of 8 offer-creating entities
  showed a new `contract_offer_created` event on literally every tick a decision persisted (e.g.
  entity 7: ticks 19,20,...,29 — 11 consecutive offers, up to 13 for others), 84 total
  gap-under-10-tick burst instances across the run. Post-fix, zero burst instances — every entity's
  offers are now spaced by a full 10-tick offer lifetime or more (e.g. entity 7: ticks 19, 29 only).
  SOCIAL pillar `normalized_score` improved from 5.636363636363637 to 6.0202 (`event_count` 399 →
  323); grade stayed `S` in both runs, so `tests/simulation_quality/fixtures/grade_anchors.json`'s
  `highland_traverse_seed42_200t` SOCIAL anchor did **not** need re-baselining — the fix moved the
  score within the same anchor band, per the ticket's own "check before assuming" Out-of-Scope
  guard. `test_grade_within_anchor_band[highland_traverse_seed42_200t]` and all 10 pillars remain
  PASS against the unchanged anchor.
- **Docs**: added a new "Cooperation Offer Pending-Duplicate Gate" subsection to
  `docs/mechanics/04_strategic_cognition.md`, directly after the existing Retry Cooldown subsection.
  Added parity ledger entry `SOC-255` to `docs/parity_ledger/social_narrative.yaml` via
  `tools/parity_ledger_writer.py::write_entry()` (status=verified, priority=P2, cites the new test).
- **Disclosed, not a gap**: the gate is single-entity-scoped (mirrors the retry cooldown's own
  scope) — it only prevents an entity from having multiple simultaneous *outgoing* offers, not a
  target-side cap on simultaneous *incoming* offers from different entities. That's a materially
  different, unscoped question and was never part of this ticket's AC.

## Test Summary
Scoped pytest run, all green: **1016 passed, 1 deselected (slow), 0 failed**
(`pytest tests/unit/domains/ tests/integration/domains/cooperation/
tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py tests/unit/social/ -m "not slow" -q`).
2 new regression tests added and passing (see Implementation Notes). Test-scope-coverage structural
backstop (`tools/gate_checks/test_scope_coverage_static.py`) confirmed PASS — `tests/unit/domains/`
is present as required for the changed `src/domains/cooperation/services.py` file.

## Files Changed
- `src/domains/cooperation/services.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
- `docs/mechanics/04_strategic_cognition.md` (new "Cooperation Offer Pending-Duplicate Gate" subsection)
- `docs/parity_ledger/social_narrative.yaml` (new entry `SOC-255`)

## Completion Summary
Gated cooperation-offer creation in `CooperationDecisionService.select()` on whether the entity
already has a pending (`OFFERED`, unexpired) `RECRUITMENT` contract, closing the secondary
duplicate-offer-burst gap disclosed by `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`. A
real A/B corpus trial (`highland_traverse_seed42_200t`, seed 42, deterministic) confirmed the fix:
84 total per-tick duplicate-offer-burst instances pre-fix, 0 post-fix, across all 8 offer-creating
entities. SOCIAL pillar score improved (5.636 → 6.020) while staying within the same `S` grade
band, so no `grade_anchors.json` re-baseline was needed. 2 new regression tests added and passing;
the full relevant scoped regression suite (1016 tests) is green. Docs updated:
`docs/mechanics/04_strategic_cognition.md` (new subsection) and `docs/parity_ledger/social_narrative.yaml`
(new entry SOC-255). No material gaps: the gate is intentionally single-entity/outgoing-offer-scoped,
matching the retry cooldown's own precedent scope — a target-side incoming-offer cap was never part
of this ticket's AC and is a materially different question if ever wanted.
