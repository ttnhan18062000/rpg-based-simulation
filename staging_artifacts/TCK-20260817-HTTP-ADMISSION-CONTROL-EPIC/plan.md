---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
artifact_type: plan
tags: [architecture]
---

# Plan — TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC

Scope-only epic. Plan is the ticket file plus `docs/plans/http_admission_control_epic.md` — no
code change, no `create-tickets` run yet. When this epic is chosen for action (gated on
deployment plans), write a fresh proposal document scoped to its items only and run
`create-tickets` against it, producing investigated child tickets in
`tickets/todos/http-admission-control/`.

**Downgraded from epic to standard tier (2026-08-18):** see the ticket's Assumptions/Open
Questions section for rationale. No `create-tickets` pass needed — the ticket's own Scope now
carries concrete, directly-actionable items. Ticket file moved to `tickets/todos/TCK-*.md`
(flat, no subfolder) since standard tier tickets in this project don't carry a per-ticket
todos subfolder the way epic tier does.
