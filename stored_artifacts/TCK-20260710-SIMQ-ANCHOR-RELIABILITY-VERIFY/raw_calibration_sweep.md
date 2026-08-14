---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Raw Calibration Sweep — TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY

Working evidence file (not a required staging artifact). All 18 `SLOW_ANCHOR_KEYS` re-run
3x each via `tools/calibrate_simq.py`, real throttled `Kernel` (no `audit_mode`). Trial 1 =
canonical output path (`data/calibration/{run_key}/`); Trial 2/3 = `--output
data/calibration/{run_key}_trial{2,3}/`. `elapsed_s` = engine tick-loop wall-clock time
(printed by `calibrate_simq.py`). `budget_warnings` = count of `Tick N exceeded budget`
log lines (mid-tick emergency throttle, `kernel.py:574-601`). `watchdog_trips` = count of
`WatchdogTrip` CRITICAL alerts (end-of-tick DEGRADED-mode transition, `kernel.py:420-442`).
These counts confirm the throttle mechanism fired in every single run (never zero), and
varied trial-to-trial for identical seed/code — direct evidence of the F6 wall-clock
mechanism operating during this sweep, not a hypothetical.

## `dungeon_crawl_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 24.24 | 703 | 55 | 1 |
| trial2 | 22.69 | 666 | 49 | 1 |
| trial3 | 24.35 | 686 | 53 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | C | C | C | C |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `dungeon_crawl_seed123_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 20.66 | 626 | 51 | 1 |
| trial2 | 23.04 | 643 | 47 | 1 |
| trial3 | 21.91 | 641 | 50 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | C | C | C | C |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `dungeon_crawl_seed456_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 21.38 | 626 | 64 | 1 |
| trial2 | 20.50 | 598 | 41 | 1 |
| trial3 | 23.36 | 608 | 48 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | C | C | C | C |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `dungeon_crawl_seed42_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 44.49 | 829 | 118 | 1 |
| trial2 | 45.44 | 837 | 105 | 1 |
| trial3 | 41.19 | 854 | 93 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | C | C | C | C |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `dungeon_crawl_seed123_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 42.49 | 779 | 114 | 1 |
| trial2 | 46.39 | 765 | 119 | 1 |
| trial3 | 46.63 | 797 | 109 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | C | C | C | C |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `dungeon_crawl_seed456_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 48.79 | 790 | 128 | 1 |
| trial2 | 44.93 | 779 | 121 | 1 |
| trial3 | 44.67 | 752 | 114 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | C | C | C | C |
| COMBAT | B | B | B | B |
| ECONOMY | C | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | C | C | C | C |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `urban_political_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 53.54 | 10834 | 148 | 1 |
| trial2 | 53.34 | 12046 | 156 | 1 |
| trial3 | 53.13 | 11338 | 114 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | B | B | B | B |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | S | S | S | S |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): S / S / S

## `urban_political_seed123_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 84.38 | 18669 | 424 | 2 |
| trial2 | 65.88 | 14522 | 225 | 2 |
| trial3 | 69.21 | 15449 | 303 | 2 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | B | B | B | B |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | S | S | S | S |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): S / S / S

## `urban_political_seed456_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 65.46 | 15278 | 222 | 2 |
| trial2 | 64.43 | 15982 | 191 | 2 |
| trial3 | 59.44 | 14711 | 153 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | B | B | B | B |
| NARRATIVE | B | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | S | S | S | S |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): S / S / S

## `urban_political_seed42_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 146.29 | 26831 | 539 | 3 |
| trial2 | 121.82 | 28258 | 276 | 2 |
| trial3 | 113.21 | 26819 | 258 | 2 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | B | B | B | B |
| NARRATIVE | B | B | B | B |
| PROGRESSION | B | B | B | B |
| SOCIAL | S | S | S | S |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): S / S / S

## `sandbox_world_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 21.18 | 319 | 73 | 1 |
| trial2 | 19.33 | 310 | 65 | 1 |
| trial3 | 20.67 | 319 | 64 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | B | B | B | B |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `sandbox_world_seed42_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 39.97 | 462 | 117 | 1 |
| trial2 | 37.95 | 487 | 122 | 1 |
| trial3 | 40.24 | 491 | 122 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | B | B | B | B |
| NARRATIVE | A | B | B | B |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `unit_faction_tension_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 18.95 | 310 | 59 | 1 |
| trial2 | 15.99 | 300 | 53 | 1 |
| trial3 | 71.41 | 311 | 72 | 2 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | C | C | C | C |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `unit_faction_tension_seed42_2000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 30.34 | 460 | 117 | 1 |
| trial2 | 27.36 | 444 | 100 | 1 |
| trial3 | 28.90 | 458 | 113 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | B | B | B | B |
| INFORMATION | C | C | C | C |
| NARRATIVE | A | A | B | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## `unit_selfmodel_pilot_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 36.90 | 17354 | 84 | 1 |
| trial2 | 38.81 | 17363 | 82 | 1 |
| trial3 | 38.05 | 17360 | 94 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | S | S | S | S |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | C | C | C | C |
| INFORMATION | C | C | C | C |
| NARRATIVE | B | B | B | B |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): A / A / A

