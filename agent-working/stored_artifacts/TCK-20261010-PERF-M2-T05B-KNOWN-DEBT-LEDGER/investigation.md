---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER
date: 2026-10-12
tags: [performance, benchmarking, testing]
---

# Investigation: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

- The shared module (#502) already supports an extension field: `optional_fields` plus `strict_fields`, unit-tested upstream. Only the signature format is perf's.
- `compare()` runs six checks (`_CHECKS` in `src/perf/benchmark_record.py`); a test pins the `CHECKS` vocabulary to those names so a renamed check fails here.
- `baseline_change_policy.md` (testing, due 2026-10-13) does not exist yet; `rpg_gate_baseline_format.md` was followed for the ownership model.
