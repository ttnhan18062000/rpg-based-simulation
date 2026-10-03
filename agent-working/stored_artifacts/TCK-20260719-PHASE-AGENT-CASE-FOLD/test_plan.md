---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-AGENT-CASE-FOLD
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260719-PHASE-AGENT-CASE-FOLD

## Regression Surface

- `tests/tools/test_generate_retro.py` — all pre-existing tests must pass, with exactly one
  updated (the documented-keys assertion, for the new `phase_status_distribution` key).
- `tests/tools/test_validate_agent_monitoring.py` — all 13 must pass with **zero source diff** to
  `validate.py` (a stronger guarantee than "still passing" — proves genuine non-interference, not
  coincidental).
- `tests/tools/test_agent_ops_dashboard_stats.py` — must pass unmodified, proving the new
  `phase_status_distribution` key doesn't break the dashboard's typed API-boundary mapping.

## New Tests Required

- Review's real merged failure rate (41 failed/184 ok across 3 casing variants → 18.2%), with an
  explicit naive-single-variant comparison (16.7%) proving the fragmentation was real and the merge
  materially changes the answer, not just a cosmetic dedup.
- The new "## Phase Status Distribution" section actually renders in `generate()`'s Markdown
  output with correctly merged counts.
- Agent-name casing merge mechanism (real data shows zero drift today, but the code path must be
  proven correct, not just assumed correct by symmetry with phase).
- `spend_proxy_by_phase` merges casing variants (proves normalization applies to all 3 affected
  aggregations, not just `agent_status_distribution`).
- Unknown-workflow run_id passes phase/agent through completely unchanged — no crash, no
  fabricated canonical spelling.
- create-tickets' `investigate:C1`/`investigate:C2` prefix-family agents are never merged into a
  single literal (there isn't one) and never collide with each other.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_generate_retro.py -q
python3 -m pytest tests/tools/test_validate_agent_monitoring.py -q
python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py -q
python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent"
```

## Anti-Drift Test Guards

- The Review-failure-rate test's naive-vs-merged comparison is load-bearing — it's what proves the
  fix changes a real, materially-different answer, not just internal bookkeeping with no visible
  effect.
- `git diff --stat -- tools/agent-monitoring/validate.py` must show zero output — checked directly
  as part of Test phase, not inferred from the test suite alone passing.
