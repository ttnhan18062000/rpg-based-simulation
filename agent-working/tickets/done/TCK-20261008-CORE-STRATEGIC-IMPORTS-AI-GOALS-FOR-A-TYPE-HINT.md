---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT
phase: done
date: 2026-10-08
tags: [strategy, architecture]
---

# TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT

## Title
`src/core/strategic.py` imports `src.ai.goals.base.GoalScore` for a type hint, and `src/engine/tactical_rest.py` imports `src.ai.goals.need_pull`; both break the registry layer order (core and engine must not import ai).

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Owner-confirmed small hotfix for #416: the import-linter contract "Registry layer order" flips to blocking on 2026-10-19 and reported two violations. One is the `TYPE_CHECKING` import of `GoalScore` in `src/core/strategic.py` (added by #406). The other is mine: `src/engine/tactical_rest.py` imports `src.ai.goals.need_pull` (added by #414, SURV-07). No behaviour change, so hash-neutral.

## Scope
1. `with_live_current_score` stays in `src/core/strategic.py`. Its `live_scores` parameter is typed by a small `LiveScore` Protocol defined in core (read-only properties `kind` and `utility`); the `TYPE_CHECKING` import of `GoalScore` is dropped. `GoalScore` satisfies the protocol structurally.
2. `need_pull.py` is a pure curve used by both the AI scorers and the tactical pass, so it moves from `src/ai/goals/` to `src/engine/` (ai may import engine, not the reverse). Imports, the test file (`tests/unit/engine/test_need_pull.py`) and the doc and ledger path references move with it.

## Out of Scope
- Any behaviour or constant; the other ignored imports of the advisory contract.

## Acceptance Criteria
- [x] `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml` reports **17 kept, 0 broken** (it was 16 kept, 1 broken: core to ai and engine to ai).
- [x] `tests/unit/strategic/test_project_switch_uses_live_current_score.py` passes (6), and the need and rest tests pass (`tests/unit/engine/test_need_pull.py`, `tests/unit/ai/test_need_scorers.py`, `tests/unit/engine/test_rest_in_place.py`).
- [x] mypy gate (`codebase.gates.mypy_gate`) exits 0 and the code-health ratchet reports 0 new, 0 worse.

## Related Tickets
- `TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE` (#406), `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07` (#414).

## Related Docs
- `codebase/structure/importlinter.toml`; the SURV-07 references in `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml` (STRAT-280) and `docs/guidelines/intentional_divergences.md` (2.81) now name `src/engine/need_pull.py`.

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- `src/core/strategic.py`, `src/engine/need_pull.py`, `src/engine/tactical_rest.py`, `src/ai/goals/scorers.py`.

## Assumptions / Open Questions
- The closed SURV-07 ticket and its stored artifacts still name `src/ai/goals/need_pull.py`; they are history and are left as written.

## Implementation Notes
`LiveScore` is a `Protocol` with read-only `kind` and `utility` properties. `git mv src/ai/goals/need_pull.py src/engine/need_pull.py` and its test; `ruff --fix` for the import order the move changed in `tactical_rest.py`.

## Test Summary
import-linter 17 kept, 0 broken (was 16 kept, 1 broken); project-switch tests 6 passed; need and rest tests and the mechanism completeness pins pass (49 passed in the combined run); mypy gate exit 0; code-health ratchet 0 new, 0 worse.

## Files Changed
`src/core/strategic.py`, `src/engine/need_pull.py` (moved), `src/engine/tactical_rest.py`, `src/ai/goals/scorers.py`, `tests/unit/engine/test_need_pull.py` (moved), `tests/unit/ai/test_need_scorers.py`, `tests/unit/tools/test_mechanism_registry_completeness_check.py` (comment path), `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`, `docs/guidelines/intentional_divergences.md`, `docs/REGISTRY.yaml`.

## Completion Summary
Core no longer imports the AI layer for a type hint, and the engine no longer imports the AI layer for the pull curve. Contracts: 17 kept, 0 broken. No behaviour change.
