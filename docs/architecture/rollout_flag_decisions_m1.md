---
status: active
layer: engine
authority: P1
audience: agent
tags: [feature-flags, architecture]
---

# Rollout Flag Decisions — RPG Design Roadmap M1

**Source ticket**: `TCK-20260824-ROLLOUT-FLAG-DECISIONS`, the first ticket implemented in the
`m1-quick-wins` batch (`docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`, idea 9), run
first per that epic's own explicit acceptance signal: "Idea 9's flag-governance ticket lands
before any other M1 ticket that adds new flag-gated behavior."

This is the durable, discoverable decision artifact `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own
Scope calls for — the full evidence trail lives in
`staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md`; this document states the
decisions and their rationale for future reference, including for the 38 more M2+ flagged ideas
this precedent governs.

## The 8 Flags Reviewed

| Flag | Verdict | Rationale |
|---|---|---|
| `ENABLE_BELIEF_ASSIMILATION` | **Flipped ON** | Real, live corpus-profile evidence — already `ON` in both `config/simulation_quality/profiles/sandbox_world.yaml` and `urban_political.yaml`. `docs/guidelines/intentional_divergences.md` DEV-003. |
| `ENABLE_SOCIAL_COOPERATION` | **Flipped ON** | Real, live corpus-profile evidence — already `ON` in `urban_political.yaml`. DEV-003. |
| `ENABLE_GUILD_QUEST_GENERATION` | **Kept OFF** | Already had a deliberate, documented DEV-002-policy rationale in `feature_flags.py`'s own comment before this ticket — formalized, not re-litigated. |
| `ENABLE_COMBAT_ENGAGEMENT` | **Kept OFF, deferred (real trial evidence now on file)** | `TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION` ran a real 4-leg corpus trial — no suppression regression, the TCK-20260809 `u.merge(...)` fix holds, but zero shipped profiles turn this flag on and real combat-activity signal stayed thin. See "ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result" below. |
| `ENABLE_SELF_MODEL_COGNITION` | **Kept OFF, deferred (real trial evidence now on file)** | `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION` ran 2 fresh corpus-profile trials on top of 2 prior real trials already on file (a shipped-ON Unit-tier world, `INFRA-266`'s real-world generalization split verdict) — still no shipped archetype-world default profile, and the fresh trial surfaced a real, undisclosed anchor drift requiring its own follow-up. See "ENABLE_SELF_MODEL_COGNITION — Validation Trial Result" below. |
| `ENABLE_WORLD_EMERGENCE` | **Kept OFF, deferred (real trial evidence now on file)** | `TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION` ran a real 4-leg corpus trial — no suppression regression, real phase execution/telemetry/entity-signal exposure confirmed, but zero shipped profiles turn this flag on and neither trial world produced a single `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` event, leaving quest-registry growth specifically unconfirmed. See "ENABLE_WORLD_EMERGENCE — Validation Trial Result" below. |
| `ENABLE_PROGRESSION_EVOLUTION` | **Kept OFF, deferred (crash prerequisite now fixed; reward-ledger gap remains)** | `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION` ran a real 4-leg corpus trial — both ON legs deterministically crashed the real `Kernel` pipeline (`CanonicalStateHasher.get_hash()` cannot serialize the raw `ProgressionDecisionResult` the phase stores in `property_updates`), a stronger "keep OFF" finding than any of the 3 sibling flags produced, on top of the already-predicted reward-ledger producer gap. `TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH` has since fixed the crash (verified via a real flag-ON 300-tick trial, exit 0, no `TypeError`) — that blocking prerequisite is resolved, but the flag's default stays OFF pending the separate reward-ledger producer gap (DEV-004). See "ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result" below. |
| `ENABLE_INFORMATION_INTENT_EXECUTION` | **Kept OFF, deferred (real trial evidence now on file)** | `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION` ran a real single-variable OFF-vs-ON corpus trial against `urban_political` with `ENABLE_BELIEF_ASSIMILATION` held ON in both legs — no suppression regression, the distinction from `ENABLE_BELIEF_ASSIMILATION` (production vs execution of Branch B's `ActionIntent`) confirmed by direct code read and by trial data, but zero shipped profiles turn this flag on and Branch B did not route a query in either leg of this trial's corpus/seed/window, matching `INFRA-270`'s and `INFRA-266`'s prior findings. See "ENABLE_INFORMATION_INTENT_EXECUTION — Validation Trial Result" below. |

## ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result (TCK-20260826)

`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION` is the follow-up this table's own
`ENABLE_COMBAT_ENGAGEMENT` row named. Its job was to produce the standing evidence this row's
prior "Kept OFF, deferred" verdict was missing — a real corpus-profile trial, not another one-off
synthetic test. Full raw tally:
`staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md` (moved to
`stored_artifacts/` at ticket close).

**Worlds tested**: `dungeon_crawl` (32 entities, `monster_only_gauntlet` archetype, `COMBAT: 2.0`
pillar weight — the same world/seed TCK-20260809 used to find and fix the original bug) and
`wilderness_survival` (11 entities, same archetype, `--profile default` since it has no dedicated
scoring profile) — both seed 42, 2000 ticks, run OFF then ON. Both worlds confirmed to load their
real compiled `data/worlds/{name}/resolved/world.resolved.yaml` spec (via each run's own tick-0
`fingerprint.entity_count`: 32 for `dungeon_crawl`, 11 for `wilderness_survival`), not the generic
hero+goblins fallback — resolving investigation.md's open question about which code path fires.

**Commands** (mirroring TCK-20260809's own A/B method):
```
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_OFF
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_ON

