---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
artifact_type: investigation
tags: [strategy, simulation-quality, progression]
---

# investigation.md — TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING

## Summary — scope grew twice during investigation, both times confirmed with the user before
## proceeding, per CLAUDE.md's Clarification Rule

This ticket's own Scope assumed the fix was "wire `GuildAction` into `ActionRouter`'s dispatch
table." Real-kernel tracing found two deeper, sequential blockers, each surfaced to the user
before implementation began:

1. **`TOWN_RETURN`'s own objective never resolves a navigable target at all** —
   `TownScorer.score()` sets `target_id="town_center"` (a string), but
   `TacticalDecisionSystem._resolve_target_position()` only parses an int-castable ID or a
   stringified coordinate tuple; `"town_center"` is neither. Confirmed by monkeypatching the real
   function during a live 280-tick run: every call for a `town_return` objective returned
   `(None, None, None)`. The position drift observed in an earlier naive trace turned out to be
   an unrelated combat anti-stalemate fallback (`tactical.py:424`, `STALEMATE_BREAK`) that
   coincidentally also targets `(0.0, 0.0)` — the same coordinate as `town_center` in every
   sampled world, a red herring initially mistaken for purposeful town-ward movement.
2. **No world in the real content corpus ever declares a `"guild"` building** — checked every
   resolved world (`data/worlds/*/resolved/world.resolved.yaml`); the complete universe of real
   building types is `blacksmith`/`healer_hut`/`inn`/`mine_entrance`/`shop`/`town_hall`/
   `watchtower`. Not even `hero_guild_routing` (a world named for guild routing) has one — it
   only has `town_hall`+`shop`. `docs/systems/buildings_and_economy.md`'s own building table
   (listing "Adventurer's Guild"/"Class Hall"/"Hero's House") is itself stale — confirmed via
   its own "Primary files" line citing `src/core/buildings.py`/`src/ai/states.py`, neither of
   which exist; it documents a legacy V1 AI-state system, not the current V2 `GoalKind`
   architecture.

Per explicit user decision, `GuildAction` is rebased onto `town_hall` (present in every real
world) rather than deferring the guild-content gap to a separate ticket.

## A third finding, discovered while designing the actual dispatch mechanism:
## `GuildAction.visit()` cannot safely run through the `ENTITY_ACT`/`ActionRouter` path

`PROD_SMALL` (the profile used throughout this session's real-kernel verification,
`max_worker_count=2`) routes `ENTITY_ACT` tasks through `ConcurrentExecutionAdapter` →
`default_simulation_worker()`, whose `context` parameter is a `WorkerPacket`
(`src/core/worker_protocol.py`), not a full `AuthoritativeState` — by explicit, documented design
("Law: A worker must receive a compact, bounded, and read-only context"). `WorkerPacket` carries
`seed`/`tick`/`subject`/`neighbor_view` but NOT `regions`/`resource_nodes`. `GuildAction.visit()`
needs both (region trauma/hazard for `QuestPressureProfile`, resource nodes for lead generation).
Dispatching `GuildAction` via `ActionRouter`/`CoreActions` (the pattern `EAT`/`REST`/`INTERACT`
use) would either crash or silently misbehave under the concurrent executor — the same executor
this session's own real-kernel verification runs use every time.

**Resolution**: follow this codebase's own established precedent for state-heavy logic —
`QuestRewardPhase`, `FactionDecisionPhase`, and `WorldDynamicsSystem` all run as dedicated,
sequential authoritative-pipeline phases (`run_phase(...)` in `pipeline.py`), never as
`ENTITY_ACT` actions, specifically because they need full `state` access.
`GuildVisitPhase` follows the same pattern. This also means `tactical.py`/`ActionRouter` need NO
changes at all — `GuildVisitPhase` independently detects "entity's active project is
`kind=="guild"` and its target building is within reach," mirroring
`_resolve_active_objective`'s own existing "detour" arrival-check pattern
(`intelligence.py:1017-1056`), rather than depending on `tactical.py`'s per-tick dispatch.

## Design

