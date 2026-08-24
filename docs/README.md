---
status: active
layer: guidelines
authority: P1
audience: developer
---

# RPG Engine Documentation

> **Browse all docs locally:** `make docs-serve` → [http://localhost:3000](http://localhost:3000)

---

## Documentation Site

The project uses a [Docusaurus 3](https://docusaurus.io/) site to make all documentation navigable and searchable in one place.

### Starting the site

```bash
make docs-serve      # Start dev server at http://localhost:3000 (live-reload)
make docs-build      # Build static site into website/build/
```

The site publishes a single section accessible from the homepage:

| Section | URL | What's in it |
|---|---|---|
| **Docs** | `/docs/` | Mechanics Bible, engine contracts, architecture decisions, guidelines — sidebar grouped by layer |

As of `TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD`, the `tickets/done`, `stored_artifacts`,
and `agent-monitoring/retro` plugin-content-docs instances (previously served at `/tickets/`,
`/artifacts/`, and `/agent-monitoring/`) were removed entirely to keep the GitHub Pages build under
its memory ceiling, and `docs/archive/`, `docs/plans/`, and `docs/audits/` were added to the `docs`
preset's own `exclude` list. That content still exists in the repo (browse it directly on disk or
via `git`) but is no longer part of the published Docusaurus site or its full-text search index.

Full-text search covers the Docs section. Each page shows a **status badge** (`authoritative` / `active` / `historical` / `archive`) based on the file's frontmatter.

### Adding new docs to the site

1. Create the `.md` file under `docs/` (or the appropriate section).
2. Add a YAML frontmatter block at the very top (see schema below).
3. Run `make docs-registry` to update the machine-readable index.
4. Run `make docs-serve` — the new file appears automatically.

---

## How the System Works

### Frontmatter classification

Every `.md` file in the project carries a YAML frontmatter block that classifies it by content type, status, layer, authority, and audience. This is the foundation that powers Docusaurus navigation, the registry index, and agent doc discovery.

Schema: [`docs/guidelines/frontmatter_schema.md`](guidelines/frontmatter_schema.md)

**Doc frontmatter** (files under `docs/`, excluding archive):
```yaml
---
status: authoritative    # authoritative | active | historical | archive
layer: mechanics         # mechanics | engine | core | architecture | systems | combat |
                         # strategy | observability | performance | testing | compliance |
                         # ai | guidelines | simulation | economy | world | misc
authority: P0            # P0 (gates on it) | P1 (active reference) | P2 (historical/FYI)
audience: developer      # developer | agent | designer | historical
tags: [combat, damage]   # optional free list
last_verified: 2026-06-06  # required when status: authoritative
---
```

**Ticket frontmatter** (files in `tickets/done/`):
```yaml
---
ticket_id: TCK-YYYYMMDD-FEATURE-NAME
title: "Short title"
status: DONE
layer: engine
authority: P1
audience: developer
date: 2026-06-06
tags: []
---
```

**Artifact frontmatter** (`stored_artifacts/*/investigation.md` etc.):
```yaml
---
ticket_id: TCK-YYYYMMDD-FEATURE-NAME
artifact_type: investigation    # investigation | plan | test_plan
layer: engine
tags: []
---
```

**Archive frontmatter** (`docs/archive/`):
```yaml
---
status: archive
authority: P2
audience: historical
layer: combat              # auto-inferred from filename
original_date: 2026-03-15  # from filename date prefix if present
---
```

### Validating frontmatter

```bash
python3 tools/validate_frontmatter.py docs/mechanics/       # check a directory
python3 tools/validate_frontmatter.py docs/engine/kernel.md # check a single file
```

Exits 0 if valid, 1 on any violation. Content type is inferred from path (no `content_type` field required).

### The doc registry

`docs/REGISTRY.yaml` is a flat machine-readable index of all tagged docs and closed tickets. It is committed to git so agents can query it without running the script.

```bash
make docs-registry   # Regenerate docs/REGISTRY.yaml
```

Each entry is either a `doc` entry or a `ticket` entry (with `artifact_files` listing investigation/plan/test_plan if they exist):

```yaml
- type: doc
  path: docs/mechanics/02_combat_laws.md
  title: Combat Laws
  status: authoritative
  layer: mechanics
  authority: P0
  ...

- type: ticket
  path: tickets/done/TCK-YYYYMMDD-FEATURE-NAME.md
  ticket_id: TCK-YYYYMMDD-FEATURE-NAME
  title: "Feature Name"
  date: "2026-06-06"
  artifact_files:
    - stored_artifacts/TCK-YYYYMMDD-FEATURE-NAME/investigation.md
    - stored_artifacts/TCK-YYYYMMDD-FEATURE-NAME/plan.md
    - stored_artifacts/TCK-YYYYMMDD-FEATURE-NAME/test_plan.md
  related_code_areas:
    - src/core/foo.py
```

Agents query the registry to find relevant docs without reading 500+ files. The `investigator` agent uses `related_code_areas` overlap to surface prior work; `mechanics-auditor` and `architecture-reviewer` use it to find P0 authoritative docs for a given layer.

### Artifact index pages

`stored_artifacts/*/index.md` landing pages are generated by `tools/generate_artifact_pages.py`. Each page groups the investigation, plan, and test_plan files for one ticket. `make docs-build`/`make docs-serve` still regenerate these files (via the `docs-artifacts` Makefile prerequisite), but since `TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD` removed the `artifacts` plugin-content-docs instance, they are no longer published as navigable pages on the Docusaurus site — they remain on disk under `stored_artifacts/` for direct browsing.

```bash
make docs-artifacts   # Regenerate stored_artifacts/*/index.md
```

---

## Authoritative Docs (P0)

These files are law — simulation behavior must match them exactly:

| Chapter | File | Covers |
|---|---|---|
| 01 | [mechanics/01_entity_anatomy.md](mechanics/01_entity_anatomy.md) | Core attributes, derived stats, biological pressures, XP scaling |
| 02 | [mechanics/02_combat_laws.md](mechanics/02_combat_laws.md) | Damage formula, tactical modifiers, durability decay |
| 03 | [mechanics/03_economic_laws.md](mechanics/03_economic_laws.md) | Atomic conservation, harvesting, trade, crafting |
| 04 | [mechanics/04_strategic_cognition.md](mechanics/04_strategic_cognition.md) | Goal hierarchy, interruption resistance, knowledge management |
| 05 | [mechanics/05_world_evolution.md](mechanics/05_world_evolution.md) | Tick-to-day time, regional trauma, ecology, calamities |
| 06 | [mechanics/06_worldbuilding_foundation.md](mechanics/06_worldbuilding_foundation.md) | Declarative topology, sovereignty, integrity validation |

Engine contracts: [engine/kernel.md](engine/kernel.md) · [engine/authoritative_pipeline.md](engine/authoritative_pipeline.md) · [engine/project_lawbook.md](engine/project_lawbook.md)

---

## Cognition Subsystem — `cognition/`

Entity self-knowledge layer. Covers: self-assessment, capability estimation, knowledge assimilation, and need interpretation.

| Doc | Contents |
|---|---|
| [cognition/README.md](cognition/README.md) | Subsystem overview, pipeline, relationship to strategy/domains/AI |
| [cognition/self_model_contract.md](cognition/self_model_contract.md) | Self-assessment thresholds, dirty check, SelfAwarenessComponent |
| [cognition/capability_and_knowledge_contract.md](cognition/capability_and_knowledge_contract.md) | Capability estimation formulas, knowledge model assimilation |
| [cognition/need_interpretation_contract.md](cognition/need_interpretation_contract.md) | Drive-to-need translation, urgency thresholds, trace events |

---

## AI Tooling

Claude Code subagents, workflows, and skills for the development and simulation lifecycle.

- [System Overview](ai/system_overview.md) — consolidated technical narrative of the full agent system
- [AI README](ai/README.md) — overview
- [Agents](ai/agents.md) — all subagents: roles, inputs, outputs
- [Workflows](ai/workflows.md) — multi-agent orchestration phases and return values
- [Skills](ai/skills.md) — slash commands for focused task patterns
- [Ticket Lifecycle](ai/ticket-lifecycle.md) — complete flow from request to closed ticket

---

## Developer Guides — `guides/`

Practical how-to guides for working with each major subsystem. These are starting points, not contracts — each links to the authoritative spec for full detail.

| Guide | What it covers |
|---|---|
| [guides/simulation.md](guides/simulation.md) | World authoring, CLI flags, run artifacts, determinism guarantee |
| [guides/observability.md](guides/observability.md) | Event bus, backpressure modes, decision traces, hard-law monitor |
| [guides/testing.md](guides/testing.md) | Test layout, markers, CI gates, P0 authority, regression triage |
| [guides/simulation_quality.md](guides/simulation_quality.md) | SimQ pillars, grades, REST API, feed modes, configuration |
| [guides/content_authoring.md](guides/content_authoring.md) | World modules, compositions, scenarios — quickstart, sharp edges, FAQ |
| [guides/bounded_cognition_tuning.md](guides/bounded_cognition_tuning.md) | Tuning AI cognition parameters, archetype defaults, troubleshooting |
| [guides/agent_monitoring.md](guides/agent_monitoring.md) | Agent retrospectives, monitoring queries, gate failure patterns |
| [guides/feature_flags.md](guides/feature_flags.md) | Feature flag defaults, rollout profiles, SimQ activation, and the DEV-002 default-OFF policy |
| [guides/agent_ops_dashboard.md](guides/agent_ops_dashboard.md) | Agent ops dashboard: build/serve, Gantt/Replay/Tickets views, API + design constraints |

---

## Verification

All documentation is verified against source code via `tests/docs/`. Run:

```bash
pytest tests/docs/ -v
```

If you find a discrepancy, mark it with `TODO:` in the code and update the doc. See [parity ledger](parity_ledger/) for machine-readable verification status per subsystem.
