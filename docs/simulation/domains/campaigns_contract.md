---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [domains, campaigns, lifecycle, analysis, contract]
---

# Campaigns Domain Contract

**Source:** `src/domains/campaigns/` (10 files + `__init__.py`)  
**Authoritative status:** Analysis domain — NOT simulation state. Campaigns run the Kernel internally for analysis/testing; they are not a primary tick producer.

---

## Purpose

The campaigns domain orchestrates **multi-tick simulation runs** for analytical and testing purposes. A campaign is a bounded scenario execution that produces arc analysis, behaviour classification, and quality metrics. Campaigns are used by the lab (`src/lab/`) and regression testing — not by the primary simulation loop.

---

## Campaign Lifecycle

```
CampaignSpec → SimulationAnalysisRunner → [Kernel ticks × N] → CampaignResult
```

| State | Description |
|---|---|
| **Created** | `CampaignSpec` constructed with `ActorDistribution`, tick budget, scenario parameters |
| **Running** | `SimulationAnalysisRunner` executes Kernel ticks using `DeterministicRNG` (same seed → same result) |
| **Analysing** | Sub-analysers run after final tick: arc classification, behaviour change detection, diversity scoring, forbidden-behaviour detection |
| **Done** | `CampaignResult` produced: `EntityArcReport` per actor, `WorldArcReport`, scorecard |

There is no `Failed` state — if the Kernel raises during a campaign run, the exception propagates to the caller.

---

## CampaignSpec

Key fields in `CampaignSpec`:
- `ActorDistribution` — count, start_region, start_level, class_distribution, trait_distribution
- Tick budget — maximum ticks to run
- Scenario parameters — seed, world composition reference

All fields are frozen (immutable) after construction.

---

## Sub-Analyser Contracts

| Class | File | Responsibility |
|---|---|---|
| `LifeArcClassifier` | classifier.py | Classifies the entity's life arc (hero / villager / etc.) from tick history |
| `BehaviorChangeProofDetector` | behavior_change.py | Detects measurable, evidence-backed behaviour changes across ticks |
| `RouteDiversityAnalyzer` | diversity.py | Measures diversity of routes and decisions taken (prevents degenerate loops) |
| `CampaignScorecardEvaluator` | scorecard.py | Aggregates sub-analyser outputs into a pass/fail scorecard |
| `ForbiddenBehaviorDetector` | forbidden.py | Flags explicit anti-patterns (infinite loops, locked states, illegal goal sequences) |

All sub-analysers receive the tick event log and return typed result records — they do not re-run ticks.

---

## Output

`CampaignResult` contains:
- `EntityArcReport` per actor — life arc, behaviour change evidence, route diversity score
- `WorldArcReport` — world-level state trajectory over the campaign
- Scorecard pass/fail verdict
- List of forbidden-behaviour violations (empty if clean)

---

## Determinism Contract

`SimulationAnalysisRunner` uses `DeterministicRNG` seeded from `CampaignSpec`. Given the same `CampaignSpec` (same seed, same world composition, same actor distribution), the `CampaignResult` must be bit-identical. This is enforced by:
1. All randomness sourced from `DeterministicRNG`
2. Kernel ticks run in single-threaded mode during campaign runs
3. `ActorDistribution` and spec fields are frozen — no external mutation

---

## Boundary: Campaigns vs. Primary Simulation

| | Campaigns | Primary Simulation |
|---|---|---|
| Runs Kernel | Yes (internally, bounded) | Yes (primary loop) |
| Produces AuthoritativeState | Shadow only (not persisted) | Persisted |
| Purpose | Analysis / regression | Live simulation |
| Entry point | `SimulationAnalysisRunner.run()` | `Kernel.tick_once()` |

Campaigns **may not** share `AuthoritativeState` with the primary simulation — they operate on their own isolated state instances.

---

## REST API (E32E)

The multi-episode `CampaignOrchestrator` (E32C) exposes its `NarrativeLedger`
via REST:

```
GET /api/v1/campaigns/{id}/history
    ?event_type=entity_death
    &min_significance=0.5
    &episode=1
→ { campaign_id, entry_count, entries: [{episode, tick, event_type, subject_id, payload, significance, entry_id}] }
```

See `docs/simulation/domains/campaign_orchestrator_contract.md` for the full
orchestrator lifecycle, NarrativeLedger schema, carry-forward rules, and REST
endpoint contract.

| Component | File | Role |
|---|---|---|
| Route | `src/api/routes/campaigns.py` | `GET /api/v1/campaigns/{id}/history` |
| Presenter | `src/api/presenters/campaigns.py` | `CampaignHistoryResponse`, `NarrativeLedgerEntryPresenter` |
| Service | `src/domains/campaigns/narrative_ledger.py` | `NarrativeLedger.query()` |
| State | `src/domains/campaigns/state.py` | `CampaignState.narrative_ledger` |

---

## Constraints

- Campaigns must not write to shared `AuthoritativeState` — each run creates an isolated state.
- `DeterministicRNG` must be the only source of randomness inside a campaign run.
- Sub-analysers must not re-run Kernel ticks — they receive the tick log only.
- Must not import from other domain packages except through `src/core/` types.
- REST responses must go through the presenter layer — no raw domain models from API.
