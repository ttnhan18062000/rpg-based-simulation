---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS
tags: [testing, ai, bug]
---

# Plan — TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS

## Sequencing
Wire the 16 directories into CI only after every real failure found within them is fixed (all 4
tickets referenced in investigation.md's "Real failures found" section landed first in this
session's batch) — never wire in known-red coverage.

## Placement
- `tests/unit/actions`, `tests/unit/ai` → `unit-gameplay` job (joins sibling `tests/unit/strategic`,
  `tests/unit/tactical`, etc. — thematically consistent).
- `tests/unit/tools` → `unit-infra` job (joins sibling `tests/unit/api`, `tests/unit/cli`).
- `tests/regression` → no explicit fast-lane placement. Its only test
  (`test_behavioral_5k_regression`) is `@pytest.mark.extra_slow`; the `slow` job's existing
  blanket `pytest tests/ -m "slow or extra_slow"` scan already covers it automatically once the
  directory exists — adding it to a `-m "not slow"` fast-lane job would just select 0 tests.
- The 12 `agent_codex_*`/`agent_orchestration*`/`agent_replay*` directories (83 files) → new
  dedicated job `agent-orchestration` ("Agent orchestration / codex / replay"), not folded into
  the already-large `api-tools` job, given the volume. Added to the `slow` job's `needs:` list
  alongside the other fast-lane jobs it already waits on.

## Filter correctness
The new `agent-orchestration` job uses `-m "not slow and not extra_slow"` (correctly excluding
both markers), unlike 7 of the 8 pre-existing fast-lane jobs which only exclude `slow` — a
separate, real inconsistency found and filed as its own follow-up
(`TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY`), not fixed here to keep this
ticket's diff to coverage-wiring only.

## Verification
Ran the exact real scope of every modified/new job locally before considering this done — not
just the 16 previously-orphaned paths in isolation, but each job's FULL real pytest invocation
(including all pre-existing directories in that job), to catch any interaction/collision.
