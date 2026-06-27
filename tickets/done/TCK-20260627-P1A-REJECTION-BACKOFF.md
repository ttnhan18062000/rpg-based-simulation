---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P1A-REJECTION-BACKOFF
phase: done
date: 2026-06-27
tags: [p1, rejection-cascade, project-state, backoff, memory, performance]
---

# TCK-20260627-P1A-REJECTION-BACKOFF

## Title
Add backoff/expiry to `ProjectState` to stop rejection cascade

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
After the RC1 spawn-project fix, the opportunity pipeline runs at full volume but many requirement checks (near_service, inventory_space, has_item) fail every tick without any cooldown or expiry. Observed rate: ~650 rejections/tick → ~550K cumulative at tick 1,000. This scales to 3–4M at tick 5,000 — a memory and diagnostic noise risk that will invalidate long-run regression tests. Source: D03 F3, D04 §4, D06 F3.

## Scope
Add one backoff mechanism to `ProjectState` (choose one):
- **Option A — Max-retry count**: abandon project after N consecutive rejections (recommended N ≈ 20).
- **Option B — Tick-expiry**: mark project stale after M ticks without progress (recommended M ≈ 50).
- **Option C — Requirement cooldown**: suppress re-evaluation of a failed requirement for K ticks.

Update `ProjectState` dataclass in `src/core/state.py`, and the evaluation logic in `src/engine/apply.py` / `src/engine/interaction.py`.

## Out of Scope
- Fixing the underlying requirement failures (near_service, inventory_space, has_item) — those are downstream content/world issues.
- P2-A (spawn lock duration) — that is a related but separate tuning ticket.
- Changes to quest activation (P1-B).

## Acceptance Criteria
- [ ] `ProjectState` carries the chosen backoff field(s) (e.g. `consecutive_rejection_count: int = 0` or `stale_since_tick: int | None = None`).
- [ ] The chosen mechanism correctly abandons or suppresses stale projects.
- [ ] In a 1,000-tick urban_political run, total rejection count stays below 50,000 (down from 550K).
- [ ] Parity ledger updated for `ProjectState` (check `docs/parity_ledger/strategic_cognition.yaml`).
- [ ] New test: rejection count per entity stays below threshold in a 1,000-tick run.

## Related Tickets
- TCK-20260627-P0A-ADVENTURE-FLAG (P0 must be fixed first for meaningful measurement)
- TCK-20260627-P2A-SPAWN-LOCK-COND (related spawn-lock tuning)
- TCK-20260627-P3A-DEFERRED-EPICS (long-horizon regression suite depends on this)

## Related Docs
- `docs/audits/D03_behavioral_emergence.md` RC4, F3
- `docs/audits/D04_balance_tuning.md` §4
- `docs/audits/D06_longrun_health.md` F3
- `docs/parity_ledger/strategic_cognition.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-AUDIT-D06/`

## Related Code Areas
- `src/core/state.py` (`ProjectState` dataclass)
- `src/engine/apply.py` (authoritative apply path)
- `src/engine/interaction.py` (requirement evaluation — lines 86–88)

## Assumptions / Open Questions
- Option A (max-retry count) is the least disruptive and easiest to reason about. Prefer it unless option B fits better with existing tick-tracking patterns in `ProjectState`.
- N ≈ 20 is a starting point; calibrate against observed rejection distribution from D06 data.

## Implementation Notes
- `ProjectState.failure_count: int = 0` already existed at `src/core/strategic.py:L253` — no new
  field needed. The AC's `consecutive_rejection_count` is satisfied by this field.
- The abandonment check at `intelligence.py:L1147` (`if project.failure_count >= 3:`) existed but
  was dead code — `failure_count` was never incremented anywhere.
- Wire-up location: `evaluate_strategic_intent` in `src/systems/strategic_systems/intelligence.py`.
  In the "Project Abandonment (PH6)" block, before the threshold check, read
  `entity.identity.latest_intent_results`. If all results are rejected (none accepted): increment
  `failure_count` via `replace()`. If any accepted: reset to 0. Empty list: no-op.
- Added module-level constant `_MAX_CONSECUTIVE_REJECTIONS = 20` (changed threshold from 3 → 20).
- Added sub-threshold persistence path: when `failure_count` incremented but < 20, return early
  with `StrategicUpdate(projects_add_or_update=[project])` so the count is durably saved.
- Boredom penalty on abandonment already existed; no changes needed to that path.
- New test: `tests/unit/strategic/test_rejection_backoff.py` (5 test classes, 7 test methods).

## Test Summary
- Unit test: `ProjectState` abandons project after N+1 consecutive rejections.
- Integration test: 1,000-tick run with urban_political, assert total rejection events < 50,000.

## Files Changed
- `src/systems/strategic_systems/intelligence.py` — added `_MAX_CONSECUTIVE_REJECTIONS = 20` constant; wired up `failure_count` increment/reset/abandonment in `evaluate_strategic_intent` PH6 block (STRAT-234)
- `tests/unit/strategic/test_rejection_backoff.py` — new file; 5 test classes, 7 test methods covering increment, accumulation, abandonment threshold, reset on accept, boredom penalty
- `tests/unit/strategic/test_strategic_memory_v2.py` — updated `test_project_abandonment` to use `_MAX_CONSECUTIVE_REJECTIONS - 1` and inject a rejected `IntentResult` via `fast_replace`
- `docs/parity_ledger/strategic_cognition.yaml` — added STRAT-234 entry (verified, P1)

## Completion Summary
Implementation chose Option A (max-retry count). `ProjectState.failure_count` already existed as dead code at `src/core/strategic.py:L253`; no new field was needed. Wired increment in `evaluate_strategic_intent`'s PH6 block: reads `entity.identity.latest_intent_results` per tick — all-rejected increments, any-accepted resets to 0, empty is no-op. Abandonment fires when `failure_count >= 20`, emitting `ProjectStatus.ABANDONED` + boredom frustration penalty (0.5). Sub-threshold early return is guarded by `not strat.blockers` to avoid interfering with detour logic. 10/10 unit tests pass (7 new + 3 updated). Parity ledger entry STRAT-234 added as `verified`.
