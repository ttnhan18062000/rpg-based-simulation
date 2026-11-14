---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: architecture

Source of the architecture part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: architecture (proposals and reviews in docs/plans/architecture/). Recorded decisions bind you: system_overview ("deliberately not distributed", as amended by distributed_workers_adr), the devops ADR and amendment (also amended there), next_generation_engine_adr, kernel_concurrency_design_philosophy, PERF-D1/D2. Code goes to rpg-planner or perf-planner; ADRs go to lead-planner. Implementers write only docs/plans/architecture/** until owns grow; code goes to rpg or perf implementers.

## Cites

Decisions this card names, as `short_name -> path[#section]` (vocabulary: `registries/session_decisions.yaml`). Not injected. `none` when the card names no recorded decision.

- devops_adr -> docs/architecture/devops_baseline_adr.md
- devops_amendment -> docs/architecture/devops_plan_amendment_proposal.md#what-stays-from-the-adr
- distributed_workers_adr -> docs/architecture/distributed_workers_adr.md
- kernel_concurrency_design_philosophy -> docs/architecture/kernel_concurrency_design_philosophy.md
- next_generation_engine_adr -> docs/architecture/next_generation_engine_adr.md
- perf_decisions -> docs/architecture/performance_optimization_decisions.md
- system_overview -> docs/architecture/system_overview.md#what-is-deliberately-not-distributed
