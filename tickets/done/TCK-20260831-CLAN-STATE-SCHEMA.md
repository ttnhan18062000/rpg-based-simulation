---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-CLAN-STATE-SCHEMA
phase: done
date: 2026-08-31
tags: [faction, social]
---

# TCK-20260831-CLAN-STATE-SCHEMA

## Title
Define ClanState schema reusing FactionState's shape

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Reuse FactionState's shape almost verbatim for a new ClanState. This ticket is schema/shape wiring only — lifecycle actions (formation, dissolution, succession) belong to idea 40 in M4, which targets the same ClanState class and must not race with this ticket over the same dataclass.

## Scope
- Add a new ClanState frozen dataclass (clan_id, name, member_entity_ids, home_region_ids, tension_level, leader_entity_id, founded_tick, dissolved_tick) with to_canonical_dict/from_dict following FactionState's exact pattern (src/core/state.py:609-645).
- Add a new dedicated parity ledger entry to docs/parity_ledger/social_narrative.yaml (not reusing SOC-166/228/230).
- Record a correction to the epic's own risk framing: the Party Formation & Lifecycle precedent has at least 9 real test files (~73 test functions), not 1 as previously stated.
- Explicitly decide and document whether Clan succession should fire on leader death (Group's SOC-228 does NOT — it dissolves instead per SOC-176/189) — if diverging, add a docs/guidelines/intentional_divergences.md entry.
- Explicitly decide whether ClanState.home_region_ids permits non-contiguous holdings, since FactionState.territory's merge logic (apply.py:348-360) has no adjacency/contiguity check and this ticket would implicitly inherit that if reusing the shape.

## Out of Scope
- Lifecycle actions (formation, dissolution, succession execution) — owned by idea 40/M4, not this ticket.
- idea 66 (Region/Place rebuild) — confirmed not a blocker for this ticket in both source docs, no need to sequence after it.

## Acceptance Criteria
- [x] A new ClanState frozen dataclass exists with clan_id/name/member_entity_ids/home_region_ids/tension_level/leader_entity_id/founded_tick/dissolved_tick, plus to_canonical_dict/from_dict following FactionState's exact pattern.
- [x] A new dedicated parity ledger entry (not reusing SOC-166/228/230) is added to docs/parity_ledger/social_narrative.yaml.
- [x] Ticket scope explicitly excludes lifecycle actions (owned by idea 40/M4) — schema/shape only.

## Related Tickets
- TCK-20260619-E53Aa-FACTION-STATE
- TCK-20260619-E41B-LEADERSHIP
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Related Docs
- docs/parity_ledger/social_narrative.yaml
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/systems/social_systems/party_lifecycle.py
- src/systems/social_systems/groups.py
- src/engine/apply.py

## Assumptions / Open Questions
- Leadership-succession-on-death is an open divergence decision (Group dissolves on leader death per SOC-176/189/SOC-228, Clan may want different behavior) — must be decided and documented.
- Territory contiguity for ClanState.home_region_ids is an open decision — FactionState's own territory merge has no adjacency check.
- This ticket must not race with idea 40/M4's ticket over the same ClanState dataclass — scope stays schema-only.
- `layer: core` was chosen because this ticket adds a state dataclass to src/core/state.py following existing entity/state primitive patterns; no dedicated `social` or `faction` layer is registered in registries/layer_registry.jsonl.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/plan.md`, no deviations:

1. **`src/core/state.py`** — added `ClanState` (`@dataclass(frozen=True, slots=True)`) immediately
   after `FactionState` (before `EquipmentComponent`), mirroring `FactionState`'s exact pattern:
   `clan_id: str`, `name: str = ""`, `member_entity_ids: Tuple[int, ...] = ()`,
   `home_region_ids: Tuple[str, ...] = ()`, `tension_level: float = 0.0`,
   `leader_entity_id: Optional[int] = None`, `founded_tick: int = 0`,
   `dissolved_tick: Optional[int] = None`, trailing `_canonical_cache` field. `to_canonical_dict()`
   is cache-guarded via `object.__setattr__` and explicitly sorts `member_entity_ids`/
   `home_region_ids` at serialization time (no apply-path writer exists yet to pre-sort them, so
   sorting happens inside the method itself to guarantee determinism regardless of construction
   order). `from_dict()` is a classmethod doing the standard list->tuple JSON round-trip
   conversion. `ClanState` is not referenced anywhere else in `src/` — no field was added to
   `AuthoritativeState` or `StateUpdate`, no `ClanUpdate` type was created, `apply.py` was not
   touched. Verified via `dataclasses.fields()` introspection that neither `AuthoritativeState`
   nor `StateUpdate` gained a `clan`-named field.
2. **`tests/unit/domains/faction/test_clan_state.py`** (new file) — all 6 required tests from
   `test_plan.md`: round-trip serialization, round-trip with defaults, frozen-immutability guard,
   canonical-dict sort/determinism guard, `AuthoritativeState`/`StateUpdate` no-field architecture
   guard, and a `ClanState is not FactionState` / no-`isinstance` identity guard. Test #7
   (optional parity-ledger content test) was not added — no existing `tests/tools/` convention for
   asserting individual shard entry content was found, matching the plan's "do not invent a new
   ledger-testing convention" instruction; the ledger entry is instead schema-validated by the
   existing `tests/tools/test_parity_index.py` / `test_parity_ledger_schema.py` suite, which was
   run and passes with the new `SOC-256` entry present.
3. **`docs/parity_ledger/social_narrative.yaml`** — appended `SOC-256` (confirmed as the next
   available id via `tools/gate_checks/parity_updater_static.py::next_available_id()` at
   implementation time, not hardcoded), `status: verified`, `priority: P2`, `v2_evidence` pointing
   at the new `ClanState` class, `test_path` pointing at
   `test_clan_state_serialization_round_trip`.
4. **`docs/guidelines/intentional_divergences.md`** — added a `Social/Clan` row to the Section 1
   summary table and a new `### 2.48 Clan Succession-on-Death Diverges from Group's
   Dissolve-on-Death` detailed entry in Section 2, `Status: DEFERRED`, recording the ratified
   design decision that `leader_entity_id` is meant to support future succession rather than
   Group's unconditional dissolve-on-leader-death — no succession-execution code was written; the
   entry records intent only, per Scope Guards.

Both open design questions in the ticket's Assumptions/Open Questions were resolved per the plan's
ratified decisions: (1) succession-on-death — diverges from Group, recorded in
`intentional_divergences.md` as `DEFERRED`; (2) territory contiguity — no contiguity enforcement,
matching `FactionState.territory`'s existing unconstrained set-merge shape as-is (no code change
needed, since `apply.py` is untouched in this ticket).

## Test Summary

- `pytest tests/unit/domains/faction/test_clan_state.py -x -v` — 6/6 passed.
- `pytest tests/unit/domains/faction/ tests/unit/core/test_authoritative_state_contract.py tests/unit/social/ tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py -v -m "not slow"` — 365 passed, 1 deselected, 0 failed. Confirms no regression to `FactionState`, `AuthoritativeState`, or any Group/Party lifecycle test from adding the new neighboring `ClanState` class.
- `pytest tests/tools/test_parity_index.py tests/tools/test_parity_prompt_ledger_file_list.py tests/tools/test_parity_ledger_schema.py -v` — 42 passed. Confirms the new `SOC-256` entry does not collide with any existing id and the shard still imports cleanly.

## Files Changed

- `src/core/state.py` — added `ClanState` frozen dataclass.
- `tests/unit/domains/faction/test_clan_state.py` — new test file (6 tests).
- `docs/parity_ledger/social_narrative.yaml` — added `SOC-256` entry.
- `docs/guidelines/intentional_divergences.md` — added Section 1 table row + Section 2.48 entry.
- `tickets/inprogress/TCK-20260831-CLAN-STATE-SCHEMA.md` — this file (Implementation Notes, Test Summary, Files Changed, Completion Summary, Status, Acceptance Criteria checkboxes).
- `staging_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/investigation.md` — created this run's Investigate phase (not edited by this Implement phase).
- `staging_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/plan.md` — created this run's Plan phase; no deviations found during implementation, so no Deviations section was added.
- `staging_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/test_plan.md` — created this run's Plan phase (not edited by this Implement phase).

## Completion Summary

Added `ClanState`, a new standalone frozen dataclass in `src/core/state.py` that reuses
`FactionState`'s exact serialization pattern (`to_canonical_dict`/`from_dict`, cache-guarded,
sorted collection fields), covering `clan_id`, `name`, `member_entity_ids`, `home_region_ids`,
`tension_level`, `leader_entity_id`, `founded_tick`, and `dissolved_tick`. This is deliberately
schema-only: `ClanState` has zero constructors anywhere in `src/` outside its own definition and
its dedicated test file (`tests/unit/domains/faction/test_clan_state.py`, 6 tests, all passing),
is not wired into `AuthoritativeState` or `StateUpdate`, and `apply.py` was not touched — durable
lifecycle wiring is explicitly deferred to a separate idea 40/M4 ticket. Documented the schema via
a new parity ledger entry (`SOC-256` in `docs/parity_ledger/social_narrative.yaml`) and recorded
the ratified succession-on-death design decision (Clan diverges from Group's unconditional
dissolve-on-death) as a new `DEFERRED` entry (`2.48`) in
`docs/guidelines/intentional_divergences.md`. Full regression suite for `FactionState`,
`AuthoritativeState`, and all Group/Party lifecycle tests (365 tests) passes unmodified.
