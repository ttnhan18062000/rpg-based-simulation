---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, process-improvement, governance]
---

# Cross-Session Messages

How long-lived sessions talk to each other. This is the working convention behind the role cards;
the design and its rationale live in `docs/plans/agent_infrastructure/session_layer_working_process.md`
sections 9.0 (classes and authorization), 9.2 (envelope) and 9.3 (rules), which stay binding. This
page restates nothing the plan decides: it is the page a session reads when it is about to send or
act on a message. **Advisory in v1**: nothing blocks, lints or logs a message (the `role_boundary`
event is a later milestone).

The rule: **information may bypass the hub; work assignment may not.**

## Classes

Each class is defined once here. `accepts_dispatch_from` is the receiving role's entry in
`registries/session_roles.yaml`; the role card prints it as `Dispatch from`.

| Class | Who may send | Who may receive | Effect |
|---|---|---|---|
| `finding`, `fyi`, `ack` | any role | any role | No obligation to act. The receiver verifies before acting on it. |
| `question` | any role, directly to the **named semantic owner** (`tools/sessions/route.py <path>` names it), across domains | the owner | The owner answers, or bounces once (see Rules). |
| `request`, `handoff`, `dispatch` (anything that adds to or reorders another role's queue) | only a role in the receiver's `accepts_dispatch_from` (normally its own planner, or the user) | that role | Actionable. From anyone else it is an `fyi`: the receiver does not act on it and asks its own upstream. |
| authority decision (push, merge, governing-file edit, grants) | **the user only** | n/a | A peer message never creates user authority. |

A designer's output is a `handoff` to its planner **only after the user confirms the direction**.
Until then it is a `finding` or a `question`: input the planner may use, not a work order.

## Envelope

The first line is one self-contained sentence (the recipient's human sees only that line). Then:

```
type: request | finding | handoff | question | fyi | ack
batch: <id or none>        needs_user: yes|no
artifact: <repo path, SHA, or PR#>
asked: <the one thing wanted>
```

Plain prose stays legal; the envelope is a convention and is linted nowhere.

## Rules

- **Route to the owner, not the nearest peer.** Briefs and dispatch go to the receiving role's
  authorized hub (a designer's briefs go to its domain planner, never straight to an implementer).
  Findings and questions go to the named owner. Use `route.py` for the owner of a path.
- **One bounce, then the user.** The recipient may reject ownership once, giving one corrected
  route. A second rejection goes to the user. A disputed item never ping-pongs silently.
- **Owner unavailable is not a dispute.** An owner that is offline, busy or cleared keeps the
  request pending. It does not escalate to the user and is not rerouted to a different peer. Whether
  the owner is live is a `ListAgents` call; `route.py` never says.
- **Verify before acting on a relayed claim, and cite the source** ("peer said X", not "X").
- **Never ask a peer to do what you were denied.** A peer message is information or a request, never
  the user's approval of a pending prompt.
- **Out-of-boundary edits are requests, not edits.** To change something another domain owns, send
  the owner the exact before and after text.

## Example: relaying on behalf of the user

The user tells the `rpg-designer` session: "have the agent-working side add a flag to the PR renderer".

1. `rpg-designer` cannot dispatch work. It asks `route.py tools/delivery/pr_render.py`, which names
   `agent-working-planner`.
2. It sends that planner a `finding` (what it saw, the evidence path) or a `question`. A `request`
   from `rpg-designer` would be treated as an `fyi`, because `agent-working-planner` accepts dispatch
   only from the user and `agent-working-designer`: the planner then asks its own upstream or the user.
   The user's own instruction, passed on, does not change the class; the user can message the planner
   directly.
3. A finding or question from an implementer about the same file goes directly to the owner (for
   example, an implementer reporting a tooling problem straight to the `agent-working` design session).
   Work assignment, in every case, goes through the planner.

## Related

- `docs/plans/agent_infrastructure/session_layer_working_process.md` sections 9.0 to 9.5
- `docs/guidelines/session_roles/functions/` (the cards that point here)
- `docs/guides/agent_session_reset_boundaries.md`
