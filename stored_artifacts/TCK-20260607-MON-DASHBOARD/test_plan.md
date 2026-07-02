---
ticket_id: TCK-20260607-MON-DASHBOARD
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260607-MON-DASHBOARD

## Verification

1. `make docs-build` (or `cd website && npm run build`) completes with no errors
2. The built output includes pages at `/agent-monitoring/` (index) and `/agent-monitoring/RETRO-ALL`
3. Navbar shows "Agent Monitoring" link
4. `agent-monitoring/retro/index.md` is the landing page

## Manual

- `make docs-serve` → navigate to /agent-monitoring/ → landing page renders
- RETRO-ALL page reachable from sidebar
