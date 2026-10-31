---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
phase: open
date: 2026-10-31
tags: [social, simulation-quality]
---

# Plan: group ids from a typed counter

Binding: `rpg_designer_ruling_2026-10-31.md` (Option A, four additions) and the ticket. Nothing below replaces them. Investigation: `investigation.md`.

## Design (settled here; items marked ASK change behaviour or hashes)
1. **Counter.** `AuthoritativeState.next_group_id: int = 10000`. Read by decision code; written only by apply.
2. **Typed add.** `StateUpdate.groups_add: List[GroupRecord]` is the only way to create a record. `groups_add_or_update` keeps in-place updates of an existing group (dissolution markers, cohesion update, election/defection results). Squad records (`military_conflict.py:341`) move to `groups_add`, ids unchanged.
3. **Formation id (decision code).** `GroupSystem.update_groups` allocates from `state.next_group_id` plus a local pending offset: start at the counter, step past any id in `state.groups`, in `update.groups_add` or already allocated this tick; no state is written. It sets `StateUpdate.next_group_id_set` = last allocated + 1 (max-merged in `StateUpdate.merge`). Squad producers set none, so squad adds never advance it.
4. **Apply (`apply_plan.py:124`).** Process `groups_add` in order: an id already in the store (prior state or an earlier add this tick) is a TYPED REJECTION, not a replace: the row is dropped, `rejections_delta["group_add_id_taken"]` counts it. Then `groups_add_or_update` rows are upserted as today. Counter = max(prior, `next_group_id_set`).
5. **Same-tick merge (`pipeline_phases/groups.py:45-55`).** `groups_add` lists are concatenated, never merged by id, so a duplicate reaches apply and is rejected there. Election/defection passes read `groups_add` rows too and write their results as updates.
6. **Other readers of `groups_add_or_update`** (`core/dirty.py:117,294`, `updates.py` is_empty/merge/replace, `apply_plan.py:105`, `cooperation/phase.py:213`) must also see `groups_add`.
7. **Canonical + replay.** `next_group_id` joins `CanonicalStateHasher.to_canonical_data` and the fingerprint. ASK: unconditional (every hash moves at tick 0) vs omitted while it equals 10000 (the `grief_drained_tick` precedent, `checkpoint.py:123`; hashes then move at the first allocation). Plan default: omit at 10000, so the first diff is the first allocation. Round-trip architecture test either way.
8. **Load seed (addition 4).** Where a state is rebuilt from saved data and `next_group_id` is absent: `max(10000, highest id of groups without a FACTION_SQUAD role + 1)`. Find the loader(s) first; if none exist in `src/`, record that and test the seed function directly.
9. **Disclosures.** `Bug Fix` divergence (next free ubuntu id at close; 2.144 is B, 2.145 likely the generator), `social_narrative.yaml` parity entry, Bible chapter if it states the id rule (search first), mechanism note text from rpg-planner only if `implemented_by` changes.
10. **Fold-in:** the 12 whole-key slow_known_reds entries under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, expiry 2026-11-15 -> 2026-11-29, citing #715 6540197059, nothing else.

## Order
Locate loader + all `groups_add_or_update` readers -> tests first (fail on old code) -> state/update/apply -> allocator and squad move -> canonical/fingerprint -> docs -> measure (needs lead-planner's go).

## Out of scope
Squad id generation, SimQ re-anchor, retention fix, anything in `registries/mechanisms.yaml`.
