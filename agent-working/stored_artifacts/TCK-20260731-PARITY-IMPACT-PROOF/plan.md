---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-IMPACT-PROOF
artifact_type: plan
tags: [ai, observability, process-improvement, testing]
---

# Implementation Plan — TCK-20260731-PARITY-IMPACT-PROOF

## Summary

Add the Phase-2 read-only `impact`, `entry`, and `health` query surface to the existing
`tools/parity_index.py` module (extended in place — no new module, no new package, per
`v1_decisions_phase0.md`'s CLI/module-ownership decision), each backed by exact SQL lookups over
Phase 1's already-populated schema, with synthesized selection reasons (since `relation` is `NULL`
for most rows), deterministic sort orders, and explicit no-match/unknown responses. In parallel,
build a versioned equivalence fixture corpus in `tests/tools/test_parity_index.py` that proves the
new index's behavior against both legacy comparison targets (`find_p0_intersection` — P0-only,
`v2_evidence`-only, substring; `cross_reference_touched`/`derive_mapping` — all-priority,
ANY-of-multi-shard, silent-skip-on-malformed) as two independently distinct comparisons, plus a
faction-evidence case and a malformed-input divergence case. Finally, narrow Phase 1's own
`TestArchitectureGuards::test_importer_does_not_implement_impact_or_entry_or_health_cli` — an
anticipated, named-in-advance obsolescence, not a gate-dodge — down to only its still-valid
`search`-forbidden assertion. No `src/` code, no `docs/parity_ledger/*.yaml` content, and no legacy
comparison-target function are touched anywhere in this plan.

## Decisions (resolving investigation.md's two open questions)

