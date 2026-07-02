---
ticket_id: TCK-20260619-E63-FEATURE-PACKS
phase: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E63-FEATURE-PACKS

## Summary

Pluggable Feature Pack Architecture (Epic 6.3) is a Phase 6 long-horizon deferred bet.
Zero code exists. The epic generalizes the extension patterns already in
`adventure_routing_contract.md` and `world_emergence_contract.md` into a self-describing
manifest system with runtime profile selection and compatibility resolution.

**Decision Gate Status: NOT SATISFIED.**
Gate requires ≥3 independent features added via the existing extension patterns.
E53 child tickets (war, diplomacy, faction history) are scoped but not yet implemented.
This epic cannot start implementation until the gate is re-evaluated post-E53.

---

## Extension Pattern Inventory (Re-use Sources)

### 1. Adventure Routing Extension Pattern
- `docs/simulation/domains/adventure_routing_contract.md` — defines `enum → generator
  → scorer → mapper → tests` pattern for adding new route types
- RouteFamily enum + generator + scorer = one complete extension unit
- Pattern proven for: EXPLORE, TRADE, PROTECT_TARGET, OWN_SURVIVAL (E41D added last two)
- **Extension count via this pattern: 2 (EXPLORE, TRADE at baseline + 2 from E41D = 4 route families)**

### 2. World Emergence Extension Pattern
- `docs/simulation/domains/world_emergence_contract.md` — defines pattern for adding
  new world event types and regional pressure models
- WorldEventCategory + DemographicCycleService + RegionalPressureModel = one unit
- Pattern proven for: POPULATION_BIRTH, POPULATION_DEATH, POPULATION_MIGRATION (E52)
- **Extension count via this pattern: 3 (all from E52)**

### 3. Content Pack Format
- `docs/content/content_pack_format.md` — versioned, dependency-aware bundle of
  catalog records. frontier_extended_pack is one concrete example.
- This is content-level not code-level extension; partially relevant as a model for
  FeaturePackManifest format design.

### 4. Decision Gate Assessment
Gate: "≥3 independent features added via the existing extension points."
- Adventure routing: 4 route families (EXPLORE/TRADE/PROTECT_TARGET/OWN_SURVIVAL)
- World emergence: 3 new event types (BIRTH/DEATH/MIGRATION) 
- **Verdict: Gate appears numerically satisfied (≥3 in each pattern)**
- **But:** Gate intent requires E53 features (faction decisions, diplomacy, war directives)
  to also be proven via these patterns before generalizing. E53 child tickets are scoped
  but not implemented. Re-evaluate after E53Aa–E53Dd are complete.

---

## What Does NOT Exist (Gap Inventory)

| Gap | Notes |
|---|---|
| `FeaturePackManifest` | Zero code — needs fresh design (YAML + Python module entry points) |
| `RuntimeProfile` | Zero code — selects active packs per simulation run |
| `CompatibilityResolver` | Zero code — dependency/conflict/version checking |
| `BalanceExperimentSpec` | Zero code — declarative balance test harness per pack |
| `docs/architecture/feature_pack_architecture.md` | Not created |
| Parity ledger entries for pack loading | Not in infrastructure.yaml |

---

## Architecture Sketch (Pre-Gate — Speculative)

```
FeaturePackManifest (YAML)
  ├─ name, version, dependencies
  ├─ extension_points: [{domain: adventure_routing, class: MyRouteGenerator}]
  └─ balance_specs: [{test: my_balance_test, baseline: default_profile}]

RuntimeProfile
  └─ active_packs: [base, faction_pack, culture_pack]
       └─► CompatibilityResolver.resolve(packs) → sorted load order

Engine boot:
  RuntimeProfile → CompatibilityResolver → load pack modules → register entry points
  into existing enum/generator/scorer registries
```

Key insight: existing registries (RouteFamily, WorldEventCategory) are already
extensible via enum addition. The manifest layer adds discovery and ordering on top —
it does NOT replace the underlying extension pattern.

---

## Risks

1. **Gate not yet truly satisfied by intent.** Numeric count passes but E53 faction
   extension points (new directive types, faction state enum expansion) must be proven
   before generalizing.
2. **Enum extensibility.** Python enums are closed — adding new RouteFamily values in
   a pack requires a registry pattern (dict-based, not enum-based). This is the primary
   architectural shift E63 must make.
3. **XL effort.** Estimated XL effort — the largest epic in Phase 6. Should not start
   until all of Phase 5 and at least E61/E62 are implemented.
4. **Scope creep risk.** BalanceExperimentSpec is genuinely novel and could balloon.
   Scope conservatively: spec must be a pure declarative YAML, not a new test framework.
