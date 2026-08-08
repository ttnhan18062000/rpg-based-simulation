---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION
artifact_type: investigation
tags: [observability, engine, simulation-quality, progression]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION

## Current Behavior — field-mapping confirmation

Confirmed all 7 events' exact source, per `event_extractor.py:266-282,773-834` against
`IdentityUpdate` (`src/core/updates.py:220-243`):

| Event | Source field | Notes |
|---|---|---|
| `xp_granted` | `evolution_points_delta: int` | direct |
| `level_up` | `evolution_level_set: Optional[int]` | direct, fallback to `prior_id.evolution_level` for the "did it increase" comparison |
| `skill_unlocked` | `learned_skills: list[str]` | confirmed a per-tick accumulator, not a full-snapshot replacement — traced construction site `src/engine/evolution.py:122-125`: `learned_skills=list(set(id_upd.learned_skills + skills_to_learn))` unions newly-unlocked IDs into whatever the update already carries. Unlike `traits_add`/`breakthroughs_add`, this field's name has no `_add` suffix — required tracing to confirm delta semantics, not assumed from naming alone. |
| `trait_expressed` | `traits_add: list[str]` | direct |
| `pillar_trait_unlocked` | `breakthroughs_add: list[str]` | direct |
| `progression_conversion_applied` | `unspent_ap_delta: int` | direct (`ap_spent = -delta` when negative) |
| `progression_plateau_detected` | cross-tick derived | shaper-local state, same pattern as `StrategyShaper`'s `belief_stale`/`route_family_first_use` |

## Key finding (real bug, fixed): `progression_plateau_detected` needs any-update gating, not identity-update gating

Found via real, non-mocked kernel run (`dungeon_crawl_seed42_500t`): with
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2=ON`, `event_extractor` delivered 32
`progression_plateau_detected` events (unchanged, its branch isn't flag-gated yet) but
`event_shapers` delivered **0** — a clear divergence, not assumed correct.

Root cause: the old extractor's plateau check sits inside `for eid in dirty_entity_ids`
(`event_extractor.py:122`, `= update.entity_updates.keys()` under normal operation) and reads
`entity.identity`/`prior_ent.identity` — the entity's `IdentityComponent`, which **always exists**
on every `EntityState` regardless of whether that tick's `EntityUpdate` happened to include an
`identity` sub-update. So the old extractor checks plateau status for every dirty entity, for ANY
reason it's dirty (e.g. a routing change with zero identity change). My first implementation gated
the entire per-entity block on `id_upd = getattr(e_upd, "identity", None); if id_upd is None:
continue` — narrower than `dirty_entity_ids`, since `EntityUpdate.identity` is only non-`None`
when something identity-specific changed that tick. This is the exact same category of gap found
and fixed for `belief_stale` in `StrategyShaper` (materialized-component-always-exists vs.
update-sub-record-sometimes-`None`), not a new kind of bug.

**Fix**: restructured `shape()` so `progression_plateau_detected`'s check runs unconditionally for
every entity with SOME update this tick, using `prior_id` (always available via `prior_ent`) as
the baseline and `id_upd` (possibly `None`) only for this tick's XP/level/skill delta
contribution. The other 6 events remain gated on `id_upd is not None` (correct — they only have
something to report when an identity-specific update exists).

**Verified the fix directly**: same real kernel run, `ON` mode now shows
`event_extractor=32, event_shapers=32` — exact parity, confirming the shaper reproduces the old
extractor's plateau logic exactly, not just approximately. `SHADOW` mode confirmed 0 delivered
(construct-without-deliver, same verification methodology `StrategyShaper` established).

## Key finding 2: registering a 2nd Phase 2 shaper broke Child 2's own registry-level tests

Adding `ProgressionShaper` to `PHASE2_SHAPER_REGISTRY` made `run_shadow_shapers()`'s registry-level
tests in `test_event_shapers_strategy.py` (Child 2, previously green) crash — those tests' mock
`EntityUpdate` never set `.identity` explicitly, so it defaulted to an auto-generated `MagicMock`
that `ProgressionShaper` (now also invoked by the same `run_shadow_shapers()` call) tried to read
real fields from. Fixed by adding `u.identity = None` to `test_event_shapers_strategy.py`'s
`_entity_update()` helper, alongside the existing `.combat`/`.intent_results` inertness. **Every
future Phase 2 child's own registry-level tests need the same defensive inertness for whatever new
shaper fields it introduces** — flagging this pattern for children 4-5, not just fixing it here.

## Docs Requiring Update

- `docs/parity_ledger/progression.yaml`: new entry for the shaper build.

## Parity Ledger Overlap

`progression.yaml` — no existing entry for this shaper work.

## Prior Work

- `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY` (Phase 2, DONE) — the `PHASE2_SHAPER_REGISTRY`/
  flag-split mechanism and the "materialized-component-always-exists" gating pattern this ticket
  reuses and confirms generalizes.

## Risks and Open Questions

None left open.

## Anti-Drift Hazards

- `ProgressionShaper.reset_run_state()` must stay wired into `Kernel.__init__` alongside
  `StrategyShaper`'s and `EventExtractor`'s — omitting it would leak `_last_xp_tick`/
  `_emitted_plateau` across separate runs within the same process.
