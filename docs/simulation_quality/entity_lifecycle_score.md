---
status: active
layer: simulation
authority: P2
audience: developer
last_verified: 2026-08-08
---

# Entity Lifecycle Score

**Source:** `tools/entity_lifecycle_score.py`, `config/simulation_quality/entity_lifecycle_weights.yaml`
**Related docs:** [../guides/entity_lifecycle_score.md](../guides/entity_lifecycle_score.md) (practitioner guide),
`docs/event_ledger/entity.yaml`, `docs/simulation_quality/event_type_coverage.md`,
`docs/simulation_quality/quality_scoring_contract.md` §4.7 (related but distinct pillar-level
loop detection)
**Ticket:** TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

---

## Why this tool exists

A 2026-08-08 investigation into entity lifecycle observability found that under the real
production default (`ObservabilityMode.LIGHT`), a full 800-tick simulation on a real corpus
world recorded as few as 368 total events across 62 entities — and of those, 67% of the
population on `sandbox_world` shared one identical 2-event-type "shape"
(`{capability_growth_stalled, progression_plateau_detected}` — both meaning "nothing happened").
There was no repeatable tool to measure this; only a one-off scratch script produced those
numbers. This tool formalizes that investigation into a real, tested, documented instrument.

## Why multiple metrics, not one score

Matching this repo's own established pattern (`docs/world/density_metrics.md`'s "why multiple,
not one" reasoning): a single blended score would hide exactly the failure mode above — a
healthy-looking mean can coexist with a population that's 67% identical. 7 per-entity metrics are
computed, each answering one real question, aggregated with **mean AND spread**, never mean alone.

## The 7 per-entity metrics

| Metric | Formula | Range | Direction | Confidence-gated? |
|---|---|---|---|---|
| `path_length` | raw total recorded event count | unbounded | higher, with caveats | no — this metric IS the gate |
| `path_density` | `path_length / ticks_observed` | unbounded (events/tick) | higher, moderated | no |
| `phase_coverage` | fraction of the 9 lifecycle-phase buckets touched at least once | [0,1] | higher | no |
| `path_entropy` | Shannon entropy of the entity's own event-type distribution, normalized to [0,1] | [0,1] | higher | **yes**, below `minimum_sample_threshold` |
| `loop_score` | `1 - dominant_repeating_cycle_coverage` (shortest period with ≥85% match over the sequence) | [0,1] | not simply lower-is-better — some repetition (eat/sleep/rest maintenance) is normal; only *dominating* repetition with nothing else is bad | **yes** |
| `growth_trajectory` | `(positive-growth event count − stall-tag count) / path_length` | ~[-1,1] | higher | no |
| `conclusion_coherence` | `not any(life_arc_incoherent tag present)` | bool | coherent-is-better | no (the tag itself is the direct signal, not a derived statistic) |

`path_length`/`path_density` are **hard gates**, not just "one more metric" — when they're low,
the reliability of `path_entropy`/`loop_score` collapses (entropy on a 2-event sequence is nearly
meaningless; loop detection is undefined below 6 events by construction). Every entity below
`minimum_sample_threshold` (config-driven, default `6`) has `path_entropy_confidence`/
`loop_score_confidence` marked `"low"` rather than silently trusted.

## Real event-type → lifecycle-phase-bucket mapping

Re-derived directly from `docs/event_ledger/entity.yaml`'s own 22-row `event_types` columns (the
authoritative `EntityUpdate`-mutation → event-type catalog), not invented ad hoc — see this
ticket's own `investigation.md` for the full row-by-row cross-reference. 9 buckets:
`VITALS`, `GROWTH_PROGRESSION`, `EXPLORATION`, `COMBAT`, `ECONOMY`, `SOCIAL`,
`STRATEGY_COGNITION`, `NARRATIVE_QUEST`, `IDENTITY`, `CONCLUSION_DEMOGRAPHIC`. The exact
event-type lists live in `config/simulation_quality/entity_lifecycle_weights.yaml`'s
`lifecycle_phase_buckets` key, data-driven per `quality_scoring_contract.md` §4.8's own
convention. `ENTITY-015` (`TaskUpdate`) contributes no bucket, matching its own already-documented
`deliberately_uncovered` verdict.

