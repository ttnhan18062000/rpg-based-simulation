---
status: active
layer: guidelines
authority: P2
audience: developer
tags: [diagrams, documentation, guide]
---

# Diagram Index

Every diagram in this repo stays co-located with the doc that explains it — this index only
**links** to them, it doesn't relocate anything. Keeping a diagram next to its prose means a reader
never has to jump between two files to follow one concept, and it keeps `search_docs`' semantic
chunking from splitting a diagram from the explanation of what it means.

If you're building a new diagram for a doc not listed here, add a row when you're done — this list
is only as good as it stays current, and there's no automated check keeping it in sync with the
corpus (deliberately: the diagram count is small enough today that automation would be
premature — see `stored_artifacts/TCK-20260706-DIAGRAM-COVERAGE/plan.md`).

## Engine & Simulation

| Doc | Diagram | Covers |
|---|---|---|
| [`docs/engine/architecture.md`](../engine/architecture.md) | Mermaid | Engine architecture |
| [`docs/engine/contracts/infrastructure_overview.md`](../engine/contracts/infrastructure_overview.md) | Mermaid | Component map — full ecosystem structural directory |

## Observability & Simulation Quality

| Doc | Diagram | Covers |
|---|---|---|
| [`docs/architecture/observability_behavior_profiling_boundary.md`](../architecture/observability_behavior_profiling_boundary.md) | Mermaid `graph TD` | Observability/behavior-profiling pipeline boundary |
| [`docs/guides/simulation_quality.md`](simulation_quality.md) | Mermaid `flowchart LR` | SimQ data flow: engine event bus → feed mode (in-process/broker) → `QualityHub` → 10 pillar scorers → grades → REST API/`QualityReport` |

## Cognition & Strategy

| Doc | Diagram | Covers |
|---|---|---|
| [`docs/strategy/bounded_cognition_decision_flow.md`](../strategy/bounded_cognition_decision_flow.md) | Mermaid | Bounded-cognition decision flow |

## Entities

| Doc | Diagram | Covers |
|---|---|---|
| [`docs/entity/entity_aspect_relationship_diagram.mmd`](../entity/entity_aspect_relationship_diagram.mmd) | Standalone `.mmd` | Entity/aspect relationship model |

## Agent Process

| Doc | Diagram | Covers |
|---|---|---|
| [`docs/ai/ticket-lifecycle.md`](../ai/ticket-lifecycle.md) | Mermaid `flowchart TD` | `implement-ticket`'s full phase/agent/gate pipeline, tier-routing skips, and every gate-branch return status |

## Related docs

- [`docs/guides/ticket_reporting.md`](ticket_reporting.md) — a sibling "index of reporting angles over the ticket corpus," same organizing instinct applied to a different kind of artifact
- `stored_artifacts/TCK-20260706-DIAGRAM-COVERAGE/investigation.md` — the corpus scan this index was built from, plus the reasoning for indexing in place rather than relocating diagrams into a `docs/diagrams/` folder
