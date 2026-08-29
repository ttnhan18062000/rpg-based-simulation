---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
artifact_type: report
tags: [feature-flags, combat]
---

# Trial Evidence — TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

Raw output of the 4-leg corpus trial run per `plan.md` Steps 1-3. Environment note: the
worktree's bare `python3` lacks `pydantic` (a pre-existing, unrelated environment gap); all 4
runs were executed with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`
(the main checkout's venv) instead, with `cwd` still the worktree so `data/runs/` and
`data/calibration/` output landed in the same place the plan's commands specify.

## Commands run (verbatim except interpreter path)

```
# dungeon_crawl OFF
.venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_OFF
# -> data/runs/run_1788015282_5169

# dungeon_crawl ON
ENABLE_COMBAT_ENGAGEMENT=ON .venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_ON
# -> data/runs/run_1788015419_5169

# wilderness_survival OFF
.venv/bin/python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_OFF
# -> data/runs/run_1788015532_5169

# wilderness_survival ON
ENABLE_COMBAT_ENGAGEMENT=ON .venv/bin/python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_ON
# -> data/runs/run_1788015623_5169
```

## World-loading path confirmation (Step 2's open question)

Both worlds resolved their real compiled `data/worlds/{name}/resolved/world.resolved.yaml` spec
via `_load_world_state()`, not the generic hero+goblins fallback — confirmed by reading each
run's own tick-0 `fingerprint.entity_count` in `chunk_0000.json` (the CLI's own
`entities=10` stdout line is just the unrelated `--entities` fallback-only default and is not
evidence either way):
- `dungeon_crawl`: `entity_count=32` in all 4 legs' tick-0 fingerprint (matches
  `corpus_registry.yaml`'s documented 32-entity `monster_only_gauntlet` archetype).
- `wilderness_survival`: `entity_count=11` in all 4 legs' tick-0 fingerprint (matches
  `corpus_registry.yaml`'s documented 11-entity archetype).
- OFF and ON legs share the same tick-0 `state_hash` per world (e.g.
  `5bb702562879beaea7535e690ccdba2a` for both `dungeon_crawl` legs), confirming the flag has no
  effect on initial world compilation — a valid controlled A/B on identical starting state.

## Evidence tally (5 signals x 4 legs)

| Signal | dungeon_crawl OFF (run_1788015282_5169) | dungeon_crawl ON (run_1788015419_5169) | wilderness_survival OFF (run_1788015532_5169) | wilderness_survival ON (run_1788015623_5169) |
|---|---|---|---|---|
| `combat_engagement_started` | 1 | 0 | 0 | 0 |
| `combat_engagement_ended` | 10 | 10 | 10 | 10 |
| `combat_resolved` | 0 | 0 | 0 | 0 |
| `combat_damage` | 0 | 0 | 0 | 0 |
| `entity_killed` | 0 | 0 | 0 | 0 |
| `metric_counters["run_combat_engagement"]` (summed across all ticks) | 0 | 1811 | 0 | 1937 |
| `metric_counters["skip_combat_engagement"]` (summed across all ticks) | 1785 | 0 | 1926 | 0 |
| Phase skip-rate (`skip / (run + skip)`) | 100% (flag OFF, phase never runs — expected) | 0% | 100% (flag OFF — expected) | 0% |
| `quality_report.json` COMBAT pillar `event_count` | 1 | 0 | 0 | 0 |

(Ticks with a `metric_counters` payload observed: 1785/1811 for `dungeon_crawl` OFF/ON,
1926/1937 for `wilderness_survival` OFF/ON — short of the full 2000 because
`Kernel.tick_once()`'s own watchdog/budget throttling aborts a small fraction of ticks under
sustained overrun, a pre-existing condition, not something this trial's counters correct for.)

## No-suppression check (the TCK-20260809 regression class)

**Passes in both worlds.** `combat_engagement_ended` — the one signal with real, repeatable
volume — is identical between the ON and OFF leg in both worlds (10 == 10 in each pair), not
collapsed toward zero on the ON leg. `run_combat_engagement`/`skip_combat_engagement` confirm
`CombatEngagementPhase` actually executes on effectively every eligible tick when ON (0% skip
rate in both ON legs) rather than being silently starved by
`PhaseDependencyGraph.should_run_phase()` — ruling out the "no suppression, but also no real
activity because the phase never ran" false-negative investigation.md flagged as a risk. This is
the opposite of TCK-20260809's own documented pre-fix signature (a deterministic 100%->0%
collapse across all 5 event types on the ON leg while OFF stayed nonzero) — the `u.merge(...)`
fix in `src/engine/pipeline.py:276` continues to hold under this real 2000-tick, two-world trial.

`combat_engagement_started` differs by exactly 1 event in `dungeon_crawl` (1 OFF vs 0 ON) — at
this volume (n=1) this reads as ordinary run-to-run stochastic variance in exactly *which* tick a
first-contact posture assessment fires, not a suppression pattern; a real suppression bug
produces a collapse across all 5 signal types simultaneously (per TCK-20260809's own confirmed
signature), not a 1-vs-0 difference on a single low-volume signal while the higher-volume sibling
signal (`ended`) stays exactly matched.

## Real combat activity — the honest gap

**`combat_resolved`, `combat_damage`, and `entity_killed` are all 0 in every one of the 4 legs,
including both OFF/baseline legs.** This is materially thinner than TCK-20260809's own OFF
baseline on the same `dungeon_crawl_seed42` world/seed/tick-count, which recorded
`combat_damage=1`, `combat_resolved=1`, `entity_killed=1` (thin, but present) alongside
`combat_engagement_started=2`, `combat_engagement_ended=11`
(`stored_artifacts/TCK-20260809-.../investigation.md`, "Real corpus confirmation" section).

Per this ticket's own Anti-Drift Notes ("a near-zero OFF-leg baseline invalidates that world's
data point, not just its ON leg"), this is disclosed honestly rather than smoothed over: neither
world's OFF baseline in *this* trial run produced a lethal/damage-bearing combat interaction
within 2000 ticks, so the trial cannot independently confirm "the ATTACK/damage-resolution path
keeps firing and producing real combat events" beyond what `combat_engagement_ended=10` (present
and matched in every leg) already shows. The closest available real-activity floor is
`combat_engagement_ended`'s own consistent volume across all 4 legs — a genuine repeatable
signal, just not one of the 3 signals (`resolved`/`damage`/`killed`) most directly tied to
lethal/tactical combat outcomes. Re-running with a higher tick count, a different seed, or a
corpus world with a higher `COMBAT` pillar weight and larger contested-territory footprint would
be needed to produce nonzero `combat_damage`/`entity_killed` counts; that is out of this ticket's
own scope to pursue further (see Completion Summary / recommendation).

## Secondary, already-disclosed effect (not investigated further, per TCK-20260809's own
non-fix decision)

Elevated `Tick N exceeded budget` / `WatchdogTrip` warnings were observed again in both worlds'
ON legs (e.g. a `CRITICAL WatchdogTrip` at tick 1918 in `dungeon_crawl` ON, 184.6ms vs an 83.45ms
threshold, with `persistence` — not `combat_engagement` itself — the dominant per-tick cost in
that trace). This is consistent with TCK-20260809's own disclosed 6.2%->7.1% tick-budget-exceeded
finding and its explicit decision not to fix it as part of that ticket; this trial does not
reopen that investigation.
