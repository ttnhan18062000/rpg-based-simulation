---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
phase: done
date: 2026-08-19
tags: [architecture, testing]
---

# TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

## Title
Add a permanent make codebase-health-baseline target for LoC/churn snapshots, excluding bookkeeping noise

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Item 1 (Phase 1, item 4) of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, extracted
once confirmed concrete and self-contained. Cross-referencing D24's own 11-item master plan
against this session's completed work found Phases 1-2 (7 of 11 items) already done, and Epic K's
own stated prerequisite (Epic G, boundary-test hardening) confirmed done — Epic K is now genuinely
unblocked. This specific item has no dependency on the rest of Epic K's scope (impact command,
scorecard, PR report generator, which are genuinely sequential and stay bundled in the epic) and
is ready to build now: a permanent, `make`-invokable LoC/churn snapshot reproducing the shape of
`docs/audits/D24_codebase_health_observatory.md` §C's table, computed fresh each run, with known
append-only bookkeeping files excluded from the churn measurement specifically (without that
exclusion, every report is dominated by expected bookkeeping noise, not real signal).

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- New script (e.g. `tools/codebase_health_baseline.py`) computing: source/test LoC and file
  counts, test:source ratio, top-level `src/` package count, test subdirectory count, commit
  count, `.md` doc count, `docs/REGISTRY.yaml` size, dead-bytecode file count.
