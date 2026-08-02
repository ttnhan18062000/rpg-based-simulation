---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-IMPACT-PROOF
artifact_type: test_plan
tags: [ai, observability, process-improvement, testing]
---

# Test Plan — TCK-20260731-PARITY-IMPACT-PROOF

## Regression Surface

This ticket touches no `src/` code. It extends `tools/parity_index.py` (adding `impact`/`entry`/
`health` read functions and CLI subcommands on top of Phase 1's existing `build()`/schema) and
extends `tests/tools/test_parity_index.py`. It must not modify `tools/parity_ledger_scan.py`,
`tools/gate_checks/parity_updater_static.py`, or `tools/parity_index_baseline.py` — those are
read-only comparison targets/reused conventions.

**Unit (must stay green after this ticket, confirmed 44/44 passing today before implementation):**
- `tests/tools/test_parity_ledger_scan.py` — 3 tests. Read-only reference; zero edits authorized.
- `tests/tools/test_parity_updater_static.py` — 10 tests. Read-only reference; zero edits authorized.
- `tests/tools/test_parity_index_baseline.py` — Phase-0 suite; zero edits authorized, must remain green.
- `tests/tools/test_parity_index.py` — Phase-1's 15 existing tests, with **one named, anticipated
  exception**: `TestArchitectureGuards::test_importer_does_not_implement_impact_or_entry_or_health_cli`
  currently asserts `impact`/`entry`/`health` are *absent* from the CLI — this ticket's whole purpose
  is to add them, so this specific test's `impact`/`entry`/`health` assertions must be narrowed or
  inverted (see investigation.md Risk #1). Its `search`-forbidden assertion (`add_parser("search"`
  and `"search"` absent from `--help`) must remain intact and unmodified, since `search` stays out
  of this ticket's scope. This is a deliberate, documented test update anticipated by Phase 1's own
  plan.md ("Phase 2 — TCK-20260731-PARITY-IMPACT-PROOF" named explicitly as the ticket authorized to
  build this CLI surface), not a scope violation or gate-gaming edit.
- Combined regression command confirmed passing today (44/44, pre-implementation):
  `pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py
  tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -q`

**Known pre-existing failure, NOT part of this ticket's regression surface, must not be fixed as a
drive-by:** `tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`
(Makefile phony-target quirk, documented by both Phase 0 and Phase 1 investigations, unrelated to
this ticket's Related Code Areas). Do not include `test_build_index.py` in this ticket's
required-green set.

**Frontmatter validation (must stay green):**
`python3 tools/validate_frontmatter.py` against this ticket's own staging artifacts.

**No integration or arena-combat tests apply** — agent-infrastructure tooling only, reconfirmed
here: no `docs/mechanics/` or `docs/engine/` contract governs parity-ledger tooling.

## New Tests Required

Mapped to this ticket's Acceptance Criteria. Exact names are recommendations; Plan may adjust
naming but must preserve one-to-one AC coverage. All new tests live in
`tests/tools/test_parity_index.py` unless noted, extending Phase 1's existing test-class/fixture
idiom (`_load_module()`, `_make_corpus`, `_full_nine_shard_corpus`, `_entry()`).

**AC #1 — `impact`/`entry`/`health` return deterministic, documented machine-readable output;
unknown paths are explicit no-match rather than an implicit success.**

1. `test_impact_returns_sorted_deterministic_schema_for_known_changed_path`
   Category: unit
   Verifies: querying `impact` against a fixture corpus with a `code_refs` row citing a known
   changed path returns a stable, documented schema (entry ID, priority, status, selection reason,
   matched path/table) in deterministic sort order (priority, status severity, stable entry ID —
   per the idea doc's Read Path spec), and running the same query twice yields byte-identical output.
   Where: `tests/tools/test_parity_index.py`

2. `test_impact_returns_explicit_no_match_for_unknown_path`
   Category: unit / anti-drift guard
   Verifies: querying `impact --changed-path` against a path with zero `code_refs`/`test_refs`/
   `constraint_refs` rows returns an explicit "no match" result (a documented empty/unknown marker),
   never an implicit empty-list-as-success indistinguishable from "checked, found nothing to report."
   Where: `tests/tools/test_parity_index.py`

3. `test_entry_returns_full_normalized_record_for_known_id`
   Category: unit
   Verifies: `entry ENTRY-ID` against a fixture entry returns every `entries` column plus its
   joined `code_refs`/`test_refs`/`constraint_refs`/`ticket_refs`/`entry_health` rows in one
   structured record.
   Where: `tests/tools/test_parity_index.py`

4. `test_entry_returns_explicit_unknown_for_missing_id`
   Category: unit / anti-drift guard
   Verifies: `entry NONEXISTENT-ID` returns an explicit "unknown entry" result, never a crash, `None`,
   or an empty dict indistinguishable from a found-but-empty entry.
   Where: `tests/tools/test_parity_index.py`

5. `test_health_output_is_ordered_and_machine_readable`
   Category: unit
   Verifies: `health` against a fixture corpus with mixed finding types returns entries in stable
   `(shard, id)` order (matching every other Phase-1 SELECT's ordering convention) with the exact
   `serialize_manifest` JSON convention (`sort_keys=True, indent=2, ensure_ascii=True` + trailing
   newline).
   Where: `tests/tools/test_parity_index.py`

**AC #2 — The compatibility suite captures exact current legacy results where comparable and
documents every difference: P0-substring vs. all-priority, ANY-of multi-shard semantics,
malformed-input treatment, and faction's legacy exclusion.**

6. `test_equivalence_p0_substring_vs_all_priority_documented`
   Category: unit / equivalence-fixture guard
   Verifies: against a fixture corpus with a mix of P0 and non-P0 entries whose `v2_evidence` cites
   a changed path, `find_p0_intersection` (imported directly from `tools.parity_ledger_scan`) returns
   only the P0 hit, while the new `impact` query returns both — asserting the new index's
   all-priority behavior is a labeled, intentional difference, not an accidental omission of the
   legacy P0 filter.
   Where: `tests/tools/test_parity_index.py`

7. `test_equivalence_any_of_multi_shard_semantics_matches_legacy`
   Category: unit / equivalence-fixture guard
   Verifies: against a fixture corpus where the same `src/` path is cited by two different shards'
   `v2_evidence` (mirroring `test_derive_mapping_handles_multi_subsystem_file`'s exact fixture
   shape), the new index's `impact`/`entry` result for that path includes both candidate entries —
   matching `cross_reference_touched`'s ANY-of-candidates semantics, not narrowing to a single match.
   Where: `tests/tools/test_parity_index.py`

8. `test_equivalence_malformed_input_treatment_documented_as_divergence`
   Category: unit / equivalence-fixture guard
   Verifies and documents (via assertion + inline comment, not just a passing test) that
   `derive_mapping`'s silent `except Exception: continue` on a malformed shard (see
   `test_derive_mapping_skips_malformed_yaml_file`) is a **labeled intentional difference** from the
   index importer's `ShardParseError` whole-build-abort behavior — this test must not attempt to
   make the two behaviors equal; it proves and records that they differ, and that no rebuild masks
   the difference silently.
   Where: `tests/tools/test_parity_index.py`

9. `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`
   Category: unit / faction evidence case (explicit AC requirement)
   Verifies: a fixture `faction.yaml` shard with a `v2_evidence` citation to a real `src/`/`tests/`
   path produces `code_refs`/`test_refs` rows and appears in `impact`/`entry` results, **despite**
   both `find_p0_intersection` (`CANONICAL_LEDGER_FILES` excludes `faction.yaml`) and
   `cross_reference_touched`/`derive_mapping` (same exclusion) never seeing it at all — directly
   exercising `test_only_scans_canonical_eight_not_faction` and `test_excludes_faction_yaml`'s
   fixture shapes as the "legacy exclusion" baseline this new behavior contrasts against. This test
   is the ticket's explicit "include a faction evidence case" requirement.
   Where: `tests/tools/test_parity_index.py`

**AC #3 — All nine shards and their IDs can be represented; faction's source/test evidence appears
in the new read path despite its zero-P0/legacy exclusion status.**

10. `test_impact_and_entry_cover_all_nine_shards_including_faction`
    Category: unit
    Verifies: against `_full_nine_shard_corpus` (Phase 1's existing 9-shard fixture builder,
    reused not reinvented), `entry` resolves an ID from every one of the 9 shards including
    `faction.yaml`'s, and `impact` can surface a `faction.yaml`-shard entry when its evidence
    matches a queried path.
    Where: `tests/tools/test_parity_index.py`

**AC #4 — Legacy scanner/static-gate tests remain unchanged in behavior, and every synthetic
fixture result plus an unchanged rebuild/query is reproducible.**

11. `test_legacy_scanner_and_static_gate_tests_unmodified_and_green`
    Category: regression / anti-drift guard
    Verifies: `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -q`
    exits 0 (13/13) after this ticket's implementation — satisfied by the Scoped Pytest Command
    below rather than a literal wrapper test, per Phase 1's own established precedent for this
    exact class of guard (its own `test_legacy_eight_shard_tests_unmodified_and_green` recommendation).
    Where: N/A if satisfied by the scoped command; otherwise `tests/tools/test_parity_index.py`

12. `test_impact_query_is_reproducible_on_unchanged_index`
    Category: unit / determinism guard
    Verifies: running the same `impact`/`entry`/`health` query twice against an unchanged,
    already-built index produces byte-identical serialized output (extends Phase 1's
    `test_build_is_deterministic_on_unchanged_source` pattern to the new read functions, which did
    not exist when that test was written).
    Where: `tests/tools/test_parity_index.py`

**AC #5 — Health output reports uncertainty/missing links without modifying YAML or claiming
symbol-level coverage.**

13. `test_health_subcommand_never_writes_to_docs_parity_ledger`
    Category: architecture guard
    Verifies (source-text + behavioral): no `open(..., "w")`/`write_text` call targeting
    `docs/parity_ledger/` exists anywhere in `tools/parity_index.py` after this ticket's changes
    (extends Phase 1's existing `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` scope to
    cover the new code added by this ticket, not just Phase 1's own code), and a `health` call
    against a fixture with `missing_test_path`/`legacy_unstructured` findings leaves the source YAML
    fixture files byte-identical before/after.
    Where: `tests/tools/test_parity_index.py`

14. `test_impact_never_claims_symbol_level_match`
    Category: unit / anti-drift guard
    Verifies: passing a `--symbol` argument to `impact` (per the idea doc's CLI sketch) either
    returns a documented "unsupported at v1" response or is accepted as an inert no-op filter that
    never narrows results based on symbol identity — never silently fabricates or implies a
    symbol-level match, per `v1_decisions_phase0.md`'s "Path-only links" decision. Exact behavior
    (reject vs. no-op) is a Plan decision (see investigation.md Risk #4); this test asserts whichever
    is chosen is explicit and documented, not silent.
    Where: `tests/tools/test_parity_index.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_index.py -v
```
This ticket's extended importer/read-path test suite — all Phase 1 tests (with the one named,
anticipated `TestArchitectureGuards` update) plus all new tests above.

```
pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v
```
Regression confirmation — legacy tools' behavior stays exactly as documented (13 tests, confirmed
13/13 passing in this investigation before implementation). Zero edits authorized to these files.

```
pytest tests/tools/test_parity_index_baseline.py -v
```
Regression confirmation — Phase-0's baseline/fixture/decision-doc suite stays green and untouched.

```
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/investigation.md staging_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/test_plan.md staging_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/plan.md
```
Frontmatter validity for this ticket's own staging artifacts — required for `done-checker`'s
`frontmatter_valid` condition.

**Never:** `pytest tests/` (repo-wide) — this ticket's regression surface is narrowly
`tests/tools/` only; no `src/` or simulation-domain test directory is affected.

**Do NOT include `tests/tools/test_build_index.py`** in the required-green regression set — it has
one pre-existing, unrelated failure (Makefile phony-target quirk, documented by both Phase 0 and
Phase 1) this ticket must not be blamed for or attempt to fix.

## Anti-Drift Test Guards

- **`test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`** (item 9) — the
  direct, ticket-mandated proof that the new index's all-shard behavior is real and observable, not
  just claimed in a docstring. This is the single most load-bearing new test in this plan, since
  it is the one AC #2/AC #3 both explicitly name by requirement text ("include a faction evidence
  case").
- **`test_equivalence_malformed_input_treatment_documented_as_divergence`** (item 8) — guards
  against a well-intentioned but wrong "fix" that tries to make the new importer silently skip a
  malformed shard the way `derive_mapping` does, which would silently reintroduce Phase 1's
  explicitly rejected weaker behavior (build-abort was a deliberate strengthening, not an oversight
  to reconcile away).
- **`test_impact_never_claims_symbol_level_match`** (item 14) — guards against future scope creep
  where a `--symbol` flag, once present in the CLI surface, gets "helpfully" wired to a heuristic
  path-to-symbol guess by a later change, silently violating the v1 path-only-links boundary.
- **`test_health_subcommand_never_writes_to_docs_parity_ledger`** (item 13) — extends Phase 1's own
  write-path guard to the code this ticket adds; without re-running this check against the
  post-Phase-2 source, a new `health`-adjacent helper could accidentally introduce a write path
  Phase 1's original guard never had the chance to catch.
- **`test_equivalence_p0_substring_vs_all_priority_documented`** (item 6) — guards against silently
  narrowing the new `impact` query to P0-only (which would look like a "safer" default but would
  contradict the ticket's explicit all-priority requirement) or, in the other direction, against a
  future change that quietly drops the labeled-difference documentation and lets the two priority
  scopes drift apart unnoticed.
- **New guard recommended for Plan to size:
  `test_impact_entry_health_still_forbid_search_cli`** — a narrower replacement for the
  `search`-forbidden half of Phase 1's `test_importer_does_not_implement_impact_or_entry_or_health_cli`
  (the half that must survive this ticket unmodified) — isolating it from the `impact`/`entry`/
  `health` assertions this ticket is expected to invert, so the anti-drift intent (no FTS-backed
  `search` surface) is preserved with its own named test rather than getting lost when the parent
  test is edited.
