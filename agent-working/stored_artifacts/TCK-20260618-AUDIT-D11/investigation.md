# D11 Investigation — Dead Code & Orphaned Modules

## Method

Import graph built via grep: for each top-level `src/` directory, check whether any
file in `src/` or `tests/` contains `from <dir>.` or `from src.<dir>.` or `import <dir>.`
outside of the directory itself. Zero importers = confirmed orphan cluster.

Also scanned for: deprecated/legacy code markers, commented-out class/function definitions,
and suspiciously named backup/draft files in `src/`.

## Baseline

- `src_legacy/` — does NOT exist (confirmed)
- `tests_legacy/` — does NOT exist (confirmed)
- Deprecated/TODO:remove markers in src/ — 2 inline comments (LEGACY_FALLBACK, LEGACY GUARD), not dead files
- Commented-out def/class blocks in src/ — none found
- Backup/temp/draft named files in src/ — none found

## Orphan Directory Inventory

All 9 directories below: zero importers in live `src/` pipeline AND zero direct imports in `tests/`.
The orphan files do import from each other and from `src.core.*` (which is live), but nothing
external imports FROM them.

| Directory | Files | Bytes | Lines | Character |
|---|---|---|---|---|
| `src/town/` | 10 | 23,427 | 625 | V1 building-level logic (blacksmith, inn, shop, guild, home) |
| `src/content_semantics/` | 4 | 19,724 | 522 | V1 faction/role/relation semantic helpers |
| `src/ai/` | 5 | 17,934 | 424 | V1 GoalScorer/ScoreModifier pattern |
| `src/entities/` | 4 | 15,127 | 446 | V1 archetype factory, contract builder, identity resolver |
| `src/progression/` | 5 | 12,839 | 349 | V1 leveling, breakthroughs, evolution, skills, veterancy |
| `src/actions/` | 3 | 5,335 | 148 | V1 attribute/harvest/loot action handlers |
| `src/quests/` | 3 | 6,252 | 185 | V1 quest generator/service/templates |
| `src/runtime/` | 1 | 6,049 | 193 | V1 bootstrap |
| `src/views/` | 1 | 2,162 | 63 | V1 readiness view |
| **Total** | **36** | **108,849** | **2,955** | |

## V2 Supersession Map

| Orphan cluster | V2 replacement |
|---|---|
| `src/ai/` GoalScorer subclasses | `src/domains/*/phase.py` XPhase.execute() pattern |
| `src/town/` building logic | `src/systems/economy_systems/`, `src/domains/` domain phases |
| `src/entities/` archetype factory | `src/worldassembly/resolver.py` + `src/content/resolver.py` |
| `src/progression/` leveling/skills | `src/domains/progression/phase.py` |
| `src/content_semantics/` | `src/content/` repository + catalog system |
| `src/actions/` | Authoritative pipeline typed updates |
| `src/quests/` | World module quest_definitions + `src/systems/` |
| `src/runtime/` bootstrap | `src/engine/kernel.py` |
| `src/views/` | `src/api/routes/` + observability layer |

## Key Confirmation: ai/ is V1 GoalScorer Pattern

`src/ai/goals/scorers.py` opens:
```python
from src.ai.goals.base import GoalScorer, GoalScore

class HarvestScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        ...
```

This is exactly the V1 pattern D12 F3 found documented (but stale) in `design_patterns.md`.
The V2 engine uses `domains/*/phase.py` with `execute()` returns instead.

`ai/personality.py` and `ai/score_modifiers.py` carry compliance IDs (SOC-142, COMB-093–099,
STRAT-166–174), confirming these were part of the live system at some prior milestone and
were formally verified — but are no longer reachable from any live code path.

## Non-Finding: systems/quest_generator.py

`src/systems/quest_generator.py` (2 lines):
```python
from src.systems.world_systems.quest_generator import QuestGenerator
__all__ = ["QuestGenerator"]
```

This is a thin re-export facade with 0 direct importers. The actual implementation in
`src/systems/world_systems/quest_generator.py` IS imported (70+ importers). The root-level
file is a vestigial re-export stub — low priority to remove, not a real dead code cluster.

## Scan Results for Other Dead Code Categories

| Category | Result |
|---|---|
| Commented-out def/class blocks | None found in src/ |
| Files named *_old, *_backup, *_draft, *_temp | None found in src/ |
| `# DEPRECATED` / `# TODO: remove` markers | 2 inline comments (LEGACY_FALLBACK, LEGACY GUARD) — runtime guards, not dead code |
| `src_legacy/` / `tests_legacy/` directories | Do not exist |
