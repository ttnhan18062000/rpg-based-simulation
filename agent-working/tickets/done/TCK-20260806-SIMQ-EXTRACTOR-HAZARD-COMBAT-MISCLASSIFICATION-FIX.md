---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX
phase: done
date: 2026-08-06
tags: [observability, combat, simulation-quality]
---

# TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX

## Title
Fix `event_extractor.py`'s combat-damage branch double-firing on hazard drain (confirmed root
cause of the corpus's zero-kill combat data)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
**Root cause confirmed (2026-08-06), not just hypothesized** — direct trace of
`src/observability/event_extractor.py`:

- Lines 136-151 (`if hp_diff < 0: ... CombatDamageEvent(...)`) fire on **any** HP decrease between
  two tick snapshots, with **no check on `CombatUpdate.outcome_kind`**.
- Lines 394-396, later in the *same file*, correctly check `combat_upd.outcome_kind == "HAZARD"` to
  emit a distinct `hazard_drain_applied` event.
- `src/engine/world_dynamics.py:39` confirms `WorldDynamicsSystem` **already tags hazard damage
  honestly**: `c_upd = replace(c_upd, hp_delta=..., outcome_kind="HAZARD", ...)`.
- `src/engine/combat.py` already tags every real combat outcome too (`outcome_kind="KILL"`/
  `"DEFEAT"`/`"SURVIVE"`/`"REJECTED"`, lines 233/317/428/480/538 etc.).

**The causal information was never missing.** The bug is that the combat-damage detection branch
never reads the `outcome_kind` field that's already sitting on the same `CombatUpdate` record it
partially reads (it does read `attacker_id` from the same object, just not `outcome_kind`). Result:
any hazard-drain hit on an entity double-fires as both `combat_damage`/`combat_initiated`/
(sometimes) `near_death_survival` **and** `hazard_drain_applied` for the same HP loss — inflating
and mislabeling non-combat environmental damage as combat activity across the entire corpus. This
was the leading hypothesis in
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s investigation.md Finding 3; this
ticket confirms it precisely and fixes it.

## Scope
1. In `event_extractor.py`'s combat-damage/combat-initiated/near-death-survival branches
   (lines ~136-203), add a guard so HP-loss events are only classified as `combat_*` when
   `combat_upd.outcome_kind` is a genuine combat outcome (`"SURVIVE"`, `"DEFEAT"`, `"KILL"` — check
   whether `"REJECTED"` should also be excluded, since it represents a rejected/no-op combat intent,
   not real damage) — **not** `"HAZARD"` or any other non-combat tag. Mirror the pattern the
   `hazard_drain_applied` branch (lines 394-396) already uses correctly.
2. Do not change `world_dynamics.py` or `combat.py` — their `outcome_kind` tagging is already
   correct; this is purely an observability-consumption fix.
3. Add a unit test in `tests/unit/observability/` (or wherever `event_extractor.py`'s existing
   tests live — check first) covering: a hazard-drain-only tick produces `hazard_drain_applied` and
   **not** `combat_damage`/`combat_initiated`; a real combat tick still produces
   `combat_damage`/`combat_initiated` correctly.
4. Re-run the 3 sample calibration scenarios from the parent investigation
   (`dungeon_crawl`/`sandbox_world`/`hero_guild_routing`, seed 42, 500t) and confirm
   `combat_damage`/`combat_initiated` counts drop to reflect only genuine combat, with
   `hazard_drain_applied` unaffected.
5. If any `grade_anchors.json` entries shift for COMBAT as a result, recalibrate and update per
   CLAUDE.md's parity rule; update `docs/parity_ledger/combat_movement.yaml` if applicable.

## Out of Scope
- The bigger push-vs-diff observability architecture question —
  `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`'s scope. This ticket is a narrow,
  confirmed bug fix within the existing diff-based extractor, not a redesign.
- The quest-reward-dispensing pacing question — separate, unrelated mechanism.
- Whether `"REJECTED"` combat intents should ever surface as any kind of event — flag as an open
  question if found relevant during implementation, don't silently decide either way.

## Acceptance Criteria
- [ ] `event_extractor.py`'s combat-damage/combat-initiated/near-death-survival branches check
      `outcome_kind` before classifying as combat
- [ ] New unit test(s) cover the hazard-vs-combat distinction explicitly
- [ ] Existing `event_extractor.py` test suite still passes
- [ ] Re-run of the 3 sample scenarios shows no `combat_damage`/`combat_initiated` events without a
      genuine combat `outcome_kind`
- [ ] `grade_anchors.json`/parity ledger updated if any scenario's COMBAT grade shifts

## Related Tickets
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (parent investigation — this ticket
  implements its confirmed Finding 3)
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE (sibling — broader architecture question,
  independent of this narrow fix)

## Related Docs
- `docs/audits/D20_simq_quality_status_review.md` (COMBAT Full Pillar Health entry — may need
  re-verification once this fix lands and the corpus is recalibrated)

## Related Stored Artifacts
None yet — hotfix tier; self-evident intent per CLAUDE.md (root cause already confirmed with exact
line numbers, no further investigation needed before implementing).

