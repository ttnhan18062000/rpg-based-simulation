---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260907-CHURCH-CONTENT-AUTHORING
artifact_type: investigation
---

# Investigation — TCK-20260907-CHURCH-CONTENT-AUTHORING

## Current Behavior (file:line refs)

- `BuildingRegistry._templates[CHURCH]["services"] = ["BLESSING", "RESURRECTION"]`
  (`src/town/buildings.py:15,23`) — a real data-label entry, but with zero real (non-test) callers
  of `BuildingRegistry.get_services()` anywhere in `src/`, and zero occurrences of the strings
  `BLESSING`/`RESURRECTION` anywhere outside this one dict (`grep -rni "blessing\|resurrection"
  src/ --include="*.py"`).
- Every sibling service string in the same dict IS live: `REST`→`src/engine/town_resolution.py:
  100-106`, `CRAFT`→`src/engine/blacksmith.py:225`/`src/town/blacksmith.py:56`, `TRADE`→`src/
  engine/domain/action_router.py:52`, `QUEST`→`src/engine/quests.py:209`, `INTEL`→`src/engine/
  town_resolution.py:100`.
- `BuildingRegistry` is itself disconnected from the real building-creation runtime path:
  `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`, step 5, ~line 425-449) sets
  `BuildingState.kind = bld_spec.type` directly from the world module's own lowercase `buildings:`
  count-map key, resolved against `data/content/world/buildings.yaml` via
  `src/content/resolver.py::BuildingResolver` — never touching `BuildingRegistry` at all. Runtime
  service dispatch (`town_resolution.py:100-106`) compares `building_type` against lowercase
  literal strings (`"inn"`, `"home"`), not `BuildingRegistry`'s uppercase constants.
- `data/content/world/buildings.yaml` (the real content catalog `WorldCompiler` reads through) had
  no `church` entry at all before this ticket — placement was impossible without adding one.

## Mechanics/Engine Constraints
None specific to Church — `docs/simulation/town_contract.md` "Building System" section documents
`BuildingRegistry`'s static-template shape but does not assert a runtime consumer exists for every
listed service; no Mechanics Bible chapter references Blessing/Resurrection.

## Docs Requiring Update
- `docs/guidelines/intentional_divergences.md`: new disclosure entry for the confirmed-inert
  BLESSING/RESURRECTION labels, matching the existing "No Live Consumer Yet" precedent shape.

## Parity Ledger Overlap
None — no `src/` behavior change; pure content-catalog + world-module data addition. Parity-updater
is skip-eligible per `implement-ticket.js`'s own rule (no `src/` path touched, `behavior_changed`
false).

## Prior Work
- `docs/mechanics/05_world_evolution.md` "No Live Consumer Yet" sections (Chronicle Fidelity Drift,
  Living Legend Perception) — the precedent shape this ticket's disclosure follows.
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (§2.53) — the immediately-prior sibling ticket
  in this epic that used the same "confirm dead, disclose, don't silently revive or hide" pattern.

## Risks and Open Questions
None open — the real user decision (place + disclose, Option 2) was ratified before this
implementation proceeded; see the ticket's own "Decision, 2026-09-07" section.

## Anti-Drift Hazards
- Do not add a `service_profile_id` to the new `church` catalog entry — that would misleadingly
  imply the services are wired to something real when they are not.
- Do not add any BLESSING/RESURRECTION-reading logic to any engine phase as part of this ticket —
  that was explicitly ruled out by the ratified decision (Option 1, larger scope, rejected).
