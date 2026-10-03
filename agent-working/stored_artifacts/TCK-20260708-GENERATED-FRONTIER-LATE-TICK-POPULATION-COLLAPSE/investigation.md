---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
artifact_type: investigation
tags: [simulation-quality, world, corpus, calibration]
---

# Investigation — TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE

## Current Behavior

### Method: direct instrumented drive, densified across the 700–1000 window, run twice

Same harness as `test_population_stability` (`WorldRepository.load_world` →
`WorldCompiler.compile` → `Kernel(profile=PROD_SMALL, flags={"no_frame_pacing": True})` →
`tick_once()` loop, seed 42), extended to 1000 ticks with checkpoints every 50 ticks through
tick 700 and every **20** ticks from 700–1000, plus a per-checkpoint `alive_by_faction` /
`dead_by_faction` breakdown (faction resolved via
`src.content_semantics.faction.get_faction_id_str`, the same resolver
`EnvironmentService.calculate_hazard_drain` uses). Run **twice**, back to back, same seed, same
code, same machine, no changes in between — see the non-determinism finding below for why.

Starting composition (44 entities): `town_council:14, goblin_warband:9, wild_beast_pack:5,
orc_clan:5, bandit_company:4, arcane_circle:4, merchant_league:3`.

**Run 1** (key checkpoints):
```
tick  50: alive=38/44 (86.4%)  dead={town_council:2, arcane_circle:4}
tick 400: alive=38/44 (86.4%)  dead={town_council:2, arcane_circle:4}          <- unchanged 50-400
tick 450: alive=34/44 (77.3%)  dead+={orc_clan:4}
tick 550: alive=34/44 (77.3%)  a new 'monster_horde':3 faction appears (calamity/trauma spawn, not part of starting 44)
tick 700: alive=34/44 (77.3%)
tick 800: alive=33/44 (75.0%)
tick 860: alive=31/44 (70.5%)
tick 900: alive=29/44 (65.9%)
tick 920: alive=27/44 (61.4%)  <- last checkpoint still above the 26.4 floor
tick 960: alive=24/44 (54.5%)  <- FIRST floor violation
tick 980: alive=23/44 (52.3%)
tick1000: alive=12/44 (27.3%)
```

**Run 2** (identical code/seed, run immediately after Run 1):
```
tick  50: alive=38/44 (86.4%)  dead={town_council:2, arcane_circle:4}   <- matches Run 1
tick 450: alive=33/44 (75.0%)  dead+={orc_clan:4, bandit_company:1}     <- already diverges from Run 1 (34 vs 33)
tick 700: alive=36/44 (81.8%)
tick 800: alive=32/44 (72.7%)
tick 840: alive=31/44 (70.5%)
tick 860: alive=24/44 (54.5%)  <- FIRST floor violation (100 ticks earlier than Run 1's)
tick 900: alive=19/44 (43.2%)
tick1000: alive= 5/44 (11.4%)
```

