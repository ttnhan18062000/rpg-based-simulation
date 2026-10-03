---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS
date: 2026-09-06
---

# Plan: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS

## Ordered Steps
1. Idea 4 — write a small citation-confirmation test reading `grade_anchors.json` directly (no
   Kernel run needed — the coverage already exists).
2. Idea 13 (team-up) then idea 30 (owner_history), since idea 30's own AC depends on idea 13
   landing first within this ticket.
3. Ideas 10, 14, 22, 33, 39 — independent, hand-seeded `AuthoritativeState` +
   `Kernel.tick_once()` proofs, following ticket 2's established Unit-tier pattern.
4. Idea 36/40 — hand-seeded 2-Clan `AuthoritativeState`, real `Kernel.tick_once()` defection path
   (`PartyLifecycleService.check_defection()`), matching the immediately-prior M9 sibling ticket's
   own precedent exactly.
5. Idea 44 — real compiled `hero_guild_routing` world content (read `world_compile_report.json` or
   compile fresh), assert real `PlaceKind` presence/absence.
6. Idea 49 — real compiled `mountain_pass` module content, assert `frost_shard` resource-node
   placement/harvest availability.
7. Run all 11 test files together, confirm 0 failures.
8. Finalize: move ticket, update working_log.csv, migrate staging artifacts.

## Files to Change
- 11 new test files under `tests/simulation_quality/` (see test_plan.md for exact names).
- `tickets/inprogress/TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS.md` -> `tickets/done/`.
- `tickets/working_log.csv` (append one row).
- `staging_artifacts/TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS/` -> `stored_artifacts/`.

## Explicit Scope Guards
- No `src/` production code changes — this ticket is test-authoring only.
- No new corpus world authoring — every sub-test either reuses an existing real world/module or
  uses a hand-seeded Unit-tier `AuthoritativeState` per `corpus_tier_taxonomy.md`'s own allowance.
- Do not "fix" the 5 corrections found in investigation.md — test the real mechanism as it exists.

## Dependency Map
Idea 30 depends on idea 13 (per this ticket's own AC) — sequenced accordingly in Step 2. All
others are independent.

## Acceptance Criteria Mapped to Steps
- AC1 (all 5 corpus tests... wait, 11 sub-items authored and passing) -> Steps 1-7.
- AC2 (no new corpus world authored) -> Step 4's hand-seeded-state choice, explicitly disclosed.

## Unresolved Questions
None.
