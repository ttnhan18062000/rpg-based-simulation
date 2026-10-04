---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION
phase: open
date: 2026-10-02
tags: [ai, process-improvement, governance]
---

# TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION

## Title
Epic A — Session-layer foundation: verified harness facts, a repo-versioned role registry, and a launcher that starts, resumes and recovers a session by role id

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Several long-lived interactive Claude Code sessions cooperate on this repo and the owner hand-orchestrates
them: telling each who it is, what it may touch, which worktree to use, when to `/clear`. Recent incidents
show the cost (all in the binding plan, section 1):

- role knowledge lives in about seven per-machine memory files, handover notes and typed prompts, with no
  single versioned source; a stale ownership note caused a misroute on 2026-10-02;
- `session_start_handover_hook.py` lists every handover note and says "read the one matching your role",
  but nothing tells a session which role it is;
- `/clear` allocates a new session id with no link to the old one (verified 2026-09-27), so a session
  killed unexpectedly cannot be found by id;
- the volume reached 100% and blocked a push (worktree and branch sprawl).

This epic builds the **identity layer** the rest of the session layer sits on: it verifies the harness
facts the design depends on (M0), defines the roles as configuration (M1), and makes launch, resume and
recovery work from the role id alone (M2). The model is three functions (designer, planner/reviewer,
implementer), a full set of three seats per domain, the **role id as the permanent identity**, and sessions
as disposable instances that hold a seat.

Binding plan: `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 2 to 6.1,
12.1, 12.2). Owner decisions are recorded in its section 12.3 (2026-10-02).

## Scope

- **M0 — harness spike (first, gates the rest).** One investigation record with a **positive-controlled
  local result for every item a to r** in plan 12.1: name, `/clear`, resume, rename, fork and duplicate-name
  behaviour; `agent_type` / `SESSION_ROLE` / `session_title` / `session_id` stability (the
  signal-precedence table); `--agent` applied to the main session and its effect on the subagent roster;
  what a `PreToolUse` hook can return (deny / ask / allow) and what the harness does on a classification
  failure or hook error; inbound `accept` / `hold` / `refuse` behaviour by permission-mode pair and the
  5-minute dialog expiry; idle-session wake; prompt-submit payload; transcript and title persistence,
  `--resume` from another cwd, liveness detection, and the crash cases in plan 6.1. Where documentation
  and a local observation disagree, the local behaviour is recorded and the plan is updated from it.
  Outcome: a go / adjust decision on plan sections 5, 9.5 and 10.
- **M1 — registry and validator.** `registries/session_roles.yaml` and `registries/session_authority.yaml`
  (the latter a governing-file class), the three function templates and one domain overlay per domain
  (`rpg`, `agent-working`, `testing`), generated `.claude/agents/session-<role>.md` files, and a validator.
  The nine seats are recorded, including the two unstaffed ones (`agent-working-planner`,
  `testing-designer`). The ~7 role-defining memory files are reduced to pointers.
- **M2 — launcher, binding, recovery.** `tools/sessions/launch.py` and the `cc <role>` alias; role
  resolution from harness signals at `SessionStart`; the binding record and the role-state directory under
  the git common directory; card injection and **own-handover-only** injection (replacing today's list of
  every note); the writer lease; the orphan recovery flow (resume / replace / inspect, never silent); worktree
  self-heal from the role's branch; start of role sessions with `--settings
  '{"crossSessionInbound":"accept"}'` (owner-approved 2026-10-02).

## Out of Scope

- Routing, the message classes and any authority guardrail (Epic B).
- Worktree and branch hygiene tooling, `status.py`, disk warnings (Epic C).
- Metrics, roster-check analytics, the first-month review (Epic D).
- Staffing the two unstaffed seats and the practice changes in plan section 3 (owner decisions).
- Auto-wake and a message inbox (Epic B decides the inbox from M0's wake result).
- Any change to `.claude/agents/` agent roles, `agent-orchestration/`, or `Workflow` scripts.
- The home-directory authority digest pin (deferred by plan section 10).

## Acceptance Criteria

1. **M0 record.** Every item a to r has a recorded local result with a positive control and the exact
   Claude Code version; the signal-precedence table exists; each disagreement with the official docs is
   listed; the go / adjust decision is written down.
2. **Registry.** The validator passes on the real registry and fails on a seeded defect for each rule:
   an `owns` glob that resolves to nothing, two roles owning one path without a stated split, a missing
   handover, a `routes` target that is not a role, a worktree with no or two writers, and a generated agent
   file that no longer matches the manifest. It *reports* per-role complexity (overrides, unique routes,
   authority exceptions). The nine seats are present; unstaffed seats are explicit.
3. **Launch.** `cc <role>` starts a session named by the role id, in the role's worktree, with the role card
   and only its own handover, and **no typed instructions**. A second launch against a live instance is
   refused. Role resolution uses the harness signals; disagreeing signals inject nothing privileged. A plain
   `claude` injects nothing and says how to launch with a role. The existing `/clear` handover behaviour does
   not regress.
4. **Recovery.** After a killed instance, `cc <role>` detects the orphan and shows last activity,
   worktree, branch, dirty and unpushed state, any git operation left in progress, the PR, the handover's
   age and the candidate transcripts, then offers resume / replace / inspect. It never starts or resumes
   silently, and never deletes an old transcript. A removed worktree is recreated from the role's branch.
   Tested on the crash cases M0 found reproducible; the others are listed as not covered.
5. **Writer lease.** Exactly one lease per worktree; a dead holder's lease is reported stale and is retaken
   only by the same role or by the owner, never silently stolen.
6. **Governing files.** Every `settings.json` / hook change is confirmed by the owner against the literal
   diff before it lands.

## Related Tickets

- Sibling epics: `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (B),
  `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (C), `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (D).
