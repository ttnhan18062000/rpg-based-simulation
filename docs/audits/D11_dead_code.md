---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, dead-code, orphaned-modules, v1-legacy, cleanup, ai, town, progression, entities]
---

# D11 — Dead Code & Orphaned Modules

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Codebase / Architecture |
| **State** | `done` |
| **Impact** | 2 / 5 |
| **Interest** | 2 / 5 |
| **Priority** | 4 |
| **Method** | measure |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** What code exists in `src/` but is never reached from the
live pipeline — and how much confusion or maintenance risk does it create?

**Related dimensions:** D12 (Pattern Consistency) — F3 there identified `design_patterns.md`
as documenting V1 GoalScorer/StateHandler patterns; D11 confirms those patterns exist as
live files in `src/ai/`; D09 (System Wiring) — established 61 `[E]` features are all
reachable; D11 maps the unreachable surface.

---

## Measure Method

Import graph built via grep: for each top-level `src/` directory, the number of files
in `src/` and `tests/` containing `from <dir>.`, `from src.<dir>.`, or `import <dir>.`
(outside the directory itself) was counted. Zero external importers = confirmed orphan
cluster. Supplementary scans checked for: deprecated markers, commented-out code, and
backup-named files.

Each orphan cluster is scored by Dead Code Risk — how much its presence harms the
developer navigating or extending the codebase.

### Dead Code Risk Scoring

3 dimensions, each 1–5. Maximum: 15. Higher score = more urgent to remove.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Confusion Risk** | Clearly separate from live code; unlikely to be confused | Same domain as live code; a developer might reach for it | Identical purpose to a live module; easy to import the wrong one |
| **Volume** | < 5 files / < 5 KB | 5–15 files / 5–30 KB | > 15 files / > 30 KB or > 2,000 lines |
| **Compliance Debt** | No prior compliance IDs; purely experimental | Has compliance IDs but were never verified | Compliance IDs present, once verified — formal ledger drift if removed without updating parity ledger |

---

## Orphan Cluster Inventory

**Total: 36 files, 108,849 bytes (~106 KB), 2,955 lines** of unreachable V1 code.

All clusters below have confirmed zero importers from the live `src/` pipeline and zero
direct imports from `tests/`. Orphan files do import from each other and from `src.core.*`
(live), but nothing external reaches into them.

| Directory | Files | Lines | V2 replacement |
|---|---|---|---|
| `src/town/` | 10 | 625 | `src/systems/economy_systems/` + domain phases |
| `src/content_semantics/` | 4 | 522 | `src/content/` repository + catalog |
| `src/ai/` | 5 | 424 | `src/domains/*/phase.py` XPhase pattern |
| `src/entities/` | 4 | 446 | `src/worldassembly/resolver.py` + `src/content/resolver.py` |
| `src/progression/` | 5 | 349 | `src/domains/progression/phase.py` |
| `src/quests/` | 3 | 185 | World module `quest_definitions` + `src/systems/` |
| `src/actions/` | 3 | 148 | Authoritative pipeline typed updates |
| `src/runtime/` | 1 | 193 | `src/engine/kernel.py` |
| `src/views/` | 1 | 63 | `src/api/routes/` + observability layer |

---

## Key Findings

### F1 — src/ai/: V1 GoalScorer system is live dead code with compliance IDs — Priority: 12 / 15

| Dimension | Score | Reason |
|---|---|---|
| Confusion Risk | 5 | `src/ai/goals/scorers.py` is structurally identical to what a developer would write following `design_patterns.md` (D12 F3) — the file exists, imports succeed, classes are coherent |
| Volume | 2 | 5 files, 424 lines — moderate |
| Compliance Debt | 5 | `ai/personality.py` carries IDs SOC-142, STRAT-166–174, STRAT-178–179; `ai/score_modifiers.py` carries COMB-093–099. These were formally verified at a prior milestone. Removing without updating the parity ledger creates ledger drift. |
| **Total** | **12** | |

`src/ai/goals/scorers.py` implements V1-style `GoalScorer` subclasses:

```python
from src.ai.goals.base import GoalScorer, GoalScore

class HarvestScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        ...
```