## `hero_guild_routing_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 21.36 | 2197 | 58 | 1 |
| trial2 | 21.09 | 2203 | 58 | 1 |
| trial3 | 22.36 | 2197 | 59 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | A | A | A | A |
| COGNITION | A | A | A | A |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | C | C | C | C |
| INFORMATION | C | C | C | C |
| NARRATIVE | S | S | S | S |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): A / A / A

## `simq_routing_test_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 20.47 | 2178 | 47 | 1 |
| trial2 | 22.22 | 2185 | 67 | 1 |
| trial3 | 22.44 | 2174 | 56 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | A | A | A | A |
| COGNITION | A | A | A | A |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | C | C | C | C |
| INFORMATION | C | C | C | C |
| NARRATIVE | S | S | S | S |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): A / A / A

## `generated_frontier_3_42_seed42_1000t`

**Timing / throttle evidence:**

| Trial | elapsed_s | events | budget_warnings | watchdog_trips |
|---|---|---|---|---|
| trial1 | 24.32 | 644 | 77 | 1 |
| trial2 | 23.08 | 639 | 71 | 1 |
| trial3 | 23.15 | 624 | 48 | 1 |

**Per-pillar grades:**

| Pillar | Anchor | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|---|
| AGENCY | C | C | C | C |
| COGNITION | B | B | B | B |
| COMBAT | B | B | B | B |
| ECONOMY | B | B | B | B |
| FACTION | A | A | A | A |
| INFORMATION | B | B | B | B |
| NARRATIVE | A | A | A | A |
| PROGRESSION | B | B | B | B |
| SOCIAL | C | C | C | C |
| WORLD | B | B | B | B |

Overall grade (T1/T2/T3): B / B / B

## Classification

Classification rule (per plan.md Step 2): a key is **stable** if every trial's every
pillar grade is within the existing ±1-`GRADE_ORDER` band
(`test_grade_regression.py:140-148`, `_within_band`) of the committed anchor in
`grade_anchors.json`. **unstable** if any trial/pillar falls outside that band with
run-to-run scatter (not all trials landing on the identical off-anchor grade).
**escalate** if a violation is out-of-band AND all 3 trials agree on the same off-anchor
grade (looks like a genuine, reproducible drift rather than throttle noise).

| Key | Status | Notes |
|---|---|---|
| `dungeon_crawl_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `dungeon_crawl_seed123_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `dungeon_crawl_seed456_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `dungeon_crawl_seed42_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `dungeon_crawl_seed123_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `dungeon_crawl_seed456_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `urban_political_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `urban_political_seed123_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `urban_political_seed456_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `urban_political_seed42_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `sandbox_world_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `sandbox_world_seed42_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `unit_faction_tension_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `unit_faction_tension_seed42_2000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `unit_selfmodel_pilot_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `hero_guild_routing_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `simq_routing_test_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |
| `generated_frontier_3_42_seed42_1000t` | **stable** | All 10 pillars, all 3 trials within ±1 band of anchor. Zero band violations. |

**Result: all 18/18 keys classified stable. Zero unstable, zero escalate.**

Every pillar/trial combination across all 18 keys x 3 trials x 10 pillars (540 data
points) landed within the ±1-letter band of its committed anchor, despite the timing
table above confirming real, variable throttle activity (budget_warnings ranging
41-539 per run, watchdog_trips 1-3, elapsed_s varying up to ~4x for identical seed/code
within the same key — e.g. `unit_faction_tension_seed42_1000t` trial3 took 71.41s vs
15.99-18.95s for trials 1-2). A small number of pillars show a *consistent* one-band
difference from the anchor across all 3 trials for a given key (e.g.
`dungeon_crawl_*` ECONOMY anchor=C vs. observed B in all trials; `dungeon_crawl_seed123_*`
NARRATIVE anchor=B vs. observed A in all trials; `sandbox_world_seed42_2000t` NARRATIVE
anchor=A vs. observed B in all trials) — these are still within the ±1 band (not
violations) and are not evaluated under the escalate rule, since the escalate rule only
applies to out-of-band violations. No out-of-band violation occurred anywhere in this
sweep, so the escalate path was never triggered.

**Step 4 outcome: documented no-op.** Zero keys were classified unstable, so no new
`@pytest.mark.slow` grade-stability multi-trial test was added to
`tests/unit/worldassembly/test_corpus_diversity.py`. This is a valid, explicitly
documented outcome per plan.md Step 4 and test_plan.md's callout that a zero-conversion
result must still be documented, not skipped silently.
