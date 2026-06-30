---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-INVESTIGATION
artifact_type: investigation
tags: [simulation-quality, scoring, pillars, architecture]
---

# Investigation — TCK-20260628-SIMQ-INVESTIGATION

## 1. What Exists Today

### 1.1 Existing Scoring Infrastructure

Four scoring systems exist. None of them are the module being proposed. Understanding
why they are different is critical to avoiding duplication and correctly positioning
the new module.

| System | File | What it scores | When | Gap |
|---|---|---|---|---|
| `RunBehaviorScorecard` | `src/observability/behavior/behavior_scorecard.py` | Population-level behavioral outcomes: diversity, stagnation, episode success rate, adaptation proofs | Post-run, from episode aggregates | Not per-event, not per-pillar, not incremental |
| `EntityBehaviorScorecard` | same file | Per-entity behavioral outcomes: route families used, progression/cooperation/diversity scores | Post-run, per entity | Not incremental, not cross-domain, not real-time |
| `CampaignScorecardEvaluator` | `src/domains/campaigns/scorecard.py` | Semantic arc verdict: pass/fail on arc types, forbidden behaviors, route diversity | Post-run, from arc reports | Semantic verdict only; not graded per subsystem |
| `AnalyzerQualityReporter` | `src/observability/understanding/quality/quality_report.py` | Analyzer rule quality: false positive / confirmed-bug rates from human reviews | Post-analysis-run | About the analyzer's accuracy, not simulation quality |

**Correctness monitors (not quality scorers):**
- `hard_law_monitor.py` — detects contract invariant violations; binary (violated or not),
  not graduated quality scoring
- Audit dimensions D01–D19 — manual, human-authored, static analysis snapshots; not runtime

**Conclusion:** No incremental, per-event, per-subsystem quality scoring system exists.

### 1.2 Event Infrastructure

The event bus (`src/observability/events.py`) emits `ObservabilityEventEnvelope` records
in 13 event categories:

```
movement | combat | resource | economy | inventory |
quest | strategy | social | lifecycle | region |
infrastructure | hard_law | anomaly
```

These categories partially map to simulation domains but do not align 1:1 with the
quality pillars needed. The `social` category covers cooperation, contracts, groups,
and reputation simultaneously. The `economy` category covers harvesting, crafting, and
trade. The proposed pillars cut across categories differently — e.g., the **Faction &
Military** pillar draws from `strategy`, `combat`, and `region` categories together.

### 1.3 Live Pipeline Phases (D19 Source)

53 live phases are confirmed in `pipeline.py:refine()` and `world_dynamics.py:resolve_dynamics()`:
- 30 active (every tick)
- 7 feature-gated (default ON)
- 1 direct-call
- 15 world dynamics sub-phases (7 every-tick, 8 cadence-gated)

Every pillar in the proposed module is grounded in specific phase IDs from D19.

---

## 2. The Usage Scenarios

These are the concrete questions a developer or designer would ask about the simulation.
The pillar structure is designed so that every question maps to exactly one primary pillar
and at most one secondary pillar. Ambiguous questions (crossing two pillars) indicate
a correlation to investigate, not a design fault.

| Question | Primary Pillar | Secondary Pillar |
|---|---|---|
| "Is the simulation in an infinite loop — same set of goals cycling?" | Agency & Action | Cognition |
| "Why do entities all do the same thing every tick?" | Agency & Action | Cognition |
| "Is combat balanced — not instant extinction, not never-firing?" | Combat | World Dynamics |
| "Is any entity class dominating in combat?" | Combat | Progression |
| "Is any faction dominating politically or militarily?" | Faction & Military | — |
| "Are factions actually forming alliances, or are they all isolated?" | Faction & Military | Social |
| "Is the economic loop alive — harvesting, crafting, trading?" | Economy | World Dynamics |
| "Is resource ecology in balance — not depleted-forever or never-depleted?" | Economy | World Dynamics |
| "Is gold accumulating without being spent (inflation spiral)?" | Economy | — |
| "Are entities growing — gaining XP, leveling up, evolving?" | Progression | — |
| "Is progression plateauing — entities stuck at level 1 for 500 ticks?" | Progression | — |
| "Are entities cooperating, or acting in complete isolation?" | Social | Agency & Action |
| "Are contracts completing, or always expiring?" | Social | — |
| "Is reputation changing meaningfully, or always flat?" | Social | — |
| "Is information asymmetry creating decision divergence?" | Information & Belief | Cognition |
| "Are entities actually using intelligence to make different decisions?" | Information & Belief | — |
| "Is the world alive — calamities, boss spawns, region transformations?" | World Dynamics | — |
| "Is ecology regenerating, or are all resource nodes permanently depleted?" | World Dynamics | Economy |
| "Are quests starting and completing, or zero quest activity?" | Narrative | — |
| "Is the world producing history — chronicle entries, milestones?" | Narrative | — |
| "Do entities behave like distinct RPG archetypes, or are they homogeneous?" | Cognition | Progression |
| "Is the scenario making progress toward its objectives?" | Narrative | Agency & Action |

