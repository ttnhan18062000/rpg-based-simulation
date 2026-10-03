---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-TICKETS
phase: done
date: 2026-06-06
tags: [docsite, fm, tickets]
---

# TCK-20260606-DOCSITE-FM-TICKETS

## Title
Apply frontmatter to tickets and stored artifacts; update ticket format for new tickets

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

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

- `tools/add_frontmatter_tickets.py` written following `add_frontmatter_archive.py` pattern.
- Layer inference: `movement` is not a valid LAYER_VALUE — remapped to `engine` (locomotion is engine-layer). `guidelines` listed before `engine` in LAYER_KEYWORDS to prevent over-matching.
- Idempotency uses conformance check (`status: historical` for tickets, `artifact_type:` for typed artifacts, `content_type: doc` for non-standard) rather than bare `---` presence — prevents skipping files with incomplete frontmatter from a prior tooling pass.
- Non-standard artifact filenames (walkthrough, task, implementation_plan, etc.) get `content_type: doc` frontmatter so the validator routes them through the doc schema (no `artifact_type` field required). This avoids polluting `ARTIFACT_TYPE_VALUES` with 30+ legacy one-off names.
- `planner.md` also updated (gap from original scope — `plan.md` is produced by planner, not investigator).
- `done-checker.md` now has 13 conditions: frontmatter check inserted as condition 12, agent monitoring shifted to 13.
- Backfill result: 656 tickets modified, 1240 artifacts processed (1096 initial pass, 177 follow-up fixes for incomplete frontmatter and non-standard filenames, 10 movement-layer rewrite).

## Test Summary

- 30 unit/integration tests in `tests/tools/test_add_frontmatter_tickets.py` — all pass.
- Full `tests/tools/` suite (246 tests) — all pass.
- `validate_frontmatter.py tickets/done/` — 656 files, 0 violations.
- `validate_frontmatter.py stored_artifacts/` — 1240 files, 0 violations.

## Files Changed

- `tools/add_frontmatter_tickets.py` (NEW)
- `tests/tools/test_add_frontmatter_tickets.py` (NEW)
- `CLAUDE.md` (ticket template — frontmatter block added)
- `.claude/agents/ticket-scoper.md` (frontmatter block in ticket output template)
- `.claude/agents/investigator.md` (frontmatter instructions in Output 1 and Output 2)
- `.claude/agents/planner.md` (frontmatter instruction in plan.md output — gap from scope)
- `.claude/agents/done-checker.md` (new condition 12, monitoring renumbered to 13)
- `tickets/done/*.md` — 656 files backfilled
- `stored_artifacts/**/*.md` — 1240 files backfilled

## Completion Summary
Backfilled frontmatter on 656 tickets in `tickets/done/` and 1240 artifact files in `stored_artifacts/`. Wrote `tools/add_frontmatter_tickets.py` (idempotent, layer-inference, handles non-standard artifact filenames via `content_type: doc`). Updated `CLAUDE.md` ticket template and 4 agent files (`ticket-scoper.md`, `investigator.md`, `planner.md`, `done-checker.md`) to produce frontmatter on all future tickets and artifacts. `done-checker.md` now has 13 DoD conditions (frontmatter check as condition 12, monitoring shifted to 13). 86 tests pass (1 skipped). `validate_frontmatter.py` reports 0 violations across all 1896 backfilled files.
