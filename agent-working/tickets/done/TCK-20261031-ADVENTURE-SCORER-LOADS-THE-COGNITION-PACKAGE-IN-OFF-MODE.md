---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261031-ADVENTURE-SCORER-LOADS-THE-COGNITION-PACKAGE-IN-OFF-MODE
phase: done
date: 2026-10-31
tags: []
---

# TCK-20261031-ADVENTURE-SCORER-LOADS-THE-COGNITION-PACKAGE-IN-OFF-MODE

## Title
The adventure scorer loads the cognition observability package in an OFF-mode process

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
#547 condition (rpg-planner): an OFF-mode kernel imports none of the four reporting/cognition modules. testing-planner's TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK found it false on main 6fdfdf555 (testing-implementer, fresh subprocess, SIM_OBS_MODE=OFF, sandbox_world s42, one tick_once + shutdown): `src.observability.cognition.recorder` and `decision_trace_writer` are loaded. Path: src/ai/goals/adventure_scorer.py:10 imports `get_active_writer` from `src.observability.cognition.decision_trace_writer` at module top; that runs `src/observability/cognition/__init__.py`, which eagerly imports `recorder` (line 11). It loads at world compile, before any Kernel. A lazy import at the call site does NOT fix it: the scorer calls `_get_active_writer()` on the first tick for every entity, so the package would load anyway.

## Scope
Plan (rpg-planner):
1. New dependency-free module `src/observability/active_decision_trace.py` holding the run-scoped slot: `_active_writer`, `set_active_writer(writer)`, `get_active_writer()`. It imports nothing from `src.observability.cognition` or `src.observability.queue` (type via `TYPE_CHECKING` only, or a small Protocol with `write_trace`).
2. `decision_trace_writer.py` drops its own `_active_writer` global and re-exports `set_active_writer` / `get_active_writer` from the new module, so `tests/unit/observability/test_decision_trace.py` and kernel.py:267-272 keep working unchanged.
3. `adventure_scorer.py:10` imports from the new module, keeping the alias `_get_active_writer` (the patch target at test_decision_trace.py:354).
4. No other change; `cognition/__init__.py` is left as is.

## Out of Scope
- Slimming `cognition/__init__.py`; other import edges; the phase19 contract/linter source list and the toml (testing-planner); kernel.py line-number drift (codebase).
- TCK-20261029-KERNEL-IMPORTS-SIMQ-WIRING-INSTEAD-OF-RECEIVING-IT-FROM-ITS-COMPOSITION-ROOT.

## Acceptance Criteria
1. Fresh subprocess, SIM_OBS_MODE=OFF, sandbox_world s42, one tick_once + shutdown: none of `src.observability.cognition.recorder`, `src.observability.cognition.decision_trace_writer`, the artifact repository and the metric recorder modules is in sys.modules (the testing harness's own OFF assertion passes; testing-implementer owns that test).
2. ON mode: the decision trace is still written (existing tests green: tests/unit/observability/test_decision_trace.py and the adventure scorer tests).
3. Behaviour neutral: gate-world digests unchanged (a short paired run, e.g. 3 worlds x s42 x 500t, base 6fdfdf555, byte-equal final hashes).
4. A unit test that the new module imports nothing from `src.observability.cognition` (fresh subprocess or import-graph check).

## Related Tickets
- TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK (testing-planner; held on this); #547.

## Related Docs
- docs/observability/decision_trace_contract.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/ai/goals/adventure_scorer.py:10,184; src/observability/cognition/decision_trace_writer.py:50-61; src/engine/kernel.py:252-272

## Assumptions / Open Questions
- `src/observability` is a namespace package (no __init__.py on main), so the new module drags nothing in.

## Implementation Notes
New src/observability/active_decision_trace.py holds the slot; decision_trace_writer re-exports set/get; adventure_scorer imports from the new module keeping the `_get_active_writer` alias.

## Test Summary
New tests/unit/observability/test_active_decision_trace_isolation.py (subprocess import check + re-export identity). tests/unit/observability + test_adventure_goal_scorer: 1250 passed. OFF-mode kernel probe (sandbox frontier_living_world s42, one tick_once + shutdown): no src.observability.cognition.*, artifact or metric module loaded. paired --neutral base 6fdfdf555 vs 7c03fe435: 3 worlds s42 1000t final hashes IDENTICAL.

## Files Changed
src/observability/active_decision_trace.py (new); src/observability/cognition/decision_trace_writer.py; src/ai/goals/adventure_scorer.py; tests/unit/observability/test_active_decision_trace_isolation.py (new).

## Completion Summary
OFF-mode runs no longer load the cognition package via the adventure scorer; behaviour neutral.
