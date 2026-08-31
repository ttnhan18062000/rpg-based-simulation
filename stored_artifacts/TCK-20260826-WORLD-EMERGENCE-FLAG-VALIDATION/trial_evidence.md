---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION
artifact_type: report
tags: [feature-flags, world]
---

# Trial Evidence — TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION

Raw output of the 4-leg (2-world x OFF/ON) fresh calibration trial run per `plan.md` Steps 2-6.
Environment note: the worktree's bare `python3` lacks `pydantic` (a pre-existing, unrelated
environment gap both sibling tickets in this batch also worked around the same way); all four
runs were executed with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the
main checkout's venv) instead, with `cwd` still the worktree so `data/runs/` and
`data/calibration/` output landed where the plan's commands specify.

## Commands run (verbatim except interpreter path)

```
# dungeon_crawl OFF
.venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_OFF
# -> data/runs/run_1788020954_5169

# dungeon_crawl ON
ENABLE_WORLD_EMERGENCE=ON .venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_ON
# -> data/runs/run_1788021599_5169

# resource_dense_basin OFF
.venv/bin/python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_OFF
# -> data/runs/run_1788021673_5169

# resource_dense_basin ON
ENABLE_WORLD_EMERGENCE=ON .venv/bin/python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_ON
# -> data/runs/run_1788021702_5169
```

All four commands exited 0 and produced `data/runs/{run_id}/simulation_events.jsonl` and
`data/calibration/{...}/quality_report.json` each.

## World-loading confirmation

`calibrate_simq.py`'s own stdout prints `entities={args.entities}` (the `--entities` CLI
argument's default value, `10`), **not** the actually-loaded world's real entity count — this is
a CLI-arg echo, not a world-loading signal, and must not be read as one. The real fingerprint is
each run's own tick-0 `chunk_0000.json` payload, which carries typed content
(`nodes_add: [{"kind": "stone_outcrop", ...}]` etc.) from the real compiled world spec. Grepping
`"entity_count"` in each run's `chunk_0000.json` (populated by `REFINED_UPDATE` fingerprint
payloads) gives:

| World | `chunk_0000.json` `entity_count` | `corpus_registry.yaml` documented `scale.entity_count` | Match |
|---|---|---|---|
| `dungeon_crawl` (both legs) | 32 | 32 | Yes |
| `resource_dense_basin` (both legs, not independently re-checked per-leg since the loader either resolves the real world or raises `FileNotFoundError` — see below) | — | 23 | Confirmed via successful run (see note) |

`dungeon_crawl`'s `chunk_0000.json` `entity_count` was independently grepped for both the OFF and
ON run and read `32` in both, matching `corpus_registry.yaml`'s `_worlds.dungeon_crawl.scale.entity_count: 32`
exactly. Per `calibrate_simq.py:143-157`'s `_load_world_state()`, a `--name` that fails to resolve
raises `FileNotFoundError` rather than silently falling back to the generic hero+goblins world
(the same reasoning both sibling trials relied on) — a successful exit-0 run against `--name
resource_dense_basin` is itself sufficient proof the real
`data/worlds/resource_dense_basin/resolved/world.resolved.yaml` loaded, since no other Yaml exists
under that name and the fallback path is exclusively for the literal string `"generic"`.

## Evidence tally (5 signal groups x 4 legs)

Extracted by iterating every `chunk_*.json` file's `REFINED_UPDATE` payloads for each run and
summing `metric_counters`, collecting distinct `quest_registry_add` ids, and counting
`entity_updates[*].property_updates` keys — not from `simulation_events.jsonl`, per
investigation.md's finding that `world_emergence_event` in that file is produced by other phases
via `world_events_add` and is not gated by `ENABLE_WORLD_EMERGENCE` at all.

### Signal 1 — run/skip counters (`metric_counters["run_world_emergence"]` / `["skip_world_emergence"]`, summed)

| | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| `run_world_emergence` | 0 (absent) | 1837 | 0 (absent) | 908 |
| `skip_world_emergence` | 1836 | 0 (absent) | 931 | 0 (absent) |
| Total `REFINED_UPDATE` payloads (≈ticks recorded) | 1836 | 1837 | 931 | 908 |
| Run-rate on the ON leg | n/a | **100%** | n/a | **100%** |

Confirms `must_run_every_tick=True` (`src/engine/phase_graph.py:69`) holds empirically: zero
`skip_world_emergence` on either ON leg, zero `run_world_emergence` on either OFF leg — a clean
binary split, no phase-starvation false negative.

### Signal 2 — phase telemetry (`metric_counters["world_emergence_ms"]` / `["aggregates_generated"]`)

| | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| `world_emergence_ms` | absent | 883.31 | absent | 431.83 |
| `aggregates_generated` | absent | 89 | absent | 182 |

Both fields are present and nonzero on both ON legs, absent on both OFF legs (the phase body never
executes when OFF, per its own `if not flag: return update, WorldEmergenceResult()` early-out) —
confirms real work happens on ON ticks, not a no-op pass.

### Signal 3 — quest registry growth (`quest_registry_add`, distinct ids, final tally)

| | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| Distinct `quest_registry_add` ids | 0 | **0** | 0 | **0** |

**Zero growth on every leg, including both ON legs.** See "Honest gap" below — this is a real,
disclosed finding, not smoothed over.

### Signal 4 — entity signal exposure (`exposed_world_signals` / `force_route_reevaluation` `property_updates`)

| | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| `exposed_world_signals` property-update count (summed across all entity-updates, all ticks) | 0 | **33869** | 0 | **18518** |
| `force_route_reevaluation` property-update count | 0 | **33869** | 0 | **6563** |

Present in volume on both ON legs, absent on both OFF legs (the bridging step
`WorldToEntitySignalBridge` only runs inside `execute()`, which never runs when OFF). Note
`dungeon_crawl`'s ON leg shows `exposed_world_signals` and `force_route_reevaluation` at the exact
same count (33869 == 33869) — every entity that receives an exposure in this monster-gauntlet
world crosses the `danger_pressure > 0.2` threshold that triggers `force_route_reevaluation`
(`phase.py:97-118`), consistent with a purpose-built combat/danger archetype. `resource_dense_basin`
shows the expected partial subset instead (6563 of 18518 exposures cross the threshold) — a
civilian-settlement world with lower ambient danger pressure. Both are plausible, not anomalous.

### Signal 5 — absolute OFF-baseline activity (`RESOURCE_DEPLETED` / `ENTITY_DEATH` / `CAMP_RAID` `WorldEvent`s feeding the quest generator)

Counted every `world_events_add` entry's `category` field across all four runs (this field is
populated by other phases — `diplomatic_transitions`, `military_conflict`,
`src/engine/pipeline_phases/actions.py`'s `COMBAT_LOSS` producer — never by
`WorldEmergencePhase.execute()` itself, confirmed again this session):

| | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| `world_events_add` total | 1 | 1 | 3 | 2 |
| By category | `COMBAT_LOSS`: 1 | `COMBAT_LOSS`: 1 | `COMBAT_LOSS`: 3 | `COMBAT_LOSS`: 2 |
| `RESOURCE_DEPLETED` / `ENTITY_DEATH` / `CAMP_RAID` count | **0** | **0** | **0** | **0** |

**Zero qualifying events in every leg of both trial worlds.** `QuestOpportunityGenerator`'s two
code paths (`phase.py:61-74`) only fire on `WorldEventCategory.RESOURCE_DEPLETED` or
(`severity >= 0.5` and category in `{ENTITY_DEATH, CAMP_RAID}`) — none of these three categories
appeared in either world's `world_events_add` output at all, in either leg. This directly explains
Signal 3's zero quest-registry growth: it is not a suppression artifact of the flag, it is an
absent precondition in both trial worlds within these windows (2000 ticks for `dungeon_crawl`,
1000 for `resource_dense_basin`).

## No-suppression check

