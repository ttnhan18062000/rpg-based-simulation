---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-REGISTRY
artifact_type: investigation
tags: [dashboard, observability, reporting]
---

# Investigation: TCK-20260718-GLOSSARY-REGISTRY

## Current Behavior
No glossary/description infrastructure exists anywhere in this repo for the Agent Ops Dashboard.
`search_docs` + `graphify query` (run during the parent epic's proposal-writing step) both
confirmed empty results specific to this dashboard. Enum-like labels the dashboard already renders
have no accompanying description anywhere the frontend could fetch from.

## Mechanics/Engine Constraints
None — this is dashboard tooling only (`tools/`, `docs/guidelines/`), not simulation/mechanics
code. No Mechanics Bible chapter or engine contract applies.

## Prior Work / Precedent
Two registries built earlier today by `TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC` are the direct
template:
- `tools/tag_registry.py` / `docs/guidelines/tag_registry.jsonl` — append-only JSONL, `category`
  field (4-way taxonomy), `add`/`list` CLI, `load_registry()` read function.
- `tools/layer_registry.py` / `docs/guidelines/layer_registry.jsonl` — same shape, no `category`
  field (Layer is single-dimension).

Glossary terms span multiple distinct domains (ticket status vs run status vs reason code vs
event status vs tier vs priority vs type), so the Tag registry's `category`-field shape is the
better fit of the two — confirmed and applied.

## Term domains and sources (compiled fresh, not copied blindly from the proposal)
- `tools/ticket_field_values.py::TIER_VALUES` = `{hotfix, standard, epic}` (3 terms).
- `tools/ticket_field_values.py::PRIORITY_VALUES` = `{P0, P1, P2, P3}` (4 terms).
- `tools/ticket_field_values.py::WORKFLOW_STATUS_VALUES` = `{OPEN, INPROGRESS, BLOCKED, DONE,
  EPIC_SCOPED}` (5 terms) — ticket body `## Status`.
- `## Type` values per `CLAUDE.md`'s Ticket Format section: `{bug, feature, refactor, chore,
  repair}` (5 terms).
- Run/gate `final_status` values, live-scanned via
  `python3 -c "..."` Counter over `agent-monitoring/runs.jsonl`
  (same technique used by earlier tickets today): `ALL_SCOPED, BLOCKED, CONFLICTS_DETECTED,
  DOD_BLOCKED, DONE, DONE_NO_TICKET, EPIC_SCOPED, GATE_FAIL, INPROGRESS, IN_PROGRESS,
  NEEDS_CHANGES, NEEDS_HUMAN_INPUT, STOPPED_BY_USER` — `DONE`/`BLOCKED`/`EPIC_SCOPED`/`INPROGRESS`
  overlap in meaning with the ticket-status set above and are registered once, not duplicated.
  `TESTS_FAILED`/`SECURITY_BLOCKED` do not currently appear in the live corpus but are real,
  reachable statuses per `.claude/workflows/implement-ticket.js`'s Test/Security-Review phases —
  registered anyway since they are genuine possible values, not speculative ones.
- `reason_code` values: fully enumerated in `docs/agent-monitoring/schema.md`'s "`reason_code`
  values" table (`conflicts_detected`, `tag_registry_rejection`, `dod_condition_failed`) —
  descriptions sourced directly from that authoritative table, not re-derived.
- Agent-monitoring event `status` values: `docs/agent-monitoring/schema.md`'s "`status` values"
  table (`ok`, `failed`, `blocked`, `skipped`) — same, descriptions sourced directly from there.

Total: 35 terms registered.

## Risks and Open Questions
- Case-sensitivity: `ok`/`failed`/`blocked`/`skipped` (event-status) share text with, but are
  distinct keys from, any uppercase ticket/run-status terms of similar spelling (no actual
  collision found: no uppercase `OK`/`FAILED`/`SKIPPED` term exists in the ticket/run-status
  domains). Confirmed no `load_registry()` duplicate-key collision after seeding all 35 terms.
- `EPIC_SCOPED` legitimately means the same thing whether encountered as a ticket `## Status`
  value or a run `final_status` value — registered once under `ticket-status`, with a description
  written to read correctly in both contexts.

## Anti-Drift Hazards
- Do not let a future ticket duplicate `tag_registry.py`'s canonical-form enforcement onto this
  registry — deliberately absent here (see `tools/glossary_registry.py`'s module docstring):
  glossary terms are existing fixed strings this repo's code already emits verbatim, not
  freely-chosen labels: forcing lowercase-hyphen form would break real terms like `DONE`, `P0`,
  `ok`.
