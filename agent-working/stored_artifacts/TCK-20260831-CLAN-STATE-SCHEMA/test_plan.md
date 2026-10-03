---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-CLAN-STATE-SCHEMA
artifact_type: test_plan
tags: [faction, social]
---

# Test Plan — TCK-20260831-CLAN-STATE-SCHEMA

## Regression Surface

This ticket is scoped to a standalone frozen dataclass addition in `src/core/state.py` — it does
**not** touch `AuthoritativeState`, `StateUpdate`, or `apply.py`. Regression surface is therefore
narrow: only tests that would break from an unrelated new class being added to `state.py`, or that
enumerate/hash the module's contents.

**Unit:**
- `tests/unit/domains/faction/test_faction_state.py` — must keep passing unmodified. `ClanState`
  must not share any symbol name, cache key, or import path with `FactionState`/`FactionUpdate`.
- `tests/unit/core/test_authoritative_state_contract.py` — `AuthoritativeState`'s field
  enumeration/isolation test. Must keep passing unmodified since this ticket does not add any
  field to `AuthoritativeState`.
- Any test that does `from src.core.state import *` or enumerates all dataclasses in the module
  (none found by direct grep as of this investigation — confirmed no such enumeration test exists
  today) would be a hazard if one is added later; not currently a regression risk.

**Integration:**
- `tests/integration/pipeline/test_state_isolation.py` — exercises `apply_generation()` round
  trips; must keep passing unmodified, since `ClanState` is not threaded through `apply.py`.

**Social/party lifecycle (must not be touched by this ticket at all — verifies no scope creep into Group):**
- `tests/unit/social/test_group_lifecycle_fields.py`
- `tests/unit/social/test_groups.py`
- `tests/unit/social/test_party_lifecycle.py`
- `tests/unit/social/test_party_composition.py`
- `tests/unit/social/test_party_coordination.py`
- `tests/unit/social/test_phantom_leader.py`
- `tests/unit/social/test_social_lifecycle.py`
- `tests/unit/social/test_social_party_regression.py`
- `tests/unit/social/test_domain_7_social.py`
- `tests/unit/social/test_social_phase7.py`
- `tests/unit/social/test_party_agency.py`
- `tests/unit/social/test_multi_hero.py`
- `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py`

These 13 files (90 test functions, see investigation.md) are the real "Party Formation & Lifecycle
precedent" — none of them import or exercise `ClanState`, and this ticket's diff should not touch
`src/systems/world_systems/groups.py` or `src/systems/social_systems/party_lifecycle.py` at all
(read-only investigation targets, not edit targets). Running them is a scope-creep guard, not a
functional dependency.

## New Tests Required

**File:** `tests/unit/domains/faction/test_clan_state.py` (new file, alongside the existing
`test_faction_state.py` in the same directory — that directory already has an `__init__.py`, no
new package init needed).

1. **`test_clan_state_serialization_round_trip`**
   - Category: unit
   - Verifies: `ClanState(...)` with all fields populated → `to_canonical_dict()` →
     `ClanState.from_dict()` round-trips to an equal object; `member_entity_ids`/`home_region_ids`
     survive JSON's list→tuple boundary as `tuple` (mirrors
     `test_faction_state_serialization_round_trip`'s `isinstance(restored.territory, tuple)`
     assertions).
   - Location: `tests/unit/domains/faction/test_clan_state.py`

2. **`test_clan_state_serialization_round_trip_defaults`**
   - Category: unit
   - Verifies: `ClanState(clan_id="x")` (all other fields defaulted) round-trips correctly;
     `member_entity_ids == ()`, `home_region_ids == ()`, `tension_level == 0.0`,
     `leader_entity_id is None`, `founded_tick == 0` (or whatever default Plan pins),
     `dissolved_tick is None` (mirrors `test_faction_state_serialization_round_trip_defaults`).
   - Location: `tests/unit/domains/faction/test_clan_state.py`

3. **`test_clan_state_is_frozen`**
   - Category: unit
   - Verifies: attempting to set any field on a constructed `ClanState` raises
     `dataclasses.FrozenInstanceError` (mirrors the `AuthoritativeState` frozen check pattern in
     `test_authoritative_state_has_factions_field`).
   - Location: `tests/unit/domains/faction/test_clan_state.py`

