---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07
artifact_type: test_plan
tags: [combat, cognition, agency]
---

# Test plan

New: `tests/unit/engine/test_safety_retreat_needs_present_threat.py`. Existing, rerun: `tests/unit/engine/test_pressure_perception_consumers.py`, `tests/integration/campaigns`, and the CI jobs' directory lists. Gates: code-health ratchet, parity-ledger schema, frontmatter and registry clean-export check.

## Proof Plan
- **Level**: unit (gate and terms) and campaign episode (before/after counts).
- **Proof kind**: regression test with a disabling control (old gate restored fails the defect test); before/after measurement with identical repeat runs.
- **Oracle source**: World Rule AGENCY-07 (decision 21, #392): flight needs a present threat to the subject; a trait never decides it alone.
- **Expected effect**: no `SAFETY_PRESSURE_RETREAT` without a named threat term; the 19 on-sight retreats fall, each remaining decision has a term.
- **Selected commands**: `pytest tests/unit/engine/test_safety_retreat_needs_present_threat.py tests/unit/engine/test_pressure_perception_consumers.py tests/integration/campaigns`; the CI directory lists; `safety_probe.py` and `share_probe.py` on both seeds, two runs each.
