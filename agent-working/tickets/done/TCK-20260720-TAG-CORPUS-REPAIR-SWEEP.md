---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
phase: done
date: 2026-07-20
tags: [tagging, data-quality, reporting]
---

# TCK-20260720-TAG-CORPUS-REPAIR-SWEEP

## Title
Build a report-only legacy corpus repair-sweep tool for tag/category violations

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Enforcement of tag rules is forward-only from 2026-07-04, leaving a large, never-checked historic gap. Build a report-only sweep, extending tag_report.py's existing corpus-walk and frontmatter parser (no second parser, no per-file agent/LLM reads due to context cost), covering the full corpus (tickets/done, tickets/inprogress, tickets/todos/**, stored_artifacts/**). For every tag in every file's frontmatter it should flag unregistered tags, tags whose recorded category doesn't resolve in the new category registry, and non-canonical-form tags that predate enforcement. It must not auto-fix or rewrite any historic file — output is a list of (file, tag, issue) rows; deciding what to do with findings is left to a human or a follow-up ticket.

## Scope
- Extend tag_report.py's existing corpus-walk into a new non-cutoff-gated sweep across tickets/done/**, tickets/inprogress/**, tickets/todos/**, and stored_artifacts/**.
- Reuse validate_frontmatter.py's extract_frontmatter() as the sole parser — no second parser, no per-file LLM reads.
- Call tag_registry.py's canonical_form_violation/is_tag_registered/check_tags_registered/load_registry as the single source of truth for flagging.
- Emit (file, tag, issue) rows for unregistered, invalid_category, and non_canonical_form cases; report-only, no writes.
- Add a new subsection to docs/guides/ticket_reporting.md describing this sweep (its scope, corpus coverage, and report-only nature), following the same "Pillar" documentation pattern that section already uses for tag_report.py.

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch).
- Auto-fixing or rewriting any historic file — no --fix flag; deciding what to do with findings is left to a human or a follow-up ticket.
- Re-deriving tag validation rules independently of tag_registry.py's existing functions.

## Acceptance Criteria
- [ ] The sweep walks tickets/done/**, tickets/inprogress/**, tickets/todos/** (skipping SEQUENCE.md at every level, same as collect_completed_tickets' existing skip) and stored_artifacts/**/*.md, parsing via extract_frontmatter() only, and does NOT apply the pre_taxonomy_or_legacy_ticket_id date-cutoff skip — pre-2026-07-04 files are included.
- [ ] For every tag found, a (file, tag, issue) row is emitted per applicable case: unregistered (not in registry, not canonical phase-N) -> 'unregistered'; registered but recorded category not in the current valid-category set -> 'invalid_category'; canonical_form_violation(tag) is not None -> 'non_canonical_form'; a tag with multiple issues produces multiple rows.
- [ ] Files with no frontmatter or no tags key produce zero rows, not a crash (verified against real fixtures: stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md and stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md).
- [ ] Running the sweep against the real corpus produces zero filesystem writes (git-diff-clean before/after) — output is stdout/JSON rows only, no --fix flag exposed.
- [ ] The exact intended semantics of the 'invalid_category' flag are confirmed during this ticket's own Scope phase rather than assumed, given no direct precedent and possibly zero real hits today.
- [ ] docs/guides/ticket_reporting.md has a new subsection describing this sweep, mirroring the documentation depth already given to tag_report.py's Pillar 1.

## Related Tickets
- TCK-20260706-TAG-REPORT-TOOL
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260704-TAG-TAXONOMY
- TCK-20260719-TAG-COLLISION-DEDUP
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guidelines/tag_registry.jsonl
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_report.py
- tools/tag_registry.py
- tools/validate_frontmatter.py
- tests/tools/test_tag_report.py
- tests/tools/test_tag_registry.py

