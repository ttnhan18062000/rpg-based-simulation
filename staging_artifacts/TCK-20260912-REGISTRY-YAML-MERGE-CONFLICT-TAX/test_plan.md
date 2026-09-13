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

- `tests/integrity/test_registry_yaml_matches_fresh_regeneration.py`
  - `test_registry_yaml_in_sync_with_fresh_regeneration`: runs
    `python3 tools/generate_registry.py --check` as a subprocess, asserts exit code 0. This is the
    CI backstop (Acceptance Criterion #4) — fails whether the drift came from a bad manual merge
    resolution, a partial merge-driver install, or an unrelated stale commit.
- `tests/tools/test_generate_registry_hooks.py` (new, or added to an existing
  `tests/tools/test_generate_registry*.py` file if one exists — check before creating)
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
  `tests/integrity/test_registry_yaml_matches_fresh_regeneration.py` file lands inside that same
  pytest invocation with no workflow YAML change.
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
