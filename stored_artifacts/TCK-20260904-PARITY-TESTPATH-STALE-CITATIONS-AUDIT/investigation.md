---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT
artifact_type: investigation
tags: [testing, registry]
---

# Investigation — TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT

All figures verified against `origin/main` on 2026-09-11. Every count below was produced by running
code against the live ledger, not estimated.

## 0. Context-scan note

The mandatory `mcp__knowledge-search__search_docs` step could not run: the semantic index is not
built in this worktree (`{"error":"index not found"}`). Duplicate-work detection used the documented
fallback — a `docs/REGISTRY.yaml` query — which surfaced 23 related tickets. The two load-bearing ones
are covered in §4 and §5.

## 1. The ticket's premise, re-verified

The ticket estimated ~44 stale citations from a grep for two path prefixes (`tests_v2/`,
`tests/rpg/`). Re-enumerated with an actual existence check using the repo's own
`mechanics_auditor_static.parse_test_path_citations()`:

**28 genuinely stale entries — every one `status: verified`, and 27 of 28 are `priority: P0`.**

- 27 are found by the parser directly.
- 1 more (`TOWN-011`) hides inside an entry the parser cannot parse (see §3).

A first pass with a naive parser reported 53. That figure was wrong: it did not strip backticks, so
valid backtick-wrapped paths looked nonexistent. It is recorded here only so the discrepancy is not
rediscovered. The ticket's ~44 was roughly right in *distribution* (combat_movement, strategic_cognition,
substrate dominate) because it grepped the right prefixes; it undercounted because prefix-matching
cannot see entries whose citation is embedded in prose.

## 2. Resolution classes for the 28

Classified by recovering the deleted test tree from git history (`tests_v2/` existed in 12 commits
and was deleted in `828cb73f` / `6e5c2899` with **zero renames detected** — content that survives
under `tests/` was re-created, not moved).

### Class A — repoint candidate (7)

A same-named successor file exists under `tests/`.

| Entry | Stale citation | Successor | Node-level status |
|---|---|---|---|
| `STRAT-014` | `tests_v2/strategic/test_interruption_resistance.py::TestCognitionProfile` | `tests/unit/strategic/test_interruption_resistance.py` | **Confirmed** — `TestCognitionProfile` exists there |
| `COMB-003` | `tests_v2/test_occupancy_conflicts.py` | `tests/unit/movement/test_occupancy_conflicts.py` | Unverified |
| `COMB-008` | `tests_v2/test_substrate_hardening.py` | `tests/unit/core/test_substrate_hardening.py` | Unverified |
| `STRAT-011` | `tests_v2/strategic/test_event_interpretation.py` | `tests/unit/strategic/test_event_interpretation.py` | Unverified |
| `SUB-029` | `tests_v2/test_snapshot_integrity.py` | `tests/integration/kernel/test_snapshot_integrity.py` | Unverified |
| `TOWN-011` | `tests/rpg/test_resource_conservation_v2.py` | `tests/integration/kernel/test_resource_conservation_v2.py` | Unverified |
| `TOWN-012` | `tests/rpg/test_resource_conservation_v2.py` | same | Unverified |

A surviving filename is not evidence of surviving coverage — see `STRAT-004` in Class C, whose cited
test exists nowhere. Each Class A entry needs its successor confirmed to actually test the entry's
`text` before repointing.

### Class B — deleted in history, no successor (7)

The whole `tests_v2/parity/*_parity.py` suite. Its tests were recovered from the deletion patches and
searched for by name across the current tree. **Zero of seven survive.**

| Entries | Deleted file | Recovered tests (none in current tree) |
|---|---|---|
| `COMB-001`, `COMB-002` | `test_movement_parity.py` | `test_movement_parity_with_oracle` |
| `COMB-004`, `COMB-005` | `test_combat_parity.py` | `test_damage_formula_parity`, `test_evasion_absence_divergence` |
| `COMB-009` | `test_oa_parity.py` | `test_no_oa_if_no_hostiles`, `test_oa_triggered_on_disengagement_hardened` |
| `COMB-010`, `COMB-013` | `test_tactical_parity.py` | `test_retreat_threshold_divergence`, `test_target_selection_parity` |

### Class C — phantom citation (14)

**The cited file never existed in this repository, at any point in its history.** Confirmed against the
complete inventory of every path ever committed under `tests_v2/`. These `verified` entries were never
backed by a test here.

`PROG-001` (`test_evolution_parity.py`), `SOC-052` / `SUB-007` / `SUB-073` (`test_entity_construction.py`),
`STRAT-001` / `STRAT-002` / `STRAT-003` / `STRAT-004` (`test_strategic_persistence.py`), `STRAT-005`
(`test_blocker_resolution.py`), `STRAT-012` (`test_uncertainty_contract.py`), `SUB-022` / `SUB-034`
(`test_isolation_boundary.py`), `WORLD-061` (`test_weather.py`), `WORLD-062` (`test_transformations.py`).

`WORLD-061` and `WORLD-062` are a sub-case: the cited *path* is phantom, but same-named files now exist
at `tests/unit/world/`. They may be coverage written later under the real path, and need the same
per-entry check as Class A.

