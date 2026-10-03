---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
artifact_type: investigation
tags: [simulation-quality, cognition, self-model, determinism]
---

# Investigation — TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

## Current Behavior

### Event origin (self_model_updated / decision_divergence_detected)
- `self_model_updated`: emitted unconditionally, once per entity per tick, whenever
  `EntityUpdate.self_model_bundle_set is not None` on that tick's committed update
  (`src/observability/event_extractor.py:276-283`). `self_model_bundle_set` is produced
  deterministically by `SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:32-74`),
  which runs the bottom-up self-model pipeline for every alive entity, every tick — this is
  ordinary per-tick game-state derivation, not wall-clock- or timing-sensitive by itself.
- `decision_divergence_detected`: emitted per-entity-per-tick when the entity's top strategic
  concern is `danger` with `urgency > 0.7` **and** its active project kind is in
  `_NON_SURVIVAL_PROJECT_KINDS` (`src/observability/event_extractor.py:477-496`). This condition
  is re-evaluated fresh every tick from `entity.strategic.concerns`/`current_project_id` — there is
  **no "already emitted" gating set** for this event type (contrast with `_emitted_stale_leads`,
  `_emitted_social_memory`, `_emitted_contract_milestones`, which dedupe similar per-entity
  conditions elsewhere in the same file). If the mismatch (critical danger concern + entity stuck on
  a non-survival project) persists across many consecutive ticks, this event fires **every single
  tick** it persists — this is the mechanism, confirmed by reading the actual gating logic, not
  assumed.
- `SimulationEvent.event_id` defaults to `uuid.uuid4().hex` via a Pydantic `default_factory`
  (`src/observability/events.py:56`) when not explicitly passed — and `event_extractor.py` never
  passes an explicit `event_id` for either event type. So every constructed `SimulationEvent` gets a
  fresh random UUID at construction time; `event_id` is **not** derived from `(tick, entity_id,
  event_type, payload)` content.

### Delivery path (constructed once → dedup-by-id in accumulator)
- `EventExtractor.extract()` is called exactly once per tick from
  `Kernel._phase_observability` (`src/engine/kernel.py:806-818`), fed the tick's already-resolved
  `prior_state`/`self._state`/`update` — a single deterministic pass over the committed tick result,
  not re-entrant, not re-invoked mid-tick.
- `EventRecorder.record()` (`src/observability/event_recorder.py:151-223`) pushes one envelope per
  event into a `BoundedObservabilityQueue` (`src/observability/queue.py:14-84`); a single
  `QueueDrainWorker` background thread (`src/observability/event_recorder.py:96-107`,
  `src/observability/queue.py:87-154`) drains the queue and calls `quality_fn=hub.on_envelope`
  exactly once per envelope object — no retry/redelivery path exists in `QueueDrainWorker._run()`;
  a scorer exception is caught, logged, and the loop continues to the next envelope (no re-push).
  **No duplicate-delivery mechanism was found** in this path under load — each real
  `SimulationEvent` construction reaches `QualityHub.on_envelope()` exactly once.
- `PillarAccumulator.add()` (`src/simulation_quality/pillar_accumulator.py:43-58`) dedupes by
  `record.event_id` via `self._seen_event_ids`. Because each construction gets a fresh random UUID
  (see above), this dedup can only ever catch the same object flowing through twice — it does
  **not** protect against the same *logical* event being independently re-derived and
  re-constructed (e.g. by a hypothetical retry/replay path). **No such re-derivation path exists in
  the current code** — so this dedup mechanism is not, on the evidence gathered, the cause of the
  event-count blowup. It is flagged as a latent, unexercised risk in Anti-Drift Hazards below.

### Loop detection
`PillarAccumulator._check_loop_detection()` (`pillar_accumulator.py:60-70`) is a pure function of
`window_buffer` (last 200 `ScoreRecord`s, `window_size` from `config/simulation_quality/detection_params.yaml`):
any tag occupying `> loop_threshold` (0.70) of the window trips `loop_flags`. This logic is correct
and deterministic **given its inputs** — it is not the source of nondeterminism; it faithfully
reports whatever event stream it is fed.

