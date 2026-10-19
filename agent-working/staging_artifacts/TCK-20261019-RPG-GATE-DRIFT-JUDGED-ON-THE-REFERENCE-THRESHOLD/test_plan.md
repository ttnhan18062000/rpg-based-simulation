---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD
artifact_type: test_plan
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Test plan — TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD

All in `tests/unit/tools/test_rpg_gate_report.py` (+ one in `test_rpg_gate_candidate.py`):
- AC1 run row: baseline floor 3.0, candidate floor 9.0, mean diff 5.0, small se -> DRIFT judged on 3.0; result `floor == 3.0` and `threshold_moved["floor"]` shows 3.0 vs 9.0. Same case on a pooled row.
- AC1 control: same data with the candidate floor equal -> no `threshold_moved`.
- AC2 `last` floor 3.0 and `milestone-first` floor 9.0, diff 5.0: `last` DRIFT, `milestone-first` PASS, each with its own floor.
- AC3 reference row without numeric floor (run row also without k): that reference is no-data/contract_error with the detail; the other reference is judged normally; no fallback (a case where falling back would flip the state).
- Oracle: one-sided oracle (candidate has one, reference none, and the reverse) -> `threshold_moved.oracle` with null on the missing side; neither side -> no `oracle` key.
- Test Summary note: the `_baseline` helper gains k/floor because a recorded baseline carries them by contract; one test keeps a baseline WITHOUT them for AC3.
- AC4 two documents of one world with different floors -> still `contract_error` "mixed metric module versions" (#663's rule).
- AC5 candidate: documents with floor 9.0 -> the recorded candidate row has floor 9.0 and k as given.
- Markdown: `threshold moved` appears on the row and the state is unchanged.
- Run: tests/simulation_quality/rpg_gate and tests/unit/tools -k rpg_gate.
