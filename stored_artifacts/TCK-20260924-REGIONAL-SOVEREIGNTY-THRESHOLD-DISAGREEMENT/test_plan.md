---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT
artifact_type: test_plan
tags: [world, documentation, determinism]
---

# Test Plan — TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT

## Regression Surface

- `tests/unit/world/test_influence.py` — full file must keep passing. **`test_conquest_and_liberation_thresholds`
  (`:40-76`) currently asserts the ±50 value directly** (region influence -46.0 + one hero death =
  -51.0 ≤ -50.0 conquest; 46.0 + one monster death = 51.0 ≥ 50.0 liberation). Per the settled
  decision this test's fixture values must be updated to cross ±100 instead of ±50 (e.g. -96.0 →
  -101.0, 96.0 → 101.0) as **in-scope work for this ticket**, not treated as an unrelated
  regression to leave broken or to skip.
- `tests/unit/world/test_stronghold.py` — full file must keep passing. Both
  `test_stronghold_lifecycle` (`:8-35`, 10 hero deaths × 5.0 = -50.0, currently exactly at the ±50
  conquest threshold) and `test_stronghold_removal` (`:37-71`, 20 monster deaths × 5.0 = +100.0
  from a -50.0 start, currently exactly at the ±50 liberation threshold) must have their death
  counts increased (conquest: 20 hero deaths for -100.0; liberation: from a -100.0 start, 40
  monster deaths for +100.0) to keep exercising real conquest/liberation transitions after the
  constant change.
- `tests/unit/world/test_sovereignty_events.py` — full file exercises
  `WorldDynamicsSystem.resolve_dynamics`'s step-2.2 ownership+event-emission logic in isolation
  (via its own `_run_step22` helper, `:33-44`), independent of `FactionInfluenceService`. **These
  four tests will need real rework, not just threshold-value edits**, because the settled decision
  removes the code they exercise (`world_dynamics.py:80-89`) and, per the investigation's finding,
  the event-emission code at `:91-100` that they also indirectly assert on depends on that block.
  Specifically:
  - `test_sovereignty_shift_event_emitted_on_hero_takeover` (`:59-73`) constructs a region at
    influence=110.0 with no pre-existing `owner_faction_id_set` in the input `StateUpdate`, and
    expects `resolve_dynamics` alone to both decide `HERO_GUILD` ownership *and* emit the event.
    After the fix, `resolve_dynamics` alone can no longer make that decision (see investigation's
    "HERO_GUILD" risk) — this test's setup must change to pre-seed `w_upd.owner_faction_id_set`
    (simulating what `FactionInfluenceService` would have already written this tick) if the intent
    is to test "event fires when ownership changed," or be deleted/moved if the decision is that
    `resolve_dynamics` no longer independently triggers HERO_GUILD takeovers at all.
  - `test_sovereignty_shift_event_emitted_on_monster_takeover` (`:76-86`) — same shape, MONSTER_HORDE
    side; same rework need.
  - `test_no_sovereignty_event_when_influence_below_threshold` (`:89-98`) — asserts no event at
    influence=50.0; should still hold true after the fix (below any real threshold, before or
    after ±50→±100), but must be re-verified once the emission logic is rewired to read
    `owner_faction_id_set` rather than compute its own threshold.
  - `test_sovereignty_event_payload_contains_influence` (`:101-112`) — same rework need as the two
    takeover tests above (influence=120.0, no pre-seeded ownership decision).
