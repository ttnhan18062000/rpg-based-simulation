## Finalize Plan

### 1. [x] Finish the structured reason migration

This is the biggest remaining contract gap.

**Implementation**: 
* `ActionReason` is now the authoritative runtime reason model across all core logic.
* `ActionProposal` and `IntentUpdate` strictly require `ActionReason` or provide valid coercion from legacy types.
* Move/combat/tactical rejection paths in `ActionSystem` and `MovementModel` now emit typed reason codes and payloads.

### 2. [x] Fix watchdog semantics so code matches the plan

**Implementation**:
* `ArenaWatchdog` now explicitly raises `WatchdogTimeoutError` (via `interrupt_main`), which is caught by `ArenaRunner`.
* It is surfaced as `ArenaStopCondition.WATCHDOG_TIMEOUT` in results, separate from generic stalls.

### 3. [x] Close Milestone 5 for real

**Implementation**:
* `apply_soft_cap` is implemented in `src/core/gameplay/attributes.py` and applied to all derived combat/progression stats.
* Comprehensive tests for soft-cap behavior, role hysteresis, and stat ceilings added in `tests/unit/test_milestone_5_specialization.py`.
* Verified that speed correlates to action tempo under the new balanced model.

### 4. [x] Remove stale fallback behavior after the above lands

**Implementation**:
* Removed major legacy fallback branches in `MovementModel` and `TacticalEvaluator`.
* Narrowed shims in `src/ai/states/base.py`; `ActionReason` now handles legacy string coercion as a safe degradation path with proper logging.

## What you do **not** need to reopen

You do **not** need another big pass on:

* Milestone 1 rulebook core
* Milestone 2 combat-context basics
* Milestone 3 movement model
* Milestone 4 tactical depth
* Milestone 6 arena foundation

Those look materially real now.

## Priority order

1. Structured reason authority
2. Watchdog semantics cleanup
3. Milestone 5 soft-cap / role-ceiling completion
4. Remove legacy fallback and tighten docs
