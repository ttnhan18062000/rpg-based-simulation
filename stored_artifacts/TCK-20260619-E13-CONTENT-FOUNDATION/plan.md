---
ticket_id: TCK-20260619-E13-CONTENT-FOUNDATION
phase: plan
date: 2026-06-20
---

# Plan: Content Foundation Layer — Epic Scope

## Child Ticket Sequence

E13A and E13B can run in parallel (no dependency between quest defs and module types).
E13C (recipes) is independent of both.
E13D (scenarios) is independent but benefits from E13A quests being in the modules.

Recommended order: A → B → C → D (sequential, lowest-to-highest risk).
But E13A and E13C have no dependency — can be batched if running fast.

```
E13A (quest defs) ─────────────────────┐
E13B (module types) ───────────────────┤─► E13 DONE
E13C (recipes) ────────────────────────┤
E13D (scenarios) ──────────────────────┘
```

## Child Ticket Summary

| Ticket | Scope | Deliverable |
|---|---|---|
| E13A-QUEST-DEFS | 30+ quest definitions across 10 modules | Updated module YAMLs + test |
| E13B-MODULE-TYPES | 4 new modules (terrain ×2, population ×2) | New YAML files |
| E13C-RECIPES | 8 → 25+ crafting recipes, gather→craft chain | Updated recipes.yaml + test |
| E13D-SCENARIOS | 6+ scenarios for dungeon/urban/wilderness | New scenarios YAML + test |

## Acceptance Path

1. E13A: `urban_political` modules get quest defs → `test_quest_starts_in_urban_political` passes
2. E13C: gather→craft chain added → `test_crafting_chain_completes` passes
3. E13D: ≥2 scenarios per world → `test_all_world_compositions_have_two_scenarios` passes
4. E13 epic ticket: move to done after all 4 children DONE

## Key Risk

E13B: if `CatalogValidator` has a hardcoded allowlist for `module_type`, `terrain` and `population`
must be added. Check `src/content/validator.py` before authoring — this is the first step of E13B.
