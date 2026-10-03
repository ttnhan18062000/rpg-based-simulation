---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI

## Title
`Makefile`'s `$(PYTHON)` interpreter-discovery loop silently resolves to empty on any CI runner,
breaking every `$(PYTHON)`-using target

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the "Slow regression" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32034124182): `make
simq-corpus-diversity-slow-isolated` fails with `sh: 1: -m: not found` and `ERROR: expected >=32
tests from test_corpus_diversity.py -m slow, collected 0`.

Root cause: `Makefile:346`'s `PYTHON := $(shell for py in .venv/bin/python3
/home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done)`
uses `[ -x "$$py" ]`, which only tests whether a literal file at that exact path is executable —
it never performs a `PATH` lookup for a bare command name. `.venv/bin/python3` doesn't exist on a
fresh CI checkout (no venv created; packages installed globally), and
`/home/vboxuser/Work/venv/bin/python3` is a specific local dev machine's path (per this repo's own
two-dev-environment convention), so both fail. The bare `python3` fallback ALSO fails the same
`[ -x ]` check, since `[ -x "python3" ]` only succeeds if a file literally named `python3` exists
in the current working directory — it does not resolve `python3` via `PATH` the way invoking it as
a command would. The loop therefore silently produces an empty `PYTHON` on every CI runner, and
every `$(PYTHON)`-prefixed shell command becomes ` -m pytest ...` — `sh` tries to execute `-m` as
a program name and fails.

This was masked until now because `simq-corpus-diversity-slow-isolated` is only invoked by the
`slow` job, which is gated behind `needs:` on every fast-lane job — it had never actually run to
completion on CI before this session's earlier fixes (the "API / tools / logging" job) unblocked
the dependency chain for the first time.

## Scope
- `Makefile`: replace `[ -x "$$py" ]` with `command -v "$$py" >/dev/null 2>&1` in both occurrences
  of the discovery loop (`eval-search`'s inline `$(shell ...)` and the `PYTHON :=` assignment) —
  `command -v` correctly resolves both absolute/relative paths and bare command names via `PATH`.

## Out of Scope
- Any change to which targets use `$(PYTHON)` vs. bare `python3` — `lane-all-fast`,
  `gate-expansion`, `lane-legacy-regression` (the other `slow`/`migration-lanes` job steps) already
  use bare `python3` directly and were never affected by this bug.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] `command -v "$$py"` correctly resolves `.venv/bin/python3` when present (local dev,
      preserving existing behavior) and falls back to `PATH`-resolved `python3` when no venv
      exists (matching CI).
- [x] `make -n simq-corpus-diversity-slow-isolated` shows `$(PYTHON)` expanding to a real
      interpreter path, not empty.
- [x] The test-collection step that was failing (`collected 0`) now collects the real 32 tests.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work; found via a live real-CI
re-check after other fixes this session unblocked the `slow` job's dependency chain for the first
time.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `Makefile`

## Implementation Notes
Changed both occurrences of the broken `[ -x "$$py" ]` test to `command -v "$$py" >/dev/null
2>&1`, keeping the same 3-candidate priority order (`.venv/bin/python3`, the second dev machine's
absolute venv path, then bare `python3`). Verified locally: the fixed loop still resolves
`.venv/bin/python3` first when present, and a simulated CI-like environment (run from a directory
with neither candidate path present) correctly falls through to `PATH`-resolved `python3`.

## Test Summary
- Simulated the exact broken loop (`[ -x "python3" ]`) and the fixed loop (`command -v "python3"`)
  side by side: broken loop produces no match at all; fixed loop matches `python3`.
- `make -n simq-corpus-diversity-slow-isolated`: `$(PYTHON)` now expands to `.venv/bin/python3` in
  this dev environment (was empty before the fix, producing the exact `sh: 1: -m: not found` seen
  on real CI).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large
  --collect-only -q`: 32 tests collected (matches the target's own `>=32` threshold; was 0 on CI
  before the fix).

## Files Changed
- `Makefile`

## Completion Summary
Fixed a real, standalone Makefile bug that silently broke Python-interpreter discovery on every CI
runner (and any environment without one of the two hardcoded local dev venv paths) for 11
`$(PYTHON)`-using target lines. Only surfaced now because the `slow` CI job — the sole caller of
the one affected, CI-reachable target — had never run to completion before this session's earlier
fixes unblocked its `needs:` dependency chain.
