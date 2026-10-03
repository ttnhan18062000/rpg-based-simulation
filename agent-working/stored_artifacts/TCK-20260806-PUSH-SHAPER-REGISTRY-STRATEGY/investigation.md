---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY

## Current Behavior — field-mapping confirmation

Confirmed all 14 events' exact source, per `event_extractor.py:295-563`:

| Event | Source (old extractor) | Confirmed push-ready via |
|---|---|---|
| `route_selected`/`action_executed`/`route_family_first_use` | `e_upd.property_updates["last_routing_family"]` (`:301`) | Same field, direct read — already non-diffing |
| `defer_with_reason` | `e_upd.property_updates["last_defer_reason"]` (`:328`) | Same field |
| `self_model_updated` | `e_upd.self_model_bundle_set is not None` (`:338`) | Same field |
| `belief_assimilated`/`belief_updated` | `e_upd.property_updates["last_assimilated_tick"] == prior_state.tick` (`:347`) | Same field |
| `route_new_query` | `e_upd.property_updates["last_routed_query_tick"] == prior_state.tick` (`:363`) | Same field |
| `cooperation_event` | `e_upd.property_updates["last_cooperation_decision"]` (`:373`) | Same field |
| `lead_certainty_changed`/`lead_certainty_updated` | diffs `entity.strategic.leads` (materialized) vs `prior_ent.strategic.leads` (`:479-505`) | `StrategicUpdate.leads_add_or_update: list[LeadState]` (`src/core/updates.py:480`) — each entry IS the new value (frozen dataclass, any change constructs a fresh instance) |
| `belief_stale` | full scan of `entity.strategic.leads` (materialized) (`:506-523`) | `_current_leads()` helper: `prior_ent.strategic.leads` (full prior snapshot) merged with this tick's `leads_add_or_update`/`leads_remove` |
| `decision_diverged_by_belief` | `entity.strategic.current_project_id`/`.projects` (materialized) (`:525-542`) | `StrategicUpdate.current_project_id_set` (fallback to `prior_strategic.current_project_id`) + `projects_add_or_update`/`projects_remove` merged with prior |
| `decision_divergence_detected` | `entity.strategic.concerns` (materialized) (`:544-563`) | `concerns_add_or_update`/`concerns_remove` merged with prior, same pattern |

## Key finding 1: `belief_stale` looked materialized-state-only, but isn't

Initial read suggested `belief_stale` (re-checks ALL of an entity's current leads every tick, not
just changed ones) needed post-apply `current_state` — architecturally unavailable to a shaper by
design. Resolved by confirming `event_extractor.py:122`'s own `dirty_entity_ids = update.
entity_updates.keys()` (falls back to all entities only when `entity_updates` is empty entirely —
not normal per-tick operation): the OLD extractor **also** only visits entities with some update
this tick. Since `AuthoritativeState` is a full snapshot each tick (not incremental),
`prior_ent.strategic.leads` (full prior snapshot) merged with this tick's `leads_add_or_update`/
`leads_remove` delta reconstructs the exact same "current leads" view the old extractor computes
from materialized state — for any entity visited at all, which both implementations require
identically. Implemented as a shared `_current_leads()` module helper, reused by
`decision_diverged_by_belief`'s `has_vague_lead` check too. No genuine architectural gap — all 14
events are push-ready with zero new instrumentation.

## Key finding 2 (real bug, fixed): registering directly into `SHAPER_REGISTRY` double-fires

Discovered via a real, non-mocked kernel run (not assumed): `ENABLE_PUSH_EVENT_SHAPERS` already
defaults `ON` (Phase 1's cutover flipped it), and `Kernel._phase_observability`'s ON/SHADOW switch
applies uniformly to `run_shadow_shapers()`'s **entire** return value. Registering `StrategyShaper`
directly into the existing `SHAPER_REGISTRY` — the pattern Phase 1's own shaper-build children used
safely, because at that time the flag still defaulted `OFF` — made it **live-deliver immediately**
on landing, with zero SHADOW window, since `event_extractor.py`'s corresponding branches for these
14 events were never flag-gated (Phase 1 only gated COMBAT/ECONOMY/FACTION). Confirmed via direct
JSONL inspection: `self_model_updated`/`cooperation_event` both showed `source_system=event_extractor`
AND `source_system=event_shapers` firing simultaneously, roughly doubling delivered counts.

**Fix**: added `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (new flag, default `OFF` per standard DEV-002
policy — unlike `ENABLE_PUSH_EVENT_SHAPERS`, which was a deliberate, documented exception).
`StrategyShaper` lives in a new `PHASE2_SHAPER_REGISTRY`, gated **inside** `run_shadow_shapers()`
itself: `OFF` → not even constructed (zero overhead); `SHADOW` → constructed, logged, excluded from
the returned list (so `Kernel._phase_observability` never sees anything to deliver, regardless of
the Phase 1 flag's own state); `ON` → included in the return (will still double-fire against
`event_extractor.py`'s unguarded branches until Cutover — expected and out of this ticket's scope,
exactly mirroring how Phase 1's own shaper-build children never touched `event_extractor.py`
either, only Child 5/Cutover did).

