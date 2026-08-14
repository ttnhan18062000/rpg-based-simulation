---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-TICKET-TITLE-PARSE-FIX
phase: done
date: 2026-07-17
tags: [debugging]
---

# TCK-20260717-TICKET-TITLE-PARSE-FIX

## Title
Fix backend ticket ingest returning ticket_id as the title for every ticket

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Every row's Ticket column and Title column in the dashboard's Tickets view show the exact same string (the ticket ID) instead of a distinct human-readable title, wasting roughly a third of the table's horizontal width. Investigation found the root cause: src/api/agent_ops_dashboard/ingest.py's parse_ticket_file() calls parse_h1_title(body), which is always equal to the ticket_id per the project's mandated ticket format (H1 heading == ticket_id), instead of parse_body_section(body, "Title") — the sibling function tools/generate_registry.py's collect_tickets() already uses correctly for tickets. This silently degrades the title field for the entire ticket corpus the dashboard has ever rendered, not just a rare edge case.

## Scope
- Change src/api/agent_ops_dashboard/ingest.py's parse_ticket_file() to use parse_body_section(body, "Title") instead of parse_h1_title(body), mirroring tools/generate_registry.py's collect_tickets().
- Preserve the existing null/empty-surfacing pattern used for tier/ticket_type/priority/workflow_status — an empty ## Title section yields "" (not None, since TicketSummary.title is typed non-Optional str).
- Correct docs/observability/agent_ops_dashboard_contract.md's statement that parse_h1_title is used for ticket body-section fields.

## Out of Scope
- Any frontend change — TicketsView.tsx's column rendering (separate <td> cells for ticket_id and title) is already correct.
- Changing the ticket format itself — the H1 == ticket_id convention remains mandated.

## Acceptance Criteria
- [ ] ingest.parse_ticket_file() on a ticket fixture whose ## Title body section differs from its H1/ticket_id returns record["title"] equal to the ## Title content, not the ticket_id.
- [ ] ingest.parse_ticket_file() on a ticket fixture with no ## Title section returns record["title"] == "" (matching the existing empty-surfacing pattern), not a fallback to the H1/ticket_id string.
- [ ] GET /api/tickets response's title field is distinct from its ticket_id field for every ticket fixture with a real Title section (route/integration-level regression guard, not just a parser unit test).
- [ ] docs/observability/agent_ops_dashboard_contract.md is corrected to reflect the actual parser used for the title field.

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260716-AGENTOPS-TICKETS-VIEW

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/models.py
- tests/tools/test_agent_ops_dashboard_ingest.py

## Assumptions / Open Questions
- This is a backend data-shaping bug, not a frontend bug — TicketsView.tsx already renders ticket_id and title in separate cells correctly; confirmed during investigation.

## Implementation Notes
- `src/api/agent_ops_dashboard/ingest.py::parse_ticket_file()`: replaced `title = parse_h1_title(body)` with `title = parse_body_section(body, "Title")`, mirroring `tools/generate_registry.py::collect_tickets()`'s exact pattern (no `or` fallback — `parse_body_section` already returns `""` when the section is absent, which satisfies `TicketSummary.title`'s non-Optional `str` typing without any extra normalization).
- Dropped the now-unused `parse_h1_title` import from `ingest.py` (it was only ever called at this one call site) and updated the module docstring's "Reuses" list and `docs/observability/agent_ops_dashboard_contract.md`'s Ingest/cache section to stop citing `parse_h1_title` for ticket body-section fields, explaining why (H1 == ticket_id is mandated, so `parse_h1_title` structurally could never return anything but the ticket_id).
- No change to `TicketSummary` in `models.py` — `title: str` was already correctly typed; verified before touching anything.
- Added two parser-level unit tests in `tests/tools/test_agent_ops_dashboard_ingest.py` (distinct-title fixture, missing-Title-section-yields-`""` fixture) and one route-level regression test in `tests/tools/test_agent_ops_dashboard_api.py` (`GET /api/tickets` title distinct from ticket_id), matching the ticket's three testable acceptance criteria.

## Test Summary
`python3 -m pytest tests/tools/ -k "agent_ops_dashboard" -q` → 42 passed. Also ran the full `test_agent_ops_dashboard_ingest.py`, `test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_api_boundary.py`, and `test_generate_registry.py` together (83 passed) to confirm the reuse contract (AC #3 in the parent backend ticket) and the sibling `generate_registry.py` parser behavior are both unaffected.

## Files Changed
- src/api/agent_ops_dashboard/ingest.py
- docs/observability/agent_ops_dashboard_contract.md
- docs/parity_ledger/infrastructure.yaml
- tests/tools/test_agent_ops_dashboard_ingest.py
- tests/tools/test_agent_ops_dashboard_api.py

## Completion Summary
Fixed `parse_ticket_file()` to source `TicketSummary.title` from the ticket's `## Title` body section via `parse_body_section(body, "Title")` instead of `parse_h1_title(body)`, which was structurally guaranteed to equal `ticket_id` under this project's mandated H1-equals-ticket_id ticket format. This was silently degrading the title field for every ticket the dashboard has ever rendered. The fix now mirrors `tools/generate_registry.py::collect_tickets()`'s already-correct pattern, preserves the `""`-not-`None` empty-surfacing convention required by `TicketSummary.title`'s non-Optional typing, corrects the contract doc's description of which parser backs the title field, and adds unit + route-level regression coverage. No frontend change, no ticket-format change — both explicitly out of scope and untouched.
