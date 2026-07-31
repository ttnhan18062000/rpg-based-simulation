---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CATEGORY-REGISTRY
artifact_type: plan
tags: [tagging, frontmatter, taxonomy]
---

# Implementation Plan — TCK-20260720-TAG-CATEGORY-REGISTRY

## Summary

Convert tag categories from a hardcoded Python set (`ALL_CATEGORIES`/`ADDABLE_CATEGORIES` in
`tools/tag_registry.py`) into a registry-file-backed live value, mirroring the pattern
`TCK-20260718-LAYER-REGISTRY-CONVERSION` already established for `layer:`. Because `add_category()`
and `category_values()` are specified to live **inside `tag_registry.py` itself** (not a new
sibling module like `layer_registry.py` was), the implementation adds a second, independent
registry surface (path, loader, add/values functions) alongside the existing tag-scoped one in the
same file — the two must not collide or merge. Work proceeds: add the new functions (additive) →
add a CLI subcommand for them → seed the real registry file through that CLI (not hand-written) →
rewire `add_tag()`/argparse to read the new live source and delete the old constants → add the new
test file → update docs. `validate_frontmatter.py` and `ticket_stats_report.py` are confirmed by
investigation to have no tag-category code today and are explicitly not touched.

## Design Decisions (resolving the 3 flagged open questions)

1. **`add_category()`'s canonical-form check reuses the existing module-level
   `canonical_form_violation()`** (the one `add_tag()` already uses), rather than defining a
   second, category-specific one. Rationale: `add_category()` lives in the *same file* as that
   function (unlike `add_layer()`, which is in a separate module and therefore needed its own copy
   of the rule). The existing function's core check (lowercase, hyphen-separated, no underscore) is
   exactly the rule categories need too; its extra tag-specific branches
   (`FORBIDDEN_PRIORITY_TAGS`, `_PHASE_NONCANONICAL_RE`, `TAG_SYNONYM_MAP`) are harmless no-ops for
   category strings (none of `subsystem-topic`, `process-skill-signal`, `quality-attribute`,
   `meta-process` match `p0`/`p1`/`p2`, `phaseN`, or a synonym-map key), so reuse is safe and avoids
   a duplicate regex in the same file. "Identical shape to `add_layer()`" (ticket Scope bullet 2)
   refers to `add_category()`'s signature/raise-behavior, not to duplicating a second
   canonical-form function.
2. **Add `is_category_registered(category, registry)`**, mirroring `layer_registry.py`'s
   `is_category_registered`-equivalent (`is_layer_registered`). Rationale: AC 5 requires the new
   test file to mirror `test_layer_registry.py`'s structure, and that structure has a dedicated
   `is_layer_registered` test section — omitting the function would leave that section of the
   mirror with nothing to test. It is a trivial pure function (`category in registry`); include it
   for structural parity, but do **not** add a `check_categories_registered()` plural-batch helper —
   nothing in this ticket's scope needs a batch check (unlike `check_tags_registered()`, which the
   Scope phase workflow actually calls), so adding it would be unused surface.
3. **CLI-layer test uses an in-process `main()` invocation with monkeypatched `sys.argv` and
   `pytest.raises(SystemExit)` + `capsys`, not a subprocess.** Rationale: `test_tag_registry.py` has
   zero existing CLI-layer tests (all call functions directly), so there's no subprocess precedent
   to match, and a subprocess test would be slower and heavier for no added guarantee — argparse's
   own `choices` validation runs in-process and raises `SystemExit(2)` with a stderr message listing
   the live choices, which is exactly what needs proving. See Step 5.

## New Public Surface Added to `tools/tag_registry.py`

To avoid name collisions with the existing tag-scoped `registry_path()` / `load_registry()`
(which stay untouched, still pointed at `registries/tag_registry.jsonl`, keyed on `entry["tag"]`),
the category registry gets its own distinctly-named path/loader pair:

- `_CATEGORY_REGISTRY_REL_PATH = Path("registries/tag_category_registry.jsonl")`
- `category_registry_path(root=None) -> Path`
- `load_category_registry(root=None) -> dict` — same shape as `load_registry()` (missing file →
  `{}`, skips blank lines, raises `ValueError` on duplicate `category` key) but reads
  `category_registry_path()` and keys on `entry["category"]`
- `is_category_registered(category, registry) -> bool`
- `add_category(category, note="", root=None) -> dict`
- `category_values(root=None) -> frozenset[str]`

## Steps

### Step 1 — Add category registry path/loader/query functions (additive only)
**Files:** `tools/tag_registry.py`
**Change:** Add, in a new section near the existing "Registry file I/O" section (after
`get_skill_mapping()`, before the `# CLI` section, so tag-scoped and category-scoped I/O are
visually grouped but distinct):
- `_CATEGORY_REGISTRY_REL_PATH = Path("registries/tag_category_registry.jsonl")`
- `category_registry_path(root=None) -> Path` — same body shape as `registry_path()`, using
  `_CATEGORY_REGISTRY_REL_PATH` instead of `_REGISTRY_REL_PATH`.
- `load_category_registry(root=None) -> dict` — same body shape as `load_registry()` (lines
  171-194 today), reading `category_registry_path()`, keyed on `entry["category"]`, raising
  `ValueError` with the same `"duplicate registration for category {category!r}..."` message
  pattern on a repeated key.
- `is_category_registered(category, registry) -> bool` — `return category in registry`.
- `category_values(root=None) -> frozenset[str]` — `return frozenset(load_category_registry(root).keys())`.
  No caching, matching `layer_values()` exactly (ticket Scope bullet 3).

Do not yet add `add_category()`, do not touch `add_tag()`, `ALL_CATEGORIES`, `ADDABLE_CATEGORIES`,
or argparse — those come in later steps so each step verifies one thing.
**Do NOT touch:** `registry_path()`, `load_registry()`, `_REGISTRY_REL_PATH` (the existing
tag-scoped ones) — they must remain byte-for-byte unchanged and still govern
`registries/tag_registry.jsonl`.
**Verify:** New tests in `tests/tools/test_tag_category_registry.py` (created in this step, partial
— only the sections that don't depend on `add_category()` or the seeded file): canonical-form
reuse sanity check (`canonical_form_violation("subsystem-topic") is None`), `load_category_registry`
missing-file/reads-entries/skips-blanks/duplicate-raises (mirroring
`test_load_registry_raises_on_duplicate_layer`, using `tmp_path` and hand-written JSONL fixtures —
this is the one place hand-written JSONL is correct, since it's testing the *loader*, not seeding
the real file), `is_category_registered` true/false.

### Step 2 — Add `add_category()` function
**Files:** `tools/tag_registry.py`
**Change:** Add `add_category(category: str, note: str = "", root: Path | str | None = None) -> dict`
directly after `load_category_registry()`/`is_category_registered()`, mirroring `add_layer()`'s body
exactly (layer_registry.py:112-141): validate via `canonical_form_violation(category)` (reusing the
existing module-level function per Design Decision 1) → raise `ValueError` on violation → load via
`load_category_registry(root)` → raise `ValueError` with `"{category!r} is already registered
(added {existing['added_date']}) — categories cannot be re-added or changed"` on duplicate → build
`entry = {"category": category, "added_date": <utc today>, "note": note}` → write one line via
`category_registry_path(root)`, `path.parent.mkdir(parents=True, exist_ok=True)`,
`json.dumps(entry, sort_keys=True) + "\n"` in append mode → return `entry`.
**Do NOT touch:** `add_tag()` itself, `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` (still present and
still what `add_tag()` reads at this point), argparse.
**Verify:** New tests in `test_tag_category_registry.py`: `add_category` appends entry and returns
it (asserting the entry has exactly `{"category", "added_date", "note"}` — no stray keys, no
`addable`/`exempt` field per Anti-Drift Hazard); rejects non-canonical category name (`ValueError`,
message contains "canonical form"); rejects duplicate category (`ValueError`, message contains
"already registered"); append-only — two `add_category()` calls against the same `tmp_path` leave
both entries' `note` fields independently correct (mirrors
`test_add_layer_is_append_only_existing_entries_unchanged`).

