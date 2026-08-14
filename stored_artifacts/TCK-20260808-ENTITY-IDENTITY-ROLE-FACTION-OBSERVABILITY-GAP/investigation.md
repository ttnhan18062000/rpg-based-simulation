---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP

## Docs Requiring Update

- `docs/simulation_quality/event_type_coverage.md`: register the new event(s) (Implement phase)
- `docs/event_ledger/entity.yaml`: update `ENTITY-007`/`ENTITY-015` (Implement phase)

## `role_set` / `faction_set` — genuinely never mutated anywhere, not just gated

`grep -rn "role_set\s*=\|faction_set\s*=" src/` (excluding the type's own definition/apply/patch
machinery) returns **zero** real assignment sites. This is a different reachability class from
every other sibling ticket's findings so far (vitals/attributes/equipment all found at least one
producer, even if gated or narrow) — role/faction reassignment (defection, promotion) is a
defined-but-entirely-unimplemented mechanic. The only place `faction_set` is even *read* is
`src/observability/event_shapers.py:1222`'s `faction_extinct` detection, which uses it only to
compute an entity's *current effective* faction for a population-extinction check — it does not
emit any event about the reassignment itself, and doesn't change this verdict.

Per the ticket's own Assumptions/Open Questions ("not assumed; Investigate must confirm real
mutation sources exist") — confirmed: they don't. Not fabricating a route for this (per this
session's own standing discipline against forcing unrealistic routes to hit a target) — the event
is still designed and wired below (future-proof, zero runtime cost when unused, matches the
user's own "even invisible events, maybe we will change the code to make it visible" direction),
but verified only via hand-built state since there is no live trigger of any kind, gated or
otherwise, to attempt a real-kernel check against.

## `recipes_learned` — 3 producers, 1 genuinely LIVE and unconditional

| Site | Verdict | Evidence |
|---|---|---|
| `src/engine/blacksmith.py:143` (`BlacksmithSystem.enforce`, wholesale recipe grant) | **LIVE, unconditional** | `pipeline.py:174`: `run_phase("blacksmith", update, lambda u: BlacksmithSystem.enforce(state, u))` — no feature-flag argument (contrast `progression_conversion`'s 4-arg call with `"ENABLE_PROGRESSION_EVOLUTION"`). Runs every tick, unconditionally. Fires when an entity occupies a functional blacksmith building tile with empty `known_recipes` — grants all `BlacksmithSystem.RECIPES` at once ("Wholesale learning (Parity with V1)"). |
| `src/engine/domain/core_actions.py:205` (`execute_train`) | **WIRED, no live AI driver** | Routed via `action_router.py`'s `"TRAIN"` action. `grep -rn "\"TRAIN\"\|'TRAIN'" src/ai/ src/engine/intent/action_intent.py` returns zero hits — nothing ever selects this action, same reachability class as `ALLOCATE_AP`/`REPAIR` in the sibling attributes/equipment tickets. |
| `src/town/class_hall.py:33` (`ClassHallAction.train`) | **DEAD CODE** | `grep -rln "ClassHallAction\|class_hall" src/` returns zero hits outside its own file — never called. |

## `cooldown_updates` — 1 producer, wired but no live driver

`src/engine/domain/skill_actions.py:113` sets `cooldown_updates` after a skill use. Routed via
`action_router.py`'s `"SKILL"` action. `grep -rn "\"SKILL\"\|'SKILL'" src/ai/
src/engine/intent/action_intent.py` returns zero hits — same "real, wired, no live AI driver"
class as `execute_train`/`execute_repair`/`execute_allocate_ap` in the sibling tickets.

## `TaskUpdate.work_kind_set` — verdict: deliberately NOT worth an event

`grep -rn "work_kind_set=" src/` returns 24 hits, overwhelmingly from `src/engine/tactical.py`,
`src/engine/executor.py`, `src/engine/worker_logic.py` — the core per-tick action-scheduling
internals. Every entity gets a `work_kind_set` of `"ENTITY_MOVE"` or `"ENTITY_ACT"` on essentially
every tick it acts at all; this is which-verb-executes-this-tick scheduling plumbing, not
persistent narrative state. Confirms the ticket's own hypothesis and `ENTITY-015`'s existing
ledger note ("Plausibly intentional... internal bookkeeping"). A handful of hits
(`resolver.py`'s `BLACKSMITH_REPAIR`/`BLACKSMITH_CRAFT`/`ASK_INFORMATION`) are more
narratively-flavored but are themselves part of the same `ENABLE_PROGRESSION_EVOLUTION`-gated
domain already covered in the attributes/equipment tickets' findings, and don't change the
overall verdict given the field's dominant real usage pattern.

**Verdict: no `TaskUpdate` event.** Emitting one would be `movement`-class volume (every acting
entity, every tick) for a field carrying zero narrative content beyond "what verb runs next" —
unlike `movement` itself (which at least carries positional/spatial meaning), `work_kind_set` is
pure scheduling plumbing. This is a documented deliberate skip, not a silent drop, satisfying the
ticket's own Acceptance Criteria.

## Event design

Post-tick STATE diffing, same methodology as the sibling tickets. `IdentityComponent`
(`src/core/state.py:469-489`): `role: int`, `faction: int`, `known_recipes: Set[str]`,
`cooldowns: Dict[str, int]`.

- **`entity_role_changed`** — fires when `entity.identity.role != prior_ent.identity.role`.
  Severity `INFO` — a reassignment is inherently notable but not itself good/bad the way a
  decline/wound is, and no existing signal in the repo distinguishes "which role change is
  concerning." Currently cannot fire in any real path (see above) — future-proofed, not dead.
- **`entity_faction_changed`** — same shape, `entity.identity.faction`. Same severity reasoning.
- **`recipe_learned`** — per newly-present entry in `entity.identity.known_recipes` (set diff,
  new - prior). Severity `INFO`. The one genuinely reachable new event in this ticket via a real
  `Kernel.tick_once()` loop (blacksmith visit is unconditional).
- **`skill_cooldown_started`** — per `cooldowns` entry that's new or whose `tick_ready` value
  changed (skill use resets the cooldown). Severity `INFO`. Real, wired, currently unreachable
  (no live AI driver for `"SKILL"`) — same fallback-verification class as wound events.

## Real-verification (actual result, not just the plan)

Attempted a real `Kernel.tick_once()` loop for `recipe_learned` first (1500 ticks,
`sandbox_world`, seed 42) — checked directly, not assumed: `sandbox_world` has 1 blacksmith
building and all 18 entities start with empty `known_recipes`, so the mechanic's trigger
conditions ARE met in principle; no entity happened to path onto the exact blacksmith tile within
the 1500-tick window though. Same reachability class as the equipment ticket's goblin-evolution
gear grant (real, live, trigger conditions satisfiable, just not naturally exercised within a
practical verification budget). Fell back to this repo's own precedented hand-built-state
pattern for all 4 new events (`entity_role_changed`/`entity_faction_changed` have no live trigger
path at all; `skill_cooldown_started` has no live AI driver; `recipe_learned` per the above).

## Classification (per explicit user direction — precise, not binary)

Currently: `docs/event_ledger/entity.yaml` `ENTITY-007` = `partial` (skills/traits/evolution_level
observed; role/faction/recipes/cooldowns silent), `ENTITY-015` = `silent` (TaskUpdate). After this
ticket: `ENTITY-007` → `observed` (all sub-fields now covered, either by an event or a documented
deliberate skip verdict — role/faction/recipes/cooldowns are the un-covered remainder, now fixed);
`ENTITY-015` stays `silent` but with a documented, deliberate verdict rather than an
unaddressed gap — reclassified with a clear rationale note, not silently left as-is. New events
classified `unscored_intentional` (`docs/simulation_quality/event_type_coverage.md` §5) — the
ticket's own Out of Scope flags FACTION pillar as a plausible future candidate for
`entity_faction_changed`, not decided here.