**Verified all 3 states directly**:
- Default (flag absent → `OFF`): `event_shapers` source count = 0 for all 14 event types — no
  double-fire, confirmed via real kernel run + JSONL inspection.
- `SHADOW`: constructed 5610 `self_model_updated` + 455 `cooperation_event` (captured via direct
  function-return inspection); delivered-to-JSONL `event_shapers`-sourced count = 0 — construct
  without deliver confirmed.
- `ON`: `event_extractor`=3128, `event_shapers`=3128 for the same 6256 total strategy-type
  events — exact 50/50 double-fire confirmed, as expected (Cutover's job to resolve, not this
  ticket's).

This finding and fix apply to every future Phase 2 shaper (children 3-5 will each add their shaper
class to `PHASE2_SHAPER_REGISTRY`, not `SHAPER_REGISTRY`) — recorded here since this is the first
child to discover it, cross-reference from each subsequent child's own investigation.md rather
than re-deriving.

## Key finding 3 (real bug, fixed): missing `reset_run_state()` for the new per-run caches

`route_family_first_use`/`belief_stale` need cross-tick, per-run dedup state
(`_seen_routing_families`/`_emitted_stale_leads`), mirrored from `EventExtractor`'s identically-named
class attributes. `EventExtractor` has a `reset_run_state()` classmethod, called once at
`Kernel.__init__` (`kernel.py:311`) specifically because these are class-level (process-lifetime)
attributes that would otherwise leak across separate runs within the same process (e.g. two
consecutive calibration runs in one pytest session or one `calibrate_simq.py` invocation loop).
`StrategyShaper`'s new caches had no equivalent — found by inspection while implementing the class,
not by an actual observed leak, but real and worth fixing before it caused one. Added
`StrategyShaper.reset_run_state()`, wired into `Kernel.__init__` immediately after
`EventExtractor.reset_run_state()`. Confirmed importable and non-breaking via a direct import
smoke check.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml`: new entry (`STRAT-247`) documenting the shaper
  build (SHADOW state) and the `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag split finding.
- `docs/parity_ledger/social_narrative.yaml`: new cross-reference entry (`SOC-239`) for
  `cooperation_event` (SOCIAL-scored but STRATEGY-implemented).
- `docs/guides/feature_flags.md`: new flag row added — and, found stale while doing so, the
  EXISTING `ENABLE_PUSH_EVENT_SHAPERS` row still said "Default: OFF" / "ON mode is reserved for a
  future cutover ticket, not implemented," predating Phase 1's cutover (which already flipped it
  to `ON` and implemented delivery). Phase 1's own cutover ticket should have updated this row but
  didn't — fixed here as a pre-existing doc-staleness gap found incidentally, not this ticket's own
  drift. "12 flags" → "13 flags" throughout (11 default-OFF + 2 documented exceptions).

## Parity Ledger Overlap

`strategic_cognition.yaml` and `social_narrative.yaml` — no existing entry for this exact shaper
work; new entries needed (see Docs Requiring Update).

## Prior Work

- `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`, `TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION` (Phase 1,
  DONE) — the shaper-registry pattern this ticket extends.
- `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC` (parent epic) — the field-level
  readiness audit this ticket's own Investigate phase confirms in full detail.

## Risks and Open Questions

None left genuinely open — both findings above were fully resolved, not deferred.

## Anti-Drift Hazards

- `PHASE2_SHAPER_REGISTRY` must not be merged into `SHAPER_REGISTRY` by any future child before
  Cutover (child 8) — doing so would reintroduce the exact double-fire bug this ticket fixed.
- `_current_leads()`/the projects/concerns merge pattern assumes `*_add_or_update` lists never
  contain a stale/superseded entry for the same tick (last-writer-wins via dict overwrite) —
  matches `StrategicUpdate.merge()`'s own semantics, not a new assumption.
