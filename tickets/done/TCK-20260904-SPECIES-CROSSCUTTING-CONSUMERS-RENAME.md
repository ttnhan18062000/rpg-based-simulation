---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
phase: done
date: 2026-09-04
tags: [content, observability]
---

# TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME

## Title
Rename remaining race_id/RaceDefinition consumers outside the core schema and race-relations subsystem

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 3/4 of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Depends on
`TCK-20260904-SPECIES-CORE-SCHEMA-RENAME`. Covers every remaining `race`/`race_id` consumer not
already handled by child 1 (core schema) or child 2 (race-relations subsystem) — the kernel, engine
cognition/replay, observability, quests, API websocket stream, world environment, and remaining
content data files.

## Scope
- `src/engine/kernel.py`, `src/engine/cognition.py`, `src/engine/replay_manager.py`.
- `src/observability/event_recorder.py`, `src/observability/event_shapers.py`,
  `src/observability/alerts/sinks.py`.
- `src/quests/generator.py`, `src/api/ws/stream.py`.
- `src/world/environment.py` (the `RaceDefinition`-referencing comment about hazard_immunities noted
  during investigation), `src/content_semantics/personality.py`.
- Remaining content data: `data/content/entities/entity_archetypes.yaml`,
  `data/content/social/factions.yaml`, `data/content/social/personality_bias.yaml`.
- Any remaining `race`-referencing test file not already covered by child 2's list — confirm the
  actual remaining set at pickup time (14 of the 20 originally-found test files, per the epic's
  count, since 6 are child 2's).

## Out of Scope
- Core schema/entity plumbing — child 1.
- Race-relations subsystem — child 2.
- Docs sweep — child 4.

## Acceptance Criteria
- [x] Every listed file's `race`/`race_id` reference renamed consistently with child 1's chosen
      naming. (Most were already closed by child 1's hard-coupling fixes; re-confirmed via grep,
      not assumed — see investigation.md.)
- [x] Remaining content data files updated to reference the renamed catalog paths/field names.
- [x] All affected tests pass unchanged.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-CORE-SCHEMA-RENAME (dependency)

## Related Docs
None beyond the parent epic.

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME/{investigation,plan,test_plan}.md

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/cognition.py`, `src/engine/replay_manager.py`
- `src/observability/event_recorder.py`, `src/observability/event_shapers.py`,
  `src/observability/alerts/sinks.py`
- `src/quests/generator.py`, `src/api/ws/stream.py`, `src/world/environment.py`,
  `src/content_semantics/personality.py`
- `data/content/entities/entity_archetypes.yaml`, `data/content/social/factions.yaml`,
  `data/content/social/personality_bias.yaml`

## Assumptions / Open Questions
- Exact remaining test-file list should be re-confirmed at pickup time (childrens' scopes may shift
  slightly once child 1/2 land and some renames turn out to already be covered). Resolved: nearly
  all of this ticket's own listed scope was already closed by child 1's necessary hard-coupling
  fixes by pickup time — re-confirmed via direct grep of every listed file, not assumed. Only 2 real
  gaps remained: `event_shapers.py`'s deliberately-deferred output key, and
  `FactionDefinition.common_races`.

## Implementation Notes
Re-confirmed via direct grep that `src/engine/{kernel,cognition,replay_manager}.py`,
`src/observability/{event_recorder,alerts/sinks}.py`, `src/quests/generator.py`,
`src/api/ws/stream.py`, `src/content_semantics/personality.py`, and 2 of the 3 listed content data
files needed zero further change — already closed by child 1 or never functionally coupled to
"race" terminology (confirmed each hit was unrelated concurrency-race language, not assumed clean).
Real remaining work: (1) `event_shapers.py`'s deliberately-deferred `combat_engagement_started`/
`ended` event output key (`"race_id"` → `"species_id"`, confirmed zero downstream consumers first);
(2) `FactionDefinition.common_races` → `common_species` (16 `factions.yaml` entries + schema field
+ 1 test fixture, zero functional `src/` consumers found). Also fixed 2 leftover terminology
comments (`cognition.py`, `test_semantics.py`) found via a fresh full-repo grep sweep.

## Test Summary
1324 passed, 1 skipped across the scoped observability/content/content_semantics sweep. Full
non-slow `tests/unit/ tests/integration/` sweep: 6008 passed, 9 skipped, 84 deselected, 2 failed
(identical `tests/conftest.py` resource-time-limit `TimeoutError`s already diagnosed as environment
noise in child 1/2 — same two tests, same signature, no new regressions). Full details in
stored_artifacts/TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME/test_plan.md.

## Files Changed
- `src/content/schema.py`, `data/content/social/factions.yaml`,
  `tests/unit/content/test_layered_catalog.py` (`common_races` → `common_species`)
- `src/observability/event_shapers.py`, `tests/unit/observability/test_event_shapers.py`
  (deferred output key rename)
- `src/engine/cognition.py`, `tests/unit/content_semantics/test_semantics.py` (comment accuracy)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-401)

## Completion Summary
Closed out the remaining `race`/`race_id`/`RaceDefinition` consumers not already covered by child 1
(core schema) or child 2 (race-relations subsystem). Confirmed via fresh grep that most of this
ticket's own listed file scope was already resolved by child 1's necessary hard-coupling fixes by
the time this ticket started — did not assume the epic's now-stale original scan was still accurate.
The two real remaining items — the observability event schema's deferred output key and
`FactionDefinition.common_races` — are now renamed. Full repo-wide grep confirms zero remaining
`race_id`/`RaceDefinition`/`common_races` references outside historical TCK-ID citations, child 2's
own untouched race-relations-subsystem scope, and unrelated concurrency terminology.
