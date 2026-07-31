---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
artifact_type: plan
tags: [tagging, data-quality, reporting]
---

# Implementation Plan — TCK-20260720-TAG-CORPUS-REPAIR-SWEEP

## Summary

Build a report-only, non-cutoff-gated tag/category violation sweep across the full corpus
(`tickets/done/**`, `tickets/inprogress/**`, `tickets/todos/**`, `stored_artifacts/**/*.md`). The
walk/collection logic is added as new functions alongside `collect_completed_tickets()` in
`tools/tag_report.py` (satisfying the ticket's "extend tag_report.py's existing corpus-walk"
instruction and letting it share `extract_frontmatter()`/`SEQUENCE.md`-skip conventions in the same
module) — but the CLI entrypoint (`argparse`, `main()`, JSON/stdout output) lives in a **new** file,
`tools/tag_corpus_sweep.py`, so that `tag_report.py`'s own existing `main()`/CLI wiring is never
touched, which is the safest way to guarantee the Anti-Drift Hazard "do not silently change
`tag_report.py`'s...existing behavior while extending shared code." All violation classification
(`unregistered` / `invalid_category` / `non_canonical_form`) is one pure function implementing the
semantics resolved in `investigation.md`, built and tested before anything touches the filesystem
walk or CLI layer. No `--fix` flag, no write path, no second frontmatter parser, and no reuse of the
`TAG_TAXONOMY_EFFECTIVE_DATE` skip anywhere in the new path.

## Steps

### Step 1 — Multi-root file collection (no date-gate, `SEQUENCE.md` skip only)

**Files:** `tools/tag_report.py`

**Change:** Add a new function `collect_sweep_files(root: Path) -> tuple[list[str], Counter, defaultdict]`
placed directly below `collect_completed_tickets()` (same section, same style — reuse `Counter`/
`defaultdict` already imported). It walks all four corpus roots via `root.rglob("*.md")` on each of
`tickets/done`, `tickets/inprogress`, `tickets/todos`, `stored_artifacts` (skip a root directory
silently if it doesn't exist, matching `collect_completed_tickets`'s `if not done_dir.is_dir():
return` pattern), sorts the combined file list, and skips any file named `SEQUENCE.md` at any
nesting level (the **only** skip rule at this stage — no frontmatter parsing, no date check, no
tags check happens here). Returns `(relative_paths, skip_reasons, skipped_paths)` where
`skip_reasons["sequence_index_file"]` counts the skips, mirroring the existing function's return
shape so the CLI layer in Step 4 can reuse the same printing pattern.

**Do NOT touch:** `collect_completed_tickets()` itself — it must remain byte-for-byte unchanged
(still `tickets/done/`-only, still date-gated, still no-tags-skipped). Do not add a `root` parameter
to it or refactor it to share code with the new function beyond the `Counter`/`defaultdict`/`Path`
imports already at the top of the file.

**Verify:** `test_sweep_walks_all_four_corpus_roots`, `test_sweep_skips_sequence_md_at_every_level`
(`tests/tools/test_tag_corpus_sweep.py`, new file — create it in this step with just these two
tests; later steps append to it).

---

### Step 2 — Pure per-tag violation classifier

**Files:** `tools/tag_report.py`

**Change:** Add a new pure function, placed near `categorize_tag()`:

```python
def tag_issues(tag: str, registry: dict, valid_categories: frozenset) -> list[str]:
    """Return the list of violation issue strings for `tag` under investigation.md's resolved
    semantics: 'unregistered', 'invalid_category', 'non_canonical_form' — zero, one, two, or all
    three may apply. 'unregistered' and 'invalid_category' are mutually exclusive by construction;
    'non_canonical_form' is independent of both.
    """
    issues = []
    if not is_tag_registered(tag, registry):
        issues.append("unregistered")
    elif tag in registry:
        recorded_category = registry[tag].get("category")  # defensive: missing category -> invalid
        if recorded_category not in valid_categories:
            issues.append("invalid_category")
    if canonical_form_violation(tag) is not None:
        issues.append("non_canonical_form")
    return issues
```