**Both runs agree qualitatively**: population holds comfortably through the existing 300-tick
test window (no divergence there — first `tick N exceeded budget` warning in both runs is at
tick 321, after the existing test's last checkpoint at 300), erosion accelerates broadly across
**multiple factions** (`town_council`, `goblin_warband`, `wild_beast_pack`, `bandit_company`,
`merchant_league`) starting somewhere in the **740–860** range, and the 60%-alive floor (26.4) is
violated well before tick 1000 in both runs — consistent with the ticket's own finding. **They
disagree sharply on exact numbers**: floor-violation onset differs by 100 ticks (tick 860 vs.
960) and the tick-1000 endpoint differs by more than 2× (12/44 vs. 5/44). This is same
seed, same code, same machine, back-to-back runs — the divergence is not attributable to seed or
content.

### Root cause 1 (confirmed, reproducible in both runs): `moon_cave`'s missing `hazard_kind` — same bug class as `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`

`data/content/world_modules/moon_cult_ruins.yaml:8-13` declares region `moon_cave` with
`hazard_level: 4.0` (the **highest** hazard level of any region in this world — higher than
`goblin_camp`'s 3.0, `orc_stronghold`'s 3.0, `old_mine`/`bandit_road`'s 2.0) and **no**
`hazard_kind`. `src/worldassembly/resolver.py:798` silently defaults this to `"PHYSICAL"`
(confirmed in the resolved output: `data/worlds/generated_frontier_3_42/resolved/
world.resolved.yaml:46-55`, `hazard_kind: PHYSICAL`). `moon_cave`'s sole populating faction,
`arcane_circle` (`data/content/social/factions.yaml:129-136`), declares **no**
`hazard_immunities` at all. Per `EnvironmentService.calculate_hazard_drain`
(`src/world/environment.py:16-41`), this is `4.0 * (1.0 + calamity_intensity) * 10 ≈ 40`/tick,
unconditional, every tick. The population `moon_cult_apprentice_circle` (4 `apprentice_mage`
entities, `data/content/entities/populations.yaml:88-92`) is the **only** population stationed
there — both instrumented runs show `dead_by_faction={'arcane_circle': 4}` already fully
populated by the **first** checkpoint (tick 50), i.e. 100% of this population is dead almost
immediately, deterministically, in every run. This is the exact bug pattern
`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s investigation diagnosed and fixed for
`dungeon_crawl`/`urban_political`: a `hazard_level > 0` region whose module never declared
`hazard_kind`, colliding with a populating faction that declares no matching immunity.
`generated_frontier_3_42` was not covered by that ticket (explicitly out of scope — see its
Related Tickets) and `moon_cult_ruins` was never in the 7/10-module hazard-kind sweep lists
(`docs/mechanics/05_world_evolution.md` lines 100-106; `NEWLY_ANCHORED_MODULES` in
`test_corpus_diversity.py`, where it is listed as newly anchored but the hazard-kind-**match**
check, `test_hazard_kind_matches_populating_faction_immunity`, only covers
`HAZARD_KIND_MATCH_WORLDS = ["dungeon_crawl", "urban_political"]` — `generated_frontier_3_42` is
not in that list, so this gap was never caught by any existing test).

**This 4-entity loss happens by tick 50 in both runs and is already "baked into" the 86.4%
figure at every checkpoint through tick 400 — it does not, by itself, explain the tick-700-1000
acceleration.** It is a genuine, real, fixable content gap that should be fixed regardless
(same remediation pattern as the sibling ticket), but is not sufficient on its own to account for
the late collapse.

### Root cause 2 (confirmed, same unresolved design question already flagged by the sibling ticket): `bandit_road`-stationed `town_council` guards have no hazard immunity

`data/worlds/generated_frontier_3_42/resolved/world.resolved.yaml:191-196`:
`merchant_caravan_frontier_guard` — 2 `town_council` entities, `role: guard`, `spawn_region:
bandit_road`. `bandit_road` (`data/content/world_modules/bandit_road_trade_pressure.yaml:8-14`)
correctly declares `hazard_kind: "NATURAL_TERRAIN"`, matching `bandit_company`'s own
`hazard_immunities: ["NATURAL_TERRAIN"]` (`factions.yaml:73`) — but `town_council`
(`factions.yaml:12-19`) declares **no** `hazard_immunities` at all. This is the *exact* pattern
`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s investigation flagged as **Risk/Open Question
#2** for `urban_political`'s own `town_council` guards at its own `bandit_road`, and left
explicitly unresolved ("may be intentional 'conflict pressure' flavor... does not have evidence to
decide this either way"). `generated_frontier_3_42` reproduces the identical unresolved case with
the identical faction pairing (`town_council` guard, `bandit_road`, `merchant_league`'s own turf
region shared with `bandit_company`). `town_council`'s dead count climbs steadily across both
instrumented runs (2 dead at tick 50 → 12-13 of 14 dead by tick 1000) — far beyond just the 2
hazard-exposed guards, indicating combat losses dominate `town_council`'s later attrition (see
Root cause 3), but the 2 guards' unmitigated hazard exposure is a real, distinct, fixable gap in
its own right and is already contributing at the earliest checkpoints.

### Root cause 3 (NOT a content bug — an engine/architecture finding): tick-budget-driven `DEGRADED`-mode work-dropping is wall-clock-dependent, not seed-dependent, and explains the run-to-run divergence

`src/engine/kernel.py::_tick_once_inner` measures real wall-clock compute time
(`time.perf_counter_ns()`) every tick. Two independent throttle paths fire when a tick's
**measured** compute time exceeds budget:

1. **End-of-tick watchdog** (`kernel.py:420-442`): if `_final_compute_ms > min(hard_cap,
   avg*2.0)`, logs `"Tick N exceeded budget... Aborting next tick if sustained"`,
   `self._status.record_dropped_work(9999)`, and routes a `watchdog_trip` alert. **This fired
   dozens of times in both runs**, starting at **tick 321 in both runs** (i.e. after the existing
   300-tick `test_population_stability` window's last checkpoint — this is why that test has
   never caught anything here) and growing more frequent as the run progresses (world/entity/event
   volume grows — more quests resolved, `monster_horde` calamity spawns, more concurrent group
   activity).
2. **Mid-tick emergency throttle** (`kernel.py:574-601`): if elapsed time mid-resolution exceeds
   the hard cap, the Kernel **drops the remaining resolution-queue work items for that tick**
   (`logger.warning(f"...Dropping {N} items")`) and forces `RuntimeMode.DEGRADED` via
   `self._governor.force_mode(...)`.

Both paths are documented, intentional engine behavior — `docs/engine/kernel.md` §"Emergency
Throttling" (lines 66-70): *"If a tick exceeds 2x its average duration or the hard cap... 1.
Signal the Governor to transition to DEGRADED mode. 2. Drop remaining work items in the current
resolution queue."* — and `docs/engine/kernel.md` lines 100-126 / `docs/engine/known_limitations.md`
explicitly document that `DEGRADED` mode is **not** a complete determinism-proof state (canonical
hash is `"SKIPPED"` in `DEGRADED`; only the lightweight fingerprint, itself missing several state
domains, is emitted). **Critically, both throttle paths are gated behind `not self._audit_mode`**
(`kernel.py:423`, `kernel.py:578`) — they are unconditionally active in the standard (non-audit)
mode both `test_population_stability` and this investigation's harness use.

**Consequence**: when a tick's real wall-clock compute time exceeds budget (which happens
increasingly often after ~tick 300+ in this world, driven by growing entity/event/group volume,
independent of the RNG seed), some entities' resolution work is **silently dropped for that
tick** — they do not act, defend, flee, or otherwise get processed that tick. *Which* entities get
dropped depends on where in the sorted resolution queue the mid-tick elapsed-time check trips,
which depends on the actual wall-clock timing of that specific run (system load, scheduler
jitter, GC pauses) — not on the deterministic seed or RNG stream. This is the direct mechanical
explanation for why two back-to-back runs of the same seed and code diverge by 100+ ticks in
floor-violation onset and by more than 2× in the tick-1000 alive count. It is also consistent
with a documented, pre-existing parity-ledger observation
(`docs/parity_ledger/infrastructure.yaml` ~line 3245) that `GovernorModeChanged` "fires naturally
(63-73 occurrences)" through real `Kernel.tick_once()` loops — i.e. this world's late-game
governor engagement is not anomalous, it is the expected shape of sustained long-run load on this
architecture.

### Is the tick 982-1000 `entity_killed` COMBAT cluster the cause or a symptom?

**Symptom, not cause.** Both instrumented runs show the 60% floor already violated well before
tick 982 (tick 960 in Run 1, tick 860 in Run 2), and show broad **multi-faction** erosion
(`town_council`, `goblin_warband`, `wild_beast_pack`, `bandit_company`, `merchant_league` — not
just whichever faction the 6 reported `entity_killed` events involved) accelerating from roughly
tick 740-860 onward in both runs — a full 120-240+ ticks before the reported 982-1000 combat
cluster. The 6 late `entity_killed` events documented in the original calibration report are
consistent with being the **tail end** of an already-in-progress, broad erosion process (fewer
and fewer entities remain, so remaining deaths cluster later in wall-clock/tick terms simply
because there are fewer entities left to die and the world's `calamity_intensity`/`monster_horde`
threat pressure has had more ticks to accumulate — `docs/mechanics/05_world_evolution.md`
"Threat Evolution: Monsters in high-hazard regions evolve to higher Evolution Levels, becoming
deadlier"), not a discrete triggering event. This confirms and sharpens the ticket's own stated
suspicion ("checkpoint data shows erosion beginning by tick 900, earlier than those specific
worst-events entries suggest") — the true onset is earlier still (~740-860), and the shape/
magnitude of the acceleration is itself governed by the wall-clock-dependent throttle mechanism
in Root cause 3, not by a fixed combat-formula trigger.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §"Hazard Impacts" / "Native Endurance to a Region's
  Hazard Kind" (lines 55-93) — same authoritative law as the sibling ticket: the passive-drain
  formula, the `hazard_kind`/`hazard_immunities` exemption mechanism, and the explicit warning
  that the resolver default (`"PHYSICAL"`) grants no accidental immunity. Directly governs Root
  causes 1 and 2.
- `docs/mechanics/05_world_evolution.md` "Threat Evolution" (line 186) — monsters in high-hazard
  regions become deadlier over time; relevant context for why late-game combat lethality
  increases independent of any single triggering event.
- `docs/engine/kernel.md` §"Emergency Throttling" (lines 66-70) and §"State Hashing in Phase 7"
  (lines 100-126) — the authoritative, already-documented description of the `DEGRADED`-mode
  work-dropping behavior underlying Root cause 3. This is **not** a divergence from documented
  behavior; it is documented behavior whose interaction with this specific world's long-run
  compute growth has not previously been exercised (no existing test drives this world past tick
  300).
- `docs/mechanics/02_combat_laws.md` — read in full. No formula-level divergence found; the
  observed pattern (broad, accelerating, multi-faction losses, not a single-faction uniform
  wipeout) is consistent with ordinary combat resolution under increasing threat pressure, not a
  combat-law bug.
- `docs/mechanics/03_economic_laws.md` — read in full. No resource-conservation or starvation
  mechanic implicated; not relevant to this finding.

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml::WORLD-029` and `::WORLD-060` (both P0, status
  `verified`) — "Calamity aura and regional hazards apply local debuffs/drain" /  "Regional
  hazards drain HP/Readiness based on intensity." Same entries the sibling ticket flagged.
  `v2_evidence` still does not mention `moon_cult_ruins` or `generated_frontier_3_42`. **Needs
  updating** once the `moon_cave` hazard_kind fix lands, adding this module/world to the
  evidence trail (same update pattern as the sibling ticket's WORLD-029/WORLD-060 note).
- `docs/parity_ledger/infrastructure.yaml` (~line 3230-3277, `GovernorModeChanged` /
  `test_governor_mode_changed_fires_through_real_tick_once_loop`) — documents that
  `GovernorModeChanged` firing through real `tick_once()` loops (63-73 occurrences) is expected,
  already-verified behavior. **No update needed** — Root cause 3 does not contradict this entry;
  it is additional evidence for a scenario (a specific world's long-run compute growth) that
  entry's existing verification already covers structurally. Cited here for traceability, not
  because it needs to change.
- No P0 parity entry currently governs test-determinism guarantees for `Kernel.tick_once()`
  under sustained load — `docs/engine/deterministic_execution.md` (referenced by `kernel.md`
  line 125) is the relevant determinism contract but was not found to contain a parity-ledger
  entry ID; **flagged as a documentation gap**, not something this ticket should originate a fix
  for (see Anti-Drift Hazards).

## Prior Work

- `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md` — direct
  methodology precedent (instrumented per-checkpoint `alive_by_faction`/`dead_by_faction` drive)
  and the exact bug-class precedent for Root causes 1 and 2 (missing/mismatched `hazard_kind`,
  including the *same* unresolved `town_council`-at-`bandit_road` open design question — its Risk
  #2 applies verbatim here). Its Anti-Drift Hazards section explicitly warned this pattern would
  recur in any newly-anchored module carrying `hazard_level > 0` without a declared `hazard_kind`
  — `moon_cult_ruins` is exactly the case that warning anticipated.
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Finding 3/4 — the
  original precedent for this defect class, one level further back.
- `tests/unit/worldassembly/test_corpus_diversity.py` —
  `test_hazard_kind_matches_populating_faction_immunity` already exists as a regression guard for
  this exact defect class but is scoped to `HAZARD_KIND_MATCH_WORLDS = ["dungeon_crawl",
  "urban_political"]` only; `generated_frontier_3_42` is not covered. `test_population_stability`
  already includes `generated_frontier_3_42` in `POPULATION_STABILITY_WORLDS`, but only checks to
  tick 300 — insufficient to catch this ticket's finding, exactly as the ticket states.
- No prior ticket has touched `moon_cult_ruins.yaml`'s hazard fields, nor investigated
  `Kernel`'s tick-budget-governor behavior as a source of run-to-run population-outcome variance
  at long tick counts — this is a new finding, not previously documented anywhere in
  `docs/parity_ledger/`, `docs/audits/`, or `docs/plans/audit_fix_plan.md`'s existing P2-B entry
  (which is about spawn-cadence-vs-attrition-rate, a different mechanism — see Anti-Drift Hazards).

## Risks and Open Questions

1. **BLOCKING for test design — the extended-window regression guard's determinism is not
   guaranteed by content fixes alone.** Root cause 3 means that even after fixing the two
   confirmed content gaps, the exact population trajectory from tick ~700-1000 will still vary
   run-to-run depending on wall-clock system load (verified: two back-to-back runs on identical
   seed/code diverged by 100+ ticks in floor-violation onset and >2× in the tick-1000 endpoint).
   The ticket's AC requires a guard that "passes cleanly" — this investigation does **not** assume
   an answer for how the planner should reconcile a floor-style assertion with genuine run-to-run
   variance. Concrete options surfaced for the planner (not chosen here):
   (a) fix only the confirmed content gaps and accept the guard may need a wider or
   run-count-averaged tolerance rather than a tight per-tick assertion;
   (b) run the new extended-window test with `audit_mode=True`, which structurally disables both
   throttle paths (`kernel.py:423`, `kernel.py:578` are both gated `not self._audit_mode`) — but
   this is a **materially different code path**, not merely a deterministic replay of the same
   trajectory: with throttling disabled, strictly more entities get processed each tick than in a
   throttled run, which would very likely produce a *higher*, not merely more reproducible,
   population outcome. Choosing this changes what the test is actually verifying (best case,
   unthrottled population health) versus what the world experiences in a real/CI run (load-
   dependent, throttled).
   This is a genuine architectural fork in what "passing cleanly" should mean here, not a detail
   the investigation should resolve by default.
2. **Whether Root cause 2's `town_council`-at-`bandit_road` gap should be fixed here.** Same
   unresolved design question as the sibling ticket's Risk #2 (intentional "conflict pressure"
   flavor for a guard escort posted to a contested road, vs. a genuine content gap). Since the
   sibling ticket left this open without fixing it for `urban_political`'s identical case, fixing
   it only for `generated_frontier_3_42` here (without a documented decision either resolving or
   superseding that open question) would create an inconsistency between two worlds sharing the
   same content pattern. Recommend either resolving the question once (applicable to both
   worlds) or deferring both consistently — not deciding ad hoc per-ticket.
3. **`hero_guild_routing`** and no other corpus world compose `moon_cult_ruins` (confirmed via
   `grep -rl moon_cult_ruins data/worlds/*/world.yaml` equivalent — only `generated_frontier_3_42`
   references it in its `module_refs`), so a `moon_cult_ruins.yaml` hazard_kind fix has no
   cross-world blast radius to re-verify, unlike the sibling ticket's `ruins_mystery_quest`/
   `scalable_bandit_camp` fixes.
4. Root cause 3's tick-budget-throttle behavior is a **corpus-wide** engine characteristic, not
   specific to this world — but this is the **first** existing/planned test to drive any corpus
   world past tick 400-500 in a hard-assertion (non-advisory) context, so it is the first place
   this determinism gap becomes test-visible. Whether other long-run calibration tiers (1000t/
   2000t anchors elsewhere in `docs/simulation_quality/eval_matrix_results.md`) are silently
   exposed to the same run-to-run variance in their `quality_report.json` outputs is out of this
   ticket's scope to investigate, but is flagged here so a future ticket does not have to
   rediscover the mechanism from scratch.
5. The exact attribution of `town_council`'s later (tick 700+) losses between residual hazard
   drain (Root cause 2, only 2 of 14 entities exposed), ordinary combat, and any second-order
   effect of dropped resolution work (Root cause 3, e.g. an entity that misses several
   consecutive flee/heal opportunities) was not fully decomposed — the evidence supports all
   three contributing but does not isolate their individual share. Not resolved here; flagged so
   the planner does not assume a single dominant mechanism for `town_council` specifically.

## Anti-Drift Hazards

- Do not touch `src/world/environment.py::calculate_hazard_drain` or
  `src/worldassembly/resolver.py:798`'s default — both are working as documented and covered by
  existing unit tests (same ruling as the sibling ticket).
- **Do not touch `src/engine/kernel.py`'s tick-budget watchdog or emergency-throttle logic
  (`kernel.py:420-442`, `kernel.py:574-601`), the `ResourceGovernor`, or any `DEGRADED`-mode
  behavior as part of this ticket's fix.** This is documented, intentional, corpus-wide engine
  behavior (`docs/engine/kernel.md` §"Emergency Throttling") governing real hardware-class
  performance scaling (`docs/engine/performance_contract.md` §7 "Adaptive Phase Budget
  Governor") — changing it to "fix" this ticket's determinism concern would be a major,
  out-of-scope architecture change with corpus-wide blast radius, not a `generated_frontier_3_42`
  content fix. If the planner decides `audit_mode=True` is the right lever for the new test
  (Risk 1b above), that is a **test-harness** choice (how the guard drives the Kernel), not an
  engine-code change.
- `docs/plans/audit_fix_plan.md`'s existing **P2-B** ("Late-run attrition exceeds spawn rate")
  and `docs/audits/D06_longrun_health.md`'s **F5** finding are a **different** mechanism
  (`SpawnService` cadence vs. attrition rate, ticket `TCK-20260627-P2B-SPAWN-CADENCE`) — do not
  conflate this ticket's findings with that one or assume they share a fix. This investigation
  found no evidence that `SpawnService`'s cadence is implicated here (no new entities of the
  *original* factions were observed spawning in either run — only the `monster_horde` calamity/
  trauma spawn, a distinct mechanism); flagging explicitly so the planner does not merge these.
- Any fix to `moon_cult_ruins.yaml` requires a **recompile** of `generated_frontier_3_42` (the
  only world composing it) to pick up the change, per the established pattern.
- Adding `generated_frontier_3_42` to `HAZARD_KIND_MATCH_WORLDS` in
  `test_corpus_diversity.py` (New Test #2 in test_plan.md) must not be done until the
  `moon_cave`/`arcane_circle` fix (and, if the planner decides to fix it, the `bandit_road`/
  `town_council` gap) actually lands and is re-verified — do not add the world to that list
  pre-emptively with the gap still present, which would make that test fail immediately rather
  than guard against regression.
- Do not assume the `moon_cave` fix alone will make a tick-1000 regression guard pass reliably —
  per Risk 1, it addresses only ~4 of the 44 starting entities and does not touch the dominant
  tick-700-1000 erosion mechanism.
