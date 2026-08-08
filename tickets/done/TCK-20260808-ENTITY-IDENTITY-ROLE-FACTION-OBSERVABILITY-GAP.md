---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP
phase: open
date: 2026-08-08
tags: [observability, world]
---

# TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP

## Title
An entity's role or faction reassignment, recipe learning, and task assignment have zero
observability events — distinct from `IdentityUpdate`'s already-observed skill/trait/evolution_level sub-fields

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`TCK-20260808-ENTITY-EVENT-LEDGER`'s cross-reference (`docs/event_ledger/entity.yaml`
`ENTITY-007`, `ENTITY-015`) found `IdentityUpdate`'s `role`/`faction`/recipes/cooldowns fields, and
`TaskUpdate` (work-kind assignment) entirely, have no corresponding event — confirmed via
`grep -n "\.role\b\|\.faction\b\|role_set\|faction_set"` and `grep -n "\.task\.\|work_kind"` in
`event_extractor.py`, zero matches for both. This is distinct from `IdentityUpdate`'s
`learned_skills`/`traits`/`evolution_level` fields, which ARE observed
(`skill_unlocked`/`trait_expressed`/`level_up`) — an entity changing FACTION or ROLE (e.g. a
defection, a promotion) is invisible, even though this is exactly the kind of narratively
significant event a NARRATIVE or FACTION pillar signal would plausibly want.

## Scope
1. **Investigate**: find every code path that reassigns `entity.identity.role`/`.faction` and
   `entity.task` to understand real triggers (defection mechanics, promotion, task-queue
   assignment).
2. **Plan**: design `entity_role_changed`/`entity_faction_changed` events (task assignment likely
   stays unobserved by design — low narrative value, internal bookkeeping — Investigate should
   confirm rather than assume).
3. **Implement**: wire emission, register in `event_type_coverage.md`, update the ledger.

## Out of Scope
- SimQ scorer wiring — a faction-change event is a plausible strong candidate for FACTION pillar
  scoring, but that decision belongs to whoever implements this, not assumed here.
- Sibling findings tracked in their own tickets.
- `TaskUpdate` observability, if Investigate confirms it's genuinely low-value bookkeeping not
  worth an event — document that conclusion explicitly rather than silently dropping it.

## Acceptance Criteria
- [x] investigation.md identifies every real role/faction reassignment trigger (none exist —
      confirmed via direct grep, the mechanic is defined but never implemented anywhere)
- [x] A clear verdict on `TaskUpdate`: deliberately NOT worth an event — 24 real producers found,
      confirmed to be pure per-tick scheduling plumbing with zero narrative content; documented as
      a new `deliberately_uncovered` category in `event_type_coverage.md`, not silently dropped
- [x] New event(s) wired (4: `entity_role_changed`, `entity_faction_changed`, `recipe_learned`,
      `skill_cooldown_started`) — real `Kernel.tick_once()` verification attempted for
      `recipe_learned` (its one real producer is unconditional); confirmed unreachable within a
      1500-tick budget despite trigger conditions being met, so verified via this repo's own
      precedented hand-built-state pattern for all 4 events
