---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: platform

Source of the platform part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: platform (deployment and runtime: compose, images, CI/CD for images, Kubernetes/Helm, Terraform, observability stack, runbooks). The engine runs as one process by default; the opt-in distributed-workers mode follows docs/architecture/distributed_workers_adr.md; src/** changes go to rpg-planner; ADR changes go to lead-planner for review.

## Cites

Decisions this card names, as `short_name -> path[#section]` (vocabulary: `registries/session_decisions.yaml`). Not injected. `none` when the card names no recorded decision.

- distributed_workers_adr -> docs/architecture/distributed_workers_adr.md
