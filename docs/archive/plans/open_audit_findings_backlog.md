---
status: historical
layer: architecture
authority: P1
audience: agent
tags: [audit, backlog, cheap-fixes, doc-debt, ci, dead-code, product-surface, roadmap]
date: 2026-06-23
updated: 2026-06-26
closed: 2026-06-26
source: docs/audits/audit_dimensions.md
---

# Open Audit Findings — Implementation Backlog

## Purpose

This document captures all outstanding work items surfaced by the 18-dimension engine
audit (`TCK-20260618-AUDIT-EPIC`, completed 2026-06-19) that have not yet been
implemented as of 2026-06-23.

It is a companion to `engine_future_epics_roadmap.md` (which focuses on large epics)
and the audit detail files in `docs/audits/` (which are source-of-truth for findings).
When an item is resolved, update the status here and update the relevant parity ledger
entry or audit detail file.

**Epics already complete** (not repeated here): Worldgen, E53-Faction, E61-Progression,
E62-Culture-Drift, E63-Feature-Packs. The RC1/RC2/RC3 wiring bugs are also fixed.

**Status as of 2026-06-26:** Investigation confirmed that the vast majority of items
below were completed between 2026-06-19 and 2026-06-25 via the Phase 0 tickets and
the E11–E42 epic series. The only remaining open item is `design_patterns.md` (§2, P1).
Ticket: `TCK-20260626-FIX-DESIGN-PATTERNS`.

---

## Section 1 — Cheap Fixes

### 1A — Parity Ledger Debt (P0/P1)

> **RESOLVED by `TCK-20260619-PARITY-P0-BUGS` (2026-06-19).**
> COMB-006 AoE legality guard fixed; COMB-290 wound threshold doc reconciled; COMB-133/134
> documented as unsupported stubs; STRAT-164, STRAT-177, SOC-134 parity tests added.

Source: `docs/parity_ledger/combat_movement.yaml`, `strategic_cognition.yaml`,
`social_narrative.yaml`.

| ID | Status |
|---|---|
| `COMB-006` | **DONE** — AoE alive/active guard added |
| `COMB-133` | **DONE** — documented as unsupported |
| `COMB-134` | **DONE** — documented as unsupported |
| `STRAT-164` | **DONE** — parity test added |
| `STRAT-177` | **DONE** — parity test added |
| `SOC-134` | **DONE** — parity test added |

### 1B — Determinism & Scoring Bugs

> **RESOLVED by `TCK-20260619-P0-CODE-INTEGRITY` (2026-06-19) and
> `TCK-20260619-E12B-BLOCKER-RECAL`.**
> Sort tiebreaker added to `generator.py` and `selector.py`. Blocker penalty investigated
> and intentionally kept at 2.0 — blocker frequency measured at 0.0% (< 5% threshold),
> so graduated penalty has no observable effect. `docs/mechanics/04_strategic_cognition.md`
> §6 updated with scoring constants; STRAT-227 parity entry added.

| Finding | Status |
|---|---|
| D12 F1 — unstable sort | **DONE** — `entity_id` tiebreaker added |
| D04 — blocker penalty imbalance | **CLOSED (by design)** — penalty kept at 2.0; blocker_freq = 0.0% |

### 1C — Architecture Coupling Violations

> **RESOLVED by `TCK-20260619-P0-CODE-INTEGRITY` (2026-06-19).**
> `TemporalPressureService` injected via pipeline orchestrator (cross-domain import removed).
> `MovementPlanCache` construction moved out of `AuthoritativeState.__post_init__` — cache
> is now injected by the pipeline bootstrap.

| Finding | Status |
|---|---|
| D14 prohibited import (`memory/phase.py`) | **DONE** — constructor injection |
| D14 upward coupling (`core/state.py`) | **DONE** — cache injected at pipeline bootstrap |

### 1D — WorldCompiler Personality Seeding

> **RESOLVED by `TCK-20260619-P0-ENTITY-INIT` (2026-06-19).**
> `WorldCompiler.compile()` now seeds `PersonalityComponent` per entity using
> `DeterministicRNG` sub-seeds derived from entity role + archetype. Class assignments
> read from `data/content/spawn_tables.yaml` — no entity spawns as NOVICE by default.

### 1E — Dead Code Removal

