---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL
phase: open
date: 2026-07-09
tags: []
---

# TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL

## Title
Backfill missing frontmatter on 3 closed DOCSITE tickets

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md, TCK-20260606-DOCSITE-INTEGRATION.md, and TCK-20260606-DOCSITE-REGISTRY.md have no frontmatter at all, causing generate_registry.py warnings and blank tier/ticket_type/date/tags fields in the registry. tools/add_frontmatter_tickets.py already has hardcoded, idempotent, test-covered inference for these exact three ticket_ids, so the fix is to re-run the established tool rather than hand-write frontmatter.

## Scope
- Run tools/add_frontmatter_tickets.py against the 3 named files: tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md, tickets/done/TCK-20260606-DOCSITE-INTEGRATION.md, tickets/done/TCK-20260606-DOCSITE-REGISTRY.md
- Verify each resulting frontmatter block passes tools/validate_frontmatter.py --content-type ticket
- Regenerate docs/REGISTRY.yaml and confirm the 3 prior warnings no longer appear and the corresponding entries have populated tier/ticket_type/date/tags

## Out of Scope
- Running add_frontmatter_tickets.py against any tickets outside these 3 confirmed files
- Any change to tools/add_frontmatter_tickets.py's inference logic itself (it already has correct hardcoded mappings for these ticket_ids)

## Acceptance Criteria
- [ ] Running `python3 tools/add_frontmatter_tickets.py` against the 3 named files leaves each starting with a valid '---' frontmatter block
- [ ] `python3 tools/generate_registry.py` produces zero 'WARNING: ... DOCSITE ... missing frontmatter' lines for these 3 files (currently reproduces exactly 3 such warnings)
- [ ] Regenerated docs/REGISTRY.yaml entries for these 3 ticket_ids have non-empty tier/ticket_type/date/tags
- [ ] `python3 tools/validate_frontmatter.py <each file> --content-type ticket` passes with 0 violations for all 3

## Related Tickets
- TCK-20260606-DOCSITE-FM-TICKETS
- TCK-20260606-DOCSITE-REGISTRY
- TCK-20260606-DOCSITE-INTEGRATION
- TCK-20260606-DOCSITE-FM-ARCHIVE
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Related Docs
- `docs/guidelines/frontmatter_schema.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/add_frontmatter_tickets.py`
- `tools/generate_registry.py`
- `tools/validate_frontmatter.py`
- `tools/tag_registry.py`
- `tests/tools/test_add_frontmatter_tickets.py`
- `tests/tools/test_generate_registry.py`
- `tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md`
- `tickets/done/TCK-20260606-DOCSITE-INTEGRATION.md`
- `tickets/done/TCK-20260606-DOCSITE-REGISTRY.md`

## Assumptions / Open Questions
- Scope is confirmed as exactly these 3 files — a repo-wide scan of tickets/done/*.md found no other frontmatterless tickets
- add_frontmatter_tickets.py walks the whole tickets/done/ tree (656 tickets) when run — should verify with a diff/dry check before commit that it only touches these 3 files
- TCK-20260606-DOCSITE-FM-TICKETS's own implementation notes explicitly flagged this gap as a known accepted trade-off at the time, not an oversight in that prior work

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