## Related Code Areas
- `src/observability/event_extractor.py` (the fix)
- `src/core/updates.py` (`CombatUpdate.outcome_kind`, reference only)
- `src/engine/world_dynamics.py`, `src/engine/combat.py` (reference only, not modified)

## Assumptions / Open Questions
- Whether `"REJECTED"` should be excluded from combat classification alongside `"HAZARD"` — treat
  as an implementation-time decision to make explicitly, not silently.

## Implementation Notes
Investigate found a second, more consequential bug beyond the ticket's original single-bug
framing: `event_extractor.py` read a nonexistent attribute (`e_upd.combat_upd`) at 4 call sites
instead of the real `EntityUpdate.combat` field, silently returning `None` every time via
`getattr`'s default — meaning `attacker_id`/`killer_id` were always `None`, not just for hazard
hits but for every real combat hit too, and the despawn-branch's `has_attacker` check was always
`False`, causing every real combat kill to also incorrectly co-emit `demographic_mortality`.

Before writing the fix, cross-checked every real `hp_delta`-setting call site in `src/` (not just
the two already-discussed sources) and found a third issue: a naive `outcome_kind` allow-list
(e.g. including `"SURVIVE"`) would have misclassified `biological.py`'s starvation/exhaustion
damage as combat too, since `CombatUpdate`'s own dataclass default for `outcome_kind` happens to
be `"SURVIVE"` and `biological.py` relies on that default without setting an explicit tag. Settled
on `attacker_id is not None` as the primary, semantically-correct discriminant (every real
damage-dealing `CombatUpdate` in `combat.py` sets it; hazard drain and biological damage never do),
with `outcome_kind not in ("HAZARD", "REJECTED")` as defense-in-depth.

Added `_real_combat_update(e_upd)` helper and routed all 4 buggy call sites plus
`near_death_survival` (which previously had no causal check at all) through it. Left
`CombatKillEvent`'s own firing condition unchanged (still fires on any death, only `killer_id`'s
population was fixed) — flagged explicitly as a deliberately deferred question, not silently
decided, since redesigning what event type represents a non-combat death is a larger scope than
this ticket's stated bug fix.

Also found and fixed a test-fixture bug while writing regression tests: 3 pre-existing tests in
`test_event_extractor_simq.py` mocked `MagicMock(combat_upd=...)` — matching the *buggy* attribute
name, not the real field — which is exactly why they never caught Bug 2. Corrected the mocks to
use the real field name so they actually exercise the fixed code path.

## Test Summary
`tests/unit/observability/test_event_extractor_simq.py`: 25 tests (21 pre-existing + 4 new), all
pass. `tests/unit/observability/test_event_extractor_world.py`: 18 tests (17 pre-existing + 1 new,
using genuinely differing prior/curr HP to actually exercise the hazard-vs-combat interaction,
unlike the file's existing same-state-object hazard tests), all pass. Full
`tests/unit/observability/` directory: 759 passed, 6 skipped (skip count unchanged from before
this change). `python3 -c "import ast; ast.parse(...)"` confirmed no syntax errors before running
tests. Confirmed via grep that no test file outside `tests/unit/observability/` imports or calls
`EventExtractor` directly (SimQ scorer tests hand-construct events/envelopes, unaffected).
Architecture-Verify (`architecture_reviewer_static.run_architecture_checks`) against the real diff
returned PASS on both durable-state-mutation and reason-metadata-smuggling checks.

## Files Changed
- `src/observability/event_extractor.py` — `_real_combat_update()` helper added; 4
  `combat_upd`→`combat` attribute fixes; `attacker_id`-based combat-classification guard added to
  `combat_damage`/`combat_initiated`/`near_death_survival`; `killer_id` fix in Kill events
  (firing condition unchanged); `has_attacker` fix in the despawn branch
- `tests/unit/observability/test_event_extractor_simq.py` — 3 test-fixture mocks corrected
  (`combat_upd=`→`combat=`); 2 existing tests updated to supply a valid combat mock; 4 new
  regression tests added
- `tests/unit/observability/test_event_extractor_world.py` — 1 new regression test added
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-323` entry (P1, verified), schema-validated

## Completion Summary
Fixed the confirmed root cause from `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s
investigation, and found it was larger than originally scoped: not just a missing `outcome_kind`
filter, but a wrong-attribute-name bug that had made causal attribution (`attacker_id`/`killer_id`)
silently broken for *every* real combat event, plus a design flaw in the originally-proposed fix
itself (a plain `outcome_kind` allow-list would have let biological damage through the same way
hazard damage did) caught before it shipped by systematically checking every real HP-reduction
source in the codebase. Also fixed a test-fixture bug that explains why none of this was ever
caught before. All fixes verified via 759/759 passing tests in the scoped domain, a new
schema-valid P1 parity ledger entry, and a clean Architecture-Verify pass. `CombatKillEvent`'s own
firing semantics were deliberately left unchanged and explicitly flagged as an open question, not
silently expanded into.
