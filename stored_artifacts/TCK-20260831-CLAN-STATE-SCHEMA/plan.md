---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-CLAN-STATE-SCHEMA
artifact_type: plan
tags: [faction, social]
---

# Implementation Plan — TCK-20260831-CLAN-STATE-SCHEMA

## Summary

Add a new standalone frozen dataclass `ClanState` to `src/core/state.py`, reusing `FactionState`'s
exact pattern (`src/core/state.py:608-645`: `@dataclass(frozen=True, slots=True)`, trailing
`_canonical_cache` field, cache-guarded `to_canonical_dict()`, classmethod `from_dict()`). This is
schema/shape wiring only — no field is added to `AuthoritativeState` or `StateUpdate`, no
`ClanUpdate` type is created, and `apply.py` is not touched, per the ticket's explicit Out of
Scope and the investigation's anti-drift hazards. Two design decisions the ticket flagged as open
are resolved here per the investigation's own grounded recommendations, both ratified as this
plan's decision rather than left open: (1) `ClanState` schema supports future succession-on-death
(an independently reassignable `leader_entity_id`, distinct from `Group`'s unconditional
dissolve-on-death at `src/systems/world_systems/groups.py:93-108`), recorded as a new `DEFERRED`
entry in `docs/guidelines/intentional_divergences.md` since the succession execution logic itself
belongs to idea 40/M4; (2) no territory-contiguity enforcement, matching
`FactionState.territory`'s existing plain set union/diff merge shape
(`src/engine/apply.py:348`) as-is. A new dedicated parity ledger entry (`SOC-256`, next available
id per direct scan of `docs/parity_ledger/social_narrative.yaml`) documents the schema. A new test
file `tests/unit/domains/faction/test_clan_state.py` covers round-trip serialization, frozen
immutability, canonical-dict determinism, and two anti-drift guards (no `AuthoritativeState`/
`StateUpdate` field, no identity-sharing with `FactionState`).

## Steps

### Step 1 — Add the `ClanState` frozen dataclass
**Files:** `src/core/state.py`

**Change:** Insert a new `@dataclass(frozen=True, slots=True)` class `ClanState` immediately after
`FactionState` (which ends at `src/core/state.py:645`, confirmed by direct read — `from_dict`'s
closing `)` is on line 645, followed by two blank lines and `EquipmentComponent` at line 649).
Field list, in order, following `FactionState`'s exact field-ordering convention (id field first,
then collection fields, then scalar fields, then trailing `_canonical_cache`):

```python
@dataclass(frozen=True, slots=True)
class ClanState:
    """Authoritative durable state for a named clan (schema-only; idea 40/M4 owns lifecycle)."""
    clan_id: str
    name: str = ""
    member_entity_ids: Tuple[int, ...] = ()
    home_region_ids: Tuple[str, ...] = ()
    tension_level: float = 0.0
    leader_entity_id: Optional[int] = None
    founded_tick: int = 0
    dissolved_tick: Optional[int] = None
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
```