> **INVALID (2026-06-23):** Investigation during TCK-20260623-DEAD-CODE-REMOVAL confirmed
> that all 9 directories have live engine importers — they are not dead code. `src/quests/`
> and `src/progression/` are imported top-level by `src/engine/apply.py`. `src/ai/` is
> imported by `intelligence.py`. `src/content_semantics/` is imported by 10+ engine files.
> No deletions will occur. See `stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md`
> for full importer evidence.

### 1F — CI / Release Pipeline

> **RESOLVED (2026-06-25).** `.github/workflows/test.yml` added with 8 parallel domain
> jobs plus a slow-regression job (`-m "slow or extra_slow" --resource-budget large`)
> gated to PRs targeting `main`. `mypy` step also wired. See commit `146e5f31`.

| Finding | Status |
|---|---|
| No `test.yml` | **DONE** — 8-job parallel CI + slow-regression gate |
| Certification requires local invocation | **DONE** — slow-regression job covers it |

### 1G — Type Checker

> **RESOLVED by TCK-20260623-TYPE-CHECKER (2026-06-23).**
> Parity ledger entry: `INFRA-TYPE-001`. `[tool.mypy]` in `pyproject.toml`, `make typecheck-py`
> target, `response_model=` on 13/18 routes, typed schemas in `src/api/schemas.py`.

---

## Section 2 — Documentation Staleness (D17 findings)

Source: D17 (Documentation Currency).

| Priority | Doc | Status |
|---|---|---|
| **P0** | `docs/engine/authoritative_pipeline.md` | **DONE** — phase table updated 17→31 phases (`TCK-20260619-P0-DOC-REPAIR`) |
| **P0** | `docs/engine/kernel.md` | **DONE** — stale first phase table removed (`TCK-20260619-P0-DOC-REPAIR`) |
| **P1** | `docs/mechanics/01_entity_anatomy.md` | **DONE** — biological thresholds corrected (`TCK-20260619-P0-DOC-REPAIR`) |
| **P1** | `docs/mechanics/04_strategic_cognition.md` | **DONE** — interruption margin formula reconciled (`TCK-20260619-P0-DOC-REPAIR`) |
| **P1** | `docs/engine/known_limitations.md` | **DONE** — Blacksmith-Only claim updated (`TCK-20260619-P0-DOC-REPAIR`) |
| **P1** | `docs/guidelines/design_patterns.md` | **OPEN** — still describes V1 patterns only (`GoalScorer`, `src/ai/goals/`); V2 extension patterns undocumented. Ticket: `TCK-20260626-FIX-DESIGN-PATTERNS` |

---

## Section 3 — Product-Surface Epics

All five epics completed via the E-series tickets (2026-06-19 to 2026-06-22).

| Epic | Status | Tickets |
|---|---|---|
| 3A — Resource Ecology Regeneration | **DONE** | `TCK-20260619-E21*` (E21A–E21D) |
| 3B — Persistent Campaign Runtime | **DONE** | `TCK-20260619-E32*` (E32A–E32E) |
| 3C — Scenario Runtime Service | **DONE** | `TCK-20260619-E31*` (E31A–E31D) |
| 3D — Active Information-Seeking / Belief Economy | **DONE** | `TCK-20260619-E42*` (E42A–E42E) |
| 3E — Entity Decision "Why" Tooling | **DONE** | `TCK-20260619-E22*` (E22A–E22C) |

---

## Section 4 — Content Gaps (D07 findings)

All four content gaps resolved via E13 content foundation epic.

| Gap | Status | Tickets |
|---|---|---|
| Quest definitions | **DONE** — quest_definitions in 8+ modules; E23 quest generation added runtime activation | `TCK-20260619-E13A-QUEST-DEFS`, `TCK-20260619-E23*` |
| Terrain / population module types | **DONE** — 2 terrain modules (mountain_pass, river_crossing) + 2 population modules added | `TCK-20260619-E13B-MODULE-TYPES` |
| World compositions without scenarios | **DONE** — ≥2 scenarios per composition | `TCK-20260619-E13D-SCENARIOS` |
| Crafting recipes | **DONE** — iron_ore→steel→ember_axe chain + expanded recipe catalog | `TCK-20260619-E13C-RECIPES` |

---

## Remaining Open Item

**One item remains open as of 2026-06-26:**

| ID | Item | Ticket | Priority |
|---|---|---|---|
| §2 P1 | `docs/guidelines/design_patterns.md` — V1→V2 rewrite | `TCK-20260626-FIX-DESIGN-PATTERNS` | P1 |
