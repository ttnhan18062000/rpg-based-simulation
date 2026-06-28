# Implementation Sequence — Deferred Epics

Spawned by TCK-20260627-P3A-DEFERRED-EPICS on 2026-06-28 after P0–P2 audit-fix
sprint cleared. Two lanes are immediately unblockable; four require prerequisite
data from the regression suite.

---

## Stage 1 — Parallel launch (OPEN, no blockers)

Both can start immediately. Run concurrently.

```
TCK-20260628-E-LONGRUN-REGRESSION    (start first — generates 5k-tick data for Stage 2)
TCK-20260628-E-NARRATIVE-CONSEQUENCE (independent; no data dependency)
```

**E-LONGRUN-REGRESSION** produces the automated 5,000-tick CI regression harness
and the run artifacts that gate all four Stage 2 tickets.

---

## Stage 2 — After 5k-tick data exists (after Stage 1)

### 2a — Quick prerequisite checks (do these while Stage 1 runs)

```
Verify HERO-role archetype exists in data/content/entities/entity_archetypes.yaml
    → unblocks TCK-20260628-E-PARTY-LOOP

Run: make sim-run TICKS=1000 SEED=42 OBS_MODE=LIGHT  (store results)
    → unblocks TCK-20260628-E-PERSONALITY-CALIBRATION
```

### 2b — After E-LONGRUN-REGRESSION 5k data is archived

```
TCK-20260628-E-RESOURCE-ECOLOGY    (needs 5k depletion/recovery curve data)
TCK-20260628-E-WORLD-EVOLUTION     (needs 5k trauma/sovereignty event confirmation)
TCK-20260628-E-PARTY-LOOP          (needs HERO-role verification from 2a)
TCK-20260628-E-PERSONALITY-CALIBRATION  (needs 1k-tick personality audit from 2a)
```

All four Stage 2b tickets are independent of each other — run in any order or
concurrently once their prerequisite is met.

---

## Stage 3 — Combat Ecology Extension (no epic yet)

Gated behind 5k-tick run data confirming combat encounter rates at scale.
Create the epic ticket once Stage 1 data is archived and scope is clear.

---

## Status at spawn time

| Ticket | Status | Gate |
|---|---|---|
| TCK-20260628-E-LONGRUN-REGRESSION | OPEN | None |
| TCK-20260628-E-NARRATIVE-CONSEQUENCE | OPEN | None |
| TCK-20260628-E-PARTY-LOOP | BLOCKED | HERO-role archetype check |
| TCK-20260628-E-PERSONALITY-CALIBRATION | BLOCKED | 1k-tick LIGHT run |
| TCK-20260628-E-RESOURCE-ECOLOGY | BLOCKED | 5k-tick run data |
| TCK-20260628-E-WORLD-EVOLUTION | BLOCKED | 5k-tick run data |