This requires importing `is_tag_registered` alongside the existing `canonical_form_violation`,
`is_phase_milestone_tag`, `load_registry` import from `tag_registry` at the top of `tag_report.py`,
and importing `category_values` as well (needed by Step 4's orchestration, add it in this step
since it's the same import line). No new logic is derived — every branch calls straight into
`tag_registry.py`'s existing functions, per Scope.

**Do NOT touch:** `categorize_tag()` — it stays exactly as-is (display-category lookup, a different
question from violation classification). Do not merge or rename the two functions.

**Verify:** `test_sweep_flags_unregistered_tag`, `test_sweep_does_not_flag_phase_n_tag_as_unregistered`,
`test_sweep_flags_invalid_category_for_registered_tag_with_stale_category`,
`test_sweep_invalid_category_does_not_fire_for_unregistered_tag`,
`test_sweep_invalid_category_never_fires_for_phase_n_tags`,
`test_sweep_flags_non_canonical_form_independent_of_registration`,
`test_sweep_multi_issue_tag_produces_multiple_rows`.

---

### Step 3 — Per-file row builder (frontmatter parse, no date-gate, no crash)

**Files:** `tools/tag_report.py`

**Change:** Add `sweep_file_rows(rel_path: str, text: str, registry: dict, valid_categories:
frozenset) -> list[dict]`, placed after `tag_issues()`. Calls `extract_frontmatter(text)` — the
**only** parser, per Scope — inside a `try/except ValueError` that returns `[]` on failure (an
unparseable frontmatter block is treated the same as "nothing to flag," not a crash, extending
AC #3's no-frontmatter/no-tags tolerance to malformed frontmatter defensively). If `fm is None`
(no frontmatter block) or `not fm.get("tags")` or the tags value isn't a `list`, return `[]`. Do
**not** read or check `ticket_id` / `_ticket_id_effective_date` anywhere in this function — this is
the single line of code this whole ticket exists to omit. Otherwise, for each `tag` in
`fm["tags"]`, call `tag_issues(tag, registry, valid_categories)` and emit one row dict
`{"file": rel_path, "tag": tag, "issue": issue}` per issue string returned (a tag with N issues
produces N rows, per AC #2).

**Do NOT touch:** `_check_tags()` in `validate_frontmatter.py` — it stays as the forward-only,
date-gated enforcement path; this new function is a parallel, independent read path, not a
replacement or a shared refactor of `_check_tags`.

**Verify:** `test_sweep_does_not_apply_taxonomy_date_cutoff`,
`test_sweep_no_frontmatter_fixture_produces_zero_rows` (against the real
`stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md` fixture),
`test_sweep_no_tags_key_fixture_produces_zero_rows` (against the real
`stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md` fixture).

---

### Step 4 — Sweep orchestration and report shaping (new module)

**Files:** `tools/tag_corpus_sweep.py` (new file)

**Change:** Create the new module following `tag_report.py`'s own `sys.path.insert` + import
pattern (same `_TOOLS_DIR` trick) to import `collect_sweep_files`, `sweep_file_rows` from
`tag_report`, and `load_registry`, `category_values` from `tag_registry`. Add:

- `run_sweep(root: Path) -> dict` — calls `load_registry(root)`, `category_values(root)`,
  `collect_sweep_files(root)`; for each returned relative path, reads the file text (`(root /
  rel_path).read_text(encoding="utf-8")`) and calls `sweep_file_rows(...)`, concatenating all rows.
  Returns a dict with `rows` (list), `scanned_files` (count of files walked, i.e. included +
  skipped), `skipped` (the `skip_reasons` Counter from `collect_sweep_files`, as a plain dict), and
  per-issue summary counts (`Counter(row["issue"] for row in rows)`).
- `print_report(result: dict) -> None` — prints scanned/skipped summary counts first (per
  investigation.md's "print progress/summary counts...not only a final row dump" note), then the
  per-issue-type counts, then the full `(file, tag, issue)` row list.
- `build_json_report(result: dict) -> dict` — same shape as `tag_report.py`'s
  `build_json_report`, with a `generated` UTC timestamp, for `--json` output.

**Do NOT touch:** `tools/tag_report.py`'s own `main()`, `print_report()`, `build_json_report()`, or
its `--json`/`--show-tickets`/`--list-skipped` argparse wiring — none of it is imported or modified
by this step; this is a wholly separate output layer for a wholly separate CLI.

**Verify:** `test_sweep_json_and_stdout_output_shapes_agree_on_row_count`.

**Depends on:** Steps 1–3 (imports their functions directly).

---

### Step 5 — CLI entrypoint (report-only, no `--fix`)

**Files:** `tools/tag_corpus_sweep.py`

**Change:** Add `main()` with `argparse`: `--root` (default `.`), `--json` (optional output path,
same resolve-then-`mkdir`-then-write pattern as `tag_report.py`'s `main()`). Call `run_sweep`,
`print_report`, and conditionally `build_json_report` + write. Add
`if __name__ == "__main__": main()`. The parser must define **no** `--fix`, `-f`, or any argument
whose help text implies a write/mutate action — this is a structural property a future edit could
silently reintroduce, so keep the argument list minimal and exhaustively enumerated in one place
(no dynamic flag construction).

**Do NOT touch:** Do not add any `Path.write_text` call anywhere in this module except the single,
explicit, opt-in `--json` output path (which writes a *new* report file under e.g. `reports/`, not
any corpus file under `tickets/` or `stored_artifacts/`) — this is the same write-surface shape
`tag_report.py`'s own `--json` flag already has, not a new kind of write.

**Verify:** `test_sweep_has_no_fix_flag_exposed`,
`test_sweep_against_real_corpus_produces_zero_filesystem_writes` (subprocess test invoking
`python3 tools/tag_corpus_sweep.py` against the real repo root, asserting `git status --porcelain`
is identical before/after).

**Depends on:** Step 4.

---

### Step 6 — Documentation: new Pillar subsection + stale-link fix

**Files:** `docs/guides/ticket_reporting.md`

**Change:**
1. Add a new **Pillar 3: Legacy Corpus Tag/Category Repair Sweep** subsection, inserted after the
   existing Pillar 2 section and before "Related docs," following the exact same structure already
   used for Pillar 1/2 (`**Tool:**` line, `### What it does`, `### Quick start`, `### Technical
   detail`, and a dated snapshot line once the tool has been run once against the real corpus during
   this ticket's own Test phase). Content must state: report-only, no `--fix`/write path; corpus
   coverage is all four roots (`tickets/done/**`, `tickets/inprogress/**`, `tickets/todos/**`,
   `stored_artifacts/**/*.md`); it does **not** apply the `TAG_TAXONOMY_EFFECTIVE_DATE` cutoff
   (explicitly contrast this with Pillar 1's cutoff-gated scope, so a reader doesn't conflate the two
   tools); the three issue kinds (`unregistered`, `invalid_category`, `non_canonical_form`) and their
   resolved semantics (mutual exclusivity of the first two, independence of the third, multi-issue
   rows). Link to `registries/tag_registry.jsonl` and `registries/tag_category_registry.jsonl` (the
   correct, post-relocation paths — see point 2).
2. **Design decision (in-scope, do this):** while editing this file for the new subsection, also fix
   the pre-existing stale link in the Pillar 1 section (line 31: `[registries/tag_registry.jsonl](../guidelines/tag_registry.jsonl)`
   → should link target `../../registries/tag_registry.jsonl`). Rationale: this is the same file
   being edited in this same step for an unrelated-but-adjacent reason, the fix is a one-line link
   target correction with zero behavioral risk, and leaving a freshly-written correct link (Pillar 3)
   next to a known-stale one (Pillar 1) in the same document would itself be a small new
   inconsistency. This is a documentation-only touch-up, not a code or registry change, and is not a
   separate ticket's scope — it is bounded to this one link.

**Do NOT touch:** Pillar 1's or Pillar 2's prose, numbers, or code-level technical-detail tables
beyond that single link-target correction — do not update Pillar 1's dated snapshot numbers, add new
examples to it, or restructure its table.

**Verify:** No automated test (documentation-only); manual check that both links in the file
(Pillar 1's corrected link and Pillar 3's new links) resolve to `registries/tag_registry.jsonl` /
`registries/tag_category_registry.jsonl` relative to `docs/guides/`, and that the new subsection
follows the existing Pillar heading/subsection depth (confirms AC #6's "mirroring the documentation
depth already given to tag_report.py's Pillar 1").

**Depends on:** Step 5 (should describe the finished CLI's actual flags/output, not a
planned/guessed shape).

---

## Scope Guards

- No `--fix` flag, anywhere, in either `tools/tag_report.py` or `tools/tag_corpus_sweep.py`. No
  `Path.write_text` call touches any file under `tickets/` or `stored_artifacts/` in either module.
- No second frontmatter parser. `extract_frontmatter()` (imported from `validate_frontmatter.py`) is
  the only parser called anywhere in the new code.
- No re-derivation of canonical-form, registry-membership, or category-validity rules.
  `canonical_form_violation`, `is_tag_registered`, `load_registry`, `category_values` are imported
  from `tag_registry.py`, never reimplemented.
- The `TAG_TAXONOMY_EFFECTIVE_DATE` / `_ticket_id_effective_date` skip-gate must not appear anywhere
  in `collect_sweep_files()` or `sweep_file_rows()` — this is the entire point of the ticket (AC #1).
- `collect_completed_tickets()`, `categorize_tag()`, `build_tag_rows()`, and `tag_report.py`'s
  existing `main()`/CLI wiring are not modified. All 15 existing `test_tag_report.py` tests must
  pass unmodified — if any need editing to pass, that is a scope-creep signal, not something to fix
  forward.
- `tools/validate_frontmatter.py` is imported from, never edited. `_check_tags()` and
  `validate_directory()` stay exactly as they are.
- No full-schema validation (required-field checks, `status` enum, etc.) for `stored_artifacts/`
  files — only the tag/category checks named in AC #2.
- No wiring of this sweep into any agent workflow, gate, CI check, `make` target, or the
  `done-checker`'s `frontmatter_valid` condition. It is a standalone, manually-invoked report tool,
  same as `tag_report.py`.
- No fixing of any flagged historical violation (no retagging, no registry edits triggered by sweep
  findings) — report-only is the entire mandate.
- Do not touch `docs/guidelines/tag_taxonomy.md`, `registries/tag_registry.jsonl`, or
  `registries/tag_category_registry.jsonl` — read-only inputs to this ticket.
- Do not modify Pillar 1's or Pillar 2's content in `docs/guides/ticket_reporting.md` beyond the one
  named stale-link correction in Step 6.
- No `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX` work — separate, already-filed ticket, not absorbed
  here.

## Dependency Map

- Step 1 (collection) — independent, can be implemented and tested first.
- Step 2 (classifier) — independent of Step 1, can be implemented and tested in parallel/either
  order.
- Step 3 (per-file rows) — depends on Step 2 (calls `tag_issues`); independent of Step 1's exact
  implementation but conceptually pairs with it (both are `tag_report.py` additions consumed by
  Step 4).
- Step 4 (orchestration) — depends on Steps 1, 2, 3 (imports all three functions).
- Step 5 (CLI) — depends on Step 4 (`run_sweep`/`print_report`/`build_json_report` must exist).
- Step 6 (docs) — depends on Step 5 (documents the finished CLI's real flags and output shape).

Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 (each step's tests gate the next).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Sweep walks all 4 roots (skip `SEQUENCE.md`, no date-cutoff), parses via `extract_frontmatter()` only | Steps 1, 3 | `test_sweep_walks_all_four_corpus_roots`, `test_sweep_skips_sequence_md_at_every_level`, `test_sweep_does_not_apply_taxonomy_date_cutoff` |
| `(file, tag, issue)` row per applicable case; multi-issue tags produce multiple rows | Steps 2, 3 | `test_sweep_flags_unregistered_tag`, `test_sweep_does_not_flag_phase_n_tag_as_unregistered`, `test_sweep_flags_invalid_category_for_registered_tag_with_stale_category`, `test_sweep_invalid_category_does_not_fire_for_unregistered_tag`, `test_sweep_invalid_category_never_fires_for_phase_n_tags`, `test_sweep_flags_non_canonical_form_independent_of_registration`, `test_sweep_multi_issue_tag_produces_multiple_rows` |
| No-frontmatter / no-tags files produce zero rows, not a crash (real fixtures) | Step 3 | `test_sweep_no_frontmatter_fixture_produces_zero_rows`, `test_sweep_no_tags_key_fixture_produces_zero_rows` |
| Zero filesystem writes against real corpus; no `--fix` flag exposed | Step 5 | `test_sweep_against_real_corpus_produces_zero_filesystem_writes`, `test_sweep_has_no_fix_flag_exposed` |
| `invalid_category` semantics confirmed during Scope phase, not assumed | Resolved in `investigation.md`; implemented by Step 2 | `test_sweep_flags_invalid_category_for_registered_tag_with_stale_category` + the mutual-exclusivity tests (#7, #8) |
| New Pillar subsection in `docs/guides/ticket_reporting.md`, matching Pillar 1's depth | Step 6 | Manual review (documentation-only, no automated test) |

## Anti-Drift Notes

- The single highest-value regression test in this plan is
  `test_sweep_does_not_apply_taxonomy_date_cutoff` (Step 3) — it is the concrete guard against
  silently reusing `collect_completed_tickets()`'s 4th skip rule (`pre_taxonomy_or_legacy_ticket_id`)
  wholesale. The other three of that function's skip rules (`sequence_index_file`,
  `unparseable_frontmatter`/`no_frontmatter_legacy_format`, `no_tags`) are correct to mirror in
  spirit in Steps 1 and 3 — only the date rule must be dropped.
- `invalid_category` has zero real hits in the live corpus today (verified in `investigation.md`
  directly against `registries/tag_registry.jsonl`'s 53 entries). Do not write any test that asserts
  a nonzero `invalid_category` count against the real corpus — that assertion would be true today
  only by accident of current registry contents, not by design, and would misrepresent what the
  check is for (future drift protection). All `invalid_category` tests must use synthetic
  registry/`valid_categories` fixtures (Step 2's tests), exactly as `test_plan.md` specifies.
  Likewise, no test anywhere in this ticket should assert an exact row *count* against the live
  corpus (`test_plan.md`'s explicit anti-drift guard) — the corpus grows continuously.
  Live-corpus-facing tests (`test_sweep_against_real_corpus_produces_zero_filesystem_writes`) assert
  structural properties (zero writes) only, never counts.
  - Note the one deliberate implementation-level extension beyond `investigation.md`'s literal
    pseudocode: `sweep_file_rows()` (Step 3) also catches `ValueError` from `extract_frontmatter()`
    (malformed frontmatter) and treats it as zero rows, not a crash. `investigation.md`'s "Risks and
    Open Questions" section frames the crash-tolerance requirement as extending to "registry-side
    malformation, not just file-side" — this plan applies the same spirit symmetrically to
    file-side malformed frontmatter, since AC #3's fixtures only cover "no frontmatter block" and
    "no tags key," not "unparseable frontmatter," and a sweep tool that crashes partway through a
    ~3954-file corpus walk on one malformed legacy file would defeat the tool's purpose. This is a
    reasonable, narrow interpretation, not scope creep — flagging it here for visibility during
    implementation review rather than treating it as silently obvious.
- `stored_artifacts/**/*.md` is walked by direct glob, not by joining through a ticket-ID-shaped
  folder list — some `stored_artifacts/` subdirectories are not `TCK-`-named (UUID-named, milestone
  folders, etc.), and the sweep must not assume or filter on folder-name shape.
- Keep `tools/tag_corpus_sweep.py`'s CLI surface minimal (`--root`, `--json` only) — do not add
  `--show-tickets`-style conveniences or a `--list-skipped` flag in this pass unless a test in
  `test_plan.md` specifically requires it; the test plan's 15 new tests define the full required
  surface, and nothing beyond it is in scope.

## Deviations

None from the 6 ordered steps or the Scope Guards above. Two implementation-level choices not
explicitly dictated by this plan, both within the freedom the plan leaves open:

- `print_report()`'s row lines use a tab-separated `file\ttag\tissue` format rather than
  `tag_report.py`'s fixed-width column style — chosen so the stdout output is unambiguous to
  parse back into rows for `test_sweep_json_and_stdout_output_shapes_agree_on_row_count`, which
  this plan requires (Step 4) but does not prescribe a print format for.
- `tests/tools/test_tag_corpus_sweep.py` ships 20 tests, not exactly the 15 named in
  `test_plan.md` — the 5 extra are additional negative/regression angles on the same required
  behaviors (e.g. a `sweep_file_rows`-level date-cutoff check alongside the
  `collect_sweep_files`-level one named in the test plan, and an explicit unparseable-frontmatter
  case for the disclosed `ValueError`-tolerance extension already called out in this plan's own
  Anti-Drift Notes). All 15 named tests are present verbatim by name; nothing named in
  `test_plan.md` was dropped or renamed.
