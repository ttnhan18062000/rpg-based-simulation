---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260821-HOTFIX-LAYER-REGISTRY-FRONTEND-BASELINE-DRIFT
phase: done
date: 2026-08-21
tags: [testing, registry]
---

# TCK-20260821-HOTFIX-LAYER-REGISTRY-FRONTEND-BASELINE-DRIFT

## Title
Sync hardcoded layer-value test baselines with the `frontend` layer registry addition

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
A concurrent session's commit (`2de94ab4`, `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) added a new
`frontend` entry to `registries/layer_registry.jsonl` (2026-08-21) but did not update the two
hardcoded-set anti-drift tests that assert the registry's exact contents:
`tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_layer` and
`tests/tools/test_layer_registry.py::test_layer_values_matches_real_seeded_registry`. Both still
assert the old 19-value set, so both now fail against the real, correctly-registered 20-value
registry. Discovered while triaging a CI failure on PR #32
(`kernel-concurrency-design-review`, "API / tools / logging" job) — confirmed via
`git diff main...HEAD -- registries/layer_registry.jsonl` that the `frontend` entry is real,
intentional, and already part of that branch's history, and via `git log --oneline main..HEAD --
registries/layer_registry.jsonl` that it landed via an unrelated ticket, not the branch's own
kernel-concurrency-design-review work. This matches the sanctioned baseline-drift pattern already
used for `tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count` — a small hotfix
updating the baseline with fresh evidence, not a silent edit outside a ticket.

## Scope
- Update `tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_layer`'s
  hardcoded `expected` set to include `"frontend"` (20 values total).
- Update `tests/tools/test_layer_registry.py::test_layer_values_matches_real_seeded_registry`'s
  hardcoded `expected` set to include `"frontend"` (20 values total).

## Out of Scope
- Any change to `registries/layer_registry.jsonl` itself — the `frontend` entry is correct,
  intentional, already-registered content from a different ticket; not touched here.
- Any other test failure observed in the same CI job run (`tests/api/test_live_*`,
  `tests/cli/*`, `tests/observability/*`, etc.) — these are documented environment-dependent soft
  monitors per `docs/testing/regression_policy.md` §3 (require a running server), reproduced
  locally as connection-refused errors with no live server, not caused by or related to this
  registry drift. Not fixed here.
- `TCK-20260817-STATE-DESIGN-PRIORITY-ORDER`'s own scope (already closed) — that ticket
  identified this same failure as pre-existing and correctly left it out of scope.

## Acceptance Criteria
- [x] `pytest tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_layer` passes
- [x] `pytest tests/tools/test_layer_registry.py::test_layer_values_matches_real_seeded_registry` passes
- [x] No change to `registries/layer_registry.jsonl`
- [x] Full `tests/tools/` suite still passes (no other test broken by this 2-line change)

## Related Tickets
- TCK-20260817-STATE-DESIGN-PRIORITY-ORDER (surfaced this as a confirmed pre-existing, out-of-scope failure)
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (origin of the `frontend` layer registry addition)

## Related Docs
- registries/layer_registry.jsonl

## Related Stored Artifacts
None (hotfix -- no staging artifacts).

## Related Code Areas
- tests/tools/test_validate_frontmatter.py
- tests/tools/test_layer_registry.py
- registries/layer_registry.jsonl

## Assumptions / Open Questions
None.

## Implementation Notes
Added `"frontend"` to both hardcoded `expected` sets, in-place, no other change:
- `tests/tools/test_validate_frontmatter.py:672-678` (`TestEnumAntiDrift.test_enum_values_layer`)
- `tests/tools/test_layer_registry.py:187-192` (`test_layer_values_matches_real_seeded_registry`)

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_layer_registry.py -v`
— both previously-failing tests now pass; no other test in either file regressed.

## Files Changed
- `tests/tools/test_validate_frontmatter.py` — added `"frontend"` to `test_enum_values_layer`'s expected set
- `tests/tools/test_layer_registry.py` — added `"frontend"` to `test_layer_values_matches_real_seeded_registry`'s expected set

## Completion Summary
Synced two hardcoded layer-value anti-drift test baselines with a real, intentional
`registries/layer_registry.jsonl` addition (`frontend`, landed by an unrelated concurrent
session's ticket already baked into this branch's history) that they had not been updated to
match. No registry content changed — this is a pure test-baseline sync, unblocking a real CI
failure on PR #32 that was unrelated to that PR's own diff.
