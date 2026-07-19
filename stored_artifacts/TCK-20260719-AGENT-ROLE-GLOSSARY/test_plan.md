---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENT-ROLE-GLOSSARY
artifact_type: test_plan
tags: [dashboard, observability]
---

# Test Plan — TCK-20260719-AGENT-ROLE-GLOSSARY

## Regression Surface

- `tests/tools/test_agent_ops_dashboard_glossary.py` — all 7 pre-existing
  tests must still pass unmodified in behavior (only the real-corpus test's
  assertions were extended, not weakened).
- `dashboard-frontend/src/test/StatsView.test.tsx` — all 10 pre-existing
  tests must still pass.
- `dashboard-frontend/src/test/GlossaryTooltip.test.tsx`,
  `BarChart.test.tsx`, `GroupedBarChart.test.tsx` — unaffected by this
  ticket's changes, must stay green as a regression guard.

## New Tests Required

- Backend: agent-role merge happy path, missing-`.claude/agents/` tolerance,
  missing-`description:` skip.
- Frontend: Top Agents hint-icon present for a matching agent, absent for a
  non-matching one.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_glossary.py -q
python3 -m pytest tests/tools/ -q -k "agent_ops_dashboard or glossary"
```

## Scoped Frontend Commands

```
cd dashboard-frontend && npm run test -- --run
cd dashboard-frontend && npx tsc -b --noEmit
cd dashboard-frontend && npm run build
```

## Anti-Drift Test Guards

- The real-corpus test (`test_glossary_against_real_seeded_registries`)
  asserts against the actual repo's `.claude/agents/` directory, not a
  fixture — proves the live merge works end to end, not just on a mock.
- The missing-directory tolerance test is load-bearing: every other
  `tmp_path`-based test in this file relies on the same tolerance (none of
  them create a `.claude/agents/` directory in their skeleton), so this
  test also guards against a future regression silently breaking every
  other test in the file.
