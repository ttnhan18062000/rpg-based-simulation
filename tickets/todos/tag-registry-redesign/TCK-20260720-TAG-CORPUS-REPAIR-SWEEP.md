---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
phase: open
date: 2026-07-20
tags: [tagging, data-quality, reporting]
---

# TCK-20260720-TAG-CORPUS-REPAIR-SWEEP

## Title
Build a report-only legacy corpus repair-sweep tool for tag/category violations

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Enforcement of tag rules is forward-only from 2026-07-04, leaving a large, never-checked historic gap. Build a report-only sweep, extending tag_report.py's existing corpus-walk and frontmatter parser (no second parser, no per-file agent/LLM reads due to context cost), covering the full corpus (tickets/done, tickets/inprogress, tickets/todos/**, stored_artifacts/**). For every tag in every file's frontmatter it should flag unregistered tags, tags whose recorded category doesn't resolve in the new category registry, and non-canonical-form tags that predate enforcement. It must not auto-fix or rewrite any historic file — output is a list of (file, tag, issue) rows; deciding what to do with findings is left to a human or a follow-up ticket.

## Scope
- Extend tag_report.py's existing corpus-walk into a new non-cutoff-gated sweep across tickets/done/**, tickets/inprogress/**, tickets/todos/**, and stored_artifacts/**.
- Reuse validate_frontmatter.py's extract_frontmatter() as the sole parser — no second parser, no per-file LLM reads.
- Call tag_registry.py's canonical_form_violation/is_tag_registered/check_tags_registered/load_registry as the single source of truth for flagging.
- Emit (file, tag, issue) rows for unregistered, invalid_category, and non_canonical_form cases; report-only, no writes.

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch).
- Auto-fixing or rewriting any historic file — no --fix flag; deciding what to do with findings is left to a human or a follow-up ticket.
- Re-deriving tag validation rules independently of tag_registry.py's existing functions.

## Acceptance Criteria
- [ ] The sweep walks tickets/done/**, tickets/inprogress/**, tickets/todos/** (skipping SEQUENCE.md at every level, same as collect_completed_tickets' existing skip) and stored_artifacts/**/*.md, parsing via extract_frontmatter() only, and does NOT apply the pre_taxonomy_or_legacy_ticket_id date-cutoff skip — pre-2026-07-04 files are included.
- [ ] For every tag found, a (file, tag, issue) row is emitted per applicable case: unregistered (not in registry, not canonical phase-N) -> 'unregistered'; registered but recorded category not in the current valid-category set -> 'invalid_category'; canonical_form_violation(tag) is not None -> 'non_canonical_form'; a tag with multiple issues produces multiple rows.
- [ ] Files with no frontmatter or no tags key produce zero rows, not a crash (verified against real fixtures: stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md and stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md).
- [ ] Running the sweep against the real corpus produces zero filesystem writes (git-diff-clean before/after) — output is stdout/JSON rows only, no --fix flag exposed.
- [ ] The exact intended semantics of the 'invalid_category' flag are confirmed during this ticket's own Scope phase rather than assumed, given no direct precedent and possibly zero real hits today.

## Related Tickets
- TCK-20260706-TAG-REPORT-TOOL
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260704-TAG-TAXONOMY
- TCK-20260719-TAG-COLLISION-DEDUP
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guidelines/tag_registry.jsonl
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_report.py
- tools/tag_registry.py
- tools/validate_frontmatter.py
- tests/tools/test_tag_report.py
- tests/tools/test_tag_registry.py

## Assumptions / Open Questions
- Full corpus size confirmed: tickets/done has 1199 .md files, tickets/inprogress 0, tickets/todos 20 (4 SEQUENCE.md-bearing subfolders), stored_artifacts 2735 .md files across 814 ticket-id directories (~3954 total) — a non-cutoff-gated scan will surface far more rows than the 185-violation baseline previously measured only on tickets/done post-taxonomy; needs a sane CLI/JSON output shape.
- 22% of stored_artifacts .md files sampled (601/2730) have no tags: frontmatter field, some have no frontmatter block at all — the sweep must tolerate both as 'nothing to flag'.
- TCK-20260719-TAG-COLLISION-DEDUP already ran an ad-hoc (not checked into tools/) full-corpus scan finding 1352 distinct tags as of 2026-07-19 — useful sizing precedent but a one-time manual-fix action, not a substitute for this reusable tool.
- docs/guides/ticket_reporting.md's Pillar 1 section documents tag_report.py's current narrower scope and needs a new subsection once this sweep exists.
- Layer chosen as `ai` (Claude agent/orchestration tooling) since this is a workflow-tooling build against tools/tag_report.py, not a gameplay subsystem; no better-fitting registered layer was found.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
