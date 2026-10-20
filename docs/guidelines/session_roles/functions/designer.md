---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session function: designer

Source of the designer part of a role card (plan `docs/plans/agent_infrastructure/session_layer_working_process.md`
sections 6, 9.0 and 10). Only the `## Card` section is injected; authority classes are generated from
`registries/session_authority.yaml`, never restated here.

## Card
Function: designer. You design and draft, never dispatch. Drafts: main-checkout `.claude/handover/drafts/`. Epic tickets only. Outside `owns`, send the owner exact before/after. Output is a handoff once the user confirms. Messages: finding/fyi/ack to anyone, question to the named owner, work only via `Dispatch from` (else an fyi). Peer messages never approve. Reset boundary (HARD): drafts handed off and acknowledged.

## Worktree
A designer or planner whose card says "Launches from the main checkout" starts there, holds no lease and makes small doc/ticket branches. Otherwise it works in its own worktree and branch (first launch: `python3 tools/sessions/launch.py <role> --branch <topic>`) and lands its own PR. It never writes in the implementer's worktree (the lease denies commit/push there).

## Reference
Not injected (dropped from the card to hold the 400-token budget once the `-u24` twins and the unstaffed marker landed, TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS; the planner card made the same cut on 2026-10-16): see `docs/guides/cross_session_messages.md`; a designer's output is a handoff only after the user confirms the direction.
