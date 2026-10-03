# Test Plan — TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

- `tests/tools/test_agent_ops_dashboard_stats.py`: extend to assert `SlowRunEntry`/
  `DurationOutlierEntry` carry `active_duration_s`/`idle_gap_s` (present when computable, `None`
  default otherwise, backward compatible).
- `dashboard-frontend/src/test/StatsView.test.tsx`: extend to assert the new Active/Idle columns
  render in both the Slow Runs and Duration Outliers tables.

## Scoped commands
```
pytest tests/tools/test_agent_ops_dashboard_stats.py -q
cd dashboard-frontend && npm test -- StatsView
```