### Step 3 — Add `add-category` CLI subcommand
**Files:** `tools/tag_registry.py`
**Change:** In `main()`, add a new subparser alongside the existing `add`/`list`/`skill-mapping`
ones:
```python
add_category_p = sub.add_parser(
    "add-category",
    help="Register a new tag category (append-only — cannot update or delete an existing one)",
)
add_category_p.add_argument("category")
add_category_p.add_argument("--note", default="", help="Why this category exists")
add_category_p.add_argument("--root", default=None)
```
and a handling branch (placed after the existing `if args.command == "add":` block, before `list`):
```python
if args.command == "add-category":
    try:
        entry = add_category(args.category, args.note, root=args.root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Registered category {entry['category']!r} ({entry['added_date']}).")
    return
```
This subcommand is named `add-category` (not `add`) because `add` is already taken by tag
registration in this same file — this naming is explicit in ticket AC 6 ("the new `add-category`
CLI command").
**Do NOT touch:** the existing `add` subcommand's definition or handling block in this step (its
`--category choices=sorted(ADDABLE_CATEGORIES)` line is rewired in Step 5, not here).
**Verify:** New test in `test_tag_category_registry.py` (or `test_tag_registry.py`, implementer's
choice — put it in `test_tag_category_registry.py` since it exercises `add-category`, not `add`):
invoke `main()` with `monkeypatch.setattr(sys, "argv", ["tag_registry.py", "add-category",
"some-new-cat", "--note", "test", "--root", str(tmp_path)])`, assert it returns without raising,
and assert `load_category_registry(tmp_path)` contains `"some-new-cat"` afterward.

### Step 4 — Seed `registries/tag_category_registry.jsonl` via the CLI
**Files:** `registries/tag_category_registry.jsonl` (new, generated — not hand-written)
**Change:** Run the `add-category` CLI four times against the real repo root (no `--root`
override) to seed exactly the 4 currently-addable categories, using their existing descriptions
from `docs/guides/ticket_tagging.md`'s "The 5 Categories" table as the `--note` text for
traceability:
```bash
python3 tools/tag_registry.py add-category subsystem-topic --note "A subject-matter area the ticket touches"
python3 tools/tag_registry.py add-category process-skill-signal --note "A tag whose canonical spelling matches an existing skill/process gate 1:1"
python3 tools/tag_registry.py add-category quality-attribute --note "The nature of a change, not tied to a specific skill"
python3 tools/tag_registry.py add-category meta-process --note "About the ticket/agent-workflow process itself, not gameplay or engine subject matter"
```
This produces `registries/tag_category_registry.jsonl` with 4 lines, `sort_keys=True` formatting
(`added_date`, `category`, `note` order), matching `registries/layer_registry.jsonl`'s existing
style exactly. Do **not** add a 5th line for `phase-milestone` — see Design/Anti-Drift below.
**Do NOT touch:** `registries/tag_registry.jsonl`, `registries/layer_registry.jsonl` — unrelated
files, must not be regenerated or reformatted as a side effect.
**Verify:** New pin tests in `test_tag_category_registry.py`, run against the real repo (no `root`
override), mirroring `test_layer_values_matches_real_seeded_registry`:
- `category_values() == frozenset({"subsystem-topic", "process-skill-signal", "quality-attribute", "meta-process"})`
- `"phase-milestone" not in category_values()`

