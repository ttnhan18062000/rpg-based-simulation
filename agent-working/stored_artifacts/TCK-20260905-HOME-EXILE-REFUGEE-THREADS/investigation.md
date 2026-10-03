---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
artifact_type: investigation
tags: [strategy, world]
---

# Investigation — TCK-20260905-HOME-EXILE-REFUGEE-THREADS

## Current Behavior (file:line refs)

- `StrategicComponent.home_region_id: Optional[str] = None` (`src/core/strategic.py:414`) — a real,
  typed field. `V2EntityBuilder.strategic(home_region_id=...)` (`src/core/builder.py:449-451`)
  already accepts it as a kwarg — no builder plumbing is missing.
- **Confirmed only real production writer today**: `src/world/boss.py:62,135` — reads the boss's
  own spawn position, resolves it to a region, and passes `home_region_id=region_id` into the
  builder. Grepped every other `V2EntityBuilder(...)`/`.strategic(` construction site in `src/`
  (`spawn_humanoid_offspring`, `spawn_natural_creature_offspring`, `spawn_magical_demonic_entity`,
  world-compile-time settlement spawning) — none pass `home_region_id`. Confirms the sibling
  ticket's (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`) own finding: populated only for bosses.
- **Confirmed only real consumer today**: `RoutineService.evaluate_anchored_behavior()`
  (`src/systems/world_systems/routine.py:163-190`) — if `home_region_id` is set, entity is idle,
  and current region (via `LegalityServiceV2.get_region_for_position`) differs from home, emits a
  `concern_return_home` `ConcernState` (urgency 0.4). Called from
  `src/systems/strategic_systems/intelligence.py:541,857` (confirmed via grep).
- `V2EntityBuilder.birth_record()` (`src/core/builder.py:625-640`) has no `home_region_id`/
  `birth_region_id` kwarg — only `birth_city_id`. Confirms the epic's own premise: birth-time
  home-region population is genuinely missing, not just unused.
- **No existing displacement/exile/refugee mechanism anywhere**: grepped `displac|exile|refugee|flee`
  across `src/world/calamity.py` and the whole `src/` tree — zero hits. `CalamityService.
  apply_calamity_consequences()` (`src/world/calamity.py:80-99`) only *increases*
  `region.calamity_intensity` on hero death in a high-hazard region; it never relocates or displaces
  any living entity. `region.calamity_intensity` (a real, live, per-region float already driving
  `CalamityPressurePropagator`'s own seasonal spread logic) is the only real "this region has become
  dangerous" signal that exists today.

## Mechanics/Engine Constraints

- Durable State Rule (`CLAUDE.md`): any new write to `home_region_id` or `entity.navigation.position`
  must go through the authoritative apply-path (typed `StrategicUpdate`/`NavigationUpdate` fields
  applied via `src/engine/patches.py`), never a direct mutation.
- `src/replay/fingerprint.py`: both sibling tickets in this epic (idea 39, idea 56) independently
  found and fixed real determinism-coverage gaps in `StateFingerprinter`. `home_region_id` and
  `navigation.position` must be confirmed covered before this ticket closes — checked directly
  during Implement, not assumed.
- No Mechanics Bible chapter exists for this content (same gap idea 39's own ticket disclosed) —
  document in a `docs/world/` contract doc, cross-reference `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`.

## Docs Requiring Update

- `docs/world/home_exile_refugee_contract.md` (new)
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` (status annotation)
- `docs/parity_ledger/world_dynamics.yaml` (new entry: birth-time `home_region_id` population)
- `docs/parity_ledger/strategic_cognition.yaml` (new entry: displacement-time `home_region_id`
  write + its interaction with `evaluate_anchored_behavior()`)

## Parity Ledger Overlap (IDs + status)

None pre-existing for either mechanism. `next_available_id()` at investigation time (to be
re-confirmed live at Parity phase, not cached here): `world_dynamics.yaml` and
`strategic_cognition.yaml` next available IDs computed fresh during Parity.

## Prior Work

- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39, DONE, commit `d86b882b`) — sibling,
  no hard dependency, but established the `StateFingerprinter` determinism-gap precedent this
  ticket must check for its own new fields.
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56, DONE, commit `a8567112`) — sibling, no hard
  dependency; its own Investigate phase is the source of the "home_region_id only populated for
  bosses" finding, independently re-confirmed here via direct grep.
- `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`/`-GENETICS-INHERITANCE` (M3) — the precedent
  shape for extending `birth_record()`/`spawn_humanoid_offspring()` with new optional kwargs
  threaded through a real call chain, reused here for `home_region_id` at birth.

## Risks and Open Questions

- **Design decision, resolved here with real evidence**: the displacement trigger is
  `region.calamity_intensity` crossing a threshold (reusing the existing, live signal — no new
  detection mechanism invented) for a living entity currently positioned in that region. This
  reuses `apply_calamity_consequences()`'s own established `hazard_level > 0.5`-shaped threshold
  convention rather than inventing a new one.
- **Design decision, resolved here**: displacement should NOT overwrite an already-set
  `home_region_id` — a refugee's `home_region_id` continues to represent their *original* home even
  after being forced to relocate current position elsewhere. This is what makes
  `evaluate_anchored_behavior()`'s existing "return home" concern narratively meaningful for free:
  a refugee is definitionally "idle and away from home" the moment they're relocated.
- **Design decision, resolved here**: birth-time population (idea 59) derives the home region from
  the spawn position (`pos` parameter already threaded through `spawn_humanoid_offspring()`), via
  the same `LegalityServiceV2.get_region_for_position()` helper `boss.py`/`routine.py`/`calamity.py`
  already use — no new region-resolution logic needed.
- Whether displacement should also relocate `entity.navigation.position` to a *specific* safer
  region (nearest low-`calamity_intensity` neighbor) or simply mark the entity as displaced without
  a forced position change is a real Plan-phase decision — Investigate found no existing
  "find nearest safe region" helper to reuse; a naive first implementation should pick the lowest-
  `calamity_intensity` neighbor via `RegionalPressureModel`'s existing adjacency helper
  (`CalamityPressurePropagator._are_adjacent`, `src/world/calamity.py`) rather than inventing new
  adjacency logic.

## Anti-Drift Hazards

- Do not conflate this ticket's displacement mechanism with idea 39's `Faction.NEUTRAL` defection
  trigger (`PartyLifecycleService.check_defection()`) — they are different triggers (calamity
  vs. social grievance) writing to different fields (`navigation.position`/`home_region_id` vs.
  `identity.faction`). No shared code path is expected; if one is found, treat it as a Plan-phase
  finding to disclose, not something to silently merge.
- Do not repurpose `region.calamity_intensity` semantics — read it, never mutate its existing
  meaning or thresholds owned by `CalamityService`/`CalamityPressurePropagator`.
