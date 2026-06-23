---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, backlog, cheap-fixes, doc-debt, ci, dead-code, product-surface, roadmap]
date: 2026-06-23
source: docs/audits/audit_dimensions.md
---

# Open Audit Findings — Implementation Backlog

## Purpose

This document captures all outstanding work items surfaced by the 18-dimension engine
audit (`TCK-20260618-AUDIT-EPIC`, completed 2026-06-19) that have not yet been
implemented as of 2026-06-23.

It is a companion to `engine_future_epics_roadmap.md` (which focuses on large epics)
and the audit detail files in `docs/audits/` (which are source-of-truth for findings).
When a item is resolved, update the status here and update the relevant parity ledger
entry or audit detail file.

**Epics already complete** (not repeated here): Worldgen, E53-Faction, E61-Progression,
E62-Culture-Drift, E63-Feature-Packs. The RC1/RC2/RC3 wiring bugs are also fixed.

---

## Section 1 — Cheap Fixes (not epics; handle as hotfix or small standard tickets)

These were explicitly flagged by the audit as "handle before epic prioritization." Most
are ≤1 day of work individually. Group them into a single batch ticket if preferred.

### 1A — Parity Ledger Debt (P0/P1)

Source: `docs/parity_ledger/combat_movement.yaml`, `strategic_cognition.yaml`,
`social_narrative.yaml`.

| ID | File | Status in Ledger | Work Required |
|---|---|---|---|
| `COMB-006` | combat_movement.yaml | `missing`, **P0** | AoE legality: impact-center vs. radius legality currently use a unified check; parity contract requires split. Fix legality check in `src/engine/pipeline_phases/` and add test. |
| `COMB-133` | combat_movement.yaml | `missing`, **P0** | "Phase 8 owns:" stub — empty ledger entry. Fill with actual phase-8 ownership statement and confirm against `pipeline.py`. |
| `COMB-134` | combat_movement.yaml | `missing`, **P0** | "Phase 9 owns:" stub — same as COMB-133. |
| `STRAT-164` | strategic_cognition.yaml | `missing`, **P0** | Missing parity test on an otherwise-certified subsystem. Add test; update ledger entry `test_path`. |
| `STRAT-177` | strategic_cognition.yaml | `missing`, **P0** | Same as STRAT-164. |
| `SOC-134` | social_narrative.yaml | `missing`, **P0** | Missing parity test. Add test; update ledger entry. |

### 1B — Determinism & Scoring Bugs

Source: D12 (Pattern Consistency), D04 (Balance & Tuning).

| Finding | Location | Issue | Fix |
|---|---|---|---|
| D12 F1 — unstable sort | `src/domains/adventure/generator.py`, `selector.py` | Candidates sorted by score with no `entity_id` tiebreaker — score ties produce non-deterministic tick ordering; replay can diverge silently. | Add `entity_id` (or stable secondary key) to all `sorted(candidates, key=...)` calls. |
| D04 — blocker penalty imbalance | `src/domains/adventure/scoring.py` | `blocker_penalty = 2.0` (fixed) vs. max achievable non-blocked score ~2.65. Any route with a single minor blocker scores near zero regardless of urgency, systematically excluding quests with any blocker condition. | Graduated penalty (e.g. proportional to number of blockers) or reduce fixed value. Recheck after quest generation epic. |

### 1C — Architecture Coupling Violations

Source: D14 (Coupling Depth).

| Finding | Location | Issue | Fix |
|---|---|---|---|
| D14 prohibited import | `src/domains/memory/phase.py` | Imports `TemporalPressureService` directly from `src/domains/time/`. Cross-domain import violates domain ownership. | Inject `TemporalPressureService` via the pipeline orchestrator constructor; remove direct import. |
| D14 upward coupling | `src/core/state.py` | `AuthoritativeState.__post_init__` constructs `MovementPlanCache` — a core data model instantiating an engine-layer service. Risk: `core/state.py` is imported by nearly every file; any import-time side-effect in `MovementPlanCache` propagates everywhere. | Move cache construction to the pipeline bootstrap; pass it into `AuthoritativeState` as an injected dependency. |

### 1D — WorldCompiler Personality Seeding

Source: D05 (Entity Differentiation), audit update section in `engine_future_epics_roadmap.md`.

| Finding | Location | Issue | Fix |
|---|---|---|---|
| Zero personality initialization | `WorldCompiler.compile()` | Produces `PersonalityComponent(greed=0.0, bravery=0.0, sociability=0.0, industry=0.0)` for every entity. OCEAN scoring formula is correctly implemented; the world compiler never seeds non-zero values. Entity differentiation is impossible from tick 0. | Seed personality from archetype/role distribution in `WorldCompiler.compile()`. Add a parity test confirming that two entities with different archetypes produce different `PersonalityComponent` values post-compile. |

