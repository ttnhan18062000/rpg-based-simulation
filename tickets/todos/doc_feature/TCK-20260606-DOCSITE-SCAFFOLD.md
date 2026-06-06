# TCK-20260606-DOCSITE-SCAFFOLD

## Title
Initialize Docusaurus 3 site with multi-instance content plugins and local search

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Set up a Docusaurus 3 site that can serve all project content types (docs, tickets, artifacts, archive) as a unified, searchable site. This is the structural skeleton — content wiring and frontmatter-driven features come in Ticket 7.

## Scope
- Initialize Docusaurus 3 under `website/` directory
- Configure `@docusaurus/plugin-content-docs` with four instances pointing at the four content roots
- Install and configure `docusaurus-search-local` for offline full-text search
- Add `make docs-serve` and `make docs-build` targets to the Makefile
- Add `website/node_modules/`, `website/build/`, `website/.docusaurus/` to `.gitignore`
- Minimal homepage with navigation map linking to each content section
- Verify `make docs-serve` starts the site with all four sections reachable

## Out of Scope
- Frontmatter-driven sidebar, tag pages, status badges (Ticket 7)
- Artifact grouping by ticket ID (Ticket 7)
- Registry integration (Ticket 6)
- Applying frontmatter to any content files (Tickets 3, 4, 5)
- Deploying or hosting the site publicly

## Acceptance Criteria
- [ ] `website/` directory exists with valid Docusaurus 3 config
- [ ] Four content plugin instances configured: `docs`, `tickets`, `artifacts`, `archive`
- [ ] `docusaurus-search-local` installed and enabled
- [ ] `make docs-serve` starts the site without errors
- [ ] `make docs-build` produces a static build without errors
- [ ] All four content sections are reachable from the homepage
- [ ] `website/node_modules/` and `website/build/` are gitignored
- [ ] Existing Makefile targets are unaffected

## Related Tickets
- TCK-20260606-DOCSITE-SCHEMA (parallel — independent)
- TCK-20260606-DOCSITE-INTEGRATION (consumer — this is the base it builds on)

## Related Docs
- `tickets/todos/PLAN-DOCSITE.md`
- `README.md` (Makefile targets reference)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `website/` (new)
- `Makefile`
- `.gitignore`

## Assumptions / Open Questions
- Docusaurus 3 under `website/` — confirm this doesn't conflict with the existing React frontend under `frontend/`
- Content plugin instance IDs: `docs`, `tickets`, `artifacts`, `archive` — these become the URL prefixes (`/docs/`, `/tickets/`, `/artifacts/`, `/archive/`)
- `docusaurus-search-local` vs Algolia DocSearch — local is correct for a private/offline project
- Does `make docs-serve` need to activate the Python venv first, or is it pure Node? (Suggested: pure Node, no venv needed)
- Node.js ≥ 18 is already a project requirement — no new system dependency needed

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
