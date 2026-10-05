---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING

- `tests/unit/world/test_world_boss_spawn_flag.py`: flag registered default OFF; only an explicit `ON` enables; each of the three branches inert when OFF and unchanged when ON; the calamity trigger still advances; `resolve_dynamics` spawns no boss of any branch when OFF.
- `tests/unit/core/test_violent_cause.py`: `KILL`/`DEFEAT` violent; `HAZARD`, `SURVIVE`, `REJECTED`, passive causes and `None` not; the set derives from the terminal combat outcomes; building destruction violent only with a damaging delta.
- `tests/unit/engine/test_trauma_counts_violent_cause_only.py`: the real death block credits a `DEFEAT`/`KILL` and not a `HAZARD` death; the rule is the cause, not the attacker id (a `HAZARD` death carrying an attacker id adds nothing, a `DEFEAT` without one adds 1.0); a sabotaged building destruction adds 2.0, one without a damaging delta adds nothing.
- Seven existing tests that asserted a boss spawn set the flag ON, and the boss tests that previously passed vacuously with the flag OFF were given it too.
- Corpus before/after under `audit_mode`: `investigation.md` section 8.
- Full CI lane set run on the final tree.

## Proof Plan
- level: unit plus corpus measurement
- proof kind: behavioural tests that fail without the change; paired before/after runs under `audit_mode`
- oracle source: owner decisions 14 and 15; Mechanics Bible 05
- expected effect: no boss of any branch spawns by default; trauma counts only violent causes
- selected commands: `pytest tests/unit/world/test_world_boss_spawn_flag.py tests/unit/core/test_violent_cause.py tests/unit/engine/test_trauma_counts_violent_cause_only.py`; the CI lane set
