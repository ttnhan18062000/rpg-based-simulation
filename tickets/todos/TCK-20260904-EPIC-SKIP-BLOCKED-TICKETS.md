---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS
phase: open
date: 2026-09-04
tags: [ai, workflows]
---

# TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS

## Title
implement-epic.js has no mechanism to skip an individual BLOCKED ticket inside a folder/epic batch

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Discovered live while assembling a 13-ticket batch under `tickets/todos/ai-first-hardening-governance-guardrail-batch/`: one ticket (`TCK-20260904-BASH-SECRET-SCAN-HOOK`) had to carry `## Status: BLOCKED` because its hard prerequisite (a separate knowledge-gateway re-ratification) does not exist yet. `.claude/workflows/implement-epic.js`'s folder-mode and epic_id-mode both determine "already done, skip" purely by checking `ls tickets/done/` for a matching ticket ID (Step 2/comment at line 15: "discovers all TCK-*.md files, skips ones already in tickets/done/"; line 106-107, 136-137: "A ticket is already done if tickets/done/{ticket_id}.md exists"). Neither branch reads a candidate ticket's own `## Status` body field at all. If a `BLOCKED` ticket is left inside a todos folder or epic child list, `/implement-epic` would attempt it in normal sequence (SEQUENCE.md order, or alphabetical) and either fail mid-pipeline or produce unusable work against a ticket that cannot structurally proceed — there is no early, cheap skip. This repo already has the identical fix shipped for a sibling tool: `epic_staleness_check.py`'s `discover_candidate_epics()` reads a candidate's `## Status` and treats `BLOCKED` as a distinct, non-stale bucket (`tools/agent-monitoring/epic_staleness_check.py:23,66,146,306` — `is_blocked()` returns `(candidate.status or "").strip().upper() == "BLOCKED"`), following `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` and its folder-mode extension `TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP`. `implement-epic.js` never received the equivalent fix — it is a different tool (an implementation workflow, not a staleness reporter) that never inherited the pattern. This session's workaround was to physically move the blocked ticket out of the todos folder into `tickets/inprogress/` (matching the established convention used by `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`/`TCK-20260730-CODEX-CONTROLLED-PILOT`) — a manual step that should not be required every time a batch contains a blocked ticket.

## Scope
- In `.claude/workflows/implement-epic.js`'s folder-mode Step 2 (and the epic_id-mode equivalent), when building `ticket_ids`/`already_done`, also read each candidate ticket's `## Status` body field.
- Introduce a third bucket alongside "to implement" and "already done": tickets whose `## Status` is `BLOCKED` are reported separately and excluded from the implementation attempt order, mirroring `epic_staleness_check.py`'s "Informational: BLOCKED epics" framing (a status to surface, not an error).
- Update the workflow's final summary/return value to name any `BLOCKED` tickets found, so the user sees them without needing to grep the folder manually.
- Add a regression test proving a synthetic folder containing one normal ticket and one `## Status: BLOCKED` ticket produces an implementation order that excludes the blocked one and reports it separately.

## Out of Scope
- Any change to `epic_staleness_check.py` — it already handles this correctly and is not the tool with the gap.
- Automatically re-including a `BLOCKED` ticket once some external condition changes — that stays a manual re-scope step (flip `## Status` back to `OPEN`), not something this workflow should try to detect on its own.
- Any change to how `## Status: BLOCKED` tickets are stored/located (`tickets/inprogress/` vs `tickets/todos/`) — this ticket only fixes `implement-epic.js`'s in-run detection, not ticket file placement conventions.

## Acceptance Criteria
- [ ] `implement-epic.js`'s folder-mode reads each non-done candidate ticket's `## Status` field before adding it to the implementation order.
- [ ] A ticket with `## Status: BLOCKED` is excluded from `ticket_ids` (the order to implement) and reported in a distinct, named bucket in the phase summary/return value.
- [ ] A synthetic two-ticket folder (one normal, one `## Status: BLOCKED`) demonstrates the blocked ticket is skipped and named in the summary, not silently dropped or silently attempted.
- [ ] The epic_id-mode code path (child tickets, not folder tickets) receives the equivalent fix, verified by an analogous synthetic test.
- [ ] A normal (non-blocked) folder's behavior is unchanged — this must not weaken or slow down the existing done/not-done detection.

## Related Tickets
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC (original BLOCKED-aware fix, different tool — epic_staleness_check.py)
- TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP (extended that fix to epic_staleness_check.py's own folder-mode branch — same "fix landed on one code path, not its sibling tool" class of gap, one layer up: a different tool entirely this time)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC, TCK-20260730-CODEX-CONTROLLED-PILOT (the real BLOCKED tickets whose `tickets/inprogress/`, `phase: blocked` placement this session's manual workaround matched)
- TCK-20260904-BASH-SECRET-SCAN-HOOK (the concrete case that surfaced this gap this session; moved to `tickets/inprogress/` as a manual workaround)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .claude/workflows/implement-epic.js (folder-mode Step 2, epic_id-mode child-ticket discovery)
- tools/agent-monitoring/epic_staleness_check.py (the pattern to mirror: `is_blocked()`, `discover_candidate_epics()`)

## Assumptions / Open Questions
- Whether the fix should hard-skip a BLOCKED ticket unconditionally, or only skip with a warning that a caller could override, is left to the implementer — the safer default (matching this session's manual workaround) is an unconditional skip with a clearly named report, since attempting a structurally-blocked ticket cannot succeed.
- Whether this same gap exists in any other batch-processing tool beyond `implement-epic.js` was not swept in this session (matching `TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP`'s own out-of-scope precedent for a fuller sweep) — a future session should decide if a broader audit is warranted.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
