---
status: active
layer: simulation
authority: P1
audience: agent
tags: [audit, long-run, performance, attrition, behavioral-continuity, rejection-cascade, ecology]
---

# D06 — Long-Run Simulation Health

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | run-sim |
| **Audit date** | 2026-06-19 (original); 2026-07-09 (F6 added — wall-clock non-determinism finding from `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`) |

**What this dimension answers:** Does the simulation remain healthy, performant, and behaviorally active across 1,000 ticks — or do entities stagnate, the world deplete, or the engine degrade? This is the first long-run observation after the RC1/RC2/RC3 fixes. D03 confirmed behavioral stasis onset by tick 20 under the broken pipeline. This audit confirms the RC fixes restored behavioral activity while revealing new systemic gaps at the 1,000-tick scale.

**Related dimensions:**

| Dimension | Relationship |
|---|---|
| D03 (Behavioral Emergence) | RC1/RC2/RC3 root causes confirmed there; fixes applied before this run |
| D05 (Entity Differentiation) | Depends on route variety observed here — F1 is a prerequisite gap |
| D04 (Balance & Tuning) | Economic output still zero (F1); tuning analysis remains blocked |

---

## Run Summary

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Outcome | SUCCESS | SUCCESS |
| Governor | NORMAL throughout | NORMAL throughout |
| Hard law violations | 0 | 0 |
| Final state hash | `86a9569…` | `62219f1…` |
| Total simulation events | 253 | 221 |
| Event types observed | quest_event, combat_damage | quest_event, combat_damage |
| Project kinds observed | hunger, recover, combat_retreat, combat_engage, resolve_blocker | hunger, recover, combat_retreat, combat_engage, resolve_blocker |
| Last behavioral event | tick 997 | tick 999 |

### Metric Window Summary — Seed 42

| Ticks | alive_avg | rejections (cumulative) | events | ms_avg | p95_ms | gold_avg | mem_MB |
|---|---|---|---|---|---|---|---|
| 1–100 | 15.3 | 94 | 8 | 14.7 | 28.0 | 0 | 67.0 |
| 101–200 | 15.0 | 100 | 0 | 12.9 | 23.3 | 0 | 79.3 |
| 201–300 | 15.0 | 30,554 | 37 | 11.9 | 18.3 | 0 | 82.0 |
| 301–400 | 15.0 | 109,943 | 33 | 11.4 | 15.2 | 0 | 83.7 |
| 401–500 | 15.0 | 181,413 | 8 | 11.8 | 17.5 | 0 | 84.7 |
| 501–600 | **18.0** | 248,700 | 24 | 15.3 | 21.5 | **120.0** | 93.1 |
| 601–700 | 18.0 | 314,978 | 8 | 14.7 | 23.4 | 120.0 | 94.5 |
| 701–800 | 18.0 | 388,637 | 33 | 14.3 | 22.0 | 120.0 | 95.5 |
| 801–900 | 15.7 | 478,100 | 64 | 14.6 | 24.6 | 120.0 | 95.9 |
| 901–1000 | **13.1** | **549,612** | 38 | 14.5 | 20.8 | 120.0 | 96.0 |

### Metric Window Summary — Seed 137

| Ticks | alive_avg | rejections (cumulative) | events | ms_avg | p95_ms | gold_avg | mem_MB |
|---|---|---|---|---|---|---|---|
| 1–100 | 15.4 | 426 | 9 | 13.6 | 17.8 | 0 | 64.4 |
| 101–200 | 15.0 | 500 | 0 | 9.0 | 15.4 | 0 | 78.3 |
| 201–300 | 15.0 | 33,890 | 41 | 12.6 | 23.2 | 0 | 79.4 |
| 301–400 | 15.0 | 112,740 | 41 | 15.4 | 28.7 | 0 | 83.9 |
| 401–500 | 15.0 | 182,874 | 4 | 15.5 | 20.0 | 0 | 85.9 |
| 501–600 | **18.0** | 244,515 | 12 | 15.5 | 22.3 | **120.0** | 94.2 |
| 601–700 | 18.0 | 304,969 | 4 | 13.4 | 18.1 | 120.0 | 95.1 |
| 701–800 | 17.8 | 372,074 | 28 | 15.1 | 19.9 | 120.0 | 95.1 |
| 801–900 | 15.1 | 438,155 | 33 | 13.4 | 19.6 | 120.0 | 95.7 |
| 901–1000 | **14.6** | **497,062** | 49 | 15.3 | 23.0 | 120.0 | 93.6 |

