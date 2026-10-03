---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
artifact_type: test_plan
tags: [social]
---

# Test Plan — TCK-20260904-CLAN-REPUTATION-ASSOCIATION

## Regression Surface

**Unit — faction/clan domain** (`tests/unit/domains/faction/`):
- `test_clan_state.py` — **must be updated, not just kept passing.** `test_clan_state_no_new_idea68_fields`
  (lines 206-223) asserts the exact `ClanState`/`ClanUpdate` field sets; adding `clan_reputation` (and any
  `ClanUpdate` delta field) will fail this test until its literal set is extended in the same change.
  `test_clan_state_serialization_round_trip*`, `test_clan_state_canonical_dict_is_sorted_and_deterministic`,
  `test_clan_update_is_noop`, `test_clan_update_membership_add_remove`, `test_state_update_merge_clan_updates`,
  `test_clan_state_persists_across_ticks` must all keep passing unmodified in behavior (only the new-field
  literal assertion changes).
- `test_clan_succession.py`, `test_clan_lifecycle.py` — must keep passing unmodified; this ticket does not
  touch succession/dissolution logic.
- `test_faction_state.py` — regression only (FactionState is a sibling pattern, untouched).

**Unit — social systems** (`tests/unit/social/`):
- `test_clan_appraisal.py` — must keep passing; covers `_appraise_clan()`/`ContractKind.CLAN`, a different
  code path from the stranger-judgment blend this ticket modifies in `appraise_contract()`.
- `test_appraisal_logic.py` — covers `appraise_contract()`'s existing trust-blend formula (bond vs. no-bond
  branches); the no-bond branch is exactly what this ticket extends — must keep passing with the *pre-clan*
  behavior preserved when the observed entity has no clan (clan_reputation defaults to a neutral value).