This is the exact pattern that `docs/guidelines/design_patterns.md` documents as the
"Goal Plugin" extension point — but the V2 engine uses `XPhase.execute()` domain phases,
not `GoalScorer` subclasses. The files are syntactically valid, import successfully, and
are never called from any live path.

The compliance IDs create a formal debt: if `src/ai/` is deleted without updating the
parity ledger entries for SOC-142, COMB-093–099, and STRAT-166–174, the ledger will
show verified claims for functionality that no longer exists in any form.

**Action:** Before deleting `src/ai/`, audit each compliance ID — if the V2 domain phase
provides the same behavior, migrate the parity ledger entry's `v2_evidence` to the domain
phase test path. If the behavior no longer exists at all, mark as `legacy_verified` with
a note.

---

### F2 — src/town/: V1 building system is the largest orphan cluster — Priority: 11 / 15

| Dimension | Score | Reason |
|---|---|---|
| Confusion Risk | 4 | `src/town/blacksmith.py`, `src/town/shop.py` etc. look like live game systems; a developer implementing building interactions might reach for these before checking `src/systems/economy_systems/` |
| Volume | 4 | 10 files, 625 lines, 23 KB |
| Compliance Debt | 3 | No compliance IDs found; code imports from `src.core.state` with current field names suggesting it was updated to match V2 state types before being orphaned |
| **Total** | **11** | |

10 files implement building-level interaction logic: `blacksmith.py`, `class_hall.py`,
`guild.py`, `home.py`, `home_storage.py`, `inn.py`, `shop.py`, `sabotage.py`,
`town_navigation.py`, `buildings.py`.

`src/town/guild.py` imports from `src/quests/generator` (another orphan), making `src/quests/`
exclusively reachable only from `src/town/`. Both clusters can be deleted together.

The `src/systems/economy_systems/` directory provides the live equivalents:
`economy.py`, `crafting.py`, `market.py`, `town_service.py`.

---

### F3 — src/entities/: V1 archetype factory superseded by WorldAssemblyResolver — Priority: 9 / 15

| Dimension | Score | Reason |
|---|---|---|
| Confusion Risk | 4 | `archetype_factory.py` and `identity_resolver.py` are exactly what a developer would look for when working on entity creation — but `src/worldassembly/resolver.py` and `src/content/resolver.py` are the live implementations |
| Volume | 2 | 4 files, 446 lines |
| Compliance Debt | 3 | `entities/archetype_factory.py` references archetype resolution — same domain as `EntityArchetypeResolver` in `src/content/resolver.py:L386`. Overlap could mislead agent context search. |
| **Total** | **9** | |

4 files: `archetype_factory.py`, `contract_builder.py`, `identity_resolver.py`,
`runtime_contract.py`. These are V1 entity construction helpers that predate
`WorldAssemblyResolver` (which D16 confirmed is the V2 entry point for entity archetype
resolution via catalog-driven assembly).

The name collision between `src/entities/identity_resolver.py` and live resolvers in
`src/content/resolver.py` / `src/worldassembly/resolver.py` is the primary confusion risk.

---

### F4 — src/progression/: V1 leveling services orphaned — Priority: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Confusion Risk | 3 | `BreakthroughService`, `EvolutionService`, `LevelingService` — same domain as `src/domains/progression/phase.py` which is live |
| Volume | 2 | 5 files, 349 lines |
| Compliance Debt | 2 | No compliance IDs; `progression/leveling.py` is standalone with no cross-references to parity ledger entries |
| **Total** | **7** | |

5 files providing V1 leveling, breakthroughs, evolution, skills, and veterancy services.
`src/domains/progression/phase.py` is the V2 live equivalent. Both exist in the codebase
simultaneously with no import relationship.

---

### F5 — src/content_semantics/: V1 faction semantic helpers orphaned — Priority: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Confusion Risk | 3 | Faction/role semantic helpers look useful; `src/content/resolver.py` is the live equivalent |
| Volume | 3 | 4 files, 522 lines, 19 KB |
| Compliance Debt | 1 | No compliance IDs; experimental helpers |
| **Total** | **7** | |

4 files: `faction.py` (208 lines), `relation.py` (161 lines), `role.py` (79 lines),
`defaults.py` (74 lines). These are V1 semantic helpers for faction/relationship/role
interpretation. The live `src/content/resolver.py` handles the same domain via the
catalog system.

