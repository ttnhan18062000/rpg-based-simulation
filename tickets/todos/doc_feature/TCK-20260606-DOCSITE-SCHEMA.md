# TCK-20260606-DOCSITE-SCHEMA

## Title
Define frontmatter schema for all documentation content types

## Status
OPEN

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

## Test Summary

## Files Changed

## Completion Summary