## Assumptions / Open Questions
- Full corpus size confirmed: tickets/done has 1199 .md files, tickets/inprogress 0, tickets/todos 20 (4 SEQUENCE.md-bearing subfolders), stored_artifacts 2735 .md files across 814 ticket-id directories (~3954 total) — a non-cutoff-gated scan will surface far more rows than the 185-violation baseline previously measured only on tickets/done post-taxonomy; needs a sane CLI/JSON output shape.
- 22% of stored_artifacts .md files sampled (601/2730) have no tags: frontmatter field, some have no frontmatter block at all — the sweep must tolerate both as 'nothing to flag'.
- TCK-20260719-TAG-COLLISION-DEDUP already ran an ad-hoc (not checked into tools/) full-corpus scan finding 1352 distinct tags as of 2026-07-19 — useful sizing precedent but a one-time manual-fix action, not a substitute for this reusable tool.
- docs/guides/ticket_reporting.md's Pillar 1 section documents tag_report.py's current narrower scope and needs a new subsection once this sweep exists.
- Layer chosen as `ai` (Claude agent/orchestration tooling) since this is a workflow-tooling build against tools/tag_report.py, not a gameplay subsystem; no better-fitting registered layer was found.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260720-TAG-CORPUS-REPAIR-SWEEP/plan.md`'s 6 steps, in order:

1. **`collect_sweep_files(root)`** added to `tools/tag_report.py`, directly below
   `collect_completed_tickets()`. Walks `tickets/done`, `tickets/inprogress`, `tickets/todos`,
   `stored_artifacts` via `.rglob("*.md")`, silently skipping a root that doesn't exist, sorting
   the combined file list, and applying only the `sequence_index_file` skip. No frontmatter parse,
   no tags check, no date-cutoff check at this stage. Returns
   `(relative_paths, skip_reasons, skipped_paths)`.
2. **`tag_issues(tag, registry, valid_categories)`** added to `tools/tag_report.py` in a new
   "Sweep violation classification" section placed right after `categorize_tag()`. Implements the
   resolved semantics from `investigation.md` verbatim: `unregistered` / `invalid_category`
   mutually exclusive by construction (if/elif), `non_canonical_form` independent (separate `if`).
   Imports `is_tag_registered` and `category_values` from `tag_registry.py` alongside the existing
   `canonical_form_violation`/`is_phase_milestone_tag`/`load_registry` imports.
3. **`sweep_file_rows(rel_path, text, registry, valid_categories)`** added directly after
   `tag_issues()`. Calls `extract_frontmatter()` inside a `try/except ValueError` returning `[]` on
   unparseable frontmatter (an explicit, disclosed extension beyond the two named AC #3 fixtures,
   flagged as such in `plan.md`'s Anti-Drift Notes). Returns `[]` for `fm is None` or missing/
   non-list `tags`. Never reads `ticket_id`.
4. **`tools/tag_corpus_sweep.py`** (new file) — `run_sweep(root)` orchestrates
   `load_registry`/`category_values`/`collect_sweep_files`/`sweep_file_rows`, returning
   `{rows, scanned_files, skipped, issue_counts}`. `print_report()` prints scanned/skipped counts,
   then per-issue-type counts, then one tab-separated `(file, tag, issue)` line per row (chosen
   over the fixed-width table `tag_report.py`'s own `print_report` uses, since tab-delimited rows
   are unambiguous to parse back out for the stdout/JSON row-count-agreement test). `build_json_report()`
   wraps the same dict with a `generated` UTC timestamp.
5. **`main()`** in `tools/tag_corpus_sweep.py` — `argparse` with only `--root` and `--json`, no
   `--fix`/`-f`/any write-triggering flag defined anywhere in the parser. `tools/tag_report.py`'s
   own `main()`/CLI wiring was not touched at all (zero-diff surface confirmed: `git diff` on that
   region shows only the import-block and new-function additions, no change inside `main()`,
   `print_report()`, or `build_json_report()`).
6. **`docs/guides/ticket_reporting.md`** — added "Pillar 3: Legacy Corpus Tag/Category Repair
   Sweep" after Pillar 2 and before "Related docs," matching Pillar 1/2's `**Tool:**` /
   `### What it does` / `### Quick start` / `### Technical detail` structure plus a dated live
   snapshot line (run for real against the actual repo during this Test phase: 4145 files scanned,
   37 `SEQUENCE.md` skips, 7832 violation rows — 7002 `unregistered`, 830 `non_canonical_form`, 0
   `invalid_category`, matching investigation.md's prediction of zero real `invalid_category` hits
   today). Fixed the pre-existing stale `docs/guidelines/tag_registry.jsonl` link in Pillar 1
   (line 31) to `../../registries/tag_registry.jsonl`, per the plan's in-scope Design Decision.
   Also updated the guide's intro paragraph from "two pillars" to "three pillars" (not itself
   Pillar 1/2 prose, so within the plan's Do-Not-Touch boundary).

