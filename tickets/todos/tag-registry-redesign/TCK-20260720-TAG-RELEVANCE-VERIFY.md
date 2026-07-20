---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-RELEVANCE-VERIFY
phase: open
date: 2026-07-20
tags: [tagging, workflows]
---

# TCK-20260720-TAG-RELEVANCE-VERIFY

## Title
Add a tag-relevance verification step to catch hallucinated, wrong, or drifted tags

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Surfaced directly from this session's own experience: twice, tickets came out of `create-tickets.js`
with no Subsystem/Topic tags, and both times the correction was a human (the user) reading the
ticket and manually picking better tags. Checked `tools/validate_frontmatter.py`'s `_check_tags`
directly — it only verifies canonical form (spelling/format) and registry membership (does this
tag exist). Nothing anywhere in the pipeline verifies that an assigned tag is actually *relevant*
to what a ticket is about, and nothing revisits a ticket's tags after Scope/creation time even
when later Investigate/Plan/Implement phases reveal the ticket touches subsystems nobody
anticipated when it was tagged. This means both hallucinated tags (a plausible-sounding but wrong
tag, assigned by an LLM with no independent check) and missing tags (a ticket's actual final scope
drifts away from its declared tags during implementation) currently go completely undetected —
the only check that exists today is an attentive human noticing, which is not a reliable
mechanism.

## Scope
- A relevance-check step, following the same "second independent look" pattern this repo already
  uses for `security-reviewer`/`mechanics-auditor`, that cross-references a ticket's assigned tags
  against its title/scope/`related_code_areas` at creation time and flags an implausible tag —
  wired into both tag-assignment paths (`create-tickets.js`'s Structure phase for batch creation,
  and `ticket-scoper` for single-ticket creation).
- A drift check, run at Finalize time (or as part of `done-checker`), that re-derives candidate
  tags from a ticket's final `Files Changed`/`related_code_areas` and flags any obvious mismatch
  against its declared `tags` for human review — e.g. a ticket that ended up only touching
  `src/api/agent_ops_dashboard/` but has no `dashboard` tag.
- Document both mechanisms in `docs/guides/ticket_tagging.md`.

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- Building a fully automated tag-assignment engine — this is a verification/flagging layer over
  existing human/LLM tag assignment, not an auto-tagger.
- Retroactively re-verifying the entire historic ticket corpus for tag *relevance* —
  TCK-20260720-TAG-CORPUS-REPAIR-SWEEP already covers the full corpus, but only for
  registry-membership/canonical-form/category-validity, a deliberately different and narrower kind
  of check than relevance; this ticket does not extend that sweep's scope.
- Making either check a hard pipeline-blocking gate — both are advisory flags for human review,
  matching this repo's existing practice for soft/judgment-based signals (e.g. the existing
  `mistag_warning` heuristic in `ticket-scoper.md`/`implement-ticket.js`, which warns rather than
  blocks).

## Acceptance Criteria
- [ ] A relevance-check mechanism exists and is wired into at least one tag-assignment path
      (`create-tickets.js`'s Structure phase and/or `ticket-scoper`), flagging — not silently
      rejecting — a tag whose registered category/description doesn't plausibly match the
      ticket's title, scope, and `related_code_areas`.
- [ ] A drift-check mechanism exists that, given a ticket's final `Files Changed`/
      `related_code_areas`, flags an obvious mismatch against its declared `tags` for human
      review, without auto-adding or auto-removing any tag.
- [ ] Neither mechanism blocks or fails the ticket pipeline outright — both surface as advisory
      warnings, consistent with this repo's existing treatment of judgment-based signals.
- [ ] `docs/guides/ticket_tagging.md` documents both mechanisms: what they check, where they run,
      and that they are advisory, not enforcing.
- [ ] `docs/ai/agents.md` is updated if either mechanism is implemented as (or added to) an
      existing agent's documented behavior.

## Related Tickets
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
- TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
- TCK-20260705-TAG-SKILL-SUGGEST
- TCK-20260706-CREATE-TICKETS-TAG-CHECK
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guides/ticket_tagging.md
- docs/guidelines/tag_taxonomy.md
- docs/ai/agents.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/create-tickets.js
- .claude/agents/ticket-scoper.md
- tools/gate_checks/done_checker_static.py
- tools/validate_frontmatter.py
- tools/tag_registry.py
- .claude/agents/security-reviewer.md
- .claude/agents/mechanics-auditor.md

## Assumptions / Open Questions
- Precedent pattern for the relevance check: `security-reviewer` and `mechanics-auditor` both
  already implement a "second independent agent look" over another agent's output in this repo —
  whether the relevance check should be a similarly dedicated new agent, or a lighter-weight check
  folded into `ticket-scoper`'s/`create-tickets.js`'s own existing output, is an open
  implementation decision for this ticket's own Investigate/Plan phases, not decided here.
- Both mechanisms are inherently judgment-based (an LLM or heuristic assessing "does this tag fit"
  has no ground truth to check against) — false positives/negatives are expected and acceptable
  given the advisory (non-blocking) design; this is a deliberate trade-off, not an oversight.
- This ticket is related to but distinct from TCK-20260720-TAG-CORPUS-REPAIR-SWEEP: that sweep
  answers "is this tag validly formed and registered" across the whole historic corpus; this
  ticket answers "does this tag actually describe what the ticket is about" going forward — the
  two checks are complementary, not overlapping, and should not be merged into one tool.
- Layer assigned as `ai` (Claude agent/orchestration tooling) since this is entirely about the
  agent/ticket-workflow tooling, not gameplay subject matter, matching the rest of this batch's
  layer choices.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
