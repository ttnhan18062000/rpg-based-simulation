---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
artifact_type: plan
tags: [ai]
---

# Plan — TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC

Scope-only epic. Plan is the ticket file plus `docs/plans/epic_staleness_status_aware_epic.md` —
no code change, no `create-tickets` run yet. When this epic is chosen for action, write a fresh
proposal document scoped to its item only and run `create-tickets` against it, producing
investigated child tickets in `tickets/todos/epic-staleness-status-aware/`.

**Downgraded from epic to hotfix tier (2026-08-18):** see the ticket's Assumptions/Open Questions
section for rationale. No `create-tickets` pass needed. Ticket file moved to
`tickets/todos/TCK-*.md` (flat, no subfolder) since hotfix tier never carried staging
artifacts requirements to begin with, and standard/hotfix tier tickets in this project don't
carry a per-ticket todos subfolder the way epic tier does.
