---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM
phase: open
date: 2026-08-21
tags: [documentation]
---

# TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM

## Title
GitHub Pages docs deploy has failed on every push since 2026-06-17 (Node heap OOM in Docusaurus build)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`Deploy Docs to GitHub Pages` (`.github/workflows/deploy-docs.yml`) has failed on every single
triggering push to `main` since 2026-07-02, and on 100% of pushes since 2026-08-14 (12 consecutive
failures, confirmed via `gh run list --workflow=294250397`). The live site at
`https://ttnhan18062000.github.io/rpg-based-simulation/` has not received a successful deploy since
2026-06-17T10:48:51Z — over two months of merged docs/ticket/artifact content is not reflected on
the published Pages site. Root cause confirmed identical across the earliest (2026-07-02) and latest
(2026-08-20) failing runs: the `Build` step (`cd website && npm run build`, i.e. `docusaurus build`)
crashes with `Aborted (core dumped)` / exit code 134 from a V8 `FATAL ERROR: Ineffective
mark-compacts near heap limit Allocation failed - JavaScript heap out of memory` (observed peak
~4,129MB old-space before abort — both runs' `<--- Last few GCs --->` traces show the same ceiling).
No `NODE_OPTIONS`/`--max-old-space-size` flag is set anywhere in `website/package.json` or the
workflow, so Node's unflagged default V8 old-space limit (~4GB) applies regardless of the
`ubuntu-latest` runner's actual RAM.

The underlying driver is content volume, not a code defect: `website/docusaurus.config.js` runs
**four** separate `@docusaurus/plugin-content-docs` instances over `../docs` (816 files, 16MB),
`../tickets/done` (15MB), `../stored_artifacts` (37MB), and `../agent-monitoring/retro` —
`tickets/done` + `stored_artifacts` alone total 5,246 markdown files. This corpus grows on every
ticket close (this repo runs a high-throughput ticket pipeline), so the build's real memory need has
been climbing steadily past the unflagged default ceiling.

## Scope
- Set an explicit Node heap-size flag on the `Build` step in `.github/workflows/deploy-docs.yml`
  (e.g. `NODE_OPTIONS: --max-old-space-size=8192`), sized with headroom above the ~4.13GB observed
  crash point and within the real `ubuntu-latest` runner's available RAM.
- Confirm the next `Deploy Docs to GitHub Pages` run triggered by a real push to `main` completes
  successfully end to end (Build → Configure Pages → Upload Pages artifact → Deploy to GitHub Pages).

## Out of Scope
- Shrinking the docs/tickets/artifacts corpus itself to reduce memory usage — a content-lifecycle
  decision, not this hotfix's concern, and this corpus will keep growing regardless.
- Fixing the ~30+ dangling-markdown-link `[WARNING]` lines visible in the build log — cosmetic,
  non-blocking (`onBrokenLinks: 'warn'` in `docusaurus.config.js`), unrelated to the OOM crash.
- Restructuring the four-plugin content-docs setup or migrating off Docusaurus.
- Any further tuning (webpack parallelism, source maps, persistent caching) beyond the one heap-size
  flag needed to stop the crash — flagged as a possible follow-up, not required here.

## Acceptance Criteria
- [ ] `.github/workflows/deploy-docs.yml`'s `Build` step sets an explicit Node old-space heap limit
      comfortably above the ~4.13GB observed crash ceiling
- [ ] The next real push to `main` touching `docs/**`, `tickets/done/**`, `stored_artifacts/**`, or
      `website/**` produces a successful (not `failure`) `Deploy Docs to GitHub Pages` run
      (`gh run list --workflow=294250397 --limit 1`)
- [ ] The live site at `https://ttnhan18062000.github.io/rpg-based-simulation/` reflects
      post-2026-06-17 content after the fix lands

## Related Tickets
None found — first ticket filed against this failure (investigated via `gh run list`/`gh api`
directly; no prior ticket references this workflow's OOM failure).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/deploy-docs.yml` — the `Build` step needing the heap-limit env var (currently
  no `env:` block sets any Node memory flag)
- `website/package.json` — `"build": "docusaurus build"`, unchanged by this fix
- `website/docusaurus.config.js` — the four `@docusaurus/plugin-content-docs` instances (`docs`,
  `tickets` → `../tickets/done`, `artifacts` → `../stored_artifacts`, `agent-monitoring` →
  `../agent-monitoring/retro`) whose combined corpus size (5,246+ files across `tickets/done` +
  `stored_artifacts` alone) is the real memory driver, confirmed via `du -sh`/`find | wc -l`

## Assumptions / Open Questions
- Assumes 8192MB is sufficient headroom above the ~4.13GB observed peak; if the corpus keeps growing
  at its current rate this may need revisiting later — not necessarily a permanent fix.
- Whether this repo's GitHub-hosted `ubuntu-latest` runners actually have 16GB RAM (the 2026
  standard) should be confirmed before finalizing the exact MB value — too high a value risks a
  runner-level OOM-kill (SIGKILL, no diagnostic) instead of Node's own graceful heap-limit abort with
  a clear stack trace.
- Not investigated: whether a complementary webpack-level change (disabling source maps, tuning
  parallelism) would reduce peak memory further — out of scope here, flagged only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
