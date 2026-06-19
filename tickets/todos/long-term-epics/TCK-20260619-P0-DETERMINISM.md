---
status: open
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-DETERMINISM
phase: open
date: 2026-06-19
tags: [determinism, rng, bare-random, phase-0, p0-foundation, p0]
---

# TCK-20260619-P0-DETERMINISM

## Title
P0-2 · Determinism Enforcement — Replace bare random calls and add CI lint gate

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
Four files in `src/` contain bare `random.` calls that violate the P0 engine contract (`DeterministicRNG` is the only allowed RNG source). Replay diverges without error — two runs with the same seed produce different outcomes. A CI lint rule must prevent recurrence.

Source: `docs/audits/D10_determinism.md` F3; confirmed via grep.

## Scope
- Replace all bare `random.` usage in:
  - `src/worldbuilding/recipe.py`
  - `src/worldbuilding/compiler.py`
  - `src/engine/kernel.py`
  - `src/worldgeneration/generator.py`
- Each replacement: derive a sub-seed from the calling context (entity_id, tick, operation name) via `DeterministicRNG` at `src/platform/rng.py:L10`
- Add a CI static analysis step (can be a `pytest` test or `make` target) that fails if `import random` or `random.` appears in `src/` outside `src/platform/rng.py`
- Update `tests/integration/kernel/test_phase2_determinism.py` (existing `_scan_for_bare_random()` test) to cover the new lint rule; remove the files once fixed

## Out of Scope
- Changing RNG seeding strategy beyond what's needed to replace bare calls
- Performance changes to RNG usage
- Audit of `tests/` directory for bare random (test files may use random freely)

## Acceptance Criteria
- `grep -r "import random\|random\." src/ --include="*.py"` returns zero results outside `src/platform/rng.py`
- Two 1000-tick runs with identical seeds produce identical event logs (verified by `tests/integration/kernel/test_phase2_determinism.py`)
- CI lint step fails the build if a new bare `random.` call is added to `src/`

## Related Tickets
- TCK-20260501-E4-PHASE-ONE (prior RNG hardening — partial, 4 files still outstanding)

## Related Docs
- `docs/engine/contracts/deterministic_execution.md`
- `docs/plans/long_term_development_roadmap.md` § P0-2
- `docs/parity_ledger/substrate.yaml` (determinism — update any `missing`/`divergent` entries for bare-random rule to `verified`)
- `docs/guidelines/design_patterns.md` (add convention entry: no bare `random.` calls in `src/` outside `src/platform/rng.py`)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS/`

## Related Code Areas
- `src/platform/rng.py:L10` (DeterministicRNG)
- `src/worldbuilding/recipe.py`
- `src/worldbuilding/compiler.py`
- `src/engine/kernel.py`
- `src/worldgeneration/generator.py`
- `tests/integration/kernel/test_phase2_determinism.py`

## Assumptions / Open Questions
- Sub-seed derivation strategy: use `rng.sub_seed(context_str)` pattern consistent with how other callers derive sub-seeds — check existing usage in `src/` for the pattern before implementing

## Implementation Notes
Read `src/platform/rng.py` for the exact sub-seed API. Check how other domains call `DeterministicRNG` before picking the seeding pattern. The lint test in `test_phase2_determinism.py` already has `_scan_for_bare_random()` — extend its allowlist from `[rng.py]` to nothing (all uses should go), or keep just the rng.py allowlist and ensure all 4 files are clean.

After implementation: update `docs/parity_ledger/substrate.yaml` — find entries related to determinism/bare-random, set `status: verified`, add `v2_evidence` pointing to the fixed files and `test_path` to the determinism test. If no entry exists, add one. Run `make knowledge-index-update` after any docs/ changes.

## Test Summary
- Extend `tests/integration/kernel/test_phase2_determinism.py`: assert `_scan_for_bare_random()` returns empty list for all of `src/`
- Run existing `tests/integration/kernel/test_replay_determinism.py::test_transaction_trace_determinism` with two identical seeds — verify identical event logs
- Run existing `tests/integration/kernel/test_determinism_suite.py` — all must pass
- New CI lint step: add to Makefile or test suite so it blocks PRs on any new bare-random addition

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
