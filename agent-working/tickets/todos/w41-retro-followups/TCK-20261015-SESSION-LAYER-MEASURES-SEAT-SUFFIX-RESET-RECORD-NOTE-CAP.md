---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP
phase: open
date: 2026-10-15
tags: [agent-monitoring, hooks, process-improvement]
---

# TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP

## Title
Session-layer measures: role_boundary matches seat suffixes, reset-boundary declarations get a durable record, and SessionStart warns when a handover note is over the cap

## Status
OPEN

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
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
