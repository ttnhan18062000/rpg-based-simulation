---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-RETRO-STATS-REFACTOR
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260718-RETRO-STATS-REFACTOR

## Regression Surface (existing tests that must pass)

- `tests/tools/test_generate_retro.py` — all 15 tests, unmodified, calling `generate()` directly.
  This is the primary regression guard; if the refactor preserves `generate()`'s signature and
  behavior, these pass with zero changes.
- Any test importing `tools/tag_report.py` (precedent module, untouched by this ticket) —
  `tests/tools/test_tag_report.py` if it exists, to confirm no accidental cross-contamination.

## New Tests Required (per AC)

1. A new test file (or a new section in `test_generate_retro.py`) exercising the new extracted
   computation function directly — e.g. `test_compute_retro_metrics_returns_expected_keys`,
   asserting the structured result contains all documented metric categories (run_summary,
   gate_failure_breakdown, reason_code_breakdown, tag_breakdown_subsystem, tag_breakdown_skill,
   tier_distribution, agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent,
   summary_quality, slow_runs) with correct values against a small fixture, mirroring the
   existing fixture shapes (`_BASE_RUN`, `_write_ticket`, `_write_registry` helpers already in
   `test_generate_retro.py` — reuse them, don't duplicate).
2. A byte-identical-output proof test or script run: generate a retro report from the
   pre-refactor code and the post-refactor code against the same fixture data, diff them.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_generate_retro.py -q
```

## Anti-Drift Test Guards

- Assert `generate()`'s return type/signature is unchanged (still takes
  `runs, events, label, week_str=None, tickets_root=None`, still returns a Markdown `str`).
- Assert the new computation function is a pure function (no file writes, no printing) — mirrors
  this project's "Architecture tests: verify read-only logic did not mutate live state" rule.
