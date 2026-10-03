---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260907-CHURCH-CONTENT-AUTHORING
artifact_type: plan
---

# Plan — TCK-20260907-CHURCH-CONTENT-AUTHORING

## Ordered Steps

1. Add a `church` entry to `data/content/world/buildings.yaml` (the real content catalog
   `WorldCompiler`/`BuildingResolver` read). No `service_profile_id` — deliberately does not imply
   functionality. `hp`/`max_hp` set to `1500` to mirror `BuildingRegistry.CHURCH`'s existing
   template value for consistency, even though that registry is otherwise disconnected from this
   path.
2. Add `church: 1` to `frontier_village_core`'s `buildings:` count-map
   (`data/content/world_modules/frontier_village_core.yaml`) — a widely-reused, thematically
   fitting settlement module.
3. Recompile a real consumer world (`sandbox_world`) via `resolve` + `validate`; confirm `church_0`
   appears in the compiled output.
4. Run a real calibration (`tools/calibrate_simq.py --name sandbox_world --seed 42 --ticks 100`) to
   confirm the world runs cleanly with the new building present, and that no CHURCH-specific event
   is ever emitted (the inertness disclosure's own evidence).
5. Add the disclosure entry to `docs/guidelines/intentional_divergences.md` (§2.54), matching the
   "No Live Consumer Yet" precedent shape.
6. Update the ticket's own Implementation Notes/Test Summary/Files Changed/Completion Summary,
   close via Finalize.

## Files to Change

- `data/content/world/buildings.yaml`
- `data/content/world_modules/frontier_village_core.yaml`
- `data/worlds/sandbox_world/resolved/*` (regenerated, not hand-edited)
- `docs/guidelines/intentional_divergences.md`
- `tickets/inprogress/TCK-20260907-CHURCH-CONTENT-AUTHORING.md`

## Explicit Scope Guards

- Do NOT add any code reading `BLESSING`/`RESURRECTION` anywhere in `src/` — the ratified decision
  explicitly rejected building real service logic for this P3 item.
- Do NOT add a `service_profile_id` to the new `church` catalog entry.
- Do NOT recompile every world that composes `frontier_village_core` — one representative
  recompile (`sandbox_world`) is sufficient evidence per the ticket's amended AC.
- Do NOT touch the epic ticket or `SEQUENCE.md`.

## Dependency Map

No dependency on other child tickets in this epic — self-contained content addition.

## Acceptance Criteria Map

- AC1 ("CHURCH placed in at least one real world module") → Steps 1-2.
- AC2 (amended: "placement confirmed via real resolve/validate/calibration run, inertness formally
  disclosed") → Steps 3-5.

## Unresolved Questions
None — real user decision already ratified (see ticket's "Decision, 2026-09-07" section) before
this plan was written.
