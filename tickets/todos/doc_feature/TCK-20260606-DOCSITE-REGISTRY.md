# TCK-20260606-DOCSITE-REGISTRY

## Title
Generate docs/REGISTRY.yaml and integrate with agents for doc discovery

## Status
OPEN

## Request Summary
Build a Python script that reads frontmatter from all content types (docs, tickets, artifacts, archive) and generates a flat `docs/REGISTRY.yaml`. Update CLAUDE.md and the relevant agents to use the registry for fast doc discovery without reading 542 files.

## Scope

### Registry generation script
`tools/generate_registry.py`:
- Walks all frontmatter-tagged content roots: `docs/`, `tickets/done/`, `stored_artifacts/`
- Reads frontmatter from each `.md` file
- Emits a flat YAML list with one entry per file:
  ```yaml
  - path: docs/mechanics/02_combat_laws.md
    title: Combat Laws
    status: authoritative
    layer: mechanics
    authority: P0
    audience: developer
    tags: [combat, damage, durability]
    last_verified: 2026-06-06
  ```
- Sorts by `authority` then `layer` then `path`
- Reports count by status/layer/authority at the end
- Exits non-zero if any in-scope file is missing frontmatter (CI gate)

### Makefile target
`make docs-registry` — regenerates `docs/REGISTRY.yaml`

### Agent integration
Update `CLAUDE.md` Graphify Integration section to mention the registry.
Update these agents to query the registry before reading raw files:
- `investigator` — "before listing related docs, check docs/REGISTRY.yaml to find authoritative entries for the affected layer"
- `mechanics-auditor` — "use registry to find all P0 entries for the relevant layer before auditing"
- `architecture-reviewer` — "use registry to find active architecture docs relevant to the plan's layer"

## Out of Scope
- Building or updating Docusaurus from the registry (Ticket 7)
- Vector embedding of docs (future work)
- Automated registry update on every file edit (future CI hook)
- Updating `docs/README.md` navigation (covered in Ticket 7)

## Acceptance Criteria
- [ ] `docs/REGISTRY.yaml` exists and contains entries for all frontmatter-tagged files
- [ ] Registry is sorted: P0 authoritative first, then P1 active, then P2 historical/archive
- [ ] `tools/generate_registry.py` runs without error after Tickets 3, 4, 5 are complete
- [ ] `make docs-registry` regenerates the file in place
- [ ] Script exits non-zero if any in-scope file lacks frontmatter
- [ ] `CLAUDE.md` references the registry in the Graphify Integration section
- [ ] `investigator` agent updated to check registry for doc discovery
- [ ] `mechanics-auditor` agent updated to use registry for P0 layer lookup
- [ ] `architecture-reviewer` agent updated to use registry for relevant active docs

## Related Tickets
- TCK-20260606-DOCSITE-SCHEMA (dependency)
- TCK-20260606-DOCSITE-FM-LIVE (dependency — must complete before registry is complete)
- TCK-20260606-DOCSITE-FM-TICKETS (dependency)
- TCK-20260606-DOCSITE-FM-ARCHIVE (dependency)
- TCK-20260606-DOCSITE-INTEGRATION (consumer)

## Related Docs
- `docs/guidelines/frontmatter_schema.md`
- `tickets/todos/PLAN-DOCSITE.md`
- `CLAUDE.md` (Graphify Integration section)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/generate_registry.py` (new)
- `docs/REGISTRY.yaml` (generated, committed)
- `Makefile`
- `CLAUDE.md`
- `.claude/agents/investigator.md`
- `.claude/agents/mechanics-auditor.md`
- `.claude/agents/architecture-reviewer.md`

## Assumptions / Open Questions
- `docs/REGISTRY.yaml` should be committed to git (not gitignored) so agents can read it without running the script
- Should the registry include `tickets/todos/` and `tickets/inprogress/`? Suggested: no — only `done` tickets are stable references
- `stored_artifacts/` subdirectory structure: each entry should include which ticket it belongs to (from frontmatter `ticket_id` field)
- How often should the registry be regenerated? Manually via `make docs-registry` for now; CI hook is future work

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
