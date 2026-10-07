---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07
artifact_type: plan
tags: [combat, cognition, agency]
---

# Plan

1. Add `src/engine/tactical_threat.py`: the AGENCY-07 present-threat terms (WOUNDED, ADJACENT, TARGETED, CLOSING, OUTMATCHED) and `safety_retreat_warranted`.
2. Swap the `tactical.py` gate for it (one line, no ceiling grows). The disposition keeps lowering the bar: the branch exists only for `safety_pressure > 0.75`, with looser terms than the panic gate.
3. Tests: the old gate fails the full-HP defect test; each term; no-threat cases. Measure the campaign episode before and after (both seeds, two runs each).
4. Records: divergence 2.76, tactical contract section 4, parity COMB-335, the two campaign tickets, the share test's pooled assertion on test-architecture-reviewer's ruling.
5. Out of scope: range caps (tuning), the deliberate-attack xfail, any on-sight reflex.
