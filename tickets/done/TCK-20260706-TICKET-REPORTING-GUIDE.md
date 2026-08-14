---
status: active
layer: guidelines
authority: P2
audience: developer
ticket_id: TCK-20260706-TICKET-REPORTING-GUIDE
phase: done
date: 2026-07-06
tags: [tagging, reporting, documentation]
---

# TCK-20260706-TICKET-REPORTING-GUIDE

## Title
Add a "Ticket Reporting" developer guide, framing tag-usage reporting as its first pillar

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Follow-up to TCK-20260706-TAG-REPORT-TOOL (`tools/tag_report.py`). User asked for a `docs/guides/`
doc covering that tool's usage and technical detail, explicitly including the legacy/pre-taxonomy
corpus numbers as dated context (why 1002/1044 done tickets are skipped today), and framed the
request using this repo's existing "pillars" convention (`docs/guides/simulation_quality.md`'s "10
behavioral pillars") — tag-usage reporting is the first pillar of a broader, not-yet-built "ticket
reporting" surface, not the whole of it.

## Scope
- New `docs/guides/ticket_reporting.md`:
  - Framing section: ticket reporting as a set of pillars over `tickets/done/` +
    `tickets/working_log.csv` + `docs/REGISTRY.yaml`; tag-usage reporting is Pillar 1 (built).
  - Pillar 1 (Tag Usage Reporting): what it does, CLI usage (`tools/tag_report.py` flags,
    `make tag-report`), technical detail (3 skip rules in order, 4-category classification +
    `unclassified`, non-canonical-tag diagnostic), all cross-referenced to
    `docs/guidelines/tag_taxonomy.md` and `docs/guides/ticket_tagging.md` rather than restating
    their rules.
  - Legacy/historical context subsection: cites `tag_taxonomy.md`'s own corpus-review numbers
    (1001 tickets, 1273 distinct tags, 57.3% singleton, 19+ duplicate groups) plus a dated
    (2026-07-06) live snapshot from `tag_report.py` (1044 files scanned, 1002 skipped as
    pre-taxonomy/legacy `ticket_id`, 12 `SEQUENCE.md`, 3 no-frontmatter, 27 included, 36 unique
    tags) — explicitly labeled as a point-in-time snapshot that will shift as more post-cutoff
    tickets accumulate, not a static claim.
  - "Other candidate pillars" section: a short, non-committal list of other ticket-reporting
    angles this doc's structure leaves room for (e.g. ticket velocity/throughput from
    `working_log.csv` timestamps, tier/type/priority distribution, layer distribution, artifact
    completeness) — explicitly not scoped or promised as future work, just documented as the
    reason this guide is structured as "pillars" rather than a single flat tool doc.
