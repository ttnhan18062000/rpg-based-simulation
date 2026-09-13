---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX
phase: inprogress
date: 2026-09-13
tags: [data-quality, process-improvement]
---

# Test Plan: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX

## New tests

**Acceptance Criterion #4 needs no new test.** `tests/tools/test_generate_registry.py::
TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry` already runs
`generate_registry(..., check=True)` against the real, live `docs/REGISTRY.yaml` and is already
collected by the "API / tools / logging" CI job (`.github/workflows/test.yml:266`). Shipped by
`TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`, re-confirmed live by `TCK-20260826-REGISTRY-PARITY-
CONFLICT-GUARDS`. Found via `search_docs` during this ticket's own investigation (see
investigation.md's process note) — an earlier grep-only pass had missed it and this test plan
originally (incorrectly) proposed adding a duplicate `tests/integrity/
test_registry_yaml_matches_fresh_regeneration.py`. That duplicate is dropped.

- `tests/integrity/test_registry_merge_driver.py` (new — lives in `tests/integrity/` alongside
  `test_merge_union_gitattributes.py`, its exact pattern precedent, not `tests/tools/`)
  - `test_setup_merge_drivers_configures_git_attributes_target`: `.gitattributes` declares
    `merge=registry-regen` for `docs/REGISTRY.yaml` (a static assertion on the committed file, not
    a live git-config check — Makefile targets that mutate local git config are exercised in the
    scratch-repo-style test below, not asserted via unit test).
  - A scratch-repo-style integration test following the exact established pattern in
    `tests/integrity/test_merge_union_gitattributes.py` (`_run_git` helper, real subprocess
    `git init`/`commit`/`branch`/`merge` against a throwaway repo in `tmp_path`, never the real
    repo) proving: (a) with the driver installed via the same commands `setup-merge-drivers` runs,
    two branches that each add an independent file and regenerate a registry-like aggregate merge
    with zero conflict markers and a correct post-merge-hook-driven regeneration; (b) with no
    driver configured, the merge fails loudly (`fatal: custom merge driver ... lacks command
    line`); this test is the durable, repo-committed version of the manual scratch-repo proof done
    during investigation — same shape, same two assertions, so the ordering-bug regression this
    ticket's own investigation found can never silently return.

## Existing tests to check for impact

- `tests/architecture`, `tests/docs`, `tests/integrity`, `tests/static`, `tests/refactor` — the
  `arch-docs` CI job (`.github/workflows/test.yml:397-414`) already runs all of these; the new
  `tests/integrity/test_registry_merge_driver.py` file lands inside that same pytest invocation
  with no workflow YAML change.
- Any existing test asserting the literal content of `.gitattributes` (grep before editing it) —
  must be updated if it enumerates every line/path.
- `tests/tools/test_wave1_agent_tools_frontmatter.py`-style Makefile `.PHONY`-target existence
  tests, if any exist for `Makefile` — check `tests/tools/` for a Makefile-target coverage test
  before assuming none exists.

## Manual verification

- Re-run the scratch-repo proof from investigation.md after implementation, using the *real*
  `Makefile` target (`make setup-merge-drivers`) rather than hand-typed git config, to confirm the
  shipped installer produces the exact same working config.
- `python3 tools/generate_registry.py --check` on the real repo tree post-implementation, to
  confirm the new test's own assumption (exit 0 on a clean tree) actually holds before relying on
  it as a regression gate.
