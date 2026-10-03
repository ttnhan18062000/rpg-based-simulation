---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER
artifact_type: investigation
tags: [investigation, root-cause, corpus, world]
---

# Investigation — TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER

Three classification checks against the epic's verdict axis; no `src/` change. Full evidence is in each covered
ticket's own Implementation Notes (epic Deliverable 2) — summarised here, not duplicated. Environment: branch tip
`3dbdff48a`; `search_docs` and `graphify` both live in this worktree. The fourth ticket in the epic's
zero-caller group (`CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`) is cited, not classified — `T04` owns it.

## 1. `CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` — fifth outcome `NO-MECHANISM` (AC-7)
`grep -rn CALAMITY_RANDOM_CHANCE src tests tools data` -> one hit, the declaration (`calamity.py:19`); no
dynamic access; `git log -S` -> single introducing commit `562116889` (2026-05-18), so declared-and-never-connected,
not wired-then-orphaned. Docs already call it dead code. A constant with no consumer is not an unreachable
mechanism, so none of the four verdicts describes it; the adjacent spawn gate runs deterministically as designed.

## 2. `REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` — `UNDECLARED`
Zero callers of the class, `process_taxation` or `apply_sovereignty_debuffs` in `src/`, `tests/`, `tools/`
(confirmed). But a live second implementation exists: `TownResolutionSystem.resolve()` (`pipeline.py:339`)
taxes non-owner entities `2.0` and functional buildings `10.0` on a `2 x cadence.town_resolution` cadence and applies
a `-20%/-10%` penalty under `suppression_active`. The orphan's constants match on taxation but its cadence (fixed
100), trigger and debuff (`0.8/0.9`, MONSTER_HORDE only, and a no-op update) differ. The runtime contract names the
dead one as the taxation source and cites a regression test with no tax assertion. Nothing declares which is
authoritative.

## 3. `PROFILE-API-PAYLOAD-DEAD-API-REFS` — `DEFECT`
Executed: `ImportError: cannot import name 'EngineManager'` at `profile_api_payload.py:26`. `SimulationConfig`
(`:45`) is not defined anywhere in `src/`. `make profile-api` runs this file. Straight wiring defect.

## Not done
The epic's shared classification document (Deliverable 1) is deferred to `T06`. No doc/registry correction was
made for the findings above (the runtime contract's wrong taxation source; the constant's naming).
