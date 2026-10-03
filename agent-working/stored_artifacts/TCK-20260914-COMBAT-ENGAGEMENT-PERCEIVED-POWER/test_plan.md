# Test Plan — TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

## Unit tests (new)
- `tests/unit/domains/combat_engagement/test_memory_store.py`: bound enforcement, lowest-salience
  eviction (not oldest), upsert-by-key never grows the collection, salience computation from
  surprise magnitude + outcome severity.
- `tests/unit/domains/combat_engagement/test_power.py`: `true_power()` matches the D-11 formula
  exactly on hand-built entities; `apparent_power()` reduces correctly at each `hp_ratio` band;
  `deterministic_observation_noise()` is bit-identical across repeated calls with the same
  `(seed, tick, observer_id, observed_id)` and differs across any one changed input; `gap_uncertainty()`
  is maximal at `gap=0` and minimal at a large `gap`, and a higher `PER` sharpens faster at a fixed
  gap.
- `tests/unit/domains/combat_engagement/test_perception.py` (extend existing if present, else new):
  the dead `intel` variable is gone (a static/AST check, mirroring this arc's own dead-variable
  disposition tickets); memory blending still occurs correctly once a real `OpponentModel` is
  supplied; the full estimate pipeline uses `true_power`/`apparent_power`/gap-driven uncertainty
  end to end.
- `tests/unit/domains/combat_engagement/test_phase.py` (extend): a real two-tick sequence proves
  `memory_used` is non-empty on the second observation of the same target (storage persists).
- `tests/unit/domains/combat_engagement/test_learning.py` (extend): `CombatLearning.learn()` called
  from the real wiring point updates the correct participant's model with the correct outcome
  vocabulary mapping.
- `tests/unit/engine/test_combat.py` (extend existing `CombatResolutionSystem` tests): a real
  `resolve_attack()` KILL/DEFEAT/SURVIVE outcome produces the expected `OpponentModel` update for
  both participants via the new wiring, without changing any existing damage/reward/social assertion.

## Real corpus-world measurement (not fixture-only, per this arc's own standing bar)
- Re-run the same instrumented-measurement style used for the 214-entity `true_power` sample and the
  500-tick `frontier_living_world` region-danger-seen measurement: with `ENABLE_COMBAT_ENGAGEMENT=ON`
  in a scratch run (before the real flag flip, to validate the mechanism first), confirm:
  - `OpponentModel` entries are actually created and persist across ticks for a real entity pair.
  - The three-phase acceptance scenario from §13.6 (engage → withdraw → engage-again-once-stronger)
    is observable in at least one real or constructed-but-real-code-path scenario — same entity,
    same monster, gap narrows as the observer grows stronger, without the model's own eviction
    losing the relevant memory (proves salience eviction, not just its unit-level logic).
  - `true_power`'s own real discrimination (already proven correct in D-11) actually reaches a
    real, non-zero `gap` for a real observer/observed pair in a real corpus world.

## Integration (full suite, per peer's explicit reminder — paths named here, updated once run)
Full `tests/integration/` — every subdirectory, run and reported in the ticket's own Test Summary
once the flag flips to `ON`, not a narrowed selection. Any failure triaged per CI Failure Triage
discipline before being called a regression.

## Determinism proof (required, not optional — §13.9 is a hard law)
A dedicated test asserting two full `WorldCompiler.compile()` + N-tick runs from the same seed
produce bit-identical `OpponentModel` state across the whole `state.entities` population — the same
class of proof this repo already requires for its other authoritative-state determinism guarantees.
