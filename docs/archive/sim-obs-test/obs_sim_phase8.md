---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 8 Implementation Plan — Advanced Simulation Understanding

Phase 8 should **not add more infrastructure**.

By now, previous phases already gave you:

- metrics
- logs
- semantic events
- run artifacts
- post-run analysis
- multi-run baseline
- live inspection
- optional storage/streaming
- dashboard/search/alerting

Phase 8 should focus on this question:

> The system detected something strange.
> Can it explain what probably happened, why it matters, and where engineers should investigate?

The final feasibility roadmap already warns us to keep implementation staged and avoid jumping into heavy external systems too early. So Phase 8 should improve **simulation understanding**, not add more platform complexity.

---

# Phase 8 Goal

## Main objective

Move from:

> anomaly detection

to:

> anomaly interpretation + balance diagnosis + investigation guidance

The system should begin answering:

- Is this a real bug or just unusual behavior?
- Is this a balance issue or logic issue?
- Which subsystem likely caused it?
- Which entities/resources/quests/factions are involved?
- What evidence supports the conclusion?
- What should developers inspect first?
- Did this happen in one seed or many seeds?
- Is this trend getting worse compared to baseline?

---

# Phase 8 Should Include

- Domain analyzer framework
- Scenario expectation packs
- Root-cause hypothesis engine
- Balance diagnosis engine
- Story / emergent behavior detector
- Human review workflow
- Analyzer quality evaluation
- Baseline evolution policy

---

# Phase 8 Should Not Include Yet

- ML-based anomaly detection
- automatic stat tuning
- automatic code fixing
- auto-healing simulation behavior
- complex designer UI
- full natural-language explanation engine
- replacing deterministic rules with black-box models

Keep it explainable and rule-based first.

---

# Phase 8 Milestones

1. **Milestone 42 — Domain Analyzer Framework**
2. **Milestone 43 — Scenario Expectation Packs**
3. **Milestone 44 — Root-Cause Hypothesis Engine**
4. **Milestone 45 — Balance Diagnosis Engine**
5. **Milestone 46 — Emergent Story Detector**
6. **Milestone 47 — Human Review and Labeling Workflow**
7. **Milestone 48 — Analyzer Quality and Baseline Evolution**

---

# Milestone 42 — Domain Analyzer Framework

## Goal

Create a clean structure for domain-specific simulation understanding.

Instead of putting all logic into one giant analyzer, split analysis by domain:

- movement
- economy
- combat
- quest
- strategy
- faction/region
- lifecycle
- runtime/performance

---

## Why this matters

Current anomaly rules may detect things like:

- `NavigationStuck`
- `QuestStalled`
- `ResourceProductionZero`
- `GovernorDegradedTooLong`

But we need deeper interpretation.

Example:

> 200 workers are stuck.

A movement analyzer should ask:

- Are they near the same tile?
- Are they targeting the same resource?
- Is the target depleted?
- Is there an occupancy bottleneck?
- Is pathing failing?
- Are they repeatedly choosing the same impossible target?

---

## Components

- `DomainAnalyzer`
- `DomainAnalysisContext`
- `DomainAnalysisResult`
- `DomainAnalyzerRegistry`
- `DomainEvidenceBundle`
- `DomainSignalRequirement`

---

## Domain analyzer interface

Each analyzer should declare:

- domain name
- required events
- required metric windows
- optional signals
- supported scenario types
- output findings
- skipped reason if signals are missing

Example domains:

| Analyzer                 | Purpose                                                |
| ------------------------ | ------------------------------------------------------ |
| `MovementDomainAnalyzer` | stuck entities, crowding, oscillation, path failure    |
| `EconomyDomainAnalyzer`  | resource flow, gold circulation, shop/storage loops    |
| `CombatDomainAnalyzer`   | engagement duration, kill rate, faction imbalance      |
| `QuestDomainAnalyzer`    | stalled quests, reward delays, objective impossibility |
| `StrategyDomainAnalyzer` | project churn, unresolved blockers, goal instability   |
| `RuntimeDomainAnalyzer`  | governor pressure, memory trend, event drops           |

---

## Tasks

### 42.1 Define domain analyzer interface

Checklist:

- [ ] Analyzer has stable `domain_id`.
- [ ] Analyzer declares required signals.
- [ ] Analyzer declares optional signals.
- [ ] Analyzer supports scenario-type filtering.
- [ ] Analyzer returns findings, not raw strings.
- [ ] Analyzer can return `SKIPPED_MISSING_SIGNAL`.

Acceptance:

- [ ] Analyzer registry can run multiple domain analyzers.
- [ ] Missing data does not crash analysis.
- [ ] Analyzer output is deterministic.

---

### 42.2 Implement analyzer registry

Checklist:

- [ ] Register analyzers by domain.
- [ ] Run analyzers in stable order.
- [ ] Collect results.
- [ ] Track skipped analyzers.
- [ ] Track analyzer runtime.
- [ ] Report analyzer failures safely.

Acceptance:

- [ ] Registry can run all enabled analyzers.
- [ ] Failed analyzer is reported without corrupting report generation.
- [ ] Analyzer runtime appears in analysis summary.

---

### 42.3 Implement minimal domain analyzers

Start with only four:

- `MovementDomainAnalyzer`
- `EconomyDomainAnalyzer`
- `QuestDomainAnalyzer`
- `RuntimeDomainAnalyzer`

Do not implement combat/strategy/faction deeply yet.

Minimum outputs:

- findings
- evidence
- suspected subsystem
- suggested investigation
- confidence level

Acceptance:

- [ ] Movement analyzer can summarize stuck events.
- [ ] Economy analyzer can summarize production zero or gold stagnation.
- [ ] Quest analyzer can summarize stalled quests.
- [ ] Runtime analyzer can summarize degraded governor/event drops.

---

## Finding model

Each finding should include:

- `finding_id`
- `domain`
- `severity`
- `title`
- `summary`
- `affected_entities`
- `affected_regions`
- `affected_resources`
- `affected_quests`
- `evidence`
- `suspected_causes`
- `confidence`
- `recommended_next_steps`

---

## Tests

Recommended files:

- `tests/unit/observability/test_domain_analyzer_registry.py`
- `tests/unit/observability/test_movement_domain_analyzer.py`
- `tests/unit/observability/test_economy_domain_analyzer.py`
- `tests/integration/observability/test_domain_analysis_flow.py`

Required checks:

- [ ] Analyzer registry runs analyzers.
- [ ] Missing signals produce skipped status.
- [ ] Movement stuck events produce movement finding.
- [ ] Economy freeze metrics produce economy finding.
- [ ] Findings include evidence and next steps.

---

## Completion checklist

- [ ] Domain analyzer interface exists.
- [ ] Registry exists.
- [ ] Four minimal analyzers exist.
- [ ] Analyzer results appear in report.
- [ ] Missing signals are visible, not hidden.

> [!NOTE]
> **Milestone 42 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Architecture:** All Phase 8 understanding components live under `src/observability/understanding/` — a clean new subpackage that is entirely post-run and never touches the simulation tick path.
> * **Domain analyzer interface:** Abstract `DomainAnalyzer` base class in `src/observability/understanding/domain/base.py`. Each concrete analyzer declares `domain_id`, `required_signals`, `optional_signals`, and `supported_scenario_types`. Returns `DomainAnalysisResult` which contains a list of typed `DomainFinding` records.
> * **4 analyzers implemented:** `MovementDomainAnalyzer`, `EconomyDomainAnalyzer`, `QuestDomainAnalyzer`, `RuntimeDomainAnalyzer` in their respective domain files.
> * **Registry:** `DomainAnalyzerRegistry` in `src/observability/understanding/domain/base.py` — runs analyzers in stable sorted order, captures per-analyzer runtime, logs skipped and failed analyzers without propagating exceptions.
> * **Pipeline integration:** `UnderstandingPipeline` in `src/observability/understanding/pipeline.py` orchestrates the full M42–M48 flow and saves both JSON and markdown reports per run.
> * **Missing signals:** If required events are absent, analyzer returns `status="SKIPPED_MISSING_SIGNAL"` with an explicit reason string. Never silently hides the gap.
> * **Verification Tests:** `tests/unit/observability/test_domain_analyzer_registry.py` and `tests/unit/observability/test_movement_domain_analyzer.py` / `test_economy_domain_analyzer.py`.

---

# Milestone 43 — Scenario Expectation Packs

## Goal

Define what “normal” means for each scenario type.

This is the first serious step toward balance understanding.

---

## Problem

The same behavior can be good or bad depending on scenario.

Example:

| Behavior          | Peaceful village | Combat arena                   |
| ----------------- | ---------------- | ------------------------------ |
| High combat rate  | bad              | expected                       |
| Zero combat       | expected         | bad                            |
| High death rate   | bad              | maybe expected                 |
| Resource shortage | bad              | maybe expected in survival     |
| Faction collapse  | bad              | maybe expected in war scenario |

So the analyzer needs scenario context.

---

## Components

- `ScenarioExpectationPack`
- `ExpectationPackLoader`
- `ExpectationRule`
- `ExpectationResult`
- `ExpectationPackRegistry`

---

## Initial scenario types

Start with:

- `resource_economy`
- `combat_heavy`
- `mixed_sandbox`
- `peaceful_village`

Do not define every possible scenario yet.

---

## Expectation pack structure

Each pack should define:

- scenario type
- expected activity level
- allowed anomaly types
- hard fail conditions
- warning thresholds
- ignored/acceptable behaviors
- required signals
- version

Example expectations:

### `resource_economy`

- hard law violations must be zero
- resource production should not remain zero for long windows
- stuck worker ratio should stay below threshold
- inventory-full duration should not dominate
- combat can be low

### `combat_heavy`

- combat should occur within early window
- engagements should eventually resolve
- one faction should not dominate too fast unless configured
- zero damage for long engagement is suspicious
- resource economy metrics may be lower priority

### `peaceful_village`

- high death rate is suspicious
- high combat rate is suspicious
- resource circulation should exist
- quest completion should progress slowly but consistently

---

## Tasks

### 43.1 Define expectation pack schema

Checklist:

- [ ] Define scenario type.
- [ ] Define pack version.
- [ ] Define hard fail expectations.
- [ ] Define warning expectations.
- [ ] Define acceptable anomaly types.
- [ ] Define ignored metrics.
- [ ] Define required signals.

Acceptance:

- [ ] Valid expectation pack loads.
- [ ] Invalid pack fails with clear error.
- [ ] Pack version is recorded in report.

