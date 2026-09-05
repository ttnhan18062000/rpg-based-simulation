---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
artifact_type: plan
tags: [strategy, world]
---

# Plan — TCK-20260905-HOME-EXILE-REFUGEE-THREADS

## Ordered Steps

1. **Birth-time `home_region_id` population (idea 59).** Extend
   `EntityGenerator.spawn_humanoid_offspring()` (`src/systems/world_systems/generator.py:159`) to
   resolve the spawn `pos` to a region via `LegalityServiceV2.get_region_for_position(pos, state)`
   and pass the result into `.strategic(home_region_id=region.id if region else None)` on the
   `V2EntityBuilder` chain it already constructs. No new builder plumbing needed — `.strategic()`
   already accepts this kwarg (`src/core/builder.py:449-451`). Files: `generator.py` only.
   AC mapped: idea 59 population-rule AC.

2. **`DisplacementService` (idea 65) — new module, `src/world/displacement.py`.** A pure
   `@staticmethod compute_displacement(state: AuthoritativeState) -> StateUpdate` that:
   - Iterates `state.regions.values()` in `sorted(key=lambda r: r.id)` order (determinism guard —
     the exact bug class PR #128 caught) to find regions with `calamity_intensity >=
     DISPLACEMENT_THRESHOLD` (new constant, `0.6`, one tier above `apply_calamity_consequences()`'s
     own `hazard_level > 0.5` — deliberately distinct thresholds since one gates calamity-intensity
     *growth* and the other gates displacement *consequence*, not the same event).
   - For each such region, finds living entities whose `navigation.position` resolves to that
     region (`LegalityServiceV2.get_region_for_position`), iterated in `sorted(key=lambda e:
     e.entity_id)` order.
   - For each affected entity: picks the lowest-`calamity_intensity` adjacent region via
     `CalamityPressurePropagator._are_adjacent`-shaped adjacency (read-only reuse of that
     precedent's adjacency test, not its mutation logic) — ties broken by region id, sorted.
     Produces `EntityUpdate(entity_id=..., new_position=<new region's center>)` for that entity
     — **correction found during Review**: `NavigationUpdate` has no `position_set` field; the real,
     already-used mechanism for teleporting an entity is the top-level `EntityUpdate.new_position`
     field (`src/core/updates.py:689`), applied via `NavigationPatch.apply()`'s existing
     `self.new_position` branch (`src/engine/patches.py:287-289`,
     `ApplyPath._fast_replace_navigation`) — confirmed real, already-used precedent at
     `src/engine/movement.py:129,304`. No new Navigation plumbing needed at all.
     If `entity.strategic.home_region_id` is `None`, also sets `entity_updates[entity_id].strategic
     = StrategicUpdate(home_region_id_set=...)` on the SAME `EntityUpdate` — preserving an
     already-set value untouched (a boss's own home stays their own home even if displaced).
   - Returns a `StateUpdate` with `entity_updates` keyed by `entity_id`, applied through the normal
     authoritative apply-path — never a direct mutation.
   Files: new `src/world/displacement.py`. **Confirmed during Review**:
   `home_region_id_set: Optional[str] = None` does NOT yet exist on `StrategicUpdate`
   (`src/core/updates.py:513-533` — checked directly, only `current_project_id_set`/
   `current_objective_id_set` exist as analogous single-value setters) — must be added, along with a
   matching branch in `StrategicPatch.apply()` (`src/engine/patches.py:436+`) mirroring
   `current_project_id_set`'s own if-not-None-else-existing pattern exactly.
   AC mapped: idea 65 displacement-trigger AC, home_region_id-preserved-if-set AC.

3. **Wire `DisplacementService.compute_displacement()` into the live pipeline.** Call it from the
   same per-tick or per-world-dynamics-cycle location `CalamityService.process_world_dynamics()`
   is called from (confirm the real call site during Implement — likely `src/engine/pipeline.py` or
   `src/engine/world_dynamics.py`, mirroring this session's own M4-batch precedent for
   `CampService`/faction-directive wiring). Merge its `StateUpdate` into the existing dynamics
   update, not a parallel unmerged path.
   AC mapped: "real, tested" requirement — must be live, not built-not-wired like the M5 batch's
   disclosed gaps (avoid repeating that pattern here since a real, cheap wiring point exists).

4. **Determinism coverage.** Confirm `StrategicComponent.home_region_id` and
   `NavigationComponent.position` already participate in `StateFingerprinter`
   (`src/replay/fingerprint.py`) and `EntityState.to_canonical_dict()`. If either sibling ticket's
   own fix (idea 39/56, both landed) already extended `StateFingerprinter` broadly enough to cover
   these pre-existing fields, this step may already be satisfied — verify directly, do not assume
   either way given the prior gap precedent.

5. **Documentation.** New `docs/world/home_exile_refugee_contract.md` describing both mechanisms
   (birth-time population, calamity-driven displacement) with the exact threshold/adjacency-tiebreak
   rules from step 2. Cross-reference `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` rather than
   duplicating full Mechanics Bible integration. Update the M6 epic doc's status annotation.

6. **Parity ledger.** New entries in `world_dynamics.yaml` (birth-time population) and
   `strategic_cognition.yaml` (displacement + its interaction with `evaluate_anchored_behavior()`),
   via `tools/parity_ledger_writer.py::write_entry` only — never hand-edited.

## Files to Change

- `src/systems/world_systems/generator.py` (step 1)
- `src/world/displacement.py` (new, step 2)
- `src/core/updates.py` (step 2, only if `StrategicUpdate.home_region_id_set` is missing)
- Pipeline wiring file (step 3, confirmed during Implement)
- `src/engine/patches.py` (step 2/3, only if a new dirty-check branch is needed for
  `home_region_id_set` — check whether `StrategicPatch.apply()` already handles arbitrary
  `StrategicComponent` field replacement generically before assuming a new branch is needed)
- `docs/world/home_exile_refugee_contract.md` (new)
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`
- `docs/parity_ledger/world_dynamics.yaml`, `docs/parity_ledger/strategic_cognition.yaml`
- New test files per test_plan.md

## Explicit Scope Guards

- Do NOT touch `identity.faction` or `PartyLifecycleService` (idea 39's own territory).
- Do NOT touch `LoyaltyDriftService` or its wiring into `party_lifecycle.py` (idea 56's own
  territory) — this ticket's displacement trigger is calamity-driven, not loyalty/faction-driven,
  per Investigate's own resolved design decision.
- Do NOT modify `CalamityService.apply_calamity_consequences()`'s or
  `CalamityPressurePropagator`'s own read/write semantics — `DisplacementService` only reads
  `region.calamity_intensity`, never writes it.
- Do NOT invent a new adjacency-resolution algorithm — reuse
  `CalamityPressurePropagator._are_adjacent`'s existing shape read-only.

## Dependency Map Between Steps

Step 1 is fully independent. Steps 2-4 must land together (a `DisplacementService` with no live
wiring, or with wiring but no fingerprint coverage, would repeat the "built, not visible" gap this
epic's own siblings already disclosed once each — this ticket should be fully live, not deferred,
since the wiring point is cheap and confirmed to exist). Step 5-6 follow once 1-4 are implemented.

## Acceptance Criteria Map

- Birth/settlement population AC → Step 1.
- Displacement/refugee-thread AC → Steps 2-3.
- `evaluate_anchored_behavior()` reacts correctly to post-displacement `home_region_id` AC → Step 2
  (no change to `routine.py` itself needed — the existing consumer already does the right thing
  once `home_region_id` differs from current position, confirmed by direct read in Investigate).
- Documentation AC → Step 5.
- Parity-ledger AC → Step 6.

## Unresolved Questions

None — Investigate's own open design questions (displacement trigger source, whether to preserve
existing `home_region_id`, whether to force a position change) were all resolved with real evidence
during Investigate itself (see investigation.md's own "Risks and Open Questions" section, each
marked "resolved here"). No blocking ambiguity remains for Review/Implement.
