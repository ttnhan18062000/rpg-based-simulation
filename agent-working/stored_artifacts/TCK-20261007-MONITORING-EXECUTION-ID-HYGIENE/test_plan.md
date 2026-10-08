---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE
artifact_type: test_plan
tags: [agent-monitoring, retro]
---

# Test plan

`tests/tools/test_validate_agent_monitoring.py` and `tests/tools/test_monitoring_anomaly_validator.py` patterns (tmp index/shards, report-only functions returning strings).
1. execution_id classification: a fixture with rows predating the identity change (start_ts before 2026-07-30), a create-tickets row, an implement-epic row, an implement-ticket row with no id -> counts per class, W40+ count only counts the post-field rows; a row WITH an id is not counted.
2. Loader-skipped tools lines: a tmp shard with one torn line -> report names file:line and a count of 1; a clean shard -> "none".
3. W40+ warning count line: `--since-week` filters by the run's start_ts week; the method string is printed; a run with no start_ts is counted as unknown, not W40+.
4. Exit-code contract: validate main returns exit 0 with only warnings (existing test stays green); no past shard is modified (hash the fixture shards before/after).
5. If the decision is "tolerate by design": a test that the by-design set is exactly {create-tickets, implement-epic} and an implement-ticket row without id falls in "unexplained".