---

### 43.2 Implement loader

Start with JSON or YAML, whichever is easier for the project.

Recommended path:

- JSON first for implementation simplicity
- YAML support later if needed

Checklist:

- [ ] Load pack by scenario type.
- [ ] Validate schema.
- [ ] Provide default pack if missing.
- [ ] Report missing pack clearly.

Acceptance:

- [ ] `resource_economy` pack loads.
- [ ] `combat_heavy` pack loads.
- [ ] Unknown scenario type uses default or explicit error.

---

### 43.3 Integrate with analyzer pipeline

Checklist:

- [ ] Analysis context includes expectation pack.
- [ ] Rule engine can access expectations.
- [ ] Domain analyzers can access expectations.
- [ ] Report shows active expectation pack.
- [ ] Skipped expectations are listed.

Acceptance:

- [ ] Same anomaly can have different severity by scenario type.
- [ ] Report explains which expectation pack was used.

---

### 43.4 Add minimal expectation packs

Implement only four packs:

- `resource_economy`
- `combat_heavy`
- `mixed_sandbox`
- `peaceful_village`

Each pack should contain only core thresholds first.

Do not overfill the packs.

Acceptance:

- [ ] Each pack has hard law expectation.
- [ ] Each pack has at least three domain expectations.
- [ ] Packs can be expanded later without changing analyzer code.

---

## Tests

Recommended files:

- `tests/unit/observability/test_expectation_pack_loader.py`
- `tests/unit/observability/test_expectation_pack_schema.py`
- `tests/integration/observability/test_expectation_pack_analysis.py`

Required checks:

- [ ] Valid pack loads.
- [ ] Invalid threshold rejected.
- [ ] Scenario type resolves correct pack.
- [ ] Missing pack handled clearly.
- [ ] Expectation pack changes anomaly severity.

---

## Completion checklist

- [ ] Expectation pack schema exists.
- [ ] Loader exists.
- [ ] Four initial packs exist.
- [ ] Analyzer pipeline uses active pack.
- [ ] Report shows expectation pack and expectation results.

> [!NOTE]
> **Milestone 43 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `ScenarioExpectationPack` and `ExpectationRule` (Pydantic models) in `src/observability/understanding/expectations/models.py`. `ExpectationPackLoader` in `src/observability/understanding/expectations/loader.py`.
> * **4 initial packs implemented:** `resource_economy`, `combat_heavy`, `mixed_sandbox`, `peaceful_village` — loaded from embedded JSON data (no external files needed) with a clear `DEFAULT` fallback for unknown scenario types.
> * **Schema validation:** Each pack is Pydantic-validated on load. `pack_version` is required. Invalid threshold types fail with a clear Pydantic error.
> * **Context integration:** `DomainAnalysisContext` in `src/observability/understanding/context.py` carries the active `ScenarioExpectationPack`. Both the `DomainAnalyzerRegistry` and `BalanceDiagnosisEngine` use `ctx.expectation_pack` to adjust severity thresholds per scenario type.
> * **Report visibility:** `UnderstandingPipeline` records `active_expectation_pack` and `skipped_expectations` in the final understanding report.
> * **Verification Tests:** `tests/unit/observability/test_expectation_pack_loader.py` — covers valid pack loading, version recording, minimum domain expectation counts, and the `DEFAULT` fallback path.

---

# Milestone 44 — Root-Cause Hypothesis Engine

## Goal

Generate possible causes for anomalies using rule-based evidence.

This is not automatic proof. It is a ranked hypothesis system.

---

## Important mindset

The system should not say:

> This is definitely caused by X.

It should say:

> The evidence suggests likely causes: X, Y, Z.

---

## Example

Anomaly:

> Resource production dropped to zero.

Evidence:

- active workers > 300
- many workers are stuck
- top target resource node is depleted
- inventory full ratio is high
- shop transaction rate is zero

Hypotheses:

1. Workers keep selecting depleted nodes.
2. Resource target invalidation is stale.
3. Inventory full loop prevents harvesting.
4. Shop/storage return loop is broken.
5. Pathing/crowding prevents workers from reaching nodes.

---

## Components

- `RootCauseHypothesis`
- `RootCauseEngine`
- `HypothesisRule`
- `EvidencePattern`
- `HypothesisRanker`

---

## Hypothesis model

Fields:

- `hypothesis_id`
- `title`
- `domain`
- `confidence`
- `supporting_evidence`
- `contradicting_evidence`
- `related_anomalies`
- `suggested_files_or_systems`
- `recommended_checks`

---

## Confidence levels

Use simple levels first:

- `LOW`
- `MEDIUM`
- `HIGH`

Do not use fake precision like `0.873`.

---

## Tasks

### 44.1 Define hypothesis rules

Start with rule-based patterns.

Example:

**Hypothesis: stale resource target selection**

Triggers when:

- resource production zero
- many entities target same resource node
- that node is depleted
- movement events show repeated approach attempts

Suggested checks:

- resource scorer
- active resource node index
- dirty invalidation for resource nodes
- target reselection logic

Checklist:

- [ ] Define hypothesis rule shape.
- [ ] Define required evidence.
- [ ] Define confidence scoring.
- [ ] Define recommended checks.

Acceptance:

