---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE
artifact_type: test_plan
tags: [strategy, cognition, bug]
---

# Test plan

New: `tests/unit/strategic/test_project_switch_uses_live_current_score.py`. Existing, rerun: `tests/unit/strategic`, the CI jobs' directory lists, `tests/integration/campaigns`. Gates: code-health ratchet, parity-ledger schema, mypy baseline, frontmatter and registry clean-export check.

## Proof Plan
- **Level**: unit (the helper) and arbiter-level (the duplicate-replacement symptom), plus a corpus before and after.
- **Proof kind**: regression test with a disabling control (the old comparison fails the duplicate-replacement test); before and after measurement on one tree.
- **Oracle source**: `ProjectState.score` is documented as the "Current evaluation score", and `evaluate_project_switch` compares it against a live candidate score; the scale rule of `_score_scale_max`.
- **Expected effect**: no same-kind duplicate switches; cross-kind switching shifts (disclosed); the scorer magnitudes unchanged.
- **Selected commands**: `pytest tests/unit/strategic tests/unit/ai`; the CI directory lists; `pytest tests/integration/campaigns`; `measure_switch.py` before and after.
