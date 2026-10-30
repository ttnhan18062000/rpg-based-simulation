---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS
artifact_type: investigation
tags: [observability, testing]
---

# Investigation
- Under the default flags (all four ON) `extract()` emits almost nothing: 0 events in 300 ticks of `sandbox_world`, 4 in 200 ticks of `lifecycle_full_coverage_world`, 0 in `dungeon_crawl`. The push shapers carry the events; the rollback branches (flag OFF) are where `extract()` emits (3,707 to 12,116 events per scenario with all four OFF). So the flag matrix, not the default run, is what pins most of the file.
- Most existing unit tests build `MagicMock` states. `prior_state.feature_flags` is then a truthy mock whose `.get(...)` is never `"ON"`, so those tests run the rollback path, not the default. The `default_flags` config replaces `feature_flags` with `{}` to pin the real default as well.
- Event order depended on the string hash seed for events that list a set (seen on `skill_unlocked`, and on multi-slot equipment events). rpg hotfix (A), #790 (de5a223ca), sorts these at emission. Goldens are recorded on top of (A); recorders still run with `PYTHONHASHSEED=0`, and a test proves a second seed gives the same bytes. Not changed by this ticket.
- Three unit tests (`*through_real_kernel_tick_once`) run a Kernel without `audit_mode`; their emitted events differ run to run, so they are left out of the corpus and replaced by the audit-mode kernel scenarios.
- `TestAntiDriftGuards` reads `extract()`'s source, which the recorder wrapper hides, so it is left out of the corpus run (it still runs normally).
- No double emission was checked between `extract()` with a flag OFF and the shapers: out of scope; nothing was fixed or removed.

## Hash-seed order: how the fixtures stay byte-identical
- Before (A), the corpus showed a different digest between two recordings in separate processes (same count, different order) for events that list a set. The recorder does not sort, because emission order is behavior. The goldens were held until (A) (#790) merged, then re-recorded on top of it.
- `corpus.py` still runs both recorders in a subprocess with `PYTHONHASHSEED=0`. three tests (`test_corpus_recording_is_identical_under_a_second_hash_seed` and `test_kernel_recording_is_identical_under_a_second_hash_seed[<world>]`) record the corpus and each kernel scenario again at `PYTHONHASHSEED=12345` and assert the rows equal the pinned seed-0 fixtures.
- The corpus now includes main's `test_event_extractor_equipment_multislot.py` (3 new rows: 4 slots equipped, equip/swap/unequip across 3 slots, durability in 4 slots). The 368 earlier rows did not move under (A); only the kernel scenarios' digests changed.
- Consequence for ticket 2: the "fixtures unchanged" proof holds for a verbatim code move; a move that rebuilds a set differently could change order and would show as a digest change.
