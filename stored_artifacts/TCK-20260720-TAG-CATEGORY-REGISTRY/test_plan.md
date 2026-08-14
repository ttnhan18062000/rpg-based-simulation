---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CATEGORY-REGISTRY
artifact_type: test_plan
tags: [tagging, frontmatter, taxonomy]
---

# Test Plan — TCK-20260720-TAG-CATEGORY-REGISTRY

## Regression Surface

**Unit — `tools/tag_registry.py` and direct consumers:**
- `tests/tools/test_tag_registry.py` — all 25 existing tests, most critically:
  - `test_add_tag_rejects_invalid_category` (still must raise `ValueError` for
    `"not-a-real-category"`)
  - `test_add_tag_rejects_phase_milestone_category` (must be updated in place — see New Tests —
    but the *behavior* it protects, `add_tag(..., "phase-milestone", ...)` raising `ValueError`,
    must keep passing)
  - `test_add_tag_appends_entry_and_returns_it`, `test_add_tag_is_append_only_existing_entries_
    unchanged`, `test_add_tag_rejects_duplicate_tag`, `test_add_tag_rejects_non_canonical_tag` —
    unaffected by the category-source change, must still pass unchanged
  - `test_get_skill_mapping_*`, `test_legacy_skill_triggers_*`, `test_check_tags_registered_*` —
    unrelated to categories, must still pass unchanged (proves no collateral breakage from the
    `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` removal)
