---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260907-CHURCH-CONTENT-AUTHORING
phase: done
date: 2026-09-07
tags: [content, world]
---

# TCK-20260907-CHURCH-CONTENT-AUTHORING

## Title
Place the CHURCH building's Blessing/Resurrection services into at least one real world module

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 6 of 6,
lowest priority. `CHURCH`'s Blessing/Resurrection services (`src/town/buildings.py:15,23`) are fully
coded and real, but placed in zero of the 20 world modules and 21 compiled worlds — confirmed by
direct grep during the 2026-09-02 hardening pass, not re-verified stale since. This is a pure
content-authoring gap, not a code bug.

## Scope
- Confirm the finding is still accurate during Investigate (re-grep the 20 world modules for
  `CHURCH`/`Church` building placements).
- Add `CHURCH` to at least one real world module's building composition (a low-risk, additive content
  change — no schema or code change expected).
- Confirm the building's Blessing/Resurrection services function correctly once placed, via a real
  test or calibration run.

## Out of Scope
- Building any new CHURCH mechanic — the services already exist and are correct; this ticket only
  places the building where it can actually be used.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [x] **Amended 2026-09-07 (2nd revision, real user decision after independent review)**: `CHURCH`
      is **not** placed — deferred, matching idea 30's own treatment for the structurally identical
      "neither producer nor consumer" gap. The original AC text (placement + functional services,
      later amended to placement + disclosed inertness) is superseded by this final disposition.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (Hardening backlog item 5)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/town/buildings.py`
- `data/content/world_modules/`

## Assumptions / Open Questions
- Which world module is the best fit for CHURCH content is not decided here — real content-design
  work for this ticket's own Investigate/Plan phases.

## Implementation Notes

**BLOCKED, 2026-09-07 — investigation only, no implementation performed.** This ticket's own
premise ("services already exist and are correct; this ticket only places the building where it
can actually be used") is factually wrong, discovered during Investigate before any content was
authored:

- `BuildingRegistry._templates[CHURCH]["services"] = ["BLESSING", "RESURRECTION"]`
  (`src/town/buildings.py:23`) is real as a **data label** — the string names exist in the
  template dict.
- But unlike every sibling service (`REST`→`src/engine/town_resolution.py:100-106`,
  `CRAFT`→`src/engine/blacksmith.py:225`/`src/town/blacksmith.py:56`, `TRADE`→
  `src/engine/domain/action_router.py:52`, `QUEST`→`src/engine/quests.py:209` +
  `src/systems/social_systems/reward_distribution.py:113`, `INTEL`→`src/engine/town_resolution.py:100`),
  `BLESSING` and `RESURRECTION` have **zero occurrences anywhere else in `src/`**
  (confirmed via `grep -rni "blessing\|resurrection" src/ --include="*.py"` — zero hits outside
  `buildings.py`'s own template dict; also confirmed `BuildingRegistry.get_services()` itself has
  zero call sites in `src/`, only in tests). There is no engine phase, action router branch, or
  intent handler that ever reads or acts on these two service names.
- Consequence: placing `CHURCH` into a world module would make the building spawn, but its
  "services" would remain permanently inert — no entity could ever receive a blessing or a
  resurrection effect through any real code path. Acceptance Criterion 2 ("Blessing/Resurrection
  services confirmed functional... via a real test or calibration run") is **unsatisfiable as
  currently scoped** — there is no functionality to confirm.
- This ticket's own Out of Scope explicitly forbids "building any new CHURCH mechanic" on the
  premise that none is needed. That premise is wrong: real service-handling logic (an engine phase
  or action-router branch analogous to `REST`'s) does not exist and would need to be built for the
  AC to ever be true — a materially different, larger scope than "pure content authoring."

**Real decision needed (not this implementer's to make unilaterally):**
1. Re-scope this ticket to include building real BLESSING/RESURRECTION service-handling logic
   (comparable in shape to `REST`'s handling in `town_resolution.py`) alongside the content
   placement — genuinely larger than P3 "pure content" as currently framed.
2. Place `CHURCH` in a world module anyway, but change AC 2 to "confirmed placed, service
   inertness formally disclosed" (an `intentional_divergences.md` / roadmap-doc entry, not a
   fix) — matching the `docs/world/fame_legend_contract.md` "No Live Consumer Yet" precedent this
   same epic already used for a different mechanism.
3. Leave both content and code untouched pending a product decision on whether Blessing/
   Resurrection are still wanted mechanics at all.

No files changed except this ticket's own investigation notes. Not moved to `tickets/done/` — left
in `tickets/inprogress/` (also still present at
`tickets/todos/dormant-mechanism-closure/TCK-20260907-CHURCH-CONTENT-AUTHORING.md`, untouched) pending
the orchestrator/user's decision among the 3 options above.

### Decision, 2026-09-07 (real user decision, via `AskUserQuestion`, orchestrator-initiated)
**Option 2 — place CHURCH in a world module, formally disclose Blessing/Resurrection as inert.**
Do not build real service-handling logic (disproportionate for a P3 backlog item). AC2 is amended
to "placement confirmed, service inertness formally disclosed" rather than "services confirmed
functional." Disclose in `docs/guidelines/intentional_divergences.md`, matching the
`docs/world/fame_legend_contract.md` "No Live Consumer Yet" precedent.

Implemented as decided: added a `church` catalog entry (no `service_profile_id`), placed it in
`frontier_village_core`, verified via a real resolve/validate/100-tick-calibration run against
`sandbox_world` (`church_0` confirmed present, no `CHURCH`-specific event ever fired, confirming
inertness rather than silent malfunction). Disclosed in `docs/guidelines/intentional_divergences.md`
§2.54.

### Decision reversed, 2026-09-07 (2nd revision, real user decision after independent review)
An independent review (`rpg-feature-planning` session, explicitly requested to scrutinize this
decision, not rubber-stamp it) argued the "No Live Consumer Yet" precedent didn't actually fit:
that precedent's cases have a live, correct *derivation* with only the *consumption* pending —
here, placing `CHURCH` produced literally zero observable effect from any perspective (the
original calibration run's own evidence: no `CHURCH`-specific event ever fired). Idea 30
(`TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION`) faced the structurally identical "neither producer
nor consumer" gap and was deferred outright, not half-built — the reviewer argued CHURCH deserved
the same consistent treatment, not the fame_legend precedent's treatment.

**Reverted**: `CHURCH` removed from `data/content/world/buildings.yaml` and
`data/content/world_modules/frontier_village_core.yaml` (both restored to their pre-ticket state);
`sandbox_world` recompiled to confirm `church_0` no longer appears. `docs/guidelines/
intentional_divergences.md` §2.54 rewritten to record both decisions (place-and-disclose, then
reverted-to-deferred) rather than silently erasing the first one. **Final disposition: deferred**,
same treatment as idea 30 — `BLESSING`/`RESURRECTION` remain unplaced pending either a future
decision to build real service-handling logic, or a decision that they're not needed at all.

## Test Summary
Original placement verification (now reverted, kept here for the record): `python3 -m
src.worldbuilding.cli resolve sandbox_world`/`... validate sandbox_world` both succeeded,
`church_0` confirmed present, `tools/calibrate_simq.py --name sandbox_world --seed 42 --ticks 100`
ran cleanly with no `CHURCH`-specific event ever emitted. Post-revert verification: same
resolve/validate run against `sandbox_world` confirms `church_0` no longer present, only the 3
pre-existing unrelated `WORLD-UNEXPECTED-SECTION` warnings remain. No `src/` code was ever changed
by either revision of this ticket.

## Files Changed
- `data/content/world/buildings.yaml` (church catalog entry added, then reverted)
- `data/content/world_modules/frontier_village_core.yaml` (`church: 1` added, then reverted)
- `data/worlds/sandbox_world/resolved/` (recompiled twice — once with CHURCH placed, once without)
- `docs/guidelines/intentional_divergences.md` (§2.54 written, then rewritten to record both
  decisions)
- `tickets/done/TCK-20260907-CHURCH-CONTENT-AUTHORING.md` (this ticket)

## Completion Summary
Investigation found the ticket's own premise was wrong: `BLESSING`/`RESURRECTION` are data-label
strings with zero real code reading them anywhere in `src/`, unlike every sibling building service.
Escalated rather than silently building new service logic or silently placing the building with a
misleading "functional" claim. First ratified decision (2026-09-07): place `CHURCH` and formally
disclose the inertness. That decision was reversed the same day after an independent review argued
the precedent it relied on didn't actually fit, and that idea 30's "fully deferred" treatment was
the more consistent outcome for the same shape of gap. **Final state: `CHURCH` is not placed in any
world module — deferred, same as idea 30.**
