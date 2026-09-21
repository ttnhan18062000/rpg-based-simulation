---
status: active
layer: architecture
authority: P2
audience: developer
tags: [planning, tracking, documentation]
---

# Plans Tracking — Quick Overview

Date: 2026-09-13 (updated: added 2 previously-missing render-and-art sibling packages; archived 2 fully-shipped roadmaps — see Maintenance note; rest of the table is unchanged from the 2026-09-09 snapshot)

## Scope

This is a lightweight inventory of plan intent and declared lifecycle status. It does not validate
technical correctness, feasibility, implementation progress, or the proposed approach. Status and
authority come from document frontmatter; brainstorm sources are listed only when a plan explicitly
references `docs/brainstorm/`.

`docs/plans/archive/` is excluded. Multi-file plan packages are collapsed into one program row, so
milestone and supporting files are not repeated individually. This snapshot summarizes 97 Markdown
files as 37 plan records; `plans_tracking.md` excludes itself.

### Status key

| Status | Meaning used here |
|---|---|
| `active` | The document declares `status: active`; this index does not assert implementation progress. |
| `idea` | The document declares exploratory idea status. |
| `historical` | The document declares historical status even though it remains outside the archive folder. |

## Plan inventory

| Plan or program | Very short description | Declared status | Authority | Explicit brainstorm source | Files collapsed |
|---|---|---|---|---|---:|
| [AI-first engineering hardening program](agent_infrastructure/ai_first_hardening_epics/roadmap.md) | Hardens agent workflows, governance, guardrails, review independence, telemetry, and evaluation. | `active` | `P0 roadmap; P1/P2 children` | [ai_first_architecture_maturity_review.html](../brainstorm/agent-working-design/ai_first_architecture_maturity_review.html)<br>[ai_first_engineering_next_evolution_proposal.html](../brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html) | 9 |
| [Idea: Context-Efficient Agent Retrieval and Observability](agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md) | Explores Context-Efficient Agent Retrieval and Observability. | `active` | `P2` | — | 1 |
| [Plan: Headroom Context-Compression Bounded Trial](agent_infrastructure/headroom_context_compression_trial.md) | Concluded 2026-09-21: Phase 1 (MCP mode) shipped, Phase 2 (proxy rollout) abandoned on measured evidence; MCP registration kept on `main`. | `historical` | `P2` | — | 1 |
| [Idea: Distinguish Active Work Time from Idle/Session-Pause Gaps in Agent Monitoring Duration](agent_infrastructure/idea_agent_monitoring_active_duration.md) | Explores Distinguish Active Work Time from Idle/Session-Pause Gaps in Agent Monitoring Duration. | `idea` | `P2` | — | 1 |
| [Implementation Plan: Provider-Agnostic Agent Orchestration](agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md) | Implementation plan for Provider-Agnostic Agent Orchestration. | `historical` | `P1` | — | 1 |
| [Aseprite Agent-Controlled Pixel-Art — Draft Milestone Plan Package](aseprite-mcp-pixel-art/README.md) | Draft milestone plan for agent-controlled Aseprite pixel-art drawing (CAP-A/CAP-B), gated behind authority/preflight contracts; execution remains NO-GO pending separate authorization. | `active` | `P1` | [aseprite_mcp_pixel_art_workflow_proposal.md](../brainstorm/render-and-art/aseprite_mcp_pixel_art_workflow_proposal.md) | 8 |
| [Audit Fix Plan — Remaining Open Issues](audit_fix_plan.md) | Audit Fix Plan — Remaining Open Issues. | `active` | `P1` | — | 1 |
| [Design Enhancement Roadmap — Performance-First, With Scoped Non-Performance Additions](design_enhancement/design_enhancement_roadmap.md) | Design Enhancement Roadmap — Performance-First, With Scoped Non-Performance Additions. | `active` | `P1` | [performance_evolution_roadmap.html](../brainstorm/performance_evolution_roadmap.html)<br>[simulation_design_taxonomy.html](../brainstorm/simulation_design_taxonomy.html) | 1 |
| [Epic Plan — Determinism Envelope for Wall-Clock-Driven Mode Escalation](design_enhancement/determinism_envelope_epic.md) | Delivery program for Determinism Envelope for Wall-Clock-Driven Mode Escalation. | `active` | `P1` | — | 1 |
| [Epic Plan — Performance Evolution, Sequenced by Risk](design_enhancement/performance_milestones_epic.md) | Delivery program for Performance Evolution, Sequenced by Risk. | `active` | `P1` | [performance_evolution_roadmap.html](../brainstorm/performance_evolution_roadmap.html) | 1 |
| [Performance optimization design enhancement](design_enhancement/performance_optimization/performance_optimization_roadmap.md) | Plans evidence-gated performance contracts, assurance, baselines, exact optimizations, and Gate A/B decisions. | `active` | `P2` | [performance_optimization_architecture_proposal.md](../brainstorm/codex/system-design/performance_optimization_architecture_proposal.md) | 11 |
| [Epic Plan — Per-Sub-Phase Domain/Dependency Contracts for the 37 Resolution Phases](design_enhancement/subphase_domain_contracts_epic.md) | Delivery program for Per-Sub-Phase Domain/Dependency Contracts for the 37 Resolution Phases. | `active` | `P1` | — | 1 |
| [Engine Future Epics — Full Gap Analysis & Long-Term Roadmap](engine_future_epics_roadmap.md) | Engine Future Epics — Full Gap Analysis & Long-Term Roadmap; **its Headline Finding is stale, see note below**. | `active` | `P1` | — | 1 |
| [Roadmap — HUD: Thin Foundation, Vertical Slice, Then Extraction](hud_delivery_roadmap.md) | Roadmap for HUD: Thin Foundation, Vertical Slice, Then Extraction. | `active` | `P1` | — | 1 |
| [Epic Plan — HUD Design System Foundation](hud_design_system_foundation_epic.md) | Delivery program for HUD Design System Foundation. | `active` | `P1` | — | 1 |
| [Idea: Cognition Graph as a First-Class Analytics Object](idea_cognition_graph_analytics_pipeline.md) | Explores Cognition Graph as a First-Class Analytics Object. | `idea` | `P2` | — | 1 |
| [Idea: Embeddings & Latent Space for Entity Cognition](idea_embedding_latent_cognition.md) | Explores Embeddings & Latent Space for Entity Cognition. | `idea` | `P2` | — | 1 |
| [Idea: Frontend Canvas Render Tiers — Shared Pipeline, Not Three Separate Renderers](idea_frontend_canvas_render_tiers.md) | Explores Frontend Canvas Render Tiers — Shared Pipeline, Not Three Separate Renderers. | `active` | `P2` | — | 1 |
| [Idea: Redesign the Frontend's Data-Visualization Palette — a New Baseline, Not a Consolidation of the Old One](idea_hud_color_asset_system.md) | Explores Redesign the Frontend's Data-Visualization Palette — a New Baseline, Not a Consolidation of the Old… | `active` | `P2` | — | 1 |
| [Idea: A Motion/Transition Token System — a Real Gap, Corrected From an Earlier Overstatement](idea_hud_motion_transition_system.md) | Explores A Motion/Transition Token System — a Real Gap, Corrected From an Earlier Overstatement. | `active` | `P2` | — | 1 |
| [Idea: HUD Quality Measurement — A Third Sibling to SimQ and Visual-Quality Validation](idea_hud_quality_measurement.md) | Explores HUD Quality Measurement — A Third Sibling to SimQ and Visual-Quality Validation. | `active` | `P2` | — | 1 |
| [Idea: Intention Log as First-Class Runtime Object](idea_intention_log_first_class.md) | Explores Intention Log as First-Class Runtime Object. | `idea` | `P2` | — | 1 |
| [Idea: Pressure Propagation Between Regions](idea_pressure_propagation_economy.md) | Explores Pressure Propagation Between Regions. | `idea` | `P2` | — | 1 |
| [Idea: Semantic Entity Index for World Queries](idea_semantic_entity_index.md) | Explores Semantic Entity Index for World Queries. | `idea` | `P2` | — | 1 |
| [Idea: World Grammar with Semantic Constraints](idea_world_grammar_semantic_constraints.md) | Explores World Grammar with Semantic Constraints. | `idea` | `P2` | — | 1 |
| [Proposal: Kernel Concurrency Design Review — Findings & Follow-Ups](kernel_concurrency_design_review_proposal.md) | Proposes Kernel Concurrency Design Review — Findings & Follow-Ups. | `active` | `P2` | — | 1 |
| [Proposal: Local Knowledge Gateway MCP](knowledge-gateway-mcp-proposal.md) | Proposes Local Knowledge Gateway MCP. | `active` | `P1` | — | 1 |
| [Epic Plan — Reconnect the Existing Player-Facing Live Map to the Real V2 Backend](live_map_reconnection_epic.md) | Delivery program for Reconnect the Existing Player-Facing Live Map to the Real V2 Backend. | `historical` | `P1` | — | 1 |
| [Roadmap — Live Map: Reconnection, Then Evidence-Driven Scaling](live_map_scaling_roadmap.md) | Roadmap for Live Map: Reconnection, Then Evidence-Driven Scaling. | `active` | `P1` | — | 1 |
| [Roadmap — Live Map Rendering and Surface Integration](live_map_rendering_and_surface_integration_milestone_plan.md) | Coordinates renderer evidence, independent Live Map/HUD readiness, directional integration, browser adoption gates, conditional native validation, and [detailed work packages](render-and-art/README.md). | `active` | `P1` | [renderer architecture](../brainstorm/render-and-art/live_map_rendering_engine_architecture_proposal.md)<br>[surface-integration architecture](../brainstorm/render-and-art/live_map_hud_surface_integration_architecture.md) | 10 |
| [Engine Long-Term Development Roadmap](long_term_development_roadmap.md) | Engine Long-Term Development Roadmap. | `active` | `P1` | — | 1 |
| [Roadmap — Full Delivery of the Three Rendering and Art Epics](render_and_art_program_roadmap.md) | Cross-epic coordinator tying together Live Map/HUD, Aseprite CAP-A/CAP-B, and visual asset management — conditional dependency graph, gate IDs, and cross-plan wiring; does not replace the three owner packages. Copy of `docs/brainstorm/render-and-art/three_epic_full_delivery_roadmap.md`, added 2026-09-13 for parity with how `performance_optimization_roadmap.md` is placed. | `active` | `P1` | [three_epic_full_delivery_roadmap.md](../brainstorm/render-and-art/three_epic_full_delivery_roadmap.md) | 1 |
| [RPG design roadmap program](rpg_design_roadmap/rpg_design_roadmap.md) | Sequences RPG mechanics, world, social, memory, SimQ, generation, and corpus-test milestones. | `active` | `P1` | [2026-09-02-core-rpg-knowledge-belief-axis-proposal.md](../brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md)<br>[2026-09-02-core-rpg-social-relationship-axis-proposal.md](../brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md)<br>+12 explicit | 16 |
| [Epic Plan — Scripts & Tools Governance](scripts_tools_governance_epic.md) | Delivery program for Scripts & Tools Governance. | `active` | `P1` | — | 1 |
| [Visual Asset Management and Runtime Integration — Draft Milestone Plan Package](visual-asset-management-runtime-integration/README.md) | Draft milestone plan for candidate intake, quarantine/adoption, immutable source/artifact/release records, and semantic runtime resolution feeding Live Map/HUD. | `active` | `P1` | [asset_management_and_runtime_integration_proposal.md](../brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md) | 10 |
| [Epic Plan — Seed-Varied, Organic World-Generation Terrain](world_generation_organic_terrain_epic.md) | Delivery program for Seed-Varied, Organic World-Generation Terrain. | `active` | `P1` | — | 1 |
| [World rendering core and validation](world_rendering_core_epic.md) | Plans a server-owned rendering core with visual and geometric validation. | `active program; idea/historical support` | `P1 program; P2 support` | — | 3 |

## Maintenance note

Update this table when a plan is added, archived, grouped into a program, or changes declared status.
Do not infer completion from ticket state here; use the plan frontmatter and its own tracking surfaces.

**2026-09-13 archival pass:** `architecture_resilience_remediation_roadmap.md` and
`http_admission_control_epic.md` were confirmed fully shipped (all tracked epics/tickets in
`tickets/done/`) and moved to `docs/plans/archive/` with `status: historical`, `maturity: shipped`;
both are removed from this table per the exclusion rule above.

**Known-stale item not yet fixed:** `engine_future_epics_roadmap.md`'s "Headline Finding" (no
faction/diplomacy/war system exists) is contradicted by shipped `TCK-20260619-E53-FACTION-DIPLOMACY`
and the registered `grand-strategy` tag — flagged inline in that document, not yet corrected in the
document body itself.