- `tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip` (`:9-71`) —
  **this is the test that will actually fail (not just need value updates) if
  `WorldDynamicsSystem`'s HERO_GUILD-assignment is deleted without `FactionInfluenceService`
  gaining equivalent logic** (see investigation's Risks section). This is the single most
  important existing test to watch during implementation — it must stay green or its failure must
  be explicitly reconciled with whatever the planner decides about HERO_GUILD assignment, not
  silently rewritten to assert something weaker.
- `tests/integration/world/test_regional_sovereignty.py::test_governance_taxation_and_vaults` (below
  `:73` in the same file) — unrelated to the threshold/ownership-decision logic (reads only
  `region.owner_faction_id`, already committed), should be unaffected; run alongside the file's
  other test as a sanity check that nothing else in the same module broke.
- `tests/integration/world/test_phase9_stability.py`, `tests/integration/pipeline/test_strategic_cadence.py`,
  `tests/integration/scenarios/test_demographics.py`, `tests/simulation_quality/test_region_transformation_pipeline_corpus.py`,
  `tests/integrity/test_logic_guards.py` — all call `WorldDynamicsSystem`/`resolve_dynamics`
  indirectly per the graphify/grep sweep; none were found to assert on the ownership threshold or
  event-emission specifics, but each exercises `resolve_dynamics` end-to-end and should be run to
  catch any collateral breakage from restructuring `:62-116`.
- `tests/unit/world/test_camp_lifecycle.py`, `tests/unit/world/test_creature_territory_lifecycle.py`,
  `tests/unit/world/test_reproduction_humanoid_cadence.py` — exercise other sections of
  `resolve_dynamics` (camps, creature territory, reproduction) that live in the same function but
  are structurally independent of the ownership block (confirmed in investigation's Current
  Behavior — nothing past line 110 reads `new_owner`/`owner_fid`); included as a sanity net, low
  expected risk.

## New Tests Required

1. **AC 2/4/5 — the threshold is ±100 everywhere and cannot silently drift apart again.**
   - `test_conquest_and_liberation_thresholds_match_across_both_paths` — a new regression test
     (location: `tests/unit/world/test_influence.py` or a small dedicated
     `tests/unit/world/test_sovereignty_threshold_parity.py`) that asserts
     `FactionInfluenceService.CONQUEST_THRESHOLD == -100.0`,
     `FactionInfluenceService.LIBERATION_THRESHOLD == 100.0`, and — via a source-level or
     behavioral check — that whatever value(s) `WorldDynamicsSystem`'s remaining code (post-fix)
     uses for ownership-adjacent logic agree with these constants (e.g. if the event-emission
     rewrite keeps a literal `100.0`/`-100.0` comparison for detecting a same-tick change, assert
     it against the same constants rather than a hardcoded literal, or assert both values via a
     single shared constant/import to make future drift structurally impossible). Category:
     unit/regression guard. This is the test AC 5 explicitly requires ("fails if either drifts").
2. **AC 4 — the strict-inequality/clamp reconciliation is real, not just prose.**
   - `test_influence_exactly_at_clamp_boundary_triggers_ownership_change` — asserts that an
     influence value of exactly 100.0 (the clamp's own boundary, `influence.py:59`) is sufficient
     to trigger conquest/liberation via `FactionInfluenceService`, proving the Bible's `>= 100.0`
     phrasing (not `> 100.0`) is what the code actually implements post-fix. Category: unit.
     Lives in `tests/unit/world/test_influence.py`.
3. **AC 3 — dual-authority is resolved: `WorldDynamicsSystem` no longer independently writes
   `owner_faction_id`.**
   - `test_world_dynamics_never_sets_owner_faction_id_independently` — drives
     `WorldDynamicsSystem.resolve_dynamics` directly (mirroring `test_sovereignty_events.py`'s
     `_run_step22` helper) with a region at an extreme influence value (e.g. 150.0, past any
     threshold) and an **empty** input `StateUpdate` (no pre-seeded `owner_faction_id_set` from
     `FactionInfluenceService`), then asserts the returned `WorldUpdate.owner_faction_id_set` is
     `None` — i.e. `resolve_dynamics` alone, without `FactionInfluenceService` having already
     decided something this tick, never assigns ownership. This is the direct, positive proof that
     the conquest block was actually deleted and not merely left dormant. Category: unit/
     architecture guard. New or extended `tests/unit/world/test_sovereignty_events.py`.
   - `test_sovereignty_shift_event_reflects_upstream_owner_decision` — feeds a `StateUpdate` whose
     `world_updates[region_id].owner_faction_id_set` is already set (simulating
     `FactionInfluenceService` having run earlier — see investigation's ordering note about phase
     sequencing) into `resolve_dynamics`, and asserts the SOVEREIGNTY_SHIFT event still fires with
     the correct `subject`/`payload`. This preserves WORLD-107's certified behavior (event emission
     on ownership change) under the new architecture. Category: unit. Same file.
4. **AC 1/7 — the HERO_GUILD-assignment gap flagged in investigation is resolved one way or the
   other, and is testable either way.**
   - Not written here — this depends on the planner's decision (documented as an open question in
     investigation.md, not resolved there). Whichever way it resolves, `plan.md` must name the
     exact test that proves it:
     - If `FactionInfluenceService` gains HERO_GUILD-assignment logic:
       `test_liberation_can_produce_hero_guild_ownership` (or equivalent) in
       `tests/unit/world/test_influence.py`, mirroring the existing conquest/liberation test shape.
     - If the narrowing is accepted as intentional: `test_regional_ownership_flip` (existing,
       `tests/integration/world/test_regional_sovereignty.py:9-71`) must be explicitly updated
       (not deleted silently) to reflect the new expected outcome, and
       `docs/guidelines/intentional_divergences.md` must carry an entry per AC 7 documenting this
       specific narrowing as an intentional behavior change (see below).