**Event-type translation**: the raw `simulation_events.jsonl` this tool reads carries
PRE-translation, engine-emitted event names (e.g. `StrategicObjectiveChanged`) —
`src/simulation_quality/quality_hub.py`'s own `QualityHub._translate()` only normalizes these to
the SimQ contract vocabulary (e.g. `strategic_goal_changed`) at scoring time, not at emission
time. This tool reuses `QualityHub._translate()` directly before bucket lookup, so its bucket
mapping (built from the translated catalog) actually matches what's in the JSONL. One raw name
(`StrategicBlockerAdded`) has no SimQ-contract translation at all — added as its own alias in the
`STRATEGY_COGNITION` bucket, since this tool's scope is broader than the SimQ-scored event set.

## Real entity metadata fields (a real correction, not an assumption)

Grouping is by `role`/`faction`/`kind`/`region`. Direct inspection of a real compiled world found
two of these are NOT what they first look like:

- **`faction`**: `entity.identity.faction` (the int field) is the *legacy* `Faction` `IntEnum`
  with only 4 values (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`). The real,
  content-driven faction — matching `state.factions`' own 9–16 real keys per world — lives at
  `entity.identity.properties["faction_id"]` (a string). Grouping by the int field would silently
  collapse every real faction distinction into 4 buckets; this tool uses the properties string.
- **`region`**: `entity.identity.properties["spawn_region"]` is directly available on every real
  entity — no `LegalityServiceV2.get_region_for_position` spatial lookup needed, and arguably
  more meaningful for cohort analysis than an entity's live end-of-run position.
- **`kind`**: `entity.kind` is a job/archetype string (worker/guard/raider/scout/etc) — the
  closest real proxy for "race/species" this codebase has, not literal species. Disclosed as
  such, not overclaimed.

**Mid-run-spawned entities** (`TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP`): real
population growth during a run (via `SpawnService`/`BossService`/`RaidService`/`CampService`/
`CalamityService`/`DemographicCycleService` — a real, multi-source mechanic, not one birth
formula) used to leave newly-born entities with `role: None`/`faction: None`/`kind: None`/
`region: None` in every grouped breakdown, since the metadata source was built once from the
pre-run world snapshot. `_run_for_analysis()` now also captures the real, post-run entity map
(`kernel.state.entities`, before shutdown) and `extract_entity_paths()` resolves any entity
missing from the pre-run snapshot against it. **One real, disclosed residual limitation**: an
entity both born and removed (death/despawn) entirely within the observed window still falls back
to `None` — present in neither snapshot. This only affects driving a fresh run
(`--world`/`--ticks`); `--run-dir` mode (scoring a historical run with no live Kernel) keeps the
pre-run-only behavior, since there is no live `kernel.state` to read post-run metadata from.

## Population aggregation, grouping, and clustering

For every metric: **mean and stdev**, globally and per group (`role`/`faction`/`kind`/`region`).
Within-run **z-scores** per entity per metric are computed relative to that run's own population
— the primary cross-entity comparison mechanism, chosen because it's automatically robust to
tick-length and world-density confounds (both are run-level constants that shift the whole
population's baseline together; see the sibling `TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION`
ticket for empirical validation of exactly how robust).

**Path clustering** is the most direct "repeat between paths" signal: entities are grouped by
their exact event-type-set, reporting the number of distinct shapes and the dominant shape's
population share, globally and per group. This is the mechanism that actually caught the
investigation's own 67%-identical finding — a mean/stdev alone would not have.

**Archetype-aware interpretation** (`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`):
`cluster_paths()`/`score_run()` accept an optional `world_name` (threaded from the CLI's
`--world`), used to look up `config/simulation_quality/corpus_registry.yaml`'s
`_worlds.<name>.archetype` and, when it's `"monster_only_gauntlet"`, attach a `diversity_context`
string to `clustering.global`. `archetype` is computed by `tools/generate_corpus_registry.py`'s
`compute_archetype()` from each world's own static `resolved/world.resolved.yaml` `entities`
list — `"civilian_settlement"` if any population entry's `role` field is in `{"worker", "guard",
"merchant", "blacksmith"}`, else `"monster_only_gauntlet"`. A real, corpus-wide survey (this
ticket's own investigation.md) found this is genuinely bimodal across all 20 corpus worlds — no
world sits in between. **`entity.identity.role` (the `EntityRole` IntEnum) was tried first and
found unreliable** — real data shows monster-kind entities are tagged `role=CITIZEN` corpus-wide,
not `role=MONSTER`; `entity.kind` (a content-driven string, matching the resolved YAML's `role`
field 1:1 despite the confusing name collision) is the real, correct signal. This annotation never
adjusts the raw `dominant_shape_share`/`distinct_shapes` numbers — only their interpretation.

## Real operational finding: observability mode, and a run-driver design decision

The real production default (`ObservabilityMode.LIGHT`) suppresses `movement` and every event
this session's own entity-observability-gap tickets added (vitals/attributes/equipment/identity)
— confirmed via direct code inspection, not assumed. This tool forces `SIM_OBS_MODE=NORMAL`
(config-driven, `default_obs_mode`) before running a fresh simulation — confirmed via a real
flag-mapping diff that NORMAL adds genuinely useful signal (`OBS_BEHAVIOR_NORMALIZATION`/
`TIMELINE`/`METRICS`) with no real cost (`OBS_WAREHOUSE_INGEST`, NORMAL's one seemingly-risky
flag, has zero consumers anywhere in `src/` — dead code, confirmed via direct grep).

**Real numbers, `sandbox_world` seed 42, 800 ticks**: LIGHT mode recorded 368 total events;
NORMAL mode recorded 35,785 — a ~97x increase, unlocking `biological_state_changed` (dominant),
`stamina_changed`, `movement`, and real strategic/governance/ecology signal that was completely
invisible at the real default.

**A real conflict was found and resolved during Implement**: `tools/calibrate_simq.py`'s own
`_run_engine()` has a stricter integrity guard (`pressure_mode_final == "NORMAL"`, i.e. zero
queue backpressure for the *entire* run) calibrated for SimQ-score CALIBRATION trustworthiness
specifically. Running the same `sandbox_world`/seed-42/800-tick case twice at
`SIM_OBS_MODE=NORMAL` produced one pass and one `CalibrationIntegrityError` — the higher NORMAL-
mode event volume genuinely triggers real-time queue pressure that is **non-deterministic**
(timing-sensitive, not a function of world/seed/ticks). This tool does not reuse `_run_engine()`;
it has its own dedicated, lean run-driver checking the narrower, directly-relevant bar
(`dropped_count == 0` — no event was actually lost), reported in its own output as
`run_health.dropped_count`, never hard-failing on transient backpressure alone.

## Empirical calibration (TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION)

The comparability assumptions above were shipped as reasoned-but-unverified initial values. This
follow-up ticket ran the tool itself across real worlds and real tick-lengths to check them.

**Density vs. `path_length`/`path_density`** — 6 real worlds spanning the real
`entity_density_per_area` range, fixed at 500 ticks: Pearson r = 0.495 (n=6). Weak/non-robust at
this sample size, and the raw numbers are non-monotonic. **No density-based correction was added**
— the within-run z-score mechanism is not shown to need one; this is a verified "no correction
needed" finding, not a gap. A real, much stronger secondary correlation was found instead:
density vs. `dominant_shape_share`, **r = -0.734 (n=6)** — denser worlds measurably show less
population-wide path clustering. Not strong enough at n=6 to hard-code, but real enough to use as
interpretive context (see the guide's own updated interpretation section).

**Tick-length activity profile** — fixed world (`sandbox_world`, seed 42), 4 tick-lengths:

| Ticks | `path_length` mean | `path_density` mean | `dominant_shape_share` | `phase_coverage` mean |
|---|---|---|---|---|
| 200 | 191.9 | 0.9597 | 0.500 | 0.239 |
| 500 | 635.4 | 1.2709 | 0.611 | 0.378 |
| 1000 | 1175.9 | 1.1759 | 0.190 | 0.533 |
| 2000 | 1259.0 | 0.6295 | 0.179 | 0.557 |

`path_density` is genuinely non-flat (rises then falls — plausibly consistent with
`docs/audits/D05_entity_differentiation.md` F4's own precedented "entities settle into uniform
routine after early ticks" finding, not independently re-verified here). `phase_coverage`
monotonically increases with tick length, confirming its own documented tick-sensitivity with
real numbers. **`dominant_shape_share` is artificially inflated at short tick-lengths** (0.50–0.61
at 200–500 ticks) and stabilizes by ~1000 ticks (0.190 vs 0.179, a small gap vs. the much larger
500→1000 swing) — a real, measured instance of the "short paths mechanically look more clustered"
confound. **Real fix**: `clustering_reliable_tick_threshold: 1000` added to the weights config;
`run_metadata()` now reports `clustering_reliable` alongside `stall_detector_reachable`.

**Minimum-sample threshold** — truncated-prefix entropy vs. full-length entropy, 59 real entities
(`frontier_extended`, 800 ticks, ≥30 events each): mean deviation decreases smoothly from 0.43
(L=3) to 0.26 (L=25), no sharp knee anywhere. **`minimum_sample_threshold` kept at `6`** — the
evidence doesn't justify changing it; this is documented as a verified, deliberate non-change.

**`life_arc_detector_reachable`** remains `null` — none of this ticket's own real runs reached
Hero generation 2 either, consistent with the sibling ticket's own disclosed rarity finding, not
resolved here.

## Why `growth_trajectory` reads negative population-wide (TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX)

A real, structural pacing finding, not a residual bug from the sibling kill-reward fix
(`TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE`, which was independently
verified correct). Two real, live 2000-tick probes (`urban_political`, `resource_dense_basin`)
found **only `xp_granted`** ever fires among the 6 `growth_trajectory_tags.positive` tags —
`level_up`, `skill_unlocked`, `recipe_learned`, `item_equipped`, `attribute_changed` were all zero
in both. `xp_granted` itself only fired 3-5 times population-wide, vs. `capability_growth_stalled`
+ `progression_plateau_detected` firing 63-64 times — a real ~13-21x imbalance, sufficient on its
own to explain the negative population mean (most entities never receive a single growth-tagged
event across 2000 ticks, while the stall detector re-fires roughly every 300 ticks regardless).

Traced why `level_up` specifically never fires despite `xp_granted` occurring: a single kill
delivers `defender.identity.evolution_level * classification.xp_multiplier` = 10 XP (level-1
monster) against a real level-1 threshold of 100 XP (`LevelingService.get_xp_required(1)`) — with
only 3-5 real kills population-wide, spread across different attackers rather than concentrated,
no entity in either real run crosses even the first level threshold.

**A real fix candidate (raising the per-kill XP multiplier) was evaluated and found insufficient
by the numbers** — even doubling the growth-event count (via unlocking `level_up` on the first
kill) remains tiny against the real ~63-64 stall-tag count; the imbalance is ~13-21x, not ~2x. Not
implemented — it would be a disclosed Mechanics Bible divergence for a change that demonstrably
doesn't resolve the finding. Real quest-completion rate re-confirmed still zero at 2000 ticks
(`quest_started`/`quest_completed` both 0, direct probe, not inherited from the 1000-tick finding
uncritically).

**Real conclusion**: this is a genuine pacing/balance characteristic of the current corpus — real
combat/kill frequency is too low relative to the stall detector's own comparatively frequent
300-tick cadence — the same class of finding as `wilderness_survival`'s archetype-correct low
diversity, not a code defect. The real remedy (raising corpus-wide combat frequency, or
lengthening `capability_growth_stalled`'s own cadence) is a substantial balance initiative with
its own real risk (`grade_anchors.json` recalibration across dozens of scenarios) — tracked as its
own follow-up ticket rather than forced through here.

## Long-run observation tier (TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER)

The tick-length profile above (200-2000 ticks, `sandbox_world` only) motivated a real, corpus-wide
follow-up: a survey of `docs/simulation_quality/quality_scoring_contract.md` found 7 more
tick/event-window-gated SimQ scorer rules beyond `capability_growth_stalled` (300 ticks) and this
tool's own `clustering_reliable_tick_threshold` (1000 ticks) — `belief_system_dormant`/
`entropy_reward` (100 ticks), `faction_trajectory_stagnant`/`social_structure_static` (300
ticks), `gold_frozen`/`emergence_dormant` (500 ticks), `trauma_hazard_broken` (loop signal, >100
ticks). Real max found: 500 ticks — below this tool's own 1000-tick `clustering_reliable`
threshold, which remains the binding constraint. §4.7's own 200-scored-event loop-detection
window is a distinct, related concept (events, not ticks — see that section) with only an
indirect tick-length implication.

Real 5000-tick runtime cost, measured (not assumed): `frontier_extended` (59 entities) and
`simq_scale_stress_seed42` (68 entities — the corpus's 2 largest worlds) both complete a real
5000-tick `Kernel` run in ~250s, `dropped_count=0`. `tools/simq_long_run_observation.py`
(`make simq-long-run-lifecycle-observation`) drives one real Kernel run per world at 5000 ticks
(reusing this tool's own `_run_for_analysis()` driver, not `calibrate_simq.py`'s `_run_engine()`
— same non-determinism-avoidance rationale as this doc's own "real conflict" note above), and
derives **both** the real SimQ pillar report (reusing `calibrate_simq.py`'s own
`_build_hub`/`_replay_jsonl_through_hub` against the same `run_dir`, no second Kernel run) and the
entity-lifecycle score from that single run — writing both to
`docs/simulation_quality/long_run_observations/{world}_seed{seed}_{ticks}t.json`. Default world
set is the same 6-world density-correlation sample this ticket's own calibration sibling already
established. This is a periodic observation practice, not a fast-tier regression fixture —
`grade_anchors.json` and pillar-scoring formulas are untouched.