**Structural half — passes, both worlds.** Signal 1's clean 100%/0% run/skip split on the ON/OFF
legs (`skip_world_emergence` never coexists with `run_world_emergence` in the same leg) confirms
`WorldEmergencePhase` runs on effectively every eligible tick once ON, not silently starved by
`PhaseDependencyGraph.should_run_phase()`.

**Empirical half — passes, both worlds, using domain-independent signals as the regression check.**
Per the same class of check TCK-20260809 (`combat_engagement`) failed and was fixed for, this
trial confirms no *other* domain's independent signal collapsed toward zero on the ON leg relative
to OFF, in the same world:

- `dungeon_crawl`: total `simulation_events.jsonl` line count OFF=22395 vs ON=20261 (both large,
  neither collapsed); breaking down by `event_type`, the only categories that differ at all are
  SOCIAL-domain (`contract_offer_created` 7197→6271, `contract_expired_offer` 7127→6201,
  `cooperation_event` 7611→7329, `commitment_abandoned` 40→28, `GovernorModeChanged` 162→174) — all
  stay in the thousands, none zero out. This reads as ordinary cascading divergence (entities
  receiving `force_route_reevaluation` make different movement/interaction choices, which shifts
  downstream contract-formation opportunities over a 2000-tick window), not suppression — a real
  suppression bug collapses a signal to zero or near-zero, not shifts it ±13% within the same
  order of magnitude.
- `resource_dense_basin`: total event count OFF=3707 vs ON=5468 — an *increase*, not a collapse.
  Every domain-independent signal that changed moved in the same direction (up): `combat_damage`
  3→4, `combat_engagement_ended` 56→89, `combat_initiated` 8→12, `cooperation_event` 1841→2345,
  `contract_offer_created` 836→1452, `entity_killed` 0→1 (new activity, not suppressed),
  `gold_transaction` 3→4, `xp_granted` 3→4. `world_emergence_event` itself (the red-herring signal
  investigation.md disqualified) shifted 3→2 — small numbers either way, consistent with it being
  produced by other phases entirely and not a reliable ON/OFF signal for this flag specifically, as
  already established.

`WorldEmergencePhase.execute()`'s `dataclasses.replace(update, ...)` call (confirmed again by
direct read this session, `phase.py:129-135`) continues to carry forward every field it does not
explicitly set — this real 4-leg trial's empirical result (no domain's independent signal
collapsed) is consistent with that static structural finding, not contradicting it.

**Verdict: no suppression regression in either world.**

## Honest gap — quest-registry growth (Signal 3) is untestable from this trial, not just zero

