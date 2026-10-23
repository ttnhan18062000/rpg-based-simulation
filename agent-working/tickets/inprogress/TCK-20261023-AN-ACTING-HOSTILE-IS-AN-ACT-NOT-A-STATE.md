---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE
phase: inprogress
date: 2026-10-23
tags: []
---

# TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE

## Title
A hostile "acts on" a subject only by an act (an attack or pursuit aimed at it, or a hit that landed), not by a state (wounded, adjacent, closing, outmatched)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
STEP B of the hunger-and-retreat work, built FIRST (designer ruling, user-confirmed on #715 comment 6356212656, memo row 88). TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE stays as step A and is measured on this ticket's tip. Decision 76: each step is measured once, at fold, against its parent.

The ruling as dispatched by rpg-planner (the designer's own text is memo row 88; replace this block with it verbatim if it differs):
- ACTING: hostile H acts on subject S only if S perceives H AND either
  - (a) H's CURRENT TASK is an attack or pursuit targeting S (the work kinds are listed in plan.md with file:line for designer confirmation; a bare payload `target_id` does not count; CLOSING is NOT used and there is no "closed this tick" stamp), or
  - (b) H took hp from S by a hit since S's previous decision, opportunity hits included. (b) adds a typed last-hit tick beside `CombatComponent.last_attacker_id`, written by CombatPatch on `damage_taken > 0`, canonical (hashed) and tested. With no stored previous-decision tick, the window anchor comes from an EXISTING field (no new constant), which the designer confirms.
  - NOT acts: wounded, adjacent, closing without (a), outmatched. They stay AGENCY-07 flight terms.
- SCOPE S1:
  - the act test replaces `present_threat_to`'s terms at `scorers.py:61` and `:69` (the row-83 bypass and the hunger/sleep escalation);
  - the panic hold at `tactical.py:203-219`: under an ESCALATED need, panic retreat and the freeze yield unless a perceived hostile is acting; without an escalated need, unchanged;
  - `tactical_rest` (rest in place, eat carried, eat at carcass) and `safety_retreat_warranted` keep the full terms.
- TESTS: AGENCY-07 flight-warrant pins keep their assertion; "a state holds back an escalated need" pins change (named in test_plan.md, old -> new; the planner's yes covers exactly those). `test_starving_wounded_merchant_eats_through_the_real_kernel` must stay green. Acting-vs-resting pairs per reader, plus "a targeting hostile still counts".
- DOCS with the diff: a divergence entry (Enforced, SURV-07 / AGENCY-07) and parity on the present-threat entry. The designer drafts the Bible 04 §1 and SURV-07 sentences once the diff exists.
- MEASURE: paired `--base 341f700d0 --new <B tip>`, seeds 42-46, 3 worlds, 5000 ticks, crowded first, after the host is free. N15 (raider 38, worker 2) and guard 11 are predicted in investigation.md first.

Why: v1_disclosure N15 (two owned known reds) and C4 (guard 11 holds in place about 180 ticks, starving, beside a resting raider and a sleeping one; `present_threat_to` is True on every sample with WOUNDED, ADJACENT, CLOSING and OUTMATCHED held). `CLOSING` is sticky: `navigation.last_position` is written only on a successful move, so a hostile that stopped keeps reading as closing.

## Scope
- A typed `last_hit_tick` on `CombatComponent`, written by `CombatPatch.apply` when `damage_taken > 0` (the same place as `last_attacker_id`, `patches.py:329`), added to `to_canonical_dict` (hashed; see plan.md).
- One acting predicate (pure read) used by the SURV-07 bypasses and the panic hold under an escalated need.
- Tests, docs and parity as listed.

## Out of Scope
- Step A (retreat escalation) and the hp line.
- `tactical_rest`, `safety_retreat_warranted`, panic start (cognition.py), engaged retreat, the CLOSING term itself.
- The hunger pull and the tactical order.
- Fixing hash coverage of other state (#593 F1).

## Acceptance Criteria
- A hostile that is only adjacent, closing, outmatching or merely present does not hold back an escalated need or hold a subject in a panic freeze; a hostile whose current task attacks or pursues the subject, or that hit it within the window, still does.
- Rest in place, eat carried, eat at carcass and the safety retreat behave exactly as before.
- `last_hit_tick` is typed, hashed, round-trips, and is written only by CombatPatch on damage.
- The named pins change as listed; the merchant-37 real-kernel test stays green.
- Paired measurement on B's tip passes the stop line, or the result goes to the owner.

## Related Tickets
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A, measured on this tip)
- the V3 step (ii) (SURV-07 row 83)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-07, rows 83/84/88)
- docs/world_rules/knowledge-agency/agency-decision.md (AGENCY-07)
- docs/mechanics/04_strategic_cognition.md §1
- docs/plans/systemic_world/owner_decision_memo.md row 88

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/tactical_threat.py, src/ai/goals/present_threat.py, src/ai/goals/scorers.py:61-75
- src/engine/tactical.py:203-219
- src/core/state.py CombatComponent, src/engine/patches.py CombatPatch

## Assumptions / Open Questions
- Window anchor and work-kind list: see plan.md, for the designer to confirm.
- Hash change: see plan.md.

## Implementation Notes
Proposal stage: no code. plan.md, investigation.md and test_plan.md are in `agent-working/staging_artifacts/TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE/`.

## Test Summary

## Files Changed

## Completion Summary
