---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENT-ROLE-GLOSSARY
artifact_type: investigation
tags: [dashboard, observability]
---

# Investigation: TCK-20260719-AGENT-ROLE-GLOSSARY

## Current Behavior

`src/api/agent_ops_dashboard/ingest.py::DashboardCache.get_glossary()`
(built by `TCK-20260718-GLOSSARY-API`) merged exactly two sources at read
time into `GET /api/glossary`'s response: `tools/glossary_registry.py`'s
`docs/guidelines/glossary_registry.jsonl` (35 terms across
ticket-status/tier/priority/type/run-status/reason-code/event-status), and
`tools/layer_registry.py`'s `docs/guidelines/layer_registry.jsonl` (19
layers, description reused from each entry's `note` field) — 54 total terms
live-confirmed before this ticket.

The Stats view's "Top agents by call volume" table
(`dashboard-frontend/src/views/StatsView.tsx`) renders one row per distinct
`agent-monitoring/events.jsonl` `agent` value (via
`tools/agent-monitoring/generate_retro.py`'s `agent_status_distribution`
computation, `e.get("agent", "?")`). This `Agent` column had no glossary
wiring at all — plain text, no hover affordance, confirmed via direct read
of `StatsView.tsx` before this ticket.

## Mechanics/Engine Constraints

None — this is dashboard tooling (read-only over `tickets/**` and
`agent-monitoring/*.jsonl`), not simulation gameplay. No Mechanics Bible or
Engine Contract chapter applies.

## Prior Work

`TCK-20260718-GLOSSARY-REGISTRY`, `TCK-20260718-GLOSSARY-API`,
`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`, `TCK-20260718-GLOSSARY-DOCS-UPDATE`
(the glossary-tooltips epic) built the registry + endpoint + frontend
wiring this ticket extends. `TCK-20260718-LAYER-REGISTRY-CONVERSION`
established the exact "merge an existing registry's own field at read time,
never duplicate it into glossary_registry.jsonl" pattern this ticket's Agent
merge mirrors for a third source.

## Key Finding: Every `.claude/agents/*.md` file already has a ready-to-use description

Confirmed via direct read of all 13 role files
(`architecture-reviewer.md`, `concern-investigator.md`, `done-checker.md`,
`implementer.md`, `investigator.md`, `mechanics-auditor.md`,
`parity-updater.md`, `planner.md`, `security-reviewer.md`,
`simulation-analyst.md`, `test-scoper.md`, `ticket-scoper.md`,
`world-debugger.md`): each has a `name:` and `description:` field in its own
YAML frontmatter, already accurate, one sentence each. This is pure
extraction/reuse, not new content authorship.

## Scope-limiting finding: not every "agent" table row maps to a role file

`agent-monitoring/events.jsonl`'s `agent` field is free text, not strictly
the 13 `.claude/agents/*.md` names. Live data confirmed a mix: real
role names (`architecture-reviewer`, `ticket-scoper`, `done-checker`,
`implementer`, `test-scoper`, `parity-updater`, `investigator`, `planner`)
alongside workflow/orchestrator-level labels with no corresponding file
(`implement-ticket`, `implement-ticket-orchestrator`, `create-tickets`,
`claude-fork-direct`, `investigate:C1`, `investigate:C2`, `finalizer` — the
last one specifically has no dedicated `.claude/agents/finalizer.md`, it's
an inline Finalize-phase label from `implement-ticket.js`). Graceful
degradation (no icon, no tooltip, no crash) for these is required and is
already this dashboard's established default for every glossary lookup.

## Risks and Open Questions

None outstanding — resolved during implementation (see Completion Summary
on the ticket for the test-isolation bug found and fixed along the way).

## Anti-Drift Hazards

- The Agent merge must reuse `extract_frontmatter` (the established single
  frontmatter-parsing path in `tools/validate_frontmatter.py`) — never a
  second, parallel frontmatter parser.
- Term key must exactly match `agent-monitoring/events.jsonl`'s `agent`
  field convention (the role file's `name:`, matching
  `docs/agent-monitoring/schema.md`'s documented "Agent identifier (matches
  `.claude/agents/{agent}.md` filename)" convention) — not the filename
  itself, not the `# Heading` title.
