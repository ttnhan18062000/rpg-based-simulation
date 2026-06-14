# Implementation Sequence — World Generation Module Epic

Strict dependencies enforced. Complete each ticket before starting dependents.

## Phase 1 — Foundation (implement in order)

1. **TCK-20260614-WORLDMOD-UNIFY** — unified schema first; everything else builds on it
2. **TCK-20260614-WORLDMOD-PARAMS** — expression engine; required before any parametric module data
3. **TCK-20260614-WORLDMOD-PACKS** — pack validation; no dependency on params
3. **TCK-20260614-WORLDMOD-QUEST-SCHEMA** — QuestDefinition schema; required before module quest contribution
4. **TCK-20260614-WORLDMOD-QUEST-MOD** — quest contribution; requires QUEST-SCHEMA

Phase 1 tickets 3 and 3 (PACKS and QUEST-SCHEMA) can run in parallel after WORLDMOD-UNIFY.

## Phase 2 — Procedural Generation (after Phase 1)

5. **TCK-20260614-WORLDGEN-SCORING** — module scorer; requires unified schema
6. **TCK-20260614-WORLDGEN-COMPOSE** — composition generator; requires SCORING
7. **TCK-20260614-WORLDGEN-SEED-PARAMS** — seed randomization; requires COMPOSE + PARAMS

## Phase 3 — Data Expansion (after Phase 1 complete)

8. **TCK-20260614-WORLDDAT-MIGRATE** — migrate existing YAML; requires UNIFY + QUEST-MOD
9. **TCK-20260614-WORLDDAT-NEWMODS** — new modules; requires MIGRATE + PARAMS + QUEST-MOD
10. **TCK-20260614-WORLDDAT-COMPOSE** — new compositions; requires NEWMODS

## Phase 4 — Scenario Layer (after Phase 3)

11. **TCK-20260614-WORLDSCEN-PERSPECTIVES** — perspective resolution; requires UNIFY + COMPOSE data

## Dependency Graph

```
WORLDMOD-UNIFY
  ├── WORLDMOD-PARAMS
  │     └── WORLDGEN-SEED-PARAMS
  ├── WORLDMOD-PACKS
  ├── WORLDMOD-QUEST-SCHEMA
  │     └── WORLDMOD-QUEST-MOD
  │           └── WORLDDAT-MIGRATE
  │                 └── WORLDDAT-NEWMODS
  │                       └── WORLDDAT-COMPOSE
  │                             └── WORLDSCEN-PERSPECTIVES
  └── WORLDGEN-SCORING
        └── WORLDGEN-COMPOSE
              └── WORLDGEN-SEED-PARAMS

```

## Already Done — Do NOT Re-implement

- Relationship resolver wiring (`src/worldassembly/resolver.py:209,543,711`)
- `SimulationScenarioDefinition` (`src/scenarios/schema.py`)
- `ScenarioWorldFeatureValidator` (`src/scenarios/feature_validator.py`)
- `ScenarioSetupResolver` (`src/scenarios/resolver.py`)
