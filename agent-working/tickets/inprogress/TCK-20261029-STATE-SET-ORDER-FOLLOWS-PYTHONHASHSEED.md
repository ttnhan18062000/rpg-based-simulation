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
rpg-planner's audit list (ruling 2, word for word in the ruling file) governs this ticket. The plan first audits these items. rpg-planner reviews the audit before any code change.
1. `src/engine/tactical.py:704-722`, skill choice.
   - Use an explicit tie-break key: power descending, then skill id.
   - It may change seed-0 behaviour, so a paired run is needed and deaths must show no drift. Any drift is a STOP to rpg-planner.
   - Update the wording of Bible `02_combat_laws.md` and COMB-264/265.
   - Add a divergence from ubuntu's block (2.144-2.149), class `Bug Fix`.
2. `src/progression/leveling.py:137`: a float sum over a set. Sum in sorted order and check the effect on the seed-0 hash.
3. `src/domains/combat_engagement/learning.py:45`: `known_skill_ids` is an ordered tuple in combat memory. Use `sorted(set(...))` and check whether any reader is positional.
4. `IdentityUpdate.merge` (`src/core/updates.py:276-281`).
   - Confirm in the audit the pre-investigation finding that apply folds these lists into sets: check `src/engine/apply.py:639-708`, `src/engine/patches.py:230-232`, and every reader before apply.
   - If nothing reads them positionally, sort anyway for hygiene, with no behaviour claim.
5. A repo-wide sweep for `list(set(`, iteration over a set or frozenset that feeds decisions, and dicts built from sets. Report them, but don't fix them all. Append the items reported by ticket A's sweep.

Use a stable key everywhere: the ID string or the enum `.value`, never `str(obj)`. Update the Bible and the parity ledger where a law's observable behaviour changes, as rpg-planner rules for each entry.

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
- Dispatch needs a fresh owner go. Standard tier is not covered by S4. lead-planner asked the owner on 2026-10-29.
- `src/core/state.py` stays read-only until #785 (:1610) merges. After that, coordinate with rpg-planner if this ticket needs it.
- The paired run takes the heavy slot after perf's quiet hour.
- If the audit finds a site in a file on u24's open branches, stop and route it through lead-planner.

## Implementation Notes
Unit-level work done on ruling 3 (2026-10-30): the tactical tie-break (extracted as `pick_highest_power_skill`), the 5b concern merge (first-seen order via `dict.fromkeys`, sorted by urgency descending then id), and the hygiene sorts (`updates.py`, `evolution.py`, `apply_plan.py`, `learning.py`, `capacity_enforcement.py`, `intelligence.py`), each with a why-comment. `enforce_bandwidth` (`detour.py`) is unchanged: the merge now inserts concerns in id order, so a tie at the cap is already dropped by id; rpg-planner to say if it wants the id key there too. 5e (`generator.py`) stays out (own ticket). Docs: divergence 2.144 (STABILIZED), Bible `02_combat_laws.md` 5.5, COMB-264/265 via `parity_ledger_writer.py`.
**AC7**: cached paired-run arms recorded before this fix stay valid only for branches still based before it; a branch based on it needs a fresh arm.
Pending a heavy slot: the crowded-world cross-seed hash (PYTHONHASHSEED 0-3 identical, shown differing before if it does) and the seed-0 final hash against main on 3 worlds x seeds 42-46. If the seed-0 hash moves, STOP to rpg-planner.

## Test Summary
- `tests/unit/determinism/test_set_order_follows_no_hash_seed.py`: 6 passed, including two positive controls that flip with the seed.
- Scoped regression (`tests/unit/{strategic,combat,core,engine,progression,domains,ai,economy}`, `tests/engine`, `tests/mechanic_scenarios`, not slow): 3255 passed, 3 skipped, 1 xfailed.
## Files Changed
## Completion Summary
