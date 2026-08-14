---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-19
archived: 2026-07-19
tags: [dashboard, observability]
---

# Proposal: Agent-name glossary descriptions (extend the existing glossary registry with an "agent" category)

**Archived:** 2026-07-19 — shipped by `TCK-20260719-AGENT-ROLE-GLOSSARY` (`tickets/done/`):
`_load_agent_role_descriptions()` added to `src/api/agent_ops_dashboard/ingest.py` as a third
`get_glossary()` merge source (category `"agent"`), reading every `.claude/agents/*.md` role file's
own frontmatter `description:` field; the Stats view's Top Agents table `Agent` column wrapped in
`GlossaryTooltip`. Term count grew from 54 to 67. This document is the historical design reference.

**Maturity: SHIPPED** — direct user follow-up during a live bug report
("the TIER DISTRIBUTION ... tooltips ... not trigger" — a separate,
already-fixed `GroupedBarChart` hover-trigger bug). User explicitly asked
for agent-name row descriptions in the Stats view's "Top agents by call
volume" table, and added: "add agent-name rows description is a good
thing to add, not only for this feature" — read as: this is useful data
worth having in the shared backend glossary generally, not a
narrowly-scoped one-off UI hack for this one table.

## Background investigation (already done, feed this to Investigate — do not redo)

`GET /api/glossary` (`src/api/agent_ops_dashboard/ingest.py::get_glossary`,
built yesterday by `TCK-20260718-GLOSSARY-API`) already merges two sources
at read time into one response: `docs/guidelines/glossary_registry.jsonl`
(via `tools/glossary_registry.py`) plus `docs/guidelines/layer_registry
.jsonl`'s existing per-layer `note` field, re-exposed under
`category="layer"` — see `ingest.py:790-826`. This proposal adds a third
source, following the exact same "merge at read time from an existing
authoritative source, never duplicate the content into a second file"
pattern.

**Every `.claude/agents/*.md` role file already has a ready-to-use
one-sentence description** in its own YAML frontmatter `description:`
field (confirmed via direct read of all 13 files:
`architecture-reviewer.md`, `concern-investigator.md`, `done-checker.md`,
`implementer.md`, `investigator.md`, `mechanics-auditor.md`,
`parity-updater.md`, `planner.md`, `security-reviewer.md`,
`simulation-analyst.md`, `test-scoper.md`, `ticket-scoper.md`,
`world-debugger.md`). This is genuinely authoritative, already-accurate
content — not new copy to write from scratch, mirroring exactly how the
Layer merge reused `layer_registry.jsonl`'s existing `note` field rather
than writing new layer descriptions.

**Important scope-limiting finding**: the "Agent" column in the Stats
view's "Top agents by call volume" table is keyed by
`agent-monitoring/events.jsonl`'s free-text `agent` field
(`tools/agent-monitoring/generate_retro.py:277`,
`agent_stats[e.get("agent", "?")]`) — this is **not** strictly limited to
the 13 `.claude/agents/*.md` role names. Confirmed via a live Stats view
screenshot: real values include both real agent-role names
(`architecture-reviewer`, `ticket-scoper`, `done-checker`, `implementer`,
`test-scoper`, `parity-updater`, `investigator`, `planner`) **and**
workflow/orchestrator-level labels with no corresponding `.claude/agents/`
file (`implement-ticket`, `implement-ticket-orchestrator`,
`create-tickets`, `claude-fork-direct`, `investigate:C1`, `investigate:C2`,
`finalizer` — `finalizer` specifically has no dedicated
`.claude/agents/finalizer.md` file, it's an inline Finalize-phase label).
Graceful degradation for these (no icon, no crash) is required and is
already this session's established default behavior for every other
glossary lookup — no new logic needed for it, just don't assume every
`agent` value maps to a `.claude/agents/*.md` file.

## Architectural constraints (carry forward from yesterday's glossary epic)

- Extend `tools/glossary_registry.py`'s merge surface the same way Layer
  was added: read `.claude/agents/*.md` frontmatter directly at
  `get_glossary()` call time (via a small helper, mirroring
  `layer_registry.load_registry()`'s shape) — never copy agent
  descriptions into `glossary_registry.jsonl` itself as a second source of
  truth for the same content. Category should be `"agent"`.
- Term key = the agent's `name:` frontmatter field (matches the exact
  string `agent-monitoring/events.jsonl`'s `agent` field uses for a real
  agent-role run, per `docs/agent-monitoring/schema.md`'s own documented
  convention: "Agent identifier (matches `.claude/agents/{agent}.md`
  filename)").
- Frontend: wire `GlossaryTooltip` (or reuse the flattened-`descriptions`-map
  pattern `BarChart`/`GroupedBarChart` already use, whichever fits
  `StatsView.tsx`'s "Top agents by call volume" table's existing structure
  better — a plain `<table>`, not a chart) around the `Agent` column's cell
  text in that one table. Confirm no other single-value-per-row table in
  the dashboard would benefit from the same wiring while touching this
  (check `TicketsView.tsx`/`ReplayTimelineView.tsx` for any other spot an
  agent name is rendered — likely none, since agent identity is a
  Stats-view-specific concept, but verify rather than assume).
- Graceful degradation is mandatory (per the Background finding above): a
  workflow/orchestrator label with no matching `.claude/agents/*.md` file
  renders with no icon, no tooltip, no crash — same behavior every other
  glossary lookup in this dashboard already has.
- Update `docs/observability/agent_ops_dashboard_contract.md`'s existing
  glossary/`get_glossary()` description (already documents the Layer merge
  — extend it to describe the new Agent merge in the same paragraph/section,
  don't create a disconnected second description).

## Concerns for Comprehend/Investigate to turn into ticket scope

1. Add an agent-frontmatter-reading helper (reusing
   `tools/validate_frontmatter.py::extract_frontmatter` — already the
   established, single way this repo parses any file's YAML frontmatter,
   never reimplement frontmatter parsing a second way) and wire it into
   `ingest.py::get_glossary()` as a third merge source, category `"agent"`.
2. Wire the Stats view's "Top agents by call volume" table's `Agent` column
   to look up and display the description on hover, matching this
   dashboard's existing "?" icon + hover-description pattern established
   across every other label type today.
3. Update `docs/observability/agent_ops_dashboard_contract.md`'s glossary
   section.
4. Verification: live-verify the new `/api/glossary` response includes all
   13 real agent-role terms with their real frontmatter descriptions
   (re-run corpus check yourself, don't just trust a prior claim), and
   confirm live in a headless browser that hovering a real agent-role name
   (e.g. `architecture-reviewer`) in the Top Agents table shows its real
   description, while a non-agent-file label (e.g. `finalizer` or
   `implement-ticket-orchestrator`) shows no icon/tooltip and doesn't crash.

## Explicitly out of scope

- Writing NEW descriptions for agent roles — every description already
  exists in each file's own frontmatter; this is pure extraction/reuse, not
  content authorship.
- Any change to how `agent-monitoring/events.jsonl`'s `agent` field is
  populated, or to what values it can hold — this proposal only documents
  existing values that happen to match a real `.claude/agents/*.md` file,
  never invents new ones for workflow/orchestrator labels.
