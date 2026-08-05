---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, corpus, calibration, roadmap]
---

# SimQ Extension Points

**Purpose:** a single map of every axis along which the Simulation Quality system can be
extended — what exists today on each axis, the real mechanism/file to extend it, and the
governing doc. Distinct from the other SimQ docs: `quality_scoring_contract.md` is the
authoritative *rules* spec, `docs/guides/simulation_quality.md` is the *how-to* for the
event/pillar mechanics specifically, `corpus_tier_taxonomy.md` covers world-corpus structure in
depth. This document is the *inventory of dials* — refreshed in place (like
`current_state.md`), not layered with dated notes.

**Last refreshed:** 2026-08-05.

---

## 1. World breadth — how many worlds

**Now:** 18 worlds across 4 tiers.

| Tier | Count | Job |
|---|---|---|
| Unit | 5 | Isolates exactly one gated mechanic, everything else at baseline |
| End-to-end | 8 | Real, coherent gameplay archetypes |
| Stress | 3 | Fills a named scale/composition gap |
| Regression / baseline | 2 | Frozen control group — do-not-touch |

**Extend via:** `corpus_tier_taxonomy.md`'s explicit classification decision tree — isolates one
mechanic → Unit; fills a named gap → Stress; represents a coherent scenario → End-to-end;
already anchored, no active work → Regression/baseline.

**Open candidates:** 5 named scale-diversity gaps remain unfilled (`corpus_tier_taxonomy.md`
§"Named scale-diversity gaps") — e.g. no world combines a high distinct-faction count (6-9) with
a small map; quest density has never been decoupled from entity count; no AGENCY-active world
exists that's also a "real" gameplay archetype rather than a purpose-built calibration fixture.

**Governing doc:** `docs/simulation_quality/corpus_tier_taxonomy.md`

---

## 2. World depth — modules/content richness within a world

**Now:** entity counts range 11–62, regions 1–10, resource-node density ~1.3–1.75/region across
the corpus. Depth comes from Pattern-6 gated content
(`faction_tension_overrides`/`information_source_profiles`/`pending_information_responses`) and
feature flags (`ENABLE_ADVENTURE_ROUTING`, `ENABLE_SOCIAL_COOPERATION`,
`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`).

**Extend via:** composing existing modules (e.g. `trading_company_hub`) into a world's
`world.yaml` — no new world required, just richer content in an existing one.

