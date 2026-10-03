---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW
phase: done
date: 2026-10-03
tags: [world, observability, determinism]
---

# TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW

## Title

The region-owner "unowned" sentinel `-1` is never decoded and is persisted raw, crashing the
authoritative pipeline on the next tax tick

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

`WorldUpdate.owner_faction_id_set=None` already means "no change", so a liberation cannot express
clear-to-unowned with `None` and signals it with an in-band `-1`
(`src/world/influence.py`, liberation branch). **Nothing decoded it.** `src/engine/apply_plan.py`
guarded with `is not None`, which `-1` satisfies, so `-1` was written into a region's durable
`owner_faction_id`.

**Reproduced end-to-end through the real pipeline before fixing, not reasoned about.** Two ticks are
required: liberate on a tax tick (taxation that tick still sees the old valid owner), then the *next*
tax tick reads the persisted value — `src/engine/town_resolution.py:136` guards taxation with
`owner_faction_id is not None`, which `-1` passes, then does `faction_keys[region.owner_faction_id]`.
`faction_keys` is keyed by `Faction` members, whose values are `0..3`, so this raises
**`KeyError: -1`** and crashes the authoritative pipeline. `town_resolution.py:158` has the same
shape.

The same raw value also reached `SOVEREIGNTY_SHIFT` payloads as `new_owner="-1"` through both
`src/observability/event_extractor.py` and `src/observability/event_shapers.py`, which stringify it
directly.

The bare `-1` appeared in **four** places with no shared name, which is how it was missed. The correct
idiom already existed one file away: `src/engine/patches.py:236`,
`gid = None if self.group_id_set == -1 else self.group_id_set`.

Found while measuring `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`; it is **not** that
ticket's subject, whose own premise measured false.

## Scope

- Name the sentinel and decode it in exactly one place.
- Decode at the apply boundary so `-1` can never reach durable state.
- Decode at both observability sites so a liberation reports `None`, not `"-1"`.
- Regression tests that fail on the unfixed code, including one that reaches the real `KeyError`.

## Out of Scope

- The **semantic** overload of `owner_faction_id` (claim / control / jurisdiction in one slot) holding
  `TERR-01`/`TERR-03` at `CONFLICTING`. Confirmed by `world-rule-catalog-design` as a separate issue:
  fixing this sentinel changes neither verdict, and resolving the overload would not fix this.
- The `FAC-010` desync between `FactionState.territory` and `RegionState.owner_faction_id`.
- Consolidating the two ownership writers — `TCK-20260925-...` owns that, and deferred it.
- Ownership dynamics being near-inert in corpus worlds (balance, parked by `owner_decision_memo.md`
  row 7).

## Acceptance Criteria

1. A liberation persists `owner_faction_id is None`, never `-1`. **Met** —
   `test_liberation_clears_owner_to_none_not_raw_sentinel`.
2. Reaching a later tax tick with a previously-liberated region does not raise. **Met** —
   `test_liberated_region_survives_a_later_tax_tick_without_keyerror`, which reproduces the real
   `KeyError: -1` on the unfixed code.
3. `Faction.HERO_GUILD` is `int 0`, so the decoder must map only `-1` and must never treat `0` as
   absent. **Met** — asserted directly in
   `test_decode_owner_faction_id_set_maps_sentinel_but_preserves_hero_guild`.
4. Every test added fails on the unfixed code and passes after. **Met** — verified by reverting the
   apply-boundary decode and re-running.
5. No new bare `-1` literal for this concept; all sites share one named constant and one decoder.
   **Met**.

## Related Tickets

- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — where this was found; its own premise
  measured false and it closed decision-only.
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` — work-order item 1. **The
  scheduling dependency:** this defect is dormant today only because regional influence never moves
  (most regions pinned at `0.0`). Liberation requires a prior conquest and influence ≥ +50. Item 1's
  expected effect is more decided attacks, hence more deaths, hence influence actually moving — which
  turns this latent crash live. Landed with item 1 for that reason, on
  `world-rule-catalog-design`'s analysis and the owner's decision of 2026-10-03.
- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` — settled the ±50 constants this branch
  compares against.

## Related Docs

