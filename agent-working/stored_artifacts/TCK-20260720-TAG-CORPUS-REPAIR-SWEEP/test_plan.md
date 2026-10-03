---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
artifact_type: test_plan
tags: [tagging, data-quality, reporting]
---

# Test Plan — TCK-20260720-TAG-CORPUS-REPAIR-SWEEP

## Regression Surface

Existing tests that must keep passing unmodified (or with only additive changes — no behavior
change to any existing function signature's default path, per investigation.md's Anti-Drift
Hazards):

**Unit — tag/frontmatter tooling (the direct blast radius: this ticket only imports from these
modules, per Scope, and must not alter their existing behavior):**
- `tests/tools/test_tag_registry.py` — all 33 tests (`canonical_form_violation`,
  `is_tag_registered`, `check_tags_registered`, `load_registry`, `add_tag`, `category_values`,
  `load_category_registry`, `add_category`, skill-mapping tests). None of these functions are
  modified by this ticket (import-only), but they are the sweep's single source of truth and must
  stay green.
- `tests/tools/test_tag_category_registry.py` — all 16 tests (`load_category_registry`,
  `is_category_registered`, `add_category`, `category_values`) — the `invalid_category` check
  depends directly on `category_values()`'s behavior verified here.
- `tests/tools/test_validate_frontmatter.py` — all 83 tests (`extract_frontmatter`,
  `detect_content_type`, `validate_file`, `validate_directory`, the 4 content-type validators, the
  cutoff-date helper `_ticket_id_effective_date`). `extract_frontmatter` is the sole parser this
  ticket reuses (Scope-mandated) — must not regress.
- `tests/tools/test_tag_report.py` — all existing tests (`categorize_tag`,
  `collect_completed_tickets`, `build_tag_rows`). Confirms the ticket's extension does not disturb
  `tag_report.py`'s own narrower (`tickets/done/`-only, date-gated) behavior, even if the new sweep
  lives in the same file or imports shared helpers from it.

**Integration / architecture-guard adjacent:**
- `tests/tools/test_layer_registry.py` — unrelated in content, but shares the
  registry-file-append-only-pattern convention (`registries/*.jsonl`) this ticket's read path
  touches (`registries/tag_registry.jsonl`, `registries/tag_category_registry.jsonl`); include as a
  cheap regression guard that no accidental cross-module import breakage occurred.
- `tools/gate_checks/done_checker_static.py`'s `check_frontmatter_valid` — not a pytest target
  directly, but confirm (via `tests/tools/test_validate_frontmatter.py`'s directory-scan tests, and
  a manual `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260720-TAG-CORPUS-REPAIR-SWEEP.md`
  smoke check before Finalize) that this ticket's own frontmatter/tags stay valid under the existing
  (non-sweep) enforcement path — the sweep tool is new and separate from this gate, but must not be
  confused with it or accidentally wired into it (Out of Scope: "Wiring this report into any agent
  workflow, gate, or CI check" — inherited from `TCK-20260706-TAG-REPORT-TOOL`'s equivalent
  out-of-scope line and still applicable here by the same reasoning; not explicitly restated in this
  ticket's own Out of Scope section, so confirm this reading holds, or flag it, before treating any
  gate-wiring as in-bounds).

## New Tests Required

Per AC #1 (corpus walk, no date-gate), AC #2/#46 (three violation cases + multi-issue rows), AC #3
(no-frontmatter / no-tags tolerance against the two named real fixtures), AC #4 (zero writes), AC #5
(the `invalid_category` semantics are resolved — tested, not just documented):

1. **`test_sweep_walks_all_four_corpus_roots`**
   Category: unit.
   Verifies: given a `tmp_path` fixture tree with one tagged file under each of
   `tickets/done/`, `tickets/inprogress/`, `tickets/todos/`, `stored_artifacts/{id}/`, the sweep's
   collection function returns all four files represented in its output (by path), none silently
   dropped.
   Location: `tests/tools/test_tag_corpus_sweep.py` (new file, mirrors `test_tag_report.py`'s
   `tmp_path`-fixture style — no dependency on the live corpus).

2. **`test_sweep_skips_sequence_md_at_every_level`**
   Category: unit.
   Verifies: a `SEQUENCE.md` placed under `tickets/todos/{folder}/SEQUENCE.md` (and, for parity, one
   under a `tickets/done/{folder}/` subfolder) produces zero rows and is not treated as a tagged
   file — mirrors `collect_completed_tickets`'s existing `sequence_index_file` skip
   (`tools/tag_report.py:97-100`), now asserted across all applicable roots, not just `tickets/done/`.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

