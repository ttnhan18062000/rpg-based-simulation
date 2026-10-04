---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-DECISION-TRACE-VACUOUS-ASSERT
phase: done
date: 2026-10-04
tags: [testing]
---

# TCK-20261004-TEST-ARCH-MAINT3-DECISION-TRACE-VACUOUS-ASSERT

## Title
test_decision_trace.py: remove a vacuous assert and make the import guard AST-based

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary

`tests/unit/observability/test_decision_trace.py` had `assert "src.engine.domain.cognition" not in sys.modules or True`,
which can never fail. Remove it, and strengthen the remaining guard, which only matched the text
`from src.engine.domain.cognition`. Found by codebase-planner (PR #322 section 3.4), verified by
`test-architecture-reviewer` (maintenance 3, T4).

## Scope

In `test_decision_trace_writer_does_not_import_engine_cognition`: drop the vacuous assert (a `sys.modules` check
cannot work in a shared pytest process) and replace the substring checks with an AST walk of the writer module
(`src/observability/cognition/decision_trace_writer.py`) that fails on `import src.engine.domain.cognition[...]`,
`from src.engine.domain.cognition[...] import ...` and `from src.engine.domain import cognition`. The walk is a
module-level helper `_find_engine_cognition_imports(source)` so it can be tested against sources other than the
writer.

## Out of Scope

- Any change to the writer module, any other test, any `src/` change.
- Adjusting the guard to pass: the brief said to stop and report if it went red on `origin/main`.

## Acceptance Criteria

- [x] The vacuous line is gone.
- [x] The guard flags all three import forms (plus `import ... as`), and passes on the real writer.
- [x] Positive control shown: a scratch copy with one injected import fails; nothing of it is committed.

## Related Tickets

- Siblings: `TCK-20261004-TEST-ARCH-MAINT3-EPIC-B-COST-ROWS-AFTER-306`,
  `TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING`,
  `TCK-20261004-TEST-ARCH-MAINT3-API-SERVER-READINESS-POLL`

## Related Docs

None.

## Related Stored Artifacts

None.

## Related Code Areas

- `tests/unit/observability/test_decision_trace.py`; `src/observability/cognition/decision_trace_writer.py` (read only)

## Assumptions / Open Questions

- The old second check `"import CognitionDomain" not in source` is dropped: it matched a symbol name, and any
  import of that name from the cognition package is already caught by the module-path forms.
- Relative imports (`from ..engine.domain import cognition`) are not covered (the walk skips `level > 0`); the writer
  has none, and the repo's style is absolute `src.` imports.

## Implementation Notes

Two extra tests were added beside the guard: a parametrized detector test over five import forms (the detector's own
positive control, committed because it needs no scratch copy) and one that unrelated imports are not flagged. The
brief's scratch-copy control was also run: the real writer gives `[]`, and the same source with one injected
`import src.engine.domain.cognition`, `from src.engine.domain.cognition.x import y` or
`from src.engine.domain import cognition` is flagged at the injected line each time. The old substring check would
have missed the first and third.

## Test Summary

`pytest tests/unit/observability/test_decision_trace.py`: 34 passed. The guard passes on the real writer (no such
import exists on `origin/main`), so there was nothing to stop and report.

## Files Changed

- `tests/unit/observability/test_decision_trace.py`

## Completion Summary

Done 2026-10-04. The architecture guard now fails on any absolute import of `src.engine.domain.cognition` in
`decision_trace_writer.py` in the three forms named, instead of one substring, and the always-true assert is gone.
