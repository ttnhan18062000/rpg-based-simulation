---
status: active
layer: observability
authority: P2
audience: developer
maturity: proposal
date: 2026-07-18
tags: [dashboard, observability, reporting, agent-monitoring]
---

# Proposal: Backend-driven glossary metadata + hover tooltips across the Agent Ops Dashboard

**Maturity: PROPOSAL** — direct follow-up request during the Stats board epic's
review, immediately after `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC` closed.
User asked for hover tooltips on enum-like labels (ticket status, run/gate
status, reason codes, "everything you think it needs") across the whole
dashboard, explicitly requiring the descriptions be **backend-owned
metadata**, not hardcoded frontend strings — "in the best scenario, this
should be stored as metadata somewhere in the backend, not the UI-layer
data, UI only load it." Confirmed scope via a direct question: broad first
pass across the whole app, not scoped to the Stats tab alone.

## Background investigation (already done, feed this to Investigate — do not redo)

No existing glossary/description infrastructure exists for this dashboard
(`search_docs` + `graphify query` both confirmed empty — the one
`MetadataContext.tsx` hit found belongs to the unrelated main game
`frontend/`, not `dashboard-frontend/`). The closest, most relevant prior
art in this repo is the **registry pattern** established twice already
today by `TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`:
`tools/tag_registry.py`/`docs/guidelines/tag_registry.jsonl` and
`tools/layer_registry.py`/`docs/guidelines/layer_registry.jsonl` — both
append-only JSONL files with a small Python module exposing `add`/`list`/
`load_registry()`. A glossary registry should follow this exact shape
(one JSON object per line, one term per entry), not a new pattern.

