# Plan — TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Ordered per peer direction: storage first, flag flip last. Each step is independently testable
before moving to the next.

## Step 1 — Storage
- `src/domains/combat_engagement/schema.py`: add `salience: float = 0.0` to `OpponentModel`.
- `src/core/cognition.py`: retype `CombatMemory.opponent_stats` from `Mapping[str, Any]` to
  `Mapping[str, OpponentModel]`; import `OpponentModel`.
- New helper module `src/domains/combat_engagement/memory_store.py`:
  - `MAX_OPPONENT_MODELS_PER_ENTITY` bound constant (small — a handful, per §13.6's own "an entity
    remembers a handful of things it has met recently or been hurt by").
  - `compute_salience(prior: Optional[OpponentModel], updated: OpponentModel, outcome_severity:
    float) -> float`: surprise magnitude (`abs(updated.estimated_power - (prior.estimated_power if
    prior else updated.estimated_power))`, normalized) + outcome severity, matching §13.6's "already
    computed at the moment an estimate updates, so this is a stored score, not a new calculation."
  - `store_opponent_model(combat_memory: CombatMemory, model: OpponentModel) -> CombatMemory`:
    upsert `model` by `subject_key`; if at bound and inserting a new key, evict the entry with the
    LOWEST `salience` (not oldest) before inserting.
- Unit tests: bound enforcement, lowest-salience eviction (not oldest — a deliberately-aged
  high-salience entry must survive a newer low-salience insert), upsert-by-key (updating an existing
  subject_key never grows the collection).

## Step 2 — Wire storage into the real call site
- `src/domains/combat_engagement/phase.py`'s `CombatEngagementPhase.apply()`: before calling
  `CombatEngagementDecisionService.evaluate()`, build `subject_key = f"entity.{target.id}"`, read
  `actor.cognition.memory.combat.opponent_stats.get(subject_key)`, pass as `memory=`.
- After `evaluate()`, build the updated `OpponentModel` from `result.opponent_estimate` (passive
  observation always updates memory — §13.1's "reachable by construction" point), compute its
  salience, store it via `store_opponent_model()`, and set `cognition_bundle_set` on the SAME
  per-actor `EntityUpdate` already being constructed this tick (merge, not overwrite — read the
  existing `entity_updates.get(actor.id)` first, matching `MemoryUpdatePhase.apply()`'s pattern).
- Test: a real two-tick sequence (actor observes same target twice) proves `memory_used` in the
  second tick's `PerceivedOpponentEstimate` is non-empty (i.e., persisted, not `None` again).

## Step 3 — True power / apparent power / gap-driven uncertainty
- New helper module `src/domains/combat_engagement/power.py`:
  - `true_power(entity: EntityState) -> float`: `entity.combat.atk + entity.combat.def_stat * 0.5 +
    entity.combat.max_hp * 0.1`, exactly as specified (D-11), no re-derivation.
  - `apparent_power(entity: EntityState) -> float`: `true_power(entity)` adjusted by the existing
    `hp_ratio` condition curve already coded inline in `perception.py` (extract, don't duplicate).
  - `deterministic_observation_noise(seed: int, tick: int, observer_id: int, observed_id: int) ->
    float`: `hashlib.sha256(f"{seed}:{tick}:{observer_id}:{observed_id}".encode()).digest()` mapped
    into a bounded noise range — no RNG object, per §13.9.
  - `gap_uncertainty(gap: float, perception: float) -> float`: high uncertainty at `gap≈0`, low at
    large `gap`, PER-modulated (higher `PER` sharpens faster) — the actual curve shape is an
    implementation detail within the law's stated behavior (§13.3's two named endpoints: confident
    at extremes, uncertain at parity), not a re-litigated design question.
- `perception.py`: replace the level-based `base_power` and the flat perception threshold with calls
  into `power.py`; remove the dead `intel` variable (either use it — no, §13.4 says INT is a
  consideration-weighting future seam, not an estimation-accuracy input today — or delete the
  now-provably-dead read entirely, per the ticket's own fix directive).
- Tests: `gap=0` → uncertainty at its max; `gap` large → uncertainty at its floor; same
  `(seed, tick, observer_id, observed_id)` → bit-identical noise across repeated calls (determinism
  proof); a real corpus-world instrumented run (same measurement style as the 214-entity sample)
  confirming `true_power` now discriminates where the old level-only term did not.

## Step 4 — Witnessed-combat third tier
- New function in `power.py` or a small new `witnessed.py`: given a combat-resolution event's
  participant ids/positions/tick and `state`, find witnesses via the same perception-radius scan
  `CombatEngagementPhase.apply()` already performs (radius 10.0), and produce an `OpponentModel`
  update for each real witness about BOTH participants (a witness who saw the winner win learns the
  winner is at least as strong as demonstrated).
- Wire into wherever combat-resolution events are actually available to a phase with `state` access
  — investigate `AuthoritativeApplyPipeline.refine()`'s own phase ordering to find the correct
  insertion point (after combat resolution, same tick or next, matching this repo's existing
  one-tick-lag conventions elsewhere e.g. `MemoryUpdatePhase`'s own `WorldEventCategory.COMBAT_LOSS`
  read).
- Test: entity C, positioned within radius of A-vs-B's real fight, gains a real `OpponentModel`
  entry for both A and B it never directly interacted with.

## Step 5 — Wire `CombatLearning.learn()` into real combat resolution
- Map `CombatUpdate.outcome_kind` → `CombatLearning`'s vocabulary: `KILL`/`DEFEAT` (attacker's
  perspective on defender) → `"WON_EASY"` if the fight was low-cost, `"NEAR_DEATH"` if the attacker's
  own HP dropped low during it; defender's own `SURVIVE`-but-took-heavy-damage → `"LOST"` (matching
  `CombatLearning.learn()`'s own "LOST" semantics: "Target is stronger than expected").
- Call `CombatLearning.learn()` for BOTH participants at the real resolution call site(s) in
  `src/engine/combat.py`, threading the result through `EntityUpdate.cognition_bundle_set` the same
  way as Step 2 — this is the highest-risk step (touches the core, heavily-tested combat resolver),
  so land it with its own focused test pass before moving on.
- Tests: a real `resolve_attack()` KILL updates the attacker's `OpponentModel` for the (now-dead)
  defender; a real near-death survival updates the survivor's model for the attacker as `NEAR_DEATH`.

## Step 6 — Flag flip and full regression
- Flip `ENABLE_COMBAT_ENGAGEMENT` to `FeatureMode.ON` in `src/domains/optimization/feature_flags.py`.
- Run the full `tests/integration/` suite (every subdirectory, not a narrowed selection) — expect and
  triage real findings per §13.10's own prediction, same discipline as the raid-mob hijack hotfix.
- Update `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-273` from `missing` to `verified`
  with real `v2_evidence`/`test_path`.
- Update `docs/mechanics/04_strategic_cognition.md` §13's own "Status: declared, not yet
  implemented" line once everything above is real and tested.

## Design-decision checkpoints (bring to peer, don't decide alone)
- The exact shape of `gap_uncertainty()`'s curve beyond its two named endpoints, if a real corpus
  measurement suggests the natural first-pass curve produces an unreasonable distribution (matches
  the D-11 precedent — evidence before tuning).
- Any real bug found once `ENABLE_COMBAT_ENGAGEMENT` reaches `ON` that turns out to be a design
  question rather than a defect (§13.10's own explicit expectation).
