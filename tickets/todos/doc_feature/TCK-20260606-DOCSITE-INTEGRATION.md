# TCK-20260606-DOCSITE-INTEGRATION

## Title
Wire all content into Docusaurus with sidebars, tags, status badges, search, and artifact grouping

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Complete the Docusaurus site by wiring frontmatter-driven features: tag index pages, status badges, layer-filtered sidebars, unified search tuning, and artifact grouping (investigation + plan + test_plan shown together per ticket). This is the final integration ticket — all content should be navigable and searchable in one site.

## Scope

### Sidebar configuration
- Auto-generate sidebars from frontmatter `layer` and `status` fields
- Docs sidebar: grouped by layer (mechanics, engine, core, architecture, systems, combat, testing, simulation, ai, guidelines)
- Tickets sidebar: grouped by phase or date range, filtered to `status: DONE`
- Archive sidebar: flat list under each subdirectory, clearly marked as historical

### Tag pages
- Docusaurus tag index showing all docs tagged with each value
- Tags drive cross-cutting navigation (e.g. "combat" tag shows mechanics/02, combat rulebooks, related tickets, stored artifacts)

### Status badges
- MDX component `<StatusBadge />` that renders `authoritative` / `active` / `historical` / `archive` as colored chips
- Injected automatically based on frontmatter `status` field
- Shows in page header and in search result previews

### Artifact grouping
- Custom sidebar category or MDX wrapper that groups `investigation.md`, `plan.md`, `test_plan.md` under one ticket entry
- Clicking a ticket in the Artifacts section shows a landing page with links to all three artifact files
- Ticket ID is the parent entry; individual artifact files are children

### Search tuning
- Boost `authority: P0` docs in search results
- Demote `status: archive` docs (appear below active results)
- `docusaurus-search-local` config: `docsRouteBasePath` per instance

### Homepage
- Navigation map showing all four content sections with doc counts
- Quick links to highest-priority authoritative docs (Mechanics Bible, Engine Contracts)
- Search bar prominent at top

### docs/README.md update
- Add link to the running Docusaurus site (`make docs-serve`)
- Remove manual navigation map (now handled by the site)

## Out of Scope
- Public hosting or deployment (the site runs locally via `make docs-serve`)
- Docusaurus versioning (docs don't version independently — use `status` field instead)
- Editing or rewriting any content (navigation only)
- Custom React components beyond `<StatusBadge />` and the artifact grouping wrapper

## Acceptance Criteria
- [ ] `make docs-serve` shows a working site with all four sections (docs, tickets, artifacts, archive)
- [ ] Sidebar for main docs is grouped by layer
- [ ] Tag index pages work — clicking a tag shows all docs, tickets, and artifacts with that tag
- [ ] Status badge renders on every page based on frontmatter
- [ ] Artifact section shows tickets as parent entries with investigation/plan/test_plan as children
- [ ] Search returns results across all four content sections
- [ ] P0 authoritative docs appear before P2 historical docs in search for the same query
- [ ] Archive section clearly differentiated visually from active content
- [ ] `make docs-build` produces a static build with no broken links
- [ ] `docs/README.md` updated with link to `make docs-serve`

## Related Tickets
- TCK-20260606-DOCSITE-SCAFFOLD (dependency — Docusaurus must exist)
- TCK-20260606-DOCSITE-REGISTRY (dependency — registry drives sidebar and search tuning)
- TCK-20260606-DOCSITE-FM-LIVE (dependency — frontmatter must be in place)
- TCK-20260606-DOCSITE-FM-TICKETS (dependency)
- TCK-20260606-DOCSITE-FM-ARCHIVE (dependency)

## Related Docs
- `tickets/todos/PLAN-DOCSITE.md`
- `docs/guidelines/frontmatter_schema.md`
- `docs/ai/README.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `website/docusaurus.config.js`
- `website/sidebars.js` (or generated sidebars per plugin instance)
- `website/src/components/StatusBadge/` (new MDX component)
- `website/src/pages/index.js` (homepage)
- `website/src/plugins/artifact-grouping/` (custom plugin if needed)
- `docs/README.md`

## Assumptions / Open Questions
- Artifact grouping implementation: Docusaurus doesn't natively group docs by a custom field. Options: (a) custom sidebar plugin that reads frontmatter `ticket_id` and groups children, (b) a build-time script that generates MDX index pages per ticket. Option (b) is simpler — a `tools/generate_artifact_pages.py` script that creates `stored_artifacts/{ticket_id}/index.md` landing pages before `docusaurus build` runs.
- `docusaurus-search-local` search ranking: the plugin supports `docsRouteBasePath` and can be tuned via `searchResultLimits`. Boosting by frontmatter field requires a custom search plugin or preprocessing the index. If complex, defer boosting to future work.
- Static build link checking: `make docs-build` should include `--out-dir` to a gitignored path. Add `website/build/` to `.gitignore` if not already there from Ticket 2.
- This is the most complex ticket. If artifact grouping proves too complex, ship without it and create a follow-up ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
