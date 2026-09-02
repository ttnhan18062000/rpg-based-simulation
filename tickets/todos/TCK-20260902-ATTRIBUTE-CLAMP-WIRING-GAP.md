---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260902-ATTRIBUTE-CLAMP-WIRING-GAP
phase: open
date: 2026-09-02
tags: [testing]
---

# TCK-20260902-ATTRIBUTE-CLAMP-WIRING-GAP

## Title
`AttributePatch.apply` clamps to 100 instead of documented `ATTRIBUTE_CAP=99`, no lower bound at
all — the correct fix exists but is dead code

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`src/engine/patches.py`'s `AttributePatch.apply` (lines 579-594) clamps attribute values to an
upper bound of `100` instead of the documented `ATTRIBUTE_CAP = 99` (`src/engine/rpg_depth.py:26`),
and applies **no lower-bound clamp at all** — an attribute delta can drive a stat arbitrarily
negative. The correct clamp function, `enforce_attribute_caps`
(`src/engine/rpg_depth.py:31-44`), already exists, is already unit-tested
(`tests/unit/core/test_rpg_depth.py:451-464`), and correctly enforces `[1, 99]` — but it has
**zero callers anywhere in `src/`**. It was written but never wired into the live authoritative
mutation path.

Discovered during `TCK-20260902-PARITY-TEST-PATH-GAP` (M2 follow-up batch, already done, in
`tickets/done/`) while investigating what real invariant a new parity-ledger test should verify
for `SUB-051` ("Stats invariants"). That ticket deliberately scoped its new test
(`tests/unit/core/test_rpg_math.py::test_combat_stats_stay_within_bounds_after_normal_recalculation`)
to only construct attribute values already within the documented `1-99` range, specifically to
avoid legitimately failing on this bug — both its own architecture review and a second independent
architecture-review pass confirmed this scoping choice was sound engineering (a different,
narrower invariant than the one this bug violates) and explicitly recommended this gap be filed as
its own ticket rather than silently left only as prose in a closed ticket's stored artifacts.

## Scope
- Wire `enforce_attribute_caps` (`src/engine/rpg_depth.py:31-44`) into the live authoritative
  mutation path so `AttributePatch.apply` (`src/engine/patches.py:579-594`) actually enforces the
  documented `[1, 99]` range on both bounds, replacing the current ad hoc upper-bound-only-at-100
  clamp.
- Add a regression test proving out-of-range attribute deltas (both too-high and negative) are now
  correctly clamped to `[1, 99]` after applying an `AttributePatch` through the real authoritative
  apply path — not a synthetic call to `enforce_attribute_caps` in isolation (that coverage already
  exists), but proof it's actually reachable from `AttributePatch.apply`.
- Update or add a `docs/parity_ledger/` entry if this fix changes any documented/expected P0
  behavior around attribute mutation (check `docs/parity_ledger/substrate.yaml`/`progression.yaml`
  for an existing entry that should now cite this fix).

## Out of Scope
- The `tests/unit/core/test_rpg_math.py::test_combat_stats_stay_within_bounds_after_normal_recalculation`
  test itself (already correctly scoped and landed by `TCK-20260902-PARITY-TEST-PATH-GAP`) — do not
  touch it as part of this ticket unless this fix reveals it needs a genuinely new adversarial case
  added, which should be additive, not a rewrite.
- Any other same-pattern P0/null-`test_path` parity-ledger entries — unrelated, a separate systemic
  issue already flagged elsewhere.

## Acceptance Criteria
- [ ] `AttributePatch.apply` clamps to `[1, 99]` on both bounds via `enforce_attribute_caps` (or
      equivalent), not the current ad hoc `100`-only-upper-bound logic.
- [ ] A real test proves an out-of-range attribute delta (both a too-high case and a negative case)
      is correctly clamped when applied through the actual `AttributePatch.apply` path, not just
      `enforce_attribute_caps` called in isolation.
- [ ] `docs/mechanics/01_entity_anatomy.md`'s documented `ATTRIBUTE_CAP=99`/`[1,99]` range claim is
      confirmed still accurate against the fixed implementation (it already is — this fix makes
      code match doc, not the other way around).
- [ ] Full regression sweep for `src/engine/patches.py`/`src/engine/rpg_depth.py`'s existing
      consumers passes with no behavior change beyond the clamp fix itself.

## Related Tickets
- TCK-20260902-PARITY-TEST-PATH-GAP (where this was discovered)

## Related Docs
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/patches.py
- src/engine/rpg_depth.py

## Assumptions / Open Questions
- Not yet verified: whether any existing test or live gameplay behavior implicitly relies on the
  current buggy 100-cap/no-floor clamp (e.g. a test asserting a value of exactly 100 is reachable).
  If so, that test's expectation is itself wrong per the documented law and should be corrected,
  not preserved — but this needs real investigation before implementation, not assumed here.
- Tier filed as `hotfix` (a scoped, well-evidenced bug fix with a clear existing correct
  implementation to wire in) — reconsider if investigation surfaces meaningful complexity in how
  widely `AttributePatch.apply` is invoked across the pipeline.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
