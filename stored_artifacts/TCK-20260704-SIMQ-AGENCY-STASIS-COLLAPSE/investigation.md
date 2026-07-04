---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE
artifact_type: investigation
tags: [simulation_quality, agency, cognition, stasis, calibration, bug]
---

# Investigation: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE

## 0. Provenance note

This investigation was started once, halted mid-way (user interrupt for an unrelated reason),
and resumed/completed in a second pass. Section 1 below is the halted attempt's verified
partial findings (kept, integrated, lightly corrected where the resumed pass found more
precise numbers). Sections 2+ are new work from the resumed pass.

---

## 1. Carried-over findings from the halted attempt (verified true)

- Reproduced cleanly: `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500
  --seed 456 --name simq_routing_test` → `AGENCY grade=F, norm=-345.082, events=693, negative=491`.
  Must `rm -rf data/calibration/simq_routing_test_seed456_500t/` before re-running —
  `src/simulation_quality/persistence.py:22` opens `quality_scores.jsonl` in append mode with
  no truncation, so re-running without clearing silently duplicates stale history from prior
  runs. Real, separate tooling footgun; not this ticket's job to fix, noted here only.
- Only 3 entities emit AGENCY events in this run: entity 23 (491 events, ALL
  `defer_with_reason`/`defer_idle`/`stasis_N` — defers on essentially every tick from **tick 1**,
  not "starting tick 176" as the ticket's own phrasing implies; tick 176 is when the escalating
  penalty becomes visually dominant in `worst_events`, not when the deferring starts), entities 24
  and 25 (101 events each, non-defer — `route_selected`/`action_executed`/`route_family_first_use`).
- The penalty plateaus around tick ~170+ at roughly -406 to -418 per event. Traced to
  `src/simulation_quality/pillar_accumulator.py:37` (`window_buffer = deque(maxlen=window_size=200)`,
  `config/simulation_quality/detection_params.yaml:3`) becoming saturated with `defer_idle`-tagged
  records, and `src/simulation_quality/scorers/agency.py:106-111`'s
  `stasis_per_tick * (defer_count - stasis_gate_ticks)` formula, where `defer_count` comes from
  `context.window_tag_counts[PillarId.AGENCY].get("defer_idle", 0)` — a POPULATION-WIDE windowed
  count, not a per-entity consecutive-tick counter.
- Doc/implementation discrepancy: `docs/simulation_quality/quality_scoring_contract.md:556`
  describes the intent in prose as "Entity receives DEFER for N>5 **consecutive ticks**" (implying
  per-entity tracking), but both the contract's own pseudocode (lines 449-454, variable literally
  named `consecutive`) AND the actual `agency.py` implementation use the shared population-wide
  windowed count instead. The doc's own code sample has the same population-wide-vs-consecutive
  mislabeling as the real implementation — this is not merely prose drifting from code, the
  contract's own worked example encodes the same bug under a misleading variable name.

---

## 2. Root cause chain (this pass — confirmed with file:line evidence + live re-derivation)

### 2.1 Why entity 23 always defers (decision-path trace)

Traced the full path: `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py:87-130`)
→ `ResourceOpportunityProvider.get_opportunities()` (`src/world/providers/resources.py:26-99`)
→ `AdventureRouteGenerator.generate()` (`src/domains/adventure/generator.py:24-180`)
→ `AdventureDecisionService.decide()` (`src/domains/adventure/service.py:30-165`).

Confirmed via the raw run artifacts under `data/runs/run_1783175403_1673/` (this run's own
`decision_trace.jsonl` — not reconstructed/guessed):

```
{"entity_id": 23, "tick": 0,   "routes": [{"route_kind": "defer_with_reason", "score": 0.15, ...}]}
{"entity_id": 23, "tick": 498, "routes": [{"route_kind": "defer_with_reason", "score": 0.15, ...}]}
```

