---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS
phase: open
date: 2026-08-08
tags: [simulation-quality, observability, world]
---

# TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

## Title
Build a per-entity lifecycle scoring tool (7 named metrics, never blended into one score) plus
population/group aggregation (region/faction/kind/role) — the diagnostic layer that the
2026-08-08 lifecycle investigation found is currently missing

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A same-day deep investigation (real, non-synthetic Kernel event-recording runs on
`frontier_extended` and `sandbox_world`, 800 ticks each) found the real, production-default
(`SIM_OBS_MODE`/`RPG_OBS_MODE` unset → `LIGHT`, per `src/observability/config.py`'s own
docstring) event stream is nearly empty and dominated by a handful of near-identical shapes:

- `frontier_extended`: 368 total events across 62 entities (mean 3.3/entity); dominant shape
  `{capability_growth_stalled, progression_plateau_detected}` shared by 27+/62 entities.
- `sandbox_world`: 121 total events across 21 entities; the SAME dominant shape shared by
  14/21 entities (67%), only 5 distinct event-type "shapes" across the whole population.
- Zero `movement`, vitals, XP, level, skill, quest, social, or exploration events in either run.

Root causes (all confirmed via direct code/data inspection, not assumed): (1) LIGHT mode — the
real default — suppresses `movement` and all 13 events added by this session's own entity-
observability-gap tickets (vitals/attributes/equipment/identity), by deliberate design matching
`movement`'s own precedent; (2) genuine mechanic-level scarcity independent of mode
(`ENABLE_PROGRESSION_EVOLUTION`/`ENABLE_COMBAT_ENGAGEMENT` both off corpus-wide, near-zero real
quest completion); (3) what remains is dominated by stall/dormancy detectors, which mechanically
produce false population-wide uniformity once the real signal is hollowed out.

There is currently no tool that answers "is this simulation's entity lifecycle good, diverse, and
non-repeating" as a repeatable, scriptable check — only my own one-off scratch probe
(`/tmp/.../lifecycle_graph_probe2.py`, not committed anywhere) produced the numbers above. This
ticket formalizes that probe into a real, tested, documented tool.

**Per explicit user instruction: this ticket is filed to `tickets/todos/` and Investigate/Plan/
Implement must NOT start until the user gives an explicit go-ahead signal.**

## Scope

### Per-entity metrics (7 total — a vector, deliberately never blended into one composite score,
matching this repo's own established "why multiple metrics, not one" precedent from
`TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE`)

| Metric | Definition | Priority | Range | Direction | Tick-length sensitive? | World-density sensitive? |
|---|---|---|---|---|---|---|
| `path_length` | raw total event count for the entity | **hard gate** — near-zero disqualifies the entity's other metrics as low-confidence | unbounded | higher, with caveats | yes, strongly (more ticks → more raw events) | yes, plausibly (unverified — see sibling calibration ticket) |
| `path_density` | `path_length / ticks_observed` | **hard gate** | unbounded (events/tick) | higher, moderated | mostly removes tick-length confound | still plausibly yes |
| `phase_coverage` | fraction of ~9 lifecycle-phase buckets (vitals/growth, exploration, progression, social, cognition, narrative, identity, conclusion, combat) touched at least once | primary | [0,1] | higher | yes — some buckets (conclusion, narrative) take real time to reach; low coverage at 200 ticks isn't the same finding as low coverage at 5000 | low |
| `path_entropy` | Shannon entropy of the entity's own event-type distribution, normalized to [0,1] | primary | [0,1] | higher, but unreliable below a minimum `path_length` (small-sample noise) | indirect, via path_length | low, indirect |
| `loop_score` | `1 - dominant_repeating_cycle_coverage` (shortest period p with >=85% match over the sequence) | primary | [0,1] | **not simply lower-is-better** — some repetition (eat/sleep/rest cycles) is normal healthy-life maintenance; only *dominating* repetition with nothing else is bad | indirect via path_length; longer runs give real diversity more room to break a loop that looks dominant in a short run | low |
| `growth_trajectory` | (positive-growth event count − stall-tag count) / total events | primary | ~[-1,1] | higher | **structurally yes** — `capability_growth_stalled` needs a 300-tick flat window to be *capable* of firing at all; below that, "not stalled" and "genuinely healthy" are indistinguishable | low |
| `conclusion_coherence` | did the entity reach a sensible endpoint (combat/hazard/age death with cause, ongoing coherent survival) vs. `life_arc_incoherent`-flagged or D05's "silent from spawn" pattern | secondary | binary/flag | coherent-is-better | **structurally yes** — `life_arc_incoherent` requires Hero generation 2+, rare even at 500 ticks; absence of the flag at short tick-counts means "couldn't have fired yet," not "confirmed healthy" | low |