5. **AC 7 — intentional divergence entry, if the chosen value/structure changes observable
   behavior (it does).**
   - Not a pytest test — a documentation requirement. `docs/guidelines/intentional_divergences.md`
     needs a new row in its Summary Table (format: `| Subsystem | Feature | Rationale Class |
     Status |`, e.g. `| World / Sovereignty | Conquest/Liberation Threshold ±50→±100 | Bug Fix |
     RATIFIED |`) plus a `## 2.x` Detailed Record (Subsystem/Old Behavior/New Behavior/Rationale/
     Verification, matching the existing 48-row convention) with `Verification` pointing at
     whichever new test (item 1 above) asserts the ±100 value. If the HERO_GUILD-assignment gap is
     resolved as an accepted narrowing (item 4's second branch), that needs its **own** additional
     row/record — it is a structurally distinct behavior change (a code path removed, not a
     threshold value changed) from the ±50→±100 shift, and conflating them into one entry would
     under-document the actual behavior change per the Authoritative Mechanics Rule's Divergence
     requirement.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_influence.py tests/unit/world/test_stronghold.py \
       tests/unit/world/test_sovereignty_events.py -v
```

```
pytest tests/integration/world/test_regional_sovereignty.py -v
```

Fuller regression sweep before Verify (still scoped to the affected domain, not repo-wide):

```
pytest tests/unit/world/ tests/integration/world/ -v -m "not slow"
```

Never `pytest tests/` (repo-wide). Do not cherry-pick individual test function names into the
`test_scope_coverage_static` pytest_command — pass the real file paths/directories above.

## Anti-Drift Test Guards

- `test_world_dynamics_never_sets_owner_faction_id_independently` (above) — the direct guard
  against the dual-authority fix silently regressing into "both paths still write ownership," which
  is the exact defect this ticket exists to close. Without this test, a future change could
  reintroduce a second writer and nothing would catch it.
- `test_conquest_and_liberation_thresholds_match_across_both_paths` (above) — the direct guard
  against a future edit changing one threshold constant without the other, which is how this
  ticket's underlying bug was created in the first place (per investigation, both constants were
  actually introduced together in the same original commit, but nothing structurally prevented
  later independent drift).
- Whichever test resolves the HERO_GUILD-assignment open question (item 4 above) — guards against
  the most likely silent scope-creep failure mode for this specific ticket: deleting
  `WorldDynamicsSystem`'s conquest block cleanly, seeing most tests pass, and never noticing that
  `test_regional_ownership_flip` either broke or was quietly weakened to stop asserting
  `Faction.HERO_GUILD`.
- Re-running `tests/unit/world/test_stronghold.py` after updating its death counts guards against
  a subtler drift: if the implementer updates `CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` but
  forgets to update this file's fixture death counts, the tests will fail loudly (10 deaths no
  longer reaches -100.0) rather than silently passing against the wrong threshold — confirm this
  is the actual failure mode observed, not a pre-existing skip/xfail masking it.