Tests: `tests/tools/test_tag_corpus_sweep.py` (new, 20 tests — 15 required by `test_plan.md` plus
5 additional negative/regression cases covering the same behavior from a second angle, e.g. a
direct `sweep_file_rows`-level date-cutoff test alongside the `collect_sweep_files`-level one, and
an unparseable-frontmatter crash-tolerance case for the deliberate `ValueError` extension in step
3). All pass. Full regression surface named in `test_plan.md`
(`test_tag_corpus_sweep.py` + `test_tag_report.py` + `test_tag_registry.py` +
`test_tag_category_registry.py` + `test_validate_frontmatter.py` + `test_layer_registry.py`) —
182 tests, all pass, none modified.

No deviations from `plan.md` beyond the one already disclosed in the plan itself (the
`ValueError`/malformed-frontmatter catch in `sweep_file_rows`, which the plan's own Anti-Drift
Notes section flags as a deliberate, narrow extension rather than an undisclosed deviation).

## Test Summary

`pytest tests/tools/test_tag_corpus_sweep.py tests/tools/test_tag_report.py tests/tools/test_tag_registry.py tests/tools/test_tag_category_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_layer_registry.py -q`
→ 182 passed, 0 failed. `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260720-TAG-CORPUS-REPAIR-SWEEP.md` → OK. Manually ran
`python3 tools/tag_corpus_sweep.py --root .` against the real repo tree and confirmed
`git status --porcelain` output identical before/after (also covered by
`test_sweep_against_real_corpus_produces_zero_filesystem_writes`, a subprocess test against the
live repo).

## Files Changed

- `tools/tag_report.py` — added `collect_sweep_files()`, `tag_issues()`, `sweep_file_rows()`;
  extended the `tag_registry` import line with `category_values`, `is_tag_registered`
- `tools/tag_corpus_sweep.py` — new file: `run_sweep()`, `print_report()`, `build_json_report()`,
  `main()`
- `tests/tools/test_tag_corpus_sweep.py` — new file, 20 tests
- `docs/guides/ticket_reporting.md` — new Pillar 3 subsection; fixed stale Pillar 1 registry link;
  intro paragraph pillar count updated

## Completion Summary

Built a report-only, non-cutoff-gated tag/category violation sweep covering the full ticket and
artifact corpus (`tickets/done/**`, `tickets/inprogress/**`, `tickets/todos/**`,
`stored_artifacts/**/*.md`), closing the gap left by `tag_report.py`'s forward-only,
`tickets/done/`-only enforcement. The corpus walk and per-tag/per-file classification live as new
functions in `tools/tag_report.py` (`collect_sweep_files`, `tag_issues`, `sweep_file_rows`),
reusing `extract_frontmatter()` and `tag_registry.py`'s existing rule functions with no
re-derivation; the CLI/orchestration lives in a new, wholly separate module,
`tools/tag_corpus_sweep.py`, so `tag_report.py`'s own CLI surface is untouched (confirmed by its
15 existing tests passing unmodified). The tool is structurally write-free — no `--fix` flag
exists in the parser, and no `Path.write_text` call touches any file under `tickets/` or
`stored_artifacts/` anywhere in the new code, verified by a subprocess test that diffs
`git status --porcelain` before/after a real invocation against the live repo. All 6 acceptance
criteria are met and covered by tests; `docs/guides/ticket_reporting.md` documents the new tool as
Pillar 3, matching Pillar 1's documentation depth, and also fixes a pre-existing stale registry
link in Pillar 1 while the file was already open for the adjacent edit.