4. **`test_clan_state_canonical_dict_is_sorted_and_deterministic`**
   - Category: unit
   - Verifies: `to_canonical_dict()`'s `member_entity_ids`/`home_region_ids` (or any dict-shaped
     field, if `resources`-equivalent is added) are sorted/deterministic across two constructions
     with different insertion order but identical content — mirrors `FactionState`'s
     `dict(sorted(self.resources.items()))` guarantee. Guards against `ClanState`'s canonical form
     being non-deterministic across runs, which would break determinism law (CLAUDE.md Hard
     Rules: "Do not break determinism").
   - Location: `tests/unit/domains/faction/test_clan_state.py`

5. **`test_clan_state_does_not_touch_authoritative_state`**
   - Category: architecture guard
   - Verifies: `"clan" not in {f.name.lower() for f in dataclasses.fields(AuthoritativeState)}` and
     `"clan" not in {f.name.lower() for f in dataclasses.fields(StateUpdate)}` — a direct,
     executable guard for this ticket's explicit out-of-scope boundary (no `clans` field on
     `AuthoritativeState`, no `ClanUpdate`/`clan_updates` field on `StateUpdate`). This is the test
     most likely to catch accidental scope creep into idea 40/M4's territory, or a future ticket
     mistakenly assuming this one already wired it in.
   - Location: `tests/unit/domains/faction/test_clan_state.py`

6. **`test_clan_state_does_not_share_faction_state_identity`**
   - Category: unit / anti-drift
   - Verifies: `ClanState` and `FactionState` are distinct classes (`ClanState is not FactionState`),
     and a `ClanState` instance is not `isinstance(..., FactionState)` — guards against an
     implementation shortcut that aliases `ClanState = FactionState` or subclasses it in a way that
     would make the "dedicated parity ledger entry, not reusing SOC-166/228/230" requirement
     meaningless in practice.
   - Location: `tests/unit/domains/faction/test_clan_state.py`

7. **`test_social_narrative_parity_ledger_has_clan_state_entry`** (optional, if a
   parity-ledger-content test convention already exists for this shard — check
   `tests/tools/` for an existing `social_narrative.yaml` content-assertion test to follow the
   established pattern before adding a new one; do not invent a new ledger-testing convention if
   one already exists.)
   - Category: unit / doc-parity guard
   - Verifies: the new `SOC-25x` entry exists in `docs/parity_ledger/social_narrative.yaml`, has
     `status` and `priority` fields present, and (if `status in {"verified", "divergent"}`) has
     non-null `v2_evidence`/`test_path` per `schema.json`'s conditional `allOf` rule.
   - Location: `tests/tools/` (co-locate with existing parity-ledger schema/content tests if any
     exist; otherwise `tests/unit/domains/faction/test_clan_state.py`).

## Scoped Pytest Commands

```bash
# Primary — new ClanState unit tests
pytest tests/unit/domains/faction/test_clan_state.py -x -v

# Regression — sibling FactionState tests must be untouched
pytest tests/unit/domains/faction/ -x -v

# Regression — AuthoritativeState contract (guards against accidental field addition)
pytest tests/unit/core/test_authoritative_state_contract.py -x -v

# Anti-drift — Group/Party lifecycle must be completely unaffected
pytest tests/unit/social/ tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py -x -v -m "not slow"

# Full scoped run (all of the above together)
pytest tests/unit/domains/faction/ tests/unit/core/test_authoritative_state_contract.py tests/unit/social/ tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py -x -v -m "not slow"
```

## Anti-Drift Test Guards

| Guard | What It Catches |
|---|---|
| `test_clan_state_does_not_touch_authoritative_state` | Catches scope creep into idea 40/M4's `AuthoritativeState`/`StateUpdate` wiring territory, or a future ticket's implementer wrongly assuming this ticket already did that wiring. |
| `test_clan_state_does_not_share_faction_state_identity` | Catches an implementation shortcut (aliasing/subclassing `FactionState`) that would silently defeat the "dedicated parity entry, not reusing SOC-166/228/230" requirement. |
| Full `tests/unit/social/` regression run | Catches any accidental edit to `src/systems/world_systems/groups.py` or `src/systems/social_systems/party_lifecycle.py` — this ticket's investigation only reads these files for context; the diff must not touch them. |
| `test_clan_state_canonical_dict_is_sorted_and_deterministic` | Catches non-deterministic canonical-dict ordering, which would violate the project's determinism hard rule if `ClanState` is later hashed/checkpointed. |
| `pytest tests/unit/domains/faction/` (full directory, not just the new file) | Catches any accidental interference with `FactionState`'s existing serialization/`AuthoritativeState.factions` tests from adding a neighboring class in the same file. |
