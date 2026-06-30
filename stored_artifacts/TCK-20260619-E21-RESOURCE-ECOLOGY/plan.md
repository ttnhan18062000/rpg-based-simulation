---
ticket_id: TCK-20260619-E21-RESOURCE-ECOLOGY
phase: plan
date: 2026-06-20
---

# Plan: Resource Ecology Regeneration — Epic Scope

## Revised Child Ticket Scope

After investigation, E21D (scarcity signal to WorldEmergencePhase) is already wired.
The consumer code in `world_emergence/models.py` is ready. The only missing piece is
the **emitter** (covered in E21B). E21D is therefore a verification + parity ticket only.

```
E21A (schema extension)     ──► E21B (emitter + regen loop) ──► E21C (scoring wire-up)
                                                                    │
                                                              E21D (verify + parity)
```

E21A must complete before E21B (regen_rate_per_tick field required).
E21B must complete before E21C (depletion state must exist before scoring reads it).
E21D can run after E21B (just verification + parity, no new code).

## Child Ticket Summary

| Ticket | Scope | Files |
|---|---|---|
| E21A-NODE-SCHEMA | Add `regen_rate_per_tick` to `ResourceNodeState`; add `RESOURCE_RECOVERED` to `WorldEventCategory` | `src/core/state.py`, `src/domains/world_emergence/schema.py` |
| E21B-REGEN-SERVICE | Emit `RESOURCE_DEPLETED` in harvest apply path; add charge regen to `ResourceEcologyService` (fixed_rate only); emit `RESOURCE_RECOVERED` on regen from 0 | `src/world/ecology.py`, harvest apply path |
| E21C-SCORING-WIRE | Reduce `expected_benefit` proportionally to depletion fraction in `AdventureRouteScorer.score()` | `src/domains/adventure/scoring.py` |
| E21D-SCARCITY-VERIFY | Verify scarcity consumer fires; update parity ledger; update docs | `docs/parity_ledger/town_resource.yaml`, `docs/mechanics/03_economic_laws.md` |

## Acceptance Path

1. E21A: `ResourceNodeState(regen_rate_per_tick=2)` constructs and serializes correctly
2. E21B: 1000-tick run emits `RESOURCE_DEPLETED` and `RESOURCE_RECOVERED` events
3. E21C: depleted node scores ≤ 0.5× full node of same type
4. E21D: `RegionalPressureModel` scarcity field increases after depletion window; parity entry added

## Out of Scope for E21

- `seasonal` and `ecology_linked` regen models (Phase 3+ — add after fixed_rate proven)
- Faction territorial claims over depleted nodes (Epic 5.3)
- Population migration from depletion (Epic 5.2)