- `tests/tools/test_layer_registry.py` — all 19 existing tests, unchanged (this ticket does not
  touch `layer_registry.py`'s own logic, only uses it as a structural template)
- `tests/tools/test_validate_frontmatter.py` — full file, especially any `TestEnumAntiDrift`-style
  tests and `_check_tags`-related tests — confirms `validate_frontmatter.py` (which does not
  reference tag categories at all per investigation.md) continues to import
  `FORBIDDEN_PRIORITY_TAGS`/`TAG_SYNONYM_MAP`/`TAG_TAXONOMY_EFFECTIVE_DATE`/
  `canonical_form_violation`/`is_tag_registered`/`load_registry` from `tag_registry.py` correctly
  after those names' surrounding module content changes
- `tests/tools/test_tag_report.py` — full file; `categorize_tag()` must keep returning the same
  values (`"phase-milestone"` for pattern-matched tags, real category string for registered tags,
  `"unclassified"` otherwise) — proves `tag_report.py` (Out of Scope for edits) is unaffected
- `tests/tools/test_generate_retro.py` — full file; the `category == "subsystem-topic"` /
  `category == "process-skill-signal"` string-equality checks in `generate_retro.py` must keep
  working unchanged
- `tests/tools/test_agent_ops_dashboard_ingest.py` — full file; confirms the dashboard's
  `tag_registry.load_registry(...).keys()`-based tag facet (from
  `TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY`) is unaffected by the category-source refactor

**Integration / CLI:**
- `python3 tools/tag_registry.py list` and `python3 tools/tag_registry.py add <tag> --category
  <cat> --note "..."` against a scratch `--root` — confirms the CLI still round-trips correctly
  post-refactor (manual smoke check, not a new automated test, since existing tests already cover
  `add_tag()`/`load_registry()` at the function level)
- `python3 tools/validate_frontmatter.py <path>` over a sample ticket/artifact file — confirms
  frontmatter validation (layer/status/tags membership) is unaffected

## New Tests Required

Per Acceptance Criteria:

1. **Test name:** `test_tag_category_registry.py` (whole new file, ~19-23 tests mirroring
   `tests/tools/test_layer_registry.py`'s 9-section structure 1:1, adapted for `category` instead
   of `layer`)
   **Category:** unit
   **What it verifies:** Full lifecycle of the new `registries/tag_category_registry.jsonl` +
   `add_category()`/`category_values()` pair:
   - `canonical_form_violation()` (if `add_category()` reuses/mirrors `tag_registry.py`'s own
     `canonical_form_violation()` rather than defining a category-specific one — clarify which in
     Plan; if reused, this sub-block may be redundant with existing `test_tag_registry.py`
     canonical-form tests and can be a thin cross-check instead of a full duplicate)
   - `is_category_registered()`-equivalent behavior (true for registered, false for unregistered) —
     only needed if such a helper is added; not explicitly required by the AC, flag in Plan whether
     to include for full `layer_registry.py` structural parity or omit as unused surface
   - `load_registry()`: missing file → `{}`; reads entries; skips blank lines; raises `ValueError`
     on duplicate category registration (mirrors
     `test_load_registry_raises_on_duplicate_layer`/`_tag`)
   - `add_category(category, note, root=None)`: appends entry and returns it; entry has no
     `category`-of-a-category field (i.e., no unexpected nesting) — has `{"category",
     "added_date", "note"}` only, matching `add_layer()`'s exact shape (assert `"category" in
     entry`, no stray keys); rejects non-canonical category name (`ValueError`, message contains
     "canonical form"); rejects duplicate category (`ValueError`, message contains "already
     registered"); append-only — two `add_category()` calls leave both entries' `note` fields
     independently correct (mirrors `test_add_layer_is_append_only_existing_entries_unchanged`)
   - `category_values(root=None)`: returns a `frozenset[str]`; matches exactly what was added in a
     `tmp_path` fixture (mirrors `test_layer_values_returns_frozenset_of_registered_layers`); **and
     a real-registry pin test** — `category_values() == frozenset({"subsystem-topic",
     "process-skill-signal", "quality-attribute", "meta-process"})` against the actual seeded
     `registries/tag_category_registry.jsonl` (no `root` override), mirroring
     `test_layer_values_matches_real_seeded_registry` exactly — this is the test that catches any
     seeding typo/omission/extra-category mistake
   - **`"phase-milestone" not in category_values()`** — explicit assertion that the registry file
     was NOT seeded with `phase-milestone`, directly encoding this investigation's resolved 4-vs-5
     design decision as a regression guard (see Anti-Drift Test Guards below)
   **Where it lives:** `tests/tools/test_tag_category_registry.py`

2. **Test name:** `test_add_tag_rejects_phase_milestone_category` (existing test, updated in
   place — not a new test, but its assertions must change since `ALL_CATEGORIES` goes away)
   **Category:** unit (regression guard, updated)
   **What it verifies:** `add_tag("some-tag", "phase-milestone", root=tmp_path)` still raises
   `ValueError` with a "category must be one of ..." message, now because `"phase-milestone"` is
   absent from `category_values()` rather than absent from `ADDABLE_CATEGORIES`. Update the
   `assert "phase-milestone" not in ADDABLE_CATEGORIES` / `assert "phase-milestone" in
   ALL_CATEGORIES` lines (test_tag_registry.py:164-165) to `assert "phase-milestone" not in
   category_values()` (drop the `ALL_CATEGORIES` assertion entirely — that name no longer exists
   per Scope bullet 4) and update the import block (test_tag_registry.py:14-26) to drop
   `ADDABLE_CATEGORIES, ALL_CATEGORIES` and add `category_values`.
   **Where it lives:** `tests/tools/test_tag_registry.py`

3. **Test name:** `test_add_tag_category_validation_sources_from_category_values` (new)
   **Category:** unit / architecture guard
   **What it verifies:** `add_tag()`'s category check is genuinely live-sourced, not a residual
   hardcoded copy — e.g. register a new category via `add_category("new-cat", root=tmp_path)`
   against the *same* `tmp_path` root `add_tag` is later called with, then confirm
   `add_tag("some-tag", "new-cat", root=tmp_path)` succeeds without any code change. This is the
   single most important new test: it is the only one that actually proves `add_tag()` stopped
   reading a frozen Python literal and started reading the registry file live (the AC's "source
   add_tag()'s category validation... from category_values()" requirement). Without this test, a
   regression that silently re-hardcodes `ADDABLE_CATEGORIES` inside `add_tag()` (defeating the
   whole point of the ticket) would not be caught by any existing or planned test.
   **Where it lives:** `tests/tools/test_tag_registry.py`

4. **Test name:** `test_argparse_category_choices_match_category_values` (new)
   **Category:** unit / architecture guard
   **What it verifies:** The CLI's `add` subcommand's `--category` argparse `choices` are built
   from `category_values()`, not a stale literal — e.g. invoke `main()`'s argument parser
   construction (or inspect `sub.choices`/`add_p` if `main()` is refactored to expose the parser
   separately) and assert the choices set equals `category_values()` against the real repo
   registry. Mirrors the spirit of AC's "argparse --category choices... source from
   category_values()" bullet. If `main()`'s parser isn't easily introspectable without invoking the
   CLI, an acceptable alternative is a subprocess-based CLI smoke test
   (`python3 tools/tag_registry.py add x --category not-a-real-category` → nonzero exit,
   `stderr` contains the live category list) — decide the exact mechanism in Plan based on how
   `test_tag_registry.py` already tests (or doesn't test) the CLI layer today (current file has no
   CLI-level tests — all tests call functions directly).
   **Where it lives:** `tests/tools/test_tag_registry.py`

## Scoped Pytest Commands

```bash
# Primary scope: tag/layer/category registry tooling and its direct doc-validation consumer
pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py \
       tests/tools/test_tag_category_registry.py tests/tools/test_validate_frontmatter.py -v

# Secondary scope: downstream consumers that read categories (tag_report, retro, dashboard)
pytest tests/tools/test_tag_report.py tests/tools/test_generate_retro.py \
       tests/tools/test_agent_ops_dashboard_ingest.py -v

# Combined single run for final verification before Verify phase
pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py \
       tests/tools/test_tag_category_registry.py tests/tools/test_validate_frontmatter.py \
       tests/tools/test_tag_report.py tests/tools/test_generate_retro.py \
       tests/tools/test_agent_ops_dashboard_ingest.py -v
```

Never `pytest tests/` — scoped strictly to `tests/tools/` files that import from or exercise
`tag_registry.py`, `layer_registry.py`, `validate_frontmatter.py`, `tag_report.py`,
`generate_retro.py`, or the dashboard ingest facet built on `tag_registry.load_registry()`.
`tools/ticket_stats_report.py` and its test (`tests/tools/test_ticket_stats_report.py`, if it
exists) are intentionally excluded — investigation confirmed zero tag-category coupling there.

## Anti-Drift Test Guards

- **`"phase-milestone" not in category_values()`** (item 1 above) — directly guards against the
  5-category seeding mistake; if a future change (or an over-eager implementer) seeds
  `phase-milestone` into the registry "for completeness," this test fails immediately, forcing the
  resolved design decision in investigation.md to be revisited deliberately rather than drifted
  into silently.
- **`test_add_tag_category_validation_sources_from_category_values`** (item 3) — guards against the
  most likely silent-regression path: someone "converts" the registry file but leaves `add_tag()`
  checking a leftover local `ADDABLE_CATEGORIES` constant (forgetting to delete it per Scope bullet
  4), which would make the registry file cosmetic rather than authoritative. No existing test
  catches this because no existing test registers a *new* category at runtime and confirms
  `add_tag()` immediately honors it.
- **`test_categorize_tag_looks_up_registry_category`** (existing, `tests/tools/test_tag_report.py`)
  and the `generate_retro.py`-facing tests in `test_generate_retro.py` — re-run unchanged as
  regression guards proving the explicitly-Out-of-Scope files (`tag_report.py`,
  `generate_retro.py`) were not touched in a way that changes their behavior, even incidentally
  (e.g. via a shared import surface change in `tag_registry.py`).
- **Full existing `test_tag_registry.py` suite minus the one updated test** — re-run as a guard
  that `ADDABLE_CATEGORIES`/`ALL_CATEGORIES` removal has zero effect on tag-registration behavior
  itself (canonical-form rules, duplicate rejection, `triggers_skill`, `check_tags_registered`) —
  none of that logic should need to change, and any failure there signals unintended collateral
  scope creep into unrelated `tag_registry.py` logic.
- **`test_layer_registry.py`'s full suite, re-run unmodified** — guards that using
  `layer_registry.py` purely as a *read-only structural template* did not accidentally lead to any
  edit of `layer_registry.py` itself (Out of Scope — this ticket only adds a *new*, structurally
  similar module/file, it does not modify the existing layer registry).