### Population / group aggregation
- For every metric above: **mean AND spread (stdev)**, never mean alone — the mean alone is what
  hid the 67%-identical finding above.
- Grouped by `entity.identity.role`, `entity.identity.faction`, `entity.kind` (closest available
  proxy for "race/species"), and region (derived from `LegalityServiceV2.get_region_for_position`
  on the entity's own navigation state, or spawn region if tracked — confirm which is actually
  queryable at analysis time in Investigate, not assumed).
- **Path-clustering** (the most direct "repeat between paths" signal, and the one that actually
  caught the 67%-identical finding): cluster entities by event-type-set or transition-bigram
  Jaccard similarity; report number of distinct shapes and dominant-cluster share, globally and
  per group.
- **Cross-group comparison**: are groups meaningfully different from each other, or are ALL groups
  homogeneous too (a second-order diversity failure beyond "individuals within a group are
  clones").

### Comparability / normalization mechanism (built into the tool from the start, not bolted on)
- **Within-run z-scores** as the primary cross-entity comparison mechanism (robust to tick-length
  and world-density confounds automatically, since both are run-level constants shifting the
  whole population's baseline together).
- **Minimum-sample gating**: flag `path_entropy`/`loop_score`/`conclusion_coherence` as
  low-confidence below a `path_length` floor (start at `n<6`, matching the probe's own existing
  `if n < 6: return None` guard — exact right cutoff is an empirical question, see the sibling
  calibration ticket, not decided here).
- **Detector-window-reachability metadata**: record `stall_detector_reachable` (`ticks >= 300`)
  and `life_arc_detector_reachable` (empirically-derived threshold) as explicit run metadata
  fields, so a short run's "0% flagged" is never silently compared against a long run's "0%
  flagged" as if they meant the same claim.
- Absolute/raw-number comparison only within a fixed tick-length and world-scale — explicitly
  documented as unsafe otherwise, pending the sibling calibration ticket's empirical findings.

### Investigate (must resolve before Plan)
1. Confirm real entity metadata queryable at analysis time: role/faction/kind/region — exact
   field paths and any joins needed (e.g. faction id → real faction name).
2. **Observability-mode decision**: confirm whether this tool needs a `SIM_OBS_MODE`/
   `RPG_OBS_MODE` override to a richer mode than production `LIGHT` to get meaningful data at
   all (per this session's own finding that LIGHT suppresses `movement` and all of this session's
   own new lifecycle events) — decide whether that's a per-invocation override (matching
   `tools/calibrate_simq.py`'s own `--window-size`/`--loop-threshold` CLI-override pattern, never
   mutating `detection_params.yaml`) or something else. Do not assume; confirm against real code.
3. Confirm the exact real event-type → lifecycle-phase-bucket mapping (the 9 buckets above were
   sketched in a design conversation, not verified against the full, current
   `docs/event_ledger/entity.yaml` + `event_type_coverage.md` catalog — re-derive from those
   authoritative sources, not from memory of the design chat).
4. Confirm data source: replaying a real `simulation_events.jsonl` (matching
   `tools/calibrate_simq.py`'s own `_run_engine()`/`_replay_jsonl_through_hub()` pattern) vs. a
   fresh in-process Kernel run — pick based on what's cheapest/safest to make repeatable and
   testable, not by copying the investigation's own scratch-script shape uncritically.

### Implement
- New tool, e.g. `tools/entity_lifecycle_score.py`, computing all 7 per-entity metrics +
  aggregation + clustering + the comparability mechanism above.
- `docs/simulation_quality/entity_lifecycle_score.md` (technical: formulas, derivations,
  property table, cross-references to the detectors each metric reads from) +
  `docs/guides/entity_lifecycle_score.md` (practitioner guide: how to run it, interpret it,
  worked examples) — matching the `density_metrics.md`/`world_density.md` two-doc precedent.
- Scoped tests: real, non-mocked verification (matching this session's own established
  discipline) that the tool correctly reproduces the investigation's own findings on
  `frontier_extended`/`sandbox_world` (the 67%-clustering, the near-zero path_length) as a
  regression baseline.

## Out of Scope
- Empirically validating/tuning the normalization constants (minimum-sample threshold, whether
  world density actually correlates with event volume, whether activity is front/back-loaded
  over a run) — real follow-up work requiring this ticket's own tool to exist first; tracked in
  the sibling `TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION` ticket, not decided here with
  guessed constants presented as final.
- Fixing the underlying causes found by the investigation (LIGHT-mode suppression as a real
  production concern, `ENABLE_PROGRESSION_EVOLUTION`/quest-completion scarcity) — this ticket
  builds the diagnostic instrument, not the fix for what it measures.
- Wiring this tool into the SimQ pillar-scoring pipeline (`QualityHub`) or `grade_anchors.json` —
  a separate, later decision about whether/how these scores feed SimQ, not assumed here.
- **No implementation until the user gives an explicit go-ahead signal** — this ticket, once
  created, stays in `tickets/todos/` until that signal arrives.

## Acceptance Criteria
- [x] investigation.md confirms real entity-metadata field paths, the observability-mode
      decision, the real event-type→bucket mapping (re-derived from authoritative docs, not the
      design-chat sketch), and the data-source choice — with 2 real, load-bearing corrections
      found along the way (see Implementation Notes)
- [x] plan.md specifies the exact 7 metric formulas (final, code-ready), the aggregation/grouping
      design, the clustering algorithm, and the comparability mechanism (z-scores, gating,
      reachability metadata)
- [x] Tool implemented, computing all 7 metrics + aggregation + clustering + comparability
      mechanism, with weights/thresholds in a config file, not hardcoded in code (matching
      `quality_scoring_contract.md` §4.8's own data-driven-weights convention)
- [x] Technical doc + guide doc written, matching the density-metrics two-doc precedent
- [x] Scoped tests pass, including a real regression check against the investigation's own
      "mean-alone hides clustering" finding (`test_path_clustering_reports_dominant_shape_share`)

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION (sibling — empirical validation of this
  ticket's own normalization assumptions, depends on this ticket shipping first)
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP, TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP (added the 13 events this
  investigation found are invisible under real production LIGHT mode — all DONE)
- TCK-20260808-ENTITY-EVENT-LEDGER (the original entity-mutation-vs-event-coverage audit this
  investigation builds on)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (added `capability_growth_stalled`/
  `life_arc_incoherent` — the two detectors that dominate the real, sparse event stream found by
  this investigation)
- TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE (the "why multiple metrics, not one" precedent
  this ticket's own metric-vector design follows)
- D05_entity_differentiation (`docs/audits/D05_entity_differentiation.md`) — the closest existing
  precedent methodology (personality/class differentiation audit), 7 weeks old, not re-verified
  by this investigation — Investigate should re-check whether its fixes still hold

## Related Docs
- `docs/simulation_quality/event_type_coverage.md`, `docs/event_ledger/entity.yaml` (authoritative
  source for the real event-type → lifecycle-phase-bucket mapping)
- `src/observability/config.py` (`ObservabilityConfig` — LIGHT-mode default, `SIM_OBS_MODE`/
  `RPG_OBS_MODE` override mechanism)
- `docs/simulation_quality/quality_scoring_contract.md` §4.7 (Loop and Stagnation Detection —
  related but distinct existing mechanism, pillar-level aggregate not per-entity, largely dormant
  at calibration tick-density per its own documented finding)
- `docs/world/density_metrics.md` / `docs/guides/world_density.md` (two-doc precedent to mirror)

## Related Stored Artifacts
None yet — this investigation's own findings currently exist only as an uncommitted scratch
script (`/tmp/.../lifecycle_graph_probe2.py` and sibling files) referenced in this session's own
conversation history, not as a durable artifact. Formalizing them is part of this ticket's own
Investigate phase.

## Related Code Areas
- `tools/calibrate_simq.py` (`_run_engine`, `_replay_jsonl_through_hub` — the real event-recording
  path this tool should reuse, not re-derive externally, per the investigation's own hard-won
  methodology correction)
- `src/observability/event_extractor.py`, `src/observability/event_shapers.py` (real event
  producers, LIGHT-mode gating sites)
- `src/observability/live/entity_inspector.py` (`EntityInspectionSnapshot` — precedent for
  per-entity metadata extraction)
- `docs/simulation_quality/quality_scoring_contract.md` §4.7, §4.8

## Assumptions / Open Questions
- Whether world density genuinely correlates with per-entity event volume, and in which
  direction — explicitly NOT assumed; flagged for the sibling calibration ticket, not guessed
  here.
- Whether the `n<6` minimum-sample gating threshold (carried over from the investigation's own
  scratch script) is actually the right cutoff — likewise deferred to empirical validation.
- Whether this tool should read a freshly-generated `simulation_events.jsonl` or run its own
  in-process Kernel — left to Investigate, not decided here.

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly. Implementation began only after the user's explicit
  go-ahead ("implement all recently created tickets"), per this ticket's own standing
  instruction.
- **Real correction #1**: `entity.identity.faction` (int) is the legacy 4-value `Faction`
  `IntEnum`, not the real, content-driven faction — that lives at
  `entity.identity.properties["faction_id"]` (a string, matching all 9-16 real per-world
  factions). Found by direct inspection of a real compiled world before committing to the
  grouping design in Plan, not assumed from the field name.
- **Real correction #2**: region grouping doesn't need `LegalityServiceV2.get_region_for_position`
  spatial lookup (this ticket's own Scope text's primary proposal) —
  `entity.identity.properties["spawn_region"]` is directly available and simpler.
- **Real operational conflict found and resolved**: `tools/calibrate_simq.py::_run_engine()`'s
  own integrity guard (`pressure_mode_final == "NORMAL"`, zero queue backpressure for the whole
  run) is calibrated for SimQ-score trustworthiness specifically, and is non-deterministic under
  the higher `SIM_OBS_MODE=NORMAL` event volume this tool needs (same inputs, one run passed, one
  raised `CalibrationIntegrityError`, confirmed via 2 real back-to-back runs). Built a dedicated,
  lean run-driver (`_run_for_analysis()`) instead of reusing `_run_engine()`, checking the
  narrower, directly-relevant bar (`dropped_count == 0`) and reporting it in the tool's own
  output rather than hard-failing on transient backpressure.
- **Real translation bug found and fixed during end-to-end testing** (not caught by unit tests
  alone — found by actually running the tool against real worlds before writing the test suite):
  the raw `simulation_events.jsonl` carries PRE-translation, PascalCase engine event names (e.g.
  `StrategicObjectiveChanged`), not the snake_case SimQ-contract names `entity.yaml`'s own catalog
  uses. Fixed by reusing `QualityHub._translate()` directly (real reuse, not a hand-duplicated
  alias list) before bucket lookup; added the one genuinely untranslatable raw name
  (`StrategicBlockerAdded`, confirmed via direct inspection of `quality_hub.py`'s own translation
  dicts) as an explicit alias, since this tool's scope is broader than the SimQ-scored event set.
  `phase_coverage`'s own population mean improved from 0.35 to 0.46 after this fix (real, not
  cosmetic — a third of the previously-"unbucketed" signal was real strategic-cognition activity
  hiding behind untranslated names).
- Verified end-to-end on two structurally different real worlds (`sandbox_world`,
  `frontier_extended`) before finalizing the test suite — `frontier_extended` showed markedly
  less clustering (16% dominant-shape share, 27 distinct shapes across 62 entities) than
  `sandbox_world` (52%, 7 shapes across 21) — a real, interesting cross-world difference the
  sibling calibration ticket can investigate further.
- `life_arc_detector_reachable` is reported `null`, not guessed — `life_arc_incoherent` requires
  Hero's Journey generation ≥ 2, which has no clean tick-count proxy the way
  `capability_growth_stalled`'s 300-tick window does; fabricating one was rejected in favor of
  honestly reporting "not derivable from tick count alone."
- Parity: no subsystem mapping exists yet for these new files (brand new, not yet cited by any
  ledger entry's own evidence) — `expected_subsystems_for_files()`/`find_p0_intersection()` both
  confirmed empty.

## Test Summary
- `tests/tools/test_entity_lifecycle_score.py` (new, 17 tests across 5 classes):
  `TestPerEntityMetrics` (7 tests covering all 7 metric formulas, including a real bug caught and
  fixed in the test's own fixture — a period-7 cyclic sequence is a genuine loop regardless of
  distinct-type count, not a bug in `loop_score` itself), `TestAggregation` (3 tests, including
  the direct regression check against the investigation's own "mean hides clustering" finding),
  `TestComparability` (2 tests), `TestBucketMapping` (2 tests), `TestRealIntegration` (3 tests,
  real non-mocked Kernel runs — confirms `--run-dir` mode never drives a Kernel, confirms
  `dropped_count` reporting without hard-failing on pressure, confirms real end-to-end sane output
  on `sandbox_world` at 800 ticks).
- Combined scoped run (`test_parity_index.py` + `test_corpus_registry.py` +
  `test_score_ceilings.py` + `test_entity_lifecycle_score.py`): 67 passed, 0 failed.
- Manually verified end-to-end (beyond the automated suite) on both `sandbox_world` and
  `frontier_extended`, confirming real, sane, non-crashing output before finalizing.

## Files Changed
- `tools/entity_lifecycle_score.py` — new tool (~400 lines): dedicated run driver, entity
  metadata/path extraction, 7 per-entity metrics, aggregation/grouping, path clustering,
  comparability mechanism, CLI
- `config/simulation_quality/entity_lifecycle_weights.yaml` — new, data-driven thresholds and
  the 9-bucket event-type mapping
- `tests/tools/test_entity_lifecycle_score.py` — new, 17 tests
- `docs/simulation_quality/entity_lifecycle_score.md` — new, technical doc
- `docs/guides/entity_lifecycle_score.md` — new, practitioner guide

## Completion Summary
Built the diagnostic instrument the same-day lifecycle investigation found missing: 7 named,
never-blended per-entity metrics (path_length, path_density, phase_coverage, path_entropy,
loop_score, growth_trajectory, conclusion_coherence), aggregated with mean AND spread (never mean
alone — the exact gap that hid the investigation's own 67%-identical finding), grouped by the
real role/faction/kind/region dimensions, with path-clustering as the most direct "repeat between
paths" signal. Two real corrections were found and fixed before the design was finalized (the
legacy vs. real faction field, the unnecessary spatial-lookup region derivation), one real
operational conflict was found and resolved (calibrate_simq.py's own stricter, non-deterministic
integrity guard, worked around with a dedicated lean run-driver), and one real translation bug
was caught and fixed by actually running the tool end-to-end before trusting it (raw PascalCase
event names bypassing the bucket mapping, fixed by reusing QualityHub's own real translation
logic). All thresholds are shipped as reasoned-but-unverified initial values, explicitly flagged
for the sibling calibration ticket's own empirical validation, not presented as final.
