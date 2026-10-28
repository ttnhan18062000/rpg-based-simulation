---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
phase: done
date: 2026-10-23
tags: []
---

# TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID

## Title
Faction squad group_id uses Python's salted hash() of a str region id, so the state hash depends on PYTHONHASHSEED (#593 F4)

## Status
DONE

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
(superseded) **LANDING HOLD (planner correction 2026-10-26):** the landing slot is set by the owner-approved section 12.5 order (step B, step A, F4, D73). Code F4 and run the neutral proof as planned, but HOLD the PR until after step A, unless the owner rules to move it earlier (rpg-planner is asking).
(now conditional, see next paragraph) **LANDING HOLD LIFTED (owner ruling, #715 issuecomment-6412087297, memo row 90, relayed by rpg-planner):** F4 lands as soon as it is ready. Opening the PR still needs the user's own yes.
**PR body requirement (lead-planner-u24):** the gate-world `--neutral` IDENTICAL only shows those worlds do not exercise F4; it is NOT behaviour coverage, and the PR body must say so in those words. The behaviour evidence is the constructed-WAR-state test, where a squad actually forms: it must check the F4 path (stable_int31 used for group_id) and run twice per hashseed, so it is also deterministic within a seed.
**OWNER RULING NOW CONDITIONAL (#715 6412199242, memo row 90 reworded; relayed by rpg-planner):** probe A0 was seed 42 only and `--neutral` is 3 worlds x seed 42 x 1000t, so neither covers the gate seeds 42-46. REQUIRED before any early landing: extend probe A0 to crowded_frontier, frontier_living_world, urban_political x seeds 43-46 x 5000t, checking every tick for a WAR pair or a FACTION_SQUAD group (probe: `/mnt/data/scratch-rpg-implementer-2/f4/probe_a0.py world seed ticks out.json`, PYTHONHASHSEED=0, from the f4 worktree; needs a host slot from rpg-planner, one process at a time). If none forms anywhere: F4 lands when ready with the neutral proof plus the constructed-state test. If any (world, seed) forms a squad: F4 waits until after step A and takes its own paired step against its parent. The PR body states exactly what was measured (worlds, seeds, ticks, hashseed), never "no world forms a squad".
**Next (superseded by the ruling):** plan.md to `rpg-planner`, then code (stable digest, e.g. blake2b of the tuple modulo 2**31, one shared helper), then the cross-seed test; the paired step against the parent after step A (section 12.5 order) is a no-op on the gate worlds by A0.

### Coded 2026-10-27 (commit a08d4aef3)
New `src/core/stable_hash.py::stable_int31(*parts)`: blake2b (digest_size 8) over a type-tagged, length-prefixed encoding of str/int parts, mod 2**31; any other part type raises TypeError. Used at `military_conflict.py:340` (`stable_int31(contested_region_id, attacker_id, state.tick)`) and `perception/filter.py:88,97`. No other salted `hash()` call is left in `src/`.
**OWNER STOP (#715 6426468523, 6431749368, relayed by lead-planner-u24 and rpg-planner 2026-10-27):** finish F4 through push/PR/finalize, then stop. Probe A0 for seeds 43-46 and `paired --neutral` are heavy runs and both are still landing conditions (#715 6412199242). Neither has run. **F4 is held before push** until the owner says continue to those runs or drops the condition. Asked rpg-planner whether a parity-ledger entry and an intentional_divergences.md record are wanted.

## Test Summary
- `tests/unit/core/test_stable_hash.py`: the value is repeatable, in range and pinned; distinct tuples differ (order, concatenation, str vs int); bad part types are rejected.
- `tests/unit/domains/faction/test_squad_group_id_hashseed.py`: a real `AuthoritativeState` (fa/fb at WAR, r2 held by fb, 3 GUARDs) runs `MilitaryConflictPhase.execute` + `ApplyPath.apply_generation` in 2 subprocesses per PYTHONHASHSEED (0, 1). A squad forms; group_id == stable_int31; group_id and `CanonicalStateHasher.get_hash` are equal across all 4 runs. Sensitivity check: the old salted formula differs across hash seeds 0 and 1.
- `tests/unit/domains/perception/test_filter_ids_hashseed.py`: filter entity_id and node_id for non-int signal ids are equal across hash seeds 0 and 1.
- Scoped run (core stable_hash, domains/faction, domains/perception, social groups + lifecycle, integration faction_campaign): 214 passed. Mypy baseline filter: no new errors. Code health: 0 new, 0 worse.
- Probe A0, run 2026-10-27 after the owner's continue (#715 6437025815) on rpg-planner's host slot. Setup: F4 tip `5f6783fde`, PYTHONHASHSEED=0, crowded_frontier, frontier_living_world and urban_political x seeds 43-46 x 5000 ticks, every tick checked. Result: 0 of 12 runs had a WAR pair and 0 of 12 formed a FACTION_SQUAD. Groups alive at the end, seeds 43/44/45/46: crowded 20/18/35/12, frontier 15/12/15/55, urban 44/58/6/72 (parties, none with the squad role). The first launch failed on import (missing PYTHONPATH) in under a second and ran nothing; it was fixed and all 12 runs re-ran.
- `paired --neutral` (base `83c10685f`, new `5f6783fde`, 3 gate worlds x seed 42 x 1000 ticks, `--jobs 1`): IDENTICAL on all three, verdict PASS. That only shows those worlds do not exercise F4; it is NOT behaviour coverage.

## Files Changed
- `src/core/stable_hash.py` (new)
- `src/engine/military_conflict.py`
- `src/domains/perception/filter.py`
- `tests/unit/core/test_stable_hash.py` (new)
- `tests/unit/domains/faction/test_squad_group_id_hashseed.py` (new)
- `tests/unit/domains/perception/test_filter_ids_hashseed.py` (new)
- `docs/parity_ledger/substrate.yaml` (SUB-398, SUB-399)
- `docs/guidelines/intentional_divergences.md` (2.141)

## Completion Summary
Both acceptance criteria are met by tests. (1) On a constructed WAR state where a squad forms, the squad `group_id` and the `CanonicalStateHasher` hash are equal across PYTHONHASHSEED 0 and 1, two processes each (`tests/unit/domains/faction/test_squad_group_id_hashseed.py`). (2) `perception/filter.py:88,97` is resolved with the same helper and shown equal across hash seeds; it is not wired into production state, so it was latent. Parity SUB-398 and SUB-399 (P0, verified) and divergence 2.141 (Bug Fix) were added on rpg-planner's ruling. The mechanism-registry completeness check does not flag `src/core/stable_hash.py` (it is a helper function and appears only in the wider-scope floor), so `mechanisms.yaml` is unchanged. The changed-code advisory reports `perception` and `betrayal_siege_war` cited code changed; their `implemented_by` entries still hold, so no edit.
**Owner landing condition (#715 6412199242) met on 2026-10-27:** probe A0 found no WAR pair and no squad on the 3 gate worlds for seeds 42-46 at 5000 ticks, and `paired --neutral` is IDENTICAL; divergence 2.141 Measured is filled in. rpg-planner ruled that this satisfies the §12.5 condition for an early landing. The cross-hashseed proof of a real squad id comes from the constructed WAR-state test only. Push and PR wait for the user's yes. The PR body must say that the gate-world --neutral IDENTICAL is NOT behaviour coverage, and must state exactly what was measured.
