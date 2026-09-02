---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260902-ATTRIBUTE-CLAMP-WIRING-GAP
phase: done
date: 2026-09-02
tags: [testing]
---

# TCK-20260902-ATTRIBUTE-CLAMP-WIRING-GAP

## Title
`AttributePatch.apply` clamps to 100 instead of documented `ATTRIBUTE_CAP=99`, no lower bound at
all — the correct fix exists but is dead code

## Status
DONE

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
- [x] `AttributePatch.apply` clamps to `[1, 99]` on both bounds via `enforce_attribute_caps` (or
      equivalent), not the current ad hoc `100`-only-upper-bound logic.
- [x] A real test proves an out-of-range attribute delta (both a too-high case and a negative case)
      is correctly clamped when applied through the actual `AttributePatch.apply` path, not just
      `enforce_attribute_caps` called in isolation.
- [x] `docs/mechanics/01_entity_anatomy.md`'s documented `ATTRIBUTE_CAP=99`/`[1,99]` range claim is
      confirmed still accurate against the fixed implementation (it already is — this fix makes
      code match doc, not the other way around).
- [x] Full regression sweep for `src/engine/patches.py`/`src/engine/rpg_depth.py`'s existing
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
- Resolved: no existing test or live gameplay behavior relies on the buggy 100-cap/no-floor clamp.
  Grepped all `AttributePatch` consumers (`tests/unit/domains/optimization/test_component_patches.py`,
  `tests/integration/optimization/test_component_patch_apply_parity.py`) — the only construction
  with attribute values (`AttributeComponent(strength=10, agility=10)` + `strength_delta=5`) stays
  well within `[1, 99]`, no interaction with the clamp at all. `tests/unit/core/test_rpg_math.py`
  explicitly documents (in a comment) that it deliberately excludes out-of-range attributes "to
  avoid `AttributePatch.apply`'s unrelated, pre-existing clamp bug" — confirming the bug was known
  and deliberately routed around, not silently relied upon.
- Tier confirmed `hotfix` — investigation surfaced no meaningful complexity; `AttributePatch.apply`
  has exactly one production caller (`src/engine/apply.py`) and 5 test consumers total, all
  verified compatible with the fix.

## Implementation Notes
Wired `enforce_attribute_caps` (`src/engine/rpg_depth.py:31-44`) into `AttributePatch.apply`
(`src/engine/patches.py:579-599`), replacing the old per-field `min(100, ...)` upper-bound-only
logic. Implementation: (1) compute the raw, unclamped new attribute values via `replace()` exactly
as before but without the `min(100, ...)` wrapper: (2) call `enforce_attribute_caps()` on the raw
result to get a dict of correction deltas for any out-of-range attribute (its existing, tested
contract — clamps to `[1, ATTRIBUTE_CAP=99]` on both bounds); (3) if any correction deltas were
returned, apply them via a second `replace()` call. When every attribute is already in range,
`enforce_attribute_caps` returns an empty dict and the second `replace()` is skipped entirely — the
normal in-range case does exactly one `replace()` call, same as before.

Reused `enforce_attribute_caps` directly rather than reimplementing clamp logic inline, per this
ticket's Related Code Areas / Out of Scope guidance (the function already exists, is already
unit-tested, and its `deltas` return contract — `{attr_name}_delta` keys, only for out-of-range
attributes — was designed exactly for this kind of downstream correction).

Also updated `docs/parity_ledger/substrate.yaml` entry `SUB-376`'s `support_boundary` field via
`tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit) — that entry's
`support_boundary` had explicitly disclosed this exact bug ("AttributePatch.apply clamps only an
upper bound (100) with no lower-bound floor... explicitly NOT fixed here") as a known, tangential,
deliberately-unfixed finding from a prior (unrelated, observability-focused) ticket. Since this
ticket now fixes it, that field would otherwise be stale/inaccurate — updated it to cite this fix
and its regression test, per CLAUDE.md's Authoritative Mechanics Rule (parity ledger updates
required in the same session as a logic change). `docs/mechanics/01_entity_anatomy.md`'s existing
"scale from 1 to 99" claim was confirmed still accurate (grepped directly) — no doc edit needed,
since this fix makes the code match the already-correct doc, not the reverse.

## Test Summary
Added 2 new tests to `tests/unit/domains/optimization/test_component_patches.py`:
- `test_attribute_patch_apply_clamps_to_documented_range` — proves both the too-high case
  (`strength: 95 + 20 = 115` → clamps to `99`, not the old buggy `100`) and the negative case
  (`agility: 3 + (-10) = -7` → clamps to `1`, where the old code had no floor at all) through the
  real `AttributePatch.apply()` path, not `enforce_attribute_caps()` called in isolation.
- `test_attribute_patch_apply_within_range_unaffected` — proves in-range deltas
  (`strength: 10+5=15`, `agility: 10-3=7`) pass through completely unchanged, confirming the fix
  doesn't perturb normal behavior.

Full regression sweep (every real consumer of `src/engine/patches.py`/`src/engine/rpg_depth.py`,
found via `grep -rl`, not guessed):
```
pytest tests/unit/domains/optimization/test_component_patches.py tests/unit/core/test_rpg_depth.py \
  tests/unit/core/test_rpg_math.py tests/integration/optimization/test_component_patch_apply_parity.py -v
  → 87 passed

pytest tests/unit/core/test_entity_integrity.py tests/unit/domains/memory/test_memory_update_phase_apply.py \
  tests/unit/strategic/test_committed_intention_materialization.py tests/unit/combat/test_tactical_wound_scar_wiring.py \
  tests/unit/core/test_domain_6_hardening.py tests/unit/progression/test_rpg_advancement.py -q
  → 30 passed

pytest tests/integration/combat/test_class_tier_win_rate.py -q
  → 1 passed
```
Total: **118 passed, 0 failed**, across every known consumer. No behavior change beyond the clamp
fix itself.

## Files Changed
- `src/engine/patches.py` — `AttributePatch.apply` now wires `enforce_attribute_caps` into the real
  apply path, clamping to `[1, 99]` on both bounds instead of the old ad hoc `min(100, ...)`
  upper-bound-only logic.
- `tests/unit/domains/optimization/test_component_patches.py` — added
  `test_attribute_patch_apply_clamps_to_documented_range` and
  `test_attribute_patch_apply_within_range_unaffected`.
- `docs/parity_ledger/substrate.yaml` — updated entry `SUB-376`'s `support_boundary` field (via
  `tools/parity_ledger_writer.py`) to reflect this fix, replacing the stale "explicitly NOT fixed
  here" note.

## Completion Summary
Wired the already-existing, already-tested `enforce_attribute_caps` (`src/engine/rpg_depth.py`)
into `AttributePatch.apply` (`src/engine/patches.py`), fixing a real bug where attribute values
were clamped to an undocumented `100` upper bound (not the documented `ATTRIBUTE_CAP=99`) with no
lower bound at all — an attribute delta could previously drive a stat arbitrarily negative. Added 2
regression tests proving both bounds now clamp correctly through the real apply path, and confirmed
via a full regression sweep (118 tests across every real consumer of the touched files) that
nothing else changed behavior. No existing test or gameplay path relied on the buggy behavior —
one test even explicitly documented working around it pending this exact fix. Updated the one
parity-ledger entry (`substrate.yaml` `SUB-376`) that had disclosed this bug as a known,
deliberately-unfixed finding, so it now accurately reflects the fix.