## 3. Root cause — `test_path` has no format contract

Of 613 populated `test_path` values, 304 are a clean single `path` or `path::symbol`. The rest mix
backticks, parenthetical prose, and multiple citations joined by `,`, `;`, `+`, or the word "and".
Many are not citations at all but **test-run reports**: `tests/unit/observability/ full suite (798
passed, 6 skipped, unchanged from pre-cutover ...)`, `-- 27 tests (15 pre-existing + 12 new)`.
`INFRA-342`'s value is roughly 600 characters of test-class inventory and deletion history.

127 entries cannot be parsed even by the repo's tolerant parser.

This is directly why stale citations went undetected: two tools read `test_path`, **using different
rules** (§4).

## 4. Two parsers, and the index is blind to most of the ledger

| Tool | Parser | Accepts |
|---|---|---|
| `tools/parity_index.py` | `_TEST_PATH_DECLARED_RE = ^tests/[\w./:-]+\.py(::[\w_]+)?$` | one path, at most one `::` level |
| `tools/gate_checks/mechanics_auditor_static.py` | `parse_test_path_citations()` | backticks, `,`/`+`/`;` multi-citation, multi-level node-ids; runs pytest |

Only entries matching the index regex are inserted as `test_refs`, and only those receive an
`absent_file` health check. **The index is blind to 345 of 613 entries (56%), including 91 that are
`verified` + `P0`.**

Breakdown of the 345 blind entries:

| Count | Kind |
|---|---|
| 28 | Well-formed multi-level node-ids (`path::Class::method`) — **a regex bug**, not bad data |
| 22 | Clean except for wrapping backticks |
| 155 | Multiple citations, no prose |
| 87 | Contain prose or test-run report text |
| 53 | Other |

The ticket's own acceptance criterion measures success via the index's `absent_file` count. That
instrument cannot see over half the ledger — this is the reachability findings doc's Finding 4
(conclusions drawn from a broken measurement apparatus) occurring inside the very ticket meant to fix it.

`ci_workflow_test_coverage.py` also parses paths but reads workflow YAML, not parity citations. There
are exactly two parity `test_path` parsers.

## 5. Constraints from prior decisions

- **The index is path-level by design.** `v1_decisions_phase0.md` §"Path-only links": v1 resolves
  references to path level only, with no symbol resolution. A missing symbol inside an existing file is
  out of the index's scope deliberately, not by oversight. Symbol-level checking already exists in
  `verify_entry_test_path()`, which runs pytest on the node-id.
- **Never sweep.** `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s plan (Anti-Drift Notes): "82% of
  `verified` entries have no `test_path` today... This check will legitimately FAIL for the vast
  majority of the ledger if ever run in bulk... never a sweep." Any format contract must apply at write
  time to entries being written, not as a repo-wide validation pass.
- **Corpus test is safe.** `TestValidateEntryAgainstRealMultiSegmentCorpus` runs `validate_entry()` on 10
  real `WORLD-DEMO`/`WORLD-CULT` entries. All 10 pass the shared parser, including the 4 the index regex
  rejects. Adopting the shared parser in `validate_entry()` does not break it.
- **Baselines.** `test_parity_index_baseline.py:172` hardcodes `live_missing == 1315` — CLAUDE.md's
  documented drift pattern, recurring across at least five prior hotfix tickets. It counts entries with
  *no* `test_path`, which a parser change does not touch. No test hardcodes an `absent_file` count.

## 6. Falsified claims found in the ledger

- `TOWN-005` and `TOWN-006` — the precedent this ticket was told to generalize — state that
  `tests_v2/test_occupancy_conflicts.py` "never existed in this repo, only in a pre-migration test
  tree". **That file is in the git history inventory.** Generalizing this precedent would propagate a
  falsified claim, and would spread the prose-in-`test_path` pattern that caused the problem.
- `TCK-20260705`'s note that `tests_v2/` "does not exist anywhere in this repo" is true of the current
  tree only; it existed in 12 commits.

## 7. Adjacent finding — oracle data is guarded for existence, never for parity

`tests/parity/oracles/{movement,town,interaction}_oracle/results.json` survived the migration. Their
only consumer is `tests/integrity/test_parity_guards.py`, which asserts the files exist, parse as JSON
lists with `scenario` keys, and contain certain scenario *names*. Nothing runs the simulation against
them. The file's own docstring calls the oracles "the parity truth surface". The harness that compared
behavior to them (`test_movement_parity_with_oracle`) was deleted with `tests_v2/` and never replaced.

Out of scope here; recorded as a follow-up recommendation.

## 8. What this does not establish

- That Class B or C behavior is broken. The engine likely still implements it; what is missing is
  evidence. The entries' `verified` status is unsupported, not necessarily false.
- That every Class A successor covers its entry. File survival was checked, coverage was not.
- Anything about the ~1572 entries with a null `test_path`, which is a separate, known state
  (`TCK-20260902-PARITY-TEST-PATH-GAP`).