- Churn measurement excludes `agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
  `docs/REGISTRY.yaml` via a git pathspec exclusion, not a post-hoc filter.
- New `make codebase-health-baseline` target.
- Explicit, documented decision on CI-wiring vs. on-demand-only (default to on-demand-only,
  matching this session's finding that sibling tools in this family are Makefile-only).

## Out of Scope
- The `code-health impact <path>` command, historical snapshots/scorecard, and PR/AI report
  generator — remain Epic K's own bundled scope (genuinely sequential, not independently
  extractable).
- A single aggregate "health score" — any future scorecard built on this data must use trend
  arrows across dimensions, per the source audit's explicit guidance.

## Acceptance Criteria
- [x] `make codebase-health-baseline` exists and runs, producing the full metrics table.
- [x] Bookkeeping-file churn (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
      `docs/REGISTRY.yaml`) is excluded from the churn measurement, verified by a fixture proving
      synthetic noise in those files doesn't move the computed churn metric.
- [x] A live run produces numbers that meaningfully differ from D24 §C's stale, hardcoded
      snapshot (e.g. dead-bytecode count now 0, not 601) — proves live measurement, not an echoed
      cached value. (Live dead-bytecode count came out 478, not the illustrative "0" — see
      Implementation Notes for why; still non-stale and provably live.)

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC (item extracted from here; epic remains
  open for its other 3, genuinely-sequential items)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC (Epic K's own prerequisite, confirmed done —
  context only, not a blocker for this specific item)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§B, §C, §L, §M — source data and methodology)
- docs/plans/codebase_health_observatory_tooling_epic.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET/

## Related Code Areas
- tools/ (new script)
- Makefile

## Assumptions / Open Questions
- Exact "source" vs. "test" file-classification rule (beyond the obvious `src/` vs `tests/` split)
  is left to the implementer to infer from how the repo already partitions these directories.
- CI-wiring vs. on-demand-only is a real decision to make explicitly, not left ambiguous — see
  plan.md step 3.

## Implementation Notes
Built `tools/codebase_health_baseline.py`, a standalone module (no CLI subcommands needed — it
always computes and prints the full table) with one function per metric, each independently
testable against a synthetic git fixture repo:

- `measure_py_tree(repo_root, prefix)` — `git ls-files "<prefix>*.py"` + line counts, used for
  both `src/` and `tests/` (git's pathspec `*` spans directory boundaries, confirmed empirically,
  so this correctly captures nested files, not just top-level ones).
- `count_top_level_src_packages` / `count_test_subdirectories` — both derived from
  `git ls-files`, not a raw filesystem `find`. This was a deliberate methodology choice: the real
  repo's filesystem has stale, git-untracked directories left over from history (e.g.
  `tests/ai/` contains only an empty `__pycache__/`, no tracked source) that a raw `find` would
  wrongly count as live test structure. `tests/ai/`-style dirs are exactly the trap a naive
  implementation would fall into.
- `count_commits` — `git log --oneline | wc -l` on current HEAD, exactly as plan.md step 1
  specifies (literal ancestry of whatever is checked out when the tool runs).
- `count_docs` — `docs/*.md` only, not repo-wide `*.md`. A repo-wide count is dominated by
  `stored_artifacts/`/`tickets/` process-doc corpora (6,230 files repo-wide vs. 806 under `docs/`
  alone) and is not what D24 §C's own ~776 figure was measuring.
- `find_dead_bytecode_files` — filesystem walk (not git, since `.pyc` files are gitignored) for
  any `.pyc` whose corresponding `.py` source doesn't exist, skipping `.git/.venv/node_modules/
  .pytest_cache/build/dist`. Generalizes D24 §A's `src_legacy/`/`tests_legacy/` finding (601 dead
  files, both dirs now deleted) to the whole tree.
- `find_unused_core_dependencies` — parses `pyproject.toml`'s `[project.dependencies]` via stdlib
  `tomllib`, maps each spec to its import name (hyphen→underscore, with one explicit override:
  `python-json-logger` → `pythonjsonlogger`), then greps every git-tracked `.py` file **repo-wide**
  (not scoped to `src/`) for `import <name>` / `from <name>` — this exactly mirrors D23's own
  stated methodology (`docs/audits/D23_architecture_resilience.md` line 87: "repo-wide grep — not
  scoped to `src/` — the whole tree"). Confirmed this choice mattered on the live repo:
  `python-json-logger`'s only real usage is `scripts/turbo_run.py`, outside `src/` — a `src/`-only
  scope would have produced a false positive.
- `compute_churn_lines_changed` — `git log --shortstat --pretty=format: -- . ':!agent-monitoring/
  *.jsonl' ':!tickets/working_log.csv' ':!docs/REGISTRY.yaml'`, summing insertions+deletions
  parsed from each shortstat line. This is the critical-requirement piece: the exclusion is a real
  git pathspec on the `--` boundary, so the excluded files' commit history is never walked into the
  computation — verified directly (see Test Summary) by proving 5,000 lines of synthetic noise
  confined to the 3 excluded files leaves the computed churn value completely unchanged, while the
  same noise *does* move an unfiltered `git log --shortstat` (proving the test isn't passing
  trivially).

**Deviation from the ticket's illustrative AC wording**: the AC's parenthetical "(e.g. dead-bytecode
count now 0, not 601)" was an example, not a strict target. The live run found 478 dead `.pyc`
files, not 0 — real, current filesystem cruft from files that moved on disk without their stale
`__pycache__/` being cleaned up (e.g. `src/systems/generator.py` moved to
`src/systems/world_systems/generator.py`, leaving `src/systems/__pycache__/generator.cpython-312.pyc`
behind) and stale root-level `tests/__pycache__/*.pyc` from before test files were relocated into
subdirectories. This is exactly the same *kind* of finding D24 §A described (stale bytecode with no
surviving source), just smaller-scale and from ordinary dev-environment drift rather than one
big deleted directory. It still satisfies the AC's actual requirement — a number that meaningfully
differs from the stale hardcoded 601 and is not an echoed cached value — and is documented as a
"Deviations" entry in `staging_artifacts/.../plan.md` per the CLAUDE.md workflow rule.

CI-wiring decision (plan.md step 3): confirmed on-demand-only — no `.github/workflows/*.yml` file
references `codebase-health-baseline` or `codebase_health_baseline.py`, matching the established
`status-drift-check`/`agent-monitoring-epic-staleness` precedent of Makefile-only tooling in this
family.

## Test Summary
Added `tests/tools/test_codebase_health_baseline.py` (13 tests, all passing):
- 2 churn-exclusion tests: one proves 5,000 lines of synthetic noise confined to the 3 excluded
  bookkeeping files does not move the computed churn value (and separately proves the same noise
  *would* move an unfiltered `git log --shortstat`, so the test isn't trivially passing); one
  proves real, non-excluded `src/` churn is still counted correctly.
- 4 source/test-split tests: flat and nested directory cases for `measure_py_tree`, plus
  `count_top_level_src_packages` (root-level files must not count as packages) and
  `count_test_subdirectories` (a git-untracked directory on disk must not count).
- 2 dead-bytecode tests: a `.pyc` with no source is detected; a `.pyc` with live source is not.
- 3 unused-dependency tests: one genuinely-unused dependency is detected; a dependency used only
  outside `src/` is correctly *not* flagged (proving the repo-wide-not-src-scoped methodology
  matters); the import-name override table is verified directly.
- 1 smoke test: `make codebase-health-baseline` runs against the real repo (`returncode == 0`),
  every table row label is present in stdout, and every numeric field in `build_report()` is a
  plausible non-zero value (not a golden-value pin).
- 1 live-sanity test: `build_report()`'s live numbers for dead-bytecode count, commit count, and
  unused-dependency set are asserted to differ from D24 §C's stale, hardcoded values (601, 595,
  `{pika, confluent-kafka}`).

Ran `.venv/bin/python3 -m pytest tests/tools/test_codebase_health_baseline.py -v`: 13 passed.
Ran the broader `.venv/bin/python3 -m pytest tests/tools/ -q -m "not slow"` regression check: 2389
passed, 12 skipped, 30 deselected, 1 xfailed — no regressions in the surrounding `tools/` test
corpus.

Live run output (fresh, from this session, against this repo — see full table in the implementer's
final report):
```
Source LoC / files                                 114,526 / 695
Test LoC / files                                   199,230 / 1,326
Test:source ratio (LoC)                            1.74 : 1
Top-level src/ packages                            35
Test subdirectories                                133
Commits (full history)                             99
Docs (.md, under docs/)                            808
docs/REGISTRY.yaml size                            1,054,036 bytes / 33,035 lines
Dead bytecode files (.pyc w/ no source)            478
Declared-but-unused core dependencies              xxhash, sse_starlette
Churn (lines changed, excl. bookkeeping)           5,781,231
```

## Files Changed
- `tools/codebase_health_baseline.py` (new)
- `tests/tools/test_codebase_health_baseline.py` (new)
- `Makefile` (added `codebase-health-baseline` target, on-demand only)
- `staging_artifacts/TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET/plan.md` (Deviations
  section appended, documenting the dead-bytecode-count-478-not-0 deviation from the AC's
  illustrative example) — investigation.md and test_plan.md were not modified; they were already
  committed clean at the start of this implementation turn (part of this ticket's own earlier
  Investigate/Plan phases, commit `bc3915c0`)
- `docs/plans/codebase_health_observatory_tooling_epic.md` (Document-Update phase: struck through
  Epic K's baseline-target scope item and marked it Resolved, citing this ticket ID, what was
  built, and the churn-exclusion/on-demand-only design decisions)

## Completion Summary
Implemented a permanent, on-demand `make codebase-health-baseline` target backed by
`tools/codebase_health_baseline.py`, which computes and prints a live LoC/churn/dependency
baseline table reproducing the shape of D24 §C's table, with all values freshly recomputed from
`git ls-files`/`git log`/the live filesystem on every run (never a cached or hardcoded snapshot).
The one non-negotiable requirement — excluding `agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
and `docs/REGISTRY.yaml` from the churn measurement via a real git pathspec exclusion, not a
post-hoc filter — is implemented in `compute_churn_lines_changed` and directly verified by a test
proving synthetic noise confined to those 3 files does not move the computed value. 13 new tests
all pass; the broader `tests/tools/` suite (2389 tests) shows no regressions. Not wired into any
CI workflow, per the plan's explicit on-demand-only decision.