Field-type rationale (per investigation, resolving decision #3 from the launch prompt): the
brainstorm doc's `List[str]` proposal (`docs/brainstorm/rpg_expected_schemas.html:610-617`) is
**not** followed — the ticket's own instruction is to follow `FactionState`'s exact pattern, and
entity ids are `int`-typed throughout this codebase (`GroupRecord.member_ids: Set[int]` at
`src/core/state.py:555`; `EntityState.id: int`, confirmed directly at `src/core/state.py:668`).
`home_region_ids` mirrors
`FactionState.territory: Tuple[str, ...]` exactly (`src/core/state.py:612`) since regions are
`str`-keyed. `member_entity_ids` therefore uses `Tuple[int, ...]`, not `Tuple[str, ...]`.

`to_canonical_dict()` — cache-guarded exactly like `FactionState.to_canonical_dict()`
(`src/core/state.py:620-633`): sort `member_entity_ids`/`home_region_ids` at serialization time
(`sorted(self.member_entity_ids)` / `sorted(self.home_region_ids)`, mirroring
`GroupRecord.to_canonical_dict()`'s `sorted(list(self.member_ids))` at `src/core/state.py:582` —
note `FactionState.territory` itself is stored pre-sorted by its apply-path writer at
`apply.py:350` and just does `list(self.territory)` at serialization; since `ClanState` has no
apply-path writer in this ticket's scope, sort explicitly inside `to_canonical_dict()` instead, to
guarantee determinism regardless of construction order — this is what
`test_clan_state_canonical_dict_is_sorted_and_deterministic` verifies). Populate `_canonical_cache`
via `object.__setattr__(self, "_canonical_cache", res)`, identical to
`src/core/state.py:632`/`604`/`546`.

`from_dict()` — classmethod, `tuple(d.get("member_entity_ids", []))` and
`tuple(d.get("home_region_ids", []))` (explicit list→tuple JSON round-trip conversion, mirroring
`FactionState.from_dict()`'s `tuple(d.get("territory", []))` at `src/core/state.py:639`).

**Do NOT touch:** `FactionState` itself (no shared base class, no aliasing), `GroupRecord`,
`EquipmentComponent`, or any other class in `state.py`. Do not add `Faction(IntEnum)`
(`src/core/enums.py`) or `EntityState.identity.faction` references — unrelated numeric concept per
investigation's anti-drift note.

**Verify:** `test_clan_state_serialization_round_trip`,
`test_clan_state_serialization_round_trip_defaults`, `test_clan_state_is_frozen`,
`test_clan_state_canonical_dict_is_sorted_and_deterministic` (all from test_plan.md).

---

### Step 2 — Add the new unit test file
**Files:** `tests/unit/domains/faction/test_clan_state.py` (new file; directory already has
`__init__.py` per test_plan.md, no new package init needed)

**Change:** Implement all 6 required tests from `test_plan.md` (items 1-6; item 7 is optional and
deferred — see Step 3):
1. `test_clan_state_serialization_round_trip` — full round trip through
   `to_canonical_dict()`/`from_dict()`, asserting `isinstance(restored.member_entity_ids, tuple)`
   and `isinstance(restored.home_region_ids, tuple)`.
2. `test_clan_state_serialization_round_trip_defaults` — `ClanState(clan_id="x")` round-trips with
   `member_entity_ids == ()`, `home_region_ids == ()`, `tension_level == 0.0`,
   `leader_entity_id is None`, `founded_tick == 0`, `dissolved_tick is None`.
3. `test_clan_state_is_frozen` — `dataclasses.FrozenInstanceError` on any field assignment attempt.
4. `test_clan_state_canonical_dict_is_sorted_and_deterministic` — two `ClanState` instances built
   with same content, different insertion order, assert identical `to_canonical_dict()` output.
5. `test_clan_state_does_not_touch_authoritative_state` — architecture guard:
   `"clan" not in {f.name.lower() for f in dataclasses.fields(AuthoritativeState)}` and same for
   `StateUpdate`.
6. `test_clan_state_does_not_share_faction_state_identity` — `ClanState is not FactionState`, and
   a `ClanState()` instance is not `isinstance(..., FactionState)`.

**Do NOT touch:** any file under `tests/unit/social/`, `tests/unit/domains/cooperation/`, or
`tests/unit/domains/faction/test_faction_state.py` — these are read-only regression-verification
targets in this ticket, not edit targets.

**Verify:** `pytest tests/unit/domains/faction/test_clan_state.py -x -v` passes;
`pytest tests/unit/domains/faction/ -x -v` (full directory) still passes, confirming no
interference with `FactionState`'s existing tests.

---

### Step 3 — Add the dedicated parity ledger entry
**Files:** `docs/parity_ledger/social_narrative.yaml`

**Change:** Append a new entry with `id: SOC-256` — confirmed the next available id by direct scan
of the file: the last five existing ids are `SOC-251` (line 3602), `SOC-252` (3627), `SOC-253`
(3645), `SOC-254` (3667), `SOC-255` (line 3692, the file's final entry). Follow the file's exact
existing entry shape (see `SOC-255` at lines 3692-3706 for the format template — `id`, `text`,
`status`, `priority`, `legacy_evidence`, `v2_evidence`, `test_path`, `divergence_note`, all
required by `docs/parity_ledger/schema.json`'s `allOf` rule when `status` is `verified`/
`divergent`: both `v2_evidence` and `test_path` become required non-null strings in that case).

Use the project's `tools/gate_checks/parity_updater_static.py::next_available_id(shard_filename=
"social_narrative.yaml")` at implementation time to reconfirm `SOC-256` is still free (another
ticket may land first — investigation's own caveat), rather than hardcoding blindly.

Entry content:
```yaml
- id: SOC-256
  text: 'ClanState schema shape: a new frozen, slots dataclass (clan_id, name,
    member_entity_ids, home_region_ids, tension_level, leader_entity_id, founded_tick,
    dissolved_tick) reusing FactionState's exact serialization pattern
    (to_canonical_dict/from_dict, cache-guarded, sorted collection fields). Schema-only:
    not wired into AuthoritativeState, StateUpdate, or apply.py in this ticket -- lifecycle
    actions (formation/dissolution/succession) are owned by a separate, later ticket
    (idea 40/M4).'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: src/core/state.py (ClanState class, added alongside FactionState)
  test_path: tests/unit/domains/faction/test_clan_state.py::test_clan_state_serialization_round_trip
  divergence_note: null
```
Priority is `P2` (not `P0`/`P1`) because this is schema/shape only, with no apply-path or durable
persistence claim — matching the investigation's explicit reasoning that a P0/P1 claim would be
premature since `ClanState` is not wired into `AuthoritativeState` by this ticket.

**Ratified decision (resolving the ticket's Assumption/Open Question re: `faction.yaml` vs
`social_narrative.yaml`):** use `social_narrative.yaml`, matching the ticket's own explicit Scope
and Related Docs instruction. The investigation flagged `faction.yaml` as arguably more natural
given the shape reuse, but the ticket text is unambiguous and takes precedence over the
investigation's alternative suggestion — this plan does not silently redirect to `faction.yaml`.

**Other writers to this file (enumerated per fact-verification requirement):** `social_narrative.yaml`
is a shared, append-only ledger. Other writers observed in the repo: (a) `parity-updater` agent,
invoked at ticket-close time by other in-flight tickets touching Group/Party/Cooperation
mechanics — the most recent entries (`SOC-251`-`SOC-255`) show this file receives frequent
sequential appends from unrelated tickets; (b) `tools/parity_ledger_writer.py`, the sanctioned
schema-validating writer tool used by `parity-updater`. This step's interaction with those other
writers: append-only, single new entry at the end of the file, id reconfirmed via
`next_available_id()` immediately before writing (not pre-committed to `SOC-256` if another ticket
has landed an entry in between investigation and implementation) — this avoids an id collision if
a concurrent ticket appends first. No existing entry (`SOC-166`, `SOC-228`, `SOC-230`, `SOC-176`,
`SOC-189`) is modified.

**Do NOT touch:** `docs/parity_ledger/faction.yaml`, or any existing `SOC-*` entry in
`social_narrative.yaml`.

**Verify:** `tests/tools/` schema-validation test for `docs/parity_ledger/` (whichever existing
test validates the shard against `schema.json` — run the full `tests/tools/` parity-ledger test
file if one exists; test_plan.md item 7 flags this as optional/check-first, not a new test to
invent).

---

### Step 4 — Record the succession-on-death divergence decision
**Files:** `docs/guidelines/intentional_divergences.md`

**Change:** Add a new entry to Section 2 (Detailed Records), and a new row to the Section 1
Divergence Summary Table, following the exact format precedent at
`docs/guidelines/intentional_divergences.md:155-159` (`### 2.19 Service Assembly Gap (World
Assembly)`, which uses `**Rationale**: **Stabilized**` and is the file's only existing
`DEFERRED`-status entry — confirmed via direct grep, table row at line 25: `| **World Assembly** |
Service Assembly | **Stabilized** | DEFERRED |`).

Table row (append to Section 1, in the appropriate subsystem grouping — new `Social/Clan` row):
```
| **Social/Clan** | Clan Succession-on-Death | **Intentional Gameplay Change** | DEFERRED |
```

Detailed record (append to Section 2, numbered as the next available `2.x` — confirm the highest
existing number at implementation time, investigation observed entries up through `2.47`):
```markdown
### 2.4X Clan Succession-on-Death Diverges from Group's Dissolve-on-Death
(TCK-20260831-CLAN-STATE-SCHEMA)
- **Subsystem**: Social/Clan
- **Old Behavior**: `Group` (the existing multi-entity coordination unit) unconditionally
  dissolves when its leader dies or deactivates -- `GroupSystem.update_groups()`,
  `src/systems/world_systems/groups.py:93-108` (Logic IDs SOC-176/SOC-189), no re-election or
  succession branch exists on leader death.