1. **New `GoalKind.GUILD`** (`src/core/strategic.py`) — parallel to `FATIGUE`/`HUNGER`.
2. **New `GuildNeedScorer`** (`src/ai/goals/scorers.py`) — mirrors `EatScorer`/`SleepScorer`'s
   exact pattern: `SpatialQueryService.nearest_building(state, pos, "town_hall")`,
   `target_id=str(building.id)` (a real int-castable ID — `_resolve_target_position` already
   handles this correctly, unlike `TownScorer`'s broken string convention, so no change to that
   shared function is needed at all). Utility signal: spare project capacity (mirrors
   `GuildAction.visit()`'s own existing precondition, `len(strategic.projects) <
   profile.max_active_projects`) — moderate, non-urgent magnitude (25.0, below
   `CombatEngageScorer`'s 40+ base, above idle far-away harvesting), gated OFF entirely unless
   `ENABLE_GUILD_QUEST_GENERATION` is `ON` (checked via `state.feature_flags`, same direct-read
   convention this session's own observability flags use).
3. **New `GuildVisitPhase`** (`src/engine/pipeline_phases/guild_visit.py`) — mirrors
   `QuestRewardPhase.resolve(state, update) -> StateUpdate`'s shape. Scans entities with an
   active `kind=="guild"` project; when the entity is within reach (Manhattan distance ≤ 1) of
   its target `town_hall`, calls `GuildAction.visit(entity, state)` (full state access, safe —
   this phase runs sequentially, never through the worker/packet path), marks the project
   `COMPLETED` (mirrors `_resolve_active_objective`'s "detour" completion exactly), merges the
   visit's own `leads_add_or_update`/`projects_add_or_update` via `EntityUpdate.merge()`.
4. **Wired into `pipeline.py`** via `run_phase("guild_visit", update, ..., "ENABLE_GUILD_QUEST_GENERATION")`
   — same flag gates both the scorer (so the goal is never selected) and the phase (so even a
   stale/pre-existing `kind=="guild"` project from before a flag flip can't silently complete)
   — belt-and-suspenders, matching this repo's convention of defense-in-depth for new gameplay
   behavior (contrast with this session's earlier PROGRESSION/FACTION additions, which were
   observability-only and did NOT need flag-gating — this one genuinely changes AI behavior).
5. **New flag** `ENABLE_GUILD_QUEST_GENERATION`, default `OFF` (`src/domains/optimization/
   feature_flags.py`) — a new gameplay behavior, not a validated replacement of existing behavior,
   so DEV-002's default-OFF policy applies (unlike `ENABLE_PUSH_EVENT_SHAPERS`'s deliberate `ON`
   default, which was a *replacement* of already-proven behavior).

## What this does NOT fix (disclosed, not silently dropped)

- `TownScorer`/`_resolve_target_position`'s target-encoding mismatch for TOWN_RETURN's *other*
  purposes (selling items, HP/inventory-driven town visits) remains broken — genuinely
  out of this ticket's own scope (guild wiring specifically), and touching the shared
  `_resolve_target_position` function carries real regression risk across every other
  reach_location objective in the game. Filed as a separate follow-up,
  `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`.
- `InnAction`/`ClassHallAction`/`HomeAction` remain equally unreachable — same systemic pattern,
  but each would need its own building-kind rebase decision (inn/healer_hut is already a real
  building kind and could plausibly work with a similar `GoalKind`+scorer+phase pattern; class
  hall/hero's house have no real building kind at all, same as guild did) — out of this ticket's
  own scope, each deserves its own investigation, not a blanket fix bundled in here.
- `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` (sibling ticket, still open) — once
  real quests exist via this fix, `GATHER`/`BOUNTY`/`LIBERATE` quest kinds still cannot progress.

## Docs Requiring Update

- `docs/guides/feature_flags.md` — new flag row.
- `docs/simulation/quest_contract.md` — note the new live dispatch mechanism (GuildVisitPhase),
  distinct from the pre-existing documented Objective Reward stage.

## Parity Ledger Overlap

New entry in `docs/parity_ledger/strategic_cognition.yaml` (the file covering `GoalKind`/
`GoalScorer` architecture) — this is new AI-decision-layer behavior, not an observability signal.

## Prior Work

- `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE` (Finding 1, DONE — source of this ticket)
- `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (sibling, DONE — independent, observability-only)

## Risks and Open Questions

None left open — both scope-expansion points were surfaced to and resolved by the user before
implementation began.

## Anti-Drift Hazards

- Any future GoalKind/Scorer targeting a building must use the `SpatialQueryService.
  nearest_building()` + `target_id=str(building.id)` pattern (`EatScorer`/`SleepScorer`/now
  `GuildNeedScorer`), never `TownScorer`'s broken string-literal convention.
- Any future state-heavy dispatch (needing `state.regions`/`state.resource_nodes`/similar) must
  use a dedicated pipeline phase (`run_phase` in `pipeline.py`), never `ENTITY_ACT`/
  `ActionRouter`/`CoreActions` — the concurrent-worker path's `WorkerPacket` cannot provide it,
  by documented design, not oversight.
