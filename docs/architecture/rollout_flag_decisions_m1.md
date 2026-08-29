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
| `ENABLE_WORLD_EMERGENCE` | **Kept OFF, deferred** | No production evidence. Follow-up: `TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`. |
| `ENABLE_PROGRESSION_EVOLUTION` | **Kept OFF, deferred** | No production evidence; thinnest test coverage of the 5 deferred flags (2 files) — the follow-up must assess coverage depth before trusting any trial. Follow-up: `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`. |
| `ENABLE_INFORMATION_INTENT_EXECUTION` | **Kept OFF, deferred** | No production evidence; distinct system from the now-ON `ENABLE_BELIEF_ASSIMILATION` despite shared domain. Follow-up: `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`. |

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

**Honest gap: `INFORMATION` and `SOCIAL` drifted from their committed `grade_anchors.json` values
on both probe run keys, with no existing `known ceiling` classification covering either pillar.**
`urban_political_selfmodel_probe_seed42_200t`'s `INFORMATION` anchor is `C/0.0`; the fresh run
measured `B/0.2` (`event_count=1`, not `0`). Traced to source: both legs' single
`belief_assimilated`/`belief_updated` event pair (subject `bandit_road_danger`, actor 22, tick 1)
comes from `SelfModelUpdatePhase.run()`'s own Step 1 knowledge-assimilation
(`self_model_phase.py:103-141`, via `KnowledgeModelService.assimilate()` against a seeded
`pending_self_model_information_events` entry) — gated only by `ENABLE_SELF_MODEL_COGNITION`, not
`ENABLE_BELIEF_ASSIMILATION`. It fired identically in both legs, so this is reproducible, not
run-to-run noise; the anchor evidently predates whatever seeded-content or code-path change now
causes it to fire once within this 200-tick window. `SOCIAL` also drifted beyond score tolerance
on both run keys (13.35 actual vs 17.895/16.815 anchored) — not traced further, out of this
ticket's scope. This is disclosed as a genuine new finding requiring its own follow-up ticket to
either re-anchor or investigate as a regression — not fixed or re-anchored here (Scope Guards:
"do not fix any new bug the trial might surface inline"). It does not itself change the
recommendation below, since the DEV-003 bar was already unmet independent of anchor cleanliness.
`COMBAT`/`ECONOMY`/`PROGRESSION` also drifted on the execution-probe run key, but each carries an
existing, pre-existing `known tick_budget` ceiling classification from `tools/simq_ceiling.py`
(200-tick-window threshold noise, unrelated to this flag) — not a new finding.

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
above) is a real, disclosed finding needing its own follow-up ticket before these two grade
anchors can be trusted as regression guards again — not addressed by this ticket.

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
