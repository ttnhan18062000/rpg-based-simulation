# Implementation Sequence — TCK-20260628-SIMQ-EPIC

Parent epic: `tickets/inprogress/TCK-20260628-SIMQ-EPIC.md`
Contract: `docs/simulation_quality/quality_scoring_contract.md`

---

## Stage 1 — Foundation (no blockers)

```
TCK-20260628-SIMQ-E1-FOUNDATION
```

Core models, config YAML files, `ScoringWeights`, `PillarAccumulator` (with event_id
dedup), `QualityReport`, `QualityPersistence`, `QualityFeedAdapter` ABC,
`InProcessQualityFeed`, `build_feed_from_env()` factory.

No user-visible behavior. All subsequent tickets depend on this.

---

## Stage 2 — Hub + First Scorers (requires Stage 1)

```
TCK-20260628-SIMQ-E2-HUB-CORE
```

`QualityHub` (takes `QualityFeedAdapter` by injection), `BrokerQualityFeed`
(wraps M36 `RedisStreamConsumer`), `worker.py` separate-process entry point,
`AgencyScorer`, `CombatScorer`.

Validates the scorer pattern before batch implementation in Stage 3.

---

## Stage 3 — Remaining 8 Scorers (requires Stage 2, run in parallel)

```
TCK-20260628-SIMQ-E3-SCORERS-A    TCK-20260628-SIMQ-E4-SCORERS-B
  CognitionScorer                   SocialScorer
  FactionScorer                     InformationScorer
  EconomyScorer                     WorldDynamicsScorer
  ProgressionScorer                 NarrativeScorer
```

E3 and E4 are independent — run concurrently. Each scorer must trace to a §6
scenario entry; no event_type may be dual-owned across pillars.

**E3 note:** `EconomyScorer` must NOT score `ecology_cycle_completed` — owned by
`WorldDynamicsScorer` in E4.

**E4 note:** WD cadence-gated phases require absence-over-time detection via
`window_buffer`. Chronicle entries may not be on the event bus — verify before scoring.

---

## Stage 4 — REST API (requires Stage 3)

```
TCK-20260628-SIMQ-E5-API
```

5 endpoints: `/status`, `/pillars`, `/pillars/{id}`, `/alerts`, `/report`.
Wire `quality_report.json` to same lifecycle hook as replay `manifest.json`.
Must use `response_model=` on all handlers.

---

## Stage 5 — Full Test Suite (requires Stage 4)

```
TCK-20260628-SIMQ-E6-TESTS
```

13 unit test files, integration (both feed modes), regression anchors
(`grade_anchors.json`), performance (timeit), scenario coverage (all 22 §6 entries),
broker feed integration (skipped without Redis).

Performance gates: scorer < 0.1 ms, report build < 50 ms.

---

## Stage 6 — Calibration (requires Stage 5, P2)

```
TCK-20260628-SIMQ-E7-CALIBRATE
```

8 baseline runs (4 worlds × 2 seeds × 500 ticks). Calibrate
`grade_thresholds.yaml` and `scoring_weights.yaml` via YAML edits only — no
Python changes. Commit calibrated configs + `grade_anchors.json`. Add
SIMQ-CALIBRATED-001 parity ledger entry.

Do not clean `data/runs/` until calibration anchors are committed.

---

## Status at creation

| Ticket | Status | Gate |
|---|---|---|
| TCK-20260628-SIMQ-E1-FOUNDATION | OPEN | None |
| TCK-20260628-SIMQ-E2-HUB-CORE | OPEN | E1 |
| TCK-20260628-SIMQ-E3-SCORERS-A | OPEN | E2 |
| TCK-20260628-SIMQ-E4-SCORERS-B | OPEN | E2 |
| TCK-20260628-SIMQ-E5-API | OPEN | E3 + E4 |
| TCK-20260628-SIMQ-E6-TESTS | OPEN | E5 |
| TCK-20260628-SIMQ-E7-CALIBRATE | OPEN (P2) | E6 |
