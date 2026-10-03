---
ticket: TCK-20260627-P3A-DEFERRED-EPICS
phase: Investigate
date: 2026-06-28
---

# Investigation — TCK-20260627-P3A-DEFERRED-EPICS

## Current Behavior

This is a gate-check and epic-tracking ticket. There is no runtime behavior to audit.
The ticket's job is to review which of 7 P3-deferred feature items are now unblocked and
create child epic tickets for each unblocked item.

Source for deferred items: `docs/plans/audit_fix_plan.md` §P3-A and `docs/audits/D01_rpg_feature_impact.md` §[P] items.

## Gate Condition Assessment

All P0, P1, and P2 tickets from the audit fix plan are in `tickets/done/`. Confirmed:

| Ticket | Status |
|---|---|
| P0-A (adventure flag) | DONE |
| P0-B (urban resource nodes) | DONE |
| P0-C (entity region assignment) | DONE |
| P1-A (rejection backoff) | DONE |
| P1-B (quest activation) | DONE |
| P1-E through P1-I | DONE |
| P2-A through P2-P | DONE |
| P3-B (obs mode remap) | DONE |
| P3-C (doc currency) | DONE |
| P3-D (catalog browser) | DONE |

Only `TCK-20260627-P3A-DEFERRED-EPICS` (this ticket) remains as a todo.

## Per-Item Gate Status

### 1. Long-Horizon Regression Suite
**Gate:** P1-A rejection cascade fix  
**Status: GATE MET ✓**  
P1-A (TCK-20260627-P1A-REJECTION-BACKOFF) is in `tickets/done/`. The ticket's own
acceptance criteria explicitly names this as "highest-value first unblock" and says the
epic should be created immediately. No automated 5,000-tick regression test exists.

### 2. Narrative Consequence Layer
**Gate:** E51/E43B episode-boundary systems complete  
**Status: GATE MET ✓**  
From D01 (verified status entries):
- E51A–E51E (ChronicleCompiler): DONE — `ChronicleCompiler` in `src/domains/chronicle/`;
  `ChronicleNamer`, `ChronicleGrouper`, `ChronicleRenderer`, `EventSignificanceScorer`
  implemented; REST `GET /chronicle/{world_id}` live.
- E43A–E43E (CampaignOrchestrator / SocialMemoryRecord): DONE — `CampaignOrchestrator._advance_state()`
  wired; `SocialMemoryDecay`, `SocialMemoryExporter/Importer` implemented.
- Remaining gap per D01: real-time "grief/rage → motivation urgency" feedback loop and
  nemesis formation from chronicle events are not yet modeled. This is the scope for the new epic.

### 3. Resource Ecology Regeneration
**Gate:** P0 fixes complete; run D06 5,000-tick  
**Status: PARTIAL — P0 fixes DONE, 5,000-tick validation not yet run**  
P0-A/B/C all done. E21B added `ResourceNodeRegenerationService` with seasonal multipliers.
Remaining gaps: density-dependent rates, multi-stage ecological cycles, cross-region
pressure propagation. The 5,000-tick run is a validation prerequisite before the epic
can be properly scoped. Gate not fully met.

### 4. World Evolution System
**Gate:** P0 fixes + D06 5,000-tick run  
**Status: PARTIAL — P0 fixes DONE, 5,000-tick run not yet done**  
Regional trauma, sovereignty, and basic ecology systems exist. `WorldEmergencePhase`
evaluates `RegionalPressureModel`, `ScarcityModel`, `ServiceStatePressureModel`.
Complex regeneration cycles and seasonal multi-region propagation are missing.
Gate not fully met (same 5k-tick blocker as Resource Ecology).

### 5. Personality → Long-Run Behavior Calibration
**Gate:** P0-A fix; run D05-style audit at 1,000+ ticks  
**Status: PARTIAL — P0-A DONE, calibration audit not yet run**  
OCEAN traits, mood, grudges all implemented. TCK-20260627-P2O-ENTITY-PERSONALITY-OBS
(done) added per-entity personality snapshot in LIGHT observability mode. No validation
run at 1,000+ ticks proving personality produces distinct behavioral arcs at scale.
Gate not fully met.

### 6. Combat Ecology Extension
**Gate:** D06 5,000-tick data available  
**Status: NOT MET — requires 5k-tick run**  
AoE and wound system verified [E]. Ecology pressure-driven encounter spawning is missing.
Gate entirely conditional on the 5,000-tick run. Not yet met.

### 7. Full Party Adventure Loop
**Gate:** E61B implemented + HERO role populated  
**Status: PARTIAL — E61B DONE, HERO role population uncertain**  
TCK-20260619-E61B-PLAN-EXPORTER is in done/. However:
- The Full Party Adventure Loop ([P] per D01) depends on class-compatibility scoring (not yet implemented).
- E41B–E41D added `PartyLifecycleService`, `FairShareProtocol`, `BetrayalDesertionEvent`.
  The remaining gap is party composition optimization.
- "HERO role populated" status is not verifiable from existing done tickets — no ticket
  directly addresses HERO role population.
Gate partially met (E61B done); HERO role status unclear.

## Summary

| Item | Gate Met? | Action |
|---|---|---|
| Long-Horizon Regression Suite | YES ✓ | Create epic now |
| Narrative Consequence Layer | YES ✓ | Create epic now |
| Resource Ecology Regeneration | PARTIAL | Create planning epic with gating note |
| World Evolution System | PARTIAL | Create planning epic with gating note |
| Personality → Long-Run Calibration | PARTIAL | Create planning epic with gating note |
| Combat Ecology Extension | NO | Note gate unmet; no epic yet |
| Full Party Adventure Loop | PARTIAL | Create planning epic with gating note |

## Prior Work

- `docs/audits/D01_rpg_feature_impact.md` — authoritative [P] item source and status
- `docs/plans/audit_fix_plan.md` §P3-A — maps all 7 deferred items to gate conditions
- `docs/plans/long_term_development_roadmap.md` — phase structure for Long Horizon phase
- All P0/P1/P2 tickets in `tickets/done/` — gate prereqs confirmed complete

## Risks and Open Questions

1. The D06 5,000-tick run is a prerequisite for 3 items (Resource Ecology, World Evolution,
   Combat Ecology). Should a dedicated "run D06 at 5,000 ticks" ticket be created? This is
   a measurement task, not a feature ticket — it belongs as an epic prerequisite note.
2. HERO role population status for Full Party Adventure Loop is unclear. The epic should
   include investigation of whether this role exists in archetypes/content.
3. "Immediately create" for Long-Horizon Regression Suite (from acceptance criteria) means
   this epic must be created as part of this ticket's implementation.

## Anti-Drift Hazards

- Do not implement any of the deferred features in this ticket — each gets its own epic.
- Do not mark Combat Ecology Extension or the 5k-tick-gated items as unblocked without
  the actual 5,000-tick run being completed.
