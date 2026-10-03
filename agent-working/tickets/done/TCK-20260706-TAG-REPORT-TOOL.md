---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-TAG-REPORT-TOOL
phase: done
date: 2026-07-06
tags: [tagging, taxonomy, reporting]
---

# TCK-20260706-TAG-REPORT-TOOL

## Title
Add a tag-usage report tool over completed tickets

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
User asked whether the ticket tagging system has a defined tag list (answered by pointing to
`docs/guidelines/tag_taxonomy.md`'s controlled-vocabulary-of-categories, not a closed enum), then
asked for a script/tool to export a tag-usage report over every completed (`tickets/done/`) ticket:
tag → number-of-tickets-using-it, skipping tickets that are too old (legacy format / predate the
taxonomy) or carry no tags at all.

## Scope
- New standalone script `tools/tag_report.py`:
  - Walks `tickets/done/` recursively (including the small number of ticket files that live in
    `tickets/done/{folder}/` subfolders, e.g. `tickets/done/worldtemplate-deprecation/`), skipping
    `SEQUENCE.md` index files.
  - Reuses `tools/validate_frontmatter.py`'s `extract_frontmatter`, `_ticket_id_effective_date`,
    `TAG_TAXONOMY_EFFECTIVE_DATE`, `TAG_SYNONYM_MAP`, `FORBIDDEN_PRIORITY_TAGS` (same import
    pattern already used by `tools/generate_registry.py`) rather than re-implementing frontmatter
    parsing or taxonomy constants.
  - Reuses `tools/registry_query.py`'s `SEED_TAGS` for Subsystem/Topic tag classification, rather
    than adding a third hand-copy of that 10-word list.
  - Skip rules (counted and reported, not silently dropped): no/unparseable frontmatter (legacy
    format), `ticket_id` missing or its embedded date predates `TAG_TAXONOMY_EFFECTIVE_DATE`
    (2026-07-04), and empty/missing `tags`.
  - For included tickets: count occurrences per tag, classify each tag into one of the 4
    `docs/guidelines/tag_taxonomy.md` categories (Subsystem/Topic, Phase/Milestone,
    Process/Skill-signal, Quality-attribute) or `unclassified` when no rule matches (expected and
    fine — the taxonomy is explicitly not a closed enumeration), and flag any non-canonical-form
    tag found among *included* (post-taxonomy-cutoff) tickets as a data-quality diagnostic.
  - CLI: prints a human-readable summary (scanned/included/skipped-by-reason counts, tag frequency
    table sorted by count desc) to stdout; `--json <path>` optionally writes the full structured
    report (includes per-tag ticket ID lists) to a file.
- Add `tests/tools/test_tag_report.py` covering categorization, each skip reason, count
  aggregation, and non-canonical-tag detection, using small in-memory fixtures (no dependency on
  the live `tickets/done/` corpus, per this repo's existing `tests/tools/test_registry_query.py`
  pattern).
- Add a `tag-report` Makefile target (mirrors the existing `docs-registry` / `agent-monitoring-retro`
  targets' style).

## Out of Scope
- Any change to `tools/validate_frontmatter.py`, `tools/generate_registry.py`, or
  `tools/registry_query.py` themselves — read-only imports only.
- Retroactively re-tagging or fixing any historical ticket's tags — this is a read-only reporting
  tool, not a taxonomy-enforcement or migration tool.
- Wiring this report into any agent workflow, gate, or CI check — standalone, manually-invoked
  developer tool only.
- Docs changes (no `docs/` file created or modified — the taxonomy and tagging docs already fully
  describe the categories this tool classifies against; no `make knowledge-index-update` needed).

## Acceptance Criteria
- [ ] `python3 tools/tag_report.py` run against the live repo prints scanned/included/skipped
      counts (broken down by skip reason) and a tag → count → category table for `tickets/done/`.
- [ ] Tickets with no frontmatter, an unparseable/missing `ticket_id` date, a `ticket_id` date
      before `2026-07-04`, or empty/missing `tags` are excluded from the tag counts and counted
      under a skip reason instead.
- [ ] `--json <path>` writes an equivalent structured report to disk.
- [ ] `tests/tools/test_tag_report.py` passes.

## Related Tickets
- TCK-20260704-TAG-TAXONOMY (defined the 4 categories and the 2026-07-04 enforcement cutoff this
  tool's skip logic reads)
- TCK-20260705-TAG-REGISTRY-QUERY (prior art for the `SEED_TAGS` import pattern and the
  same-package `sys.path.insert` import style this tool reuses)

## Related Docs
- docs/guidelines/tag_taxonomy.md (category definitions, canonical-form rules, forbidden tags,
  2026-07-04 enforcement cutoff)
- docs/guides/ticket_tagging.md (practical guide, skill-suggestion table)

## Related Stored Artifacts
None (hotfix tier — no staging artifacts).

## Related Code Areas
- tools/validate_frontmatter.py (read-only import source)
- tools/registry_query.py (read-only import source)
- tools/generate_registry.py (read-only reference for the same import pattern and ticket-collection
  approach)

## Assumptions / Open Questions
- Assumed "skip too-old/untagged tickets" means: apply the same 2026-07-04 taxonomy-effective-date
  cutoff `validate_frontmatter.py` already uses, rather than inventing a separate age threshold —
  this keeps one definition of "too old" in the repo instead of two.
- Assumed a small number of ticket files live directly under `tickets/done/{folder}/` subfolders
  (confirmed: 1 real ticket file plus 12 `SEQUENCE.md` index files across 13 subfolders) and should
  be included (minus `SEQUENCE.md`, which is an index, not a ticket).

## Implementation Notes
Implemented per Scope:

1. **`tools/tag_report.py`** (new): `collect_completed_tickets(root)` walks `tickets/done/`
   recursively via `rglob("*.md")`, skipping `SEQUENCE.md` index files, and applies 3 skip rules in
   order — unparseable/missing frontmatter, `ticket_id` missing or its embedded date before
   `TAG_TAXONOMY_EFFECTIVE_DATE` (2026-07-04), and empty/missing `tags` — returning `(included,
   skip_reasons, skipped_paths)`. `build_tag_rows(included)` aggregates a `Counter` per tag, sorts
   by count desc then tag asc, classifies each tag via `categorize_tag()` (Phase/Milestone via
   `^phase-\d+$`, Process/Skill-signal via the 4-tag table in `ticket_tagging.md`, Subsystem/Topic
   via `registry_query.SEED_TAGS`, Quality-attribute via the 4 worked examples in
   `tag_taxonomy.md`, else `unclassified`), and separately flags non-canonical tag usage by
   mirroring `validate_frontmatter._check_tags`'s rules (`_is_non_canonical`). All frontmatter
   parsing and taxonomy constants are imported from `validate_frontmatter.py`; the Subsystem/Topic
   seed list is imported from `registry_query.py` — no third hand-copy. CLI supports `--json
   <path>`, `--show-tickets`, and `--list-skipped`.
2. **`tests/tools/test_tag_report.py`** (new): 15 tests covering all 5 `categorize_tag` categories,
   all 3 skip rules individually plus the "no `tickets/done/`" edge case, subfolder recursion,
   `SEQUENCE.md` skipping, count aggregation/sort order, and non-canonical-tag flagging (uppercase,
   underscore, forbidden-priority, known-synonym) — using `tmp_path` fixtures, no dependency on the
   live corpus (mirrors `test_registry_query.py`'s style).
3. **`Makefile`**: added `tag-report` target (`python3 tools/tag_report.py $(ARGS)`) alongside
   `docs-registry`, and added `tag-report` to the `.PHONY` list.

**Live-repo run** (informational, not part of Acceptance Criteria): 1044 `.md` files scanned under
`tickets/done/`; 1002 skipped as pre-taxonomy/legacy `ticket_id`, 12 as `SEQUENCE.md`, 3 as
no-frontmatter; 27 included, spanning 36 unique tags. The tool's own non-canonical diagnostic
correctly caught a real live issue: `simulation_quality` (underscore form) used on 2 tickets
(`TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`, `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`) —
disclosed here, not fixed; retagging historical tickets is explicitly Out of Scope for this ticket.

## Test Summary
`pytest tests/tools/test_tag_report.py tests/tools/test_registry_query.py
tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -v` → 121 passed, 0
failed (15 new + 106 existing, no regressions). Also manually verified `--json` output round-trips
correctly (`included_tickets`, `tags`, `skipped` keys match the stdout report) and the plain
`python3 tools/tag_report.py` invocation against the live repo (see Implementation Notes).

## Files Changed
- `tools/tag_report.py` (new)
- `tests/tools/test_tag_report.py` (new)
- `Makefile` (added `tag-report` target + `.PHONY` entry)
- `tickets/inprogress/TCK-20260706-TAG-REPORT-TOOL.md` → `tickets/done/TCK-20260706-TAG-REPORT-TOOL.md`
- No `docs/` changes (explicitly out of scope; no `make knowledge-index-update` needed).

## Completion Summary
Added `tools/tag_report.py`, a standalone read-only reporting tool that counts tag usage across
`tickets/done/`, skipping tickets that predate the `docs/guidelines/tag_taxonomy.md` enforcement
cutoff (2026-07-04) or carry no tags, and classifying included tags into the taxonomy's 4
categories (or `unclassified`) plus a non-canonical-tag diagnostic. Reuses
`validate_frontmatter.py`'s frontmatter parser and taxonomy constants and `registry_query.py`'s
`SEED_TAGS`, per this repo's existing same-package import convention — no duplicated logic. 15 new
tests, 121/121 combined regression passed. A `tag-report` Makefile target was added. No `src/`
changes, no architecture impact, no parity-ledger entry needed (agent-orchestration/developer
tooling only).
