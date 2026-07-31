---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-CATEGORY-REGISTRY
phase: done
date: 2026-07-20
tags: [tagging, frontmatter, taxonomy]
---

# TCK-20260720-TAG-CATEGORY-REGISTRY

## Title
Make tag categories registry-backed via a new registries/tag_category_registry.jsonl, mirroring layer_registry.py

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Tag categories (ALL_CATEGORIES/ADDABLE_CATEGORIES) are currently a hardcoded Python set in tools/tag_registry.py, hand-duplicated across 7 non-test files. Create a new registries/tag_category_registry.jsonl seeded with the current addable categories, add an add_category() function mirroring add_tag(), and a category_values() function returning a live frozenset exactly like layer_registry.py's layer_values() already does for validate_frontmatter.py's LAYER_VALUES. validate_frontmatter.py and every other hardcoded-category consumer should import this live value instead of a literal set. phase-milestone stays exempt from registration, unchanged.

## Scope
- create registries/tag_category_registry.jsonl seeded via the real add_category() API (not hand-written), mirroring how layer_registry.jsonl was seeded through add_layer()
- add add_category(category, note, root=None) to tools/tag_registry.py, raising ValueError on non-canonical form and duplicate, identical shape to add_layer()
- add category_values(root=None) to tools/tag_registry.py returning a live frozenset[str] with no caching, exactly matching layer_values()'s implementation
- remove the ALL_CATEGORIES/ADDABLE_CATEGORIES set literal; source add_tag()'s category validation and the argparse --category choices from category_values()
- update test_tag_registry.py's category assertions and add a new test_tag_category_registry.py mirroring test_layer_registry.py's exact structure
- document the new `add-category` CLI command in docs/guidelines/tag_taxonomy.md's "Tag Registry" section and docs/guides/ticket_tagging.md's "Registering a New Tag" section, alongside the existing `add <tag>` documentation — this is a new capability, not covered by any existing doc today

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- rewriting prose-only category references in tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, generate_retro.py to "import a live value" — those files reference individual category name strings in prose or single string-equality checks, not a Python set, so no live-import mechanism applies to them; manual prose sync remains as today
- the physical relocation of the sibling registries out of docs/guidelines/ (handled by TCK-20260720-TAG-REGISTRY-RELOCATE, which this ticket depends on)

## Acceptance Criteria
- [ ] registries/tag_category_registry.jsonl is seeded with exactly the current addable categories (subsystem-topic, process-skill-signal, quality-attribute, meta-process), one JSON object per line, written via the real add_category() API
- [ ] tools/tag_registry.py gains add_category(category, note, root=None), raising ValueError on non-canonical form and duplicate, identical shape to add_layer()
- [ ] tools/tag_registry.py gains category_values(root=None) returning a live frozenset[str], no caching, exactly matching layer_values()'s implementation
- [ ] the ADDABLE_CATEGORIES set literal is removed; add_tag()'s category validation and the argparse --category choices both source from category_values(); phase-milestone stays naturally excluded since it is never seeded in the registry file
- [ ] test_tag_registry.py's category references are updated and a new test_tag_category_registry.py mirrors test_layer_registry.py's 9-test structure
- [ ] docs/guidelines/tag_taxonomy.md and docs/guides/ticket_tagging.md document the new `add-category` CLI command with the same level of detail as the existing `add <tag>` documentation
- [ ] during this ticket's own Investigate phase, the open design question of whether the registry seeds all 5 categories (with phase-milestone marked non-addable) versus only the 4 currently-addable categories (with phase-milestone remaining purely code-side exempt via is_phase_milestone_tag()) is explicitly resolved and documented — not pre-decided by this synthesis

## Related Tickets
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/ticket_reporting.md
- CLAUDE.md
- docs/guidelines/layer_registry.jsonl
- docs/guidelines/tag_registry.jsonl

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_registry.py
- tools/layer_registry.py
- tools/validate_frontmatter.py
- tools/ticket_stats_report.py
- tools/tag_report.py
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_layer_registry.py
- tests/tools/test_tag_registry.py

## Assumptions / Open Questions
- open design question: whether the registry seeds all 5 categories or only the 4 currently-addable ones — must be resolved during this ticket's Investigate phase, not assumed
- tag_registry.py becomes self-referential (defines category_values() and consumes it for its own add_tag() validation) — should be tested for import-order issues given validate_frontmatter.py already imports from tag_registry.py
- the registries/ (not docs/guidelines/) path is the intended deliberate deviation per the proposal, but the directory only exists once TCK-20260720-TAG-REGISTRY-RELOCATE lands

## Implementation Notes

Followed staging_artifacts/TCK-20260720-TAG-CATEGORY-REGISTRY/plan.md's 6 steps in order.

1. Added `_CATEGORY_REGISTRY_REL_PATH`, `category_registry_path()`, `load_category_registry()`,
   `is_category_registered()`, `category_values()` to `tools/tag_registry.py`, placed after
   `get_skill_mapping()` and before the `# CLI` section — a second, independent registry surface
   in the same file, keyed on `"category"` instead of `"tag"`, mirroring the existing tag-scoped
   I/O shape exactly.
