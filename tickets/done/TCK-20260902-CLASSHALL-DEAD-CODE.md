---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-CLASSHALL-DEAD-CODE
phase: done
date: 2026-09-02
tags: [world]
---

# TCK-20260902-CLASSHALL-DEAD-CODE

## Title
Delete Orphaned `ClassHallAction.train()` Duplicate (src/town/class_hall.py)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`src/town/class_hall.py`'s `ClassHallAction.train()` is a confirmed-dead, unwired duplicate
of the "train a skill" mechanic. `TCK-20260831-TRUST-GATED-TEACHING` (done) rewrote the real,
live implementation as `CoreActions.execute_train()` — a two-party, trust-gated action routed
through `ActionRouter`'s `TRAIN` branch — and explicitly deferred reconciling the old
gold-only `ClassHallAction.train()` duplicate as "a separate, future architectural cleanup"
(see `docs/guidelines/intentional_divergences.md` DEV-007). This ticket is that follow-up:
delete the dead class and its dedicated test coverage, and close out the DEV-007 note.

Fresh full-repo grep (2026-09-02) confirms `ClassHallAction` has zero importers/callers
anywhere in `src/` — the only references are `src/town/class_hall.py` itself (definition) and
`tests/unit/world/test_recovery_class_hall.py` (its dedicated test). `src/town/class_hall.py`
contains nothing else (44 lines: one class, one static method, no other exports), so the whole
file can be deleted rather than surgically edited.

## Scope
- Delete `src/town/class_hall.py` in its entirety (contains only the dead `ClassHallAction`
  class — confirmed via full-file read, no other code present).
- In `tests/unit/world/test_recovery_class_hall.py`: remove `test_class_hall_training()` (the
  only test exercising `ClassHallAction.train()`) and the now-unused
  `from src.town.class_hall import ClassHallAction` import line. Leave
  `test_class_hall_inn_rest_recovery()` and `test_home_upgrade_blocker()` — and their
  `InnAction`/`HomeAction` imports — untouched; they test unrelated live-or-not-yet-investigated
  code in the same shared test file and are out of scope here.
- Update `docs/guidelines/intentional_divergences.md` DEV-007's "Decision" paragraph (or add a
  short dated addendum) to note that the deferred `ClassHallAction.train()` cleanup it flagged
  has now landed under this ticket ID, so a future reader doesn't treat it as still-outstanding.
