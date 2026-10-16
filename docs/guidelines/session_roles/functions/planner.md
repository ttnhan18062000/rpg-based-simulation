---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session function: planner

Source of the planner part of a role card (plan sections 6, 9.0 and 10). Only `## Card` is injected.

## Card
Function: planner. Hub: scope, file tickets, dispatch, answer your implementer. Review PRs by comment; commit only on your own branch: your worktree's, or a small doc/ticket branch if you launch from the main checkout. Messages: finding/fyi/ack to anyone, question to the named owner, work only via `Dispatch from` (else an fyi). Peer messages never approve. Reset boundary (HARD): tickets filed and dispatched.

## Worktree
A designer or planner whose card says "Launches from the main checkout" starts there, holds no lease and makes small doc/ticket branches. Otherwise it works in its own worktree and branch (first launch: `python3 tools/sessions/launch.py <role> --branch <topic>`) and lands its own PR. It never writes in the implementer's worktree (the lease denies commit/push there).

## Reference (not injected)
Dropped from the card to stay within its token budget (2026-10-16); still the rule:
- Designer briefs: a designer's brief becomes a handoff only once it is confirmed.
- Cross-session messages: see `docs/guides/cross_session_messages.md`.