---

## Positive Observations

- Both 1,000-tick runs complete with `LifecycleOutcome.SUCCESS`, zero hard law violations, governor NORMAL throughout.
- **Tick compute is stable**: avg 9–15ms across all windows, well within the 50ms performance contract. No degradation trend across the 1,000-tick run.
- **Memory is bounded**: +29MB over 1,000 ticks (67→96MB). No unbounded growth. Memory stabilises at ~95MB after tick 500.
- **RC fixes restored behavioral activity**: 240–253 events per 1,000-tick run vs. 8–9 events in D03. Events are continuous from tick ~201 through tick 997/999 — including quest_event and combat_damage. This directly confirms RC1 fix is effective.
- **SpawnService fires at ~tick 500**: Entity count rises from 15 → 18 in both seeds, confirming the spawn ecology system activates and replenishes entities.
- **Behavioral continuity to final tick**: Last events at tick 997/999 confirm the engine does not degrade into silence at long run lengths.

---

## Scoring Method — Emergence Gap Score

Each finding: **Variety Gap × Lifespan Gap × System Silence** (max 15/15, worst).

| Axis | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **Variety Gap** | Many goal kinds observed | 3-4 distinct kinds | 2 kinds | 1 kind, minimal variety | Zero variety, pure stasis |
| **Lifespan Gap** | Active for full run | Active for 75%+ | Active for 50%+ | Active for <25% | Collapses before tick 20 |
| **System Silence** | Multiple systems active | 2-3 systems active | 1 marginally active | 1 active <5 ticks | All systems silent |

---

## Findings

### F1 — Survival-Only Route Selection: Economic and Crafting Pipeline Still Silent

> **RESOLVED: TCK-20260619-E21-RESOURCE-ECOLOGY (2026-06-20):** Resource ecology regeneration implemented; food-kind nodes added to worlds; hunger urgency resolves after harvest.

**Score: 12/15** (Variety Gap=4, Lifespan Gap=4, System Silence=4)

Despite RC1 fix wiring `ResourceOpportunityProvider` into `AdventureDecisionPhase`, only biological survival routes are selected across all 1,000 ticks:

| Project kind | D06 observations |
|---|---|
| `hunger` | Dominant — dozens per 100-tick window |
| `recover` | Early ticks only (initial combat survivors) |
| `combat_retreat` / `combat_engage` | Early ticks and late-run combat only |
| `resolve_blocker` | Scattered — blocker detour system firing |
| `gather_resource` | **Zero** |
| `buy_upgrade` | **Zero** |
| `craft_upgrade` | **Zero** |
| `ask_information` | **Zero** |

The route generator's primary path receives opportunities from `ResourceOpportunityProvider` (RC1 fixed), but the opportunities either fail their requirements or the biological need routes (hunger, recover) outscore them by wide margins every tick. The Tier 2 biological need (hunger) has higher urgency than Tier 3–4 economic goals — entities are perpetually hungry and never advance to resource-gathering or crafting objectives.

**Immediate suspect**: The hunger drive is not being resolved by any food-source opportunity. Without food acquisition happening, hunger urgency stays high every tick, permanently suppressing economic goal selection. This is a content gap (no food-provision opportunity) or a need-satisfaction gap (hunger project completes but need resets immediately), not an architecture gap.

---

### F2 — 200-Tick Activation Delay

> **Ticket:** TCK-20260627-P2A-SPAWN-LOCK-COND

**Score: 7/15** (Variety Gap=5, Lifespan Gap=2, System Silence=5)

Ticks 101–200 produce zero behavioral events in both seeds, identical to D03 observations pre-fix. The RC1 fix has no effect on this window. Events resume at tick ~201.

The likely cause: initial spawn projects (`proj_combat_retreat`, `proj_recover`) lock entities via `lock_until_tick` during the early post-combat crisis period. The adventure routing pipeline cannot assign new routes while a locked project is active. At tick ~200 those locks expire and the RC1-fixed pipeline takes over.

This is not a bug — initial locks prevent jitter during a combat crisis. However, 200 ticks of enforced inactivity (20% of a 1,000-tick run) is a tuning concern: the lock duration may be too aggressive.