### Step 5 — Rewire `add_tag()` and CLI `add` choices; remove `ALL_CATEGORIES`/`ADDABLE_CATEGORIES`
**Files:** `tools/tag_registry.py`, `tests/tools/test_tag_registry.py`
**Change:**
- In `tools/tag_registry.py`: delete the `ALL_CATEGORIES` set literal (lines 66-72) and
  `ADDABLE_CATEGORIES = ALL_CATEGORIES - {"phase-milestone"}` (line 76), and the module docstring
  bullet referencing `ADDABLE_CATEGORIES`/the 5-categories rationale that no longer matches code
  (keep the docstring's explanation of *why* `phase-milestone` is excluded — that's still true, just
  update the mechanism it names from "not in `ADDABLE_CATEGORIES`" to "never seeded in
  `registries/tag_category_registry.jsonl`").
- In `add_tag()` (line 233 today): change `if category not in ADDABLE_CATEGORIES:` to
  `if category not in category_values():`. Keep the same error message shape, computing
  `sorted(category_values())` instead of `sorted(ADDABLE_CATEGORIES)`.
- In `main()`'s `add` subparser (line 297 today): change
  `add_p.add_argument("--category", required=True, choices=sorted(ADDABLE_CATEGORIES))` to
  `choices=sorted(category_values())`.
- In `tests/tools/test_tag_registry.py`: update the import block (lines 14-26) — remove
  `ADDABLE_CATEGORIES, ALL_CATEGORIES`, add `category_values`. Update
  `test_add_tag_rejects_phase_milestone_category` (lines 162-167): replace
  `assert "phase-milestone" not in ADDABLE_CATEGORIES` / `assert "phase-milestone" in ALL_CATEGORIES`
  with a single `assert "phase-milestone" not in category_values()`; keep the
  `pytest.raises(ValueError, match="category must be one of")` block unchanged (behavior it
  protects is unchanged, only the mechanism proving it changes).
**Do NOT touch:** any other test in `test_tag_registry.py` — `test_add_tag_rejects_invalid_category`,
`test_add_tag_appends_entry_and_returns_it`, `test_add_tag_is_append_only_existing_entries_unchanged`,
`test_add_tag_rejects_duplicate_tag`, `test_add_tag_rejects_non_canonical_tag`, all
`test_get_skill_mapping_*`/`test_legacy_skill_triggers_*`/`test_check_tags_registered_*` tests must
pass unmodified — if any of these need a change, that signals unintended scope creep into unrelated
`tag_registry.py` logic.
**Verify:**
- `test_add_tag_rejects_invalid_category` (existing, unmodified) still passes.
- `test_add_tag_rejects_phase_milestone_category` (updated per above) still passes.
- New test `test_add_tag_category_validation_sources_from_category_values` in
  `test_tag_registry.py`: `add_category("new-cat", root=tmp_path)` then
  `add_tag("some-tag", "new-cat", root=tmp_path)` succeeds without any code change — proves live
  sourcing, not a residual hardcoded copy.
- New test `test_argparse_category_choices_match_category_values` in `test_tag_registry.py`
  (mechanism per Design Decision 3): monkeypatch `sys.argv` to
  `["tag_registry.py", "add", "some-tag", "--category", "not-a-real-category"]`, call `main()`
  inside `pytest.raises(SystemExit)`, then assert every name in `sorted(category_values())` appears
  in `capsys.readouterr().err`.

### Step 6 — Document the `add-category` CLI command
**Files:** `docs/guidelines/tag_taxonomy.md`, `docs/guides/ticket_tagging.md`
**Change:**
- `docs/guidelines/tag_taxonomy.md`, "Tag Registry" section (~lines 130-171): after the existing
  "How to register a new tag" code block, add a parallel "How to register a new category" block
  documenting `python3 tools/tag_registry.py add-category <category> --note "why this category
  exists"` and `python3 tools/tag_registry.py list` note that `list` only shows tags — mention that
  `registries/tag_category_registry.jsonl` is the category-equivalent file and is seeded with
  exactly the 4 addable categories today, with `phase-milestone` deliberately never registered
  there (cross-reference the existing "`phase-N` tags are exempt from registration" paragraph).
- `docs/guides/ticket_tagging.md`, "Registering a New Tag" section (~lines 19-42): add a short
  adjacent subsection "Registering a New Category" with the same level of detail as the existing
  tag-registration walkthrough — the `add-category` command, its `--note` flag, and a pointer back
  to `tag_taxonomy.md`'s "The 5 Categories" table for what each category means.
**Do NOT touch:** `docs/guides/ticket_reporting.md`, `CLAUDE.md`, `tools/tag_report.py`,
`tools/agent-monitoring/generate_retro.py` — explicitly Out of Scope per the ticket (prose-only
category references, no live-import mechanism applies).
**Verify:** No automated test for doc prose; manual check that both files' new sections match the
actual `add-category` CLI behavior implemented in Step 3 (flag names, error behavior). Since
`docs/` files change, `make knowledge-index-update` must be run per project CLAUDE.md's After Work
rule (Finalize-phase action, not part of this step's own verification, but worth noting here so it
isn't missed).

## Scope Guards

- Do not edit `tools/validate_frontmatter.py` — confirmed by investigation to contain zero
  tag-category code; it only checks canonical form and tag *membership*, never category. Its import
  of `FORBIDDEN_PRIORITY_TAGS`, `TAG_SYNONYM_MAP`, `TAG_TAXONOMY_EFFECTIVE_DATE`,
  `canonical_form_violation`, `is_tag_registered`, `load_registry` from `tag_registry.py` is
  unaffected by every step above (none of those names are renamed, removed, or changed in shape).
- Do not edit `tools/ticket_stats_report.py` — confirmed zero tag-category coupling (it reports
  Tier/Type/Priority/Layer, not tags at all).
- Do not edit `tools/tag_report.py::categorize_tag()` or `tools/agent-monitoring/generate_retro.py`'s
  category string-equality checks — both explicitly Out of Scope in the ticket, both confirmed to
  have no set literal to replace.
- Do not edit `tools/layer_registry.py` or `tests/tools/test_layer_registry.py` — used read-only as
  the structural template; both must be re-run unmodified as a regression guard.
- Do not add an `addable`/`exempt` boolean field to the category entry schema, and do not seed
  `phase-milestone` into `registries/tag_category_registry.jsonl` — the resolved design decision
  (investigation.md) is 4 seeded categories only, `phase-milestone` staying purely code-side via
  `is_phase_milestone_tag()`'s regex.
- Do not add a `check_categories_registered()` plural-batch helper — nothing in this ticket's scope
  calls it (unlike `check_tags_registered()`, which the Scope-phase workflow genuinely uses).
- Do not hand-write `registries/tag_category_registry.jsonl` — it must be produced by running the
  real `add-category` CLI (Step 4), never authored directly with a text editor.
- Do not reference or resurrect `docs/guidelines/tag_registry.jsonl` / `docs/guidelines/layer_registry.jsonl`
  paths anywhere (new code, new docs) — both already moved to `registries/` per
  `TCK-20260720-TAG-REGISTRY-RELOCATE`; the ticket's own "Related Docs" list is stale, use the live
  `registries/...` paths.
- Do not touch `reviews/src_export.py` / `reviews/test_export.py` — stale generated code-review
  snapshots, not real importable source; they are expected to look stale until next regeneration,
  not a regression this ticket causes.
- Do not run `pytest tests/` (full suite) — scope to the pytest commands listed in test_plan.md's
  "Scoped Pytest Commands" section.

## Dependency Map

- Step 1 (path/loader/query functions) — no dependencies, first.
- Step 2 (`add_category()`) — depends on Step 1 (`load_category_registry`, `category_registry_path`).
- Step 3 (`add-category` CLI subcommand) — depends on Step 2 (`add_category()` must exist to wire).
- Step 4 (seed the real registry file) — depends on Step 3 (uses the CLI to seed, not a raw Python
  call, so the CLI subcommand must exist first).
- Step 5 (rewire `add_tag()`/argparse, remove old constants) — depends on Step 1
  (`category_values()`) and, for its live-sourcing/CLI-choices tests to be meaningful, benefits from
  Step 4 already being done (though the unit-level rewiring itself only needs Step 1's function to
  exist, not the seeded file — `add_tag()` reads `category_values()` live regardless of what's in
  it).
- Step 6 (docs) — depends on Step 3 (the CLI command must exist to document its real flags/behavior
  accurately) and is otherwise independent of Steps 4-5.
- `test_tag_category_registry.py` (built incrementally across Steps 1, 2, 4) is only complete and
  fully green once Steps 1, 2, and 4 have all landed — do not consider it done after Step 1 alone.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1 — `registries/tag_category_registry.jsonl` seeded with exactly the 4 addable categories via real `add_category()` API | Step 4 (via Step 2/3's `add_category()`/CLI) | `category_values() == frozenset({...4 names...})` real-registry pin test (Step 4) |
| AC 2 — `add_category(category, note, root=None)` added, raises `ValueError` on non-canonical form and duplicate, identical shape to `add_layer()` | Step 2 | `add_category` tests in Step 2 (appends/returns entry, rejects non-canonical, rejects duplicate, append-only) |
| AC 3 — `category_values(root=None)` added, live frozenset, no caching, matches `layer_values()`'s implementation | Step 1 | `load_category_registry`/`category_values` tests in Step 1, plus the tmp_path frozenset test |
| AC 4 — `ADDABLE_CATEGORIES` removed; `add_tag()` and argparse `--category` choices source from `category_values()`; `phase-milestone` naturally excluded | Step 5 | `test_add_tag_rejects_invalid_category`, `test_add_tag_rejects_phase_milestone_category` (updated), `test_add_tag_category_validation_sources_from_category_values`, `test_argparse_category_choices_match_category_values` |
| AC 5 — `test_tag_registry.py` updated; new `test_tag_category_registry.py` mirrors `test_layer_registry.py`'s structure | Steps 1, 2, 4, 5 (test additions embedded in each step) | Full `test_tag_category_registry.py` + updated `test_tag_registry.py`, run together |
| AC 6 — `tag_taxonomy.md` and `ticket_tagging.md` document the new `add-category` CLI command | Step 6 | Manual doc review against Step 3's actual CLI behavior (no automated test) |
| AC 7 — 5-vs-4 seeding design question explicitly resolved during Investigate, not pre-decided | Already resolved in investigation.md (Risks and Open Questions section) — no plan step needed, carried forward as a constraint on Step 4 | `"phase-milestone" not in category_values()` pin test (Step 4) |

## Anti-Drift Notes

- **The 4-vs-5 category seeding decision is final and encoded as a test, not just a comment.**
  Step 4's pin test (`"phase-milestone" not in category_values()`) will fail immediately if a future
  edit (or an over-eager implementer "completing the set") seeds `phase-milestone` into the registry
  file. Do not "fix" that test by seeding the 5th category — the test is correct, the impulse to add
  it is the drift.
- **`add_category()`'s entry schema is exactly `{"category", "added_date", "note"}` — no
  `addable`/`exempt`/`registrable` boolean field, ever.** Adding one would technically also make
  `add_tag()`'s validation work if filtered correctly, but it contradicts the ticket's explicit
  "identical shape to `add_layer()`" requirement and reintroduces the exact two-tier
  ALL/ADDABLE split this ticket removes, just relocated into the JSON schema instead of a Python
  set subtraction.
- **Two independent registry surfaces now coexist in one file (`tools/tag_registry.py`):** the
  original tag-scoped one (`registry_path`, `load_registry`, `add_tag`, over
  `registries/tag_registry.jsonl`, keyed on `"tag"`) and the new category-scoped one
  (`category_registry_path`, `load_category_registry`, `add_category`, over
  `registries/tag_category_registry.jsonl`, keyed on `"category"`). Keep them namespaced by their
  distinct function names — do not let `add_tag()`'s internals accidentally call
  `load_category_registry()`'s file or vice versa; a copy-paste of the wrong path constant would
  silently corrupt one registry with the other's entries with no import-time error to catch it.
- **`sort_keys=True` on every written JSON line** (already used by both `add_tag()` and
  `add_layer()`) must be preserved in `add_category()` for byte-identical formatting consistency
  across all three registry files.
- **Do not invent changes to `validate_frontmatter.py` or `ticket_stats_report.py`** merely because
  they appear in the ticket's "Related Code Areas" — investigation confirmed both have zero
  tag-category code today; editing them would be scope creep with no underlying behavior to convert.
- **Parity ledger:** no existing entry overlaps this ticket (confirmed by investigation). Adding a
  new `docs/parity_ledger/infrastructure.yaml` entry (P2, `status: verified`, following the
  `LAYER-REGISTRY-CONVERSION`/`TAG-REGISTRY-RELOCATE` precedent) is optional, not required — decide
  at the Parity phase, not blocking for Plan/Implement.

## Deviations

- **Step 5's `add_tag()` category check calls `category_values()` with no `root` override, not
  `category_values(root)`.** The plan's Step 5 text ("change `if category not in
  ADDABLE_CATEGORIES:` to `if category not in category_values():`") is ambiguous about whether
  `root` is threaded through, and Step 5's own new-test description
  (`test_add_tag_category_validation_sources_from_category_values`: `add_category("new-cat",
  root=tmp_path)` then `add_tag("some-tag", "new-cat", root=tmp_path)` succeeds) reads as if it
  should be root-scoped. Implementing it root-scoped (`category_values(root)`) breaks 8 of the
  pre-existing tests Step 5's own Scope Guard explicitly requires to "pass unmodified"
  (`test_add_tag_appends_entry_and_returns_it`, `test_add_tag_rejects_duplicate_tag`,
  `test_add_tag_is_append_only_existing_entries_unchanged`,
  `test_add_tag_with_triggers_skill_writes_field`,
  `test_add_tag_without_triggers_skill_omits_field`,
  `test_get_skill_mapping_single_edit_propagates_with_zero_other_changes`,
  `test_check_tags_registered_all_registered_returns_empty`,
  `test_check_tags_registered_returns_only_unregistered_subset`) — all of these call
  `add_tag(..., root=tmp_path)` with a real category name (`subsystem-topic`,
  `process-skill-signal`) but never seed a category registry at `tmp_path`, which only worked
  before this ticket because `ADDABLE_CATEGORIES` was a global constant, not root-scoped data.
  Resolved by keeping `category_values()` **unscoped from `add_tag()`'s own `root` argument** —
  it always resolves against `tag_registry._DEFAULT_ROOT` (the real repo, now permanently seeded
  with the 4 categories by Step 4) unless a test monkeypatches `_DEFAULT_ROOT` itself. This
  satisfies the explicit "pass unmodified" constraint, which is the more concrete, enumerated
  requirement of the two. The new test's intent (proving live sourcing, not a residual hardcoded
  copy) is preserved but implemented differently: it monkeypatches
  `tag_registry._DEFAULT_ROOT` to `tmp_path` for the duration of the test (rather than passing
  `root=tmp_path` to `add_category`/`add_tag` directly), so both `add_category()` and `add_tag()`'s
  internal `category_values()` call consistently resolve against the same isolated directory
  without ever writing to the real `registries/tag_category_registry.jsonl`. Net effect on
  production code is the same either way — `add_tag()`'s category validation is anchored to
  whatever the live category registry is at the module's default root, exactly like the CLI `add`
  subcommand's `--category choices=sorted(category_values())` already is (computed once, unscoped,
  at parser-definition time).
