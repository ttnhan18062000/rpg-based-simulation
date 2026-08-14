---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT
artifact_type: plan
tags: [observability, engine, combat, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT

## Unresolved Questions

None — all 3 decision points from investigation.md are resolved with reasoning (migrate
hazard_drain_applied/hero_death_unrecorded; defer demographic_mortality; disclose
combat_resolved/attrition_threshold_crossed as dead). Flag mechanism and dispatch point both
verified against real source.

## Steps

1. New module `src/observability/event_shapers.py`: `EventShaper` base/protocol, `SHAPER_REGISTRY`
   dict keyed by a domain label (not update-record type directly, since one update record —
   `EntityUpdate` — can drive multiple domains; the registry is `{"combat": [CombatShaper()], ...}`
   for now, extended by later child tickets), and a `run_shadow_shapers(prior_state, update, tick)`
   entry point that iterates registered shapers and returns constructed events without touching
   the live queue.
2. `CombatShaper.shape(prior_state, update, tick) -> list[SimulationEvent]`: for each
   `eid, e_upd in update.entity_updates.items()`, read `e_upd.combat`; apply the same
   attacker_id-primary/outcome_kind-defense-in-depth discriminant as the hotfix's
   `_real_combat_update()` (import and reuse that exact function from `event_extractor.py` rather
   than reimplementing the logic — single source of truth for the discriminant); derive
   `combat_initiated`/`combat_damage`/`near_death_survival`/`entity_killed` (translated name, to
   match what the scorer expects directly — see Decision below) from `prior_state.entities[eid]`
   + the update's delta fields, matching the current extractor's exact thresholds/payloads.
   Also derive `hazard_drain_applied`/`hero_death_unrecorded` from the same per-entity read.
3. **Naming decision**: emit `entity_killed` directly (not `combat_kill`) from the shaper, since
   the translation from `combat_kill`→`entity_killed` in `quality_hub.py`'s `_translate()` exists
   only because `event_extractor.py` uses a typed `CombatKillEvent` class with a fixed
   `event_type="combat_kill"` default — the shaper has no such constraint and can emit the
   scorer-facing name directly, one fewer translation hop. Document this as an intentional,
   disclosed naming difference from the old path (functionally identical event, different
   intermediate name) — the shadow-mode comparison ticket must account for this when comparing
   old-vs-new output (compare post-translation names, not raw event_type strings, for this one
   case).
4. Add `ENABLE_PUSH_EVENT_SHAPERS` to `FeatureFlagManager.__init__` (default OFF) and
   `calibrate_simq.py`'s `_KNOWN_FLAGS`.
5. Wire `run_shadow_shapers()` into `kernel.py`'s `_phase_observability()`, gated on
   `prior_state.feature_flags.get("ENABLE_PUSH_EVENT_SHAPERS", "OFF") in ("SHADOW", "ON")` — in
   SHADOW mode, constructed events are logged (e.g. `logger.debug` with a structured summary) but
   never pushed to `self._event_recorder`; `"ON"` mode is reserved for a future ticket (cutover),
   not implemented here.
6. Update `docs/guides/feature_flags.md`'s "The 11 flags" table (becomes 12).
7. Unit tests in `tests/unit/observability/test_event_shapers.py`: registry mechanism generically;
   `CombatShaper` for all 6 events (4 core + 2 colocated); hazard/biological exclusion (same
   collision risk as the hotfix); SHADOW-mode inertness (queue unaffected).

## Scope guard

`event_extractor.py` is not modified — confirmed via `git diff` before Finalize. `apply.py`/
`apply_plan.py` are not modified — confirmed the same way, per the epic-level design refinement.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Registry mechanism implemented | Step 1 |
| CombatShaper implemented | Step 2 |
| hazard/hero_death/demographic decisions documented | investigation.md Decisions 1-2 |
| combat_resolved/attrition dead-code disclosed | investigation.md Decision 3 |
| SHADOW-mode inert, wired via kernel.py | Steps 4-5 |
| Unit tests | Step 7 |
| event_extractor.py untouched | Scope guard |
