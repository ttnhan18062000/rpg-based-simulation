---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-BOARD-EPIC
artifact_type: test_plan
tags: [dashboard, observability, reporting, agent-monitoring]
---

# Test Plan — TCK-20260718-AGENTOPS-STATS-BOARD-EPIC

Epic tier does not carry its own test suite — each child ticket owns its own test plan and test
run. This file aggregates what was actually verified across all 4 build tickets, as the epic-level
rollup.

## Aggregate verification, by child ticket

- **RETRO-STATS-REFACTOR**: `git stash` before/after comparison of both `stdout` and
  `agent-monitoring/retro/RETRO-ALL.md` — byte-identical, independently re-run and confirmed by the
  coordinating session (not just the implementer's own claim). 20/20 tests passing
  (`test_generate_retro.py`).
- **AGENTOPS-STATS-API**: `GET /api/stats/agent-monitoring` hit directly via `curl` after killing a
  stale `dashboard-serve` process, confirmed real structured data (not mocked). 77/77 backend tests
  passing at that point.
- **TICKET-CORPUS-REPORT**: `tools/ticket_stats_report.py` run directly against the real corpus,
  cross-checked against `GET /api/stats/tickets`'s output for an exact match. 87/87 backend tests
  passing at that point.
- **STATS-TAB-FRONTEND**: 71/71 frontend tests passing (`npm test -- --run`), `npm run build`
  clean, backend boundary/isolation tests unaffected (6/6). Live end-to-end verification via a
  freshly-rebuilt `make dashboard-serve` and a headless-Chromium (Playwright) run against the real
  Stats tab: rendered numbers matched direct `curl` output exactly, zero console errors, working
  hover tooltips. Static architecture check: zero findings across 11 changed/added files.
- **STATS-DOCS-UPDATE**: `validate_frontmatter.py` clean on all 3 changed docs; parity ledger
  re-checked end to end for staleness across all prior child tickets, none found.

## What was independently re-verified (not just trusted from self-reports)

The coordinating session independently re-ran the byte-identical comparison for ticket 1, hit the
live endpoint directly for ticket 2 (after clearing a stale server process itself), and re-ran
`tools/ticket_stats_report.py` directly for ticket 3 before handing control back to continue this
epic — all three confirmed clean with no corrections needed, as recorded in this session's own
coordination log.