---

### F3 — Rejection Cascade: 500K–550K Cumulative by Tick 1,000

> **Ticket:** TCK-20260627-P1A-REJECTION-BACKOFF

**Score: 11/15** (Variety Gap=4, Lifespan Gap=4, System Silence=3)

| Seed | Ticks 1–200 | Ticks 201–1000 | Rate (ticks 201–1000) | Cumulative at tick 1000 |
|---|---|---|---|---|
| 42 | 100 | 549,512 | ~686/tick | 549,612 |
| 137 | 500 | 496,562 | ~620/tick | 497,062 |

The RC1 fix paradoxically worsens the rejection cascade: with the opportunity pipeline now firing, entities evaluate many requirements per tick that fail. The rate jumps from ~1/tick (ticks 1–200, stale projects only) to ~600–700/tick (ticks 201–1000, opportunity requirements evaluated each tick).

The monotonic increase confirms no cooldown, stale-project expiry, or backoff mechanism exists. At this rate, over a 5,000-tick run the cumulative counter would reach 3–4 million — a memory and diagnostic noise concern.

**RC4 status**: The original D03 RC4 (stale spawn-projects retrying) is now compounded by the live opportunity pipeline also generating requirements that fail. Both sources contribute to the cascade.

---

### F4 — Quest System Never Activates

> **Ticket:** TCK-20260627-P1B-QUEST-ACTIVATION

**Score: 15/15** (Variety Gap=5, Lifespan Gap=5, System Silence=5)

`quest_active_count = 0.0` and `quest_completed_count = 0.0` across all 1,000 ticks in both seeds. The 240–253 `quest_event` entries in `simulation_events.jsonl` are project status transitions (`proj_hunger_N updated to status started`), not formal quest activations from the `QuestSystem`.

The quest generation pathway (`src/systems/world_systems/quests.py`, `LEG-RPG-141`) maps strategic blockers → quest templates → strategic projects. For it to activate, an entity must have a material or access blocker that triggers quest generation. With entities perpetually in survival/hunger mode (F1), no material blockers are being generated, and the quest system has no trigger.

This confirms the system architecture is correct but the behavioral preconditions (material blocker generation from economic goal pursuit) are unreachable while F1 persists.

---

### F5 — Late-Run Attrition Exceeds Spawn Rate

> **Ticket:** TCK-20260627-P2B-SPAWN-CADENCE

**Score: 9/15** (Variety Gap=3, Lifespan Gap=3, System Silence=4)

| Phase | Seed 42 alive_avg | Seed 137 alive_avg |
|---|---|---|
| Ticks 1–200 | 15.3 → 15.0 | 15.4 → 15.0 |
| Ticks 501–700 | **18.0** (spawn fired) | **18.0** (spawn fired) |
| Ticks 801–900 | 15.7 (declining) | 15.1 (declining) |
| Ticks 901–1000 | **13.1** (net loss) | **14.6** (net loss) |

SpawnService fires at ~tick 500 and successfully adds 3 entities in both seeds. However, combat attrition in late ticks (combat_damage events reappear at ticks 800–1000) kills entities faster than the spawn rate can replace them. The net entity count at tick 1,000 is below the starting count of 15 in both seeds.

For a 1,000-tick run this is marginal. A 5,000-tick run risks entity count approaching zero.

**Status update (2026-07-04):** `docs/plans/audit_fix_plan.md`'s P2-B entry (sourced from this
finding) is now **RESOLVED** — `src/world/spawn.py`'s two-tier `SpawnConfig` cadence (WORLD-103)
addresses the spawn/attrition rate directly. A *separate*, previously-conflated symptom — total
early-tick population collapse in `frontier_extended`/`frontier_living_world`/`wilderness_survival`
(56→13 alive within the first 50 ticks in one case) — was root-caused by
`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` (2026-07-04) to a *different* cause entirely: those
worlds' compiled content was stale relative to the 2026-07-01 hazard-native-immunity fix, so
entities took unmitigated lethal hazard drain in their own habitat. Fixed by adding missing
`hazard_kind` declarations to 7 world modules and recompiling. All 5 previously-collapsing or
never-checked worlds now hold ≥60% population over 300 ticks — see
`docs/simulation_quality/eval_matrix_results.md` for the current numbers. The `sandbox_world`
data in this table itself predates that world's `worldcomposition.v1` migration
(`TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`) and is retained here as the original historical
measurement, not updated in place.

