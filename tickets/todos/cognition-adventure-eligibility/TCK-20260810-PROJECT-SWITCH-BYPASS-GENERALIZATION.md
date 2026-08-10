---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
phase: open
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION

## Title
Generalize interruption-bypass rule from kind-string allowlist to score/urgency check

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User explicitly wants to extend from the existing strategy/goal/cognition design rather than binding blindly to a hardcoded allowlist: "the strategy/goal/thinking/cognition is well made, I would love to extend from that design, not a blindly bind." This ticket replaces the hardcoded kind-string allowlist in StrategicIntelligenceSystem.evaluate_project_switch() (kind=='danger' and score>80, or kind=='detour') with a generalized rule — 'detour' remains the sole unconditional structural bypass, and any other candidate project bypasses an active lock only when its score clears both the current project's effective_current_score and a real urgency floor, regardless of kind — while resolving the already-live cross-system score-scale mismatch (System A max ~2.9 vs System B up to 100) and closing the gap where AdventureDecisionPhase never calls evaluate_project_switch() at all and instead unconditionally overwrites current_project_id.

## Scope
- Replace the hardcoded allowlist in StrategicIntelligenceSystem.evaluate_project_switch() (src/systems/strategic_systems/intelligence.py L881-935, allowlist at L915) with: kind=='detour' (unconditional structural bypass) OR (score > effective_current_score AND score clears a named urgency-floor constant), regardless of kind
- Normalize the cross-system score scale (System A max ~2.9 documented in docs/mechanics/04_strategic_cognition.md §6.6 vs System B typical range up to 100, e.g. via percentage-of-declared-system-max) before applying the urgency-floor comparison — this mismatch is already live in today's unlocked comparison path (intelligence.py:925), not merely hypothetical
- Touch src/domains/adventure/phase.py so its project handoff (currently an unconditional current_project_id overwrite at L140) routes through evaluate_project_switch() (or equivalent) once its own lock/threat-release condition clears, instead of silently stealing the project slot from a live locked System-B project
- Update the 2 existing conflicting unit tests — tests/unit/strategic/test_interruption_resistance.py::test_lock_prevents_switch and tests/unit/strategic/test_project_continuity.py::test_project_lock — to reflect the new intentional loosening for non-danger/non-detour kinds, as an explicit in-scope task
- Add a regression test confirming existing danger-bypass scenarios (kind=='danger', score>80) resolve identically post-fix when effective_current_score also clears
- Add an intentional_divergences.md entry for the bypass-tightening behavior change (rationale class Enforced or Bounded, with a Verification test path) — this ticket owns that entry since it is the one changing evaluate_project_switch's behavior
- Search docs/parity_ledger/strategic_cognition.yaml directly for existing STRAT-185/186/187 entries before assuming they are absent, and update/add parity entries for this ticket's own logic change

## Out of Scope
- C1's eligibility gate change (CognitionProfileDefinition.supports_adventure_routing) and the src/domains/adventure/scoring.py HERO checks
- The narrative doc rewrite of docs/mechanics/04_strategic_cognition.md's eligibility sections and docs/simulation/domains/adventure_contract.md's eligibility table — tracked in TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (C3); this ticket is limited to the intentional_divergences.md entry and parity-ledger entries tied directly to its own code change
- docs/audits/D22_dormant_content_wiring.md — tracked in TCK-20260810-D22-DORMANT-WIRING-AUDIT (C4)

## Acceptance Criteria
- [ ] evaluate_project_switch() replaces the allowlist with: kind=='detour' (unconditional) OR (score > effective_current_score AND score clears an explicit named urgency-floor constant) regardless of kind — verified via a synthetic never-before-seen kind bypassing when both conditions are met, and blocked when either condition isn't met
- [ ] The cross-system score scale is normalized before comparison (e.g. percentage-of-declared-system-max) — verified via a test that a maximal System A candidate (100% of its own ~2.9 scale) is not structurally incapable of exceeding a low-urgency System B project post-normalization, AND a low-urgency System A candidate cannot spuriously bypass a high-urgency System B project purely from the raw-scale gap
- [ ] AdventureDecisionPhase.apply() (src/domains/adventure/phase.py L88-141) routes its own project handoff through evaluate_project_switch() (or equivalent) once its own lock/threat-release condition clears, instead of unconditionally overwriting current_project_id at L140 — verified via a test: hero with current_project_id pointing to an ACTIVE System-B project with an unexpired lock, AdventureDecisionPhase independently proposes a new route the same tick, apply() must NOT overwrite while the System-B lock is active
- [ ] Existing danger-bypass scenarios (kind=='danger', score>80) resolve identically post-fix ONLY when effective_current_score also clears (documented intentional tightening) — regression test at a current.score low enough that effective_current_score still clears
- [ ] test_lock_prevents_switch and test_project_lock (both currently assert 'regardless of score' blocking for non-danger/non-detour kinds) are explicitly updated to reflect the new intentional loosening, not left to fail as a surprise regression

## Related Tickets
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py
- src/domains/adventure/phase.py
- src/ai/goals/scorers.py
- src/core/strategic.py
- tests/unit/strategic/test_interruption_resistance.py
- tests/unit/strategic/test_project_continuity.py

## Assumptions / Open Questions
- the scale mismatch is already live in today's unlocked comparison path (intelligence.py:925), not just a plausible future risk
- AdventureDecisionPhase's unconditional overwrite (phase.py:140) is a second independent asymmetry not fixed by touching evaluate_project_switch() alone
- the exact urgency-floor value is deferred to Implement per the design doc
- presence/absence of STRAT-185/186/187 in strategic_cognition.yaml is unconfirmed by ID search and must be verified directly, not assumed

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
