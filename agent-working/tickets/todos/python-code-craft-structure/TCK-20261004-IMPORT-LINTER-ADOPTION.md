---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-ADOPTION
phase: blocked
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-IMPORT-LINTER-ADOPTION

## Title
Adopt import-linter: layer contract from the package registry, loophole contracts, and retire the 8 equivalent tests

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/plans/codebase_health/import_linter_evaluation.md` recommends ADD with a narrow replace. BLOCKED until the owner agrees, the testing planner agrees to retire the named tests, and the owner decides whether `__init__.py` files are added to `src/` (M7 / rpg) or the 20 `src.<pkg>` root entries are accepted.

## Scope
- Add `import-linter` (exact pin) to the `lint` group and `[tool.importlinter]` to `pyproject.toml`: root packages `src` plus the 20 namespace packages as `src.<pkg>`, `include_external_packages = true`
- A `layers` contract generated from `codebase/structure/package_registry.jsonl`, advisory first, its 99 to 113 current violations carried as `ignore_imports` (or as an advisory report), with its own two-week soak before blocking
- Contracts for the loopholes the evaluation found (plain `import`, `from pkg import module`) only where no equivalent test survives
- Retire the 8 class E tests in the same change, with the testing planner's agreement: core not domains, phase19 hot path (a no-op), belief/fame/fidelity, admission control, campaign state; `visual_assets` if the root package is added
- Keep the contracts in sync with the registry (a validator or a test that every `src.<pkg>` namespace root is listed)

## Out of Scope
- Any file under src/ (including `__init__.py`)
- Editing `tests/architecture/` tests without the testing planner
- The 42 rules the evaluation says stay tests

## Acceptance Criteria
- [ ] Owner and testing planner agreement recorded
- [ ] Contracts run in an advisory CI step with a step summary and a warning annotation
- [ ] Each retired test replaced by a contract that fails on the same injected violation (shown)
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-IMPORT-LINTER-EVALUATION
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC

## Related Docs
- docs/plans/codebase_health/import_linter_evaluation.md
- docs/plans/codebase_health/src_package_structure_audit.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml, uv.lock
- tests/architecture/
- codebase/structure/

## Assumptions / Open Questions
- Testing's agreement and four conditions (#322 comment, 2026-10-04):
  1. a class E test is retired only in or after the PR that makes its replacement contract a required check;
  2. parity is shown per retired test (the injected violation, and the contract failing on it);
  3. phase19 `test_hot_path_does_not_import_heavy_analyzers` is an expectation change, not a retirement: the engine/observability owner first decides whether `kernel.py`'s function-local imports at 149/304/305/316/1241 are allowed (allowlist with a reason) or violations (an engine ticket);
  4. the blind spots and the stale allowlist are covered by contracts. The `or True` assert (`tests/unit/observability/test_decision_trace.py:376`) is testing's, not one of the eight.
- Stays BLOCKED on the owner's yes and on condition 3's decision (routed to rpg in the gates-flip PR's handoff)
- The `exclude_type_checking_imports` option is global, while the tests differ on `TYPE_CHECKING`: decide the single setting and accept the changed semantics for the rules that disagree
- `src/engine/intent` has no `__init__.py` inside a regular package and stays uncovered unless the file is added

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