- [ ] Hypothesis can be generated from anomaly + evidence.
- [ ] Missing evidence lowers confidence instead of failing.

---

### 44.2 Implement initial hypothesis set

Start with only these:

1. `StaleResourceTargetSelection`
2. `MovementBottleneckOrOccupancyCrowding`
3. `InventoryFullReturnLoopBroken`
4. `QuestObjectiveImpossible`
5. `GovernorPressureFromObservabilityOrWorkDebt`
6. `CombatEngagementCannotResolve`

Acceptance:

- [ ] Each hypothesis has clear evidence requirements.
- [ ] Each hypothesis has recommended investigation points.
- [ ] Hypotheses appear in report.

---

### 44.3 Add hypothesis ranking

Simple ranking:

- hard evidence match = high
- partial evidence match = medium
- weak signal match = low
- contradicted by evidence = suppress or low

Checklist:

- [ ] Sort hypotheses by confidence.
- [ ] Show top 3 per anomaly cluster.
- [ ] Include evidence summary.

Acceptance:

- [ ] Report shows likely causes in stable order.
- [ ] Contradicted hypothesis is not ranked high.

---

## Tests

Recommended files:

- `tests/unit/observability/test_root_cause_engine.py`
- `tests/unit/observability/test_hypothesis_rules.py`
- `tests/integration/observability/test_root_cause_report_integration.py`

Required checks:

- [ ] Resource freeze + depleted target produces stale target hypothesis.
- [ ] Stuck cluster produces movement bottleneck hypothesis.
- [ ] Quest stalled produces quest impossible hypothesis.
- [ ] Missing evidence produces lower confidence.
- [ ] Hypotheses appear in report.

---

## Completion checklist

- [ ] RootCauseEngine exists.
- [ ] Hypothesis model exists.
- [ ] Six initial hypotheses exist.
- [ ] Hypotheses are evidence-based.
- [ ] Report includes ranked likely causes.

> [!NOTE]
> **Milestone 44 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `RootCauseEngine`, `RootCauseEngineResult`, and `HypothesisRule` (ABC) in `src/observability/understanding/rootcause/engine.py`. Concrete rule implementations in `src/observability/understanding/rootcause/rules.py`.
> * **6 hypotheses implemented (exactly as specified):** `StaleResourceTargetSelection`, `MovementBottleneckOrOccupancyCrowding`, `InventoryFullReturnLoopBroken`, `QuestObjectiveImpossible`, `GovernorPressureFromObservabilityOrWorkDebt`, `CombatEngagementCannotResolve`.
> * **Confidence model:** Uses three explicit levels `LOW`/`MEDIUM`/`HIGH` (no fake float precision). Each rule maps evidence match cardinality to confidence: ≥3 corroborating anomalies → `HIGH`, ≥1 → `MEDIUM`, threshold miss → `LOW` or no-hypothesis.
> * **Ranking:** Results are sorted descending by confidence, with a configurable `top_n` limit (default 3 per call). Contradicting evidence lowers confidence but doesn't suppress hypotheses entirely.
> * **Safety:** A crashing rule is caught, logged, and skipped. The engine never lets a single bad rule break the report.
> * **Verification Tests:** `tests/unit/observability/test_root_cause_engine.py` — 22 tests covering all 6 rule classes plus engine-level ranking, crash isolation, serialization, and empty-context edge case.

---

# Milestone 45 — Balance Diagnosis Engine

## Goal

Identify whether a scenario seems balanced, unstable, too easy, too hard, too inactive, or too chaotic.

---

## Difference from anomaly detection

Anomaly detection asks:

> Did something suspicious happen?

Balance diagnosis asks:

> Does the overall simulation behavior match the intended scenario?

---

## Example

A combat scenario may have no hard law violations and no stuck entities.

But it may still be badly balanced:

- faction A wins 95% of runs
- average combat duration is too short
- weak faction survival time is too low
- skill progression happens too fast

That is a balance diagnosis, not a logic bug.

---

## Components

- `BalanceDiagnosisEngine`
- `BalanceFinding`
- `BalanceDimension`
- `ScenarioBalanceSummary`
- `BalanceSeverityPolicy`

---

## Balance dimensions

Start with:

- activity
- liveness
- dominance
- scarcity
- progression speed
- runtime stability

Later:

- fairness
- difficulty
- economy inflation
- regional diversity
- role usefulness

---

## Minimal balance checks

### Activity

Checks whether enough meaningful things happen.

Examples:

- no combat in combat-heavy scenario
- no resource production in resource economy
- no quests completed in quest scenario

### Liveness

Checks whether started processes finish.

Examples:

- combat starts but never ends
- quests start but never resolve
- projects start but never complete/fail

### Dominance

Checks one-sided outcomes.

Examples:

- one faction wins almost all runs
- one resource node gets most traffic
- one strategy dominates all entities

### Scarcity

Checks resource pressure.

Examples:

- resource production too low
- inventory full too often
- shop liquidity too low

### Runtime stability

Checks whether simulation is only “working” under stress.

Examples:

- governor degraded too often
- event drops high
- tick p95 unstable

---

## Tasks

### 45.1 Define balance finding model

Fields:

- `finding_id`
- `dimension`
- `severity`
- `summary`
- `metric_values`
- `expected_range`
- `scenario_type`
- `evidence`
- `recommendation`

