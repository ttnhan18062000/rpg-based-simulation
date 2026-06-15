# Implementation Sequence — World Generation Module Epic

Strict dependencies enforced. Complete each ticket before starting dependents.

> **Sequence updated 2026-06-15** per architectural review (world_mod_ticket_review.md):
> - WORLDSCEN-PERSPECTIVES moved earlier (after WORLDMOD-UNIFY, before data expansion)
> - WORLDGEN-E2E-SMOKE added as final epic gate
> - WORLDMOD-PACKS now uses explicit `pack_refs` field (not overloaded `catalog_refs`)
> - WORLDGEN-SCORING returns `ModuleScore` with explanation/provenance
> - WORLDGEN-COMPOSE has strict conflict policy (GenerationCompositionError)
> - WORLDDAT-COMPOSE 10-tick smoke moved to WORLDGEN-E2E-SMOKE
> - WORLDDAT-NEWMODS has anti-drift rule: modules compose, do not invent behavior

## Phase 1 — Foundation

1. **TCK-20260614-WORLDMOD-UNIFY** — unified schema first; everything else builds on it
2. **TCK-20260614-WORLDSCEN-PERSPECTIVES** — wire CompileContext.perspectives; moved earlier so perspective semantics are clear before data expansion or generated compositions reference `default_perspectives`
3. **TCK-20260614-WORLDMOD-PARAMS** — expression engine; required before any parametric module data
4. **TCK-20260614-WORLDMOD-PACKS** — pack validation via explicit `pack_refs` field; no dependency on params
4. **TCK-20260614-WORLDMOD-QUEST-SCHEMA** — QuestDefinition schema; required before module quest contribution
5. **TCK-20260614-WORLDMOD-QUEST-MOD** — quest contribution; requires QUEST-SCHEMA

Phase 1 tickets 4 (PACKS) and 4 (QUEST-SCHEMA) can run in parallel after WORLDMOD-PARAMS.

## Phase 2 — Procedural Generation (after Phase 1)

6. **TCK-20260614-WORLDGEN-SCORING** — ModuleScorer returning ModuleScore with explanation; requires unified schema
7. **TCK-20260614-WORLDGEN-COMPOSE** — composition generator with strict conflict policy; requires SCORING
8. **TCK-20260614-WORLDGEN-SEED-PARAMS** — seed randomization; requires COMPOSE + PARAMS

## Phase 3 — Data Expansion (after Phase 1 complete)

9. **TCK-20260614-WORLDDAT-MIGRATE** — migrate existing YAML; requires UNIFY + QUEST-MOD
10. **TCK-20260614-WORLDDAT-NEWMODS** — new modules (compose lower defs, no primitive behavior); requires MIGRATE + PARAMS + QUEST-MOD
11. **TCK-20260614-WORLDDAT-COMPOSE** — new compositions (load/assemble/compile only, no runtime smoke); requires NEWMODS

## Phase 4 — Epic Gate

12. **TCK-20260614-WORLDGEN-E2E-SMOKE** — 10-tick smoke for all new compositions + generated world; requires WORLDDAT-COMPOSE + WORLDGEN-COMPOSE

## Dependency Graph

```
WORLDMOD-UNIFY
  ├── WORLDSCEN-PERSPECTIVES
  ├── WORLDMOD-PARAMS
  │     ├── WORLDMOD-PACKS
  │     ├── WORLDMOD-QUEST-SCHEMA
  │     │     └── WORLDMOD-QUEST-MOD
  │     │           └── WORLDDAT-MIGRATE
  │     │                 └── WORLDDAT-NEWMODS
  │     │                       └── WORLDDAT-COMPOSE
  │     │                             └── WORLDGEN-E2E-SMOKE
  │     └── WORLDGEN-SEED-PARAMS (also needs WORLDGEN-COMPOSE)
  └── WORLDGEN-SCORING
        └── WORLDGEN-COMPOSE
              ├── WORLDGEN-SEED-PARAMS
              └── WORLDGEN-E2E-SMOKE
```

## Already Done — Do NOT Re-implement

- Relationship resolver wiring (`src/worldassembly/resolver.py:209,543,711`)
- `SimulationScenarioDefinition` (`src/scenarios/schema.py`)
- `ScenarioWorldFeatureValidator` (`src/scenarios/feature_validator.py`)
- `ScenarioSetupResolver` (`src/scenarios/resolver.py`)
