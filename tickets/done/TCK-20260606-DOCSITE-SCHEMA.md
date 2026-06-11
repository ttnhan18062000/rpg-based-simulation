---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
phase: done
date: 2026-06-06
tags: [docsite, schema]
---

# TCK-20260606-DOCSITE-SCHEMA

## Title
Define frontmatter schema for all documentation content types

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish a formal YAML frontmatter schema that classifies every markdown file in the project (docs, tickets, stored artifacts, archive) by status, layer, authority, and audience. This schema is the foundation that makes Docusaurus navigation, Registry generation, and agent doc discovery possible.

## Scope
- Define the frontmatter schema for four content types: docs, tickets, artifacts, archive
- Write the schema specification as a reference doc at `docs/guidelines/frontmatter_schema.md`
- Write a Python validation script `tools/validate_frontmatter.py` that checks any file or directory against the schema
- Define the valid enum values for all fields

## Out of Scope
- Actually applying frontmatter to any existing files (Tickets 3, 4, 5)
- Docusaurus configuration (Ticket 2)
- Registry generation (Ticket 6)

## Acceptance Criteria
- [ ] Schema spec document exists at `docs/guidelines/frontmatter_schema.md` with field definitions and valid values for all four content types
- [ ] All required vs optional fields are clearly distinguished per content type
- [ ] `tools/validate_frontmatter.py` can be run on a single file or a directory and reports missing or invalid fields
- [ ] Schema covers: `status`, `layer`, `authority`, `audience`, `tags`, `last_verified` for docs
- [ ] Schema covers ticket-specific fields: `ticket_id`, `phase`, `date`
- [ ] Schema covers artifact-specific fields: `ticket_id`, `artifact_type` (`investigation` / `plan` / `test_plan`)
- [ ] Schema covers archive minimal fields: `status: archive`, `layer`, `original_date`
- [ ] Validator exits non-zero on schema violation (CI-safe)

## Related Tickets
- TCK-20260606-DOCSITE-FM-LIVE (consumer)
- TCK-20260606-DOCSITE-FM-TICKETS (consumer)
- TCK-20260606-DOCSITE-FM-ARCHIVE (consumer)
- TCK-20260606-DOCSITE-REGISTRY (consumer)

## Related Docs
- `tickets/todos/PLAN-DOCSITE.md`
- `docs/guidelines/design_patterns.md`
- `docs/ai/README.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/` (new validation script)
- `docs/guidelines/` (new schema spec)

## Assumptions / Open Questions
- `status` values: `authoritative` / `active` / `historical` / `archive` — confirm these are sufficient
- `layer` values: `mechanics` / `engine` / `testing` / `simulation` / `ai` / `architecture` / `core` / `ticket` / `artifact` / `guidelines` — may need additions
- `authority` values: `P0` / `P1` / `P2` — mirrors parity ledger priority convention
- Should `last_verified` be required for `authoritative` docs? (Suggested: yes)
- Does the validator need to handle `.yaml` parity ledger files or only `.md` files? (Suggested: `.md` only)

## Implementation Notes

Implemented stdlib-only frontmatter parser using a single regex pattern for the `---` delimiter block, with line-by-line key:value and inline list parsing. Content type is inferred from path segments (tickets/, stored_artifacts/, docs/archive/, docs/superpowers/, docs/specs/, other docs/). An explicit `content_type` frontmatter field overrides inference. All six enum constant sets are module-level and importable. The validator collects all errors before exiting, printing errors to stderr and the summary to stdout. The main() function has a top-level exception handler to guarantee exit code 1 on unexpected failure. Empty frontmatter blocks (`---\n---\n`) are parsed as an empty dict and then fail required-field checks. The archive `status` constraint is enforced both as a missing-field check and as a value constraint (must equal "archive"). The `last_verified` conditional for authoritative docs is implemented separately from the enum checks so it produces a clear targeted error.

## Test Summary

56 tests total — all pass.
- 47 tests in tests/tools/test_validate_frontmatter.py:
  - Group 1 (4): frontmatter detection including empty block, malformed YAML, block not at file start
  - Group 2 (14): doc content type — all required fields, all enum values, authoritative/last_verified conditional, optional tags
  - Group 3 (5): ticket content type — required fields, phase enum
  - Group 4 (6): artifact content type — three artifact_type values, missing fields, invalid type
  - Group 5 (4): archive content type — valid, wrong status, missing original_date, missing layer
  - Group 6 (5): directory scan — all valid, mixed, skips non-.md, recursive, empty dir
  - Group 7 (3): subprocess exit code contract — exit 0 on valid, exit 1 on invalid, exit 1 on no frontmatter
  - Group 8 (6): anti-drift enum exact-set assertions
- Regression: pytest tests/docs/ — 9 passed, 1 skipped (unrelated), 0 failures.

## Files Changed

- tools/validate_frontmatter.py (created)
- docs/guidelines/frontmatter_schema.md (created)
- tests/tools/test_validate_frontmatter.py (created)

## Completion Summary

Created tools/validate_frontmatter.py (stdlib-only frontmatter validator, 4 content types), docs/guidelines/frontmatter_schema.md (schema spec), tests/tools/test_validate_frontmatter.py (47 tests + 9 regression = 56 passing). Frontmatter schema defined, Python validator implemented (stdlib-only, 4 content types, path inference, CLI), schema spec written, all 56 tests passing, regression clean.