---

### F6 — src/quests/, src/actions/, src/runtime/, src/views/ — Priority: 4 / 15 each

Small clusters, lower confusion risk:

| Cluster | Files | Lines | Notes |
|---|---|---|---|
| `src/quests/` | 3 | 185 | Only imported by orphaned `src/town/guild.py`; delete with town/ |
| `src/actions/` | 3 | 148 | V1 action handlers (harvest, loot, attributes); superseded by typed updates |
| `src/runtime/` | 1 | 193 | V1 `bootstrap.py`; superseded by `engine/kernel.py` |
| `src/views/` | 1 | 63 | V1 readiness view; superseded by `api/routes/` |

Each scores 4/15 — small volume, low confusion risk, no compliance IDs.

---

### Dead Code Risk Summary

| Finding | Cluster | Lines | Risk Score |
|---|---|---|---|
| F1 | `src/ai/` — V1 GoalScorer with compliance IDs | 424 | **12 / 15** |
| F2 | `src/town/` — V1 building system | 625 | **11 / 15** |
| F3 | `src/entities/` — V1 archetype factory | 446 | **9 / 15** |
| F4 | `src/progression/` — V1 leveling services | 349 | **7 / 15** |
| F5 | `src/content_semantics/` — V1 faction semantics | 522 | **7 / 15** |
| F6 | `src/quests/`, `src/actions/`, `src/runtime/`, `src/views/` | 489 | **4 / 15** each |

---

## Clean Findings (No Dead Code)

The supplementary scan confirms the codebase is otherwise clean:

| Category | Result |
|---|---|
| Commented-out `def`/`class` blocks in `src/` | None found |
| Files named `*_backup`, `*_old`, `*_temp`, `*_draft` | None found |
| `# DEPRECATED` / `# TODO: remove` markers | 2 inline runtime guards — not dead code |
| `src_legacy/` directory | Does not exist |
| `tests_legacy/` directory | Does not exist |
| `systems/` root-level files | All 1+ importers except `systems/quest_generator.py` (2-line re-export stub) |

The main `src/` codebase (excluding the 9 orphan directories) is free of conventional
dead code indicators.

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| **P1** | Audit `src/ai/` compliance IDs (SOC-142, COMB-093–099, STRAT-166–179) against parity ledger before deletion — migrate `v2_evidence` to domain phase test paths or mark `legacy_verified` | F1 — compliance debt |
| **P1** | Delete `src/ai/` after parity ledger audit | F1 |
| **P1** | Delete `src/town/` and `src/quests/` together (cross-dependent orphan pair) | F2 + F6 |
| P2 | Delete `src/entities/` — verify no hidden `from src.entities.` import exists first | F3 |
| P2 | Delete `src/progression/`, `src/content_semantics/`, `src/actions/`, `src/runtime/`, `src/views/` | F4 + F5 + F6 |
| P2 | Update `docs/guidelines/design_patterns.md` to remove V1 GoalScorer/StateHandler documentation (or archive section) — coordinated with D12 F3 follow-up | F1 + D12 F3 |
| P3 | Remove `src/systems/quest_generator.py` 2-line re-export stub | minor |

**Safe deletion order:** `src/views/`, `src/runtime/`, `src/actions/` first (no cross-deps);
then `src/quests/` + `src/town/` together; then `src/entities/`, `src/progression/`,
`src/content_semantics/`; finally `src/ai/` after parity ledger audit.

---

## Related Dimensions

- **D12 (Pattern Consistency)** — F3 there identified `design_patterns.md` as documenting V1 GoalScorer/StateHandler patterns. D11 confirms those patterns are not just in the doc but in live orphaned code in `src/ai/`. Both findings share the same P1 cleanup action.
- **D09 (System Wiring)** — D09 confirmed all 61 `[E]` features have live code paths. D11 maps the complementary surface: what exists but is never reached. Together they give a complete wiring picture.
- **D17 (Documentation Currency)** — `design_patterns.md` describes `GoalScorer` as a live extension point. D11 confirms the underlying code (`src/ai/goals/base.py`, `scorers.py`) still exists but is orphaned. A developer following the doc would write code against a dead pattern.
