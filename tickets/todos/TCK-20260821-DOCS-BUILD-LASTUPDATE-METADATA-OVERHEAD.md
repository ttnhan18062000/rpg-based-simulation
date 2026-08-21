---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD
phase: open
date: 2026-08-21
tags: [documentation]
---

# TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD

## Title
Reduce Docusaurus build memory footprint: disable per-file git-log metadata for the
high-volume archive plugins (tickets, artifacts, agent-monitoring)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM` raises the Docusaurus build's Node heap ceiling to stop the
immediate `Deploy Docs to GitHub Pages` crash, but that alone is a stopgap: the underlying corpus
this build processes keeps growing and will eventually outgrow any fixed ceiling again. This ticket
investigates and addresses a second, structurally fixable cost driver found while diagnosing the
OOM: `website/docusaurus.config.js` sets `showLastUpdateTime: true` / `showLastUpdateAuthor: true`
on **all four** of its `@docusaurus/plugin-content-docs` instances (`docs`, `tickets`, `artifacts`,
`agent-monitoring`), covering 6,185 real files as of 2026-08-21 (`docs`: 899, `tickets/done`: 1,637,
`stored_artifacts`: 3,636, `agent-monitoring/retro`: 13). Docusaurus resolves each file's
last-updated time/author via a `git log` call per file during build — a documented, independent
memory/CPU cost on top of markdown parsing and webpack bundling, and one that scales directly with
file count. `tickets/done` + `stored_artifacts` together are 5,273 of the 6,185 files and had 2,081
file-touches in the last 30 days alone (`git log --since="30 days ago"`) — this is the fastest-growing
part of the corpus, and also the part where "last updated" metadata has the least real value: it is
an append-only historical record of already-closed work, not live-authored reference material like
`docs/`.

## Scope
- Disable `showLastUpdateTime` and `showLastUpdateAuthor` for the `tickets`, `artifacts`, and
  `agent-monitoring` plugin instances in `website/docusaurus.config.js` (leave `docs`'s setting
  unchanged — smaller file count, genuine editorial value for live-authored reference material).
- Investigate and report the real before/after memory impact (e.g. a local or CI-equivalent build
  comparison) so this ticket's evidence is measured, not assumed from Docusaurus's documented
  behavior alone.
- Confirm no part of the live site (tickets/artifacts sidebar, search index, page footer) has a
  real dependency on the removed metadata before it's turned off.

## Out of Scope
- `TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM`'s own heap-limit fix — this ticket is a complementary,
  structural reduction, not a replacement for it. Both are needed; neither blocks the other.
- Deciding whether `tickets/done`/`stored_artifacts` should be excluded, truncated, or archived out
  of the public Pages build entirely (a content-retention/publishing-policy question, not a build
  performance one) — flagged in Assumptions, not scoped here.
- Any change to `docs/`'s own `showLastUpdateTime`/`showLastUpdateAuthor` setting.
- Further webpack-level tuning (parallelism, source maps) beyond this one metadata change.

## Acceptance Criteria
- [ ] `tickets`, `artifacts`, and `agent-monitoring` plugin configs in
      `website/docusaurus.config.js` no longer set `showLastUpdateTime`/`showLastUpdateAuthor`
      (or explicitly set them `false`)
- [ ] `docs` plugin's `showLastUpdateTime`/`showLastUpdateAuthor` are unchanged
- [ ] A real build comparison (or documented investigation) reports the measured memory/time
      reduction from this change
- [ ] `npm run build` (or the equivalent CI step) still completes and produces working
      tickets/artifacts/agent-monitoring pages with no missing content

## Related Tickets
- `TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM` — the immediate heap-limit fix this ticket complements

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `website/docusaurus.config.js` — lines ~19-46 (the `tickets`, `artifacts`, `agent-monitoring`
  plugin blocks) and ~66-72 (the `docs` preset block, left unchanged)

## Assumptions / Open Questions
- **Flagged, not decided here**: whether `tickets/done` and `stored_artifacts` (append-only,
  already-closed historical records, the fastest-growing part of this corpus at 2,081 file-touches
  in the last 30 days) should keep being published to the public GitHub Pages site at full depth
  going forward, versus some retention/exclusion policy (e.g. only recent N months, or an index-only
  view). That's a content-publishing decision for the repo owner, not a build-performance fix — this
  ticket does not assume an answer either way.
- Assumes Docusaurus's per-file `git log` cost for `showLastUpdateTime`/`showLastUpdateAuthor` is a
  measurable contributor to the OOM, based on documented Docusaurus build-performance behavior at
  this file count — the Investigate phase should produce real before/after numbers, not rely on this
  assumption alone.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
