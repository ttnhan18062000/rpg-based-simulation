---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260904-LINEAGE-DEATH-DISPATCH
artifact_type: plan
tags: [lifecycle, social]
---

# Plan — TCK-20260904-LINEAGE-DEATH-DISPATCH

## Ordered Steps

1. **Add `NamedIntentionBundle` and wire it onto `MotivationModel`** (`src/core/cognition.py`).
   New frozen dataclass: `text`, `source_entity_id`, `created_tick`, `status` (default `"PENDING"`),
   `to_canonical_dict()`, `empty()`. Add `named_intention: NamedIntentionBundle` field to
   `MotivationModel`, include it in `MotivationModel.to_canonical_dict()`. No `checkpoint.py` change
   needed -- `CognitionModel.to_canonical_dict()` already delegates recursively through
   `motivation.to_canonical_dict()`.
2. **Add `LifecycleSystem._transfer_inherited_feud()`** (`src/systems/lifecycle_systems/
   lifecycle.py`, idea 55). Reads `deceased.strategic.blockers` for `nemesis_*` ids, builds weakened
   copies (`severity * INHERITED_NEMESIS_SEVERITY_MULTIPLIER`, id `inherited_nemesis_{antagonist}`),
   returns `heir_upd` with `strategic.blockers_add_or_update` extended (using `heir_upd.strategic or
   StrategicUpdate()` — never overwriting an existing `strategic` update on the heir).
3. **Add `LifecycleSystem._seed_dying_wish()`** (idea 58). Read-through-then-replace on
   `heir_upd.cognition_bundle_set` (falling back to `heir.cognition`), replaces only
   `motivation.named_intention`, writes back via `cognition_bundle_set`. Deterministic wish text:
   references the deceased's active nemesis antagonist if `_transfer_inherited_feud` found one,
   otherwise a generic remembrance string.
4. **Wire the dispatch call into `resolve_lifecycle`**. Insert both handler calls right after
   `heir_upd = refined_entity_updates.get(heir_id, EntityUpdate(entity_id=heir_id))` and before the
   existing heirloom-transfer block. Move the final `refined_entity_updates[heir_id] = heir_upd`
   assignment to run unconditionally at the end of the `if heir:` block (the pre-existing code only
   wrote it back inside `if all_transfer_items:` -- now that the dispatch handlers may modify
   `heir_upd` even with zero heirlooms, this must run unconditionally to avoid silently dropping
   their writes).
5. **Tests** -- 6 new tests in `tests/unit/progression/test_lifecycle.py` per test_plan.md.
6. **Docs** -- new Section 12 in `docs/mechanics/04_strategic_cognition.md`; parity ledger entries
   COMB-321, SOC-265, STRAT-270.

## Files to Change

- `src/core/cognition.py` (new `NamedIntentionBundle`, `MotivationModel.named_intention`)
- `src/systems/lifecycle_systems/lifecycle.py` (two new handlers + dispatch wiring)
- `tests/unit/progression/test_lifecycle.py` (6 new tests)
- `docs/mechanics/04_strategic_cognition.md` (new Section 12)
- `docs/parity_ledger/combat_movement.yaml`, `docs/parity_ledger/social_narrative.yaml`,
  `docs/parity_ledger/strategic_cognition.yaml` (new entries)

## Explicit Scope Guards (what NOT to touch)

- `src/core/models/social.py` (`SocialComponent.nemesis_ids`/`grudge_history`) -- always-live legacy
  mechanism, out of scope, tracked separately by `TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`.
- `src/core/strategic.py` (`CommittedIntention`) -- the existing "Intention" concept, untouched.
- Any `SocialComponent.public_reputation` / `PublicReputationProfile` / `ReputationUpdateService`
  reference -- the reputation branch's own concern, guarded by a dedicated source-text test.
- No new feature flag -- unlike several recent M4 tickets, this mechanism has no meaningful
  "default OFF, opt-in ON" toggle point: it fires unconditionally inside the death path once
  `heir_entity_id` resolves, and is naturally inert (idea 55) or minimally intrusive (idea 58,
  writes a field nothing else reads) when its trigger data is absent.

## Dependency Map Between Steps

Step 1 (cognition model) must land before step 3 (`_seed_dying_wish` imports `NamedIntentionBundle`)
and step 4 (dispatch wiring calls both handlers). Steps 2 and 3 are independent of each other. Step 5
(tests) and step 6 (docs) both depend on steps 1-4 being complete.

## Acceptance Criteria Map

| AC | Step |
|---|---|
| Single dispatch call | Step 4 |
| Weakened feud transfer | Step 2 |
| Named intention honorable/round-trip | Step 1, 3 |
| Same-tick collision safety | Step 3 |
| No reputation-branch changes | Steps 2-4 (verified by guard test in Step 5) |

## Unresolved Questions

None -- all Plan-phase decisions flagged as open in the ticket's own "Assumptions / Open Questions"
section (weakening multiplier, wish-content-selection logic, granular-patch-vs-read-through-replace
choice) are resolved above with rationale.
