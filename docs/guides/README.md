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

The following guides live in their subsystem folders but are user-facing how-tos:

| Guide | Location | What it covers |
|---|---|---|
| Content Authoring Guide | [`docs/content/authoring_guide.md`](../content/authoring_guide.md) | World modules, compositions, simulation scenarios — quickstart, field reference, sharp edges, FAQ |
| Bounded Cognition Tuning | [`docs/strategy/bounded_cognition_tuning_guide.md`](../strategy/bounded_cognition_tuning_guide.md) | Tuning INT/WIS parameters, cognitive archetypes, troubleshooting AI behavior |
| Agent Monitoring Retro | [`docs/agent-monitoring/retro-guide.md`](../agent-monitoring/retro-guide.md) | Running agent retrospectives, querying monitoring data, interpreting gate failures |

For system architecture, see `docs/engine/` and `docs/architecture/`.
For simulation laws, see `docs/mechanics/`.
For parity and compliance tracking, see `docs/parity_ledger/` and `docs/compliance/`.
