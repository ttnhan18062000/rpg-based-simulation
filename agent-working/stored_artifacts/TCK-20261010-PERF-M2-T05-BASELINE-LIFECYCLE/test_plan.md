---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Test plan: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE

All in `tests/unit/perf/test_baseline_lifecycle.py` (29 tests): refusal per code with the directory unchanged (`dirty_src`, `mode_not_normal`,
`mode_sequence_empty`, `cost_accounting_version_missing`/`_stale`, `no_cause`, `unknown_cause`, `invalid_candidate`, `bad_name`); all reasons reported
together; the three kinds of accepted cause; version 1 and version 2 (prior bytes identical, `baseline_ref`, before and after identity, cause);
independent names; exclusive create (`FileExistsError`); `check` on the committed tree, an unlisted file, a listed legacy file, a valid unversioned
record, an edited earlier version, a missing predecessor, a missing promotion object; the CLI exit codes 0, 1, 2.

## Proof Plan

| Criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| Refusals leave `baselines/` unchanged | unit | behaviour | the T05 acceptance criteria | exit non-zero with a named reason, no file written | `pytest tests/unit/perf/test_baseline_lifecycle.py` |
| Versioned promotion | unit | behaviour | schema §4 `baseline_ref`, the ticket | new version, prior file byte-identical, before/after/cause recorded | same |
| Enumeration over `baselines/*.json` | unit | regression | the 15 committed files | passes on the tree, fails on an unlisted file | same |
| No `src/` change | static | diff check | OD-8 | `git diff <base> --name-only` has no `src/` path | `git diff perf-planner-m2-review --name-only | grep -c '^src/'` is 0 |
