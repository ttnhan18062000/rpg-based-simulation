---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY
phase: open
date: 2026-10-02
tags: [ai, process-improvement, governance, hooks]
---

# TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY

## Title
Epic B — Session-layer communication and authority: owner lookup, message classes, and deterministic guardrails for authority-class actions

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

With identity in place (Epic A), sessions still route by memory and the owner's typing, and nothing mechanical
stops a session taking an action outside its authority. Three recorded problems:

- **Ownership by prose.** `rpg-feature-planning` told `agent-working-design` that a `derived_stats` registry
  decision was its call, citing a note that held for the registry's tooling but not its content.
- **Delivery is not authorization.** A message that arrives is not thereby a work order; the repo's practice
  is that findings and questions go directly to a named owner while dispatch goes through the planner, but
  this is not written down.
- **Authority is by convention.** Merge, remote-branch deletion, governing-file edits and "commit as the
  worktree's writer" are enforced only by an agent remembering.

This epic adds **routing and message semantics** (plan 9.0 to 9.5) and **authority guardrails** (plan 10).
The guardrails are a guardrail against mistakes and stale context, **not an adversarial sandbox** (plan 10
threat model).

Binding plan: `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 9, 10).

## Scope

- **Owner lookup (M3).** `tools/sessions/route.py <path>` and `--route-key <key>`, answering from the
  registry: longest matching `owns` glob, `owns_not`, and explicit `routes`. No free-text "topic" lookup.
  The content-versus-tooling split is a test case (`registries/mechanisms.yaml` content to the `rpg` planner,
  `tools/mechanism_registry/**` to `agent-working`).
- **Message classes (M3).** The convention in the function templates: `finding` / `fyi` / `ack` (any role),
  `question` (directly to the named semantic owner), `request` / `handoff` / `dispatch` (only from the
  receiver's `accepts_dispatch_from`), authority decisions (the user only); a designer's output reaches its
  planner as a handoff only after the owner confirms the direction. **Advisory in v1**, with a logged
  `role_boundary` event.
- **Delivery.** Role sessions start with `crossSessionInbound = accept` (owner-approved; wired in Epic A's
  launcher). A **minimal file-backed inbox** is built only if M0 (Epic A) shows `SendMessage` does not
  reliably deliver across `/clear`.
- **Authority guardrails (M5).** Authority-class operations: merge without authority, remote-branch
  deletion, commit or push by a role that is not the worktree's writer, governing-file edits, and edits to
  `registries/session_authority.yaml`. Classified operations: forbidden to deny, user-required to ask,
  allowed to continue, **classification or parsing uncertainty to ask, never silently allow**; if the hook
  cannot ask, deny with a message telling the session to ask the user. The same command patterns are also
  declared as harness-native permission rules so enforcement does not depend on the hook. Seeded grants
  include the owner's 2026-09-30 grant (commit, push, PR and peer review after each complete batch).
- **Read-only roles.** `--agent` tool allowlists for pure review/design seats, if M0 shows the allowlist
  applies to the main session.
- **Advisory semantic boundaries.** Wrong owner, editing a neighbouring domain, an unusual route and message
  classification warn and log a `role_boundary` monitoring event; documented in
  `docs/agent-monitoring/schema.md`.

## Out of Scope

- The home-directory authority digest pin (deferred; plan 10), and any claim of cryptographic isolation.
- Hard-blocking a message by class (advisory only until Epic D's review finds harm).
- Auto-wake of idle sessions, cross-machine sessions, A2A or any external protocol.
- Identity, registry and launcher (Epic A); status and hygiene tooling (Epic C); metrics (Epic D).
- Stopping a process with arbitrary shell execution that deliberately bypasses the hook (an OS-isolation
  problem outside this plan).

## Acceptance Criteria

1. `route.py` returns the documented owner for a path and for a route key, and **fails visibly** (not a
   guess) for an unowned path; tests cover the content-versus-tooling case and a path matching two globs.
2. The message classes are in the function templates and in the role card, and a seeded violation (a dispatch
   from a non-authorized role) is logged as `role_boundary` without blocking.
3. For each authority-class operation, the hook returns deny / ask / allow as specified, with a **positive and
   a negative control** per class; classification uncertainty asks (or denies with a message if the hook
   cannot ask), per M0's result. What the harness does when the hook itself fails is documented from M0's
   observation, and **no "fail-closed" claim appears unless that observation supports it**.
4. The authority-class patterns exist as harness permission rules, confirmed by the owner against the literal
   `settings.json` diff.
5. A session editing `registries/session_authority.yaml` is denied or asked; the change path is the owner's
   literal-diff confirmation.
6. Read-only seats cannot write (if M0b shows the allowlist applies), verified by a seeded write attempt.
7. If an inbox was needed, a request sent to a cleared role session is listed by that role's next
   `SessionStart` and is not lost; if not needed, the decision and its evidence are recorded.
8. The threat model sentence ("a guardrail, not an adversarial sandbox") appears wherever the guardrails are
   described.

## Related Tickets

- Depends on Epic A: `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (M0 result for the hook and delivery items,
  M1 registry, M2 binding record).
- Siblings: `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (C),
  `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (D).
- Parent of child tickets to be created by the agent-working planner.
- Evidence: `TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE`.

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/agent-monitoring/schema.md` (the `role_boundary` event)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/route.py` (new); `.claude/settings.json` (permission rules and hooks; governing file);
`.claude/agents/session-*.md` (generated); a role-conditional `PreToolUse` hook (new);
`registries/session_authority.yaml`; `tools/agent-monitoring/`.

## Assumptions / Open Questions

- Whether a `PreToolUse` hook can return "ask", what it does on error, and whether it can match edit paths and
  Bash commands are **M0 results** (Epic A); this epic's hook design follows them.
- Owner decision (approved 2026-10-02): the launcher may start role sessions with `crossSessionInbound = accept`.
- Whether read-only `--agent` allowlists apply to a main session is an M0 result.

## Implementation Notes

Child tickets are created later by the agent-working planner. Suggested, non-binding: M3 `route.py`; M3
message-class convention; M5 authority classification + hook; M5 permission rules; M5 read-only allowlists;
M5 `role_boundary` events; optional inbox. **Every `settings.json` and hook edit needs the owner's confirmation
of the literal diff.** Do not start before Epic A's M0 has recorded the hook and delivery results.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