- `docs/mechanics/regional_sovereignty.md`, `docs/mechanics/05_world_evolution.md`
- `docs/world/regional_sovereignty_runtime_contract.md`
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-107`

## Related Stored Artifacts

- `agent-working/staging_artifacts/TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION/` — §4 and
  §5 hold the measurement and the observability consequence.

## Related Code Areas

- `src/core/updates.py` — `NO_OWNER_SENTINEL`, `decode_owner_faction_id_set` (new, the single home)
- `src/world/influence.py` — producer, liberation branch
- `src/engine/apply_plan.py` — apply boundary
- `src/engine/town_resolution.py:136,158` — the crash sites (unchanged; guarded by the decode)
- `src/observability/event_extractor.py`, `src/observability/event_shapers.py` — payload sites
- `src/engine/patches.py:236` — the pre-existing idiom followed here

## Assumptions / Open Questions

- Whether the three-state problem should be removed outright (a dedicated `owner_faction_id_clear:
  bool` field, rather than an in-band sentinel) is the cleaner long-term design. Not taken here: it is
  a schema change across producers and consumers, and this ticket is a hotfix on a reachable crash.
  Recorded as the better eventual fix.
- `town_resolution.py:136,158` still trust that the field holds a valid `Faction` or `None`. The
  decode now guarantees it at the only writer, but neither site validates defensively. Left as-is
  deliberately — a second guard there would hide a future encoding regression rather than surface it.

## Implementation Notes

Fix shape: one named constant plus one decoder in `src/core/updates.py`, used at the apply boundary
and both event sites; the producer now spells the constant instead of a bare `-1`.
`WorldUpdate`'s `@dataclass(frozen=True, slots=True)` was preserved — an early edit of mine briefly
dropped `slots=True` and detached the decorator; caught and corrected before commit.

## Test Summary

3 new tests in `tests/integration/world/test_region_owner_sentinel.py`, all positive-controlled
against the unfixed code:
- `test_decode_owner_faction_id_set_maps_sentinel_but_preserves_hero_guild` — unit-level, guards the
  `HERO_GUILD == 0` trap.
- `test_liberation_clears_owner_to_none_not_raw_sentinel` — fails unfixed with `assert -1 is None`.
- `test_liberated_region_survives_a_later_tax_tick_without_keyerror` — fails unfixed with the real
  `KeyError: -1` at `town_resolution.py:136`. Deliberately does **not** assert on the intermediate
  tick, because doing so short-circuits before the crash and the test would never exercise it.

352 other `tests/unit/world/` + `tests/integration/world/` tests pass. Two pre-existing failures,
both proven independent of this change by re-running without it and reported rather than masked:
`test_long_run_stability` (`TimeoutError`, fails on clean `src` too) and
`test_resource_opportunity_provider::test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village`
(cross-test pollution from the integration suite; still fails with this ticket's new test file
excluded).

## Files Changed

- `src/core/updates.py`
- `src/world/influence.py`
- `src/engine/apply_plan.py`
- `src/observability/event_extractor.py`
- `src/observability/event_shapers.py`
- `tests/integration/world/test_region_owner_sentinel.py` (new)

## Completion Summary

Closed 2026-10-03. A liberation can no longer persist `-1`; the sentinel is named once
(`NO_OWNER_SENTINEL`) and decoded once (`decode_owner_faction_id_set`) in `src/core/updates.py`, used
at the apply boundary and both observability payload sites.

All 5 acceptance criteria met. The crash was **reproduced before being fixed** -- `KeyError: -1` at
`src/engine/town_resolution.py:136`, reached across two real ticks through the authoritative pipeline
-- and all three new tests fail on the unfixed code, verified by reverting the apply-boundary decode
and re-running.

Landed with work-order item 1 rather than parked, on `world-rule-catalog-design`'s analysis and the
owner's decision: the defect is dormant only while regional influence stays inert, and item 1's
expected effect is to move influence, which turns the latent crash live.

Two pre-existing test failures were found, proven independent of this change, and reported rather than
masked or skipped: `test_long_run_stability` (`TimeoutError`, fails on clean `src/`) and
`test_resource_opportunity_provider::test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village`
(cross-test pollution; still fails with this ticket's new test file excluded).

Not done, deliberately: replacing the in-band sentinel with a dedicated `owner_faction_id_clear` field
is the cleaner design and is recorded in Assumptions as the better eventual fix, but it is a schema
change across producers and consumers and this was a hotfix on a reachable crash.