- Parent of child tickets to be created by the agent-working planner (see Implementation Notes).
- Evidence and prior art: `TCK-20260921-SESSION-CONTEXT-RESET-TRIAL` (the handover hook),
  `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (the per-session sidecar),
  `TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE` (the content-versus-tooling split).

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/plans/agent_infrastructure/agent_working_direction.md`
- `docs/guides/agent_session_reset_boundaries.md`
- `docs/guides/delivery_process.md` ("Worktree & Branch Isolation")
- `agent-orchestration/README.md` (reference only: agent roles are referenced by id, never redefined)

## Related Stored Artifacts
- `stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/` (the two external AI review rounds and the round-2 summary that shaped the plan)

## Related Code Areas
`tools/agent-monitoring/session_start_handover_hook.py`; `.claude/settings.json` (the `SessionStart` hook;
a governing file); `.claude/agents/` (generated `session-*.md`); `.claude/handover/`; `registries/`;
`tools/sessions/` (new); `tests/tools/`.

## Assumptions / Open Questions

- Every platform fact is an M0 result, not an assumption (plan 12.1). In particular: which identity signal
  is stable, whether `--agent` files affect the subagent roster, how liveness is detected, and what survives
  each crash case.
- Owner decisions still open (none blocks M0): who staffs `agent-working-planner` and `testing-designer`;
  confirmation of the practice changes in plan section 3 (detail tickets move to the planner); whether a new
  domain may start with an unstaffed seat. The recovery default (suggest resume when the transcript is newer
  than the handover, else replace; the owner chooses) was approved 2026-10-02.
- A session-layer role is not an `agent-orchestration/roles/*.yaml` agent role; the two are named apart.

## Implementation Notes

Child tickets are created later by the agent-working planner (that seat is unstaffed and currently held by
`agent-working-design`), not here. Suggested, non-binding breakdown: M0 spike; M1 registry + validator;
M1 memory migration; M2 resolution + binding record; M2 launcher; M2 recovery flow; M2 worktree self-heal.
**M0 must finish before any M1 or M2 child is activated.** Implementation commits stay with the
agent-working implementer.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