**Known label domains needing entries** (compiled from what's actually
rendered across the three existing views plus the new Stats tab — verify
this list is complete during Investigate, don't just copy it blindly):

- **Ticket body `## Status` values** (`tools/ticket_field_values.py`'s
  `WORKFLOW_STATUS_VALUES`): `OPEN`, `INPROGRESS`, `BLOCKED`, `DONE`,
  `EPIC_SCOPED`.
- **Ticket `## Tier` values** (`TIER_VALUES`): `hotfix`, `standard`, `epic`.
- **Ticket `## Priority` values** (`PRIORITY_VALUES`): `P0`, `P1`, `P2`, `P3`.
- **Run/gate `final_status` values** — a materially longer, messier list than
  the ticket-body enums: `DONE`, `DOD_BLOCKED`, `NEEDS_CHANGES`, `BLOCKED`,
  `CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `TESTS_FAILED`,
  `SECURITY_BLOCKED`, `STOPPED_BY_USER`, `EPIC_SCOPED`, `GATE_FAIL`,
  `ALL_SCOPED`, `DONE_NO_TICKET`, `IN_PROGRESS`/`INPROGRESS` — confirmed via
  the same `Counter` scan technique used earlier today
  (`agent-monitoring/runs.jsonl`'s distinct `final_status` values); re-run
  it fresh during Investigate, this list will have grown since this
  proposal was written.
- **`reason_code` values** — already fully enumerated and described in
  `docs/agent-monitoring/schema.md`'s "`reason_code` values" section
  (`docs/agent-monitoring/schema.md:122` onward) — this is a genuine
  existing source of truth to seed from, not reinvent.
- **Agent-monitoring event `status` values**: `ok`, `failed`, `blocked`,
  `skipped` — also already described in
  `docs/agent-monitoring/schema.md`'s "`status` values" section
  immediately above the `reason_code` one.
- **`docs/guidelines/layer_registry.jsonl` entries already carry a `note`
  field per layer** — investigate whether the glossary should read this
  directly for Layer tooltips (reusing existing data) rather than
  duplicating layer descriptions into a second registry file. Likely: yes,
  reuse `layer_registry.jsonl`'s `note` field for Layer, and a new glossary
  registry only needs to cover the domains that don't already have a
  `note`/description field somewhere (status/gate-status/reason-code/tier/
  priority/type).

## User's explicit decisions (already made, do not re-ask)

1. **Backend-owned metadata, not hardcoded UI strings.** Descriptions must
   live in a data file the backend serves, not literal strings embedded in
   `dashboard-frontend/src/*.tsx`. The frontend's job is fetch-and-render
   only.
2. **Broad first pass**, not staged by view — cover ticket status, run/gate
   status, reason codes, and "everything you think it needs" (Tier/Type/
   Priority almost certainly qualify, per the Background section above)
   across the whole dashboard, not just the new Stats tab.

## Architectural constraints (carry forward from the existing dashboard)

- Follow the registry pattern exactly (`tag_registry.py`/`layer_registry.py`
  as the direct templates): append-only JSONL, `add`/`list` CLI, a
  `load_registry()`-shaped read function, dedicated test file. Do not invent
  a new storage shape (no YAML, no embedded-in-code dict) when this repo
  already has an established, working pattern for exactly this kind of
  data.
- New API endpoint (e.g. `GET /api/glossary`) returning the full registry as
  a typed Pydantic model (`models.py`) — never a raw dict, per this
  dashboard's established API-boundary rule
  (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- Fetch-once-per-app-load on the frontend, not per-hover — cache the
  glossary client-side (e.g. a small context/hook fetched once in `App.tsx`
  and passed down, mirroring how `optionsFacets` is fetched once and reused
  across the Tickets view's filters) rather than re-fetching on every
  tooltip trigger.
- Reuse the existing `@radix-ui/react-tooltip` primitive already used
  throughout this app (`RecentActivityGantt.tsx`'s Gantt-bar tooltip,
  `BarChart.tsx`'s bar tooltip from the Stats work) — do not introduce a
  second tooltip library or hand-roll a new hover mechanism.
- A term with no glossary entry must degrade gracefully (no tooltip, or a
  neutral "no description" state) — never a broken/empty popover, never a
  console error, and never block rendering the label itself while the
  glossary is still loading.
- This dashboard is read-only over `tickets/**` and `agent-monitoring/
  *.jsonl` — the new registry file lives under `docs/guidelines/` (matching
  `tag_registry.jsonl`/`layer_registry.jsonl`'s location), and the dashboard
  only ever reads it, never writes.

## Concerns for Comprehend/Investigate to turn into child tickets

1. **New glossary registry + module.** `docs/guidelines/glossary_registry
   .jsonl` + `tools/glossary_registry.py`, mirroring `layer_registry.py`'s
   shape as closely as sensible (this data has more categories than Layer's
   flat single-dimension shape, so investigate whether each entry needs a
   `category` field like Tag's registry, e.g. `ticket-status` /
   `run-status` / `reason-code` / `tier` / `priority` — likely yes, unlike
   Layer). Seed it with every term found during the Background investigation
   above, each with a real, accurate one-sentence description (not
   placeholder text) — reuse `docs/agent-monitoring/schema.md`'s existing
   `reason_code`/`status` value tables as the authoritative source for those
   two domains rather than re-writing descriptions from scratch.

2. **New backend endpoint exposing the glossary as typed JSON.** New
   `GET /api/glossary` (or fold into an existing response if Investigate
   finds a cleaner fit — decide, don't presume), new Pydantic model(s) in
   `models.py`. Decide whether Layer's tooltip should be served here (by
   reading `layer_registry.jsonl`'s existing `note` field) or the frontend
   should fetch layer descriptions separately from wherever Layer's own
   canonical values are already exposed (`facets.layers` today carries no
   description, just the bare value) — a real design call, not dictated
   here.

3. **Frontend: fetch-once glossary + tooltip wiring across all four
   views.** A small shared hook/context fetching the glossary once, plus
   wrapping every relevant label (ticket Status/Tier/Priority cells in
   `TicketsView.tsx`; run/gate status text wherever it's rendered in
   `RecentActivityGantt.tsx`/`ReplayTimelineView.tsx`/`StatsView.tsx`;
   reason-code text in `StatsView.tsx`'s reason-code breakdown) in the
   existing `@radix-ui/react-tooltip` primitive, looking up its description
   from the fetched glossary. Investigate whether this needs a new small
   `GlossaryTooltip` wrapper component (label + lookup + Tooltip, one
   place) reused everywhere, rather than each call site hand-wiring Radix
   Tooltip separately four times — likely yes, follow this repo's own
   "shared component over four ad-hoc copies" precedent
   (`FilterSelect`/`StatTile`/`BarChart` are all exactly this pattern
   already).

4. **Docs update.** `docs/observability/agent_ops_dashboard_contract.md`
   needs the new endpoint/model documented (mirroring how the Stats
   endpoints were just documented). `docs/guidelines/` may want a short new
   glossary-registry doc mirroring `tag_taxonomy.md`'s shape, or this may
   fold into an existing doc — investigate rather than reflexively creating
   a new file (same call `TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE` already
   made and documented its reasoning for, re-apply that same judgment here).

## Explicitly out of scope

- Any change to the underlying meaning/behavior of ticket status, run
  status, reason codes, tier, or priority — this proposal only documents
  and surfaces existing values, never redefines or adds new ones.
- Editable/user-authorable descriptions from the dashboard UI itself — the
  registry is edited via its CLI tool (`add`/`list`), same as
  `tag_registry.py`/`layer_registry.py`; no in-app editing UI.
- Any change to `LAYER_VALUES`/`WORKFLOW_STATUS_VALUES`/`TIER_VALUES`/
  `PRIORITY_VALUES`'s actual membership — this proposal adds descriptions
  for existing canonical values, not new values.
