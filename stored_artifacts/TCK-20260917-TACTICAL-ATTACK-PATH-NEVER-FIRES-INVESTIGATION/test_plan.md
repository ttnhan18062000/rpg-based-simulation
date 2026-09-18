---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION
artifact_type: test_plan
tags: [strategy, combat, investigation]
---

# Test Plan — TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION

## What is under test
This is an investigation-only ticket — no `src/` code changes. What's being validated is the
instrumentation probe's own correctness, not simulation behavior per se: a probe that silently
fails to intercept the real call site would produce a false "never happens" conclusion, the exact
failure mode this ticket's own Acceptance Criteria #3/#4 guard against.

## Normal flow
- The probe script wraps `TacticalDecisionSystem.evaluate_entity_intent`,
  `FactionSemanticsService.is_hostile_compat` (singleton instance), and
  `CombatActions.execute_attack`, runs a real `Kernel.tick_once()` loop with
  `LocalSequentialExecutor` forced, and restores the original functions in a `finally` block so a
  probe run never leaves the module state patched afterward.

## Edge cases
- An entity with no active project/objective (`NO_PROJECT` in the objective-kind sample) — counted
  explicitly, not silently dropped from the distribution.
- An `evaluate_entity_intent` call that raises inside the wrapped body — the `try/except` around
  payload inspection means a malformed or unexpected `EntityUpdate.task` shape doesn't crash the
  whole run; it just fails to classify that one call's action, which would show as neither ATTACK
  nor SKILL rather than crashing.

## Failure modes
- **Concurrency corrupting the shared counters.** Already found once in this exact codebase
  (`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own addendum) — guarded against by
  forcing `LocalSequentialExecutor` explicitly rather than trusting the profile default.
- **A monkey-patch that doesn't actually take effect** (e.g., patching a name a caller already
  bound to a local variable before the patch ran) — checked directly: `cognition.py`'s own call
  site does `from src.engine.tactical import TacticalDecisionSystem` *inside* `execute_brain`,
  re-resolving the class reference on every call, so a class-attribute patch applied before the
  Kernel starts ticking is visible to every subsequent call. Same reasoning applies to
  `get_faction_semantics_service()`'s module-level singleton cache and `CombatActions`' own
  staticmethod lookup in `action_router.py`.

## Regression-prone paths
Not applicable — no code is changed by this ticket.

## Existing tests to run
None — this ticket adds no test to the suite; it produces a real-world measurement, recorded in
`investigation.md` and the registry's own `verified` block for `tactical_decision`.
