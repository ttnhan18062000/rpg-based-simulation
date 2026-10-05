---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS
phase: done
date: 2026-10-04
tags: [ai, hooks, process-improvement]
---

# TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS

## Title
`subagent_stop_background_guard.py` blocks subagent handback over parent-session artifact subscriptions

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Reported by `rpg-feature-planning` (2026-10-04): a `planner` subagent dispatched from that session (Plan phase of a hand-executed implement-ticket run for `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`) was blocked on two consecutive turns by the SubagentStop guard. The subagent's own `jobs` list was empty; the listed tasks were the parent session's artifact live-update subscriptions ("re-armed on session resume" / "auto-armed on publish"). A subagent cannot drain or wait on those, so the guard's remedy is unreachable: a hard stop with no legitimate exit.

Mechanism, partly verified from the repo: the hook reads `payload["background_tasks"]` unfiltered. Its docstring states the field is session-scoped by the harness's own design (one expression feeds both `Stop` and `SubagentStop`) and that no `agent_type` filtering is intentional (`TCK-20260904-TEST-SCOPER-HANG-GUARD`). So any parent-session registry entry reaches every subagent's stop. Not verified: that artifact subscriptions appear in `background_tasks` at all, and which `type` label they carry (schema fixture lists `shell`, `subagent`, `monitor`, `workflow`; no subscription type). The report is from the subagent and was relayed, not observed here.

The CLAUDE.md hard rule (a dispatched subagent never ends its turn with its own background command running) is correct and stays. The defect is only that the guard may count work the subagent does not own.

## Scope
- Capture a real `SubagentStop` payload while the parent holds an artifact subscription (diagnostic hook output to a scratchpad file, then remove it) and record the task `type`/`description` of the subscription entries. Positive control: the same capture with a real subagent-started `run_in_background` shell task.
- If subscriptions are distinguishable (type or description), exclude that class from the `SubagentStop` decision only, keeping `Stop` behavior and keeping every shell/monitor/workflow task blocking.
- If they are not distinguishable, record that, and choose with evidence between: filtering on whether the task id appears in the subagent's own transcript (`agent_transcript_path`), or accepting the block and documenting the exit.
- Tests: extend `tests/tools/test_subagent_stop_background_guard.py` with the captured subscription shape (frozen minimal fixture) and the unchanged blocking cases.
- Note in the ticket whether the `sidecar-check` PreToolUse hook's firing on every edit while a ticket is in `inprogress/` is the same session-state-not-action pattern (advisory, cost-free; no change unless the capture says otherwise).

## Out of Scope
- Weakening the rule for shell, monitor or workflow tasks; CLAUDE.md edits; any workaround that silences the hook.

## Acceptance Criteria
1. A captured real payload (committed as `.jsonl` or inline in a fixture, never `.json` under stored_artifacts) shows what a parent subscription looks like to a subagent stop.
2. A subagent with no background work of its own, under a parent with a subscription, is allowed to stop; a test proves it from the captured shape.
3. A subagent that started its own background shell command is still blocked (positive control stays green).
4. `Stop` (main session) behavior is unchanged, or the change is stated and justified.
5. Scoped tests green; the finding about distinguishability is recorded; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` (origin of the guard)

## Related Docs
- `tools/agent-monitoring/subagent_stop_background_guard.py`, `tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.json`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/agent-monitoring/subagent_stop_background_guard.py`, `.claude/settings.json` (SubagentStop entry, read-only here), `tests/tools/test_subagent_stop_background_guard.py`

## Assumptions / Open Questions
- Whether artifact subscriptions are in `background_tasks` is unconfirmed; AC 1 settles it first, and if they are not, the report's cause is wrong and this becomes a different ticket.
- A settings.json change is not expected; if one is needed it is a governing-file edit needing the owner's direct confirmation.

## Implementation Notes
- **Live capture (2026-10-05, owner-approved):** a throwaway diagnostic SubagentStop hook in the git-ignored `.claude/settings.local.json`, one private test artifact published (parent subscription auto-armed), one trivial `general-purpose` subagent dispatched. Result, frozen as `tests/fixtures/claude_hook_payloads/subagent_stop_parent_subscription.jsonl` (paths and ids redacted): `background_tasks` held exactly two entries, `{type: "monitor", description: "live updates for artifact <url> (auto-armed on publish)"}` (the parent's subscription) and `{type: "subagent", id == agent_id, status: "running"}` (the stopping subagent's own entry). Both were distinguishable by type/description, so the transcript-ownership fallback was not needed. The hook, the settings file and the test artifact were removed afterwards.
- `subagent_stop_background_guard.py`: when `hook_event_name == "SubagentStop"`, ignore the subagent's own entry (type subagent, id == agent_id) and monitor tasks whose description starts `live updates for artifact`. Every other task (shell, other monitors, workflows, other subagents) still blocks; `Stop` is untouched.
- Limit: a subagent that itself publishes an artifact gets its own auto-armed subscription, which this filter also ignores (same description). Judged acceptable: the subscription is not something a subagent can drain.
- Not established: the capture hook only logs, and the real guard also ran on that stop. The subagent was not visibly blocked even though the payload listed two tasks, so whether the unfiltered guard blocks on the first attempt or only trips in the reported two-turn shape was not measured here.
- The `sidecar-check` PreToolUse hook question in the ticket scope was not examined (advisory, cost-free; no change made).

## Test Summary
`tests/tools/test_subagent_stop_background_guard.py`: 9 pass. New: the captured payload is allowed (AC1, AC2); the captured shape plus a real shell task still blocks and the message omits the subscription (AC3, positive control); another monitor task still blocks a subagent; the same payload as a main-session `Stop` still blocks (AC4).

## Files Changed
- tools/agent-monitoring/subagent_stop_background_guard.py
- tests/tools/test_subagent_stop_background_guard.py
- tests/fixtures/claude_hook_payloads/subagent_stop_parent_subscription.jsonl

## Completion Summary
SubagentStop no longer counts the stopping subagent's own registry entry or the parent's artifact subscription; real background work of the subagent still blocks, and the main-session Stop is unchanged. The payload evidence is a real capture.
