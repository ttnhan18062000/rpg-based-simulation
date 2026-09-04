---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION
artifact_type: test_plan
tags: [faction, social]
---

# Test Plan — TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Regression Surface

**Unit — Clan schema (must keep passing unmodified except the one AC-mandated rewrite):**
- `tests/unit/domains/faction/test_clan_state.py`
  - `test_clan_state_serialization_round_trip` — unaffected, keep passing.
  - `test_clan_state_serialization_round_trip_defaults` — unaffected, keep passing.
  - `test_clan_state_is_frozen` — unaffected, keep passing.
  - `test_clan_state_canonical_dict_is_sorted_and_deterministic` — unaffected, keep passing.
  - `test_clan_state_does_not_share_faction_state_identity` — unaffected, keep passing.
  - `test_clan_state_does_not_touch_authoritative_state` — **must be replaced** (AC, explicit) —
    see New Tests Required below; this is the one intentional regression-surface change.

**Unit — FactionState wiring precedent (must NOT regress; proves Clan wiring didn't corrupt the
shared `AuthoritativeState`/`StateUpdate`/`apply.py` machinery it extends):**
- `tests/unit/domains/faction/test_faction_state.py` (all 9 tests) — especially
  `test_authoritative_state_has_factions_field`, `test_faction_update_apply_tension_delta`,
  `test_state_update_merge_faction_updates`, `test_state_update_is_noop_with_faction_updates`,
  `test_faction_state_factions_persist_across_ticks`. `apply.py`'s faction-merge block
  (`src/engine/apply.py:351-377`) and `StateUpdate.merge_many()`'s faction accumulator
  (`src/core/updates.py:1082,1151-1153,1216`) sit immediately adjacent to the new Clan code paths
  in both files — a copy-paste or ordering mistake there is the most likely way this ticket
  silently breaks Faction wiring.