- Add a row to `docs/guides/README.md`'s guide index table.
- Run `make docs-registry` (new doc needs a `docs/REGISTRY.yaml` entry) and
  `make knowledge-index-update` (incremental reindex, per `CLAUDE.md`'s docs-change rule).

## Out of Scope
- Building any of the "other candidate pillars" — documentation only, no new code.
- Adding a `--include-legacy` flag to `tools/tag_report.py` (raised as an option in conversation,
  not requested here) — the legacy numbers in this doc are a cited snapshot, not a
  tool-reproducible live query; a future ticket can add that flag if it's actually wanted.
- Re-tagging, migrating, or deduplicating the historical tag corpus.

## Acceptance Criteria
- [ ] `docs/guides/ticket_reporting.md` exists, passes `validate_frontmatter.py`, and documents
      usage + technical detail + dated legacy context for `tools/tag_report.py`.
- [ ] `docs/guides/README.md`'s index table links to the new guide.
- [ ] `docs/REGISTRY.yaml` contains an entry for the new doc (`make docs-registry` re-run).
- [ ] `make knowledge-index-update` run successfully (or its known pre-existing environmental
      failure mode reproduced and disclosed, not silently ignored).

## Related Tickets
- TCK-20260706-TAG-REPORT-TOOL (the tool this guide documents)
- TCK-20260704-TAG-TAXONOMY (source of the corpus-review numbers cited as legacy context)

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/simulation_quality.md (source of the "pillars" framing convention this guide reuses)
- docs/guides/README.md

## Related Stored Artifacts
None (hotfix tier — no staging artifacts).

## Related Code Areas
- tools/tag_report.py (read-only — the tool being documented)

## Assumptions / Open Questions
- Assumed "we might have other reporting about tickets" is a framing note for this doc's
  structure (a pillars-based guide with room to grow), not a request to build any additional
  pillar now — confirmed reasonable since no specific second pillar was named.

## Implementation Notes
Implemented per Scope:

1. **`docs/guides/ticket_reporting.md`** (new): follows `simulation_quality.md`'s "pillars"
   framing. "Pillar 1: Tag Usage Reporting" documents `tools/tag_report.py`'s quick-start CLI
   usage, the 3 skip rules in exact evaluation order, the 5-way tag classification table, and a
   dated legacy-context subsection citing both `tag_taxonomy.md`'s original corpus-review numbers
   (1001 tickets / 1273 distinct tags / 57.3% singleton / 19+ duplicate groups) and a fresh
   2026-07-06 live snapshot from re-running the tool (1044 scanned → 1002 pre-taxonomy skipped, 12
   `SEQUENCE.md`, 3 no-frontmatter → 27 included, 36 unique tags) — both explicitly labeled as
   point-in-time. An "Other candidate pillars" section lists 4 unbuilt reporting angles
   (velocity/throughput, tier/type/priority distribution, layer distribution, artifact
   completeness) purely to explain the pillars structure, with an explicit "none of the below are
   scoped, promised, or in progress" disclaimer — kept deliberately non-committal per Out of Scope.
2. **`docs/guides/README.md`**: added one row linking the new guide, matching the existing table's
   style.
3. **`make docs-registry`**: re-run — `docs/REGISTRY.yaml` now carries an entry for the new doc
   (verified via `git diff`). The run's exit code 1 is a **pre-existing, unrelated** condition: 12
   doc files already missing frontmatter before this ticket (confirmed via `git log
   --oneline -1 -- docs/engine/project_lawbook_m10.md`, last touched by an older, unrelated
   commit) — none of them touched by this ticket, disclosed not fixed.
4. **`make knowledge-index-update`**: ran successfully (108 files changed/new re-embedded, 1798
   from cache, 0 deleted). Verified the new doc is retrievable via
   `mcp__knowledge-search__search_docs` immediately after (`docs/guides/ticket_reporting.md`
   surfaced as the top hit for a query naming its own content).

## Test Summary
Documentation-only change — no test suite applies. Verification performed instead:
`tools/validate_frontmatter.py docs/guides/ticket_reporting.md` → `OK: 1 file(s) checked — no
violations`; `make docs-registry` confirmed the new entry via `git diff`; `make
knowledge-index-update` completed without error; `search_docs` confirmed retrievability.

## Files Changed
- `docs/guides/ticket_reporting.md` (new)
- `docs/guides/README.md` (added index row)
- `docs/REGISTRY.yaml` (regenerated — new doc entry, unrelated pre-existing drift from prior
  commits also picked up by the regen, not introduced by this ticket)
- `tickets/inprogress/TCK-20260706-TICKET-REPORTING-GUIDE.md` → `tickets/done/...`

## Completion Summary
Added `docs/guides/ticket_reporting.md`, framing ticket-corpus reporting as a set of "pillars"
(mirroring `simulation_quality.md`'s convention) with tag-usage reporting
(`tools/tag_report.py`, from the prior TCK-20260706-TAG-REPORT-TOOL ticket) as Pillar 1 — covering
usage, the exact skip-rule/classification technical detail, and dated legacy-corpus context (both
`tag_taxonomy.md`'s original numbers and a fresh live snapshot) so the "1002 of 1044 tickets
skipped" behavior is documented as expected, not a bug. Listed 4 unbuilt candidate pillars purely
to justify the structure, with no commitment attached. `docs/guides/README.md` indexed, registry
regenerated, and the knowledge index incrementally updated and verified retrievable — no code
changes, no `src/` impact, no parity-ledger entry needed.
