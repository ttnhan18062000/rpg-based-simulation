# TCK-20260606-DOCSITE-FM-TICKETS

## Title
Apply frontmatter to tickets and stored artifacts; update ticket format for new tickets

## Status
OPEN

## Request Summary
Apply frontmatter to all existing closed tickets (`tickets/done/`) and stored artifact files (`stored_artifacts/*/`). Update the project's ticket format, CLAUDE.md, and relevant agents so that all future tickets are born with valid frontmatter automatically.

## Scope

### Existing content
- Apply frontmatter to every `.md` file in `tickets/done/`
- Apply frontmatter to `investigation.md`, `plan.md`, `test_plan.md` in every `stored_artifacts/{ticket_id}/`
- Write `tools/add_frontmatter_tickets.py` to automate this (idempotent, skip files with frontmatter)

### Ticket frontmatter fields (from SCHEMA ticket):
```yaml
---
ticket_id: TCK-YYYYMMDD-...
title: "..."
status: DONE
layer: engine          # the layer this ticket's work touched
phase: 28              # numeric phase if applicable, omit if not phase-based
tags: [combat, content-pipeline]
date: YYYY-MM-DD
---
```

### Artifact frontmatter fields:
```yaml
---
ticket_id: TCK-YYYYMMDD-...
artifact_type: investigation   # investigation | plan | test_plan
layer: engine
tags: [...]
---
```

### Forward-looking: update ticket format
- Add frontmatter block as the first section in the ticket template in `CLAUDE.md`
- Update `ticket-scoper` agent to include frontmatter when creating new tickets
- Update `done-checker` agent to verify frontmatter is present and valid as a DoD condition
- Update `investigator` agent to add frontmatter to the artifact files it creates

## Out of Scope
- `tickets/inprogress/` — in-progress tickets do not need frontmatter until closed
- `tickets/todos/` — plan docs and todo tickets, not primary content for the site
- `tickets/backlogs/` if it exists — check but likely not needed
- `staging_artifacts/` — temporary, not indexed

## Acceptance Criteria
- [ ] Every `.md` file in `tickets/done/` has valid frontmatter (validated by `tools/validate_frontmatter.py`)
- [ ] Every `investigation.md`, `plan.md`, `test_plan.md` in `stored_artifacts/*/` has valid frontmatter
- [ ] Scripts are idempotent — safe to re-run
- [ ] Ticket template in `CLAUDE.md` includes frontmatter block as the first section
- [ ] `ticket-scoper` agent produces frontmatter in new tickets
- [ ] `investigator` agent produces frontmatter in new artifact files
- [ ] `done-checker` agent checks for valid frontmatter as condition 12 (new condition added)
- [ ] `tickets/inprogress/` files are not touched

## Related Tickets
- TCK-20260606-DOCSITE-SCHEMA (dependency)
- TCK-20260606-DOCSITE-REGISTRY (consumer)
- TCK-20260606-DOCSITE-INTEGRATION (consumer)

## Related Docs
- `docs/guidelines/frontmatter_schema.md` (dependency)
- `CLAUDE.md` (ticket template section)
- `tickets/todos/PLAN-DOCSITE.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/add_frontmatter_tickets.py` (new)
- `.claude/agents/ticket-scoper.md` (update)
- `.claude/agents/investigator.md` (update)
- `.claude/agents/done-checker.md` (update)
- `CLAUDE.md` — Ticket Format section (update)

## Assumptions / Open Questions
- `layer` for ticket frontmatter: inferred from ticket ID short-scope (e.g. `PHASE22` → `engine`, `PHASE28` → `engine`). The script should have a simple mapping and flag unresolvable cases for manual review.
- `phase` field: extract numeric phase from ticket ID where present (e.g. `PHASE22` → `22`). Leave blank if not phase-based.
- `date` field: parse from the ticket ID date prefix (YYYYMMDD → YYYY-MM-DD).
- `tags` on existing tickets: auto-infer from ticket ID scope words. Manual review recommended for accuracy.
- Should `tickets/backlogs/` be included? Check if it contains content.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