- Re-verify zero-callers at implementation time (grep across all of `src/`, and beyond if
  warranted per the original request's step 3 — `tools/`, `frontend/`) before deleting, since
  this is a shared multi-session repo and time has passed since this scoping pass.

## Out of Scope
- `CoreActions.execute_train()` (`src/engine/domain/core_actions.py`) and `ActionRouter`'s
  `TRAIN` dispatch branch (`src/engine/domain/action_router.py`) — these are the already-correct
  live implementation; do not touch.
- Any other file in `src/town/` (`blacksmith.py`, `guild.py`, `home.py`, `home_storage.py`,
  `inn.py`, `shop.py`, `town_navigation.py`, `buildings.py`) or `src/quests/`. `docs/audits/D11_dead_code.md`
  Finding F2 flagged the whole `src/town/` directory as a possible orphan cluster, but a later
  correction (`TCK-20260623-DEAD-CODE-REMOVAL`) blanket-marked all 9 originally-flagged
  directories "CONFIRMED INVALID" (live importers). That correction's own cited evidence only
  covers `src/ai/`, `src/quests/`, `src/progression/`, `src/content_semantics/` — it does not
  specifically evidence `src/town/`. This ticket does not re-investigate or resolve that
  standing inconsistency for any file besides `class_hall.py`; other `src/town/` files' live/dead
  status stays unresolved.
- `test_class_hall_inn_rest_recovery()` and `test_home_upgrade_blocker()` in the shared test
  file — preserved as-is.
- `docs/parity_ledger/town_resource.yaml` entry `TOWN-027` (`test_visit_class_hall_resolution`)
  — current evidence shows its `test_path` is `null` and its `v2_evidence` cites the general
  "exhaustive checklist audit," not `ClassHallAction` specifically, so no update is expected;
  only touch it if implementation turns up a direct citation this scoping pass missed.
- Frontend `class_hall` references (`frontend/src/components/BuildingPanel.tsx`,
  `GameCanvas.tsx`, `useCanvas.ts`) — these use `"class_hall"` as a `building_type` string / UI
  label for the town building concept, unrelated to the Python `ClassHallAction` class. Not
  touched.

## Acceptance Criteria
- [x] `src/town/class_hall.py` no longer exists in the repository.
- [x] `grep -rn "ClassHallAction" --include="*.py" .` returns zero matches anywhere in the repo.
- [x] `test_class_hall_training()` and the `ClassHallAction` import are removed from
      `tests/unit/world/test_recovery_class_hall.py`; the file still contains
      `test_class_hall_inn_rest_recovery()` and `test_home_upgrade_blocker()` unmodified.
- [x] `pytest tests/unit/world/test_recovery_class_hall.py -v` passes with exactly 2 tests
      collected and passing (down from 3).
- [x] `docs/guidelines/intentional_divergences.md` DEV-007 reflects that the deferred cleanup
      has landed, referencing this ticket ID.
- [x] No changes made to `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`,
      or any other `src/town/*.py` file besides `class_hall.py`.

## Related Tickets
- `TCK-20260831-TRUST-GATED-TEACHING` (done) — rewrote the live `execute_train()` and explicitly
  flagged `ClassHallAction.train()` as a future cleanup candidate (DEV-007).
- `TCK-20260618-AUDIT-D11-DEAD` (done) — original D11 dead-code audit; Finding F2 flagged
  `src/town/` (including `class_hall.py`) as a possible orphan cluster.
- `TCK-20260623-DEAD-CODE-REMOVAL` (done) — later blanket-marked all 9 D11-flagged directories
  "CONFIRMED INVALID," but its own cited evidence does not specifically cover `src/town/`; see
  Out of Scope above.

## Related Docs
- `docs/guidelines/intentional_divergences.md` (DEV-007 — the entry that deferred this cleanup)
- `docs/audits/D11_dead_code.md` (Finding F2, and its "Post-Audit Correction" boilerplate note)
- `docs/parity_ledger/town_resource.yaml` (TOWN-027, informational only — see Out of Scope)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-TRUST-GATED-TEACHING/investigation.md`,
  `plan.md`, `test_plan.md` — original investigation that confirmed `ClassHallAction.train()`'s
  zero-caller status and deferred its removal.

## Related Code Areas
- `src/town/class_hall.py` (delete)
- `tests/unit/world/test_recovery_class_hall.py` (surgical edit — remove one test + one import)
- `src/engine/domain/core_actions.py` (`execute_train()` — reference only, not touched)
- `src/engine/domain/action_router.py` (`TRAIN` dispatch — reference only, not touched)

## Assumptions / Open Questions
- Assumes `ClassHallAction`'s zero-caller status (confirmed by this scoping pass's full-repo
  grep on 2026-09-02) still holds at implementation time. Re-verify before deleting — this repo
  is shared across concurrent sessions per project convention.
- The D11 audit's 2026-06-23 correction note claims all 9 originally-flagged directories
  (including `src/town/`, F2) have "confirmed live importers," which appears to conflict with
  this ticket's own specific, evidenced finding for `ClassHallAction`. This scoping pass treats
  the more specific, more recent, directly-verified finding (zero callers, confirmed independently
  by both `TCK-20260831-TRUST-GATED-TEACHING`'s investigation and this ticket's own grep) as
  authoritative for `ClassHallAction` specifically, without resolving the broader inconsistency
  for the rest of `src/town/`. If this assumption is wrong (some non-obvious import surfaces
  during implementation), the deletion should be aborted and the ticket re-scoped.
- `layer: world` is used per the requesting instruction's explicit template; the `world` layer's
  own registered note ("World generation, worldbuilding, region/biome content") is a loose fit
  for a town-building-interaction dead-code cleanup — `economy` or `systems` may describe the
  subsystem more precisely. Not changed here since it was explicitly specified; flagged for
  awareness.
- Tier is set to `hotfix` (self-evident, single confirmed-dead class + one test function +
  one doc note, all evidence already gathered during this scoping pass) rather than `standard`;
  no staging artifacts are created per the hotfix tier's rules.

## Implementation Notes
- Re-verified zero-caller status before deleting: `grep -rn "ClassHallAction" --include="*.py" src/ tests/ tools/` and a full-repo pass both returned only the definition (`src/town/class_hall.py`) and the one dedicated test import (`tests/unit/world/test_recovery_class_hall.py`). A secondary `grep -rln "class_hall"` also surfaced
  `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor`; read it in full and confirmed it does not import or reference `ClassHallAction` at all — it exercises the live `TRAIN` action through `SimulationDomainLogic.execute_action`/`ActionRouter` (the DEV-007 rewrite), and its name is only a naming leftover from the migration. Left untouched, as it's out of scope and not dead code.
- Deleted `src/town/class_hall.py` in its entirety (confirmed 44 lines, single `ClassHallAction` class, no other exports).
- Removed `test_class_hall_training()` and its `from src.town.class_hall import ClassHallAction` import line from `tests/unit/world/test_recovery_class_hall.py`. `test_class_hall_inn_rest_recovery()` and `test_home_upgrade_blocker()` (and their `InnAction`/`HomeAction` imports) are untouched.
- Appended a dated addendum to DEV-007's Decision paragraph in `docs/guidelines/intentional_divergences.md` noting the deferred cleanup landed under this ticket ID, and updated the file's "Last updated" footer line. The rest of the DEV-007 entry (Situation/Rationale/Verification/Status) was left unmodified.
- Checked `docs/parity_ledger/town_resource.yaml`'s `TOWN-027` entry directly: `v2_evidence` cites the general "exhaustive checklist audit," `test_path` is `null`, and the entry's `text` describes the live "learning a skill emits a strategic resolution" behavior, not `ClassHallAction` specifically. Confirmed no update needed, per Out of Scope.
- No changes made to `CoreActions.execute_train()`, `ActionRouter`, or any other file under `src/town/`.

## Test Summary
- `.venv/bin/python3 -m pytest tests/unit/world/ -v` — 261 passed (full directory, not cherry-picked).
- `.venv/bin/python3 -m pytest tests/unit/world/test_recovery_class_hall.py -v` — exactly 2 tests collected and passing (`test_class_hall_inn_rest_recovery`, `test_home_upgrade_blocker`), down from 3 as required by AC.
- `.venv/bin/python3 -m pytest tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor -v` — 1 passed (unrelated live-code regression test, confirmed untouched and still green).
- Final grep re-confirmation: `grep -rn "ClassHallAction" --include="*.py" .` — zero matches repo-wide.

## Files Changed
- `src/town/class_hall.py` (deleted)
- `tests/unit/world/test_recovery_class_hall.py` (edited — removed `test_class_hall_training()` and its `ClassHallAction` import)
- `docs/guidelines/intentional_divergences.md` (edited — DEV-007 addendum + footer date)
- `tickets/inprogress/TCK-20260902-CLASSHALL-DEAD-CODE.md` (this ticket — implementation notes/test summary/files changed/completion summary/status/AC checkboxes)

## Completion Summary
Deleted the confirmed-dead, zero-caller `ClassHallAction` class (`src/town/class_hall.py`) and its dedicated test (`test_class_hall_training()` in `tests/unit/world/test_recovery_class_hall.py`), re-verifying zero callers across `src/`, `tests/`, and `tools/` immediately before deletion (one incidental `class_hall`-named test, `test_class_hall_train_refactor`, was inspected and confirmed to test the live `TRAIN` action, not the dead class, so it was left alone). Added a dated addendum to DEV-007 in `docs/guidelines/intentional_divergences.md` confirming the deferred cleanup it flagged has now landed under this ticket ID. `docs/parity_ledger/town_resource.yaml`'s `TOWN-027` was checked and confirmed to need no change. `tests/unit/world/` (261 tests) and the unrelated boundary regression test both pass; no reachable behavior changed.