- **New Behavior**: `ClanState`'s schema is designed to support succession instead of
  dissolution on leader death -- `leader_entity_id` is an independently reassignable field, not
  structurally tied to member-removal logic the way Group's dissolution is. This ticket
  (TCK-20260831-CLAN-STATE-SCHEMA) adds only the schema shape; it does not implement any
  succession-execution logic, event, or lifecycle action.
- **Rationale**: **Intentional Gameplay Change**. The brainstorm doc's own stated rationale for
  `dissolved_tick` is explicitly framed around avoiding "cross-generational Clans silently
  break[ing]" (`docs/brainstorm/rpg_expected_schemas.html:617`), implying Clans are meant to be
  multi-generational political entities, unlike Group's small, disposable adventuring parties.
  A `leader_entity_id` that can never be reassigned without dissolving the whole Clan would give
  no signal beyond what `dissolved_tick` alone already provides.
- **Verification**: Not yet applicable -- no succession-execution logic exists yet. This entry
  records the schema-level design intent only.
- **Unblock condition**: Idea 40/M4 implements the actual succession-on-death execution logic
  (leader-liveness check + reassignment branch, analogous to but structurally distinct from
  `GroupSystem.update_groups()`'s dissolution branch, since it must branch to reassignment
  instead of removal). When that lands, update this entry's `Verification` field with the real
  test path and flip the Summary Table Status from `DEFERRED` to `RATIFIED`.
