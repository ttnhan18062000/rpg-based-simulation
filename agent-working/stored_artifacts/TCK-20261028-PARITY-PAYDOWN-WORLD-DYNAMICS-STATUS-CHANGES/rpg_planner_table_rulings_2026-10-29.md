---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES
artifact_type: investigation
tags: []
---

# rpg-planner (u24) rulings on the draft table, 2026-10-29

Word for word, as relayed by rpg-planner-ubuntu: rpg-planner (u24) ruled via lead-planner-u24 and then lead-planner. NOT an owner approval.

NOTE 4 (blocks PR A): move WORLD-073, 082 and 083 to C, and keep the rest in D.
- 073 "Spawned entity role is valid": the cited test covers two roles. New test in C: every compiled corpus entity's role is a valid enum member.
- 082/083 "... rule is deterministic": the cited tests show the rule, not determinism. New tests in C: the same inputs twice give an identical trigger/escalation result.
- Accepted as cited: 015, 016, 041 (the tier mapping is the query and zone logic; 042's boundaries are separately in C), 023 (one scheduled advance shows the schedule), 069, 088, 092, 096.
- PR A then re-runs the tighten after the move.

NOTE 1 (sibling): agreed with ubuntu and lead. The 21 entries that rest only on 6e5c28992 become `missing`.
- Each support_boundary says, factually: "Not carried into V2: absent since the V2 rewrite 6e5c28992; no per-feature retirement decision is recorded."
- Where V2 has a successor structure, also name it: e.g. 040 Location -> PlaceState/RegionState, 052 Voronoi -> authored rectangles plus find_region_at, 051 -> PlaceKind.
- Give the owner ONE list of the 21, split into "superseded by a V2 structure" and "gameplay feature absent", with a proposed decision per group: retire (which moves them to unsupported, citing that decision) or build. Don't decide it for the owner.
- 033, 034 and 078 (D70, pinned) stay `unsupported`.

NOTE 2: WORLD-006 -> `unsupported`. The boundary names owner decision 501933066 (default-OFF) and states that no navigation path routes a world boss through the flow field.

NOTE 3
- 022 -> `missing`.
- 002: cite the route test, status unchanged, text left as it is. "terrain-cost-sensitive navigation is preserved" is still true. Note the stale test name in the table.
- 084 -> `divergent`, not missing. test_path: test_calamity_boss_spawn plus tests/architecture/test_calamity_intensity_producer_unwired.py. divergence_note names TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.
- 054: write the corpus test (every compiled corpus world: each region touches another region). If it passes, cite it. If it fails on any corpus world, `missing` with the failing world named.
- 067: cite test_compiler_seeding_determinism (same seed, same compiled world, regions included). The status stays.
- 093: say which hasher the replay path uses.
  - CanonicalStateHasher: add the per-component test and cite it.
  - StateFingerprinter (omits buildings and camps): `divergent`, with the test pinning what it covers and a note on what it omits.

NOTE 5: WORLD-013 stays legacy_verified with a test_path.

All other A, B and C rows are OK as drafted. The final sibling table comes back to rpg-planner before its PR.

ORDER (from rpg-planner-ubuntu):
1. PR A first: remove the 073, 082 and 083 citations (done at d99b1db21, tighten re-run last: world_dynamics 55/55).
2. Then rebase the stacked sibling branch onto PR A's new head and apply the rulings. Add new tests for 073, 082, 083 and 054, and a 093 test once it is decided which hasher replay uses. The 21 entries become missing with the exact boundary sentence. Build the owner list of 21, split into two groups, each with a proposed retire/build. Write NOTHING to the ledger until the final table has gone back to rpg-planner through rpg-planner-ubuntu. tests/architecture/** belongs to testing-planner: CITE the 084 test there, do not edit it. If any new test fails, stop and tell rpg-planner-ubuntu.

## Second ruling: the final table (4bb97d8a0), 2026-10-29

Word for word, relayed by rpg-planner-ubuntu: rpg-planner (u24) via lead-planner-u24 and then lead-planner. NOT an owner approval.

2) Final sibling table (4bb97d8a0, read in full): OK to write as drafted, with two additions.
- Count: 20 is right. 053 stays out of groups 1 and 2.
  - Add a GROUP 4 to section E: "never built in V2, no removal commit", covering 022, 026, 028, 035, 053 and 089.
  - Those are P0 `missing` disclosures too. Proposed decision per item: retire unless the roadmap wants it, same as group 2. No decision is made in the table.
- Group 3: rpg-planner recommends the owner ACCEPT the worlds as authored.
  - The two calibration/fixture worlds and swamp_border_world don't need region adjacency.
  - The only consumer, RegionalPressureModel propagation, just doesn't propagate into an isolated region.
  - 054 stays `missing` with the worlds named. If the owner wants adjacency instead, rpg-planner files a data/worlds ticket.
- Everything else matches its rulings.
3) The 091 finding is known and ticketed (TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT, TCK-20261009-AUTONOMOUS-LOOP-DRIFT-GUARD-RUNS-WITHOUT-AUDIT-MODE-SO-HOST-LOAD-FLIPS-IT, and the determinism-envelope epic). audit_mode plus a positive control is the established pattern. No new ticket.

Instructions from rpg-planner-ubuntu with it: write all 55 entries at their table status through parity_ledger_writer.py in chunks of about 20; groups 1 to 4 are written as `missing` and the owner's decision on section E becomes a FOLLOW-UP ticket, not part of this PR; tighten last after the final sync with origin/main (world_dynamics should reach 0 P0 / 0 all test_path errors); run the checks (gate, code-health, paths-guard, new and cited tests, generate_registry --check, done_checker for both tickets).
