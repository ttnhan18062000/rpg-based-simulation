---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-SKILL-MAPPING-DEDUP
phase: open
date: 2026-07-20
tags: []
---

# TCK-20260720-SKILL-MAPPING-DEDUP

## Title
Deduplicate the 4-copy process-skill-signal-to-skill mapping table into a single source

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The Process/Skill-signal-tag to suggested_skills table is manually duplicated across ticket-scoper.md, ticket_tagging.md, implement-ticket.js, and create-tickets.js, with a drift-detector (tools/tag_skill_mapping_check.py) that itself has a hardcoded 5th copy (KNOWN_TAGS) and previously declared dedup out of scope by design — a decision this work reopens. Preferred approach (to be confirmed/refined during Investigate) is to encode the mapping as a triggers_skill-style field directly on each process-skill-signal tag's row in tag_registry.jsonl rather than a new 5th registry file, with all 4 current copies reading from that one place. Investigate should decide whether the drift-detector becomes unnecessary or shrinks to checking that consumers read the live source.

## Scope
- resolve the append-only-vs-existing-rows conflict during this ticket's own Investigate/Plan phases and encode the target-skill mapping as a single source (preferred: a triggers_skill-style field on each process-skill-signal tag's row)
- update all 4 consumers (ticket-scoper.md, ticket_tagging.md, implement-ticket.js, create-tickets.js) to read from the single source
- explicitly decide and implement the fate of tag_skill_mapping_check.py (remove vs repurpose)

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- pre-deciding which of the 3 candidate schema-conflict resolutions to use — that decision belongs to this ticket's own Investigate/Plan phases, not to this synthesis

## Acceptance Criteria
- [ ] changing a tag's target skill in exactly ONE stored location changes what all 4 consumers actually compute/emit — verified by editing the single source and confirming all 4 outputs reflect the change with zero other file edits
- [ ] the debugging tag's conditional target (default /debugging-strategies vs the world-debugger carve-out for world-path tickets) is preserved losslessly, not flattened to a plain string that drops the branch
- [ ] tag_skill_mapping_check.py's fate is explicitly decided and implemented — either removed with its 10 tests retired/migrated, or repurposed into a check that each of the 4 consumers reads the live source rather than embedding a literal copy — not left as dead code comparing copies that no longer independently exist
- [ ] tag_registry.jsonl's append-only/no-update invariant is either preserved by the schema-change design, or the invariant break is explicitly justified and recorded
- [ ] during this ticket's own Investigate/Plan phase, one of the 3 candidate resolutions to the append-only-vs-existing-rows conflict (or an explicitly justified 4th option) is chosen and documented — not mandated in advance by this ticket's Scope

## Related Tickets
- TCK-20260705-TAG-SKILL-SUGGEST
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE

## Related Docs
- docs/guidelines/tag_registry.jsonl
- docs/guidelines/tag_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_skill_mapping_check.py
- tests/tools/test_tag_skill_mapping_check.py
- tools/tag_registry.py
- tests/tools/test_tag_registry.py
- .claude/agents/ticket-scoper.md
- docs/guides/ticket_tagging.md
- .claude/workflows/implement-ticket.js
- .claude/workflows/create-tickets.js

## Assumptions / Open Questions
- candidate resolution (a): widen add_tag()'s schema going forward only — new rows get the triggers_skill field, old rows stay without it and are read via a fallback
- candidate resolution (b): do a one-time explicitly-authorized rewrite of the 4 existing tag_registry.jsonl lines, breaking the append-only invariant, requiring explicit sign-off
- candidate resolution (c): store the mapping in a different location entirely, not on tag_registry.jsonl rows
- the 4 consumers span 3 different execution contexts requiring different read mechanisms: the 2 Node.js workflow files have a working precedent (python3 -c subprocess call + stdout JSON marker, already used at implement-ticket.js:313-314 and create-tickets.js:578-579); ticket-scoper.md is an LLM-interpreted agent prompt with no code execution; ticket_tagging.md is a pure human-read doc with no binding mechanism today
- if dedup succeeds, tag_skill_mapping_check.py's entire premise (pairwise-comparing independently-maintained texts) becomes moot, but its 3 parser functions and 10 tests encode real format-specific knowledge — delete-vs-shrink is explicitly undecided
- no prior ticket has reopened TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK's explicit out-of-scope decision — this is genuine, undone work
- layer assigned as `ai` (Claude agent/orchestration tooling) per docs/guidelines/layer_registry.jsonl — this work is entirely about agent/workflow tooling infrastructure, not gameplay cognition

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
