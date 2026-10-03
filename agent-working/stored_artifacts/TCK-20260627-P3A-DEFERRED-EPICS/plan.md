---
ticket: TCK-20260627-P3A-DEFERRED-EPICS
phase: Plan
date: 2026-06-28
---

# Plan — TCK-20260627-P3A-DEFERRED-EPICS

## Goal

Create child epic tracking tickets for every deferred P3-A item whose gate conditions are
now met (or partially met with clear next steps). Update this tracking ticket's Related
Tickets section to link the new epics.

## Gate Check Summary

| Item | Gate Status | Action |
|---|---|---|
| Long-Horizon Regression Suite | FULLY MET | Create epic — REQUIRED by acceptance criteria |
| Narrative Consequence Layer | FULLY MET | Create epic |
| Resource Ecology Regeneration | PARTIAL (need 5k-tick) | Create planning epic with gating note |
| World Evolution System | PARTIAL (need 5k-tick) | Create planning epic with gating note |
| Full Party Adventure Loop | PARTIAL (E61B done, HERO role unclear) | Create planning epic with gating note |
| Personality → Long-Run Calibration | PARTIAL (need D05 audit run) | Create planning epic with gating note |
| Combat Ecology Extension | NOT MET (need 5k-tick data) | Note in tracking ticket; no epic yet |

## Ordered Steps

### Step 1 — Create Long-Horizon Regression Suite epic ticket (REQUIRED)

File: `tickets/todos/TCK-20260628-E-LONGRUN-REGRESSION.md`

Scope: Define and implement an automated 5,000-tick regression test suite. Gate was
P1-A (done). Acceptance criteria from D01: "Behavioral regressions detected across
refactors." Child tickets will cover: test harness setup, metric capture, assertion
thresholds, CI integration.

Dependency: None (gate is already met).

### Step 2 — Create Narrative Consequence Layer epic ticket

File: `tickets/todos/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`

Scope: Wire chronicle events into real-time entity motivation feedback. Specifically:
grief/rage urgency from death/betrayal chronicle events; nemesis formation from
recurring antagonist chronicle entries. Gate was E51/E43B (both done). This epic
will NOT re-implement chronicle or social memory — those are done.

Dependency: None (gate is already met).

### Step 3 — Create Resource Ecology Regeneration epic ticket

File: `tickets/todos/TCK-20260628-E-RESOURCE-ECOLOGY.md`

Scope: Complete complex regeneration cycles: density-dependent rates, multi-stage
ecological cycles, cross-region pressure propagation. Basic per-tick regen exists
(E21B). Gate: P0 fixes done; 5k-tick run still needed for full scope validation.
Epic should be created now so it's ready when 5k-tick run completes; mark it BLOCKED
pending 5k validation.

### Step 4 — Create World Evolution System epic ticket

File: `tickets/todos/TCK-20260628-E-WORLD-EVOLUTION.md`

Scope: Seasonal multi-region pressure propagation and long-run ecological dynamics.
Trauma/sovereignty feedback loop not validated long-run. Mark BLOCKED pending 5k-tick run.

### Step 5 — Create Full Party Adventure Loop epic ticket

File: `tickets/todos/TCK-20260628-E-PARTY-LOOP.md`

Scope: Class-compatibility scoring for party composition optimization; multi-hero
orchestration. Gate is E61B (done) + HERO role populated. Mark BLOCKED pending
HERO role population verification.

### Step 6 — Create Personality → Long-Run Calibration epic ticket

File: `tickets/todos/TCK-20260628-E-PERSONALITY-CALIBRATION.md`

Scope: Run D05-style behavioral audit at 1,000+ ticks with P2O observability enabled;
establish personality calibration metrics and baselines; tune OCEAN weight constants
if arcs collapse at scale. Mark BLOCKED pending D05 audit run.

### Step 7 — Update tracking ticket (this ticket)

- Add all new epics to "Related Tickets" section.
- Add Combat Ecology Extension gate note (not yet unblocked — needs 5k-tick data).
- Update Implementation Notes.

## Scope Guards

- Do NOT implement any deferred features — only create epic tracking tickets.
- Do NOT modify any `src/` code.
- Do NOT modify parity ledger (no behavior changes).
- The new epic tickets go in `tickets/todos/` (root level or a `deferred-p3/` subfolder).
  Use root `tickets/todos/` to keep them discoverable.

## Dependency Map

Steps 1–6 are independent of each other (no ordering constraint between epic creations).
Step 7 depends on steps 1–6 (needs all epic IDs to link them).

## Files Changed

| File | Change |
|---|---|
| `tickets/todos/TCK-20260628-E-LONGRUN-REGRESSION.md` | New epic ticket |
| `tickets/todos/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md` | New epic ticket |
| `tickets/todos/TCK-20260628-E-RESOURCE-ECOLOGY.md` | New epic ticket |
| `tickets/todos/TCK-20260628-E-WORLD-EVOLUTION.md` | New epic ticket |
| `tickets/todos/TCK-20260628-E-PARTY-LOOP.md` | New epic ticket |
| `tickets/todos/TCK-20260628-E-PERSONALITY-CALIBRATION.md` | New epic ticket |
| `tickets/inprogress/TCK-20260627-P3A-DEFERRED-EPICS.md` | Update Related Tickets + Implementation Notes |

## Deviations

None recorded yet.
