---
title: Developer Guides
layer: misc
authority: P1
audience: developer
---

# Developer Guides

Practical how-to guides for working with each major subsystem. These are starting points — each guide links to the authoritative contract or spec for full details.

| Guide | What it covers |
|---|---|
| [simulation.md](simulation.md) | Authoring worlds, running simulations, reading artifacts |
| [observability.md](observability.md) | Event bus, EventRecorder, decision traces, hard-law monitor, Prometheus |
| [testing.md](testing.md) | Writing tests, test markers, CI gates, regression triage |
| [simulation_quality.md](simulation_quality.md) | SimQ scoring pillars, grades, REST API, feed modes, configuration |
| [content_authoring.md](content_authoring.md) | World modules, compositions, simulation scenarios — quickstart, field reference, sharp edges, FAQ |
| [bounded_cognition_tuning.md](bounded_cognition_tuning.md) | Tuning INT/WIS parameters, cognitive archetypes, troubleshooting AI behavior |
| [agent_monitoring.md](agent_monitoring.md) | Agent retrospectives, querying monitoring data, interpreting gate failures |
| [ticket_tagging.md](ticket_tagging.md) | Tag categories, canonical examples, which tags trigger a skill suggestion, and how tags filter REGISTRY.yaml prior-work search |
| [ticket_reporting.md](ticket_reporting.md) | Reporting over the ticket corpus itself, organized as pillars — tag-usage reporting (`tools/tag_report.py`) is Pillar 1 |
| [diagram_index.md](diagram_index.md) | Every diagram in the repo, grouped by domain, linking to where it actually lives |

For system architecture, see `docs/engine/` and `docs/architecture/`.
For simulation laws, see `docs/mechanics/`.
For parity and compliance tracking, see `docs/parity_ledger/` and `docs/compliance/`.