- `test_betrayal_consequence.py` — covers `SocialAppraisalSystem.process_betrayal()`; regression only
  unless the implementer chooses to hook the clan update onto this path instead of `contracts.py`'s
  `resolve_contract_outcome()` (Plan-phase decision per investigation's Open Question).
- `test_contract_lifecycle.py`, `test_contract_lifecycle_phase7.py`, `test_social_contracts.py`,
  `test_social_phase7.py` — cover `ContractService.resolve_contract_outcome()` including its `betrayal=True`
  branch (contracts.py:227-231); must keep passing with the existing `notoriety_delta=0.5`/
  `betrayal_increment=1` behavior on the entity-level `SocialUpdate` unchanged — the new `ClanUpdate` is
  additive, not a replacement.
- `test_social_party_regression.py` — covers `PartyLifecycleService.check_defection()`'s `notoriety_delta=2.0`
  entity-level effect; must keep passing unchanged for entities not in a clan, and unchanged at the
  entity-`SocialUpdate` level even for clan members (the `ClanUpdate` is a separate, additive output).
- `test_relationships.py`, `test_reputation_learning.py`, `test_source_trust.py` — regression only
  (`RelationshipService.process_update()` / `SocialComponent` mutation paths, untouched by this ticket).

**Architecture guards** (`tests/architecture/`):
- `test_social_write_paths.py` — must keep passing unmodified. Its repo-wide scan for
  `public_reputation=`/`regional_reputation=` writes outside the allowlist already provides defense-in-depth
  against this ticket accidentally writing a member's own `public_reputation` while wiring clan reputation.

**Apply-path / engine**:
- `tests/unit/core/test_p1_semantic_hardening.py` — touches `resolve_contract_outcome`/`betrayal_increment`;
  regression only.
- Any existing `apply.py` clan-merge tests (covered within `test_clan_state.py`'s
  `test_clan_update_membership_add_remove`/`test_clan_state_persists_across_ticks`) — must keep passing;
  the new `clan_reputation` apply-path branch must not alter `member_entity_ids`/`leader_entity_id`/
  `dissolved_tick` merge behavior.

## New Tests Required

1. **`test_clan_state_clan_reputation_serialization_round_trip`**
   - Category: unit
   - Verifies: `ClanState.clan_reputation: float` round-trips through `to_canonical_dict()`/`from_dict()`,
     including a non-default value and the class default, mirroring
     `test_clan_state_serialization_round_trip`/`test_clan_state_serialization_round_trip_defaults`.
   - Location: `tests/unit/domains/faction/test_clan_state.py`

2. **Update `test_clan_state_no_new_idea68_fields`** to include `clan_reputation` (and any new
   `ClanUpdate` field, e.g. `clan_reputation_delta`) in its literal expected field sets.
   - Category: unit (guard maintenance)
   - Location: `tests/unit/domains/faction/test_clan_state.py`

3. **`test_contract_betrayal_produces_clan_reputation_clan_update`** (name indicative — match final
   implementation's hook point)
   - Category: unit
   - Verifies: a contract-betrayal outcome (via whichever function ends up owning the hook — either
     `ContractService.resolve_contract_outcome(betrayal=True, betrayer_id=...)` or its wired caller)
     produces both the existing entity-level `SocialUpdate(notoriety_delta=0.5, betrayal_increment=1)`
     AND a `ClanUpdate` with a nonzero reputation delta for the betrayer's clan, only when the betrayer
     is confirmed to be in a clan (no ClanUpdate, or a no-op one, when the betrayer has no clan).
   - Location: `tests/unit/social/test_contract_lifecycle.py` or `test_betrayal_consequence.py`
     (co-locate with whichever function is actually extended)

4. **`test_party_defection_produces_clan_reputation_clan_update`**
   - Category: unit
   - Verifies: `GroupPhase.resolve()` (or wherever the real hook lands, per investigation) produces the
     existing entity-level `notoriety_delta=2.0` on defection AND a measurable `ClanUpdate` change to
     `clans[clan_id].clan_reputation` for the defector's clan, applied only through `apply.py`'s
     `clan_updates` merge path (assert via `ApplyPath.apply_partial`/`apply_generation`, not by reading
     the raw `ClanUpdate` object's field value alone — AC2 explicitly requires the *applied* state to
     change).
   - Location: `tests/unit/social/test_social_party_regression.py` or a new
     `tests/unit/domains/faction/test_clan_reputation_association.py`

5. **`test_stranger_judgment_incorporates_clan_reputation`**
   - Category: unit
   - Verifies: `appraise_contract()` (or the specific trust-blend helper it calls) produces a
     distinguishably different `trust_score` for an observer with **no** `SocialBond` toward a clan
     member when that member's clan has a low vs. high `clan_reputation`, and that the same observer's
     judgment of a member they **do** have a `SocialBond`/direct history with is unaffected by clan
     reputation (bond-present branch stays clan-blind, per the current `if bond: ... else: ...` structure
     at appraisal.py:39-45).
   - Location: `tests/unit/social/test_appraisal_logic.py`

6. **`test_clan_reputation_aggregation_is_deterministic`**
   - Category: unit / determinism
   - Verifies: any propagation/aggregation logic that iterates `ClanState.member_entity_ids` (or does an
     O(n_clans) reverse-lookup scan over `state.clans`) produces bit-identical `ClanUpdate` output across
     repeated runs with the same input state — construct a `ClanState`/`AuthoritativeState` fixture with
     `member_entity_ids` in a non-sorted insertion order and assert output is independent of that order.
   - Location: `tests/unit/domains/faction/test_clan_reputation_association.py` (new file) or
     `test_clan_state.py`

7. **`test_no_writes_to_member_public_reputation_from_clan_reputation_code`** (AC5 source-text guard)
   - Category: architecture guard
   - Verifies: the specific new source file(s)/functions implementing clan-reputation wiring contain no
     `public_reputation=` write (using `inspect.getsource()` on the specific new function(s), the same
     technique as the existing `test_reputation_seed_write_path_does_not_reference_reputation_update_service`
     in `test_social_write_paths.py`, or by extending that file's own repo-wide scan/allowlist if the new
     code lands in an already-covered file). Must fail loudly if a future edit accidentally propagates
     clan reputation onto individual members' `SocialComponent.public_reputation`.
   - Location: `tests/architecture/test_social_write_paths.py` (extend) or a new
     `tests/architecture/test_clan_reputation_write_paths.py`

## Scoped Pytest Commands

Primary regression + new-test verification (bare test directories, not cherry-picked files — required by
the later Test phase's structural test-scope-coverage backstop):

```
pytest tests/unit/domains/faction/ tests/unit/social/ tests/architecture/test_social_write_paths.py -v
```

If a new dedicated file is created for clan-reputation-specific tests (recommended:
`tests/unit/domains/faction/test_clan_reputation_association.py`), it is already covered by the
`tests/unit/domains/faction/` bare-directory scope above — no separate command needed.

Engine/apply-path sanity (only if the apply.py clan-merge branch changes are broad enough to warrant
direct engine-level coverage beyond the domain/social unit tests above):

```
pytest tests/unit/core/test_p1_semantic_hardening.py -v
```

Do not run `pytest tests/` — scope to the domains above per repo Testing Rule.

## Anti-Drift Test Guards

- **`test_clan_state_no_new_idea68_fields`**, once updated with the new field(s), continues to function
  as the guard against idea 68 (Inter-Clan Relations) scope creep — any accidental addition of a
  `tension_level`-interaction or diplomacy-adjacent field alongside `clan_reputation` will now fail this
  test, exactly as intended.
- **`tests/architecture/test_social_write_paths.py`**'s existing repo-wide scan is itself an anti-drift
  guard for this ticket even without modification — it will catch any accidental new
  `public_reputation=`/`regional_reputation=` write introduced by clan-reputation code landing outside
  its allowlist, satisfying AC5's spirit as a second, independent layer beneath the new dedicated test.
- **The bond-present branch of `appraise_contract()`** should get an explicit regression assertion (not
  just relying on existing `test_appraisal_logic.py` coverage) that clan reputation does **not** leak into
  judgment of a member the observer has direct history with — this is the "distinguishably different"
  half of AC3 and is the easiest part of this ticket to accidentally get backwards (blending clan
  reputation into both branches instead of only the stranger branch).
- **A defection/betrayal test with a betrayer who has no clan** (not just the clan-member case) guards
  against a crash or an accidental erroneous `ClanUpdate` (e.g. targeting a `clan_id=None`/empty string)
  when the O(n_clans) reverse-lookup finds no match — this exercises the reverse-lookup gap's "no match"
  path, not just its "match found" path.
- **A determinism test with multiple clans and multiple qualifying members** (not just one clan/one
  member) guards against an unsorted `state.clans.items()` iteration silently producing
  order-dependent `ClanUpdate` list ordering, which would be a real (if subtle) determinism regression
  the way SOC-264's existing sorted-merge patterns were designed to prevent.
