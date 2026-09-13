---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED
phase: done
date: 2026-09-12
tags: [world, architecture]
---

# TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED

## Title
`VeterancyService.get_stat_multiplier(rank)` has zero real callers, and nothing declares it
should — documented and closed as tracked-but-cosmetic, not wired

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD`'s own
earned-progression audit, while confirming `veterancy_points`/`veterancy_rank` are real,
accumulated progression worth carrying forward at survivor reconstruction.

`VeterancyService.process_points()` (`src/progression/veterancy.py:28-45`) is real and live —
wired through `src/engine/patches.py`/`src/engine/apply.py`, correctly accumulating
`veterancy_points` and incrementing `veterancy_rank` as points cross thresholds
(`get_points_to_next_rank(rank) = 10 * (2 ** rank)`). Confirmed via grep this accumulation
mechanism has real callers and genuinely runs.

`VeterancyService.get_stat_multiplier(rank)` (`veterancy.py:19-25`) — the function whose own
docstring says it provides "+5% to physical/magical output" per rank — has **zero real callers
anywhere in `src/`**. Confirmed via a full grep for `get_stat_multiplier`. Veterancy rank
accumulates correctly, tracked, persisted, carried forward — and never affects a single combat
stat, ever. This is the same "earned progression with no mechanical effect" shape as the
knowledge/investigation-layer and behavior-analytics-pipeline findings from the prior batch: a
real subsystem that computes something and nothing downstream consumes it.

## Scope
- Determine whether `get_stat_multiplier()` should be wired into `SkillScalingService.
  get_effective_stats()`/`LevelingService.recalculate_combat_stats()` (the real combat-stat
  derivation chain, confirmed in the origin ticket's own investigation) — this is a real design
  decision (does veterancy rank apply as a flat multiplier on final stats, or should it be
  folded into the base/attribute contribution some other way?), not something to resolve
  unilaterally. Route through peer review before implementing.
- Check whether `get_stat_multiplier()`'s own formula (`1.0 + rank * 0.05`) is still the intended
  design, or whether it predates other combat-stat changes and needs re-deriving — don't assume
  the dead function's own numbers are still correct just because they're unused, verify against
  current balance intent if any documentation exists.
- If wired: real test evidence that a high-veterancy-rank entity's combat stats genuinely differ
  from a same-attributes/same-equipment, zero-veterancy entity.

**Resolved 2026-09-13 — see Completion Summary.** Declared-intent check (Mechanics Bible, parity
ledger, compliance checklist) found nothing authoritative behind the "rank should modify combat"
claim; disposition is document-only, not wire. `get_stat_multiplier()`'s formula question above is
moot under that disposition — nothing re-derives a formula for a function staying unwired.

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD`'s own fix — that ticket
  carries `veterancy_points`/`veterancy_rank` forward regardless of this ticket's disposition,
  since preserving real earned state is correct even while its downstream application is
  separately incomplete. Not reopened here.
- Any other combat-stat formula change beyond wiring in the veterancy multiplier specifically.

## Acceptance Criteria
- [x] Real evidence confirms `get_stat_multiplier()` has zero callers (already established in the
      origin ticket; re-verify as current when this ticket is picked up).
- [x] A peer-routed decision: wire the multiplier in (and where/how), or formally document
      veterancy rank as tracked-but-cosmetic (no mechanical effect), obtained before
      implementation. **Decision: document-only.**
- [x] N/A — not wired. Instead: `PROG-014` and `PROG-086`'s stale citations corrected, and
      `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` filed to record the pattern.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD` (origin — found during
  its own earned-progression field audit)
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done — found and corrected the first
  instance of the same "verified with null test_path" defect in this file, `PROG-001`; this
  ticket's own investigation found the second and third instances)
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` (filed from this ticket's own finding —
  three occurrences of the same defect in one file is a pattern worth a full sweep)

## Related Docs
- `docs/parity_ledger/progression.yaml` (`PROG-014` — corrected `status: verified` →
  `status: missing` via `parity_ledger_writer.py`)
- `docs/compliance/checklist.md` (`PROG-086` — stale citations corrected in place)
- `docs/mechanics/04_strategic_cognition.md` and siblings — checked, zero mentions of veterancy
  anywhere; part of the declared-intent evidence this ticket's disposition rests on

## Related Stored Artifacts
`stored_artifacts/TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED/` (investigation.md,
plan.md, test_plan.md)

## Related Code Areas
- `src/progression/veterancy.py` (`VeterancyService.get_stat_multiplier()`, `process_points()`)
- `src/engine/rpg_depth.py` (`SkillScalingService.get_effective_stats()`)
- `src/progression/leveling.py` (`LevelingService.recalculate_combat_stats()`)

## Assumptions / Open Questions
- Whether veterancy should mechanically affect combat stats at all, or was always meant to be a
  tracked-but-cosmetic rank display, is the real open question — not pre-judged here.

## Implementation Notes
Re-verified the origin ticket's zero-callers claim for `get_stat_multiplier()` — still accurate.
Ran the declared-intent check peer's instruction required before building anything: Mechanics
Bible has zero mentions of veterancy; the parity ledger's `PROG-014` claims veterancy should boost
stats via `StatsProxy` but has `test_path: null`/`proof_type: null` and names a dead V1 concept
absent from `src/`; `docs/compliance/checklist.md`'s `PROG-086` cites a test file
(`tests/unit/progression/test_veterancy.py`) that doesn't exist and a code line
(`apply.py:454`) that's unrelated carryforward code today. All three potential "declared intent"
sources are either silent or themselves unsubstantiated.

Reported this to peer before building, per instruction. Peer's disposition: document-only — three
stale/unsubstantiated citations for the same claim is evidence the intent was never real, not weak
evidence that it was. Wiring `get_stat_multiplier()` now would invent gameplay rather than
complete a declared design.

Corrected both stale citations rather than leaving them in place: `PROG-014`'s status via
`tools/parity_ledger_writer.py` (`verified` → `missing`, with a `support_boundary` recording what
was actually found), and `PROG-086`'s test/line citations directly in `checklist.md`. Filed
`TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` since this is now the third confirmed
instance of the identical defect shape in one ledger file, across two unrelated investigations
months apart — a pattern worth a dedicated sweep rather than one-off fixes each time it's
stumbled into.

## Test Summary
No code changed in `src/` — see test_plan.md for the full evidence trail (grep re-verification,
direct file checks for both stale citations). Parity ledger write confirmed schema-valid via
`parity_ledger_writer.py`'s own `validate_entry()` gate (write succeeded, ledger rebuilt: 2187
entries, 9 shards).

## Files Changed
- `docs/parity_ledger/progression.yaml` — `PROG-014` corrected via `parity_ledger_writer.py`.
- `docs/compliance/checklist.md` — `PROG-086`'s stale citations corrected in place.
- `tickets/inprogress/TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED.md` → closed.
- `tickets/todos/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP.md` — new, filed.
- `staging_artifacts/TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED/` — new, moved to
  `stored_artifacts/` on close.

## Completion Summary
Declared-intent check found nothing real behind the "veterancy rank modifies combat" claim —
Mechanics Bible silent, and the two citations that appeared to declare it are both themselves
unsubstantiated stale citations of the same underlying (never-verified) claim. Closed
document-only per peer decision: `get_stat_multiplier()` stays unwired, both stale citations
corrected, and a ledger-wide sweep ticket filed for the now-three-times-confirmed pattern.
