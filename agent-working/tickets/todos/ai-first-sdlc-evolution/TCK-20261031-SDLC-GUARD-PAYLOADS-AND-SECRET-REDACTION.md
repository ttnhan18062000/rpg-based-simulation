---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
phase: open
date: 2026-10-31
tags: [ai, governance, security]
---

# TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION

## Title
The guard inspects interpreter payloads and asks on `gh api` writes and merges, and secret-shaped strings are redacted from tool rows and the transit export.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Phase 1 code items (plan section 39) that change no credential or ruleset. They are second-line controls, and redaction protects the later credential work.

## Scope
1. `tools/sessions/guard.py` and `classify.py`: inspect `python -c`, `node -e` and `env` payloads; add `ask` for `gh api` PUT and merge, and for `--delete-branch`. Cover the four bypass forms in the plan's P-1.
2. A `ConfigChange` warning hook.
3. Redact secret-shaped substrings in `post_tool_hook.py` tool rows and in `handover_transit.py` export, with a positive control.

## Out of Scope
- Any credential or ruleset change.
- Treating the guard as a boundary: the plan calls it mistake reduction.
- Rewriting existing monitoring rows.

## Acceptance Criteria
1. Each of the four bypass forms now classifies as `ask` or `deny`, with a test; ordinary commands stay allowed, with a test.
2. A token-shaped string in a tool input never reaches a shard or a transit bundle, with a test.
3. A `.claude/settings.json` edit is shown to the owner directly first, and shape tests are updated.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/sessions/guard.py, tools/sessions/classify.py
- tools/agent-monitoring/post_tool_hook.py, tools/handover_transit.py
- .claude/settings.json

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- `.claude/settings.json` is a governing file: it needs the owner's own OK, asked directly.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