- [x] `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-EVENT-LEDGER (found this gap — DONE)
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP, TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP (sibling findings)

## Related Docs
- `docs/event_ledger/entity.yaml` (`ENTITY-007`, `ENTITY-015`)
- `docs/core/update_intents.md` (`IdentityUpdate`, `TaskUpdate` definitions)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-EVENT-LEDGER/`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/core/updates.py` (`IdentityUpdate`, `TaskUpdate`)

## Assumptions / Open Questions
- Whether faction reassignment is even a live, exercised mechanic (vs. a defined-but-rarely-used
  intent field) — not assumed; Investigate must confirm real mutation sources exist.

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly. This is the final ticket of the entity-observability-gap
  batch (vitals, attributes, equipment, identity/role/faction) started this session.
- **`role_set`/`faction_set`: zero real producers anywhere** — distinct from every prior sibling
  ticket's findings (vitals/attributes/equipment all found at least one producer, gated or
  narrow). Role/faction reassignment (defection, promotion) is a defined-but-entirely-
  unimplemented mechanic. Wired the event anyway per the user's own standing direction to build
  "even invisible events, maybe we will change the code to make it visible" — future-proof, zero
  runtime cost when unused.
- **`recipe_learned`: found a genuinely live, unconditional producer** —
  `src/engine/blacksmith.py::BlacksmithSystem.enforce` (wholesale recipe grant on a functional-
  blacksmith-tile visit), confirmed NOT feature-flag-gated (`pipeline.py:174`'s `run_phase` call
  carries no flag argument). Trigger conditions confirmed met in `sandbox_world` (1 blacksmith,
  all 18 entities start with empty `known_recipes`) but not naturally exercised within a real
  1500-tick verification budget — same reachability class as the equipment ticket's goblin-
  evolution gear grant.
- **`skill_cooldown_started`**: real, action-router-wired producer
  (`src/engine/domain/skill_actions.py`) with no live AI driver ever selecting `"SKILL"` — same
  class as `execute_allocate_ap`/`execute_repair` in the sibling tickets.
- **`TaskUpdate` verdict: deliberately NOT worth an event**, confirmed not assumed. 24 real
  `work_kind_set=` producers found, overwhelmingly `src/engine/tactical.py`/`executor.py`/
  `worker_logic.py` — per-tick action-scheduling plumbing (`ENTITY_MOVE`/`ENTITY_ACT` on
  essentially every acting entity, every tick), zero persistent narrative content. Documented as
  a new `deliberately_uncovered` category in `event_type_coverage.md`'s Summary table, distinct
  from `unscored_intentional` (has an event, just not scored) — this field has no event, by
  deliberate, evidenced judgment.
- 4 new events added to `event_extractor.py`'s diff loop: `entity_role_changed`,
  `entity_faction_changed` (both guarded by `_is_real_number` for the int fields, avoiding the
  MagicMock false-positive class this session's own regression fix already established),
  `recipe_learned` (set-diff, new entries only), `skill_cooldown_started` (dict new/changed
  entry).
- **Real-verification attempted, confirmed unreachable within budget** for `recipe_learned`;
  `entity_role_changed`/`entity_faction_changed`/`skill_cooldown_started` had no live trigger to
  even attempt (established conclusively during Investigate, not just assumed). All 4 verified
  via this repo's own precedented hand-built-state pattern.
- **Parity**: same 3 pre-existing P0 hits re-confirmed unrelated. Added `SUB-378` to
  `docs/parity_ledger/substrate.yaml`. Cross-reference gate PASS.
- Also refreshed a stale cross-reference note at the top of `event_type_coverage.md` (previously
  said 6 mutation types had zero coverage; now accurately reflects that 5 of 6 are fixed and the
  6th — `task` — has a documented deliberate-skip verdict) while touching that file for this
  ticket's own updates.

## Test Summary
- `tests/unit/observability/test_event_extractor_identity.py` (new, 9 tests: 8 hard-assert pass,
  1 soft-warn for the real-kernel `recipe_learned` attempt which did not fire within budget —
  by design, not a failure): `test_entity_role_changed_fires_on_real_delta`,
  `test_entity_faction_changed_fires_on_real_delta`, `test_recipe_learned_fires_on_new_entry`,
  `test_recipe_learned_does_not_fire_on_removal_or_no_change`,
  `test_skill_cooldown_started_fires_on_new_or_changed_entry`, `test_no_event_on_zero_delta`,
  `test_identity_events_suppressed_in_light_and_long_run_modes`,
  `test_recipe_learned_fires_through_real_kernel_tick_once`.
- `tests/unit/observability/` full suite: 981 passed, 6 skipped, 0 failed, 1 warning (973 + 8
  hard-assert new tests, zero regressions; the 9th test's warning is expected/documented).

## Files Changed
- `src/observability/event_extractor.py` — 4 new event emission blocks
- `tests/unit/observability/test_event_extractor_identity.py` — new, 9 tests
- `docs/simulation_quality/event_type_coverage.md` — §5 new rows, Summary counts (22→26), new
  `deliberately_uncovered` category row, refreshed stale top-of-doc cross-reference note
- `docs/event_ledger/entity.yaml` — `ENTITY-007` flipped `partial`→`observed`; `ENTITY-015`
  updated with the deliberate-skip verdict (stays `silent`, now documented not unaddressed)
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-378`

## Completion Summary
Entity role/faction/recipes/cooldowns went from partial to full observability coverage (4 new
events); `TaskUpdate` received a clear, evidenced deliberate-skip verdict rather than staying an
unaddressed gap. Found that role/faction reassignment is a genuinely unimplemented mechanic (not
merely gated) — the first sibling ticket in this batch to find zero real producers at all — and
wired the event anyway per the user's own future-proofing direction. Found a genuinely live,
unconditional `recipe_learned` producer (blacksmith wholesale-learning). Verified all 4 events via
this repo's own precedented hand-built-state pattern after real-kernel attempts (where a live
producer existed) came up empty within budget. This closes out the 4-ticket entity-observability-
gap batch (vitals, attributes, equipment, identity/role/faction) that started from
`TCK-20260808-ENTITY-EVENT-LEDGER`'s original audit.
