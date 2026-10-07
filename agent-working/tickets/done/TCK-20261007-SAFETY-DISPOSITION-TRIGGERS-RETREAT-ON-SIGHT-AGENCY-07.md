---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07
phase: done
date: 2026-10-07
tags: [combat, cognition, agency]
---

# TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07

## Title
A cautious disposition no longer sends an entity into retreat on sight of a hostile: the `SAFETY_PRESSURE_RETREAT` branch needs a present threat (World Rule AGENCY-07)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TacticalDecisionSystem` retreated whenever `hostiles and safety_pressure > 0.75`. `safety_pressure` is a static trait (`max(need level, drive level)` from the catalog profiles), so every `high`-safety entity fled the moment it perceived any hostile, at full HP, with the hostile far away and not targeting it. The discriminator measured on main `3e466e132` (campaign episode, 70 ticks, seeds 42 and 1337): 19 `SAFETY_PRESSURE_RETREAT` decisions, all at HP 1.0 and `safety_pressure` 0.9, 14 of them from a single perceived hostile, none from a hostile that targeted the subject. World Rule AGENCY-07 (decision 21, #392) rules that a cautious disposition lowers the bar at which a present threat makes a subject flee and never decides flight alone.

## Scope
- Gate the branch at `src/engine/tactical.py` on a present threat to the subject: own wounds, a hostile adjacent or closing, being targeted, or being outmatched by near hostiles (`src/engine/tactical_threat.py`).
- Tests that fail on the old gate; the divergence, tactical contract and parity records; the campaign tickets updated with the finding.

## Out of Scope
- Range caps on the threat terms and the threshold constants (tuning, owner decision 7).
- The deliberate-attack campaign test, which keeps its strict xfail (`TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`).
- Any flee-on-sight reflex for a specific kind (AGENCY-02 needs its own Rule; none exists).

## Acceptance Criteria
- [x] The 19 campaign full-HP retreats no longer happen without a present threat: 12 decisions remain (7 and 5), each with a named threat term, none with no term
- [x] A regression test fails on the old gate (`test_a_cautious_subject_at_full_health_does_not_flee_a_distant_untargeting_hostile`), and each threat term makes a cautious subject flee
- [x] Divergence 2.76, the tactical contract, and parity entry COMB-335 record the change
- [x] The campaign deliberate-attack xfail is checked and reported: attempts 0 / 1 to 2 / 2 against a threshold of 3, still failing, strict xfail untouched
- [x] The cooperation-share test's strict xfail is removed on test-architecture-reviewer's ruling (pooled share across seeds 42 and 1337, threshold `< 0.5` unchanged)

## Related Tickets
- TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR (closed here)
- TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS (finding recorded, stays open)
- TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK (select() cost note)

## Related Docs
- `docs/world_rules/knowledge-agency/agency-decision.md` AGENCY-07; `docs/plans/systemic_world/owner_decision_memo.md` row 21
- `docs/engine/contracts/tactical_contract.md` §4; `docs/guidelines/intentional_divergences.md` §2.76

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07/`

## Related Code Areas
- `src/engine/tactical.py`, `src/engine/tactical_threat.py`, `src/world/motivation/pressure_resolver.py`

## Assumptions / Open Questions
- The threat constants (0.7 HP, 4 tiles, 1.5x power) are engineering choices (AGENCY-07 leaves them to engineering). `TARGETED` has no range cap and `WOUNDED` needs no near hostile; the three weakest campaign cases (id 13 targeted from 11.5 tiles, id 16 wounded at 0.657 HP with hostiles 7 to 12 tiles away, id 19 outmatched 2.2x at distance 4) are kept as threats, and a cap would be tuning for a later pass.

## Implementation Notes
- `src/engine/tactical_threat.py` (new): `ThreatTerm`, `present_threat_terms(entity, hostiles)` and `safety_retreat_warranted(entity, hostiles, safety_pressure)`. Reuses `apparent_power` from `src/domains/combat_engagement/power.py` for `OUTMATCHED`; uses `navigation.last_position` for `CLOSING` and the hostile's `task.payload["target_id"]` for `TARGETED`.
- `src/engine/tactical.py`: the gate `hostiles and safety_pressure > 0.75` became `safety_retreat_warranted(...)`, a one-line swap (no ceiling grew).
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`: the cooperation-share test lost its strict xfail and now asserts the pooled share over seeds 42 and 1337 (`< 0.5` unchanged, per-seed shares in the message); the episode fixture runs both seeds once and the other tests keep reading seed 42. Added runtime: one more campaign episode, about 15 s.
- `src/domains/cooperation/services.py`: a cost warning on `find_pending_incoming_offer` and `select` (the #394 trap: without the index each call is O(N log N), so a per-entity caller must pass the tick's index).

## Test Summary
- New `tests/unit/engine/test_safety_retreat_needs_present_threat.py` (13 tests): with the old gate restored the full-HP defect test fails (the other 12 pass on both), each of the five terms makes a cautious subject flee, a distant untargeting hostile at full HP is no threat, a hostile stepping away or beyond range is not closing, a strong hostile beyond range does not outmatch, a bystander-targeting hostile is not a threat, and the gate needs both the disposition and a threat.
- Campaign episode (NORMAL pin, two identical runs each): `SAFETY_PRESSURE_RETREAT` 10 / 9 to 7 / 5 (seeds 42 / 1337); attempts 0 / 1 to 2 / 2; hostile-perceiving decisions 11 / 11 to 31 / 17; cooperation share 0.5271 / 0.4618 to 0.4962 / 0.3562 (pooled 0.4960 to 0.4363). The pooled assertion would also have passed before this change (0.4960): it guards the co-location artefact, not this fix.
- CI directory lists, run locally with `-m "not slow and not extra_slow"`: unit-core 1839 passed, 1 skipped; unit-domain 1451 passed, 1 skipped; unit-infra 2426 passed, 1 skipped; integration plus `tests/integrity` plus `tests/architecture` 1225 passed, 7 skipped, 1 xfailed. The counts above are on the branch merged with main after Lane B's legality change (the campaign shares and retreat counts were re-measured there and are unchanged). `tests/integration/campaigns` (slow, so outside those lists), run separately: 28 passed, 1 xfailed (the deliberate-attack test). Not run locally: the full Tools job and the slow suites.
- Gates (scratch venv): code-health ratchet 0 new, 0 worse; parity-ledger schema 0 rose, 0 new; mypy baseline nothing in `tactical` or `cooperation`; CI is the first real run.

## Files Changed
`src/engine/tactical_threat.py` (new), `src/engine/tactical.py`, `src/domains/cooperation/services.py` (docstring and comment only), tests as above, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md`, `docs/parity_ledger/combat_movement.yaml`; this ticket and its artifacts; the two campaign tickets.

## Completion Summary
A cautious entity retreats from a present threat, not from a hostile merely perceived. The 19 on-sight retreats fall to 12, each with a named threat term. The deliberate-attack test still fails (2 of 3 attempts) and keeps its xfail; the cooperation-share test is un-marked on a pooled-share reformulation.