**Unit — Group lifecycle (must NOT regress; explicitly out of scope, proves no accidental shared-
helper coupling to Group's own leadership/dissolution/defection logic):**
- `tests/unit/social/test_party_lifecycle.py` (all 22 tests) — especially
  `test_leadership_election_picks_highest_sociability`,
  `test_leadership_no_election_when_diff_below_threshold` (the 0.2-margin gate Clan succession must
  NOT inherit), `test_betrayal_desertion_dissolution_on_single_member`.
- `tests/unit/social/test_groups.py` (all 3 tests) — especially `test_group_dissolution` (Group's
  unconditional dead-leader dissolution, SOC-176/SOC-189, must stay unconditional).

**Unit — Social contract appraisal (must NOT regress; the shared trust prelude and every other
`ContractKind` dispatch branch must be untouched by adding `CLAN`):**
- `tests/unit/social/test_appraisal_logic.py` (full file) — proves the shared prelude
  (`appraisal.py` lines 47-54) and existing `TEACH`/`MARRIAGE`/`TEAM_UP`/etc. dispatch branches
  are unaffected by the new `CLAN` branch.
- `tests/unit/social/test_marriage.py` (full file) — the most structurally similar precedent
  (`ContractKind` + `appraise_contract()` + durable-record-on-`ACCEPTED` pattern); must keep
  passing untouched to prove the new Clan dispatch branch didn't perturb the marriage branch's
  behavior or the shared dispatch `if`/`elif` chain in `appraise_contract()`.

**Integration (if any exist covering the authoritative apply-path or faction/social pipeline
phases) — run to catch cross-cutting apply-path breakage:**
- `tests/integration/scenarios/test_faction_campaign.py` — exercises the same `apply.py`
  Faction-merge code path this ticket's Clan-merge code sits beside.

## New Tests Required

Per acceptance criteria (ticket ACs numbered 1-7 in order):

**AC 1 — Clan succession, no sociability-margin gate:**
- `test_clan_succession_promotes_highest_sociability_on_leader_death` — unit — verifies that when
  the current `leader_entity_id` is dead/inactive, the highest-sociability surviving member (per
  `entity.identity.personality.sociability`) is promoted to `leader_entity_id`, with **no** 0.2
  margin requirement (i.e. promotion fires even when the new leader's sociability exceeds no one
  by any margin, since the old leader is gone entirely and there's no "current" sociability to
  beat) — lives in a new `tests/unit/domains/faction/test_clan_succession.py`.
- `test_clan_succession_lowest_id_tiebreak_on_equal_sociability` — unit — mirrors
  `test_leadership_election_picks_highest_sociability`'s tiebreak assertion but for the
  margin-free Clan rule — same file.
- `test_clan_succession_no_promotion_when_leader_alive` — unit — a living, active leader is never
  replaced by this path (only Marriage-style "succession," not a re-election mechanic) — same file.
- `test_clan_succession_same_tick_death_effective_state` — unit — mirrors
  `GroupSystem.update_groups()`'s `is_alive`/`is_active` same-tick-effective-state pattern
  (`groups.py:32-57`): a leader who dies earlier in the *same* tick (via a same-tick
  `CombatUpdate(alive_set=False)` in a passed-in `StateUpdate`) must trigger succession using the
  same-tick state, not the stale start-of-tick state — same file.
- `test_clan_succession_no_surviving_members_defers_to_dissolution_check` — unit — when the leader
  dies and no members remain scoreable, succession does not crash/promote a phantom leader; control
  passes to the (separate) dissolution check — same file.

**AC 2 — Dissolution only when member_entity_ids AND assets/footprint both empty:**
- Test names depend on the Plan-phase resolution of Risk #1 (schema field vs. AC scope-down) — this
  test_plan specifies the **shape** of the required coverage under each resolution so Plan can pick
  one without re-deriving test design:
  - If a schema field is added (Option a): `test_clan_dissolves_when_members_and_assets_both_empty`,
    `test_clan_does_not_dissolve_when_only_members_empty`,
    `test_clan_does_not_dissolve_when_only_assets_empty` — unit — same new
    `test_clan_succession.py` or a sibling `test_clan_dissolution.py`.
  - If scoped down to `member_entity_ids`-only (Option b): `test_clan_dissolves_when_members_empty`
    plus an explicit test asserting the deferred half is documented, not silently dropped (e.g.
    a doc-presence assertion or simply a code comment cross-checked in review — testing "the AC was
    scoped down and recorded" is a doc-completeness concern, not a unit-test concern; do not invent
    a test for an intentionally-deferred field).
  - **Do not write this test until Plan has made the call** — writing it against a guessed field
    name risks locking in the wrong shape.

**AC 3 — Clan joining routes through `appraise_contract()`, prelude untouched:**
- `test_clan_join_routes_through_appraise_contract` — unit — asserts the new `_appraise_clan()` (or
  equivalent) dispatch branch is reached via `ContractKind.CLAN` in `appraise_contract()`'s
  `if`/`elif` chain, mirroring `test_marriage.py`'s equivalent coverage for `MARRIAGE` — new
  `tests/unit/social/test_clan_appraisal.py` or extend `test_appraisal_logic.py`.
- `test_clan_join_shared_trust_prelude_still_cancels` — unit — a low-trust/high-betrayal entity is
  still hard-cancelled by the shared prelude (lines 47-54) for a `CLAN` contract, exactly as for
  every other kind — proves the prelude wasn't bypassed or duplicated — same file.
- `test_clan_join_never_silently_auto_composes` — unit/architecture guard — asserts there is no
  code path that adds an entity to `ClanState.member_entity_ids` without going through
  `appraise_contract()` first (e.g. by asserting the only test-covered call sites that produce a
  `ClanUpdate` with a membership addition go through the appraisal function) — same file.

**AC 4 — Clan leaving removes member via typed update + emits event:**
- `test_clan_leave_removes_entity_via_clan_update` — unit — asserts leaving produces a `ClanUpdate`
  (not a direct `ClanState.member_entity_ids` mutation) that, once applied via `ApplyPath`, no
  longer contains the leaving entity — new `tests/unit/domains/faction/test_clan_lifecycle.py`
  (or wherever the Plan phase places the leave-service).
- `test_clan_leave_emits_clan_specific_event` — unit — asserts the new Clan-leave event class
  (mirroring `BetrayalDesertionEvent`'s shape) is emitted with the correct `entity_id`/`clan_id`
  payload — same file.
- `test_clan_leave_never_mutates_clan_state_directly` — architecture guard — mirrors this
  project's "Decision logic reads state, does not authoritatively mutate durable state" rule;
  assert the leave-service function returns typed records only and does not call
  `object.__setattr__`/direct field assignment on any `ClanState` instance.

**AC 5/6 — Doc and test-rewrite ACs are not independently unit-testable**, but are covered
indirectly:
- The `intentional_divergences.md` §2.48 Status flip and the `test_clan_state_does_not_touch_authoritative_state`
  replacement are verified by `done-checker`'s doc-coverage and frontmatter checks, and by the
  rewritten test itself (below) — not by new pytest assertions beyond what's already listed.

**Replacing the stale test (Investigation's "Current Behavior" section, exact required rewrite):**
- `test_clan_state_is_wired_into_authoritative_state` (name TBD by Plan/Implementer, following the
  `test_faction_state.py::test_authoritative_state_has_factions_field` precedent) — unit — replaces
  `test_clan_state_does_not_touch_authoritative_state` in
  `tests/unit/domains/faction/test_clan_state.py`. Must assert:
  - `AuthoritativeState(tick=0, seed=0)` has a `clans`-equivalent field, defaulting to `{}`.
  - `dataclasses.fields(AuthoritativeState)` contains the new field name.
  - `dataclasses.fields(StateUpdate)` contains the new `ClanUpdate`-list field name.
  - Constructing `AuthoritativeState(tick=1, seed=0, clans={"x": ClanState(clan_id="x")})` round-
    trips through `state2.clans["x"]`.
  - `AuthoritativeState.clans` (or equivalent) raises `FrozenInstanceError` on direct assignment.

**Wiring-mechanics tests (mirroring every `test_faction_state.py` test 1:1 for Clan), covering the
6 touch points identified in the investigation:**
- `test_authoritative_state_has_clans_field` — unit — mirrors
  `test_authoritative_state_has_factions_field` exactly.
- `test_clan_update_apply_<field>_delta` (one per mutable field the Plan phase adds to
  `ClanUpdate` — e.g. tension delta if `tension_level` gets a delta-style mutator) — unit — mirrors
  `test_faction_update_apply_tension_delta`.
- `test_clan_update_membership_add_remove` — unit — mirrors
  `test_faction_update_territory_add_remove`'s add/remove-in-one-update shape, but for
  `member_entity_ids`.
- `test_clan_update_is_noop` — unit — mirrors `test_faction_update_is_noop`.
- `test_state_update_merge_clan_updates` — unit — mirrors `test_state_update_merge_faction_updates`.
- `test_state_update_is_noop_with_clan_updates` — unit — mirrors
  `test_state_update_is_noop_with_faction_updates`.
- `test_clan_state_persists_across_ticks` — unit — mirrors
  `test_faction_state_factions_persist_across_ticks`, using `ApplyPath.apply_generation`.

All new wiring-mechanics tests live in `tests/unit/domains/faction/test_clan_state.py` (extending
the existing file, consistent with where `test_faction_state.py` lives relative to
`FactionState`) unless the file grows unwieldy, in which case a sibling
`test_clan_wiring.py` in the same directory is acceptable — Plan phase's call.

## Scoped Pytest Commands

Never `pytest tests/`. Scope to the Clan/Faction/Social domains this ticket touches:

```
pytest tests/unit/domains/faction/ -x -v
pytest tests/unit/social/ -x -v
pytest tests/integration/scenarios/test_faction_campaign.py -x -v
```

Targeted re-run of just the new/changed surface during development:
```
pytest tests/unit/domains/faction/test_clan_state.py tests/unit/domains/faction/test_clan_succession.py tests/unit/domains/faction/test_clan_lifecycle.py tests/unit/social/test_clan_appraisal.py -x -v
```
(adjust filenames once Plan/Implementer finalize the actual module layout — the investigation
above proposes but does not mandate these exact paths).

Full Faction/Group/Social regression pass before Verify:
```
pytest tests/unit/domains/faction/ tests/unit/social/ tests/unit/world/ -m "not slow" -v
```
(include `tests/unit/world/` only if the Plan phase's succession-trigger placement touches
`src/systems/world_systems/groups.py`'s pipeline neighbor — otherwise omit; do not widen the scope
speculatively.)

## Anti-Drift Test Guards

- **`test_leadership_no_election_when_diff_below_threshold` (existing, `test_party_lifecycle.py`)
  must keep passing unmodified** — it is the direct regression guard proving Group's 0.2-margin
  gate is untouched by adding Clan's margin-free succession rule alongside it.
- **`test_group_dissolution` (existing, `test_groups.py`) must keep passing unmodified** — direct
  regression guard proving Group's unconditional dead-leader dissolution (SOC-176/SOC-189) was not
  quietly changed to a succession model by code reuse with the new Clan succession logic.
- **A new architecture-guard test should assert `PartyLifecycleService.check_leadership` and
  `GroupSystem.update_groups` source do not import or call any new Clan-succession function**, or
  equivalently, that the new Clan succession function lives in its own module and is not invoked
  from `party_lifecycle.py`/`groups.py` — catches accidental shared-code coupling between Group and
  Clan lifecycle paths that the ticket's Out-of-Scope section forbids.
- **`test_appraisal_logic.py`'s existing prelude-cancellation tests (trust < 0.2, betrayal history)
  must keep passing unmodified** — direct regression guard proving the shared prelude
  (`appraisal.py` lines 47-54) was not edited or duplicated when adding the `CLAN` dispatch branch.
- **A new test should assert `ContractKind.CLAN` (once added) does not reuse or alias
  `ContractKind.RECRUITMENT`** — RECRUITMENT already exists and has an entirely different
  utility/pay-based appraisal model (`_appraise_recruitment`); catches an implementer shortcut of
  routing Clan joining through the existing recruitment appraisal instead of building the
  ticket-mandated new branch.
- **A new test should assert idea-68 fields (any new diplomacy/alliance/war-adjacent field on
  `ClanState`) do not exist** — mirrors `test_clan_state_does_not_share_faction_state_identity`'s
  spirit of guarding schema identity; guards against the ticket's own flagged
  Inter-Clan-Relations scope-creep risk by asserting the `ClanState`/`ClanUpdate` field set stays
  exactly what Plan specifies, no more.
- **`docs/parity_ledger/social_narrative.yaml`'s SOC-228/SOC-230 entry text must remain byte-
  identical** (a parity-ledger diff review item, not a pytest assertion) — since this ticket must
  not describe Clan behavior under Group's existing verified entries.
