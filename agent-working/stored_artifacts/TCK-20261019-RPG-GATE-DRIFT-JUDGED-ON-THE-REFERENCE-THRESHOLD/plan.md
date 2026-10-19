---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD
artifact_type: plan
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Plan — TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD

Branch from origin/main after #663 merges (same files: rpg_gate_report.py, the format doc, test_rpg_gate_report.py).

1. `_compare`: read `base["floor"]` (and `base["k"]` for a run row); if not numeric -> `no-data` / `contract_error` / `reference row has no recorded threshold` for that reference. Judge with the reference's values and put them in the result. Add `threshold_moved` when the candidate's `k`/`floor`/`oracle` differ from the reference's (only differing fields, both values).
2. Markdown `_note`: show `threshold moved: floor 3 -> 9` (reference -> candidate) on the row; no state change.
3. Format doc: a "Thresholds come from the reference" rule beside the drift rule: a baseline's recorded k/floor judge it; a relative floor (O2.population) is fixed once recorded; a moved threshold is reported, not used. Cite this ticket, the designer's condition and `baseline_change_policy.md`.
4. Stub metrics: add `RPG_GATE_STUB_FLOOR_SHIFT` only if the stub cannot emit a different floor today.
5. Tests per `test_plan.md`; update the `_baseline` test helper to record k/floor.
6. Hand-close, PR, ping testing-planner; AC6 needs rpg-planner's comment on the PR.

Out of scope: candidate behaviour (pinned by a test only), rpg's module, any threshold value.