**Decision 1 — narrowing `test_importer_does_not_implement_impact_or_entry_or_health_cli`.**
Rename the test method to `test_impact_entry_health_still_forbid_search_cli` (the exact name
`test_plan.md`'s Anti-Drift Test Guards section recommended as the new, isolated guard) and reduce
its body to only the assertions that are still true: `add_parser("search"` absent from source, and
`"search"` absent from `--help` output. The `impact`/`entry`/`health` absence assertions are
deleted, not inverted into presence-assertions here — presence is already proven positively by
Steps 2/3/5's own new tests, so duplicating it inside a renamed architecture-guard test would blur
the guard's single remaining purpose (keeping `search` out). A one-line docstring/comment on the
renamed test must state why it was narrowed and cite this ticket ID, per the investigation's
explicit instruction not to leave an implementer to discover the contradiction mid-build.

**Decision 2 — `--symbol` on `impact`.** Accept it as an explicit, documented no-op: the flag is
parsed and stored, but never used to filter `code_refs`/`test_refs`/etc. (which have no symbol
column at all — `v1_decisions_phase0.md`'s "Path-only links" decision is binding). Reasoning:
outright rejection would make the CLI reject a flag the idea doc's own sketch names as part of the
intended future surface, which is more disruptive than accepting-and-ignoring for any caller
scripting against that sketch; a documented no-op keeps the door open for a real Phase-3
symbol-resolution ticket without this ticket fabricating one. The response must never be silent
about this: whenever `--symbol` is passed, the JSON output includes a `"warnings"` list entry
stating the symbol argument was accepted but not used for filtering (v1 has no symbol-level
reference data). This is asserted by test item 14.

## Steps

### Step 1 — Shared read-only query infrastructure
**Files:** `tools/parity_index.py`
**Change:** Add, near the existing module-level constants (after `_REF_TABLES`):
- `_STATUS_SEVERITY = {"divergent": 0, "missing": 1, "unsupported": 2, "verified": 3, "legacy_verified": 4}`
  and `_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}` — used by `impact`'s sort key. Unrecognized
  values sort last (`.get(value, 99)`), never raise.
- `class IndexNotBuiltError(Exception)` and a helper `_connect_readonly(db_path: Path) ->
  sqlite3.Connection` that raises `IndexNotBuiltError` with a message pointing at `parity_index.py
  build` if `db_path` does not exist, otherwise opens the connection with `sqlite3.connect(f"file:
  {db_path}?mode=ro", uri=True)` (read-only URI mode — an explicit architectural guard that the
  read-path functions added in this ticket cannot ever write to the index, matching the module's own
  "read-only" framing).
- A helper `_selection_reason(table: str, source_field: str, relation) -> str`: returns
  `f"{table} declared via {source_field} field"` if `relation == "declared"`, else `f"{table} match
  via {source_field} field"`. This directly implements investigation.md Risk #2's requirement to
  synthesize reasons from `(table, source_field, relation)` rather than reading `relation` alone.
**Do NOT touch:** `_create_schema`, `_populate_ref_tables`, `_populate_entry_health`, or any
existing `build()` internals — this step only adds new read-side helpers alongside them.
**Verify:** No standalone test for this step (pure infrastructure); exercised transitively by Step
2's tests, which will fail to import/run correctly if this step is wrong.

### Step 2 — `entry ENTRY-ID` lookup and CLI wiring
**Files:** `tools/parity_index.py`
**Change:** Add `def entry(entry_id: str, db_path=None) -> dict`. Opens the index via
`_connect_readonly`, `SELECT *` from `entries` by `id`. If no row: return
`{"entry_id": entry_id, "found": False}` (explicit unknown marker — never `None`/empty dict). If
found: return `{"entry_id": entry_id, "found": True, "record": {...all 14 entries columns...},
"code_refs": [...], "test_refs": [...], "constraint_refs": [...], "ticket_refs": [...],
"health_findings": [...]}`, each ref list containing `{"path": ..., "source_field": ...,
"selection_reason": _selection_reason(table, source_field, relation)}` rows ordered by `(path,
source_field)`, and `health_findings` as `[{"finding_type": ..., "detail": ...}]` ordered by
`finding_type`. Wire into `main()`: `entry_parser = subparsers.add_parser("entry", ...)`,
`entry_parser.add_argument("entry_id")`, `entry_parser.add_argument("--db-path",
default=str(DEFAULT_DB_PATH))`; dispatch on `args.command == "entry"`, print via
`serialize_manifest(...)`, always exit 0 for a syntactically valid query (an explicit
`found: False` is a successful query, not a CLI failure) unless `IndexNotBuiltError` is raised, in
which case print a structured `{"status": "error", "detail": str(exc)}` and exit 1.
**Do NOT touch:** the `build` subparser or its argument set.
**Verify:** `test_entry_returns_full_normalized_record_for_known_id`,
`test_entry_returns_explicit_unknown_for_missing_id` (test_plan.md items 3, 4).

### Step 3 — `impact --changed-path [--test]` exact lookup and CLI wiring
**Files:** `tools/parity_index.py`
**Change:** Add `def impact(changed_path=None, test_path=None, symbol=None, db_path=None) -> dict`.
If both `changed_path` and `test_path` are `None`, return an explicit
`{"status": "no_filter_provided", "results": []}` (never silently run an unbounded query). Otherwise:
if `changed_path` given, exact-match (`WHERE path = ?`) against `code_refs`, `constraint_refs`, and
`ticket_refs`; if `test_path` given, exact-match against `test_refs`. Union the matched
`(entry_id, table, path, source_field, relation)` rows, join each to its `entries` row for
`priority`/`status`, and build one result item per `(entry_id, table, path)` with a
`selection_reason` from Step 1's helper. Sort results by `(_PRIORITY_ORDER[priority],
_STATUS_SEVERITY[status], entry_id)` — the exact tie-break order test item 1 requires. If the
filters produced zero rows, return `{"status": "no_match", "results": []}` (distinct from
`no_filter_provided` — an explicit, labeled empty result, per AC #1's "explicit no-match rather than
an implicit success"). Otherwise `{"status": "ok", "results": [...]}`. Wire into `main()`:
`impact_parser = subparsers.add_parser("impact", ...)`, `--changed-path`, `--test`, `--db-path`
arguments (symbol wired in Step 4).
**Do NOT touch:** `find_p0_intersection` or `cross_reference_touched`/`derive_mapping` in the
legacy modules — this is a new, independent query path, not a refactor of theirs.
**Verify:** `test_impact_returns_sorted_deterministic_schema_for_known_changed_path`,
`test_impact_returns_explicit_no_match_for_unknown_path` (test_plan.md items 1, 2).

### Step 4 — `--symbol` inert no-op on `impact`
**Files:** `tools/parity_index.py`
**Change:** Add `impact_parser.add_argument("--symbol", default=None)` to Step 3's subparser and
thread `symbol` through to `impact()`'s existing `symbol` parameter (already accepted in Step 3's
signature, unused for filtering). When `symbol is not None`, append to the returned dict:
`"warnings": ["--symbol was accepted but not used for filtering; v1 has no symbol-level reference "
"data (see v1_decisions_phase0.md \"Path-only links\")"]`. When `symbol is None`, omit the
`"warnings"` key entirely (do not emit an empty list — keeps the "documented only when relevant"
contract clean). Implements Decision 2 above.
**Do NOT touch:** any ref-table schema or matching logic — `symbol` must never reach a `WHERE`
clause anywhere.
**Verify:** `test_impact_never_claims_symbol_level_match` (test_plan.md item 14).

### Step 5 — `health [--subsystem] [--priority]` and CLI wiring
**Files:** `tools/parity_index.py`
**Change:** Add `def health(subsystem=None, priority=None, db_path=None) -> dict`. Base query:
`SELECT entries.id, entries.shard, entries.subsystem, entries.priority, entry_health.finding_type,
entry_health.detail FROM entry_health JOIN entries ON entries.id = entry_health.entry_id`, with
optional `WHERE entries.subsystem = ?` / `AND entries.priority = ?` appended only when the
corresponding argument is given (exact match only — no coercion or fuzzy matching, per the ticket's
own Scope line "without inventing a relationship"). Order by `(shard, id)` — reusing the exact
convention already used by `_populate_ref_tables`/`_populate_entry_health`'s own `ORDER BY shard,
id`, per test_plan.md item 5's requirement to match "every other Phase-1 SELECT's ordering
convention." Also read one row from `ledger_generation` for a summary header
(`schema_version`, `built_at`, `shard_count`, `entry_count`, `fts5_available`). Return
`{"summary": {...}, "findings": [{"entry_id":..., "shard":..., "subsystem":..., "priority":...,
"finding_type":..., "detail":...}, ...]}`. Output serialized with `serialize_manifest` (the module's
existing convention). Wire into `main()`: `health_parser = subparsers.add_parser("health", ...)`,
`--subsystem`, `--priority`, `--db-path`.
**Do NOT touch:** `entry_health`'s population logic (`_populate_entry_health`) — this step is a
read/format layer only, never a write, and never invents a new `finding_type`.
**Verify:** `test_health_output_is_ordered_and_machine_readable` (test_plan.md item 5).

### Step 6 — Update module docstring to reflect Phase 2 delivery
**Files:** `tools/parity_index.py`
**Change:** Replace the docstring's line "`impact_candidates (the Phase-2 impact query view) is
intentionally not built here -- see TCK-20260731-PARITY-IMPACT-PROOF.`" with a truthful statement,
e.g.: "`impact`, `entry`, and `health` (the Phase-2 read path) were added by
TCK-20260731-PARITY-IMPACT-PROOF on top of this module's Phase-1 schema; `search` (FTS-backed)
remains out of scope and unimplemented." This is a documentation-accuracy fix, not a reopening of
any Phase-1 decision — Phase 1's Decisions 1–3 (FTS5 seam, abort semantics, `entry_fts` naming) are
untouched.
**Do NOT touch:** any other paragraph of the docstring (atomic-lifecycle rationale, path-only-links
rationale, `entry_health` materialization rationale all stay exactly as Phase 1 wrote them).
**Verify:** No dedicated test (docstring prose); implicitly covered by the fact that
`tests/tools/test_parity_index.py` loads the module successfully via `_load_module()` in every test.

### Step 7 — Narrow the obsolete architecture-guard test
**Files:** `tests/tools/test_parity_index.py`
**Change:** In `TestArchitectureGuards`, rename
`test_importer_does_not_implement_impact_or_entry_or_health_cli` to
`test_impact_entry_health_still_forbid_search_cli` and reduce its body to:
```python
def test_impact_entry_health_still_forbid_search_cli(self):
    """Narrowed by TCK-20260731-PARITY-IMPACT-PROOF: Phase 1's guard originally forbade
    impact/entry/health entirely. Phase 2 (this ticket) is the named, anticipated
    successor authorized to add exactly those three subcommands (see Phase 1's own
    plan.md Scope Guards forward reference). Only `search` (FTS-backed) remains out of
    scope and is still asserted absent here.
    """
    source = _MODULE_PATH.read_text(encoding="utf-8")
    assert 'add_parser("search"' not in source

    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    combined = result.stdout + result.stderr
    assert "build" in combined
    assert "search" not in combined
```
This implements Decision 1 above verbatim. Do not touch
`test_no_mutation_cli_or_write_path_to_docs_parity_ledger` in the same class — it is unaffected and
must remain exactly as Phase 1 wrote it (extended, not replaced, by Step 14 below).
**Do NOT touch:** any other test class in the file at this step.
**Verify:** `pytest tests/tools/test_parity_index.py::TestArchitectureGuards -v` — the renamed test
passes; confirms the guard's remaining purpose (no `search`) is intact after Steps 2–5 added
`impact`/`entry`/`health`.

### Step 8 — Equivalence fixture: P0-substring vs. all-priority (`find_p0_intersection`)
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_equivalence_p0_substring_vs_all_priority_documented`. Build a fixture corpus
(via `_make_corpus`) with one P0 entry and one P1 entry in the same shard, both with `v2_evidence`
containing the same `src/` path (e.g. `src/engine/legality.py`). Build the index. Import
`find_p0_intersection` directly from `tools.parity_ledger_scan` (module-path import matching that
file's own existing test idiom) and call it with `files_changed=["src/engine/legality.py"]`,
`ledger_dir` pointed at the fixture's YAML directory. Assert it returns only the P0 entry. Call the
new `impact(changed_path="src/engine/legality.py", db_path=...)` and assert both entries are present
in `results`. Inline comment must state this is a labeled, intentional all-priority behavior, not an
accidental omission of the legacy P0 filter.
**Do NOT touch:** `tools/parity_ledger_scan.py` itself.
**Verify:** `test_equivalence_p0_substring_vs_all_priority_documented` (test_plan.md item 6).

### Step 9 — Equivalence fixture: ANY-of multi-shard semantics vs. `cross_reference_touched`/`derive_mapping`
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_equivalence_any_of_multi_shard_semantics_matches_legacy`, mirroring
`test_derive_mapping_handles_multi_subsystem_file`'s exact fixture shape (same `src/` path cited by
two different shards' `v2_evidence`). Import `derive_mapping` from
`tools.gate_checks.parity_updater_static` and assert it accumulates both canonical filenames for
that path. Build the same fixture through the new importer and assert `impact(changed_path=...)`
returns candidate entries from both shards — matching the ANY-of-candidates semantics, not narrowing
to one.
**Do NOT touch:** `tools/gate_checks/parity_updater_static.py`.
**Verify:** `test_equivalence_any_of_multi_shard_semantics_matches_legacy` (test_plan.md item 7).

### Step 10 — Equivalence fixture: malformed-input treatment divergence
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_equivalence_malformed_input_treatment_documented_as_divergence`. Reuse
`test_duplicate_cross_shard_id_rejected_at_import`'s / Group 2's malformed-shard fixture pattern
(a shard with unparseable YAML alongside a valid shard). Call `derive_mapping` against the same
directory and assert it silently skips the malformed shard and returns a mapping built only from the
valid one (matching `test_derive_mapping_skips_malformed_yaml_file`'s existing behavior). Call
`_pi.build(...)` against the same directory and assert `report["status"] == "failed"` with
`failure_class == "ShardParseError"` and no database is produced. Assert explicitly, with an inline
comment, that these two outcomes are a **labeled intentional divergence** — the test must not
attempt to reconcile them into equal behavior.
**Do NOT touch:** `derive_mapping`'s `except Exception: continue` — reproducing it as comparison
evidence only, never "fixing" it.
**Verify:** `test_equivalence_malformed_input_treatment_documented_as_divergence` (test_plan.md item 8).

### Step 11 — Faction evidence case
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`. Build a
fixture corpus including a `faction.yaml` shard entry whose `v2_evidence` cites a real-shaped
`src/`/`tests/` path. Assert: (a) `find_p0_intersection` and `cross_reference_touched`/
`derive_mapping`, run against the same fixture directory, never see this entry (mirroring
`test_only_scans_canonical_eight_not_faction` / `test_excludes_faction_yaml`'s exact assertion
shape); (b) the new `impact(changed_path=...)` and `entry("...")` calls against the built index DO
surface it. This is the ticket's single most load-bearing new test per test_plan.md's Anti-Drift Test
Guards.
**Do NOT touch:** `CANONICAL_LEDGER_FILES` in either legacy module.
**Verify:** `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`
(test_plan.md item 9).

### Step 12 — All-nine-shards coverage via `entry`/`impact`
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_impact_and_entry_cover_all_nine_shards_including_faction`, built directly on
the existing `_full_nine_shard_corpus(tmp_path)` fixture builder (reused, not reinvented). After
building the index, call `entry(...)` for each of the 9 generated IDs (`f"{filename[:4].upper()}-001"`
per `_full_nine_shard_corpus`'s own naming) and assert `found: True` for every one, including the
`faction.yaml`-derived ID. Add a `v2_evidence` path reference to the `faction.yaml` shard's fixture
entry specifically for this test and assert `impact(changed_path=...)` surfaces it.
**Do NOT touch:** `_full_nine_shard_corpus`/`_NINE_SHARD_FILENAMES` themselves — reuse as-is.
**Verify:** `test_impact_and_entry_cover_all_nine_shards_including_faction` (test_plan.md item 10).

### Step 13 — Determinism of repeated read queries
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_impact_query_is_reproducible_on_unchanged_index`, extending
`TestDeterminism`. Build one index from a fixture corpus, then call `impact(...)`, `entry(...)`, and
`health(...)` twice each against the same unchanged `db_path` and assert
`serialize_manifest(result_1) == serialize_manifest(result_2)` byte-for-byte for every one of the
three functions.
**Do NOT touch:** `test_build_is_deterministic_on_unchanged_source` — add alongside it, not in place
of it.
**Verify:** `test_impact_query_is_reproducible_on_unchanged_index` (test_plan.md item 12).

### Step 14 — Extend the write-path guard to `health`
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add `test_health_subcommand_never_writes_to_docs_parity_ledger`, extending
`test_no_mutation_cli_or_write_path_to_docs_parity_ledger`'s source-text scan (already present in
`TestArchitectureGuards`, unmodified by Step 7) with a behavioral check: build a fixture index with a
shard containing `missing_test_path`/`legacy_unstructured` findings, snapshot the shard YAML file's
bytes, call `health(...)`, and assert the YAML file's bytes are unchanged. This is additive
(new test method), not a rewrite of the existing source-text-scan test.
**Do NOT touch:** the existing `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` test body.
**Verify:** `test_health_subcommand_never_writes_to_docs_parity_ledger` (test_plan.md item 13).

### Step 15 — Full regression confirmation (no code change)
**Files:** none (verification only)
**Change:** Run the three scoped pytest commands from `test_plan.md`:
```
pytest tests/tools/test_parity_index.py -v
pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v
pytest tests/tools/test_parity_index_baseline.py -v
```
Confirm all green (13/13 legacy, all Phase-1 + Phase-2 tests in `test_parity_index.py`, Phase-0
suite untouched). This step directly satisfies test_plan.md item 11
(`test_legacy_scanner_and_static_gate_tests_unmodified_and_green`) "by the Scoped Pytest Command"
rather than a literal wrapper test, per the test plan's own stated precedent. Also run
`python3 tools/validate_frontmatter.py` against this ticket's three staging artifacts.
**Do NOT touch:** `tests/tools/test_build_index.py` — excluded from this ticket's required-green
set per test_plan.md (pre-existing, unrelated Makefile failure).
**Verify:** All three scoped commands exit 0; frontmatter validation passes.

## Scope Guards

- Do not modify `tools/parity_ledger_scan.py` or `tools/gate_checks/parity_updater_static.py` —
  read-only comparison targets; any edit invalidates the equivalence proof itself.
- Do not modify `tests/tools/test_parity_ledger_scan.py` or `tests/tools/test_parity_updater_static.py`
  — zero edits authorized; they are the fixed comparison-behavior baseline.
- Do not modify `tools/parity_index_baseline.py` beyond the existing `_sha256_hex`/
  `serialize_manifest` imports already in use — reuse, do not extend or refactor it.
- Do not implement a `search` (FTS-backed) subcommand, even though `entry_fts` already exists from
  Phase 1 and would make it technically easy — explicitly Out of Scope.
- Do not wire `impact`/`entry`/`health` into any live workflow gate, agent prompt, or
  `.claude/workflows/implement-ticket.js` phase — explicitly Out of Scope; this ticket produces
  equivalence evidence, it does not consume it to flip a gate.
- Do not add any mutation command, or any write call targeting `docs/parity_ledger/*.yaml`, from any
  new code added in this ticket.
- Do not fabricate or imply a symbol-level match anywhere in `impact`'s output — `--symbol` is an
  inert, documented no-op only (Decision 2).
- Do not invent a new `entry_health` `finding_type`, or write back to `entries`/`entry_health`/
  `docs/parity_ledger/*.yaml` from the `health` subcommand — read/format layer only.
- Do not use the live 1,945-entry corpus as the primary test substrate for the equivalence proof —
  small, synthetic, `tmp_path`-isolated fixtures only, per Phase 1's own established precedent.
- Do not touch `_create_schema`, `_populate_entries`, `_populate_ref_tables`,
  `_populate_entry_health`, `_populate_entry_fts`, `_validate_build`, `_atomic_replace_db`, or the
  `build` subparser/function — Phase 1's importer internals are out of scope for this ticket.
- Do not add or edit any `docs/parity_ledger/*.yaml` entry — investigation.md's Parity Ledger
  Overlap section confirms none is required (no `src/` behavior change, no `v2_evidence` touched).

## Dependency Map

- Step 1 is a prerequisite for Steps 2, 3, 5 (shared helpers/constants).
- Step 3 is a prerequisite for Step 4 (adds `--symbol` on top of Step 3's `impact` signature/CLI).
- Steps 2, 3, 4, 5 must all be complete before Step 6 (docstring) and Step 7 (test narrowing) — the
  guard test's new form only makes sense once all three subcommands genuinely exist.
- Steps 8–14 each depend on Steps 1–5 (they call the real `impact`/`entry`/`health`/`build`
  functions) and are otherwise mutually independent — order 8→14 as listed is a suggestion for
  readability (matching test_plan.md's AC-grouped numbering), not a hard requirement.
- Step 15 depends on all prior steps being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `impact`/`entry`/`health` deterministic, documented, explicit no-match | Steps 2, 3, 5 | `test_impact_returns_sorted_deterministic_schema_for_known_changed_path`, `test_impact_returns_explicit_no_match_for_unknown_path`, `test_entry_returns_full_normalized_record_for_known_id`, `test_entry_returns_explicit_unknown_for_missing_id`, `test_health_output_is_ordered_and_machine_readable` |
| AC #2 — compatibility suite: P0-substring vs. all-priority, ANY-of multi-shard, malformed-input, faction exclusion | Steps 8, 9, 10, 11 | `test_equivalence_p0_substring_vs_all_priority_documented`, `test_equivalence_any_of_multi_shard_semantics_matches_legacy`, `test_equivalence_malformed_input_treatment_documented_as_divergence`, `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion` |
| AC #3 — all nine shards representable; faction evidence appears despite legacy exclusion | Steps 11, 12 | `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`, `test_impact_and_entry_cover_all_nine_shards_including_faction` |
| AC #4 — legacy scanner/static-gate tests unchanged; fixture + rebuild/query reproducible | Steps 13, 15 | `test_impact_query_is_reproducible_on_unchanged_index`, scoped pytest commands (13/13 legacy green) |
| AC #5 — health reports uncertainty without modifying YAML or claiming symbol coverage | Steps 4, 5, 14 | `test_impact_never_claims_symbol_level_match`, `test_health_subcommand_never_writes_to_docs_parity_ledger` |

## Anti-Drift Notes

- The renaming/narrowing in Step 7 is an anticipated, named-in-advance test change — Phase 1's own
  plan.md Scope Guards explicitly forward-referenced this ticket ID as the one authorized to build
  `impact`/`entry`/`health`. It must not be treated as "editing a test to dodge a gate" (forbidden by
  CLAUDE.md's Hard Rules); it is fixing a test whose invariant genuinely changed. Do not narrow any
  other assertion in that test beyond the specific `impact`/`entry`/`health`-absence lines named in
  Decision 1.
- `relation` is `NULL` for all regex-matched ref rows (only direct `test_path` rows get
  `"declared"`) — Step 1's `_selection_reason` helper must be the only place that interprets this;
  do not read `relation` directly anywhere else as if it were a ready-made human-facing string.
- Keep the P0-substring (`find_p0_intersection`) and all-priority/ANY-of
  (`cross_reference_touched`/`derive_mapping`) comparisons as two separate fixtures/tests (Steps 8
  and 9) — they are independently different legacy behaviors, not one blended case, per
  investigation.md Risk #3.
- The malformed-input test (Step 10) must assert the divergence, not attempt to make
  `ShardParseError`-abort and `derive_mapping`'s silent-skip behave identically — reconciling them
  would silently reintroduce Phase 1's deliberately rejected weaker behavior.
- `--symbol`'s no-op warning (Step 4) must only appear in output when the flag is actually passed —
  do not emit an always-present empty `"warnings"` key, which would blur the signal for callers
  parsing the output.
- Use `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)` (Step 1) for all three new read
  functions — this is a real architectural guard, not decoration; it makes an accidental write from
  `impact`/`entry`/`health` fail loudly instead of silently succeeding.
- Do not let Step 6's docstring edit drift into re-litigating any Phase-1 decision (FTS5 seam, abort
  semantics, `entry_fts` naming) — touch only the one sentence that is now factually stale.

## Deviations

None from the 15 ordered steps' function signatures, schemas, sort orders, CLI flag names, or file
scope — implementation matched this plan as written.

**Step 7 test-narrowing (documented per the IMPORTER ticket's own precedent for this class of
change, even though plan-approved in advance).** `tests/tools/test_parity_index.py::TestArchitectureGuards::
test_importer_does_not_implement_impact_or_entry_or_health_cli` was renamed to
`test_impact_entry_health_still_forbid_search_cli` and its `add_parser("impact"`/`add_parser("entry"`/
`add_parser("health")`-absence assertions (source-text scan) and the `"--help"` output's
`"impact"`/`"entry"` absence assertions were deleted rather than inverted into presence-assertions.
This is not a gate-dodge: Phase 1's own plan.md named this exact ticket ID as the one authorized to
add this CLI surface, so the test's original invariant was correctly scoped to Phase 1 and became
obsolete by design once Phase 2 shipped. Presence of `impact`/`entry`/`health` is now positively
covered by `TestEntryQuery`, `TestImpactQuery`, and `TestHealthQuery` (Steps 2/3/5's own tests) rather
than by this now-narrower guard, so no coverage was lost — it moved to a more specific location. Only
the still-valid `search`-forbidden assertions remain in the renamed test, matching
`stored_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/plan.md`'s own recorded precedent (2026-08-02)
for handling a cross-ticket test-assertion collision by narrowing the older test rather than leaving a
contradiction in place.