---

### F6 — Wall-Clock-Dependent Non-Determinism at Long Tick Counts (Tick-Budget Throttle)

> **Discovered:** 2026-07-09, `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`
> **Status:** Documented, not fixed — intentional engine behavior, not a bug

**Score: not scored on the Emergence Gap axes above (this is a determinism/reproducibility finding, not
a behavioral-emergence gap) — flagged here because D06 owns "does the simulation remain healthy... across
1,000+ ticks," and this finding is specifically a long-run-scale phenomenon invisible at ≤300 ticks.**

Investigating a late-tick (800→1000) population collapse in `generated_frontier_3_42`, two independent
instrumented drives — same seed (42), same code, same machine, run back-to-back — diverged sharply:
floor-violation onset differed by 100+ ticks (tick 860 vs. 960) and the tick-1000 population endpoint
differed by more than 2× (12/44 vs. 5/44 alive). Root cause: `src/engine/kernel.py`'s tick-budget
watchdog (`kernel.py:420-442`) and mid-tick emergency throttle (`kernel.py:574-601`) measure **real
wall-clock compute time** per tick (`time.perf_counter_ns()`), and when a tick's measured time exceeds
budget, the mid-tick path drops the remaining resolution-queue work items for that tick — entities do not
act, defend, or flee that tick. *Which* entities get dropped depends on where in the resolution queue the
elapsed-time check trips, which depends on actual wall-clock timing (system load, scheduler jitter, GC
pauses), not the deterministic seed or RNG stream.

