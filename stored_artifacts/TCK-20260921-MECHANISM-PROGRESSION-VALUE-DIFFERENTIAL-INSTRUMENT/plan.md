# Plan — TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT

## Step 1 — Document the instrument
Add a new section to `docs/plans/mechanic_verification_scenarios_proposal.md` describing the
value-differential methodology: both arms run the real mechanism; only one input value differs;
hold the world otherwise fixed; observe whether a downstream outcome differs. State the
calibration requirement (positive control confirms detection, negative control confirms no false
positive) and both named traps with how this program addresses each (cite the investigation.md
trace).

## Step 2 — Calibration instrument: `readiness_speed_scaling` + `derived_stats`
New test file `tests/mechanic_scenarios/test_readiness_and_derived_stats_value_differential.py`:
- Compile any existing world, take one entity, mutate `attributes` directly (`dataclasses.replace`),
  run through the real `apply.py` `stats_dirty` recalculation path (a single real Kernel tick with
  a staged `attributes_dirty`-triggering update, or a direct call to
  `SkillScalingService.get_effective_stats()` if that is the real, unconditional call site — verify
  exact trigger condition before staging).
- Arm A (baseline): default attributes.
- Arm B (agility +10, others fixed): `readiness_speed` must differ from Arm A by the exact formula
  delta; `max_hp`/`atk`/`def_stat` must be UNCHANGED from Arm A (negative control for
  `derived_stats`).
- Arm C (vitality +10, strength +10, agility fixed): `max_hp`/`atk` must differ from Arm A by the
  exact formula deltas (positive control for `derived_stats`); `readiness_speed` must be UNCHANGED
  from Arm A (negative control for `readiness_speed_scaling`).

## Step 3 — `evolution`/`xp_leveling` value differential
New test file `tests/mechanic_scenarios/test_evolution_xp_reward_value_differential.py`, reusing
`data/worlds/mechanic_scenario_combat_judgement_withdrawal/`:
- Stage goblin (id=1) forced ATTACK against orc (id=2, `combat.hp` set to 1 to guarantee a one-hit
  kill), same staging shape as `test_combat_judgement_withdrawal.py`.
- Arm A (orc `evolution_level=1`): run one real Kernel tick, read goblin's
  `identity.evolution_points` after; expect `+10` (base level-1 XP reward, matching `evolution`'s
  own existing verified formula).
- Arm B (orc `evolution_level=5`, `evolution_points` held at whatever Arm A used): expect goblin's
  `evolution_points` gain to be `+50` — 5x Arm A, confirming the reward scales with the varied
  input (positive control).
- Arm C (orc `evolution_level=1` — same as Arm A — but `evolution_points` varied to a different
  value): expect goblin's XP gain to be identical to Arm A's `+10` (negative control — the varied
  field provably does not feed the reward).
- Each arm asserts the SAME number of combat rounds/kill-in-one-tick outcome to make the
  RNG-order-safety claim directly observable in the test, not just argued in the docstring (e.g.
  assert orc's `combat.alive is False` and goblin took the same/no counter-damage across arms where
  applicable).

## Step 4 — Registry updates
Add dated (`2026-09-21`) additive notes to `readiness_speed_scaling`, `derived_stats`, `evolution`
verified blocks in `registries/mechanisms.yaml`, citing the new test files. Do not touch
`xp_leveling`'s own note beyond what's already there (it already carries the Merge pointer).
Run `python3 -m tools.mechanism_registry.registry` (or however `main()` is invoked) to confirm the
duplicate-key invariant and all existing invariants still pass after the edit.

## Step 5 — Run tests, then report
Run the new test files plus the existing `tests/unit/progression/` suite (scoped, not full
`pytest tests/`) to confirm no regression. Then send the peer report (instrument design + control
results) via SendMessage before treating any verdict as ready to scale further.

## Step 6 — Finalize
Standard ticket close: move ticket to `tickets/done/`, staging artifacts to `stored_artifacts/`,
working log, agent-monitoring, `docs/REGISTRY.yaml` regen (unconditional per Finalize), commit,
push, open PR (or fold into an already-open PR if one exists for this branch), report.