Entity 23 has **exactly one candidate route every single tick from tick 0 to tick 498**:
`defer_with_reason`, score frozen at 0.15, entirely static for the whole run. This is the
`generator.py:164-175` empty-candidate-set fallback (`opts` is empty → append one
`DEFER_WITH_REASON` route, `reason="no active opportunities or structural needs identified;
deferring."`). Confirmed against the raw `simulation_events.jsonl` payload for entity 23's
`defer_with_reason` events (not the `quality_scores.jsonl` derived record, which discards the
per-event `reason` string and always shows the scorer's generic `"entity deferred action"`):

```json
{"tick": 1, "entity_id": 23, "event_type": "defer_with_reason",
 "payload": {"entity_id": 23, "reason": "no active opportunities or structural needs identified; deferring.", "tick": 1}}
```

This is the `generator.py` path (empty `opts`), **not** the `service.py` "all candidates blocked"
path (`service.py:114`, reason string `"All candidates are blocked."`) — the two fallback reasons
are textually distinguishable and the raw payload confirms it's the former for all 491 events.

Working backward through `generate()` to find why `opts` is empty every tick:

1. **`ResourceOpportunityProvider.get_opportunities()` never returns a `gather_resource`
   opportunity for any hero spawned in `hometown`.** `resources.py:69`:
   `if current_region in res_def.source_region_tags:` — gates opportunity emission on the
   entity's current region being a member of the resource node's `source_region_tags` tuple.
   Live-compiled `simq_routing_test` world (verified via `WorldCompiler.compile()` for all 3
   seeds) has 5 resource nodes with these tags: `herb_patch → (near_forest, moon_cave)`,
   `wood_node → (near_forest,)`, `iron_vein → (old_mine,)`, `silver_vein → ()`,
   `crystal_outcrop → ()`. **None of the 5 nodes list `hometown`.** All three tracked heroes
   (23, 24, 25) spawn with `navigation.region_id = "hometown"` in all 3 seeds. This is
   seed-independent: no hero standing in `hometown` can ever receive a `gather_resource`
   opportunity in this world, regardless of seed.
2. **No structural-default route ever fires.** `generator.py:97` (`RECOVER` via
   `low_health`/`healing`) and `generator.py:110` (`ASK_INFORMATION` via
   `weak_weapon`/`equipment_improvement`) both gate on `entity.self_model.needs.active_needs` /
   `entity.self_model.self_awareness.perceived_weaknesses`. Verified directly from the compiled
   world state and from `entity_personality_snapshots.jsonl`: entities 23/24/25 all have
   `active_needs = {}` and `perceived_weaknesses = ()` at spawn, and this run's calibration
   profile does not exercise whatever systems would populate them (no combat, no hunger decay
   observed) — they stay empty for the full 500 ticks for all three entities.
3. **`FORM_PARTY` (`generator.py:124-162`) is gated on a hard personality-trait cliff:
   `if sociability >= 0.2:`.** This is the ONLY route family any `hometown`-spawned hero in this
   world can ever receive, given (1) and (2) above. Compiling the world directly with
   `WorldCompiler.compile(spec, seed)` for each seed gives entity 23's `sociability`:

   | seed | entity 23 sociability | FORM_PARTY eligible (>= 0.2)? |
   |---|---|---|
   | 456 | **0.18816282280743812** | **No** |
   | 42  | 0.533976221575395 | Yes |
   | 123 | 0.4067142624206461 | Yes |

   Entities 24 and 25 have sociability 0.19–0.78 across all seeds and are `>= 0.2` in every
   seed tested (24: 0.548/0.537/0.251, 25: 0.779/0.794/0.759) — they always qualify for
   `FORM_PARTY`, which is exactly the `form_party` route selected at tick 0 in their own
   `decision_trace.jsonl` entries, immediately followed by `action_executed` (confirmed in
   `quality_scores.jsonl` tick 1: `action_executed` events for 24 and 25).

Chain: entity 23 in seed456 has **zero possible candidate routes, every tick, for the entire
run** — not because any code path is malfunctioning relative to its own documented contract
(`docs/mechanics/adventure_routing_contract.md` describes exactly this fallback-guarantee
behavior, `generator.py:164-175`, as intended when `opts` is empty), but because this
specific world's content (no resource node tagged for the `hometown` spawn region) plus this
specific entity's randomly-rolled personality trait (`sociability` below the `FORM_PARTY` gate)
combine to close off every route family simultaneously.

### 2.2 Why seed456 specifically

Confirmed directly (not inferred) by compiling `data/worlds/simq_routing_test/resolved/world.resolved.yaml`
via `WorldCompiler.compile(spec, seed)` for `seed in (456, 42, 123)`: entity IDs and region/resource
layout are **identical** across all three seeds (30 entities, 3 regions, 5 resource nodes, same
node kinds/tags, all heroes spawn in `hometown`). The only thing that differs is the RNG-derived
personality trait roll for each entity. Entity 23's `sociability` happens to land just under the
`0.2` `FORM_PARTY` gate in seed456 only (0.188 vs. 0.534/0.407 in the other two seeds) — a genuine
RNG draw difference, not a route-generation or blocker-rejection bug. Re-ran seed42 and seed123
calibration (500t) and confirmed: `AGENCY` grades `A` for both, `overall_grade=A` for both,
zero `stasis_N`/`defer_idle` domination in either — entity 23 never enters a defer streak in
either seed because it always qualifies for `FORM_PARTY` there.

This satisfies AC "Explanation for why this occurs in seed456 but not seed42/seed123" — it is a
seed-specific RNG draw on a single personality trait crossing a hard-coded threshold, compounded
by this world's resource-node region tags never covering the heroes' spawn region (a
seed-independent world-content property that happens to only matter when `FORM_PARTY` is also
unavailable).

### 2.3 The scoring-formula mechanism (re-derived with exact numbers, not just plateau estimate)

Confirmed with the raw per-tick events (`data/calibration/simq_routing_test_seed456_500t/quality_scores.jsonl`),
ticks 1–14, `stasis_gate_ticks=5` (`config/simulation_quality/detection_params.yaml:5`),
`stasis_per_tick=-3.0`, `defer_idle=-1.0` (`config/simulation_quality/scoring_weights.yaml`):

```
tick 1-6:  defer_idle only, delta=-1.0  (window defer_idle count <= gate=5)
tick 7:    delta=-4.0   (defer_count=6,  extra=1, -1 + -3*1  = -4)
tick 8:    delta=-7.0   (defer_count=7,  extra=2, -1 + -3*2  = -7)
tick 9:    delta=-10.0  (defer_count=8,  extra=3, -1 + -3*3  = -10)
tick 10:   delta=-13.0  (extra=4)
tick 11:   delta=-16.0  (extra=5)
...
tick 14:   delta=-25.0  (extra=8)
```

This matches `agency.py:106-111` exactly: `delta = defer_idle + stasis_per_tick * (defer_count -
stasis_gate_ticks)` where `defer_count = context.window_tag_counts[PillarId.AGENCY].get("defer_idle", 0)`.
Traced `window_tag_counts` construction to `src/simulation_quality/quality_hub.py:170-176`:
it iterates `PillarAccumulator.snapshot()["window_buffer"]` (`pillar_accumulator.py:37`,
`deque(maxlen=200)`, shared across **all entities'** events for the `AGENCY` pillar) and counts
tag occurrences — there is **no `entity_id` filtering anywhere in this path**. `ScoringContext`
(`score_record.py:31`) itself has no entity dimension. This is architecturally population-wide
by construction, not an accidental oversight local to `agency.py`.

By tick ~176+, the window (200-deep) is saturated almost entirely with entity 23's own
`defer_idle` records (since entities 24/25 emit only ~101 total non-defer events across 500
ticks, most of the window's 200 slots are entity 23's repeated defers), so `defer_count`
plateaus around 144, giving `delta = -1 + -3*(144-5) = -418`, matching the reported
`worst_events` entries exactly.

Over the full run: 491 negative events accumulate to raw score **-172,541**, normalized
**-345.082** — 345x past the `D` grade floor (`config/simulation_quality/grade_thresholds.yaml`:
`D: -1.0`).

### 2.4 Is F a legitimate/reachable grade? (resolves an ambiguity noted in the ticket)

The ticket's own text (and the halted attempt) observed that `grade_anchors.json`'s consumer
`GRADE_ORDER = ["D","C","B","A","S"]` (`tests/simulation_quality/test_grade_regression.py:34`)
has no slot for `F`. This does **not** mean `F` is an illegitimate/unreachable grade in general —
`src/simulation_quality/quality_report.py:83` explicitly returns `"F"` for scores below the `D`
threshold, and `tests/simulation_quality/test_report.py:46` tests exactly this
(`_assign_grade(-2.0, ...) == "F"`). `F` is a real, intended grade tier; `GRADE_ORDER`'s omission
of it is specific to the **anchor-band regression tolerance mechanism** (which only needs to
express "how far are we from the intended grade," and treats "not in GRADE_ORDER" as an automatic
band-tolerance failure — appropriate, since any `F` is by definition worse than the worst
expressible anchor `D`). So `grade_anchors.json` recording `"D"` as a floor placeholder for this
run (per the STONE-GAP ticket's note) is a reasonable stopgap, not evidence that `F` itself is
architecturally impossible.

However, the **magnitude** (-345 normalized, i.e. 345x the `D` floor) is still informative: every
other severely-negative tag across all 10 pillars in `scoring_weights.yaml` is a **fixed
per-event scalar** (e.g. `conservation_violated: -50.0`, `extinction_degenerate: -50.0`,
`faction_conquest_degenerate: -40.0`, `omniscience_collapse: -20.0` — none of these scale
open-endedly with an accumulating count). `AGENCY.stasis_per_tick` is the **only** negative
weight in the entire scoring config that is multiplied by an unbounded, monotonically-growing
count with no ceiling. This is a genuine structural outlier in the scoring design, not merely a
matter of degree.

---

## 3. Fix determination (Scope item 3)

**Read `docs/mechanics/04_strategic_cognition.md` for stasis-penalty design intent, as
instructed: it does not mention `stasis`, `defer`, or the AGENCY-pillar penalty formula at all
(confirmed via full-file search — zero matches).** The stasis-penalty's only documented design
intent lives in `docs/simulation_quality/quality_scoring_contract.md` (the SimQ-specific
contract, not the Mechanics Bible), specifically the AGENCY table
(lines 548-561) and the worked pseudocode (lines 441-455) cited above.

**Conclusion: this is (b), the `AgencyScorer` stasis-penalty formula — not (a), decision logic.**

Reasoning:
- Every code path in `AdventureDecisionPhase` / `AdventureRouteGenerator` /
  `AdventureDecisionService` for entity 23 behaves **exactly as documented** in
  `docs/mechanics/adventure_routing_contract.md` (the fallback guarantee at `generator.py:164-175`
  is working as designed — it guarantees a non-empty candidate set, which it does). Nothing here
  is malfunctioning relative to its own contract. An entity that has genuinely no viable route
  for an extended period is a legitimate scenario the scoring layer must be able to grade
  gracefully — it is not automatically a decision-logic defect.
- The scoring formula, by contrast, has an internal inconsistency between its own documented
  intent ("N>5 **consecutive** ticks", implying per-entity tracking) and its own worked example's
  implementation (population-wide window count, mislabeled `consecutive`) — see §1 and §2.3. This
  is a defect in the contract's own worked example, not a deliberate, documented design choice.
- The unbounded linear growth (§2.4) is a structural outlier versus every other severe penalty
  in the same config file, and produces a magnitude (345x past the floor) that overwhelms the
  entire simulation's `AGENCY` grade because of ONE entity's legitimate (not buggy) idle state —
  directly contradicting AC6's evident intent that a 3-hero world where 2/3 entities behave well
  via `FORM_PARTY` should still be gradeable as `>= B`.

**What the Plan phase still needs to decide (not resolved here — a genuine design choice, not
a fact needing more evidence):**
- *How* to fix the formula. Two independent problems exist and either or both may need fixing:
  1. **Attribution**: `defer_count` should plausibly be a true per-entity consecutive-defer
     counter (matching documented intent) rather than a population-shared window count. Note:
     fixing *only* this, with the existing linear-uncapped formula, would make magnitude
     **worse**, not better — a genuine 500-tick per-entity streak with no window-imposed
     ceiling would compute `extra_ticks=495` at tick 500 (vs. the current window-capped
     `~144`), i.e. `delta ≈ -1486` per event instead of `-418`. Attribution and magnitude are
     separate problems; fixing attribution alone is insufficient.
  2. **Magnitude cap**: the `stasis_per_tick * extra_ticks` term needs an explicit ceiling
     (e.g. a capped `extra_ticks`, a saturating/diminishing scaling function, or a one-shot
     escalation similar to the existing `population_stasis` one-shot-fire pattern already used
     in the same scorer via `self._pop_stasis_fired`, `agency.py:29,93-104`) so a single
     persistently-idle entity cannot make the whole pillar's grade fall arbitrarily far below
     `D`.
  - `ScoringWeights.detection.time_gates` (`config/simulation_quality/detection_params.yaml`) is
    already a free-form `dict[str, int]` loaded via `weights.py:66` — an additional gate/cap
    constant (e.g. a max `extra_ticks` or a max per-event stasis delta) can be added there
    without a schema change, if that's the chosen mechanism. The exact cap value/mechanism is a
    calibration decision for Plan/Implementation, not something to guess here.
- Recommend flagging as a **separate follow-up** (not blocking this ticket, and explicitly
  excluded by this ticket's own Out of Scope: "Any other `simq_routing_test` content changes"):
  this world's resource nodes never being tagged for the heroes' `hometown` spawn region means
  **any** hero whose personality happens to roll `sociability < 0.2` is permanently unable to
  act for its entire life in this world, regardless of which fix lands here. That is a fragile
  edge case worth a world-content or generator-fallback follow-up ticket, independent of the
  scoring fix.

## Open Questions (for Plan phase — none block characterizing root cause, all block only the
exact implementation shape)

- OQ-1: Per-entity streak tracking, magnitude cap, or both? (See "what the Plan phase still needs
  to decide" above — recommend both, but the exact cap mechanism/value is a design decision.)
- OQ-2: Should the world-content gap (no resource node tagged `hometown`) be filed as a separate
  follow-up ticket now, given it's explicitly out of scope here but is the other half of why
  entity 23 has zero alternatives? Recommend yes, but not required to resolve this ticket.

No open question blocks stating the root cause or the recommended fix direction — both are
supported by direct evidence above, not guesses.

---

## 4. Test coverage inventory (Scope item 4)

Existing tests that exercise the code this fix will touch, and **will need updating** because
they currently assert the population-window semantics as correct behavior (not just incidentally
adjacent):

- `tests/simulation_quality/test_agency_scorer.py::TestDefer` (lines 91-129):
  - `test_stasis_fires_after_gate` (105-113) hard-codes `expected = defer_idle +
    stasis_per_tick * extra` using an injected `window_tags={"defer_idle": gate+extra}` — this
    directly encodes the population-window formula and will need to change if `defer_count`
    becomes a true per-entity counter and/or gets a cap.
  - `test_stasis_no_fire_before_gate` (98-103), `test_population_stasis_fires_when_no_actions`
    (115-121), `test_population_stasis_fires_only_once` (123-129) — the `population_stasis`
    one-shot tests are untouched by an AGENCY defer-attribution fix (different code path,
    `agency.py:92-104`) but should be re-run to confirm no regression.
- `tests/simulation_quality/test_timegate_penalties.py` (~lines 420-500):
  `test_stasis_N_timegate_fires_after_gate`, `test_stasis_N_timegate_not_before_gate`,
  `test_stasis_N_timegate_accumulates_linearly` (name itself asserts the current unbounded-linear
  behavior — will need to change to assert capped/bounded behavior post-fix),
  `test_population_stasis_timegate_fires_at_gate`.
- `tests/simulation_quality/test_grade_regression.py` — `GRADE_ORDER`/anchor-band mechanism
  itself does not need code changes, but `tests/simulation_quality/fixtures/grade_anchors.json`'s
  `simq_routing_test_seed456_500t.AGENCY` entry must be updated from the `"D"` placeholder to the
  true post-fix grade (ticket AC).
- `tests/simulation_quality/test_quality_hub_integration.py` — exercises `QualityHub`/
  `ScoringContext` construction generally; should be re-run since `window_tag_counts` construction
  (`quality_hub.py:170-176`) is shared plumbing across all pillars — any change there (as opposed
  to containing the fix entirely inside `AgencyScorer`'s own instance state) risks affecting
  other pillars' scorers. Recommend containing the fix inside `AgencyScorer` (it already carries
  per-entity instance state via `self._last_abandoned: dict[int, str]`, `agency.py:28` — same
  pattern extends naturally to a `self._entity_defer_streak: dict[int, int]` without touching
  `ScoringContext`'s shape).
- Adjacent but **not expected to need changes** (decision logic is not being touched per §3):
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`,
  `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`,
  `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`,
  `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`,
  `tests/perf/test_phase3_adventure_decision_budget.py`,
  `tests/unit/observability/test_event_extractor_agency.py`,
  `tests/unit/observability/test_event_extractor_agency2.py`,
  `tests/unit/social/test_party_agency.py` — run these as a smoke check only, no assertions here
  reference the stasis-penalty formula. (Minor aside: `docs/mechanics/adventure_routing_contract.md`'s
  "Regression Tests" table cites `tests_v2/test_adventure_routing.py` etc. — no `tests_v2/`
  directory exists in this repo; the doc reference appears stale/renamed. Not this ticket's scope
  to fix, noted for awareness only.)

---

## 5. Files touched by this investigation (read-only; no source changes made)

- `src/domains/adventure/phase.py`, `generator.py`, `service.py`, `scoring.py` (read)
- `src/world/providers/resources.py`, `requirements.py` (read)
- `src/simulation_quality/scorers/agency.py`, `pillar_accumulator.py`, `quality_hub.py`,
  `score_record.py` (read)
- `config/simulation_quality/detection_params.yaml`, `scoring_weights.yaml`,
  `grade_thresholds.yaml` (read)
- `docs/mechanics/adventure_routing_contract.md`, `docs/mechanics/04_strategic_cognition.md`,
  `docs/simulation_quality/quality_scoring_contract.md` (read)
- Re-ran calibration for seed456 (existing `data/calibration/simq_routing_test_seed456_500t/`
  from the halted attempt, re-verified fresh — timestamps confirm a live re-run in this pass,
  `run_1783175403_1673`); confirmed seed42 (`run_1783170615_5169`, AGENCY=A) and seed123
  (`run_1783170873_2994`, AGENCY=A) still pass. Compiled `simq_routing_test` world directly via
  `WorldCompiler.compile()` for all 3 seeds to inspect entity personality/region/resource-node
  state without needing a full calibration re-run each time.
- Per repo convention, `data/calibration/` and `data/runs/` run artifacts used for this
  investigation are local/gitignored scratch — will be cleaned per the workflow's "After Work"
  step (`rm -rf data/runs/* reports/release_proof/*`) at ticket completion, not before (Plan/
  Implementation phases will want to re-run calibration against the fix).
