---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
phase: investigate
date: 2026-08-10
tags: [documentation, cognition]
---

# Investigation — TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

## Method

For each of the 10 files in `docs/systems/` (9 content docs + `README.md`), extracted the doc's
own cited `src/` file paths and class/symbol names, then checked each directly against the real
codebase (`ls`/`find`/`grep -rn "class X"`). A doc counts as stale when its own cited paths/symbols
do not exist, not on a subjective read of "feels old."

## Per-file results

| File | Frontmatter | Verdict | Evidence |
|---|---|---|---|
| `state_machines.md` | `status: active`, no `last_verified` | **STALE** (comprehensive) | Every one of 5 sections cites a non-existent class: `AIBrain`, `STATE_HANDLERS`, `src/ai/states/`, `src/ai/brain.py` (Section 1); `HeroLifecycleSystem` (Section 2); `WorldLoop`, `PhaseGuard`, `EngineContext` (Section 4); `CombatAction`, `DamageResolutionService`, `CombatAftermathService`, `KillRewardService` (Section 5). Section 3 (Quest Lifecycle) cites `progression.quests`/`QuestSystem` semantics that don't match either real quest implementation (`src/quests/service.py`'s wired-in `QuestService`, sourced by `docs/simulation/quest_contract.md`; or the seemingly-orphaned `src/systems/world_systems/quest_engine.py`) |
| `mechanics.md` | `status: active`, no `last_verified` | **STALE** (already ticket-confirmed) | `next_act_at`/`spd` action-delay formula has zero real references (`grep` confirmed); real system is `combat.readiness`/`readiness_speed` |
| `ai_system.md` | `status: active`, no `last_verified` | **STALE** (partial — phase model) | Describes a "PACKETIZATION" kernel phase that does not exist in `docs/engine/kernel.md`'s real, current `Phase Domain Permissions` table (INIT/SCHEDULING/COLLECTION/RESOLUTION/CLEANUP/ADVANCEMENT/PERSISTENCE) or in `kernel.py`'s real `_phase_*` methods. `MindAspect`/`ActionResults` do not exist. `WorkerPacket` does exist (`src/core/worker_protocol.py`) — not 100% fabricated, but the overall phase-cycle framing is wrong |
| `buildings_and_economy.md` | `status: active`, no `last_verified` | **STALE** | Cites `src/core/buildings.py` (does not exist — real file is `src/town/buildings.py`) and a `Building` dataclass with `building_id`/`durability`/`max_durability` fields that don't match the real `BuildingRegistry` (static templates, uppercase type constants `INN`/`GUILD`/`SHOP`/etc., `max_hp`) + `BuildingState` (`src/core/state.py`) split |
| `combat_and_progression.md` | `status: active`, no `last_verified` | **STALE** | Cites `src/actions/combat.py`, `src/actions/damage.py`, `src/actions/base.py`, `src/ai/states.py`, `src/core/items.py`(exists)/`src/core/grid.py`(missing), `src/core/classes.py`(exists)/`src/engine/world_loop.py`(missing), `src/core/models.py`, `src/ai/perception.py` — 8 of 11 cited paths do not exist; `src/actions/` and `src/ai/states.py` do not exist anywhere in the tree |
| `world_evolution_and_resilience.md` | `status: active`, no `last_verified` | **STALE** | Cites `src/core/world_state.py`, `src/core/buildings.py`, `src/core/monuments.py`, `src/actions/raid.py`, `src/actions/repair.py` — none exist; only `src/engine/world_dynamics.py` is real |
| `world_generation.md` | `status: active`, no `last_verified` | **STALE** | Cites `src/core/grid.py`, `src/core/resource_nodes.py`, `src/core/regions.py`, `src/systems/terrain_detail.py`, `src/core/faction.py` — none exist; only `src/core/enums.py` and `src/api/engine_manager.py` are real |
| `world.md` | `status: active`, no `last_verified` | **STALE** | Describes a hardcoded `Material` enum (TOWN/SANCTUARY/ROAD/BRIDGE/WALL/MOUNTAIN/etc.) that does not exist in `src/core/enums.py`. The real terrain system is the declarative content-catalog architecture (`src/content/schema.py`, `resolver.py`, `matrix.py` — matches Mechanics Bible chapter `06_worldbuilding_foundation.md`'s "Declarative topology" design), a fundamentally different, non-enum-driven approach |
| `faction_contract.md` | `status: authoritative`, `last_verified: 2026-06-23` | **CURRENT** | Not deep-audited beyond the currency signal (status/last_verified) — out of scope to re-verify a doc already carrying this repo's own "verified current" marker; no contradicting evidence found during the broader sweep |
| `strategic_cognition.md` | `status: active`, no `last_verified` | **CURRENT** (exception to the pattern) | Describes `Directives`/`Projects`/`Objectives` hierarchy — `DirectiveState`, `ObjectiveState`, `ProjectState` all confirmed real in `src/core/strategic.py`. Links to `docs/compliance/gap_analysis.md` for known gaps, consistent with active maintenance. `status: active` + no `last_verified` is NOT a reliable stale/current discriminator on its own — it correlated with staleness in 7/8 other cases but this file breaks the pattern, confirming direct symbol verification (not frontmatter heuristics) is required, exactly as the ticket's own Acceptance Criteria demands |
| `README.md` | `status: active`, no `last_verified` | **Needs update, not itself "stale content"** | Pure directory index — its own text has no `src/` claims to falsify, but its "AI System" entry description ("Brain architecture and state machines") repeats the stale `ai_system.md`/`state_machines.md` framing, and it is MISSING entries for `mechanics.md` and `state_machines.md` entirely (both exist as unlinked orphans — explains how `search_docs` could surface them as if-current: they were never wired into the directory's own navigation, so no human/agent workflow that follows README links would ever notice them) |

## Root cause of the drift

All 8 stale files share the same signature: they cite a `src/actions/`-and-`src/ai/states.py`-centric
architecture (imperative action classes, a monolithic `AIBrain`, a raw `Material` tile enum,
`src/core/grid.py`/`world_state.py`) that predates the current `src/engine/`, `src/domains/`,
`src/core/state.py`/`strategic.py`, `src/content/` (declarative catalog), and `src/town/`
architecture. This looks like a single "generated from codebase analysis" snapshot (the exact
phrase `state_machines.md`'s own header uses) taken once, long enough ago that the codebase has
since been substantially restructured, and never regenerated or hand-verified since — consistent
with every stale file sharing `status: active` + no `last_verified` field, and with 2 of 9 files
(`faction_contract.md`, `strategic_cognition.md`) that either do carry a `last_verified` date or
happen to still describe a part of the architecture that hasn't moved.

## Real, current docs covering the same ground

| Stale doc (or section) | Real current replacement |
|---|---|
| `state_machines.md` §1 (Entity AI FSM), `ai_system.md` (cognition framing) | `docs/engine/contracts/tactical_contract.md` (tactical decisions), `strategic_cognition.md` (strategic layer — itself current) |
| `state_machines.md` §2 (Hero Lifecycle FSM) | `docs/simulation/lifecycle_systems_contract.md` |
| `state_machines.md` §3 (Quest Lifecycle FSM) | `docs/simulation/quest_contract.md` (`status: authoritative`) |
| `state_machines.md` §4 (Engine Tick Cycle FSM), `ai_system.md` (phase framing) | `docs/engine/kernel.md` (`status` unchecked but cites real `phase_domain_permissions.py`, matches `kernel.py` exactly) |
| `state_machines.md` §5 (Combat Engagement FSM), `mechanics.md` | `docs/mechanics/02_combat_laws.md` + `docs/mechanics/damage_formula_contract.md` (`status: authoritative`), `docs/engine/contracts/minimal_kernel.md` (readiness-gated action semantics, per the ticket's own original finding) |
| `buildings_and_economy.md` | `docs/simulation/town_contract.md` (`status: authoritative`, `last_verified: 2026-06-12`, sourced from real `src/town/`) — found only after checking the 3 real live cross-references still pointing at the old path (see "Cross-reference sweep" below); missed in the initial symbol-only sweep |
| `world_generation.md` | `docs/world/generator_contract.md` (`status: authoritative`, `last_verified: 2026-08-08`, sourced from real `src/worldgeneration/`) — same correction as above |
| `combat_and_progression.md`, `world_evolution_and_resilience.md`, `world.md` | No single doc fully replaces these — coverage is spread across `docs/mechanics/03_economic_laws.md`, `05_world_evolution.md`, `06_worldbuilding_foundation.md`, `regional_sovereignty.md`; a full reference-doc rewrite is out of this ticket's own scope (new-content authoring, not a stale-doc repair) |

## Cross-reference sweep

Before finalizing, grepped all of `docs/` for live links to the 8 paths being archived. 3 real,
live references found (not just the directory's own `README.md`, already accounted for):
- `docs/simulation/town_contract.md` and `docs/world/generator_contract.md` — each had a
  `**System overview:** docs/systems/{file} (do not duplicate here)` line pointing at what turned
  out to be authoritative, current, `last_verified`-dated docs of their own. This directly
  contradicts the initial "no current replacement exists" conclusion for `buildings_and_economy.md`
  and `world_generation.md` above — corrected once found. Updated both lines to note the
  archival and that the contract itself is now the primary reference (no separate overview).
- `docs/guides/diagram_index.md` — a table row citing `state_machines.md`'s mermaid diagram for
  "Engine tick cycle." Removed the row (the diagram itself describes a non-existent phase model);
  `docs/engine/architecture.md`'s own diagram remains as the real reference.

## Decision

Retire (archive, not delete) all 8 confirmed-stale files to `docs/archive/systems/`, matching this
repo's existing archival convention (`status: archive`, `authority: P2`, `audience: historical`,
`layer: systems`, `original_date: unknown` — no generation date was ever recorded in any of the 8
files' own frontmatter or content). A short pointer note is added at the top of each archived file
citing its real current replacement(s) from the table above, for the cases where a single doc
covers the ground; for `buildings_and_economy.md`/`combat_and_progression.md`/
`world_evolution_and_resilience.md`/`world_generation.md`/`world.md`, the note discloses that no
single current `docs/` reference doc exists yet (a real, disclosed gap, not silently absorbed) —
authoring 5 new reference docs from scratch is out of this ticket's own scope (doc-repair, not
new-content authoring).

`docs/systems/README.md` is rewritten to link only the 2 confirmed-current files
(`faction_contract.md`, `strategic_cognition.md`) plus a short note on the retired set and where to
find the replacements, rather than deleting the index down to 2 lonely entries with no context.
