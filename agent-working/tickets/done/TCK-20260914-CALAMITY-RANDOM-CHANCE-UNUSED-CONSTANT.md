---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT
phase: done
date: 2026-09-14
tags: [world]
---

# TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT

## Title
`CalamityService.CALAMITY_RANDOM_CHANCE = 0.005` is declared but has zero real usages anywhere — a
random-chance-shaped constant sitting inert beside the real, fully-deterministic spawn gate it looks
like it should influence

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5
(the `CalamityService.process_world_dynamics()` maturity-independent `world_boss` spawn path).
`CalamityService.CALAMITY_RANDOM_CHANCE = 0.005` (`src/world/calamity.py`) is declared as a class
constant but — confirmed via exhaustive grep of `src/` — has **zero real usages** anywhere outside
its own declaration line. The actual `should_spawn` gate next to it is driven entirely by a
deterministic interval check (`state.tick - state.last_calamity_tick >= CALAMITY_MIN_INTERVAL` AND
`state.tick % CALAMITY_FORCE_INTERVAL == 0`), not any random roll, despite this constant's name and
value strongly suggesting it was meant to gate something probabilistically.

This is the same silence-as-failure-mode family flagged repeatedly this week, but in its most inert
form: it doesn't silently produce a wrong result (nothing reads it), it's just dead weight that
misleads a reader into thinking calamity spawning has a random-chance component it does not have.

## Scope
- Determine why `CALAMITY_RANDOM_CHANCE` exists unused — check git blame / any related doc or
  ticket for whether it was ever wired and later orphaned, or declared and never connected.
- Decide and implement one of: (a) wire it into `should_spawn` as originally likely intended (real
  design decision, may need peer/user sign-off since it changes spawn behavior), or (b) delete it
  as dead code if no real intent can be found and the deterministic-only gate is confirmed correct
  as-is.
- Small, single-file change either way.

## Out of Scope
- The maturity/trauma gate reachability question itself — tracked in the sibling ticket
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), not this one.
- Any other calamity-system behavior change beyond this one constant.

## Acceptance Criteria
- [ ] Either `CALAMITY_RANDOM_CHANCE` is wired into real spawn logic with a stated rationale, or
      removed as confirmed dead code.
- [ ] No change to `should_spawn`'s existing deterministic interval behavior unless that's the
      explicit intent of the fix (option a).
- [ ] Grep-confirmed no other unused reference is left behind.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.CALAMITY_RANDOM_CHANCE`, `should_spawn` logic in
  `process_world_dynamics()`)

## Assumptions / Open Questions
- Whether this constant was ever wired and later orphaned during a refactor, or declared and never
  connected in the first place, is not yet known — first investigation step for whoever picks this
  up.

## Implementation Notes
Not implemented: the wire-or-delete choice was answered "neither" by owner decision 10 (catalog Rule `ENV-06`, commit
`043ebb30d`, 2026-10-05). The constant stays unwired and is not deleted; see the Disposition Rationale.

### 2026-09-30 — classified via `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T01`): fifth outcome `NO-MECHANISM` (AC-7)

**Zero-usage claim re-run at branch tip `3dbdff48a`, not cited.** `grep -rn CALAMITY_RANDOM_CHANCE src tests tools data`
returns exactly one hit: the declaration at `src/world/calamity.py:19`. No dynamic access exists that a
plain grep would hide (`getattr(CalamityService, ...)`, `vars(...)`, `__dict__` — none). Only docs mention
it, and they already call it dead: `docs/world/ecology_and_calamity_contract.md:81` ("defined but is not
wired into any active code path") and `:176`. `git log -S` finds a single introducing commit,
`562116889` (2026-05-18) — this answers the ticket's own open question: declared and never connected, not
wired-then-orphaned. `calamity.py` has no commits since this ticket's filing (2026-09-14).

**Why none of the four verdicts applies.** The axis classifies *mechanisms that do not execute*. There is no
mechanism here: a constant with no consumer has no code path that could be a `DEFECT` (no wiring bug hides a
working branch), a `CONDITION` (no input would make it run), or a `MISLABEL` (the contract doc describes it
accurately). The spawn gate next to it (`calamity.py:36-37`) runs, and is deterministic exactly as this ticket
says. `UNDECLARED` needs competing implementations; there is one gate. Recorded as a fifth outcome rather than
forced into the nearest bucket. The residual wire-vs-delete choice is this ticket's own scope option (a)/(b),
untouched by the classification.

## Test Summary
None: no code, test or doc was changed.

## Files Changed
Ticket only (`todos/` -> `done/`).

## Completion Summary
Closed `WONT-DO`: `CALAMITY_RANDOM_CHANCE` stays as is. Neither of the ticket's two options (wire it, delete it) is taken.

**Verdict as of 2026-09-30: fifth outcome `NO-MECHANISM` (AC-7)** — a dead constant, not an unreachable mechanism; see Implementation Notes. Still `OPEN`; wire-vs-delete decision unchanged.

## Disposition
WONT-DO

## Disposition Rationale
Owner decision 10 (commit `043ebb30d`, catalog Rule `ENV-06`) makes calamity the escalation of prolonged regional
instability and states that `CALAMITY_RANDOM_CHANCE` "stays unwired; any later probabilistic onset must be
conditioned on this escalation (`CAUSE-01`)". That answers both of this ticket's options with "neither": wiring it now
would add a probabilistic onset to a producer that does not exist yet, and deleting it would discard the constant a
later conditioned onset may use. `docs/world/ecology_and_calamity_contract.md:81` and `:176` already label it deliberate
dead code awaiting wiring, so they stay correct and are not edited. The constant's only occurrence is its declaration at
`src/world/calamity.py:19` (zero other usages, re-run 2026-09-30). **Caveat:** `043ebb30d` sits on
`origin/calamity-rule-decision` and was not on `origin/main` when this ticket was closed (checked with
`git merge-base --is-ancestor`); `ENV-06` is not citable from `main` until that branch lands.
