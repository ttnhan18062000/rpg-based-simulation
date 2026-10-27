---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH
phase: done
date: 2026-09-08
tags: [world, content]
---

# TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH

## Title
raid_size doc formula (3 + camp.maturity) contradicts the code (3 + state.maturity) and is internally inconsistent against monster_cap

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`'s investigation, deliberately not resolved
there per that ticket's own Out of Scope ("Any change to raid difficulty/reward balance"):

`docs/world/raid_boss_camp_contract.md` §"Raid composition" states:

> `raid_size = 3 + camp.maturity` (integer — high-maturity camps send larger raids)

But the actual code (`src/world/raid.py`, `RaidService.check_for_raid()`):

```python
raid_size = RaidService.RAID_BASE_SIZE + state.maturity
```

uses `state.maturity` — the single global world-maturity counter (see
`TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`), not `camp.maturity`. In any practical
simulation run, `state.maturity` stays near 0 for a very long time (a plain periodic counter
requiring roughly 50,000 ticks to move meaningfully), so `raid_size` is effectively always
`3 + 0 = 3` today, contradicting the doc's stated intent that high-maturity camps send larger
raids.

**The doc's own formula is independently suspect, not just mismatched with the code**: a camp
triggers a raid at `camp.maturity >= 80` (`CampService.RAID_MATURITY_THRESHOLD`). Applying the
doc's literal formula at that threshold gives `raid_size = 3 + 80 = 83` raiders. Compare
`CampService`'s own `monster_cap = max(2, int(camp.maturity / 10))` (`camp.py`) — the SAME camp at
maturity 80 is capped at holding only 8 resident monsters. A camp that can never house more than 8
monsters dispatching an 83-raider raid is internally inconsistent. This makes "just implement the
doc" unsafe without a real balance decision.

## Scope
- Determine the intended raid-size scaling: does it belong to `camp.maturity` (per the doc's
  stated intent, "high-maturity camps send larger raids"), `state.maturity` (per the current
  code), some other formula entirely, or a capped/scaled version of `camp.maturity` that stays
  consistent with `monster_cap`'s own scale (e.g. a fraction of it, or a different divisor than
  the doc's raw `+camp.maturity`)?
- This is a real balance/design decision — do not resolve it unilaterally. Route through the
  established decision process (peer review / real user, per this repo's standing convention) with
  the internal-inconsistency evidence above laid out plainly.
- Once decided: update whichever side (doc or code) is wrong, or both if the formula itself
  changes, and add/adjust tests proving the new formula is applied correctly at both the low end
  (fresh camp) and the raid-trigger threshold (`maturity>=80`).
- Confirm whether the fix (if it changes code) affects both the global (non-camp) raid path and
  the camp-triggered path, or only one — they may reasonably diverge given they represent
  different things (`state.maturity` = world-level threat escalation; `camp.maturity` = this
  specific camp's own growth).

## Out of Scope
- Any other part of `raid.py`'s composition logic (spawn scatter, difficulty tier, target
  selection) — already correct/already fixed by `CAMP-RAID-ORIGIN-SPAWN-FIX`.
- Re-opening `CAMP-RAID-ORIGIN-SPAWN-FIX`'s own already-closed scope.

## Acceptance Criteria
- [x] (moot, see Completion Summary) A real decision is made and recorded on the intended `raid_size` formula, with the
      internal-inconsistency-against-`monster_cap` evidence considered explicitly.
- [x] (moot, see Completion Summary) Doc and code agree on the resulting formula.
- [x] (moot, see Completion Summary) Test coverage proves the decided formula at both a low-maturity and threshold-maturity camp.
- [x] (moot, see Completion Summary) No regression in existing camp/raid test suites.

## Related Tickets
- TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX (origin of this finding, deliberately scoped out of it)
- TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN (sibling finding about `state.maturity`'s own
  slow-growth characteristics, relevant context for whether `state.maturity` was ever a sensible
  raid-size driver)

## Related Docs
- `docs/world/raid_boss_camp_contract.md` §"Raid — `raid.py`" (Raid composition)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/raid.py` (`RaidService.check_for_raid()`, `RaidService.spawn_raid()`)
- `src/world/camp.py` (`CampService.process_camps()`'s `monster_cap` computation, for the
  internal-consistency comparison)

## Assumptions / Open Questions
- Whether `state.maturity`'s own extremely slow growth (per `WORLD-MATURITY-START-VALUE-DESIGN`)
  means it was never a realistic raid-size driver in the first place, making `camp.maturity` the
  obviously-intended signal despite the doc's own unscaled formula being wrong — not assumed here,
  left for this ticket's own decision process.

## Implementation Notes
Closed by disposition, 2026-10-26 (U2 batch 1; rpg-planner OK on #593 issuecomment-6406593752). The question this ticket asked (what `raid_size` should be) no longer exists, because both raid paths it compares are retired. Verified at main 3533fde71:
- The global world-clock raid, `RaidService.check_for_raid`: retired by owner decision 9 (2026-10-03, TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION). `src/engine/world_dynamics.py` section 3.5 builds an empty `StateUpdate` for it; `RaidService` has no `check_for_raid` attribute.
- The camp-triggered raid, `RaidService.spawn_raid`: retired by owner ruling D70 (2026-10-14, divergence 2.125, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70). `RaidService` has no `spawn_raid` attribute (`tests/unit/world/test_calamity_raid.py` asserts `not hasattr(RaidService, "spawn_raid")`), and `src/world/camp.py` no longer raids.
- `src/world/raid.py` is 33 lines: the class holds its constants (`RAID_BASE_SIZE = 3` among them) and comments, with no method. Nothing computes a raid size, so neither side of the doc-versus-code question exists.
**Doc corrected in a follow-up commit (rpg-planner-ubuntu, 2026-10-26: the ticket is a DOC-CODE mismatch, so it is not closed with the doc still wrong):** `docs/world/raid_boss_camp_contract.md` (`last_verified: 2026-09-04`) described both raid paths as live: the "Resolved" paragraph for `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`, the Raid composition block with `raid_size = 3 + camp.maturity`, the camp Monster spawning and Raid trigger sections, a Regression tests list that cited `test_long_run_stability.py` for raid and camp behavior it does not cover, and an extension rule citing `spawn_raid`. The doc now opens with a correction note that cites the retiring changes (decision 9, D70 / divergence 2.125) and says `raid.py` holds constants only; each retired passage is labelled historical and kept, not deleted. Sections re-checked on 2026-10-26 are listed in that note; the Boss and Spawn sections were not re-checked and the file's `last_verified` is not bumped.

## Test Summary
No code changed, no test run for this ticket. The retirement is asserted by `tests/unit/world/test_calamity_raid.py` (`not hasattr(RaidService, "spawn_raid")`).

## Files Changed
- docs/world/raid_boss_camp_contract.md (retired raid and camp-spawning passages labelled historical; correction note; regression-test list corrected). Doc correction only; no code change.

## Completion Summary
**Closed by disposition plus a doc correction; no code changed.** Both raid paths are retired (decision 9, 2026-10-03, and D70, 2026-10-14), so there is no `raid_size` to decide, and the acceptance criteria are moot. The contract doc that still described them as live is corrected in a follow-up commit (see Implementation Notes), so doc and code agree.