---

## 3. What Is NOT Covered Here

- **Correctness** — contract violations, P0 parity bugs, hard law breaches. Those belong
  to `hard_law_monitor` and the parity ledger.
- **Performance** — tick latency, memory usage, observability overhead. Those belong to
  `performance_contract.md` and `perf_baseline_policy.md`.
- **Code quality** — test coverage, coupling depth, dead code. Those belong to audit
  dimensions D10–D14.
- **Content quality** — whether quests are narratively interesting, whether world flavor
  text is good. Those are human judgment calls, not automated scores.

The module scores **simulation health** — whether systems are alive, balanced, and
producing emergent output — not correctness, performance, or content.

---

## 4. Conflict Analysis

### 4.1 Against RunBehaviorScorecard

`RunBehaviorScorecard` measures behavioral diversity via episodes (behavioral sequences
detected by `episode_detector.py`). The new module measures incremental per-event
quality signals across 10 subsystem pillars. They are **complementary, not overlapping**:
the new module produces signals that could in the future FEED behavioral episode analysis.

### 4.2 Against CampaignScorecard

`CampaignScorecardEvaluator` produces a binary pass/fail verdict from arc types and
forbidden behaviors. The new module produces graduated health grades per pillar across
the full run. **Complementary**: campaign scorecard is a semantic verdict;
the quality module is a diagnostic health dashboard.

### 4.3 Against hard_law_monitor

The monitor fires on correctness violations (contract breaches). The quality module
fires on quality degradation (subsystems producing too little or degenerate output).
A simulation can pass all hard law checks and still score F on Economy (zero harvesting).
**No overlap**: correctness and quality are orthogonal dimensions.

### 4.4 Against Audit Dimensions

The audit dimensions are manual, one-time, human-authored analyses. The quality module
is automated, per-run, machine-computed. Audit findings document *what gaps exist*;
the quality module measures *whether those gaps affect a specific run's output*.
**No overlap**: the module automates part of what D03/D04/D05/D06 do manually per run.

---

## 5. Key Architectural Constraints

From `docs/engine/architecture_reference.md`:

1. **Decision-making must be read-only** (§1.1) — Quality scorers must never write to
   simulation state. The score records are observability artifacts, not simulation state.

2. **Typed records, not metadata blobs** (§1.2) — `ScoreRecord` must be a typed
   dataclass, not a dict of free-form strings.

3. **Layer boundaries** (§1.3) — The scoring module is a new layer (meta-evaluation)
   distinct from domain logic and observability. It must not import domain internals.

4. **Determinism** (§4.1) — Score records must be deterministic given the same event
   stream. No bare `random.` calls. Score deltas must be derived from event content only.

5. **Non-blocking** (BoundedObservabilityQueue pattern) — Scoring failure must never
   block or crash the simulation. Errors are logged and discarded.

---

## 6. Module Positioning

```
┌──────────────────────────────────────────────────────┐
│                  Simulation Loop                     │
│  (Kernel → Pipeline Phases PP-01…PP-37 + WD-01…15)  │
└─────────────────────┬────────────────────────────────┘
                      │ authoritative state transitions
                      ▼
┌──────────────────────────────────────────────────────┐
│              Observability Layer                     │
│  EventBus → BoundedObservabilityQueue → events.jsonl │
└─────────────────────┬────────────────────────────────┘
                      │ ObservabilityEventEnvelope stream
                      ▼
┌──────────────────────────────────────────────────────┐
│         [NEW] Simulation Quality Layer               │
│  QualityHub → PillarScorers → PillarAccumulators     │
│  → quality_scores.jsonl + QualityReport              │
└─────────────────────┬────────────────────────────────┘
                      │ read-only quality signals (future)
                      ▼
┌──────────────────────────────────────────────────────┐
│            Analysis / Post-Run Layer                 │
│  RunBehaviorScorecard, CampaignScorecard, Reports    │
└──────────────────────────────────────────────────────┘
```

The quality layer sits between observation and analysis. It consumes the event stream
and produces quality signals. In the future, those signals can be read by the engine
through a controlled read-only interface (like the live observability API).

---

## 7. Findings Summary

| Finding | Implication |
|---|---|
| No incremental per-event quality scoring exists | Gap is real; module is net-new |
| Existing scorecards are post-run aggregates | New module is complementary, not redundant |
| 53 live pipeline phases span 12 distinct simulation domains | 10 pillars required; fewer loses specificity |
| Event categories (13) do not map 1:1 to simulation domains | Pillars must draw from multiple event categories |
| Behavior scorecard already uses `stagnation_score`, `progression_score`, `cooperation_score` | New module should use different naming to avoid confusion; pillar names are distinct |
| `hard_law_monitor` covers correctness | Quality module covers health — orthogonal |
| Usage scenarios span all 10 proposed pillars without redundancy | Pillar coverage is complete |