**Known ceiling (2026-08-05):** content depth alone does not always move a pillar.
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` composed a proven merchant module into 3 more worlds at
two population sizes and ECONOMY did not move off C in any of the 9 recalibrated anchors — the
real blocker was upstream (no entity ever *forms* a harvest/craft/trade objective), not content
volume. See `docs/audits/D20_simq_quality_status_review.md` Finding 2 before assuming this axis
will close a gap.

**Governing doc:** `docs/simulation_quality/corpus_tier_taxonomy.md`,
`docs/simulation_quality/eval_matrix_results.md` (per-world content history)

---

## 3. Recorded events — the scoring vocabulary

**Now:** 83 scored event types (Certified Level 1, `event_type_coverage.md`). 0 translation
gaps, 0 engine-emission gaps, 1 event with no viable engine path (`camp_constructed` — no
dynamic camp construction exists), 3 flag-gated off in every calibration profile (AGENCY
routing), 13 deliberately unscored.

**Extend via** (`docs/guides/simulation_quality.md`'s 6-step recipe):
1. Add the event type to the relevant scorer's `EVENT_TYPES` (`src/simulation_quality/scorers/`).
2. Add its score delta to `config/simulation_quality/scoring_weights.yaml` under the pillar.
3. Handle it in the scorer's `score()` method, returning a `ScoreRecord`.
4. If the engine emits it under a different name, add a `QualityHub._translate()` entry
   (8 simple 1:1 remaps + 5 payload-conditional remaps exist today).
5. Add tests in `tests/unit/simulation_quality/` (normal path, zero-delta/time-gate path,
   integration through `QualityHub.on_envelope()`).
6. Update the parity ledger entry in `docs/parity_ledger/infrastructure.yaml` if this closes a
   `missing`/`divergent` entry.

**Governing doc:** `docs/simulation_quality/event_type_coverage.md`,
`docs/guides/simulation_quality.md`

---

## 4. Recorded pillars — broader than raw events

Two distinct layers extend independently here:

**Per-pillar accumulator state** (`PillarAccumulator`, §4.3 of the contract) tracks more than a
raw event tally: `event_count`, `negative_count`, `last_event_tick`, a sliding **window_buffer**
(200 events, config-tunable) driving **loop detection** (flags when one tag exceeds 70% of the
window), and **worst_events** (top 100 by `abs(delta)`, negative only — the real troubleshooting
breadcrumb trail, see §3 of `docs/guides/simulation_quality.md`'s "Diagnosing a bad grade").

**The Scenario Registry** (contract §6) — 24 named diagnostic questions (`SQ-01`–`SQ-24`, e.g.
"Is any faction dominating politically or militarily?"), each mapped to exactly one primary
pillar plus an optional secondary, with explicit conflict-avoidance notes preventing the same
signal from being double-scored across two pillars. **A new scoring rule or pillar must register
here first** — this registry is a genuinely separate extension point from adding a raw event
type; it's the layer that gives a pillar's grade a documented "what question does this actually
answer," not just an event count.

**Extend via (new pillar):** declare in the `PillarId` enum (`src/simulation_quality/pillars.py`),
add a scorer class (`src/simulation_quality/scorers/`), declare weights in
`scoring_weights.yaml`. `QualityHub.SCORER_REGISTRY` and the accumulator/report builder both
auto-wire from the scorer's own `EVENT_TYPES` — no other code changes needed.

**Known ceiling:** a completeness audit already ran once and found no 11th pillar justified —
determinism/replay-fidelity, performance/tick-budget, checkpoint integrity, and content/catalog
health are each already owned by a dedicated system outside SimQ
(`TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`).

**Governing doc:** `docs/simulation_quality/quality_scoring_contract.md` §4 (Score Model), §5
(the 10 pillars), §6 (Scenario Registry), §7 (Extensibility Protocol)

---

## 5. Tuning config — no new logic, just different values

**Now:** 4 config files under `config/simulation_quality/`:
- `scoring_weights.yaml` — per-event score deltas, grouped by pillar
- `grade_thresholds.yaml` — the 6-band letter-grade cutoffs (S/A/B/C/D, with F implicit as
  everything below D — see the grade-scale note below)
- `detection_params.yaml` — loop threshold (0.70), window size (200), max worst-events kept
  (100), and per-signal time gates (e.g. `zero_harvest` only fires after tick 100)
- `profiles/*.yaml` — scenario-specific overrides merged on top of the base weights
  (`default`, `dungeon_crawl`, `urban_political` exist today)

**Extend via:** edit the relevant YAML directly; never hardcode thresholds/weights in scorer or
accumulator Python. Activate a profile with `QUALITY_PROFILE=<name>`.

**Known inconsistency (dormant, not currently harmful):** `quality_report.py::_assign_grade()`
has a real 6th grade band, `F` (everything scoring below the `D` cutoff) — but both
`tools/evaluate_simq.py` and `tests/simulation_quality/test_grade_regression.py` define their own
5-value `GRADE_ORDER = ["D", "C", "B", "A", "S"]`, excluding F. F has never actually occurred in
the corpus (0 of 75 fresh reports in this session's full re-run, 0 committed anchors), so this is
latent, not active — but if a real run ever produces F, the comparison tooling has no ordinal
position for it and would report it as an unconditional mismatch rather than a graded distance.

**Governing doc:** `docs/guides/simulation_quality.md` §"Configuration"

---

## 6. Temporal depth — how long a scenario runs

**Now:** anchors exist at 200t/500t/1000t/2000t tick lengths, distinct from world breadth.

**Extend via:** add a new tick-length anchor for an existing world in `grade_anchors.json`
(re-calibrate via `calibrate_simq.py --ticks <n>`).

**Why this matters as its own axis:** the real population-collapse defects documented in
`docs/audits/D20_simq_integration.md` were only ever caught at 1000t/2000t — they were invisible
at 200t. Depth in ticks surfaces failure modes that depth in world content does not.

**Governing doc:** `docs/simulation_quality/eval_matrix_results.md`,
`docs/simulation_quality/corpus_tier_taxonomy.md`

---

## 7. Delivery/feed mode — not content, but a real parity risk

**Now:** two feed modes — in-process (`InProcessQualityFeed`, default, single-process) and broker
(`BrokerQualityFeed`, Redis-backed, production multi-process).

**Real, confirmed risk on this axis:** `TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX` found
broker-mode silently running only 2 of 10 scorers (`AgencyScorer`, `CombatScorer` hardcoded),
producing grades not comparable to in-process runs or the calibration corpus. Fixed, but the
lesson stands: extending anything on axes 3/4 above must be verified in *both* feed modes, not
just the default in-process path used for calibration.

**Governing doc:** `docs/guides/simulation_quality.md` §"Feed modes"

---

## 8. Anchor granularity — what gets committed per scenario

**Now:** `grade_anchors.json` stores only the discretized letter grade per pillar per scenario —
never the raw `normalized_score` that produced it, even though every `quality_report.json`
computes and prints it.

**Real, currently open gap:** because `S` is an unbounded top band (`> +2.0`, no ceiling), a
pillar already at S can regress from a normalized score of 10.0 down to 2.1 without the letter
ever changing — invisible to the regression gate. See
`docs/audits/D20_simq_quality_status_review.md` recommendation item D for the scoped fix (extend
`grade_anchors.json`'s schema to `{"grade": "S", "score": 2.87}` per pillar, add a tolerance-band
assertion alongside the existing letter-grade check).

**Governing doc:** `docs/simulation_quality/quality_scoring_contract.md` §4.4,
`docs/audits/D20_simq_quality_status_review.md`

---

## 9. The engine-correctness bridge

**Now:** one existing bridge — `HardLawMonitor` (a separate engine-invariant-checking system, not
part of SimQ) routes `LAW-SPAWN-OCCUPANCY` violations into SimQ's WORLD DYNAMICS pillar as a
frequency signal (`spawn_occupancy_violation`, `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`). SimQ scores
*how often* a violation occurs, not whether any single placement is legal — that judgment stays
HardLawMonitor's job, per the determinism-exclusion precedent.

**Extend via:** the same pattern — a `QualityHub._translate()` conditional rule keyed on the
violating law/rule ID, routed to whichever pillar owns that domain (per the Scenario Registry).

**Why this is its own axis:** most of SimQ's 83 event types come from gameplay/domain logic; this
is the one deliberate seam between *engine-layer correctness* (owned by
`tests/certification/`/`HardLawMonitor`/architecture tests) and *SimQ's* behavioral scoring. It's
a real, generalizable pattern if other engine-invariant classes ever warrant a SimQ-visible
frequency signal — not yet exercised beyond this one case.

**Governing doc:** `docs/simulation_quality/event_type_coverage.md` §1 (translation table),
`docs/observability/hard_law_monitor.md`

---

## Related

- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/guides/simulation_quality.md` — operational how-to (config, API, event/pillar extension mechanics)
- `docs/simulation_quality/corpus_tier_taxonomy.md` — world-corpus structure and classification
- `docs/simulation_quality/event_type_coverage.md` — full event-type inventory (Certified Level 1)
- `docs/simulation_quality/current_state.md` — refreshed-in-place numeric snapshot
- `docs/audits/D20_simq_quality_status_review.md` — broader-view synthesis, findings, candidate work items
- `docs/audits/D20_simq_integration.md` — original wiring/calibration audit (historical)
