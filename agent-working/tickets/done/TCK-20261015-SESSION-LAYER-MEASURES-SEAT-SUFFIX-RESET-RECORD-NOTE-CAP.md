---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP
phase: done
date: 2026-10-15
tags: [agent-monitoring, hooks, process-improvement]
---

# TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP

## Title
Session-layer measures: role_boundary matches seat suffixes, reset-boundary declarations get a durable record, and SessionStart warns when a handover note is over the cap

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, findings 6 and 8. (a) `role_boundary` flagged `edit_outside_owns` for lead-planner-u24 writing a `lead`
domain file: owner_seats lists `lead-planner`, and the `-u24` seat suffix isn't matched. (b) HARD/SOFT reset boundaries are
announced only in chat (`docs/guides/agent_session_reset_boundaries.md` around L14-18); nothing records them, so whether a
/clear happened at HARD can't be audited. (c) Six handover notes exceed the hook's 8000-character cap (rpg-planner.md
218,570 characters), and the hook cuts them silently (`session_start_hook.py` HANDOVER_CAP_CHARS); the guide still says
"one file per role name" and doesn't cover per-instance `<stem>-N` notes.

## Scope
1. role_boundary resolves a seat with a host or instance suffix to its base role's owner seats (a registry lookup, not a
   string strip, if the registry has the mapping).
2. `tools/sessions/reset_boundary.py declare --kind HARD|SOFT|NEVER --row "<boundary-map process>"` appends
   `{ts, session_id, session_role, kind, row, handover_rel, handover_sha256}` to
   `agent-working/agent-monitoring/data/<week>/reset_boundary.jsonl` (same weekly-shard conventions as role_boundary; never
   fails the caller). On `source == clear`, the hook adds one advisory line if the previous session declared no HARD, or if
   the handover changed after it. The retro counts declarations. Not in manual_actions (that metric is owner-typed repeats).
3. When a handover note is over the cap, the hook adds one line saying so (size and cap), instead of cutting silently.
4. Guide update: say it AND run the declare command; per-instance notes.

## Out of Scope
- Compacting anyone's note (each seat compacts its own).
- Making any of this blocking.

## Acceptance Criteria
- Tests: a seat with a suffix maps to its base role's owns and gives no false edit_outside_owns; declare writes one row;
  a clear without a prior HARD gives the advisory line; an over-cap note gives the size line.
- The guide text is updated, and the W42+ retro shows a declarations count (0 is fine).

## Related Tickets
- TCK-20260921-SESSION-CONTEXT-RESET-TRIAL
- TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW (M6b)

## Related Docs
- docs/guides/agent_session_reset_boundaries.md
- docs/plans/agent_infrastructure/session_layer_working_process.md (section 11)

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/sessions/boundary.py, tools/sessions/session_start_hook.py, tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- docs/guides/ is used by every role; keep guide edits to the two sentences named.

## Implementation Notes
(a) Seat suffix: not reproduced as a defect. The one flagged record (2026-10-13T07:55, lead-planner-u24 writing docs/architecture/devops_plan_amendment_proposal.md, owner_seats [lead-planner]) is the intended sibling crossing of TCK-20261013-HOST-LEAD-PLANNER-U24 (the u24 seat owns only its host page; the rest of the lead domain is lead-planner's), and with current code `check_edit` returns owner_seats [lead-planner] for it, [] for its own page, and the reverse for lead-planner writing the u24 page: the registry already maps the host seat. A numbered instance resolves to its base role (`_base_role`), and a registered seat is never string-stripped. Pinned with tests; no code change. (b) `tools/sessions/reset_boundary.py declare --kind HARD|SOFT|NEVER --row ...` appends `{ts, session_id, session_role, kind, row, handover_rel, handover_sha256}` to this week's bare `reset_boundary.jsonl` through the shared locked writer, never fails its caller; on `source == clear` SessionStart adds one advisory line when the previous session declared no HARD, or its handover note changed after the HARD declaration; the retro Run Summary shows a declarations count for weeks from 2026-W42 (0 included). Not in manual_actions. (c) A handover note over the 8000-character cap now gets a line with its size and the cap before the (still cut) text. (d) Guide: say it AND run the declare command, per-instance `<stem>-N.md` notes and the cap, two sentences as the ticket allowed.

## Test Summary
`tests/tools/test_session_reset_boundary.py` (new, 7) and `test_session_resolve_and_hook.py` (6 new: clear with no prior HARD, with an unchanged note, with a note edited after, startup never, over-cap size line, under-cap no line) and one retro row test pass; session suites pass.

## Files Changed
tools/sessions/reset_boundary.py, tools/sessions/session_start_hook.py, tools/agent-monitoring/generate_retro.py, docs/guides/agent_session_reset_boundaries.md, tests/tools/test_session_reset_boundary.py, tests/tools/test_session_resolve_and_hook.py, tests/tools/test_closure_recorder_phase_evidence.py

## Completion Summary
Reset-boundary declarations are recorded and audited at `/clear`, an over-cap note says so, the guide says to record it, and the host-seat mapping is pinned (the reported false flag was not reproduced: the flag was the intended crossing).
