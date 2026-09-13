# Plan — TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION

## Disposition: scoped fix, not accept-and-document

Per the standing user rule ("fix only if hard failure, not perf-tuning"): an entity that can
**never** re-enter candidacy by any action available to it is not degraded, it is frozen -- a
logic defect in the policy, not the performance pressure that triggers it. Confirmed via measurement
3 (fresh spawn injected while genuinely, independently confirmed DEGRADED) that this is a real,
reachable failure mode, not merely a sentinel-bug artifact.

## Fix shape, per `rpg-feature-planning`'s explicit correction of the first-proposed shape

Rejected: "grant freshly-spawned entities one guaranteed candidacy tick." This is a workaround
shaped like a fix -- it only covers the reproducible case (spawn-time), not the general one (any
entity that acquires a target through a path that never marks it dirty).

Rejected: full re-admission of any entity with an unreached target. Under real load, most entities
plausibly have an unreached target at any given moment -- granting them full candidacy would
re-admit nearly everything and defeat `EXACT_DIRTY`'s own work-shedding purpose, trading a
starvation bug for a performance regression on a system already exceeding its tick budget.

**Chosen: reduced-cadence candidacy**, keyed on the real, general condition (a real, unreached
navigation target, already established true earlier in `select()`'s own logic) rather than a
spawn-time special case. `MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO = 20`
(`src/engine/candidate_selector.py`): under `EXACT_DIRTY`, an otherwise-non-urgent entity with a
real target is admitted on `(state.tick + entity_id) % 20 == 0` instead of never -- guaranteeing
eventual movement (within a bounded window) while adding only a small, bounded fraction of extra
candidates per tick. The real readiness/move-cost gameplay gate still applies uniformly regardless
of scan policy (moved earlier in the function so it isn't bypassed by the new branch). Genuinely
urgent entities (the 5 existing urgency conditions) are entirely unaffected -- still selected every
tick, not only on the reduced cadence.

## Acceptance bar (per `rpg-feature-planning`, both required)

- Re-run the real 300-entity sustained-load scenario with a fresh mid-run spawn: injected raiders
  eventually move rather than being permanently stuck.
- `tick_compute_ms` stays bounded and DEGRADED still engages -- the fix must not neutralize the
  governor it operates inside.

## Also required

Fold the relationship between the movement-candidacy consequence and the already-known,
deliberately-deferred wall-clock-throttle determinism issue into that issue's own record. No
dedicated ticket or doc file was found for it on search (Context Scan run first, per standing
instruction) -- the closest existing traces are informal (project memory) and a structurally
related but distinct F6 finding in `docs/parity_ledger/infrastructure.yaml` (grade-anchor
load-sensitivity, not this specific mechanism). Given no single canonical doc exists to edit,
cross-reference comments were added directly at both real code sites that force `RuntimeMode.
DEGRADED` from wall-clock pressure (`governor.py`'s `tick_compute_ms` check,
`kernel.py`'s `_phase_resolution()` mid-tick `should_throttle` abort) so a future reader of either
sees the real consequence reaches movement candidacy, not only tick timing.
