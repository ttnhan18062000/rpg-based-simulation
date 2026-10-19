---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD
artifact_type: investigation
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Investigation — TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD

## Findings (read on origin/main after #663's head d59326d60; re-read after #663 merges)
1. `rpg_gate_report._compare(label, baseline, reasons, row_values, cur_row, world, config)` takes `floor = cur_row["floor"]` (line ~177) and `k = cur_row["k"]` (~187). `_outcome` passes `cur_row` as both `row_values` and `cur_row`. So both references are judged with the candidate's thresholds.
2. `_baseline_row` already finds the reference row for the same (id, scope, world, group, key, tick), so `base["k"]` / `base["floor"]` are one lookup away. The format doc says a baseline's run outcome rows record `k` and `floor`.
3. There is no baseline file in the repo yet (`tests/simulation_quality/rpg_gate/` has config.yaml and test_v8_fires.py only), so the ticket's "stop and report if an existing baseline lacks k/floor" assumption holds vacuously. Test baselines are built by `_baseline(...)` in `tests/unit/tools/test_rpg_gate_report.py`, which today records NO `k`/`floor` on its rows: they must gain them or every existing drift test becomes no-data.
4. `rpg_gate_candidate.build_candidate` records the candidate's own `k`/`floor` per row from the documents (run rows: `"k": row["k"], "floor": row["floor"]`); pooled rows carry `floor`. It needs no change; AC5 pins it by test.
5. Markdown: `_note` renders `d= se= k*se= floor=` per reference from the result dict. After the change `floor` and `k` in the result are the reference's; `threshold_moved` must be shown next to it.
6. Aggregation in `_outcome`: DRIFT wins over STALE over NO_DATA over PASS. A reference that is no-data for a missing threshold therefore does not hide a DRIFT on the other reference ("for that reference only").

## Decisions
- `threshold_moved` is `{"k": {"candidate": c, "reference": r}, "floor": {...}, "oracle": {...}}` listing only the fields that differ. Pooled rows have no `k` (only floor). Oracle is compared whenever EITHER side carries it (testing-planner ruling): one side present and the other absent is a move, with null for the missing side. It is skipped only when neither side has one.
- A missing threshold: run row without numeric `k` or `floor`, pooled row without numeric `floor` -> `{"state": no-data, "reason": "contract_error", "detail": "reference row has no recorded threshold"}` for that reference.
- No fallback to the candidate's values anywhere.

## Risks
- Existing report tests build baselines without k/floor: update the `_baseline` helper to record them (matching the candidate's defaults, so unchanged tests keep their meaning).
- The harness hash covers the report code? No: it covers the metric module and config; this change does not move it.
