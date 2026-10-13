---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER
date: 2026-10-12
tags: [performance, benchmarking, testing]
---

# Test plan: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

Tests: `tests/unit/perf/test_known_debt.py`. The real ledger lints clean. An entry that expires before it was added, an expired entry for a failing lane, a shadowed entry, an ownerless entry, an unknown field and eight malformed signatures are rejected. The vocabulary equals the real `compare()` check names. `main` exits 1 on a bad or missing file.
