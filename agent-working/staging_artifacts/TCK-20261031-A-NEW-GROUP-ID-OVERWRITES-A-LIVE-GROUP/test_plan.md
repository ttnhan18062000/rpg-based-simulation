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

# Test plan

## Tests
1. Dissolve-then-form in the same tick and across ticks, with gaps in the id range (the `repro_collision.py` state): no live record overwritten; every living member's `group_id` resolves to a group that lists it. Fails on the old formula.
2. Two formations in one tick get distinct ids; ids skip a squad hash id already in the store.
3. Apply: an add over a different live id is rejected, counted in `rejection_registry["group_add_id_taken"]`, store unchanged; an in-place update of the same group still replaces it; a duplicate pair inside one tick's `groups_add` keeps the first.
4. Squad adds do not advance the counter; formation adds do; the counter never falls.
5. Architecture: `next_group_id` in the canonical dict, round-trips; load seed from an old state without it (incl. a squad hash id that must not seed it).
6. Hard-law style check: across a multi-tick run, no GroupRecord id is re-issued and every living entity's `group_id` resolves to a group that lists it. Fires on the old formula.

## Proof Plan
- Positive control: tests 1 and 6 run against the pre-change allocator (git stash-free: temporarily restore the old line in a scratch copy) and must fail with the collision above.
- Scoped runs: tests/unit/social, tests/unit/core, tests/architecture (read-only look), the replay/checkpoint tests, `generate_registry --check`, paths-guard.

## Base / after count (needs lead-planner's go; plan sent to rpg-planner-ubuntu)
Read-only probe wrapper, no source edits: after each tick count overwrites (an incoming row whose id exists with a different leader and disjoint members) and ghost members (living entities whose group_id points at a group not listing them or missing). Positive control: run the probe on the `repro_collision.py` state (expect 1 overwrite, 2 ghosts) and on a clean state (0, 0) before the runs. After the fix, both must be 0 and the end-of-run resolve check passes.
