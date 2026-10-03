---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE
phase: open
date: 2026-10-03
tags: [ai, process-improvement, governance]
---

# TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE

## Title
Session-layer M0: verify the Claude Code harness facts the session-layer design depends on, with positive controls, and decide go / adjust on plan sections 5, 9.5 and 10

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

The session-layer plan (`docs/plans/agent_infrastructure/session_layer_working_process.md`, binding) rests on
about 18 platform facts that are documented, inferred or only partly observed. M0 turns each into a recorded
local result before any M1 or M2 code is written (plan 12.1: "verify against the real harness, with positive
controls"). Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION`; runs **after** M-1
(`TCK-20261003-AGENT-WORKING-ROOT-MOVE`) merges, so its evidence lands at the final paths. Harness version at
drafting: Claude Code 2.1.286; the record states the version actually used.

## Scope

One investigation record (`investigation.md`, plus `.jsonl` raw evidence; **never `.json`**, which `.gitignore`
drops from `stored_artifacts/`) with a result for **every** item below. Each item states: the question, the
exact procedure, the observed result, the **positive control** (a case that must show the effect, proving the
probe can see it), the harness version, and whether documentation and observation agree (a disagreement is
listed, and the plan is updated from the observation).

| Item | Verify |
|---|---|
| a | `--name` survives `/clear` and `--resume` and shows as `session_title` in `SessionStart` |
| b | `--agent session-x` applies the tool allowlist to the **main** session |
| c | `SendMessage` to an idle session in a clean launch: does it wake; what changes after `/clear` |
| d | an agent file named `session-*` does not enter the Agent-tool subagent roster in a way that makes the model spawn it |
| e | a `PreToolUse` hook receives `session_id` and can match an Edit path and a Bash command |
| f | a session started by a launcher then resumed outside it: name and role signal kept |
| g | renaming a live session after launch |
| h | forking: which identity the fork inherits |
| i | manifest changed between launch and resume: what the hook sees |
| j | the prompt-submit hook payload (for the headline metric) |
| k | `/clear` yields a new session id while the name persists |
| l | `crossSessionInbound` and permission-mode pairs: deliver, hold or drop; what the 5-minute `dialogExpiry` does to a message sent to an idle role session |
| m | duplicate names (variant rename and shared names) and what `session_title` reports |
| n | what a `PreToolUse` hook can return for an authority-class operation (deny / ask / allow), and what the harness does on classification failure, unparseable input or hook error |
| o | **signal-precedence table**: for `agent_type`, `SESSION_ROLE`, `session_title`, `session_id`: present and stable across start, resume, clear, compact, fork, rename |
| p | persistence: title written into the transcript and surviving `/clear`; transcript path convention for a worktree; `claude --resume <id>` from another cwd |
| q | liveness: telling a live instance from a dead one (harness process id, inbox socket) |
| r | the plan 6.1 crash cases and what survives each: terminal closed or process killed; machine crash or power loss; out-of-memory or harness crash; dropped ssh or editor connection; `/clear` right before the crash; crash mid-rebase or mid-merge |

Outcome section of the record: a **go / adjust decision** on plan sections 5 (launch), 9.5 (idle sessions) and
10 (authority), the signal-precedence table, a list of items **not verifiable** here with the reason, and
an answer to the open question "is a minimal inbox needed" (M0c, from item c and l).

The investigation first classifies each item as (1) checkable by the agent alone (for example hooks fed by
`claude -p` or a crafted payload) or (2) needing a live interactive session or a deliberate crash. Class 2
runs only with the owner's opt-in and in disposable sessions on a scratch worktree, never against the
owner's working sessions.

## Out of Scope

- Any production code, hook change, `settings.json` change or registry file (M1 onward).
- Changing the plan beyond what a recorded observation requires; every plan edit cites the item that forced it.
- Staffing decisions and the three open owner decisions.
- Measuring cost or latency (Epic D).

## Acceptance Criteria

1. Each of a to r has a recorded result with a positive control and the harness version; items that cannot be
   verified are listed with the reason, not left blank.
2. The signal-precedence table (item o) exists and states, per signal, which events keep it stable.
3. Every disagreement between the official documentation and a local observation is listed, and the plan is
   updated from the observation in the same PR.
4. The go / adjust decision on sections 5, 9.5 and 10 is written, with what changes in M1 to M5 if "adjust".
5. No disposable session or scratch worktree is left behind; no change to `.claude/settings.json`, hooks or
   any governing file (checked by diff); no owner session was used as a probe target.
6. Raw evidence is `.jsonl` (or text), committed, and indexed (`make knowledge-index-update` if `docs/` changed).

## Related Tickets

- Parent: `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M0); precedes M1 and M2 children.
- Depends on: `TCK-20261003-AGENT-WORKING-ROOT-MOVE` (M-1).
- Prior evidence: `TCK-20260921-SESSION-CONTEXT-RESET-TRIAL`; verified 2026-09-27 facts in plan 6.1.

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 5, 6.1, 9.0, 9.5, 10, 12.1)
- `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
(Created by this ticket.)

## Related Code Areas
`tools/agent-monitoring/session_start_handover_hook.py` (read only); `.claude/settings.json` (read only).

## Assumptions / Open Questions

- Documentation and an earlier observation may be stale for 2.1.286; every item is re-run, none copied.
- Which items need the owner's live terminal (class 2) is decided in the investigation; the owner opts in per class.
- Held messages to an idle session may need the owner to type a prompt in that terminal (plan 9.5, unverified).

## Implementation Notes
Investigation-only; the implementer commits the record and the plan edits. No `Workflow` run is needed.

## Test Summary
No code. Positive controls are the verification; a re-run script (if any) stays under the record.

## Files Changed
(Open.)

## Completion Summary
(Open.)
