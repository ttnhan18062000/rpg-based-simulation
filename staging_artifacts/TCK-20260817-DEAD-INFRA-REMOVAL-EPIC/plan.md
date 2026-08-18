---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
artifact_type: plan
tags: [architecture]
---

# Plan — TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

Scope-only epic (per Tier Routing: "epic | Scope only — no direct implementation"). Plan is the
ticket file plus `docs/plans/dead_infra_removal_epic.md` — no code change, no `create-tickets`
run yet. When this epic is chosen for action, write a fresh proposal document scoped to its
items only and run `create-tickets` against it, producing investigated child tickets in
`tickets/todos/dead-infra-removal/`.

**Downgraded from epic to standard tier (2026-08-18):** see the ticket's Assumptions/Open
Questions section for rationale. No `create-tickets` pass needed — the ticket's own Scope now
carries concrete, directly-actionable items. Ticket file moved to `tickets/todos/TCK-*.md`
(flat, no subfolder) since standard tier tickets in this project don't carry a per-ticket
todos subfolder the way epic tier does.
