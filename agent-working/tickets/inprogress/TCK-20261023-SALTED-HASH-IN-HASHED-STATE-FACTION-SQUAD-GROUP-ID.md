---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
phase: inprogress
date: 2026-10-23
tags: []
---

# TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID

## Title
Faction squad group_id uses Python's salted hash() of a str region id, so the state hash depends on PYTHONHASHSEED (#593 F4)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
#593 F4 (verified on main by rpg-planner 2026-10-22). `src/engine/military_conflict.py:339`: `group_id = abs(hash((contested_region_id, attacker_id, state.tick))) % (2 ** 31)`; `contested_region_id` is `Optional[str]` (str region ids, state.py:1348), so the tuple hash is salted per process. `groups` is in CanonicalStateHasher, so two processes with different PYTHONHASHSEED get different state hashes once a faction squad forms. Only the measurement tools pin PYTHONHASHSEED; compose, the Makefile and live/API runs do not. Same pattern at `src/domains/perception/filter.py:88,97` (`hash(signal.signal_id)` for a str id; whether it reaches hashed state is unverified).

## Scope
1. Replace with a stable digest (e.g. blake2b of the tuple) or an allocator-issued id; same for perception/filter.py:88,97 if it reaches state.
2. PROBE A0 first: does any shipped world (unit_faction_tension W5, urban_political W2) form a FACTION_SQUAD within its tick count? If none, add a small purpose-built world following the `data/worlds/mechanic_scenario_*` pattern (e.g. mechanic_scenario_faction_attack), declared as a test scenario, not a gate/benchmark world.
3. Cross-PYTHONHASHSEED test: two processes (hashseed 0 and 1) on that world give equal final hashes and equal squad ids.

## Out of Scope
Other salted-hash sites not reaching state (list them in investigation).

## Acceptance Criteria
- Squad `group_id` and `CanonicalStateHasher` hash equal across PYTHONHASHSEED=0 and =1 on a constructed state where a faction squad forms. **Amended 2026-10-26 by rpg-planner (ticket owner):** the original read "on a world where a faction squad forms"; probe A0 found no shipped world that forms one (no WAR pair in 5000 ticks on four worlds), so the proof is a constructed WAR state, not a new world.
- perception/filter.py:88,97 resolved or shown not to reach hashed state.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/engine/military_conflict.py; src/domains/perception/filter.py; data/worlds/

## Assumptions / Open Questions
Changes squad ids, so a world-changing hash difference is expected on any run where a squad forms; needs a paired step and a gate check (V-rows unchanged). Probe A0 answered on #593 6347182683 (not yet run).

## Implementation Notes
Moved from Lane C to Lane B (`rpg-implementer-2`) by `rpg-planner` 2026-10-26; branch `rpg-salted-group-id`, worktree `.claude/worktrees/f4`. The ticket was only on the planner seat branch; copied here.

### Phase 1 findings (2026-10-26)
**PROBE A0 (answered): no shipped gate or unit world forms a FACTION_SQUAD.** `probe_a0.py` (scratch `/mnt/data/scratch-rpg-implementer-2/f4/`) ran `build_kernel(world, 42)` for 5000 ticks under `PYTHONHASHSEED=0` and looked each tick for a WAR pair (`MilitaryConflictPhase.get_war_pairs`) and for a group with the `FACTION_SQUAD` role: `urban_political`, `unit_faction_tension`, `crowded_frontier`, `frontier_living_world` all show **no WAR pair and no squad in 5000 ticks** (final hashes 4c912b13..., f8fdeb88..., 5d840881..., 6d5b6a88...). So replacing the salted hash changes **no** gate-world hash and no trajectory in these worlds; the fix is not observable on a shipped world, and the cross-seed test needs a constructed case.
**Where the value goes:** `group_id` keys `state.groups`; `CanonicalStateHasher` hashes `groups` sorted by id (`checkpoint.py:126`) and `StateFingerprinter` sorts by id (`replay/fingerprint.py:259`). **Ordering by group_id exists**: `systems/world_systems/groups.py:74` (`sorted(relevant_groups)`) and `:366` (`sorted(state.groups.items())`), `engine/pipeline_phases/groups.py:70`, `core/dirty.py:47`. A different id value can therefore change update order between a squad group and other groups, but only in a run where a squad forms.
**perception/filter.py:88,97 does not reach hashed state in production:** `PerceptionFilterService.filter` is only called by `PerceptionPhase.process_entities` (`domains/perception/phase.py`), and nothing under `src/` references `PerceptionPhase` or builds `WorldSignal`s for it except the `LegendFact` wrapper in `fame/legend.py` (tests only otherwise). `PerceptionModel.to_canonical_dict` does hash `perceived_entities` keyed by `ent_id`, so if the phase were wired, `ent_id = hash(signal.signal_id)` for a non-int id (line 88) would reach hashed state; line 97 (`node_id=hash(...)`) is not in the canonical dict (only the str key and salience are). Latent, not live. Proposed: fix both with the same stable digest helper (cheap, no live effect).
**Other salted `hash()` calls under `src/`:** only these three (`grep -rn "\bhash(" src`); none else.
**Proposed test (no new world):** the squad needs a WAR pair, contested region, and at least one GUARD entity; the diplomatic state machine reaches WAR only through tension, which no shipped world does within 5000 ticks. Build the state directly (factions at WAR, a region, 3 guards), run `MilitaryConflictPhase.execute` in two subprocesses with `PYTHONHASHSEED=0` and `=1`, and compare the squad `group_id` and `CanonicalStateHasher` after applying the update. A purpose-built `mechanic_scenario_*` world is the alternative if the owner wants an end-to-end world.
**Planner ruling (2026-10-26):** plan approved as written; constructed-state subprocess test is the proof; because A0 is negative F4 is hash-neutral on the gate worlds and needs no paired step of its own, `paired --neutral` IDENTICAL is the proof and it can land whenever ready; filter.py:88 is recorded as a latent hazard (it would hash if PerceptionPhase were wired).
**Next (superseded by the ruling):** plan.md to `rpg-planner`, then code (stable digest, e.g. blake2b of the tuple modulo 2**31, one shared helper), then the cross-seed test; the paired step against the parent after step A (section 12.5 order) is a no-op on the gate worlds by A0.

## Test Summary

## Files Changed

## Completion Summary