- **Status**: DEFERRED
```

**Do NOT touch:** any other entry in this file, and do not write succession-execution code
anywhere in `src/` — this step records a decision, it does not implement it.

**Verify:** No automated test targets this doc directly (per investigation, `party_contract.md`
and this file are prose docs); manual review confirms the entry exists and matches the format
precedent. `done-checker`'s doc-parity check (if any) should be satisfied by the entry's presence.

## Scope Guards

- Do **not** add `clans: Dict[str, ClanState]` to `AuthoritativeState`, a `ClanUpdate` type, or any
  `apply.py` / `StateUpdate.merge_many()` / `is_noop()` wiring. Owned by idea 40/M4.
- Do **not** implement succession-on-death or dissolution execution logic anywhere in `src/`.
  Step 4 records the *decision*, not the code.
- Do **not** add territory/region adjacency or contiguity checking of any kind. `RegionState`
  (`src/core/state.py:236`, confirmed by investigation's direct grep) has no
  `adjacent_region_ids`/`neighbors`/`borders` field, and none is added by this ticket.
  `home_region_ids` reuses `FactionState.territory`'s unconstrained plain-set merge shape as-is —
  this is a scope guard, not a silent gap.
- Do **not** add an `EntityState.identity.clan_id` field, even though Group's dual-sided
  `identity.group_id` lookup (`src/core/state.py:488` per investigation) is a relevant precedent
  for idea 40/M4. Touching `EntityState`/`IdentityComponent` is out of scope here.
- Do **not** touch `src/systems/world_systems/groups.py` or
  `src/systems/social_systems/party_lifecycle.py` — read-only investigation targets only. The
  ticket's Related Code Areas listed the nonexistent `src/systems/social_systems/groups.py`; the
  real file is `src/systems/world_systems/groups.py` (correction applied throughout this plan).
- Do **not** reuse `SOC-166`/`SOC-228`/`SOC-230` for the new parity entry — must be a dedicated,
  new id (`SOC-256`).
- Do **not** redirect the parity entry to `docs/parity_ledger/faction.yaml` — ratified as
  `social_narrative.yaml` per Step 3.
- Do **not** touch `Faction(IntEnum)` (`src/core/enums.py`) or `EntityState.identity.faction: int`
  — unrelated numeric entity-level concept, must not be confused with the new `ClanState`.
- Do **not** modify `tests/unit/social/*.py`, `tests/unit/domains/cooperation/
  test_phase7_party_cohesion_service.py`, `tests/unit/domains/faction/test_faction_state.py`, or
  `tests/unit/core/test_authoritative_state_contract.py` — these are regression-verification
  targets only.

## Dependency Map

- **Step 1** (add `ClanState` dataclass) has no dependencies — first step.
- **Step 2** (new test file) depends on Step 1 (tests import and construct `ClanState`).
- **Step 3** (parity ledger entry) depends on Step 1 and Step 2 (the entry's `test_path` cites a
  test written in Step 2; the entry documents the class added in Step 1). Independent of Step 4.
- **Step 4** (intentional_divergences.md entry) depends only on Step 1 existing conceptually
  (references `leader_entity_id`'s field shape) — can be done in parallel with Step 3, but must
  follow Step 1.
- No step depends on external tickets landing first; idea 40/M4 is explicitly out of scope and not
  a dependency in either direction.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A new `ClanState` frozen dataclass exists with `clan_id`/`name`/`member_entity_ids`/`home_region_ids`/`tension_level`/`leader_entity_id`/`founded_tick`/`dissolved_tick`, plus `to_canonical_dict`/`from_dict` following `FactionState`'s exact pattern. | Step 1 | `test_clan_state_serialization_round_trip`, `test_clan_state_serialization_round_trip_defaults`, `test_clan_state_is_frozen`, `test_clan_state_canonical_dict_is_sorted_and_deterministic` (Step 2) |
| A new dedicated parity ledger entry (not reusing SOC-166/228/230) is added to `docs/parity_ledger/social_narrative.yaml`. | Step 3 | `SOC-256` entry present and schema-valid; optional `tests/tools/` parity-ledger content test if one exists |
| Ticket scope explicitly excludes lifecycle actions (owned by idea 40/M4) — schema/shape only. | Step 1 (design), Step 4 (divergence decision recorded, not executed), Scope Guards | `test_clan_state_does_not_touch_authoritative_state`, `test_clan_state_does_not_share_faction_state_identity` (Step 2); full `tests/unit/social/` regression run confirming no edits to Group/Party files |

## Anti-Drift Notes

- The investigation confirmed `RegionState` has zero adjacency data anywhere in the codebase —
  building contiguity validation is not a "quick addition," it would require a net-new
  region-adjacency data model. This plan does not attempt it, and no future step in this ticket
  should either.
- `PartyLifecycleService.check_leadership()`/`check_defection()`
  (`src/systems/social_systems/party_lifecycle.py:43-119`, `142-199`) are confirmed **not**
  plausible reuse targets for future Clan succession logic — both are Group-scoped and structurally
  foreclose the "leader dies → reassign" path. This is noted for idea 40/M4's benefit, not acted on
  here.
- `docs/simulation/domains/party_contract.md` has a separate, pre-existing gap (it does not
  document `SOC-176`/`SOC-189`'s leader-death dissolution rule at all). This is unrelated to
  `ClanState` and explicitly not this ticket's scope to fix.
- The ticket's Related Code Areas lists `src/systems/social_systems/groups.py`, which does not
  exist. Every reference in this plan uses the corrected path,
  `src/systems/world_systems/groups.py`.
- `member_entity_ids` must be `Tuple[int, ...]`, not the brainstorm doc's informal `List[str]`
  notation — entities are int-keyed throughout this codebase (`GroupRecord.member_ids: Set[int]`).
  Getting this field type wrong would create a codebase-wide inconsistency.