Both trial worlds were chosen specifically for their expected event-producing profile
(`dungeon_crawl`'s `monster_only_gauntlet` archetype for `ENTITY_DEATH`/`CAMP_RAID`;
`resource_dense_basin`'s highest shipped `resource_density` for `RESOURCE_DEPLETED`), per
investigation.md's and plan.md's own stated reasoning. In practice, **neither world produced a
single `RESOURCE_DEPLETED`, `ENTITY_DEATH`, or `CAMP_RAID` `WorldEvent` in any leg** (Signal 5) —
the only `world_events_add` category observed anywhere in this trial was `COMBAT_LOSS` (1-3
occurrences per leg), which is not one of the three categories `QuestOpportunityGenerator` reads.
This means Signal 3's `0` quest-registry growth on every leg, including both ON legs, is **not**
evidence of suppression (the OFF legs would trivially also show `0`, since the phase does not run
at all when OFF) and is **not** evidence the mechanism itself is broken (its own parity-ledger
tests, `WORLD-098`/`WORLD-099`/`WORLD-102`, already cover it directly and passed in Step 10's
regression run below) — it is evidence that **this specific trial's two worlds, at these
seeds/tick-counts, never crossed the precondition this pathway needs to fire at all**. This is
disclosed as a genuine limitation of this trial's chosen worlds, not smoothed over: quest-seeding
specifically remains empirically unconfirmed in a real corpus run by this ticket, even though the
phase's own execution, telemetry, and entity-signal-bridging (Signals 1, 2, 4) are all confirmed
real and working. Per the orchestrator's hard constraint, this is disclosed here and not fixed,
worked around, or compensated for with a third trial world inline — a future ticket wanting to
close this specific gap would need a world/seed/tick-count combination independently confirmed to
produce real `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` events in its baseline first (this
trial's own `dungeon_crawl`/`resource_dense_basin` choices, despite being the best available
candidates per the corpus registry's own density/archetype metadata, did not turn out to satisfy
that precondition).

## Recommendation

**Keep OFF, deferred — real trial evidence now on file, no shipped profile turns it on.**
`grep -rl "ENABLE_WORLD_EMERGENCE" config/simulation_quality/profiles/` returns nothing (confirmed
again this session) — zero shipped `config/simulation_quality/profiles/*.yaml` files enable this
flag today, the same "no shipped production profile" gap that kept both sibling flags
(`ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_SELF_MODEL_COGNITION`) at "keep OFF, deferred" despite each
having its own clean trial. Per `docs/architecture/rollout_flag_decisions_m1.md`'s "The Precedent
This Sets": Flip ON requires real, standing evidence the system already runs safely in
production — "a live SimQ corpus profile already exercising it. A one-off validated fix or trial
is necessary but not sufficient on its own." This ticket's trial is exactly that: a clean, real,
necessary trial (no suppression, real phase execution, real telemetry, real entity-signal
exposure) that is not, on its own, sufficient to meet the flip bar. `ENABLE_WORLD_EMERGENCE`
remains the only one of the three `TCK-20260826-*-FLAG-VALIDATION` siblings run so far with **zero**
prior real-world evidence of any kind before this ticket (unlike `ENABLE_COMBAT_ENGAGEMENT`'s
TCK-20260809 bug-fix history or `ENABLE_SELF_MODEL_COGNITION`'s `unit_selfmodel_pilot` shipped
profile and `INFRA-266` generalization trial) — this ticket's own trial is now that flag's first
and only standing real-corpus evidence, and it is clean but thin (Honest Gap above: quest-seeding
specifically remains unconfirmed). No new `docs/guidelines/intentional_divergences.md` entry is
added — a "keep OFF, deferred" outcome does not create a divergence from the Mechanics Bible. If a
future ticket wants to re-open this: either (a) a shipped SimQ corpus profile begins using
`ENABLE_WORLD_EMERGENCE=ON` in production, matching the DEV-003 precedent directly, or (b) a fresh
trial on a world/seed/tick-count combination independently confirmed to produce real
`RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` baseline activity closes the Honest Gap above.

**`ENABLE_WORLD_CAPABILITY_LAYER` combination — resolved, static analysis only, confirmed again
this session.** `grep -rn "ENABLE_WORLD_CAPABILITY_LAYER" src/ tools/ tests/ config/` returns
exactly its own registration (`feature_flags.py:14`, default OFF), a test-scaffold
`pressure_signals` dict entry in `src/testing/scenario_runner.py:101` that maps to nothing (no
phase names this flag in a `run_phase(..., feature_flag=...)` call), `calibrate_simq.py`'s
`_KNOWN_FLAGS` allowlist, and `tests/integration/test_scenario_feature_flag_defaults.py`'s own
default-OFF allowlist entry — no live gating call site. A separate grep for `WorldCapabilityLayer`
as a class/module name anywhere in `src/` returns zero matches — no such phase or service exists
in the codebase at all, a stronger inertness finding than `ENABLE_ADVENTURE_ROUTING`'s own case
(which used to gate a real, now-deleted phase). Combining it `ON` with
`ENABLE_WORLD_EMERGENCE=ON` is structurally impossible to produce any interaction — there is no
runtime path for its value to reach any code. No empirical combination trial was run (a trial
cannot produce a different answer than the static analysis already gives). A new durable
regression guard, `tests/architecture/test_world_capability_layer_flag_inert.py::
test_enable_world_capability_layer_has_no_live_gating_call_site`, was added, mirroring the sibling
`ENABLE_ADVENTURE_ROUTING` guard exactly — `2 passed` (both the new guard and the pre-existing
sibling guard) when run this session.