python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_OFF
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_ON
```

**Evidence tally** (5 signals x 4 legs):

| Signal | dungeon_crawl OFF | dungeon_crawl ON | wilderness_survival OFF | wilderness_survival ON |
|---|---|---|---|---|
| `combat_engagement_started` | 1 | 0 | 0 | 0 |
| `combat_engagement_ended` | 10 | 10 | 10 | 10 |
| `combat_resolved` | 0 | 0 | 0 | 0 |
| `combat_damage` | 0 | 0 | 0 | 0 |
| `entity_killed` | 0 | 0 | 0 | 0 |
| `run_combat_engagement` (summed) | 0 | 1811 | 0 | 1937 |
| `skip_combat_engagement` (summed) | 1785 | 0 | 1926 | 0 |
| Phase skip-rate | 100% (flag OFF) | 0% | 100% (flag OFF) | 0% |
| `quality_report.json` COMBAT pillar `event_count` | 1 | 0 | 0 | 0 |

**No-suppression check: passes in both worlds.** `combat_engagement_ended` — the one signal with
real, repeatable volume — is identical between ON and OFF in both worlds (10 == 10 in each pair),
not collapsed toward zero on the ON leg. `run_combat_engagement`/`skip_combat_engagement` confirm
`CombatEngagementPhase` runs on effectively every eligible tick when ON (0% skip rate in both ON
legs), ruling out the "phase silently starved by `PhaseDependencyGraph.should_run_phase()`"
false-negative risk. This is the opposite of TCK-20260809's own documented pre-fix signature (a
deterministic 100%->0% collapse across all 5 event types on the ON leg while OFF stayed nonzero).
**The `u.merge(...)` fix in `src/engine/pipeline.py:276` continues to hold** under this real
2000-tick, two-world trial. The 1-vs-0 difference on `combat_engagement_started` in `dungeon_crawl`
reads as ordinary run-to-run variance at n=1, not a suppression pattern — a real suppression bug
collapses all 5 signal types simultaneously, not one low-volume signal while its higher-volume
sibling (`ended`) stays exactly matched.

**The honest gap: `combat_resolved`/`combat_damage`/`entity_killed` are 0 in all 4 legs**,
including both OFF baselines — thinner than TCK-20260809's own OFF baseline on the same
`dungeon_crawl_seed42` world/seed (`damage=1`, `resolved=1`, `killed=1`, thin but present). Per
the near-zero-baseline caveat this ticket's own plan carried forward, this is disclosed rather
than smoothed over: neither world's OFF baseline in this trial produced a lethal/damage-bearing
combat interaction within 2000 ticks, so the trial cannot independently confirm the
ATTACK/damage-resolution path stays fully active beyond what `combat_engagement_ended=10`
(present and matched in every leg) already shows.

**Recommendation: Keep OFF, deferred.** The trial meets DEV-003's evidentiary bar for
"no suppression regression" — real, repeatable, confirmed. It does not meet the bar for "flip ON"
per this table's own precedent ("flip ON requires real, standing evidence the system already runs
safely in production... a one-off validated fix or trial is necessary but not sufficient on its
own"): `ENABLE_COMBAT_ENGAGEMENT` still has zero shipped `config/simulation_quality/profiles/*.yaml`
turning it on, and this trial's own thin real-combat-activity signal (zero damage/kill events in
either baseline) is weaker evidence than the already-flipped `ENABLE_BELIEF_ASSIMILATION`/
`ENABLE_SOCIAL_COOPERATION` flags had (standing production profile usage). No new
`docs/guidelines/intentional_divergences.md` entry is added — the flag's behavior versus the
Mechanics Bible is unchanged either way. If a future ticket wants to re-open this: either (a) a
shipped SimQ corpus profile begins using `ENABLE_COMBAT_ENGAGEMENT=ON` in production, matching the
DEV-003 precedent directly, or (b) a fresh trial on a higher-`COMBAT`-weight/longer-tick/different-seed
corpus world produces nonzero `combat_damage`/`entity_killed` in its OFF baseline, giving a
stronger real-activity floor to compare against. No concrete next-step ticket is named — this
result does not recommend a flip.

## ENABLE_SELF_MODEL_COGNITION — Validation Trial Result (TCK-20260826)

`TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION` is the follow-up this table's own
`ENABLE_SELF_MODEL_COGNITION` row named. Unlike `ENABLE_COMBAT_ENGAGEMENT` above, real trial
evidence already existed before this ticket: `unit_selfmodel_pilot` ships the flag ON by default
(a dedicated 16-entity Unit-tier isolation world, `STRAT-245`), and `INFRA-266`
(`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) ran a real 3-seed, 200-tick trial against
`urban_political`'s actual compiled state with a split verdict (materialization generalizes B→S;
query-routing did not reach a scoreable outcome at that time — subsequently fixed by `INFRA-267`).
Two permanent grade-anchor probe profiles formalize this: `urban_political_selfmodel_probe.yaml`
(materialization-only) and `urban_political_selfmodel_execution_probe.yaml` (full-stack, adds
`ENABLE_BELIEF_ASSIMILATION` + `ENABLE_INFORMATION_INTENT_EXECUTION`). This ticket's job was to
run a genuinely fresh trial on top of that prior evidence, not just cite it. Full raw tally:
`staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md` (moved to
`stored_artifacts/` at ticket close).

**World tested**: `urban_political` (real compiled state, `entities=10`, confirmed via each run's
successful load — `--name urban_political` failing to resolve raises `FileNotFoundError` rather
than silently falling back), seed 42, 200 ticks, both probe profiles run ON.

**Commands**:
```
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_probe \
  --output data/calibration/urban_political_selfmodel_probe_seed42_200t
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
```

**Evidence tally**: `self_model_updated` fired 5454 times per run (INFRA-266's historical figure
at this same world/seed/tick-count was ~5610-5611, within ~2.8% — same order of magnitude,
confirming the unconditional per-alive-active-entity firing mechanism, no collapse/suppression).
`tests/simulation_quality/test_grade_regression.py -k selfmodel -q`, re-run un-skipped now that
fresh reports exist: **2 failed, 4 skipped, 83 deselected** — both target grade-anchor tests
transitioned from `skipped` to actually asserting, but did **not** cleanly pass (see Honest Gap
below). The other 4 `selfmodel`-matched tests remain skipped (require `unit_selfmodel_pilot`'s own
separate calibration reports, out of this ticket's scope to regenerate).

**Honest gap (updated — see follow-up below): `INFORMATION` and `SOCIAL` drifted from their
committed `grade_anchors.json` values on both probe run keys, with no existing `known ceiling`
classification covering either pillar.** `urban_political_selfmodel_probe_seed42_200t`'s
`INFORMATION` anchor was `C/0.0`; the fresh run measured `B/0.2` (`event_count=1`, not `0`). Traced
to source: both legs' single `belief_assimilated`/`belief_updated` event pair (subject
`bandit_road_danger`, actor 22, tick 1) comes from `SelfModelUpdatePhase.run()`'s own Step 1
knowledge-assimilation (`self_model_phase.py:103-141`, via `KnowledgeModelService.assimilate()`
against a seeded `pending_self_model_information_events` entry) — gated only by
`ENABLE_SELF_MODEL_COGNITION`, not `ENABLE_BELIEF_ASSIMILATION`. It fired identically in both legs,
so this is reproducible, not run-to-run noise.
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` subsequently confirmed, via `git
log`/`git blame` on `self_model_phase.py`, that this Knowledge Assimilation step has never, in its
entire history, referenced `ENABLE_BELIEF_ASSIMILATION` (2 total commits, neither touching this
logic after original authorship) — the original anchor's assumption that this step was gated by
`ENABLE_BELIEF_ASSIMILATION` was simply incorrect from the start, not a later regression or
code-path change. `INFORMATION` has accordingly been re-anchored to `B/0.2`/`event_count=1` for
`urban_political_selfmodel_probe_seed42_200t` (the `_execution_probe` run key's `INFORMATION`
anchor was already correct at `B/0.2` and is unchanged). `SOCIAL` also drifted beyond score
tolerance on both run keys (13.35 actual vs 17.895/16.815 anchored at trial time).
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` has since traced `SOCIAL`'s root
cause to `CooperationPhase`'s cooperation-offer retry-without-cooldown gap
(`src/domains/cooperation/phase.py`/`services.py`) — the same mechanism separately ticketed as
`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` for `highland_traverse_seed42_200t`, now
known to also affect both `urban_political_selfmodel*_probe` run keys. This is **not** related to
`SelfModelUpdatePhase`/`ENABLE_SELF_MODEL_COGNITION` at all — a structurally independent mechanism
from `INFORMATION`'s drift. `SOCIAL` has deliberately **not** been re-anchored (the coordinator's
Option A decision, recorded in
`staging_artifacts/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION/plan.md`'s
Unresolved Questions section, moved to `stored_artifacts/` at that ticket's close), pending either
the cooperation-domain retry-cooldown fix landing and `SOCIAL` being re-measured post-fix, or a
future deliberate, disclosed pre-fix re-anchor decision — it is root-caused, not fixed. This does
not itself change the recommendation below, since the DEV-003 bar was already unmet independent of
anchor cleanliness. `COMBAT`/`ECONOMY`/`PROGRESSION` also drifted on the execution-probe run key,
but each carries an existing, pre-existing `known tick_budget` ceiling classification from
`tools/simq_ceiling.py` (200-tick-window threshold noise, unrelated to this flag) — not a new
finding.

**`ENABLE_ADVENTURE_ROUTING` combination — resolved, static analysis only.** `grep -rn
"ENABLE_ADVENTURE_ROUTING" src/ tools/` returns zero live `is_enabled(...)`/`get_flag_mode(...)`/
`feature_flag="ENABLE_ADVENTURE_ROUTING"` call sites outside the flag's own registration
(`feature_flags.py:25`). `AdventureDecisionPhase` — the phase that used to gate via
`run_phase(..., feature_flag="ENABLE_ADVENTURE_ROUTING")` — was deleted in full by
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`; its replacement, `AdventureGoalScorer.score()`,
runs unconditionally every tick for every eligible entity, not gated behind any flag
(`docs/parity_ledger/strategic_cognition.yaml STRAT-252`, `docs/engine/known_limitations.md`
Section 1.5). No runtime path exists for `ENABLE_ADVENTURE_ROUTING`'s value to interact with
`ENABLE_SELF_MODEL_COGNITION`-gated code, so no empirical combination trial was run — a trial
cannot produce a different answer than the static analysis already gives. A new durable regression
guard, `tests/architecture/test_adventure_routing_flag_inert.py::
test_enable_adventure_routing_has_no_live_gating_call_site`, was added so a future re-wiring of
the flag fails this test loudly rather than letting `known_limitations.md`'s claim go stale.

**Recommendation: Keep OFF, deferred.** Three independent real trials are now on file
(shipped-ON Unit-tier world, `INFRA-266`'s real-world generalization split verdict, and this
ticket's own 2 fresh confirming probe runs), but `unit_selfmodel_pilot` remains the sole flag-ON
shipped profile — a dedicated 16-entity Unit-tier isolation world, not a real archetype world like
`urban_political`/`sandbox_world`. The DEV-003 "shipped production profile" bar is still unmet, the
same class of outcome as `ENABLE_COMBAT_ENGAGEMENT` above. No new
`docs/guidelines/intentional_divergences.md` entry is added — the flag's behavior versus the
Mechanics Bible is unchanged either way. If a future ticket wants to re-open this: a shipped SimQ
corpus profile begins using `ENABLE_SELF_MODEL_COGNITION=ON` in production, matching the DEV-003
precedent directly. Separately, the fresh trial's `INFORMATION`/`SOCIAL` anchor drift (Honest Gap
above) was a real, disclosed finding needing its own follow-up ticket before these two grade
anchors could be trusted as regression guards again. That follow-up,
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`, has now run: `INFORMATION` is
resolved (re-anchored to `B/0.2`/`event_count=1` for `urban_political_selfmodel_probe_seed42_200t`,
confirmed as the original anchor's own incorrect assumption rather than a regression). `SOCIAL`
remains open — root-caused to `CooperationPhase`'s retry-without-cooldown gap
(`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`) and disclosed, but deliberately not yet
re-anchored, pending that cooperation-domain fix landing and a post-fix re-measurement.

## ENABLE_WORLD_EMERGENCE — Validation Trial Result (TCK-20260826)

`TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION` is the follow-up this table's own
`ENABLE_WORLD_EMERGENCE` row named. Unlike either sibling flag above, `ENABLE_WORLD_EMERGENCE` had
**zero** prior real-world evidence of any kind before this ticket — no shipped-ON profile, no bug-
fix history, no prior generalization trial. This ticket's own trial is that flag's first and only
standing real-corpus evidence. Full raw tally:
`staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` (moved to
`stored_artifacts/` at ticket close).

**Worlds tested**: `dungeon_crawl` (32 entities, `monster_only_gauntlet` archetype, seed 42, 2000
ticks) and `resource_dense_basin` (23 entities, `civilian_settlement` archetype, highest shipped
`resource_density` of any world at 2.3333, seed 42, 1000 ticks, `--profile default` since it has
no dedicated scoring profile — extended beyond its shipped 200-tick run_keys to reduce
near-zero-baseline risk), both run OFF then ON. Both worlds confirmed to load their real compiled
`data/worlds/{name}/resolved/world.resolved.yaml` spec: `dungeon_crawl`'s tick-0
`entity_count=32` (grepped directly from each run's own `chunk_0000.json`) matches
`corpus_registry.yaml`'s documented scale exactly; `resource_dense_basin`'s successful exit-0 load
against `--name resource_dense_basin` is itself sufficient proof per `calibrate_simq.py`'s own
`_load_world_state()`, which raises `FileNotFoundError` for any unresolvable name rather than
silently falling back to the generic hero+goblins world.

**Commands**:
```
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_OFF
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_ON

python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_OFF
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_ON
```

**Evidence tally** (5 signal groups x 4 legs — using `metric_counters`/`quest_registry_add`/entity
`property_updates`, never `world_emergence_event` counts in `simulation_events.jsonl`, which
investigation.md confirmed is produced by other pipeline phases via `world_events_add` and is not
gated by this flag at all):

| Signal | dungeon_crawl OFF | dungeon_crawl ON | resource_dense_basin OFF | resource_dense_basin ON |
|---|---|---|---|---|
| `run_world_emergence` / `skip_world_emergence` (summed) | skip=1836 | run=1837 (100%) | skip=931 | run=908 (100%) |
| `world_emergence_ms` / `aggregates_generated` | absent | 883.31ms / 89 | absent | 431.83ms / 182 |
| Distinct `quest_registry_add` ids | 0 | 0 | 0 | 0 |
| `exposed_world_signals` / `force_route_reevaluation` property-update count | 0 / 0 | 33869 / 33869 | 0 / 0 | 18518 / 6563 |
| `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` `WorldEvent` count (OFF-baseline activity) | 0 | 0 | 0 | 0 |

**No-suppression check: passes in both worlds, on both halves.** Structurally, the 100%/0%
run/skip split confirms `WorldEmergencePhase` runs on effectively every eligible tick once ON, not
starved by `PhaseDependencyGraph.should_run_phase()`. Empirically, no domain-independent signal
collapsed toward zero on either ON leg relative to OFF in the same world: `dungeon_crawl`'s total
`simulation_events.jsonl` count shifted 22395→20261 (SOCIAL-domain contract/cooperation events
moved ±13%, all staying in the thousands — ordinary cascading divergence from entities reacting to
`force_route_reevaluation`, not suppression); `resource_dense_basin`'s total count *increased*
3707→5468, with every changed domain-independent signal (combat, cooperation, contracts, XP, gold)
moving up, including new activity (`entity_killed` 0→1) rather than collapsing. Confirms
`WorldEmergencePhase.execute()`'s `dataclasses.replace(update, ...)` pattern (not a fresh
`StateUpdate()`) really does carry forward prior phases' work in a real run, not just by static
code reading.

**Honest gap: quest-registry growth (the durable `quest_registry_add` signal) is untestable from
this trial, not just zero.** Both trial worlds were chosen specifically for their expected
event-producing profile per the corpus registry's own archetype/density metadata, but neither
produced a single `RESOURCE_DEPLETED`, `ENTITY_DEATH`, or `CAMP_RAID` `WorldEvent` in any leg — the
only `world_events_add` category observed anywhere in this trial was `COMBAT_LOSS` (1-3
occurrences per leg), which `QuestOpportunityGenerator` does not read. This means the `0`
quest-registry growth on every leg (including both ON legs) is neither evidence of suppression nor
evidence the mechanism is broken (its own parity-ledger tests, `WORLD-098`/`WORLD-099`/`WORLD-102`,
independently cover it and passed in this ticket's own regression run) — it is evidence that this
trial's two worlds, at these seeds/tick-counts, never crossed the precondition this specific
pathway needs to fire. Disclosed as a genuine limitation, not fixed or compensated for with a third
trial world inline, per Scope Guards.

**`ENABLE_WORLD_CAPABILITY_LAYER` combination — resolved, static analysis only, zero live gating
call site anywhere.** `grep -rn "ENABLE_WORLD_CAPABILITY_LAYER" src/ tools/ tests/ config/` returns
only its own registration (`feature_flags.py:14`, default OFF), a test-scaffold `pressure_signals`
dict entry in `src/testing/scenario_runner.py:101` that maps to nothing (no phase names this flag
in a `run_phase(..., feature_flag=...)` call), and two known-flag allowlist references
(`calibrate_simq.py`, `test_scenario_feature_flag_defaults.py`) — no live gating call site. A
separate grep for a `WorldCapabilityLayer` class/module anywhere in `src/` returns zero matches —
no such phase or service exists in the codebase at all, a stronger inertness finding than
`ENABLE_ADVENTURE_ROUTING`'s own case (which used to gate a real, now-deleted phase). Combining it
`ON` with `ENABLE_WORLD_EMERGENCE=ON` is structurally impossible to produce any interaction — there
is no runtime path for its value to reach any code. No empirical combination trial was run. A new
durable regression guard, `tests/architecture/test_world_capability_layer_flag_inert.py::
test_enable_world_capability_layer_has_no_live_gating_call_site`, was added mirroring the sibling
`ENABLE_ADVENTURE_ROUTING` guard exactly — `2 passed` (both the new guard and the pre-existing
sibling guard) when run this session.

**Recommendation: Keep OFF, deferred.** `grep -rl "ENABLE_WORLD_EMERGENCE"
config/simulation_quality/profiles/` returns nothing — zero shipped production profiles turn this
flag on today, the same gap that kept both sibling flags at "keep OFF, deferred" despite each
having its own clean trial. Per "The Precedent This Sets" below: this trial is a real, necessary
"no suppression regression" confirmation, but is not on its own sufficient to meet the "flip ON"
bar (standing shipped-profile production evidence). No new
`docs/guidelines/intentional_divergences.md` entry is added — the flag's behavior versus the
Mechanics Bible is unchanged either way. If a future ticket wants to re-open this: either (a) a
shipped SimQ corpus profile begins using `ENABLE_WORLD_EMERGENCE=ON` in production, matching the
DEV-003 precedent directly, or (b) a fresh trial on a world/seed/tick-count combination
independently confirmed to produce real `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` baseline
activity closes the Honest Gap above.

## ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result (TCK-20260826)

`TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION` is the follow-up this table's own
`ENABLE_PROGRESSION_EVOLUTION` row named. Like `ENABLE_WORLD_EMERGENCE` above, this flag had zero
prior real-world evidence before this ticket. Unlike any of the 3 prior siblings, this ticket's
trial did **not** produce a clean pass — it surfaced a real, deterministic pipeline crash. Full
raw tally: `staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md`
(moved to `stored_artifacts/` at ticket close).

**Test coverage depth assessed first (per this ticket's own Scope, ahead of trusting the
trial)**: domain-logic coverage is deep — 10 dedicated `test_phase6_*.py` files exercise every
constituent service (`possession.py`/`gaps.py`/`interpretation.py`/`generator.py`/`selector.py`/
`resolver.py`) individually and through 7 integrated scenarios — but every one of them calls
`ProgressionConversionPhase.execute()` directly, bypassing `src/engine/pipeline.py`'s flag gate
and `Kernel`'s persistence phase entirely. Pipeline-wiring coverage is thin: only 2 files
reference the flag by name, and the one real-kernel-loop test
(`test_allocate_ap_dormancy.py`) only proves the OFF state over 150 ticks, never toggling ON. This
gap in coverage is precisely why the crash below went undetected until this ticket's real corpus
trial.

**Worlds tested**: `dungeon_crawl` (32 entities, `monster_only_gauntlet` archetype, seed 42, 2000
ticks requested) and `frontier_extended` (59 entities, `civilian_settlement` archetype, seed 42,
1000 ticks requested, using its own dedicated scoring profile — `calibrate_simq.py`'s
`_resolve_profile()` auto-resolves to it since the profile file exists, no `--profile default`
needed here unlike `WORLD_EMERGENCE`'s `resource_dense_basin` leg). Both worlds confirmed to load
their real compiled world spec (`dungeon_crawl`'s tick-0 `entity_count=32` and `state_hash`
identical across OFF/ON; `frontier_extended` OFF's tick-0 `entity_count=59`; `frontier_extended`
ON confirmed indirectly via 1 real tick of faction-named `diplomatic_transition` events before it
crashed, since `_load_world_state()` raises rather than silently falling back).

**Commands**:
```
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_OFF
ENABLE_PROGRESSION_EVOLUTION=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_ON

python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_OFF
ENABLE_PROGRESSION_EVOLUTION=ON python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_ON
```

**Headline finding: both ON legs deterministically crash the real pipeline.** `dungeon_crawl` ON
crashed at loop iteration ~120 of 2000 requested; `frontier_extended` ON crashed at tick 1 of 1000
requested (its `civilian_settlement` archetype produces a combat/attribute-dirty entity almost
immediately). Both crash with the identical traceback:
```
File "src/engine/kernel.py", line 1162, in _phase_persistence
    tick_hash = CanonicalStateHasher.get_hash(self._state)
File "src/engine/checkpoint.py", line 60, in to_canonical_json
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
TypeError: Object of type ProgressionDecisionResult is not JSON serializable
```
Root cause: `ProgressionConversionPhase.execute()` (`src/domains/progression/phase.py:80`) stores
the raw `ProgressionDecisionResult` dataclass (already documented as a "debug trace property" in
`docs/simulation/domains/progression_contract.md:62`) directly into
`property_updates["last_progression_decision"]`. The next tick's `_phase_persistence()` calls
`CanonicalStateHasher.get_hash()` whenever `replay_richness == "FULL"` (the policy
`calibrate_simq.py`'s `PROD_SMALL` profile runs under), which recursively JSON-serializes the
entire `AuthoritativeState` with no `default=` handler for arbitrary dataclasses. Reproduced 4
independent times (2x `dungeon_crawl` ON via `calibrate_simq.py`, 1x `frontier_extended` ON via
`calibrate_simq.py`, 1x a read-only diagnostic replay of the same `Kernel`/world-loading setup
used to sample the decision distribution below) — not a fluke.

**Evidence tally**:

| Signal | dungeon_crawl OFF (2000t, full) | dungeon_crawl ON (crashed ~t120) | frontier_extended OFF (1000t, full) | frontier_extended ON (crashed t1) |
|---|---|---|---|---|
| Completed ticks | 2000 | ~120 | 1000 | 1 |
| `item_equipped`/`item_unequipped`/`equipment_durability_changed`/`progression_conversion_applied` events | 0 | 0 | 0 | 0 |
| `last_progression_decision.selected` kind distribution (32/32 `dungeon_crawl` entities sampled via diagnostic replay at the crash point) | n/a | 100% `SAVE_FOR_LATER` | not sampled | not sampled (crashed tick 1) |
| Process exit code | 0 | 1 (crash) | 0 | 1 (crash) |

**Signal 3 — 100% `SAVE_FOR_LATER` convergence, confirmed directly.** All 32 `dungeon_crawl`
entities' stored decision at the crash tick selected only `SAVE_FOR_LATER`, with the identical
reason string `"Do nothing, keep gold and resources for later."` — exactly the outcome
investigation.md predicted from the reward-ledger producer gap (see Honest Gap below).

**No-suppression check: inconclusive at the intended tick budget, superseded by the crash.**
`progression_conversion`'s `PhaseMetadata` is dirty-set-gated (`input_domains={"attributes",
"combat"}`), not `must_run_every_tick=True` like `world_emergence`/`self_model` — so its
`skip_progression_conversion` counter cannot on its own distinguish "flag OFF" from "flag ON, no
dirty entity this tick," unlike the clean 100%/0% splits the 3 sibling trials found for their own
flags. The diagnostic replay resolves this: the phase did activate and write real decisions once a
dirty tick occurred, confirming the flag does gate live execution (no silent starvation) — but a
same-world OFF-vs-ON event-count comparison at the full 2000/1000-tick budget (the method all 3
sibling trials used) is not possible, since both ON legs terminate far short of it. Within the
ticks that did complete before each crash, no other domain's signal collapsed (`dungeon_crawl`
ON's partial 116-line event log shows ordinary cooperation/contract/diplomatic activity right up
to the crash tick). This is a materially more severe failure mode than the suppression class the
sibling checks are designed to catch: a hard process crash halting every domain simultaneously,
not a silent per-domain signal collapse.

**Honest Gap — two separate, disclosed gaps, not conflated.** (1) The reward-ledger producer gap,
predicted by investigation.md and confirmed directly by Signal 3: `RewardLedgerService` has zero
live callers anywhere in `src/`, so `ledger.entries` is always empty and
`ConversionOptionGenerator` only ever emits `SAVE_FOR_LATER`. Per the ticket's own framing, this
means wiring is safe with respect to option-generation logic (the phase falls back correctly
rather than misbehaving on empty input) but behavioral safety under real reward flow remains
genuinely untested — not a blanket "no risk observed." (2) The canonical-hashing crash, a new
finding this trial surfaced (investigation.md had flagged the raw-dataclass storage as an
architecture smell adjacent to the Durable State Rule, but not that it deterministically crashes
`Kernel` persistence). This is disclosed here, not fixed — `src/domains/progression/phase.py` was
not touched by this ticket, per its Scope Guards. A follow-up ticket to make
`last_progression_decision` a JSON-serializable typed structure (or strip it before persistence,
matching `docs/engine/state_update_compaction.md`'s existing precedent for stripping cosmetic
debug properties) is a concrete, named blocking prerequisite for any future flip-ON decision —
stronger and more actionable than the reward-ledger gap alone.

**Recommendation: Keep OFF, deferred — a stronger "keep OFF" signal than any of the 3 prior
sibling flags.** `grep -rl "ENABLE_PROGRESSION_EVOLUTION" config/simulation_quality/profiles/`
returns nothing — zero shipped production profiles turn this flag on today, the same gap the 3
sibling flags share, but this flag does not even clear the lower "no suppression regression, real
execution confirmed" bar those trials met: it crashes the real pipeline in both worlds tested. No
new `docs/guidelines/intentional_divergences.md` entry is added — a "keep OFF, deferred" outcome
does not create a divergence from the Mechanics Bible, and no chapter governs this Phase-6/Phase-
10-era subsystem regardless. Re-opening this requires first (a) fixing the JSON-serialization
crash disclosed above, and separately (b) wiring a real reward-ledger producer (or accepting that
decision-logic safety under real reward flow stays untested indefinitely) — both concrete, named
prerequisites, not "someday" items.

**Post-fix status update (TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH,
2026-08-30).** Prerequisite (a) above is now resolved: `ProgressionConversionPhase.execute()`
(`src/domains/progression/phase.py`) converts `ProgressionDecisionResult` to a plain dict via
`dataclasses.asdict()` before storing it in `property_updates["last_progression_decision"]`, so
`CanonicalStateHasher.to_canonical_json()`/`get_hash()` no longer raises `TypeError`. Re-verified
against this section's own repro shape — `ENABLE_PROGRESSION_EVOLUTION=ON`, `dungeon_crawl` seed
42 (300 ticks instead of the original 2000, since the original crash reproduced by tick ~120) —
exit code 0, all ticks completed, no `TypeError` in stdout or run logs. This ticket did **not**
flip the flag's default and did not touch prerequisite (b): `RewardLedgerService` still has zero
live callers (DEV-004 in `docs/guidelines/intentional_divergences.md`), so option-generation still
converges on `SAVE_FOR_LATER` under real reward flow being genuinely untested remains true. The
flag's default therefore stays OFF pending (b).

## ENABLE_INFORMATION_INTENT_EXECUTION — Validation Trial Result (TCK-20260826)

`TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION` is the follow-up this table's own
`ENABLE_INFORMATION_INTENT_EXECUTION` row named. **This is the 5th and final of the 5 flags
originally deferred by `TCK-20260824-ROLLOUT-FLAG-DECISIONS`** (`ENABLE_COMBAT_ENGAGEMENT`,
`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`, `ENABLE_PROGRESSION_EVOLUTION`, and now
this flag) — all 5 now carry real trial evidence on file. Full raw tally:
`staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/trial_evidence.md`
(moved to `stored_artifacts/` at ticket close).

**The distinction from `ENABLE_BELIEF_ASSIMILATION` — confirmed by direct code read, not
assumed.** Both flags live in the `information`/belief domain but gate different phases:
`ENABLE_BELIEF_ASSIMILATION` gates `InformationBeliefPhase`, whose Branch 3 ("route new query")
*produces* a raw `ActionIntent` into `EntityUpdate.intent_results` when the actor has an
unresolved unknown; `ENABLE_INFORMATION_INTENT_EXECUTION` gates
`InformationIntentExecutionPhase`, which *executes* that already-produced `ActionIntent` via
`ActionIntentAdapter.execute()`. With `ENABLE_BELIEF_ASSIMILATION` ON (its own now-flipped default)
and `ENABLE_INFORMATION_INTENT_EXECUTION` OFF, Branch B's `ActionIntent` is routed but sits inert
— confirmed by `test_action_intent_execution_phase_off_by_default_is_a_noop`. Flipping
`ENABLE_BELIEF_ASSIMILATION` ON alone does not activate this flag's own call site; both must be ON
for the loop to close.

**World tested**: `urban_political` (real compiled state, `entities=10`, confirmed via each run's
successful load), seed 42, 200 ticks, OFF leg (temporary probe, `ENABLE_INFORMATION_INTENT_EXECUTION`
omitted entirely so it falls through to its code-level default OFF) vs. ON leg (the existing
permanent `urban_political_selfmodel_execution_probe.yaml` fixture). `ENABLE_BELIEF_ASSIMILATION`
held ON in both legs throughout, per this ticket's own Out of Scope (never re-litigated, never
toggled off to isolate the flag artificially).

**Commands**:
```
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_information_intent_execution_off_probe \
  --output data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
```

**Evidence tally**: `action_intent`/`ActionIntentAdapter` trace count is **0 in both legs** —
Branch B does not route a query in this corpus/seed/window regardless of which leg, matching
`INFRA-270`'s own `support_boundary` and `INFRA-266`'s prior "does NOT generalize to
`urban_political` at seed 42" finding. Pillar-level differences between the two legs are small
(≤13-event, ≤10%) downstream-cascade deltas from the toggled flag's effect on tick-by-tick
decision ordering — no pillar collapsed toward zero on the ON leg (no-suppression check passes).
`test_information_intent_execution_fires_through_kernel_tick_once` (the deterministic hand-built
scenario, INFRA-270's own guaranteed proof `ActionIntentAdapter.execute()` fires through a real
`Kernel.tick_once()` loop) passed in both the pre-trial and post-trial pytest runs.

**Honest gap — reproduces an already-filed, still-open anchor drift, does not introduce a new
one.** The ON leg's fresh run reproduces `SOCIAL: actual_score=13.35` vs. `grade_anchors.json`'s
anchored `16.815` on `urban_political_selfmodel_execution_probe_seed42_200t` — byte-identical to
the number already reported in the still-`OPEN`
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` (filed from the
`SELF-MODEL-COGNITION` sibling ticket's own trial). `lookup_ceiling()` returns `None` for
`SOCIAL` on this run key — no existing ceiling classification covers it. `INFORMATION` itself does
**not** drift on this specific run key (exact match, `B/0.2` both actual and anchored) —
consistent with the drift ticket's own filing text, which only reported `INFORMATION` drift on the
sibling `urban_political_selfmodel_probe` (materialization-only) run key. This ticket's own
independent re-run confirms the `SOCIAL` drift is deterministic and reproducible, not run-to-run
noise — disclosed here as confirmation, not investigated or fixed (that remains
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`'s own separately-tracked job, not
this ticket's). Separately, `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist
(`calibrate_simq.py:243-250`) does not include `ENABLE_INFORMATION_INTENT_EXECUTION` — a bare
env-var override would silently no-op for this flag; this trial avoided the trap by using
`--profile`-level `feature_flags:` overrides for both legs. Not fixed here — a real, disclosed
tooling gap, out of this ticket's scope.

**Recommendation: Keep OFF, deferred.** `grep -rl "ENABLE_INFORMATION_INTENT_EXECUTION"
config/simulation_quality/profiles/` returns only the non-shipped probe fixture — zero shipped
production profiles turn this flag on today, the same DEV-003 gap all 4 prior sibling flags share.
No new `docs/guidelines/intentional_divergences.md` entry is added — the flag's behavior versus the
Mechanics Bible is unchanged either way, and no Mechanics Bible chapter governs this Phase-10-era
infrastructure flag regardless. If a future ticket wants to re-open this: either (a) a shipped
SimQ corpus profile begins using `ENABLE_INFORMATION_INTENT_EXECUTION=ON` in production, matching
the DEV-003 precedent directly, or (b) a higher-`unknowns`-density world/seed independently
confirms Branch B routing a query through a real (not hand-built) corpus run.

## RolloutProfileManager — Cut

`src/domains/optimization/rollout_profiles.py` defined a full `CLASS_A`/`CLASS_B`/`CLASS_C`
hardware-tier rollout matrix with its own default-ON/SHADOW/OFF assignment per flag —
**conflicting** with `FeatureFlagManager`'s own real defaults (e.g. its `CLASS_A` profile listed
`ENABLE_SELF_MODEL_COGNITION` as enabled; the real default was OFF). Confirmed genuinely
orphaned: the only two references anywhere in the codebase were both test-only
(`tests/perf/test_phase10_integrated_enhanced_stack_budget.py`, which borrowed its
`tick_budget_ms`/`max_trace_events` numbers as convenient test parameters — kept, with those
numbers inlined directly; and `tests/unit/config/test_phase10_rollout_profiles.py`, a dedicated
TDD suite testing nothing but the dead class itself — removed outright). Zero real application
call sites. Both the module and the dedicated test file were removed.

## The Precedent This Sets

Two decision classes exist, both legitimate, neither a default:
1. **Flip ON** requires real, standing evidence the system already runs safely in production —
   here, a live SimQ corpus profile already exercising it. A one-off validated fix (like
   `ENABLE_COMBAT_ENGAGEMENT`'s bug-fix history) is necessary but not sufficient on its own.
2. **Keep OFF, deferred** is not a non-decision — it requires a named follow-up ticket whose job is
   specifically to produce the missing evidence, not an indefinite "someday."

`DEV-002`'s own literal unblock condition (re-running `tools/balance_measure.py`) was found to be
scoped to the specific ticket that wrote it (`TCK-20260627-P0A-ADVENTURE-FLAG`,
`ENABLE_ADVENTURE_ROUTING`'s own economy/hunger metrics) and not a universal fit for every flag's
domain — `DEV-003` documents treating equivalent-strength alternative evidence (standing SimQ
corpus usage in the flag's own domain) as satisfying DEV-002's underlying intent, stated plainly
rather than silently substituted.

## A Real Correction Made During Implementation

The investigation's first pass under-counted `RolloutProfileManager`'s real reference set by one
file (missed `test_phase10_rollout_profiles.py`) and separately, a broad `HardwareClass` grep
initially over-matched dozens of unrelated files (`HardwareClassifier` in
`src/certification/hardware.py`, generic "hardware class" prose) before being narrowed to the
precise `rollout_profiles import` / `RolloutProfileManager\b` pattern. Both corrections are
recorded here and in the staging investigation.md rather than silently fixed without a trace —
worth noting for whoever reviews this precedent: a first grep pass is a starting point, not a
final answer, even on a narrowly-scoped "is this dead" question.

Separately, three independent hardcoded copies of the `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist
were found across the test suite (`tests/unit/config/test_phase10_feature_flags.py`,
`tests/integration/test_scenario_feature_flag_defaults.py`,
`tests/certification/test_phase10_enhanced_determinism_parity.py`) — each explicitly documented as
"kept in sync" with the others, none actually enforced to be in sync by any single source of
truth. All three were updated to add the 2 new flags; this is a real, disclosed architectural
smell (three manually-synchronized copies of the same allowlist) worth a future consolidation
ticket, not fixed here since it is outside this ticket's own scope.

## Related

- `staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/` (investigation.md, plan.md, test_plan.md)
- `docs/guidelines/intentional_divergences.md` (DEV-002, DEV-003)
- `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md` (idea 9, the source scope)
- The 5 named follow-up tickets (see table above)
