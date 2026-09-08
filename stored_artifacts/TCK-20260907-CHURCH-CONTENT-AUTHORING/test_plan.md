---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260907-CHURCH-CONTENT-AUTHORING
artifact_type: test_plan
---

# Test Plan — TCK-20260907-CHURCH-CONTENT-AUTHORING

## Regression Surface
No `src/` code changed — regression surface is limited to world-content compilation/validation for
any world composing `frontier_village_core`. `sandbox_world` (one real consumer) is recompiled and
validated as the regression check; other consumer worlds' `resolved/` snapshots are unaffected
until their own next recompile (normal content-versioning behavior, not introduced by this ticket).

## New Tests Required
None — pure content-catalog + world-module data addition with deliberately no behavior wired to
it. No new unit test is meaningful to add since there is nothing new to unit-test (the whole point
of the disclosure is that nothing reads the new services).

## Scoped Commands
- `python3 -m src.worldbuilding.cli resolve sandbox_world`
- `python3 -m src.worldbuilding.cli validate sandbox_world`
- `python3 tools/calibrate_simq.py --name sandbox_world --seed 42 --ticks 100`

## Anti-Drift Test Guards
- The calibration run must show zero CHURCH-specific events — a nonzero count would mean the
  inertness disclosure is factually wrong and must be corrected before closing the ticket.
- `resolve`/`validate` must not introduce any NEW warning/error class beyond the 3 pre-existing
  `WORLD-UNEXPECTED-SECTION` warnings already present for every world sharing this profile shape.