**Needs a full audit, not yet done:** `long_term_development_roadmap.md` (dated 2026-06-19) has at
least one confirmed-shipped item (§5.3 Faction & Diplomacy) and no per-item status tracking; given
this repo's ticket velocity it is plausibly 50%+ stale relative to the newer, actively-worked
`rpg_design_roadmap/` (M1-M9) program. Needs an item-by-item pass against `tickets/done/` before
being trusted for prioritization — recommend filing a ticket for this rather than assuming.

**Roadmap authority (no single index existed before this note):** for architecture/engine-scale
work, `docs/plans/architecture_resilience_remediation_roadmap.md` governed D23/D24 audit findings
(now archived, fully shipped); `docs/plans/design_enhancement/design_enhancement_roadmap.md` +
its `performance_optimization/` child package govern performance work (the child package is a
draft under review, not yet authoritative); `docs/plans/engine_future_epics_roadmap.md` and
`docs/plans/long_term_development_roadmap.md` are general gap-analysis roadmaps of uncertain
current accuracy (see notes above) — for RPG-mechanics work specifically, prefer the actively
maintained `rpg_design_roadmap/` (M1-M9) program over either. For render/art/HUD work,
`docs/plans/render_and_art_program_roadmap.md` governs cross-epic sequencing across the three
draft packages (`render-and-art/`, `aseprite-mcp-pixel-art/`, `visual-asset-management-runtime-
integration/`); like the performance package, it is a draft under review, not yet authoritative.