### 1E — Dead Code Removal

Source: D11 (Dead Code & Orphaned Modules). 9 orphaned `src/` directories, ~36 files,
~2,955 lines of unreachable V1 code.

**Safe deletion order** (to avoid breaking cross-imports):

1. `src/views/runtime/actions/` — no inbound imports
2. `src/town/` and `src/quests/` — co-dependent, delete together (10 + N files)
3. `src/entities/` (4 files) — name-collides with live `WorldAssemblyResolver` / `EntityArchetypeResolver`; confirm no collision before deletion
4. `src/content_semantics/` — only `faction.py` is relevant; verify it is truly orphaned before deletion
5. `src/ai/` — **last** and requires parity ledger audit first: files carry compliance IDs `SOC-142`, `COMB-093–099`, `STRAT-166–174`; confirm those ledger entries have passing `test_path` alternatives before deleting

> Note: `src/ai/goals/scorers.py` implements the V1 `GoalScorer` subclass pattern that
> `docs/guidelines/design_patterns.md` still documents as the V2 extension point (see 2B
> below). Both must be cleaned up together to avoid confusing future agents.

### 1F — CI / Release Pipeline

Source: D18 (CI / Release Pipeline Completeness). P0 — no test automation at merge time.

| Finding | Fix |
|---|---|
| No `test.yml` exists — only `deploy-docs.yml` runs on push | Add `.github/workflows/test.yml`: `make lane-all-fast` + `make gate-expansion` + `pytest tests/docs/` on every PR; `make lane-legacy-regression` on `main` push only. Estimated <30 lines of YAML. |
| All certification harness runs require local invocation | Wire `CertificationHarness CLASS_B` into `test.yml` on `main` push. |

### 1G — Type Checker

Source: D13 (Type Safety & Validation Boundary). F1 is the highest-risk finding.

| Finding | Fix |
|---|---|
| No `mypy` / `pyright` configured anywhere — 455 `Any` usages, 186 missing return annotations, zero automated enforcement | Add `[tool.mypy]` to `pyproject.toml` with `strict = false` initially; add `make typecheck` target; wire into `test.yml` (see 1F above). |
| `api/server.py` — 18 route handlers with no `response_model=` | Add `response_model=` to FastAPI route decorators so shape regressions are caught at startup. |
| `api/engine_manager.py` — `get_state()` / `get_full_snapshot()` / `get_entities_paged()` / `get_entity()` return `Dict[str, Any]` | Define typed response models and wire `response_model=` into routes. |

---

## Section 2 — Documentation Staleness (D17 findings)

Source: D17 (Documentation Currency). Fix these before any implementation work that
depends on them, since CLAUDE.md's Context Scan rule tells agents to trust these docs.

| Priority | Doc | Issue | Fix |
|---|---|---|---|
| **P0** | `docs/engine/authoritative_pipeline.md` | 17-phase table from an earlier version — current `pipeline.py` has 30+ named phases. Phase names, order, and count all differ. Any agent implementing against this doc uses wrong insertion points. | Regenerate phase table from `pipeline.py`; add phase count assertion in `tests/docs/`. |
| **P0** | `docs/engine/kernel.md` | Two conflicting phase tables in the same file — stale 6-phase table appears before the correct 7-phase table. Reading linearly gives wrong info first. | Remove or clearly mark the stale table; keep only the current one. |
| **P1** | `docs/mechanics/01_entity_anatomy.md` | Biological thresholds numerically wrong: hunger trigger is 95.0 (doc says 100.0), damage is +2 (doc says 5), sleep debt trigger is 98.0 (doc says 80.0), penalty is HP damage (doc says ATK/DEF multiplier). | Audit `src/` values for each threshold; update doc to match code or fix code to match doc and update parity ledger. |
| **P1** | `docs/mechanics/04_strategic_cognition.md` | Interruption margin formula: doc says `Profile_Resistance * 30.0`; code uses `profile.resistance_multiplier` (profile-defined constant, not 30.0 universally). | Reconcile doc with current `resistance_multiplier` pattern; update parity ledger `STRAT-164` or equivalent. |
| **P1** | `docs/guidelines/design_patterns.md` | Describes V1 patterns only (`GoalScorer`, `StateHandler`, `EntityBuilder`) — none are V2 extension points. A developer following this doc adds V1 abstractions to a V2 codebase. Joint D12/D17 finding. | Rewrite to document V2 patterns (domain phase class, decision/mutation separation, presenter layer). Archive V1 section. |
| **P1** | `docs/engine/known_limitations.md` | At least one claim (blacksmith-only towns) is contradicted by completed work (`TCK-20260425-PH7-M3-RECOVERY`). Flagged independently by 3 of 5 audit forks. | Full refresh pass; retire or archive stale limitations; add "last-verified" date. |