Both throttle paths are documented, intentional behavior (`docs/engine/kernel.md` §"Emergency
Throttling") and are already known to be non-determinism-guaranteed (`docs/engine/kernel.md` §"State
Hashing in Phase 7": canonical hash is `"SKIPPED"` in `DEGRADED` mode) — this finding does not reveal a
new violation, it is the **first population-outcome-level test to actually encounter** an already-known
gap, because no existing hard-assertion test previously drove any corpus world past ~tick 400-500 in a
non-`audit_mode` context. The first `"Tick N exceeded budget"` watchdog warning fires at tick ~300-320 in
every observed run; below that, floor assertions are reliably reproducible (confirmed: the existing
300-tick `test_population_stability` window has never shown this divergence).

**Resolution applied (narrow, not a fix for the underlying non-determinism):** `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`
added `test_generated_frontier_3_42_extended_population_stability` — a tolerance-based regression guard
(3 same-seed trials, throttling left active/no `audit_mode`, hard per-trial floor through tick 800,
relaxed mean-across-trials floors at ticks 900/1000, hard no-full-extinction check) rather than a tight
per-tick assertion, since the investigation confirmed a tight assertion would be empirically false and
`audit_mode=True` would verify a materially different (unthrottled, unrealistically optimistic) scenario.
Explicitly did **not** touch `kernel.py`'s watchdog/throttle/`ResourceGovernor` logic — that is documented,
intentional, corpus-wide engine behavior governing real hardware-class performance scaling
(`docs/engine/performance_contract.md` §7), not a `generated_frontier_3_42`-specific defect.

**Open question for a future ticket (not resolved here):** whether other long-run calibration tiers
(the 1000t/2000t anchors added by `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` and others in
`docs/simulation_quality/eval_matrix_results.md`) are silently exposed to the same run-to-run variance in
their `quality_report.json` outputs — i.e. whether a single calibration run's grade is representative or
got a lucky/unlucky throttle-timing draw. Out of scope for the ticket that found this; flagged so a future
audit does not have to rediscover the mechanism from scratch.

> **Resolved 2026-07-11, `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`:** all 18 `SLOW_ANCHOR_KEYS`
> entries re-run 3 independent same-seed trials each (54 total runs, real throttled `Kernel`, no
> `audit_mode`), transcribed in `staging_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`
> and documented per-key in `docs/simulation_quality/eval_matrix_results.md`'s "Anchor Reliability
> Verification" section. Result: **18/18 keys stable** — every one of 540 pillar/trial data points
> landed within the existing ±1-`GRADE_ORDER` band, despite confirmed throttle-timing variance
> (`budget_warnings` 41–539/run, `watchdog_trips` 1–3/run, up to ~4× elapsed-time spread for
> identical seed/code within a single key). No anchor required conversion to a tolerance-based guard
> and no anchor was flagged unverified. `kernel.py` and `grade_anchors.json` were left untouched, per
> this finding's scope guard.

---

## Key Findings Summary

| Finding | Score | Description |
|---|---|---|
| F1 | 12/15 | Survival-only routes — hunger perpetually outscores economic goals; gather/craft/trade pipeline silent |
| F2 | 7/15 | 200-tick activation delay from initial spawn project locks |
| F3 | 11/15 | Rejection cascade grows to 500K–550K/run at ~650/tick after RC1 fix |
| F4 | 15/15 | Quest system never activates — no material blockers generated while F1 persists |
| F5 | 9/15 | Late-run attrition exceeds spawn rate; entity count ends below starting count — **RESOLVED** (P2-B, `SpawnConfig` two-tier cadence); a separately-conflated early-collapse symptom in other worlds fixed 2026-07-04 by `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` (stale hazard-kind content, unrelated cause) |
| F6 | N/A | Wall-clock-dependent non-determinism past ~tick 300-320 (tick-budget throttle drops resolution work based on real compute time, not seed) — **documented, not fixed** (intentional engine behavior); narrow mitigation applied via a tolerance-based regression guard, `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` (2026-07-09); all 18 shipped long-run anchors re-verified stable against this variance, `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (2026-07-11) |

**Performance — all green:**
- Tick compute: 9–15ms avg, stable, well within 50ms budget ✓
- Memory: bounded +29MB across 1,000 ticks ✓
- Governor: NORMAL throughout ✓
- Hard law violations: 0 ✓

---

## Recommended Follow-Up

**P0 — Resolve hunger satiation gap (unblocks F1, F4)**
Entities are perpetually hungry because no food-provision opportunity exists or the hunger project does not resolve the hunger need. Confirm that completing a `hunger` project reduces hunger drive score — if it does not, the need resets immediately and hunger permanently outscores economic goals. Check `src/engine/pipeline_phases/advancement.py` and the need satisfaction contract.

**P1 — Add project rejection backoff / stale-project expiry (F3)**
At 500K–650K cumulative rejections per 1,000-tick run, the rejection counter is a diagnostic noise source and a potential memory concern at 5,000+ ticks. Add a max-retry count or tick-expiry to `ProjectState` such that a project is abandoned after N consecutive rejections. This was identified in D03 as P1.

**P1 — Tune initial project lock duration (F2)**
If the `lock_until_tick` for `proj_combat_retreat` / `proj_recover` is currently 200 ticks, reduce it or make it conditional on the threat resolving (entity health restored, combat enemies dead). A 200-tick enforced dead zone represents 20% of a standard 1,000-tick run.

**P2 — D04 and D05 now unblocked but conditionally**
D04 (Balance & Tuning) and D05 (Entity Differentiation) can now run, but F1 means economic/crafting tuning analysis is still not possible until hunger satiation is resolved. D05 can observe personality differentiation across survival-tier behavior; it is not blocked by F1 for that scope.

**P2 — Audit whether other long-run SimQ anchors (1000t/2000t) are throttle-timing-sensitive (F6)** — **RESOLVED 2026-07-11**
`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` and other long-run calibration entries in
`docs/simulation_quality/eval_matrix_results.md` were each captured from a single run. F6 confirmed at
least one world (`generated_frontier_3_42`) shows >2× population variance between two back-to-back
same-seed runs past ~tick 300-320. Determine whether any already-shipped 1000t/2000t anchor grade would
flip if re-measured, and whether a tolerance-based re-verification (same pattern as
`test_generated_frontier_3_42_extended_population_stability`) should become the standard for all
long-run anchors rather than a single-run point estimate.
**Sequenced as Phase 0.1 (the blocking first phase)** in `docs/plans/archive/simq_development_roadmap.md`.
**Result (`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`):** all 18 shipped anchors re-verified stable
across 3 trials each — none flip; a tolerance-based re-verification standard was evaluated but found
unnecessary since the existing ±1-`GRADE_ORDER` band already absorbs the observed variance for every
key. See the F6 finding above for full evidence.
