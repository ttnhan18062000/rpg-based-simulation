---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-RETRO-OUTLIER-FLAGS
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260719-RETRO-OUTLIER-FLAGS

## Regression Surface

- `tests/tools/test_generate_retro.py` — all pre-existing tests must pass, with exactly one
  updated (the documented-keys assertion, for the new `outliers` key).
- `tests/tools/test_agent_ops_dashboard_stats.py` — must pass unmodified, proving the new
  `outliers` key doesn't break the dashboard's typed API-boundary mapping (and confirming it
  genuinely isn't exposed there, per this ticket's explicit scope).

## New Tests Required

- Duration outliers computed against the **tier-scoped** median, not a global one — a run in one
  tier must not be flagged/unflagged based on another tier's typical duration.
- Null `duration_s` (in-progress runs) excluded from both flagging and the median basis.
- A tier group below the minimum size is skipped entirely — no flags from a 1-2-point "median."
- Cost-proxy-score outliers grouped by **normalized** phase (casing variants merge into one group).
- Events with no `cost_proxy_score` at all excluded from both flagging and the median basis.
- The "## Outliers" section is omitted from the rendered report when nothing is flagged.
- The section renders with correct content (both subsections, correct ratio formatting) when
  something is flagged.

## Real-Data Verification (beyond unit tests)

Run `python3 tools/agent-monitoring/generate_retro.py --all` against the full live
`agent-monitoring/{runs,events}.jsonl` corpus and manually confirm the output includes D25's own
originally-cited 34,837 cost_proxy_score finding as a live-computed outlier — proves the fix closes
a real, previously-known gap, not just synthetic-fixture correctness.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_generate_retro.py -q
python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py -q
python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent"
```

## Anti-Drift Test Guards

- The tier-scoped-vs-global median test is load-bearing — it's what proves the Plan-phase decision
  (tier-scoped) was actually implemented, not just decided in prose.
- The normalized-phase-grouping test directly exercises the synergy with
  `TCK-20260719-PHASE-AGENT-CASE-FOLD` — a regression here would silently re-fragment outlier
  groups even though the sibling ticket's own tests still pass in isolation.