Acceptance:

- [ ] Balance finding can serialize.
- [ ] Balance finding appears in report.

---

### 45.2 Implement balance dimensions

Start with:

- activity
- liveness
- dominance
- runtime stability

Do not add all dimensions yet.

Checklist:

- [ ] Each dimension has evaluator.
- [ ] Each evaluator can skip missing data.
- [ ] Each evaluator uses expectation pack.
- [ ] Each evaluator supports baseline comparison if available.

Acceptance:

- [ ] Combat-heavy with no combat produces activity finding.
- [ ] Long degraded governor produces runtime stability finding.
- [ ] Dominance check skips if faction metrics unavailable.

---

### 45.3 Integrate with multi-run baseline

Balance diagnosis is stronger across sweeps.

Checklist:

- [ ] Use baseline distributions if available.
- [ ] Compare current sweep to baseline.
- [ ] Mark weak baseline when sample size low.
- [ ] Avoid strong claims with insufficient data.

Acceptance:

- [ ] Diagnosis distinguishes single-run warning from multi-run trend.
- [ ] Report shows baseline confidence.

---

### 45.4 Add recommendations

Recommendations should be investigation-oriented, not auto-tuning.

Example:

> Faction A dominates 92% of combat runs. Inspect faction stat scaling, spawn positions, terrain advantage, and target selection.

Checklist:

- [ ] Each balance dimension has recommendation templates.
- [ ] Recommendations include affected systems.
- [ ] Recommendations avoid pretending to be proof.

Acceptance:

- [ ] Report includes balance diagnosis and recommendations.

---

## Tests

Recommended files:

- `tests/unit/observability/test_balance_diagnosis_engine.py`
- `tests/unit/observability/test_balance_dimensions.py`
- `tests/integration/observability/test_balance_report_integration.py`

Required checks:

- [ ] No activity produces finding.
- [ ] Governor degraded produces runtime finding.
- [ ] Missing faction metrics causes skipped dominance check.
- [ ] Baseline comparison changes severity.
- [ ] Recommendations appear in report.

---

## Completion checklist

- [ ] BalanceDiagnosisEngine exists.
- [ ] BalanceFinding exists.
- [ ] Four balance dimensions exist.
- [ ] Missing data is handled explicitly.
- [ ] Report includes balance diagnosis.

> [!NOTE]
> **Milestone 45 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `BalanceDiagnosisEngine` and `BalanceFinding` in `src/observability/understanding/balance/engine.py`, `BalanceDimension` and `ScenarioBalanceSummary` models in `src/observability/understanding/balance/models.py`.
> * **4 balance dimensions implemented (exactly as specified):** `activity`, `liveness`, `dominance`, `runtime_stability`. Each is an isolated evaluator method that skips cleanly when the required signal is absent from `AnalysisContext`.
> * **Expectation pack integration:** Each dimension evaluator queries `ctx.expectation_pack` for its relevant thresholds (e.g. `combat_heavy` pack expects activity, `peaceful_village` flags high death rate differently).
> * **Multi-run baseline integration:** When a baseline exists in context, dimension evaluators compare current sweep distributions against baseline distributions and mark findings as `SINGLE_RUN_WARNING` vs `MULTI_RUN_TREND`.
> * **Recommendations:** Each `BalanceFinding` includes an investigation-oriented recommendation template string listing relevant subsystems to inspect — not auto-tuning suggestions.
> * **Verification Tests:** `tests/unit/observability/test_balance_diagnosis_engine.py` — 9 tests covering: activity missing signal, no-pack skip, liveness from unresolved quests, liveness clean case, dominance from faction kill skew, dominance skip on missing data, runtime finding from governor pressure, balanced case, and serialization.

---

# Milestone 46 — Emergent Story Detector

## Goal

Identify interesting emergent events that are not necessarily bugs.

This helps answer:

> Is the simulation producing interesting RPG-like stories?

---

## Why this matters

A simulation can be technically correct but boring.

Story detection helps identify whether the simulation creates meaningful events:

- unlikely survival
- faction comeback
- repeated rivalry
- hero rise/fall
- region conquest
- economic collapse and recovery
- quest chain completion
- long-term project success

---

## Important boundary

Story detector should not affect pass/fail.

It should produce:

- interesting story candidates
- highlights
- run summary flavor

Not:

- hard anomaly
- balance failure
- certification failure

---

## Components

- `StoryDetector`
- `StoryCandidate`
- `StoryPattern`
- `StoryHighlight`
- `StoryReportSection`

---

## Initial story patterns

Start with only five:

1. **Unexpected Survivor**
   - entity survives many combats or near-death events

2. **Faction Comeback**
   - faction loses early but recovers later

3. **Resource Crisis**
   - production collapses then recovers

4. **Quest Hero**
   - entity completes multiple quests or major quest chain

5. **Region Power Shift**
   - region changes faction ownership

---

## Story candidate fields

- `story_id`
- `story_type`
- `title`
- `summary`
- `entities`
- `factions`
- `regions`
- `tick_range`
- `supporting_events`
- `interestingness_score`

Use simple scoring.

Do not overbuild.

---

## Tasks

### 46.1 Define story pattern interface

Checklist:

- [ ] Pattern has `story_type`.
- [ ] Pattern declares required events.
- [ ] Pattern can skip missing data.
- [ ] Pattern returns story candidates.
- [ ] Pattern does not affect health score.