3. **`test_sweep_does_not_apply_taxonomy_date_cutoff`**
   Category: unit — the single most important anti-regression test for this ticket's core
   behavioral change.
   Verifies: a file with `ticket_id: TCK-20260101-OLD` (or no `ticket_id` at all) and a real
   unregistered/non-canonical tag in its `tags:` list still produces violation row(s) — i.e. the
   sweep's collection path must NOT reuse `_ticket_id_effective_date` / `TAG_TAXONOMY_EFFECTIVE_DATE`
   as a skip condition, unlike `collect_completed_tickets`'s `pre_taxonomy_or_legacy_ticket_id` rule.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

4. **`test_sweep_flags_unregistered_tag`**
   Category: unit.
   Verifies: a tag not present in a supplied in-memory registry dict and not matching `^phase-\d+$`
   produces exactly one `(file, tag, "unregistered")` row.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

5. **`test_sweep_does_not_flag_phase_n_tag_as_unregistered`**
   Category: unit.
   Verifies: `phase-5`/`phase-12`-style tags never produce an `unregistered` row even with an empty
   registry — regression guard mirroring `test_check_tags_registered_phase_tags_never_flagged`.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

6. **`test_sweep_flags_invalid_category_for_registered_tag_with_stale_category`**
   Category: unit — exercises the resolved `invalid_category` semantics from investigation.md,
   which has zero real-corpus hits today, so this MUST be a synthetic fixture, not a live-corpus
   assertion.
   Verifies: given a registry dict `{"some-tag": {"tag": "some-tag", "category": "retired-category",
   ...}}` and a `category_values()`-equivalent set that does NOT contain `"retired-category"`
   (construct via a temp `registries/tag_category_registry.jsonl` seeded with only the 4 real
   categories, or by monkeypatching `category_values`/passing an explicit valid-set parameter,
   whichever the implementation's function signature supports), a file using `some-tag` produces
   exactly one `(file, "some-tag", "invalid_category")` row — and no `unregistered` row for the same
   tag (mutual-exclusivity property from investigation.md).
   Location: `tests/tools/test_tag_corpus_sweep.py`.

7. **`test_sweep_invalid_category_does_not_fire_for_unregistered_tag`**
   Category: unit — negative-space guard for the mutual-exclusivity property.
   Verifies: a tag absent from the registry entirely never produces an `invalid_category` row (only
   `unregistered`), even if its would-be category (if it had one) would be invalid — proves the
   `tag in registry` gate, not just `is_tag_registered`, is what the implementation checks.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

8. **`test_sweep_invalid_category_never_fires_for_phase_n_tags`**
   Category: unit.
   Verifies: `phase-5` with an empty/any registry never produces `invalid_category` (phase tags have
   no registry entry under normal operation, so the `tag in registry` gate excludes them) — covers
   investigation.md's point 2 (phase-N tags are excluded by construction, not a hardcoded special
   case).
   Location: `tests/tools/test_tag_corpus_sweep.py`.

9. **`test_sweep_flags_non_canonical_form_independent_of_registration`**
   Category: unit.
   Verifies two sub-cases in one test or two tests: (a) an unregistered non-canonical tag (e.g.
   `Combat`) produces both `unregistered` AND `non_canonical_form` rows; (b) a *registered*
   non-canonical tag (construct a registry entry keyed on a non-canonical string, or use a tag that
   is registered-but-differently-cased if the registry schema allows it) produces only
   `non_canonical_form`, not `unregistered` — proves independence from the other two checks.
   Location: `tests/tools/test_tag_corpus_sweep.py`.

10. **`test_sweep_multi_issue_tag_produces_multiple_rows`**
    Category: unit — direct AC #46 assertion ("a tag with multiple issues produces multiple rows").
    Verifies: a tag that is both registered-with-invalid-category AND non-canonical-form (e.g.
    registry entry `{"tag": "Some_Tag", "category": "retired-category"}` used against a
    `category_values()` that excludes `"retired-category"`) produces exactly two rows for that one
    `(file, tag)` pair: `invalid_category` and `non_canonical_form`.
    Location: `tests/tools/test_tag_corpus_sweep.py`.

11. **`test_sweep_no_frontmatter_fixture_produces_zero_rows`**
    Category: unit — direct AC #3 assertion, against the exact real fixture named in the ticket.
    Verifies: running the sweep's per-file row function against
    `stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md` (confirmed via direct read:
    `extract_frontmatter()` returns `None` for this file — no `---`-delimited block at all) produces
    zero rows and does not raise.
    Location: `tests/tools/test_tag_corpus_sweep.py` (read the real file via a path relative to repo
    root, not a copied fixture, so the test rots visibly if the file is ever deleted/rewritten).

12. **`test_sweep_no_tags_key_fixture_produces_zero_rows`**
    Category: unit — direct AC #3 assertion, against the second named real fixture.
    Verifies: running the sweep's per-file row function against
    `stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md` (confirmed via direct read: has a
    valid `---`-delimited frontmatter block — `ticket_id`, `phase`, `date` — but no `tags:` key at
    all) produces zero rows and does not raise.
    Location: `tests/tools/test_tag_corpus_sweep.py`.

