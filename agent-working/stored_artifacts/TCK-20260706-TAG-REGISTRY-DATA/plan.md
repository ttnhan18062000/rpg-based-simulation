---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-TAG-REGISTRY-DATA
artifact_type: plan
tags: [tagging, taxonomy, reporting]
---

# Plan — TCK-20260706-TAG-REGISTRY-DATA

## Steps

1. **New module `tools/tag_registry.py`** — owns the durable data model:
   - `docs/guidelines/tag_registry.jsonl`, one JSON object per line, one tag per line, never
     rewritten: `{"tag", "category", "added_date", "note"}`.
   - Taxonomy constants moved here from `validate_frontmatter.py`: `TAG_TAXONOMY_EFFECTIVE_DATE`,
     `FORBIDDEN_PRIORITY_TAGS`, `TAG_SYNONYM_MAP`.
   - New: `ALL_CATEGORIES` (5 values) / `ADDABLE_CATEGORIES` (4 — excludes `phase-milestone`,
     which is pattern-recognized, never registered).
   - `canonical_form_violation(tag)` — pure function, extracted from `_check_tags`'s inline loop.
   - `load_registry(root=None)`, `is_tag_registered(tag, registry)`,
     `is_phase_milestone_tag(tag)`, `add_tag(tag, category, note, root=None)`.
   - CLI: `add` (register, refuses duplicates/bad category/bad form), `list` (print all).

2. **Import Direction Decision** (avoiding a cycle): `tag_registry.py` has zero dependency on
   `validate_frontmatter.py` or `tag_report.py`. `validate_frontmatter.py` imports from
   `tag_registry.py` (constants + `canonical_form_violation` + `load_registry` +
   `is_tag_registered`), re-exporting them so existing `from validate_frontmatter import
   FORBIDDEN_PRIORITY_TAGS`-style imports (used by tests and `tag_report.py`) keep working
   unchanged. `tag_report.py` imports from both `validate_frontmatter.py` (frontmatter parsing) and
   `tag_registry.py` (registry + canonical-form check). Net: a clean DAG,
   `tag_registry.py` ← `validate_frontmatter.py` / `tag_report.py`, no cycle.

3. **`tools/validate_frontmatter.py` changes:**
   - `_check_tags(filepath, fm, registry=None)` — canonical-form check first (via
     `canonical_form_violation`), then registry-membership check only if `registry` is not `None`
     (backward compatible: every existing test that doesn't pass a registry keeps its old
     behavior).
   - Thread `registry` through `_validate_ticket`/`_validate_artifact`/`_validate_doc`/
     `_validate_archive` (doc/archive ignore it, kept for uniform `_VALIDATORS` dispatch),
     `validate_file`, `validate_directory`.
   - `main()` loads the real registry via `load_registry()` (defaults to the real repo path
     regardless of cwd) and passes it through — so actual CLI/CI runs enforce the allowlist, while
     direct unit-test calls to `validate_file()`/`_check_tags()` without a registry argument are
     unaffected.

4. **`tools/tag_report.py` changes:**
   - Remove `PROCESS_SKILL_TAGS`, `QUALITY_ATTRIBUTE_EXAMPLE_TAGS`, and the
     `registry_query.SEED_TAGS` import — replaced entirely by a registry lookup.
   - `categorize_tag(tag, registry)`: `phase-milestone` by pattern, else `registry.get(tag)`'s
     `category`, else `unclassified`.
   - `build_tag_rows(included, registry)`: thread registry through; replace the local
     `_is_non_canonical` reimplementation with `tag_registry.canonical_form_violation`.
   - `main()`: `load_registry(root)` once, pass to `build_tag_rows`.

5. **Seed the registry** by calling the real `tools/tag_registry.py add` CLI once per tag
   (dogfooding the add path end-to-end, not writing the JSONL by hand) — every tag currently in use
   across post-cutoff `tickets/done/`, categorized per investigation.md's evidence.

6. **Verification before declaring done** (see test_plan.md): re-run `tag_report.py` after seeding
   to confirm 0 unexpected `unclassified` tags (any newly-discovered gap gets registered, not
   ignored); `git stash` + `validate_frontmatter.py tickets/done` diff to confirm zero new
   regressions from turning on the hard allowlist.

7. **Tests:**
   - New `tests/tools/test_tag_registry.py`: canonical-form rule, phase-tag bypass, `load_registry`
     (missing file, parses entries, skips blanks, raises on duplicate), `add_tag` (appends,
     rejects non-canonical/bad-category/`phase-milestone`-as-category/duplicate, append-only —
     existing entries untouched by a later add).
   - Update `tests/tools/test_tag_report.py`: `categorize_tag` tests now pass an explicit small
     in-memory registry instead of relying on hardcoded heuristic sets; `build_tag_rows` tests pass
     a registry argument.
   - Update `tests/tools/test_validate_frontmatter.py`: new `TestTagRegistryEnforcement` class —
     registered tag accepted, unregistered tag rejected (with the expected CLI-hint message),
     `phase-N` accepted without registration, canonical-form violation reported before (not
     alongside) a registry-membership violation, registry check skipped when `registry` argument
     omitted (documents the backward-compat contract explicitly), artifact content-type also
     enforced, pre-taxonomy ticket stays exempt regardless of registry.
   - No changes needed to `tests/tools/test_generate_registry.py`,
     `tests/tools/test_registry_query.py`, or `tests/tools/test_add_frontmatter_tickets.py` — none
     of their fixtures use post-cutoff `ticket_id`s with tags, confirmed by reading each before
     touching anything.

8. **Docs:**
   - `docs/guidelines/tag_taxonomy.md`: revise Purpose (registry now exists, no longer "not a
     frozen enumeration"), add `Meta-Process` category + disambiguation rule, add a new "Tag
     Registry" section (why/how/append-only/CLI usage/phase-N exemption), revise Enforcement to
     describe the 2-step check (canonical form, then registry membership) and cite the
     zero-regression verification result, add a disclosed-not-decided note on `bug`/`## Type`
     redundancy (flagged, not resolved, per Uncertainty Rule).
   - `docs/guides/ticket_tagging.md`: "4 Categories" → "5 Categories" table, new "Registering a New
     Tag" section with the CLI walkthrough.
   - `docs/guides/ticket_reporting.md`: Pillar 1's classification table and legacy-context numbers
     updated to reflect registry-based lookup and the refreshed live snapshot (2 new tickets were
     created in this same session by the prior two tickets, changing scanned/included counts).
   - `make docs-registry` + `make knowledge-index-update` (docs changed).

## Out of scope (explicitly)

- Rewiring `tools/registry_query.py`'s `SEED_TAGS` to derive from the new registry instead of its
  own hardcoded 10-word tuple — real potential follow-up (would fix the "two copies kept in sync by
  hand" issue disclosed in `TCK-20260705-TAG-REGISTRY-QUERY`), but touches `create-tickets.js` /
  `investigator.md` consumers, a larger blast radius than this ticket's scope. Disclosed as a
  follow-up opportunity, not built here.
- Deciding whether `bug`/`feature`/`refactor`/`chore`/`repair` tags should become forbidden
  (mirroring `p0`/`p1`/`p2`) for duplicating the `## Type` field — flagged in `tag_taxonomy.md`,
  left for a future decision since forbidding retroactively would break 3 existing tickets.
- Retagging the 2 tickets still using non-canonical `simulation_quality` — disclosed, not fixed,
  consistent with the prior tag-report ticket's same disclosed-not-fixed item.