### Root-cause chain for the observed anomaly (`event_count` 2→119, `raw_score` 11.0→3521.0)
Two independent, compounding causes were found — **not one**:

1. **F6 (confirmed, load-sensitive, out of scope to fix — matches ticket's Out of Scope)**:
   `src/engine/kernel.py`'s end-of-tick watchdog (`kernel.py:420-442`) and mid-tick emergency
   throttle (`kernel.py:574-601`) both gate on `time.perf_counter_ns()` wall-clock elapsed time, not
   simulated tick count. Under the sweep's ~30 min of sustained concurrent load, more
   resolution-queue items get dropped per tick than in a clean/idle run
   (`self._status.record_dropped_work(...)`, `kernel.py:582`, forces `RuntimeMode.DEGRADED`). An
   entity whose resolution work is dropped on a tick where its `danger` concern is critical does not
   get to act on it that tick; the mismatch (danger concern unresolved + still on a non-survival
   project) persists into the next tick, and `decision_divergence_detected` — which has no
   "already-emitted" gate — fires again. Repeated over many ticks under sustained load, this is a
   fully plausible, evidence-consistent mechanism for a real, non-fabricated jump from 2 to ~117-119
   distinct `decision_divergence_detected`/`self_model_updated` events for the same scenario/seed.
   This is the same mechanism as D06 F6 (`docs/audits/D06_longrun_health.md` §F6) — not a new one.
   `urban_political_seed123_500t` is 500 ticks, past F6's documented ~tick 300-320 onset threshold,
   so temporal eligibility is confirmed (see Risks — the anchor is a `FAST_ANCHOR_KEYS` entry, not
   previously tested against F6; see below).

2. **New, load-independent, always-present bug discovered this session — `ScoringWeights` flat rule-key
   collision (`src/simulation_quality/weights.py:26-33`, `91-98`)**: `ScoringWeights._build_flat_index()`
   flattens **all 10 pillars'** `pillar_rules` into a single, pillar-unaware `_flat_rules` dict keyed
   only by rule name; `__getitem__` (`weights.py:91-98`) reads from this single flat namespace. Any
   rule-key name reused across two pillar sections in `config/simulation_quality/scoring_weights.yaml`
   silently collapses to whichever pillar is declared **later** in the YAML (Python dict insertion
   order: COGNITION → AGENCY → COMBAT → FACTION → ECONOMY → PROGRESSION → SOCIAL → INFORMATION →
   WORLD → NARRATIVE — later entries overwrite earlier ones for the same key). Confirmed 7 colliding
   keys exist today:
   - `subjective_divergence`: COGNITION declares `5.0` (`scoring_weights.yaml:3`), INFORMATION
     declares `30.0` (`scoring_weights.yaml:137`) — **INFORMATION wins globally**. Every
     `decision_divergence_detected` event scored by `CognitionScorer` (`scorers/cognition.py:104-108`,
     which reads `self.weights["subjective_divergence"]`) is actually scored at **30.0**, not the
     5.0 declared under its own COGNITION section — a **6x silent amplification**.
   - `belief_active`: COGNITION `2.0` vs INFORMATION `10.0` (5x amplification of COGNITION's
     `belief_active` scoring, `scorers/cognition.py:66`).
   - `knowledge_rot`: COGNITION `-3.0` vs INFORMATION `-2.0`.
   - `omniscience_collapse`: COGNITION `-20.0` vs INFORMATION `-20.0` (identical value — no visible
     symptom, but same latent collision).
   - `ecology_cycling`, `ecology_broken`, `knowledge_economy_active`: ECONOMY vs WORLD/INFORMATION
     collisions (ECONOMY's own carefully-recalibrated values are silently overridden).
   - Confirmed via direct YAML parse (`python3 -c "import yaml; ..."` cross-referencing every pillar
     section) — this is not a hypothesis, the collisions are real and present in the committed
     config today.
   - **This bug was newly exacerbated (not introduced from scratch, but made 6x worse) by
     `TCK-20260713-SIMQ-SCORE-CEILING-FIX`** (`git show 5c51dca2 -- config/simulation_quality/scoring_weights.yaml`):
     pre-fix, INFORMATION's `subjective_divergence` was `6.0` (close to COGNITION's `5.0` — mild,
     easy-to-miss collision); SCORE-CEILING-FIX's independent per-pillar ×5 rescale raised it to
     `30.0` without any pillar-cross-check, since each pillar was rescaled in isolation against its
     own richest-observed-scenario denominator. **This directly contradicts this ticket's own Request
     Summary claim** ("confirmed NOT caused by SCORE-CEILING-FIX's diff... touches zero
     COGNITION-related code, weights, or config") — the diff did not touch COGNITION's own YAML
     section, but it did touch a config value that collides with and silently overrides a COGNITION
     rule under the existing flat-index design. Flagged prominently in Risks/Open Questions below —
     this is a correction to the ticket's stated assumption, not an assumption I am making.
   - Math check: 119 events × ~30.0 (dominant `subjective_divergence` weight) ≈ 3570, closely
     matching the observed `raw_score=3521.0` (a mix of `self_model_active`=1.0 events and
     `subjective_divergence`=30.0 events, consistent with ~117 divergence events + ~2 self-model
     events). Had the collision not existed (i.e. at the intended 5.0), the same 119-event count
     would have produced raw_score ≈ 595-600 — still a real anomaly (correctly flagged by
     `_check_loop_detection`), but nowhere near as visually alarming as 3521, and the `grade=S`
     outcome specifically depends on the inflated magnitude crossing the S threshold.

### Baseline confirmation
`tests/simulation_quality/fixtures/grade_anchors.json`'s `urban_political_seed123_500t.COGNITION`
entry: `{"grade": "B", "score": 0.088}` (normalized_score, not raw_score — confirmed the ticket's
cited `raw_score=11.0`/`event_count=2` are consistent: `0.088 = 11.0 / 125`, where `125 =
floor_tick = max(1, 500 // 4)` per `QualityReportBuilder.build`'s denominator rule,
`src/simulation_quality/quality_report.py:94-104`).

**`urban_political_seed123_500t` is a `FAST_ANCHOR_KEYS` entry**
(`tests/simulation_quality/test_grade_regression.py:70`), **not** a `SLOW_ANCHOR_KEYS` entry — this
matters (see Risks): `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` explicitly scoped its 3-trial
re-verification sweep to the 18 `SLOW_ANCHOR_KEYS` (1000t/2000t) only and explicitly excluded all
`FAST_ANCHOR_KEYS` (200t/500t) with the stated rationale that F6's divergence mechanism "was only
observed to matter past ~tick 300-320" and fast anchors were assumed not to reach that far — but
500 > 320, so this specific anchor was never actually tested against the assumption that excluded
it. This ticket is the first evidence-driven test of that boundary assumption.

## Mechanics / Engine Constraints
- `docs/engine/kernel.md` §"Emergency Throttling" (lines 66-70): documents the exact two-step
  behavior read in `kernel.py:420-442`/`574-601` — DEGRADED transition + dropped resolution-queue
  work + logged warning. Confirmed source matches doc exactly.
- `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor" (lines 65-77): documents
  the broader `PhaseBudgetGovernor` mechanism (`candidate_budget`, `movement_budget`,
  `strategic_budget`, `scan_policy`, etc.) that F6's watchdog/throttle is one instrument of.
  Confirmed this is a documented, load-adaptive, intentional degradation path, not a bug in itself.
- `docs/mechanics/04_strategic_cognition.md` does not currently document the self-model
  `subjective_divergence`/loop-detection SimQ-scoring mechanism at all (it is a SimQ observability
  concept, not a gameplay law) — the one directly relevant passage found is the belief-decay
  mechanism (§ line 78, `stale_threshold=50` in `BeliefCycleSystem.decay_stale_beliefs`), unrelated
  to this ticket's symptom. **Gap noted, not fabricated**: no Mechanics Bible chapter directly
  governs SimQ's own scoring-weight correctness — that is a test/tooling correctness concern
  (`src/simulation_quality/`), not a simulation-law concern, so no Mechanics Bible update is implied
  by fixing either finding.
- `docs/guidelines/intentional_divergences.md` §2.25 (`self_model_bundle_set` Durable Materialization
  — TCK-20260703-SIMQ-UPLIFT3-BRANCH-B): confirms `self_model_updated`'s underlying data
  (`entity.self_model`) is genuinely durable and deterministic given tick state — no fresh
  load-sensitivity concern discovered there.
- **Discrepancy found**: this ticket's Related Docs claims F6 is "recorded permanently in
  `docs/guidelines/intentional_divergences.md`" — searched the full file; **no dedicated numbered
  entry for F6 exists there** (only an incidental cross-reference at line 501, inside unrelated
  entry §2.30). F6 is fully documented in `docs/audits/D06_longrun_health.md` §F6 and referenced
  from `kernel.md`/`performance_contract.md`, but not in `intentional_divergences.md` itself. Minor
  documentation-accuracy gap, not blocking, flagged for awareness.

## Parity Ledger Overlap
- **No parity ledger entry directly covers this symptom.** Searched all 8 `docs/parity_ledger/*.yaml`
  files for `self_model`/`subjective_divergence`/`loop_detect`/`determinis`/`watchdog`/`throttle`/
  `hash` text overlap. Hits are either unrelated (`strategic_cognition.yaml`'s
  `test_cognition_graph_deterministic_simulation`, `test_intel_capacity_determinism` — different
  subsystems) or infrastructure-level replay-hash entries (`infrastructure.yaml` — replay/hash
  determinism for gameplay state, not SimQ's own scoring-tool correctness).
- This makes sense: `src/simulation_quality/` is a scoring/observability **tool that measures** the
  simulation, not gameplay logic itself — the Mechanics Bible / parity ledger track simulation laws,
  not the correctness of the SimQ scoring harness. **No parity ledger entry needs updating as a
  result of this investigation** — neither the F6 event-count finding (kernel behavior, unchanged,
  out of scope) nor the weights.py collision (SimQ-tooling-local) is a gameplay-law divergence.
  Confirm this holds at Implement time if either finding's fix touches `src/cognition/` or
  `src/engine/kernel.py` in an unexpected way (it should not, per Scope).

## Prior Work
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — direct precedent. Re-ran all 18
  `SLOW_ANCHOR_KEYS` 3x each under real throttled `Kernel`; found all 18/18 grade-stable within the
  existing ±1-band despite confirmed throttle-timing variance (`budget_warnings` 41-539/run,
  `watchdog_trips` 1-3/run). Established the "stable / converted-to-tolerance / flagged-unverified"
  reliability-status vocabulary and the `test_generated_frontier_3_42_extended_population_stability`
  tolerance-guard pattern this ticket's AC explicitly asks to reuse if root cause is F6. Explicitly
  excluded `FAST_ANCHOR_KEYS` (200t/500t) including `urban_political_seed123_500t` from its sweep.
  **Important**: that ticket's `_within_band` check (grade-only, ±1 letter) predates
  `test_grade_within_anchor_band`'s current `_within_score_tolerance` check (added by
  `TCK-20260713-SIMQ-RAWSCORE-PERSIST`, same commit batch as SCORE-CEILING-FIX) — the newer,
  stricter score-magnitude tolerance (`abs_floor=0.05`, `rel_pct=0.20`) did not exist when
  ANCHOR-RELIABILITY-VERIFY established its "stable" classifications, so its precedent should be
  read as "grade-band stable," not "score-tolerance stable."
- `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` (done) — originated F6, established
  the "run twice back-to-back, same seed/code/machine" instrumented-drive methodology and the
  tolerance-guard test pattern (`test_generated_frontier_3_42_extended_population_stability`,
  `tests/unit/worldassembly/test_corpus_diversity.py:289-374`) this ticket's Scope explicitly points
  to as the template.
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done, same session, immediately prior commit) — recalibrated
  WORLD/ECONOMY/PROGRESSION/INFORMATION per-event weights independently, per-pillar, against each
  pillar's own richest-observed-scenario denominator. Did not check for or account for the shared
  flat rule-key namespace in `weights.py`, which is what turned INFORMATION's `subjective_divergence`
  rescale into a silent 6x amplification of COGNITION's own declared weight for the same key name.
  This ticket's own Request Summary — written at the end of that same session — asserts SCORE-CEILING-FIX
  is unrelated based on a diff review that only checked whether COGNITION's *own* YAML section or
  *any COGNITION-labeled* code changed; it did not check for cross-pillar key collisions, which is
  exactly the mechanism found here.
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` (done) — fixed `self_model_bundle_set` durable materialization
  (`intentional_divergences.md` §2.25); confirms `self_model_updated`'s data path is real and
  deterministic, ruling it out as an independent nondeterminism source.

## Risks and Open Questions
1. **Open question requiring a decision (blocks fix scope, not investigation)**: the weights.py
   flat-index collision is a real, load-independent bug distinct from this ticket's stated Scope
   ("load-sensitive nondeterminism... in the COGNITION self-model loop-detection path"). It is not
   itself the cause of the *event-count* explosion (that traces to F6/decision_divergence_detected
   firing more under load) but it **does** explain why the anomalous run's *raw_score magnitude*
   (3521 vs. an expected ~595-600 at the correct weight) looks so extreme, and it silently affects
   **every** run of every scenario that emits COGNITION `subjective_divergence` or `belief_active`
   events, all the time — not just this one anchor, not just under load. Fixing it is out of this
   ticket's literal Scope (which is about the loop-detection *nondeterminism*, not general
   scoring-weight correctness) but leaving it unfixed/unreported would violate "no known material
   gap is left unstated." **Recommend**: report this as a separate, new P1/P2 ticket
   (`src/simulation_quality/weights.py` pillar-namespace collision — affects 7 confirmed key pairs
   across COGNITION/INFORMATION/ECONOMY/WORLD) rather than silently folding a `weights.py`/global-config
   fix into this ticket, since fixing it would legitimately change scoring for **every** anchor that
   has any of the 7 colliding keys, a much larger blast radius than this ticket's stated scope. This
   must be decided by the orchestrator/planner, not assumed.
2. This ticket's own Related Tickets/Out of Scope text asserts SCORE-CEILING-FIX's diff is "confirmed
   unrelated." Investigation found that assertion is **incomplete**: the diff did not touch
   COGNITION's code or its own declared weight, but it did touch a shared-namespace config value that
   changes what COGNITION's scorer actually reads at runtime. This does not invalidate the ticket's
   Scope (F6 is still independently confirmed as a real, evidence-consistent driver of the
   event-count anomaly), but the magnitude of the observed anomaly (`grade=S`, `raw_score=3521`) is
   not attributable to F6 alone — it is F6 (event count) **compounded by** the weights collision
   (per-event magnitude). Both must be named in whatever gets written up at Implement/Finalize time;
   do not describe this as "F6 alone" without qualification.
3. Genuinely could not obtain the anomalous sweep's raw `quality_report.json` or a saved per-tick log
   — no artifact from `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s Step 12 live-mode sweep was found under
   `stored_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/` (only `investigation.md`/`plan.md`/
   `test_plan.md` exist there, no raw run data) or anywhere under `docs/simulation_quality/`. The
   119-event, 3521-raw_score, `loop_detected=True` figures are taken as given from this ticket's own
   Request Summary text (presumed transcribed accurately from the original sweep's terminal
   output/log at the time) — **not independently re-verified against a saved artifact**. If a
   controlled repro (AC #2) does not reproduce a comparable magnitude, this is the first place to
   re-check.
4. `urban_political_seed123_500t` sits right at F6's documented "first watchdog trip ~tick 300-320"
   boundary (500 > 320, but not by a wide margin — unlike the 1000t/2000t `SLOW_ANCHOR_KEYS` that
   `ANCHOR-RELIABILITY-VERIFY` tested, which have 3-7x more tick-runway past the boundary). A
   controlled repro should explicitly check whether this anchor's throttle engagement is marginal
   (a few watchdog trips near the end) or substantial (many trips, consistent with the ticket's
   described 30-min sustained-load sweep) — this affects whether a tolerance-guard's floor/ceiling
   should be tight or wide.
5. `ENABLE_SELF_MODEL_COGNITION` gating: not confirmed in this investigation which profile/flag
   combination `urban_political_seed123_500t`'s calibration run uses. If self-model cognition is off
   by a runtime flag for some corpus profiles, `self_model_updated` would never fire regardless of
   load — worth a quick confirmation at Implement time via the actual calibration invocation/profile
   config, not assumed here.

## Anti-Drift Hazards
- **Do not "fix" `event_id` to be content-derived (deterministic hash of tick/entity/event_type/payload)
  as a side effect of this ticket** without confirming it is actually needed — it is a real design
  smell (defeats `PillarAccumulator`'s dedup-by-id intent against any future retry/replay path) but
  is not the confirmed cause of this specific symptom. Changing it touches every `SimulationEvent`
  construction path repo-wide (`event_recorder.py:134-147`'s stream-republish path reconstructs a
  `SimulationEvent` with an explicit `event_id=envelope.event_id` — a deterministic `event_id` scheme
  would need to preserve round-trip equality there too). Out-of-scope scope-creep risk; flag, don't fix,
  unless the repro specifically implicates it.
- **Do not touch `kernel.py`'s watchdog/throttle logic anywhere** — hard Out of Scope, already
  litigated by the precedent ticket, restated here as a hazard because the natural instinct when
  looking at `decision_divergence_detected`'s missing "already-emitted" gate is to think "add a
  per-entity cooldown like the other event types have" — that would change gameplay-observable SimQ
  event semantics for *all* runs (not just throttled ones), a much bigger behavior change than this
  ticket's Scope, and is a distinct design decision from "guard the anchor against throttle variance."
  If a per-entity cooldown for `decision_divergence_detected` is later proposed, it needs its own
  ticket and its own blast-radius review (D06 F3's rejection-cascade precedent shows this event family
  is already sensitive to "unbounded per-tick re-fire" concerns).
- **Do not silently fix the `weights.py` collision as part of this ticket's diff** (see Risk #1) — it
  would change scoring for every anchor with a colliding key, not just this one, which is out of this
  ticket's stated blast radius and would invalidate committed anchors this ticket does not intend to
  touch.
- **Do not conflate `urban_political_seed123_500t` (FAST_ANCHOR_KEYS) with the 18 already-verified
  SLOW_ANCHOR_KEYS** — `ANCHOR-RELIABILITY-VERIFY`'s "18/18 stable" result says nothing about this
  key; it was explicitly excluded. Do not cite that prior result as if it already covers this anchor.
- If a tolerance-guard conversion is chosen (F6-confirmed path), follow
  `test_generated_frontier_3_42_extended_population_stability`'s exact shape (multi-trial averaging,
  real throttled `Kernel`, no `audit_mode`) — do not invent a new pattern; test_plan.md below details
  the concrete adaptation for a *grade/score* guard rather than a *population* guard.
