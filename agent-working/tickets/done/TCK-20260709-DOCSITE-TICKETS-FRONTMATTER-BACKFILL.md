---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL
phase: done
date: 2026-07-09
tags: []
---

# TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL

## Title
Backfill missing frontmatter on 3 closed DOCSITE tickets

## Status
DONE

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
Running `python3 tools/add_frontmatter_tickets.py` with no args (its only invocation mode — it has no CLI file-targeting flags) walks the entire `tickets/done/` and `stored_artifacts/` trees and touched 1160 files (203 tickets + 956 artifacts modified), not just the 3 named files — it rewrites any file carrying the stale `layer: movement` value in addition to files with no frontmatter at all, and `TICKET_DIR.rglob("*.md")` also sweeps up `SEQUENCE.md` files. Per the ticket's explicit verify-or-revert instruction, this repo-wide run was reverted immediately (`git checkout -- tickets/done stored_artifacts`) without committing.

Instead, applied the script's own unmodified logic to only the 3 named files by importing `add_frontmatter_tickets` as a module and calling its existing `process_ticket_file()` function directly against each of the 3 target paths (no change to the script's inference logic or CLI, per Out of Scope). `git diff --stat` confirmed only the 3 target files changed as a result (plus the auto-updated `agent-monitoring/tools.jsonl`, unrelated to this fix).

All 3 files now start with a valid `---` frontmatter block (`status: historical`, inferred `layer: guidelines`, `ticket_id`, `phase: done`, `date: 2026-06-06`, and inferred `tags`). Verified each with `python3 tools/validate_frontmatter.py <file> --content-type ticket` — 0 violations for all 3.

Ran `python3 tools/generate_registry.py` — zero WARNING lines of any kind were produced (previously exactly 3 DOCSITE frontmatter-missing warnings). Confirmed via `grep` on the regenerated `docs/REGISTRY.yaml` that all 3 entries now have populated `tier`, `ticket_type`, `date`, and `tags` fields. Per the task instructions this regeneration was a verification byproduct, not a required commit artifact, but it was left in the working tree since regenerating the registry is itself in-scope per the ticket's acceptance criteria.

## Test Summary
- `python3 tools/validate_frontmatter.py <file> --content-type ticket` run individually against all 3 target files: 0 violations each.
- `python3 tools/generate_registry.py`: 0 WARNING lines (was 3 DOCSITE-related warnings before the fix).
- `git diff --stat` after the targeted run: confirmed exactly the 3 named ticket files changed (no stray edits from the tool's broader tree walk).

## Files Changed
- tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md
- tickets/done/TCK-20260606-DOCSITE-INTEGRATION.md
- tickets/done/TCK-20260606-DOCSITE-REGISTRY.md
- docs/REGISTRY.yaml (regenerated byproduct, not required to commit per task instructions but left as-is)

## Completion Summary
Backfilled missing frontmatter on the 3 closed DOCSITE tickets (`tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md`, `TCK-20260606-DOCSITE-INTEGRATION.md`, `TCK-20260606-DOCSITE-REGISTRY.md`) by calling `tools/add_frontmatter_tickets.py`'s existing `process_ticket_file()` function directly against just these 3 files — not the full-tree CLI entrypoint, which would have touched 1160 files (203 tickets + 956 artifacts) across the repo. `git diff --stat` confirmed only the 3 target files changed as a result.

All 3 files now pass `tools/validate_frontmatter.py --content-type ticket` with 0 violations. Regenerated `docs/REGISTRY.yaml`, which now shows zero DOCSITE-missing-frontmatter warnings and has populated `tier`/`ticket_type`/`date`/`tags` fields for all 3 entries.

Tests: the 70 existing tests in `tests/tools/test_add_frontmatter_tickets.py` and `tests/tools/test_generate_registry.py` all pass — no test changes were required since no script logic was modified, only its existing function was invoked more narrowly.

Files changed: `tickets/done/TCK-20260606-DOCSITE-FM-TICKETS.md`, `tickets/done/TCK-20260606-DOCSITE-INTEGRATION.md`, `tickets/done/TCK-20260606-DOCSITE-REGISTRY.md`, `docs/REGISTRY.yaml`.
