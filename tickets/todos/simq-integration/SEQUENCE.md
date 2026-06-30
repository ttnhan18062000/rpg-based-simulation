# SimQ Integration Fix — Execution Sequence

**Source:** D20 audit (`docs/audits/D20_simq_integration.md`)  
**Epic:** TCK-20260628-SIMQ-EPIC  
**Date:** 2026-06-30

SimQ is fully built (E1–E7 done) but receives zero events in every run because three
integration gaps prevent the hub from being wired into the event pipeline. This folder
contains the fix sequence.

---

## Dependency Graph

```
TCK-20260630-SIMQ-WIRE-KERNEL  ──────────────────┐
  (standard — G1 + G3)                           │
                                                  ▼
TCK-20260630-SIMQ-WIRE-SERVER   TCK-20260630-SIMQ-RECALIBRATE
  (hotfix — G2, independent)      (hotfix — blocked on WIRE-KERNEL)
```

---

## Step 1 — SIMQ-WIRE-KERNEL + SIMQ-WIRE-SERVER (parallel)

Both can start at the same time. WIRE-KERNEL is the larger change; WIRE-SERVER is a
hotfix and can be done in minutes while WIRE-KERNEL is in review.

### TCK-20260630-SIMQ-WIRE-KERNEL (standard)

**Gaps fixed:** G1 + G3  
**Why first:** This is the root cause. `EventRecorder` creates a `QueueDrainWorker`
without `quality_fn`, so no events reach the hub. `InProcessQualityFeed` creates a
competing second worker on the same queue — it has `quality_fn` set correctly but loses
the race to EventRecorder's worker every time.

**What changes:**
- `src/observability/event_recorder.py` — accept optional `quality_fn` param, pass to its `QueueDrainWorker`
- `src/engine/kernel.py` — build hub before EventRecorder; pass `quality_fn=hub.on_envelope`
- `src/simulation_quality/feed.py` — refactor `InProcessQualityFeed` into a lifecycle
  manager only (no second `QueueDrainWorker`; inject hub reference for health/stop)

**Acceptance gate:** 20-tick sandbox_world run → `report.tick_count > 0`

### TCK-20260630-SIMQ-WIRE-SERVER (hotfix)

**Gap fixed:** G2  
**Why parallel:** Independent of kernel changes; touches only `server.py` lifespan.
`set_quality_hub()` exists in `src/api/dependencies.py` but is never called, so REST
endpoints always return the disabled-hub response.

**What changes:**
- `src/api/server.py` — call `set_quality_hub(manager.quality_hub)` after manager starts

**Acceptance gate:** `GET /api/v1/quality/pillars` returns live data during a server run

---

## Step 2 — SIMQ-RECALIBRATE (after WIRE-KERNEL is merged)

### TCK-20260630-SIMQ-RECALIBRATE (hotfix)

**Blocked on:** WIRE-KERNEL merged and green  
**Why last:** `tools/calibrate_simq.py` ran against a disconnected hub in E7 — all
thresholds in `config/simulation_quality/grade_thresholds.yaml` were calibrated against
zero signal. Once WIRE-KERNEL is in, re-run calibration on ≥3 seeds to get real
percentile baselines.

**What changes:**
- `config/simulation_quality/grade_thresholds.yaml` — updated with real percentile values
- `docs/simulation_quality/quality_scoring_contract.md` §4.5 — calibration status updated

**Acceptance gate:** `calibrate_simq.py` exits 0 with non-zero event counts per pillar;
COMBAT and AGENCY normalized scores > 0 for seed 42, 200 ticks

---

## Known Scope Boundary

`ENABLE_ADVENTURE_ROUTING` defaults to OFF (P0-A in `audit_fix_plan.md`). Until P0-A is
fixed, ECONOMY, SOCIAL, and NARRATIVE pillar scores will remain near zero even after
wiring is complete — entities do not run the adventure pipeline. Defer calibration of
those three pillars to a post-P0-A pass.
