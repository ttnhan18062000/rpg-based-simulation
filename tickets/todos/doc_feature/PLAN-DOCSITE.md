# Implementation Plan — Unified Documentation Site (DocSite)

## Goal

Build a unified, searchable documentation system that covers all content layers of the project: engine contracts, mechanics laws, testing docs, simulation observability, architecture decisions, closed tickets, stored artifacts, and archived historical docs.

The system consists of two complementary layers:
- **Docusaurus** — human-navigable site with unified search across all content types
- **Frontmatter + Registry** — machine-readable metadata that feeds Docusaurus and allows agents to query doc authority, status, and layer without reading 542 files

---

## Content Types in Scope

| Directory | Content | Volume |
|---|---|---|
| `docs/mechanics/` | Mechanics Bible (authoritative simulation laws) | 8 files |
| `docs/engine/` | Engine contracts and phase documents | 137 files |
| `docs/core/` | State, entities, attributes | 5 files |
| `docs/architecture/` | ADRs | 8 files |
| `docs/systems/` | Gameplay system descriptions | 10 files |
| `docs/combat/` | Combat rulebooks per milestone | 9 files |
| `docs/observability/` | Run guides, phase observability | 26 files |
| `docs/performance/` | Performance reports | 11 files |
| `docs/strategy/` | Bounded cognition contracts | 10 files |
| `docs/compliance/` | Checklist, gap analysis | 3 files |
| `docs/testing/` + `docs/test_coverage/` | Taxonomy and coverage reports | 7 files |
| `docs/ai/` | Agent, workflow, skill docs | 5 files |
| `docs/guidelines/` | Design patterns, divergences | 3 files |
| `docs/parity_ledger/` | Machine-readable parity YAMLs | 8 files |
| `docs/archive/` | Historical docs | 173 files |
| `docs/superpowers/specs/` | Historical design specs | 33 files |
| `tickets/done/` | Closed ticket history | ~40 files |
| `stored_artifacts/*/` | Investigation, plan, test_plan per ticket | ~120 files |

---

## Approach

### Layer 1 — Frontmatter schema (Ticket 1)
Every markdown file gets a YAML frontmatter block that classifies it:
- `status`: `authoritative` / `active` / `historical` / `archive`
- `layer`: `mechanics` / `engine` / `testing` / `simulation` / `ai` / `architecture` / `core` / `ticket` / `artifact`
- `authority`: `P0` (law, gates on it) / `P1` (active reference) / `P2` (historical/FYI)
- `audience`: `developer` / `agent` / `designer` / `historical`
- `tags`: free list for cross-cutting topics
- `last_verified`: ISO date

Tickets and artifacts get additional fields (`ticket_id`, `phase`, `artifact_type`).

### Layer 2 — Docusaurus site (Ticket 2)
Docusaurus 3 with `@docusaurus/plugin-content-docs` instances pointing at each content root, `docusaurus-search-local` for offline search, and tag index pages driven by frontmatter. One `make docs-serve` command starts the site.

### Layer 3 — Frontmatter rollout (Tickets 3, 4, 5)
Apply frontmatter across three passes in parallel:
- **Live docs** (Ticket 3): the ~150 actively referenced docs
- **Tickets + Artifacts** (Ticket 4): `tickets/done/` and `stored_artifacts/`
- **Archive** (Ticket 5): bulk minimal tagging of `docs/archive/` and `docs/superpowers/specs/`

### Layer 4 — Registry (Ticket 6)
A Python script reads frontmatter across all content types and generates `docs/REGISTRY.yaml` — a flat list of every doc with its metadata. Updated in CI or manually. Agents use it for fast doc discovery without reading files.

### Layer 5 — Content integration (Ticket 7)
Wire all sources into Docusaurus with proper sidebars, tag pages, status badges, and artifact grouping (investigation + plan + test_plan shown together per ticket ID).

---

## Ticket Dependency Graph

```
[1] SCHEMA ──┬──→ [3] FRONTMATTER-LIVE ──────────────┐
             ├──→ [4] FRONTMATTER-TICKETS-ARTIFACTS ───┼──→ [6] REGISTRY ──→ [7] CONTENT-INTEGRATION
             └──→ [5] FRONTMATTER-ARCHIVE ─────────────┘
[2] SCAFFOLD ────────────────────────────────────────────────────────────────→ [7] CONTENT-INTEGRATION
```

Tickets 3, 4, 5 can run in parallel after Ticket 1.
Ticket 2 can run in parallel with everything until Ticket 7.

---

## Tickets

| ID | Short name | Depends on | Effort |
|---|---|---|---|
| TCK-20260606-DOCSITE-SCHEMA | Frontmatter schema definition | — | Small |
| TCK-20260606-DOCSITE-SCAFFOLD | Docusaurus initialization | — | Medium |
| TCK-20260606-DOCSITE-FM-LIVE | Frontmatter — live docs | SCHEMA | Medium |
| TCK-20260606-DOCSITE-FM-TICKETS | Frontmatter — tickets + artifacts | SCHEMA | Medium |
| TCK-20260606-DOCSITE-FM-ARCHIVE | Frontmatter — archive bulk pass | SCHEMA | Small |
| TCK-20260606-DOCSITE-REGISTRY | Registry YAML + script + agent integration | FM-LIVE, FM-TICKETS, FM-ARCHIVE | Small |
| TCK-20260606-DOCSITE-INTEGRATION | Docusaurus content wiring + search + polish | SCAFFOLD, REGISTRY | Large |

---

## Risks

- `docs/engine/` has 137 files — many are historical phase packages. Ticket 3 must decide which are `active` vs `historical` without reading every file. A heuristic (date-stamped files → historical, named contract files → active) will cover most cases.
- Ticket 4 touches the ticket format itself (adding frontmatter to the template in CLAUDE.md). The `ticket-scoper` and `done-checker` agents will need updating so new tickets are born with frontmatter.
- Docusaurus build lives in `website/` (or similar). `node_modules/` and `build/` must be gitignored from the start.
- `stored_artifacts/` has nested structure (one folder per ticket, 2-3 files each). Artifact grouping in Ticket 7 is the highest-complexity piece — may need a custom Docusaurus plugin or MDX wrapper.