13. **`test_sweep_json_and_stdout_output_shapes_agree_on_row_count`**
    Category: unit/integration.
    Verifies: whatever the sweep's output surface is (mirrors `tag_report.py`'s `--json <path>`
    pattern per repo convention), the JSON row count and the stdout-summarized row count are
    identical for the same synthetic corpus — catches a divergent-formatting bug the way
    `tag_report.py`'s own `build_json_report`/`print_report` pair does today.
    Location: `tests/tools/test_tag_corpus_sweep.py`.

14. **`test_sweep_against_real_corpus_produces_zero_filesystem_writes`**
    Category: architecture guard — direct AC #4 assertion, run against the real repo tree (not
    `tmp_path`), since AC #4 explicitly says "against the real corpus."
    Verifies: `git status --porcelain` (or a content-hash snapshot of every file the sweep will
    touch) is identical before and after invoking the sweep's CLI/main entrypoint end-to-end against
    the live repo root. Implement as a subprocess test (mirrors
    `test_validate_frontmatter.py`'s "Exit code contract (subprocess)" test group) so it exercises
    the real CLI path, not just the in-process row-computation function, since the risk is in the
    CLI/`main()` wiring accidentally gaining a write path, not the pure function.
    Location: `tests/tools/test_tag_corpus_sweep.py`.

15. **`test_sweep_has_no_fix_flag_exposed`**
    Category: architecture guard — direct AC #4 assertion ("no `--fix` flag exposed").
    Verifies: `argparse`'s parsed arguments (or `--help` output) contain no `--fix`/`-f`
    write-triggering flag; a static/structural check, not just a runtime behavior check, so a future
    edit can't silently reintroduce one without this test catching it at parse-definition level.
    Location: `tests/tools/test_tag_corpus_sweep.py`.

## Scoped Pytest Commands

```bash
# New sweep tests + its direct dependencies (primary verification for this ticket):
pytest tests/tools/test_tag_corpus_sweep.py -v

# Full regression surface — the tag/frontmatter tooling family this ticket touches by import,
# plus the category-registry surface the invalid_category check depends on:
pytest tests/tools/test_tag_corpus_sweep.py tests/tools/test_tag_report.py \
       tests/tools/test_tag_registry.py tests/tools/test_tag_category_registry.py \
       tests/tools/test_validate_frontmatter.py tests/tools/test_layer_registry.py -q
```

Never `pytest tests/` — scoped to `tests/tools/` (the domain under modification), per
`CLAUDE.md`'s Testing Rule.

## Anti-Drift Test Guards

- **Date-cutoff regression guard is test #3 above** — the single highest-value anti-drift test in
  this plan. If a future edit to the sweep (or a refactor that reuses more of
  `collect_completed_tickets`) accidentally reintroduces the `TAG_TAXONOMY_EFFECTIVE_DATE` gate, this
  is the test that catches it; without it, the sweep would silently degrade back into
  `tag_report.py`'s narrower behavior and this entire ticket's purpose would be defeated invisibly
  (a passing-but-wrong-scope test suite).
- **`tests/tools/test_tag_report.py` run unmodified in the regression surface** guards against the
  new sweep accidentally changing `tag_report.py`'s own `collect_completed_tickets`/`categorize_tag`/
  `build_tag_rows` behavior if the implementation chooses to add shared helpers to that file rather
  than a fully separate module — if any of those 15 existing tests need modification to pass, that
  is itself a signal of scope creep into `tag_report.py`'s narrower, already-shipped behavior and
  should be treated as a red flag, not just fixed forward.
- **Mutual-exclusivity tests (#6, #7, #8) together are the anti-drift guard for the `invalid_category`
  semantics resolution itself** — since the real corpus has zero hits today, nothing would organically
  catch a wrong implementation (e.g. one that conflates `is_tag_registered` with "has a valid
  category" and never fires `invalid_category` at all, or one that double-fires both `unregistered`
  and `invalid_category` for the same tag) without these synthetic-fixture tests specifically
  targeting the boundary.
- **Test #14 (zero filesystem writes) run against the real repo tree, not a tmp_path copy** — a
  tmp_path-only version would not actually prove the live corpus survives a real invocation
  untouched; this must run the literal CLI entrypoint against the real `tickets/`/`stored_artifacts/`
  trees to be a meaningful AC #4 guard, mirroring the ticket's own acceptance-criterion wording
  ("Running the sweep against the real corpus produces zero filesystem writes").
- **No test should assert a specific row *count* against the live corpus** (e.g. "exactly N
  unregistered tags found today") — the corpus grows continuously (confirmed: `tickets/done` grew
  from ~1044 files at `TCK-20260706-TAG-REPORT-TOOL` time to ~1199 today), so any such assertion
  would be a flaky, drift-prone test from the day it's written. Assert structural properties
  (row shape, non-negative counts, zero-crash) against the live corpus; assert exact counts only
  against synthetic `tmp_path`/in-memory fixtures.