2. Added `add_category(category, note="", root=None)` directly after the new loader/query
   functions, mirroring `add_layer()`'s body exactly (reuses the existing module-level
   `canonical_form_violation()` per the plan's Design Decision 1 — no duplicate regex). Entry
   schema is exactly `{"category", "added_date", "note"}`, `sort_keys=True` on write.
3. Added an `add-category` CLI subcommand (distinct from the existing `add` tag subcommand) with
   `category`, `--note`, `--root` arguments and a handling branch placed after the `add` block,
   before `list`.
4. Seeded `registries/tag_category_registry.jsonl` by running `python3 tools/tag_registry.py
   add-category <category> --note "..."` four times against the real repo root (subsystem-topic,
   process-skill-signal, quality-attribute, meta-process) — file is CLI-generated, not
   hand-written. `phase-milestone` deliberately not seeded (stays code-side, `is_phase_milestone_tag()`).
5. Removed the `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` set literals. Rewired `add_tag()`'s category
   check and the `add` subcommand's `--category` choices to source from `category_values()`
   (called with no root override — see Deviation note below). Updated
   `tests/tools/test_tag_registry.py`'s import block and `test_add_tag_rejects_phase_milestone_category`;
   added 2 new tests (`test_add_tag_category_validation_sources_from_category_values`,
   `test_argparse_category_choices_match_category_values`) plus a new
   `tests/tools/test_tag_category_registry.py` (16 tests) mirroring `test_layer_registry.py`'s
   9-section structure exactly, including an in-process `main()` CLI test with monkeypatched
   `sys.argv` (no subprocess), per the plan's Design Decision 3.
6. Documented `add-category` in `docs/guidelines/tag_taxonomy.md`'s "Tag Registry" section and
   `docs/guides/ticket_tagging.md`'s new "Registering a New Category" subsection, alongside the
   existing `add <tag>` documentation.

Did not touch `tools/validate_frontmatter.py` or `tools/ticket_stats_report.py` (scope guard, per
investigation.md — neither has any tag-category code today).

Scoped tests run: `pytest tests/tools/test_tag_registry.py tests/tools/test_tag_category_registry.py
tests/tools/test_layer_registry.py tests/tools/test_validate_frontmatter.py -q` — 149 passed, 0
failed.

`make knowledge-index-update` was **not** run by this implementer session — the plan itself flags
this as a Finalize-phase action, not part of Implement's own step verification; it must still run
before this ticket closes, since `docs/guidelines/tag_taxonomy.md` and `docs/guides/ticket_tagging.md`
were both modified.

## Test Summary

- `tests/tools/test_tag_registry.py` — 33 tests (2 new, 2 updated, rest unmodified), all pass.
- `tests/tools/test_tag_category_registry.py` — new file, 16 tests, all pass.
- `tests/tools/test_layer_registry.py` — 17 tests, unmodified, all pass (regression guard).
- `tests/tools/test_validate_frontmatter.py` — 83 tests, unmodified, all pass (confirms
  `validate_frontmatter.py`'s unrelated imports from `tag_registry.py` are unaffected).
- Manual CLI smoke test: `python3 tools/tag_registry.py add-category --help` and the 4 real
  seeding invocations (Step 4) all behaved as expected; `registries/tag_category_registry.jsonl`
  verified to contain exactly the 4 lines, untouched by any subsequent test run.

## Files Changed

- `tools/tag_registry.py`
- `tests/tools/test_tag_registry.py`
- `tests/tools/test_tag_category_registry.py` (new)
- `registries/tag_category_registry.jsonl` (new, CLI-generated)
- `docs/guidelines/tag_taxonomy.md`
- `docs/guides/ticket_tagging.md`

## Completion Summary

Converted tag categories from the hardcoded `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` Python set
literals in `tools/tag_registry.py` into a registry-file-backed live value
(`registries/tag_category_registry.jsonl`), mirroring `TCK-20260718-LAYER-REGISTRY-CONVERSION`'s
conversion of `layer:`. Added `add_category()`/`category_values()`/`load_category_registry()`/
`is_category_registered()`/`category_registry_path()` as a second, independent registry surface
inside the same module, plus an `add-category` CLI subcommand. The real registry file was seeded
via that CLI with exactly the 4 currently-addable categories (`phase-milestone` intentionally
excluded, staying pattern-recognized). `add_tag()`'s category validation and the CLI `add`
subcommand's `--category` choices now source live from `category_values()` instead of the removed
constants. All acceptance criteria met; observable CLI/validation behavior is unchanged
(`add_tag`/`validate_frontmatter` still accept exactly the same 4 categories, reject
`phase-milestone` the same way) — this is an internal mechanism swap, not a behavior change. One
deviation from the plan's literal text was needed and is documented in plan.md's Deviations
section: `add_tag()`'s category check calls `category_values()` with no root override (always
resolving against the real repo registry via `_DEFAULT_ROOT`), not `category_values(root)`,
because passing `root` through broke 8 pre-existing tests the plan explicitly required to stay
unmodified.