---

## Section 3 — Product-Surface Epics (larger work, not yet started)

These are the remaining items from `engine_future_epics_roadmap.md` Section D and C
that represent the gap between "engine that works" and "product that runs an RPG
simulation." Sequencing recommendation is preserved from the roadmap.

### 3A — Resource Ecology Regeneration (Section C, size S–M)

**Why it's blocking:** Nodes are largely static/reset-on-reload. No seasonal
growth/depletion/cooldown loop exists. Hunger pressure can never resolve because no
food-kind resource node exists in any tested world — entities generate hunger projects
every ~30 ticks indefinitely. This blocks economic balance measurement, quest pressure,
and meaningful faction conflict.

**Unblocks:** Macro-Economy Health Metrics, Pressure-Driven Quest Generation, D06
long-run health re-validation.

### 3B — Persistent Campaign Runtime (Section D, size L)

**Why it's blocking:** `CampaignRunner` is explicitly analysis-only (isolated state,
no `Failed` state, can't share `AuthoritativeState` with live sim). No multi-scenario
continuity / persistent-consequence campaign system exists. This is a different concept
from what currently bears the "campaign" name — naming collision risk for future tickets.

**Unblocks:** Social Memory as Campaign Consequence, Faction/History writing cross-episode
consequences, cross-episode culture drift persistence.

### 3C — Scenario Runtime Service (Section D, size M)

**Why it's blocking:** No interactive, product-shaped single-scenario execution loop
exists — only `CampaignRunner` (analysis) and sweep/CI batch runs (neither has
objective/win-loss-stall state or pause/resume/checkpoint). Without this, the engine
has no product entry point.

**Depends on:** Persistent Campaign Runtime (3B) for episode boundary state.

### 3D — Active Information-Seeking / Belief Economy (Section B, size M)

Entities are effectively omniscient-by-passive-injection. No deliberate "ask
guide/merchant," no paid info transaction, no contradiction-driven replanning.
Blocked by: nothing architectural. Can start independently.

**Audit confirmation:** Parity entries `STRAT-164/177` (missing tests) and leads system
are coded; the gap is the "active seeking" half of the belief economy.

### 3E — Entity Decision "Why" Tooling (D15, size S–M)

Route trace is computed every tick in `execute_brain()` but discarded at the tick
boundary. Rich `cognition_graph_snapshots.jsonl` exist per run but only in
DEBUG/CERTIFICATION mode, with no REST query API and no tick indexing.

**Fix without new simulation logic:** promote existing computed data to a queryable REST
API (`/api/v1/observability/cognition/{entity_id}/tick/{n}`). The 6 missing capabilities
(goal score comparison, tick-N reconstruction, cognition REST API, route trace
persistence, BehaviorTimeline REST API, LIGHT-mode cognition capture) all cluster around
this single promotion.

---

## Section 4 — Content Gaps (D07 findings)

Source: D07 (Content Depth & Variety). Not epics — content authoring work.

| Gap | Current State | Risk | Action |
|---|---|---|---|
| Quest definitions | Only 4 total; 3 of 14 world modules have any quests | **P0** — without quests, conflict produces combat loops, not RPG story arcs | Add quest definitions to at least 8 world modules; target ≥20 total |
| Terrain / population module types | 0 entries for 2 of 7 registered module types | No terrain traversal or population distribution possible | Author at least 2 terrain modules and 2 population modules |
| World compositions without scenarios | `dungeon_crawl`, `urban_political`, `wilderness_survival` have 0 scenarios | These compositions cannot be entered from the scenario layer | Add ≥1 scenario per composition |
| Crafting recipes | 8 recipes for 34 items | No "gather→craft→upgrade" chain available | Add recipes for top-tier items; audit which items have zero production path |

---

## Recommended Work Order

1. **Section 2 docs first** — stale docs mislead agents using the Context Scan rule;
   fix P0 items (`authoritative_pipeline.md`, `kernel.md`) before any epic that touches
   the engine loop.

2. **Section 1 cheap fixes** — batch into one or two tickets; most are ≤1 day each.
   Priority order within section: 1A (parity debt) → 1D (personality seeding) →
   1B (determinism) → 1F (CI) → 1E (dead code) → 1G (type checker) → 1C (coupling).

3. **Section 3A (Resource Ecology)** — unblocks the most downstream work; start here
   once cheap fixes are cleared.

4. **Section 3B → 3C (Campaign Runtime → Scenario Service)** — sequential dependency;
   implement in order.

5. **Section 3D and 3E** — can run in parallel with 3B/3C; no dependency between them.

6. **Section 4 (Content)** — ongoing; author content in parallel with any epic that
   adds a system that consumes it (e.g. add quest definitions when Scenario Runtime
   Service is implemented).
