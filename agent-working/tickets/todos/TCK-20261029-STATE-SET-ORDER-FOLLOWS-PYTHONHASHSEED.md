---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED
phase: open
date: 2026-10-29
tags: [determinism]
---

# TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED

## Title
Set ordering that reaches durable state or decisions follows the process hash seed. Audit every consumer, then sort.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
This is (B) of rpg-planner's 2026-10-29 split ruling. The ruling, word for word, is in `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`. The event-side half is TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (A).

String hashes vary per process with `PYTHONHASHSEED`, so any `list(set(...))`, or any iteration over a set, that reaches durable state or a decision makes two runs of the same world and seed diverge across processes. Harness and gate runs pin `PYTHONHASHSEED=0`, which hides this from every measurement.

The sites rpg-planner named (verified on 33da13604):
- `src/core/updates.py:276-281`, `IdentityUpdate.merge`: `breakthroughs_add`, `learned_skills`, `traits_add` and `traits_remove` are built with `list(set(...))`.
- `src/domains/combat_engagement/learning.py:45`: `known_skills = list(set(...))` is stored as the tuple `known_skill_ids` (`learning.py:98`, `schema.py:98`) in combat memory, which is ordered state.

rpg-planner-ubuntu's pre-investigation on 33da13604 is input to the audit, not a conclusion:
- **The merge lists may not reach state order.**
  - The apply path folds them into sets (`src/engine/patches.py:230-232`).
  - `IdentityComponent` holds `learned_skills`/`traits`/`active_breakthroughs` as `Set[str]` (`src/core/state.py:646-648`).
  - `to_canonical_dict` sorts them (`state.py:670`).
  - The audit must confirm this for every apply path, including `src/engine/apply.py:639-708`, and for every reader of the update lists before apply.
- **Set iteration in decision code does reach behaviour.**
  - `src/engine/tactical.py:704-722` iterates `entity.identity.learned_skills` (a set) into `available_skills`, then does a stable `sort(key=power, reverse=True)` and takes `[0]`.
  - When two ready skills tie on power, the chosen skill follows the hash seed. This is a live behaviour divergence, not just a hash change.
  - `src/progression/leveling.py:137-138` sums passive bonuses over a set. Float addition order is a possible bit-level difference.
- `known_skill_ids` tuple order is state: it reaches the canonical hash if combat memory is canonicalised.

## Scope
1. **Plan first: the audit.**
   - Find every `list(set(...))`, `tuple(set(...))` and `for ... in <set/frozenset>` under `src/`, outside `src/observability/` (that is ticket A), whose result reaches durable state, a decision or a canonical hash.
   - For each site, record: the file and line; what it feeds (state, decision, hash, emission-only); every consumer that reads it positionally (`[0]`, first match, stable sort, ordered join, float accumulation); and its disposition.
   - The audit table goes in `investigation.md` and is reviewed by rpg-planner before any code change.
2. Sort at each state- or decision-reaching site, with a stable key: the ID string or the enum `.value`, never `str(obj)`. Sites include the named ones, `tactical.py:706` and whatever the audit finds.
3. Add an intentional-divergence entry, numbered from ubuntu's block 2.144-2.149, with rationale class `Stabilized` (or as rpg-planner rules), and a verification test path. Update the Bible and parity ledger where a law's observable behaviour changes. Take rpg-planner's ruling per entry; COMB-264/265 cover skill selection.
4. Run a paired run at `PYTHONHASHSEED=0`, base main against this branch.
   - The state hash is expected to change.
   - Deaths must show no drift. Any drift in deaths or V-gates is a STOP and goes back to rpg-planner.

## Out of Scope
- Emit-loop ordering in `src/observability/` (ticket A).
- Pinning `PYTHONHASHSEED` in entry points instead of fixing the ordering.
- Dict iteration (insertion-ordered).
- Any file on u24's open branches. rpg-planner confirmed that `updates.py`, `evolution.py`, `event_extractor.py` and `learning.py` don't overlap #785, #781 or lane B's rpg-one-admission branch. Re-check before editing any other file the audit adds.

## Acceptance Criteria
1. The audit table is in `investigation.md`, and rpg-planner has OK'd it (comment id recorded) before Implement.
2. Every site the audit classes as state-, decision- or hash-reaching iterates in a stable sorted order.
3. A tie test: an entity with two ready skills of equal power picks the same skill under two `PYTHONHASHSEED` values, run in subprocesses.
   - Positive control: show it can differ on main, or explain why the fixture forces the tie.
4. A cross-process test: a fixed short run gives an identical final canonical state hash at two `PYTHONHASHSEED` values.
5. The paired run at seed 0 has been run, with worlds, seeds and ticks recorded.
   - The state-hash change is expected and noted.
   - Deaths show no drift, or the result is a STOP reported to rpg-planner.
6. The divergence entry, Bible and parity updates are made per rpg-planner's ruling. `parity_ledger_writer.py` was used for ledger edits.
7. The ticket states that cached paired-run arms from before this fix stay valid only for branches still based before it.
8. If any event in codebase M7's goldens changes, it is reported to rpg-planner as a finding. M7 does not re-pin silently.

## Related Tickets
- TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (A, lands first)
- codebase M7 batch 2 (does not wait for B)

## Related Docs
- `docs/engine/kernel.md` (determinism)
- `docs/mechanics/02_combat_laws.md` (skill selection)
- `docs/guidelines/intentional_divergences.md`
- `docs/parity_ledger/combat_movement.yaml` (COMB-264..267)

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`

## Related Code Areas
- `src/core/updates.py`
- `src/domains/combat_engagement/learning.py`
- `src/engine/tactical.py`
- `src/progression/leveling.py`
- `src/engine/patches.py`
- `src/engine/apply.py`
- `src/core/state.py` (read only: it is on u24's :1610 branch, so don't edit it)

## Assumptions / Open Questions
- Dispatch needs a fresh owner go. Standard tier is not covered by S4.
- The paired run takes the heavy slot after perf's quiet hour.
- If the audit finds a site in a file on u24's open branches, stop and route it through lead-planner.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
