# Investigation — TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION

## Re-measurement against the fixed worker-utilization sentinel

Full evidence trail (three real, uninstrumented measurements) recorded directly in the ticket's
own Implementation Notes on 2026-09-13, per this repo's existing precedent for this ticket (the
2026-09-11 partial recheck used the same location rather than a separate file). Summary:

1. The exact original raider precondition, re-run against the real production Kernel config
   (`scenario_runtime.py`'s `max_worker_count=0`) now that
   `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER` is fixed: 0/30 ticks enter
   DEGRADED, all raiders move. The specific finding that motivated this ticket no longer
   reproduces -- confirming `rpg-feature-planning`'s prediction.
2. A real 300-entity sustained-load run (no mocking): DEGRADED genuinely engages via
   `tick_compute_ms` exceeding budget (real watchdog alert, real per-phase costs). The mechanism
   is not dead.
3. A fresh raider wave injected mid-run, after DEGRADED was independently confirmed active: 5/5
   permanently stuck across 15 subsequent ticks (pre-fix). This isolates the mechanism from the
   sentinel bug entirely -- it is real, and confirmed under genuine load, not reasoning alone.

## Root cause, precisely

`MovementCandidateSelector.select()` (`src/engine/candidate_selector.py`), under
`ScanPolicy.EXACT_DIRTY`, unconditionally excluded every non-urgent movement candidate. Candidacy
requires one of 5 urgency conditions (`target_changed`, `is_dirty`, `tile_blocked`,
`interaction_req`, `strategic_req`) -- all five are **change-driven**. An entity that never
changes never qualifies, and it can only ever become "changed" by first being selected (moving, or
being marked dirty as a consequence of moving/receiving an update). A freshly-spawned entity with
a static `navigation.target` baked in at construction and no active goal/interaction/project
satisfies none of the five and has no path, by any action available to it, to ever escape
exclusion while `EXACT_DIRTY` holds. This is permanent starvation, not throttling -- confirmed via
measurement 3 above.

`rpg-feature-planning`'s correction to the initially-proposed fix shape (a spawn-time exemption)
was decisive: the real defect is not "freshly spawned," it is the general case of any entity with
a real, unreached navigation target and no other urgency signal. A spawn-time-only exemption would
not cover an entity that acquires a target through a path that doesn't mark it dirty.

## Real trigger, confirmed to reach actual gameplay consequence

`ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`)'s own
`signals.tick_compute_ms >= profile.max_tick_budget_ms` check is the real, confirmed driver of
`RuntimeMode.DEGRADED` under genuine sustained load (measurement 2/3 above). A second, structurally
separate path also forces `RuntimeMode.DEGRADED`: `Kernel._phase_resolution()`'s own mid-tick
`should_throttle` emergency abort (`src/engine/kernel.py`, `should_throttle = not self._audit_mode
and elapsed > hard_cap`), which calls `self._governor.force_mode(RuntimeMode.DEGRADED, ...)`
directly. This second path is the same, already-known, deliberately-deferred determinism-breaking
mechanism from an earlier informal finding (no dedicated ticket/doc found on search -- see
Completion Summary). Both paths are real, wall-clock-driven, and both now cross-reference this
ticket's own fix directly in-code (see Files Changed) so a future reader of either sees that their
consequences reach movement candidacy, not only tick timing.
