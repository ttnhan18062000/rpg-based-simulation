---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING

## Title
Session-layer M2b: signal-based role resolution, binding record and card injection in SessionStart

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Replace the one-size handover hook with a role-aware `SessionStart`: gather the harness signals, resolve the role, bind the current `session_id`, write the binding record, inject the role card and **only that role's** handover. Fails open.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M2). Depends on M2a.

## Scope
- `tools/sessions/resolve.py`: pure function from signals (`agent_type`, `session_title`, `SESSION_ROLE`, worktree path, `source`) to a role or an explicit `unresolved`/`disagree` result, following the M0o precedence table: on `source: resume` do not trust `agent_type` or the environment, `session_title` is the resume signal; signals that disagree resolve nothing and inject nothing privileged.
- `tools/sessions/session_start_hook.py`: reads the hook payload, resolves, appends a binding record via M2a (`session_id`, `role`, `manifest_digest`, `worktree`, `branch`, `source`, `signals`, pid with start time, `ts`), injects `compose_card()` output plus the role's own handover note only, and updates `instance.json`. Unknown or missing role (a plain `claude`): inject nothing and say once how to launch with a role.
- Manifest digest diff: on resume or clear, if the digest differs from the previous binding, say what changed in a line or two; flag an authority reduction.
- Writer lease taken at SessionStart for a worktree's writer role (M2a).
- Keep the existing `session_start_handover_hook.py` behaviour reachable as the fallback for unresolved sessions only if the owner wants it (see Assumptions); do not delete it in this ticket.
- `.claude/settings.json`: replace the SessionStart command with the new hook, keeping `2>/dev/null || true` fail-open. This is a governing-file edit: owner confirms the literal diff (feedback_verify_governing_file_edits_directly) and a settings-shape test search runs first (grep `tests/` for the pinned hook shape).

## Out of Scope
- Launcher and recovery (M2c), `PreToolUse` guardrail (M5), monitoring `session_role` field (M6a), `/clear` and live-rename probes (class 2, still unrun).

## Acceptance Criteria
1. Resolution table test covers start, resume (no `agent_type`, no env), fork (duplicate title, new id), clear, compact, plain `claude`, and a disagreeing-signals case; each yields the stated result.
2. Hook output on a resolved role contains the card and that role's handover and no other role's title or handover; on unresolved it contains one launch hint and nothing privileged.
3. A binding record is appended per start and `instance.json` holder updates; the hook exits 0 and injects nothing on any exception (fail-open test with a malformed payload and an unreadable manifest).
4. Digest-change message appears when the manifest changes between two bindings, and an authority reduction is flagged.
5. Resume from a different cwd: transcript path is stored as a hint only; the test asserts nothing depends on it (M0p).
6. Owner confirmation of the literal `settings.json` diff is recorded in the ticket; no existing hook-shape test regresses; scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done), M1a-d (done, #314 and the M1d PR)
- M2a (dependency), M2c (parallel after M2a), M5 (consumes the binding record).

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 5, 6, 6.1, 8, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; signal precedence table)
- `docs/guides/agent_session_reset_boundaries.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Implementation Notes
`resolve.py` (pure, M0o table; `<role>-N` instance ids from `max_sessions`; disagreement resolves nothing), `manifest_diff.py` (digest of the two registry files + a per-role `manifest.json` snapshot so the hook can say what changed and flag an authority reduction; a change that does not touch the role's own summary is silent), `session_start_hook.py` (bind, lease, card + only that role's handover; unresolved gets the OLD all-roles listing as the fallback (owner decision) plus one launch hint; transit notice on every outcome; fail open). `.claude/settings.json` SessionStart command now points at the new hook: the owner confirmed this literal diff directly in the terminal (AskUserQuestion, 2026-10-04).

## Test Summary
`tests/tools/test_session_resolve_and_hook.py` (34): resolution table (start, resume, fork, clear, compact, plain claude, unknown title, disagreement), instance ids, diff and reduction flag, card + only own handover, fallback listing + one hint, binding per start and instance update, lease taken by writer only, foreign lease reported not stolen, digest message/silence, cross-cwd transcript hint only, second live holder flagged, fail-open on bad payloads and unreadable manifest.

## Files Changed
tools/sessions/{resolve,manifest_diff,session_start_hook}.py; .claude/settings.json; tests/tools/test_session_resolve_and_hook.py; docs/guides/agent_session_reset_boundaries.md

## Completion Summary
Delivered as part of the M2a-c bundle on branch `session-layer-m2-role-state`; scoped tests green; docs and registry regenerated.

## Related Code Areas
- `tools/sessions/` (`resolve.py`, `session_start_hook.py`; reuses `card.py`, `roster.py`, `state.py`), `tools/agent-monitoring/session_start_handover_hook.py`, `.claude/settings.json`, `tests/tools/`.

## Assumptions / Open Questions
- Whether the old all-roles handover hook stays as the unresolved-session fallback: drafted as removed from the hook chain (plan 5: "inject nothing and say how to launch"); owner may veto.
- `/clear` and live-rename are unprobed: the design assumes only that at least one signal survives start, resume and fork.
