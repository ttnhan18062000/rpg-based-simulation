---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC

Scope-only epic (per Tier Routing: "epic | Scope only — no direct implementation"). The full
design already exists and is merged to `main`
(`docs/plans/simulation_semantic_control_plane/{README,architecture,agent_operating_model,
rollout_plan,roadmap}.md`, PR #223, commit `a4333bcef`). This epic's own job is milestone-by-
milestone child-ticket creation, not design work.

This pass ran `create-tickets` against `roadmap.md`'s M0 section only (scoped via a targeted
Comprehend-phase instruction, since M0 is the only milestone gated on nothing) and produced one
child ticket, `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`
(`tickets/todos/semantic-control-plane-m0/`), covering all three M0 schemas, the shared validator,
its broken-fixture proof, and the `architecture.md` §3 doc-sync — merged into one ticket per every
investigating agent's independent recommendation (they cannot be built or scheduled separately).

M1 (Territory/Control) is gated on M0 and is explicitly NOT created by this pass. M2 (drift
detection) is gated on M1. M3 (existing-finding ingestion) is a permanent stream with no bounded
gate. M4 (second slice) is gated on M1/M2/M3's Territory+Combat-scoped triage. Each of these gets
its own `create-tickets` run once its own gate is satisfied — this plan does not pre-plan them.