Acceptance:

- [ ] Story patterns run separately from anomaly rules.
- [ ] Missing data does not fail analysis.

---

### 46.2 Implement five initial story patterns

Checklist:

- [ ] Unexpected Survivor.
- [ ] Faction Comeback.
- [ ] Resource Crisis.
- [ ] Quest Hero.
- [ ] Region Power Shift.

Acceptance:

- [ ] Synthetic event stream can produce each story type.
- [ ] Normal boring run can produce no stories.

---

### 46.3 Add story section to report

Checklist:

- [ ] Show top story candidates.
- [ ] Include supporting events.
- [ ] Mark as “interesting behavior,” not warning.
- [ ] Keep section optional.

Acceptance:

- [ ] Report includes story section when stories exist.
- [ ] No story section or empty state when none exist.

---

## Tests

Recommended files:

- `tests/unit/observability/test_story_detector.py`
- `tests/unit/observability/test_story_patterns.py`
- `tests/integration/observability/test_story_report_section.py`

Required checks:

- [ ] Quest hero story detected.
- [ ] Region shift story detected.
- [ ] Story does not change health score.
- [ ] Missing signals produce skipped pattern.
- [ ] Story appears in report.

---

## Completion checklist

- [ ] StoryDetector exists.
- [ ] Five initial story patterns exist.
- [ ] Story candidates appear in report.
- [ ] Stories do not affect pass/fail.

> [!NOTE]
> **Milestone 46 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `StoryDetector` in `src/observability/understanding/stories/detector.py`. `StoryPattern` ABC, `StoryCandidate`, and `StoryHighlight` models in `src/observability/understanding/stories/models.py`. 5 concrete pattern classes in `src/observability/understanding/stories/patterns.py`.
> * **5 story patterns implemented (exactly as specified):** `UnexpectedSurvivor`, `ResourceCrisis`, `QuestHero`, `FactionComeback`, `RegionPowerShift`.
> * **No-impact guarantee:** `StoryDetector.detect()` is a pure read operation on `AnalysisContext`. Stories are attached to a separate `StoryReportSection` in `UnderstandingReport`. The main health score and anomaly severity are never modified by story detection.
> * **Missing signal resilience:** Each pattern individually checks for the presence of its required event types. If absent, returns an empty candidate list rather than raising.
> * **Interestingness score:** Uses a simple integer scale (1–10) based on event frequency, recency, and entity count. Avoids fake float precision.
> * **Verification Tests:** `tests/unit/observability/test_phase8_m46_m47_m48.py` — includes `TestStoryDetector` tests for serialization, story type detection, and health score immutability. Pattern-level tests for all 5 patterns with synthetic event streams.

---

# Milestone 47 — Human Review and Labeling Workflow

## Goal

Let developers mark Observatory findings as useful, false positive, expected, bug, or balance issue.

This is essential because anomaly/balance rules will not be perfect.

---

## Why this matters

The system will produce warnings.

Some will be real.

Some will be false positives.

Some will be expected behavior.

Without feedback, rules will not improve.

---

## Review labels

Start with:

- `CONFIRMED_BUG`
- `BALANCE_ISSUE`
- `EXPECTED_BEHAVIOR`
- `FALSE_POSITIVE`
- `NEEDS_MORE_DATA`
- `DUPLICATE`
- `IGNORED_FOR_NOW`

---

## Components

- `FindingReview`
- `ReviewStore`
- `ReviewLabel`
- `ReviewSummary`
- `RuleFeedbackAggregator`

---

## Storage

Keep it simple.

Use local artifact file:

- `finding_reviews.jsonl`

Later, this can move to a database.

---

## Tasks

### 47.1 Define review model

Fields:

- `review_id`
- `run_id`
- `finding_id`
- `label`
- `comment`
- `reviewed_by`
- `reviewed_at`

Acceptance:

- [ ] Review serializes to JSON.
- [ ] Invalid label rejected.

---

### 47.2 Add CLI review command

Commands:

- `rpg-observe review <run_id> <finding_id> --label FALSE_POSITIVE`
- `rpg-observe list-reviews <run_id>`

Checklist:

- [ ] Add review.
- [ ] List reviews.
- [ ] Prevent duplicate review unless update flag.
- [ ] Store in run artifact directory.

Acceptance:

- [ ] Developer can label a finding.

---

### 47.3 Add API review endpoint

Optional if API exists:

- `POST /observability/runs/{run_id}/findings/{finding_id}/review`
- `GET /observability/runs/{run_id}/reviews`

Keep it simple and internal.

Acceptance:

- [ ] Review can be added through API.
- [ ] API does not allow arbitrary file access.

---

### 47.4 Use reviews in future reports

Checklist:

- [ ] Report shows reviewed findings.
- [ ] False positives are marked.
- [ ] Confirmed bugs are highlighted.
- [ ] Review summary appears.

Acceptance:

- [ ] Report distinguishes unreviewed vs reviewed findings.

---

## Tests

Recommended files:

- `tests/unit/observability/test_finding_review_model.py`
- `tests/cli/test_finding_review_cli.py`
- `tests/api/test_finding_review_api.py`

Required checks:

- [ ] Valid review saved.
- [ ] Invalid label rejected.
- [ ] Review appears in report.
- [ ] Duplicate handling works.

---

## Completion checklist

- [ ] Review model exists.
- [ ] Local review store exists.
- [ ] CLI review works.
- [ ] Reports include review status.
- [ ] Feedback data is available for future rule improvement.

> [!NOTE]
> **Milestone 47 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `FindingReview` (Pydantic model), `ReviewLabel` (Enum with 7 labels) in `src/observability/understanding/review/models.py`. `ReviewStore` (JSONL-backed file store) in `src/observability/understanding/review/store.py`.
> * **7 review labels:** `CONFIRMED_BUG`, `BALANCE_ISSUE`, `EXPECTED_BEHAVIOR`, `FALSE_POSITIVE`, `NEEDS_MORE_DATA`, `DUPLICATE`, `IGNORED_FOR_NOW` — exactly as specified.
> * **Storage:** `ReviewStore` appends to `finding_reviews.jsonl` in the run artifact directory. Reads back with full deserialization on access. Uses JSONL (append-friendly) as specified.
> * **CLI commands:** `rpg-observe review <run_id> <finding_id> --label FALSE_POSITIVE` and `rpg-observe list-reviews <run_id>` implemented in `src/cli/entry.py`. Duplicate review detection raises a warning unless `--update` flag is passed.
> * **API endpoints:** `POST /api/v1/observability/runs/{run_id}/findings/{finding_id}/review` and `GET /api/v1/observability/runs/{run_id}/reviews` added to `src/api/server.py` — ID-sanitized, no arbitrary file access.
> * **Report integration:** `UnderstandingPipeline._evaluate_expectations()` reads `ReviewStore` to annotate confirmed bugs and false positives in the final report.
> * **Verification Tests:** `tests/unit/observability/test_phase8_m46_m47_m48.py` — `TestFindingReview` (label enum, to_dict, roundtrip) and `TestReviewStore` (add, list, get_by_finding, update_label, empty store, label_summary).

---

# Milestone 48 — Analyzer Quality and Baseline Evolution

## Goal

Measure whether the Observatory itself is useful and keep baselines from becoming stale.

---

## Why this matters

The Observatory will evolve.

Rules will change.

Balance will change.

Performance will change.

So we need a way to manage:

- false positives
- missed issues
- stale baselines
- weak baselines
- baseline replacement
- rule quality

---

## Components

- `AnalyzerQualityReport`
- `RuleQualityMetrics`
- `BaselineEvolutionPolicy`
- `BaselineReviewRecord`
- `BaselinePromotionWorkflow`

---

## Rule quality metrics

Track:

- total findings by rule
- reviewed findings
- confirmed bugs
- false positives
- expected behavior labels
- unreviewed rate
- average severity
- rule disabled count

Example:

> `NavigationStuckBasic` produced 300 findings, 20 reviewed, 12 confirmed bugs, 6 false positives, 2 expected behavior.

---

## Baseline evolution policy

Baselines should not auto-update silently.

Use explicit promotion.

States:

- `CANDIDATE`
- `ACTIVE`
- `DEPRECATED`
- `REJECTED`

---

## Baseline promotion criteria

Example:

- minimum run count reached
- no hard law violations
- no critical anomalies
- acceptable performance envelope
- human approval if required

---

## Tasks

### 48.1 Generate analyzer quality report

Checklist:

- [ ] Load findings.
- [ ] Load reviews.
- [ ] Compute rule-level quality metrics.
- [ ] Identify noisy rules.
- [ ] Identify under-reviewed rules.
- [ ] Write quality report.

Acceptance:

- [ ] Quality report shows false-positive rates where reviews exist.
- [ ] Unreviewed findings are counted separately.

---

### 48.2 Add baseline status model

Checklist:

- [ ] Baseline has status.
- [ ] Baseline has source sweep.
- [ ] Baseline has promotion timestamp.
- [ ] Baseline has reviewer optional.
- [ ] Baseline has deprecation reason optional.

Acceptance:

- [ ] Baseline can be candidate or active.
- [ ] Active baseline is discoverable by scenario type.

---

### 48.3 Add baseline promotion command

Command:

- `rpg-observe baseline promote <baseline_id>`
- `rpg-observe baseline deprecate <baseline_id>`

Checklist:

- [ ] Validate baseline before promotion.
- [ ] Reject baseline with critical failures unless forced.
- [ ] Record promotion metadata.
- [ ] Do not overwrite active baseline silently.

Acceptance:

- [ ] Candidate baseline can become active.
- [ ] Old baseline can be deprecated.

---

### 48.4 Add stale baseline detection

A baseline may be stale if:

- engine version changed
- scenario config changed
- artifact schema changed
- performance profile changed
- rule pack version changed

Checklist:

- [ ] Compare current run metadata to baseline metadata.
- [ ] Mark stale if important version mismatch.
- [ ] Report stale baseline warning.

Acceptance:

- [ ] Comparator warns when baseline is stale.
- [ ] CI can treat stale baseline as warning or fail.

---

## Tests

Recommended files:

- `tests/unit/observability/test_analyzer_quality_report.py`
- `tests/unit/observability/test_baseline_evolution_policy.py`
- `tests/cli/test_baseline_promotion_cli.py`

Required checks:

- [ ] Quality report counts reviewed findings.
- [ ] Candidate baseline can be promoted.
- [ ] Bad baseline promotion rejected.
- [ ] Stale baseline detected.
- [ ] Deprecated baseline not used by default.

---

## Completion checklist

- [ ] Analyzer quality report exists.
- [ ] Baseline status model exists.
- [ ] Baseline promotion workflow exists.
- [ ] Stale baseline detection works.
- [ ] Rule feedback can guide future improvements.

> [!NOTE]
> **Milestone 48 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:**
>   - `AnalyzerQualityReporter` and `AnalyzerQualityReport` / `RuleQualityMetrics` models in `src/observability/understanding/quality/quality_report.py` + `models.py`.
>   - `StaleBaselineDetector`, `StalenessResult`, `StalenessWarning` in `src/observability/understanding/quality/stale_detector.py`.
>   - `BaselineEvolutionPolicy` and `BaselinePromotionWorkflow` in `src/observability/understanding/quality/baseline_evolution.py`.
> * **Quality report:** Aggregates `FindingReview` data from `ReviewStore` per rule. Tracks: `total_findings`, `reviewed_count`, `confirmed_bug_count`, `false_positive_count`, `expected_behavior_count`, `unreviewed_count`, and computes `false_positive_rate`. Flags rules with false-positive rate > 50% as `noisy_rules`.
> * **Baseline status lifecycle:** `BaselineStatus` enum with 4 states: `CANDIDATE → ACTIVE → DEPRECATED` (or `REJECTED`). `BaselineEvolutionPolicy.promote()` validates: no hard law violations, no critical anomalies, min run count, acceptable performance envelope. Rejects silently bad baselines unless `force=True`.
> * **Stale detection:** `StaleBaselineDetector.check()` compares schema version, scenario type, engine version string, and expectation pack version between the current run manifest and the stored baseline metadata. Returns a list of `StalenessWarning` records with precise mismatch descriptions.
> * **CLI commands:** `rpg-observe baseline promote <baseline_id>` and `rpg-observe baseline deprecate <baseline_id>` implemented in `src/cli/entry.py`.
> * **Verification Tests:** `tests/unit/observability/test_phase8_m46_m47_m48.py` — `TestAnalyzerQualityReporter` (unreviewed, false positive rate, noisy rule detection, dict serialization) and `TestStaleBaselineDetector` (schema version mismatch, scenario type mismatch, clean match, dict serialization).

---

# Phase 8 End-to-End Flow

At the end of Phase 8:

1. A scenario run produces events, metrics, anomalies, and reports.
2. Domain analyzers interpret anomalies by system domain.
3. Scenario expectation packs define what is normal for that scenario type.
4. Root-cause engine proposes likely causes with evidence.
5. Balance engine diagnoses activity, liveness, dominance, and stability.
6. Story detector identifies interesting emergent behavior.
7. Developers review findings and label them.
8. Analyzer quality report shows which rules are useful or noisy.
9. Baselines can be promoted, deprecated, or marked stale.

---

# Minimal Data Coverage for Phase 8

## Minimal domain analyzers

- movement
- economy
- quest
- runtime

## Minimal expectation packs

- resource economy
- combat heavy
- mixed sandbox
- peaceful village

## Minimal root-cause hypotheses

- stale resource target selection
- movement bottleneck
- inventory return loop broken
- quest objective impossible
- governor pressure
- combat cannot resolve

## Minimal balance dimensions

- activity
- liveness
- dominance
- runtime stability

## Minimal story patterns

- unexpected survivor
- faction comeback
- resource crisis
- quest hero
- region power shift

## Minimal review labels

- confirmed bug
- balance issue
- expected behavior
- false positive
- needs more data

---

# Phase 8 Performance Rules

Most Phase 8 processing should be post-run.

Rules:

- [ ] Domain analysis does not run inside tick path.
- [ ] Root-cause engine does not run inside tick path.
- [ ] Balance diagnosis does not run inside tick path.
- [ ] Story detector does not run inside tick path.
- [ ] Human review workflow does not touch engine state.
- [ ] Live system only receives summarized outputs later.

---

# Phase 8 Final Acceptance Criteria

- [ ] Domain analyzers exist and run through registry.
- [ ] Expectation packs affect severity and interpretation.
- [ ] Root-cause hypotheses appear in report.
- [ ] Balance diagnosis appears in report.
- [ ] Story highlights appear in report.
- [ ] Findings can be reviewed and labeled.
- [ ] Analyzer quality report exists.
- [ ] Baselines can be promoted/deprecated.
- [ ] Stale baselines are detected.
- [ ] Missing signals remain explicit.

---

# Recommended Execution Order

1. **Milestone 42 — Domain Analyzer Framework**
2. **Milestone 43 — Scenario Expectation Packs**
3. **Milestone 44 — Root-Cause Hypothesis Engine**
4. **Milestone 45 — Balance Diagnosis Engine**
5. **Milestone 46 — Emergent Story Detector**
6. **Milestone 47 — Human Review and Labeling Workflow**
7. **Milestone 48 — Analyzer Quality and Baseline Evolution**

Reason:

> First interpret by domain.
> Then add scenario expectations.
> Then infer likely causes.
> Then diagnose balance.
> Then detect interesting stories.
> Then add human feedback.
> Finally manage analyzer quality and baselines.
