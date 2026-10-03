---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL
phase: open
date: 2026-08-22
tags: [cognition, combat, calibration, determinism]
---

# TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL

## Title
Offline calibration tool for the bravery combat-scoring coefficient

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The original proposal asked to replace manual grid-search calibration of the bravery scoring coefficient with an embedding-based/small-trained-model approach. Investigation found no grid-search mechanism exists to replace -- prior calibration work, including this proposal's own predecessor ticket and the recent quartile-engagement-inversion fix, used direct single-run measurement and evidence-based constant adjustment, not grid-search -- and that the proposal's stated calibration target (scoring.py's risk_multiplier) is confirmed dead code for combat routing. The actual live coefficient is CombatEngageScorer/CombatRetreatScorer's bravery multiplier in src/ai/goals/scorers.py. This ticket delivers an offline calibration tool that measures bravery-vs-engagement-rate and proposes a constant for that live coefficient, keeping the runtime scorer as a plain deterministic constant with no embedding/ML on the hot path. The source idea doc marks this work Phase 3+/not scheduled, so this is a deliberate pull-forward that must be flagged for explicit authorization, not silently assumed.

## Scope
- Build an offline tool (e.g. tools/calibrate_bravery_coefficient.py) that accepts harness-measured (bravery, combat_engage-rate) samples and outputs a proposed float coefficient
- Target the live coefficient in CombatEngageScorer/CombatRetreatScorer (src/ai/goals/scorers.py), not scoring.py's dead risk_multiplier
- Validate the proposed coefficient by substituting it into scorers.py and re-running tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x
- Update the STRAT-226 parity ledger entry (docs/parity_ledger/strategic_cognition.yaml) and adventure_contract.md's Calibration Note in the same session if the coefficient changes
- Explicitly flag in the ticket that this is a pull-forward of docs/plans/idea_embedding_latent_cognition.md's Phase 3+ scope

## Out of Scope
- Chronicle arc clustering (separate ticket)
- Social memory vector field (separate ticket)
- Cross-region culture convergence (separate ticket)
- Personality/life-arc drift mechanism (separate ticket)
- Adding any ML/embedding dependency to requirements.txt (core CI-installed deps) -- isolated optional requirements file only
- Any runtime/hot-path use of a trained model or non-deterministic inference
- Calibrating src/domains/adventure/scoring.py's risk_multiplier (confirmed dead code for this differential)

## Acceptance Criteria
- [ ] New offline tool (e.g. tools/calibrate_bravery_coefficient.py) accepts harness-measured (bravery, combat_engage-rate) samples and outputs a proposed float coefficient; it is never imported by any src/ module
- [ ] Substituting the tool's output into CombatEngageScorer.score()'s bravery*40.0 term (src/ai/goals/scorers.py:120) and re-running test_bravery_quartile_combat_rate_2x passes at >=1.5x, matching or exceeding the current 1.7421x baseline
- [ ] Ticket explicitly states the calibration target is the live coefficient in src/ai/goals/scorers.py, NOT the confirmed-dead-code risk_multiplier in src/domains/adventure/scoring.py, to prevent building a tool with zero real effect
- [ ] Any new ML/embedding dependency is added only to an isolated optional requirements file (never requirements.txt); verified by `grep -r "sklearn\|torch" src/` returning zero matches
- [ ] test_replay_determinism.py and the target harness continue to pass unmodified, confirming the runtime scorer contains only a plain constant post-calibration
- [ ] Ticket explicitly flags that this work is a pull-forward of docs/plans/idea_embedding_latent_cognition.md, which states 'Phase 3+, not scheduled yet' -- surfaced for explicit authorization, not silently assumed

## Related Tickets
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260619-E11D-SCORING-CAL
- TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/plans/idea_embedding_latent_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/ai/goals/scorers.py
- src/domains/adventure/scoring.py
- tools/calibrate_simq.py
- tests/integration/scenarios/test_entity_differentiation.py
- docs/parity_ledger/strategic_cognition.yaml
- docs/plans/idea_embedding_latent_cognition.md
- requirements.txt
- requirements-knowledge.txt
- expected: tools/calibrate_bravery_coefficient.py

## Assumptions / Open Questions
- Whether pulling this forward from 'Phase 3+, not scheduled' in docs/plans/idea_embedding_latent_cognition.md is actually authorized needs explicit confirmation before implementation
- 'Small trained model' is underspecified: the harness produces one scalar ratio per coefficient tried, not a rich labeled dataset -- unclear what a model would train on or how it would outperform direct single-parameter search; likely resolves to a simple offline search tool rather than an ML model
- Harness cost (~139s/run, extra_slow) makes iterative calibration expensive; a cheaper proxy measurement may be needed

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
