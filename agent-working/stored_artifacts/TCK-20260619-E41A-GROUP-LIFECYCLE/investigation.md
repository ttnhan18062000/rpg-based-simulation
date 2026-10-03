---
ticket_id: TCK-20260619-E41A-GROUP-LIFECYCLE
phase: investigation
date: 2026-06-21
---

# Investigation · TCK-20260619-E41A-GROUP-LIFECYCLE

## Current Behavior (file:line refs)

### GroupRecord definition — `src/core/state.py:L509-L550`

`GroupRecord` is a `@dataclass(frozen=True, slots=True)`. Current fields:

| Field | Type | Default |
|---|---|---|
| `id` | `int` | required |
| `leader_id` | `int` | required |
| `member_ids` | `Set[int]` | required |
| `anchor` | `tuple[float, float]` | required |
| `shared_target_id` | `Optional[int]` | `None` |
| `contract_id` | `Optional[str]` | `None` |
| `cohesion_radius` | `float` | `5.0` |
| `last_updated_tick` | `int` | `0` |
| `roles` | `Dict[int, str]` | `field(default_factory=dict)` |
| `str_apt` / `int_apt` / `agi_apt` / `vit_apt` / `end_apt` | `float` | `1.0` each |
| `_canonical_cache` | `Any` | `field(default=None, init=False, repr=False, compare=False)` |

Six fields are **absent** that E41A must add:

| New field | Type | Default | Semantic purpose |
|---|---|---|---|
| `formation_tick` | `int` | `0` | Tick when group was formed (needed for duration-based leader elections in E41B) |
| `escort_target_id` | `Optional[int]` | `None` | Entity id of the designated ESCORT_TARGET member (E41D) |
| `grievance_log` | `Tuple[str, ...]` | `()` | Immutable append-only log of grievance event strings (dissolution condition in E41B/D) |
| `reward_pool` | `int` | `0` | Accumulated gold for FairShareProtocol (E41C) |
| `last_leadership_check_tick` | `int` | `0` | Last tick that leadership election ran (gates 100-tick interval in E41B) |
| `dissolution_tick` | `Optional[int]` | `None` | Set when group dissolves (graceful or conflict); enables NarrativeLedger entry |

### `to_canonical_dict()` — `src/core/state.py:L528-L550`

Uses `_canonical_cache` pattern: computes once, stores via `object.__setattr__`. Current keys are flat (no nested sub-dict for lifecycle fields). Aptitudes are nested under `"aptitudes"` sub-key. Roles are emitted as `{str(k): v}` sorted by key. `member_ids` is emitted as `sorted(list(...))`. All six new fields **must be added** to the output dict in a deterministic order (sorted key alphabetical is the repo pattern — see `AptitudeComponent.to_canonical_dict` at L490-L505 and the `roles` sort above).

### `StateUpdate` — `src/core/updates.py:L833`

`StateUpdate.groups_add_or_update: List[GroupRecord]` already exists (L858). No new update vehicle is required. The existing apply path (`ApplyPath.apply_generation`) accepts the extended `GroupRecord` transparently — no changes to `StateUpdate` or `ApplyPath` are needed for this ticket.

### `_canonical_cache` invalidation risk

`GroupRecord` is `frozen=True`, so field values cannot change post-construction. The `_canonical_cache` is valid for the lifetime of the instance. This is safe. Adding new fields is a constructor-time change only — the cache is always `None` on first access and will include the new fields as long as `to_canonical_dict()` references them explicitly.

### Existing test constructions

`tests/unit/social/test_groups.py:L20-L27` constructs `GroupRecord(id=100, leader_id=1, member_ids={1,2}, anchor=(10.0, 10.0), roles={...})`. Because all six new fields have defaults, existing construction calls remain valid without modification.

---

## Mechanics/Engine Constraints

### Frozen dataclass + slots

`slots=True` constrains field addition: any new field must be declared in the class body at definition time; no dynamic attributes. `Tuple[str, ...]` for `grievance_log` is the correct immutable sequence type — a `List` would be mutable and violate `frozen=True` semantics.

### Durable state rule (CLAUDE.md)

All six new fields survive beyond the current tick once written into a `GroupRecord` stored in `AuthoritativeState.groups`. They therefore satisfy the "typed model + stable location + defined lifecycle + inspection visibility + tests" requirement. The `to_canonical_dict()` inclusion covers inspection/serialization visibility. Tests cover lifecycle.

### `grievance_log` type choice

`Tuple[str, ...]` with default `()` is the idiomatic V2 immutable-log pattern. Log entries are appended by constructing a new `GroupRecord` via `dataclasses.replace(group, grievance_log=group.grievance_log + (event_str,))`. Do not use `List` (mutable inside frozen is a dataclass violation).

### E41B/C/D dependency on these fields

- E41B (leadership election) reads `formation_tick` and `last_leadership_check_tick`; writes updated `last_leadership_check_tick` via `groups_add_or_update`.
- E41C (reward distribution) reads and writes `reward_pool` via `groups_add_or_update`.
- E41D (defection/escort) reads `escort_target_id` and `grievance_log`; sets `dissolution_tick` on dissolution.

These fields must be present and correctly typed **before** E41B can begin implementation.

### Canonical dict determinism

The `to_canonical_dict()` output determines replay/snapshot equality. New keys must be added in a deterministic order. The repo convention (per `AptitudeComponent`) is to list fields in declaration order within a flat dict. The six new fields should be emitted in the order they appear in the class body. `grievance_log` (a tuple) must be emitted as a `list` (JSON-serializable) — use `list(self.grievance_log)`.

### cooperation_contract.md — `GroupEvaluator` read path

`GroupEvaluator` (cooperation domain) reads `GroupRecord.leader_id` and `GroupRecord.member_ids` to detect leader-loss and compute trust decay. It does not read any of the six new fields. No cooperation domain changes are needed for E41A.

---

## Parity Ledger Overlap (IDs + status)

Source: `docs/parity_ledger/social_narrative.yaml`

| Entry | Text | Status | Overlap with E41A |
|---|---|---|---|
| SOC-166 | Contract party has founder/leader | verified | Tests `GroupRecord` construction with `leader_id` — will pass unchanged |
| SOC-167 | Contract party has member roles | verified | Tests `GroupRecord.roles` — will pass unchanged |
| SOC-173 | Party cohesion is updated from member positions | verified | Tests `GroupService.calculate_cohesion` — unchanged |
| SOC-191 | Group dissolution test covers contract abandonment consequence | verified | Tests group removal via `StateUpdate.groups_remove` — unchanged |
| SOC-225 | Social tests include party dissolution consequence if contract-backed | verified | Tests `groups_remove` apply path — unchanged |

**None of these entries require status update** from E41A alone. The six new fields do not alter any existing behavior tested by SOC-166 through SOC-225.

**New parity entry needed:** A new `SOC-xxx` entry (suggest `SOC-227`) should be added when E41A is finalized to record: "GroupRecord carries lifecycle fields (formation_tick, escort_target_id, grievance_log, reward_pool, last_leadership_check_tick, dissolution_tick) that survive across ticks and are serialized in to_canonical_dict()." This entry is P1 and should gain a test_path pointing to the new lifecycle field tests.

---

## Prior Work

### TCK-20260503-PHANTOM-LEADER-HARDENING

Scope: `GroupSystem.update_groups` fixed to use the sliding (refined) world state so leader death is detected same-tick. Files changed: `src/systems/groups.py`, `src/engine/pipeline.py`. **Not a structural change to `GroupRecord`** — no field additions. This ticket does not conflict with E41A.

### TCK-20260619-E41-PARTY-LOOP (parent epic, done/scoped)

Key finding from epic investigation: "no new `PartyState` class needed — avoids state bifurcation". The six lifecycle fields are the authoritative scope of E41A. The epic also confirmed `grievance_log` threshold for defection detection is length ≥ 3 (used in E41D), and leadership election runs at 100-tick intervals keyed by `last_leadership_check_tick` (E41B).

### TCK-20260501-SOCIAL-LIFECYCLE / TCK-20260410-PH4-SOCIAL-CONTRACTS

Both stored artifacts confirm `ContractState` and `ContractKind.RECRUITMENT` exist at `src/core/strategic.py`. The `contract_id` field already present on `GroupRecord` links back to these. E41A does not touch `ContractState`.

---

## Risks and Open Questions

### R1 — `grievance_log` entry format is unspecified in E41A
**Risk:** E41B and E41D will need to parse grievance log entries. If E41A sets the type as `Tuple[str, ...]` but leaves the string format unspecified, E41B may use an incompatible format (e.g. free text vs structured "event_type:tick:entity_id"). **Recommendation:** Document a minimal format in E41A test fixtures even if not enforced: `"<event_type>:<tick>"` (e.g. `"ABANDON:120"`). This creates a convention for E41B/D to follow.

### R2 — `reward_pool` currency unit alignment
**Risk:** `reward_pool: int` is declared as `int` matching the gold balance convention. Confirm that `FairShareProtocol` (E41C) uses integer arithmetic consistent with the existing economic system (no float rounding). The `ResourceTransferIntent` uses integer amounts. This is a design confirmation question for E41C, but E41A must commit the type now.

### R3 — `dissolution_tick` vs `groups_remove` interplay
**Risk:** The cooperation_contract.md and existing tests (`test_group_dissolution`) use `groups_remove` to remove a group. If E41D sets `dissolution_tick` and still keeps the group in `state.groups` for one tick before removal, there is a window where a "dissolved" group remains present. **Decision needed:** Does dissolution mean immediate `groups_remove`, or does `dissolution_tick` set + then groups_remove one tick later? E41A must document the intended semantics to avoid divergence in E41D.

### R4 — `_canonical_cache` field ordering in `to_canonical_dict()`
The current dict uses flat field ordering without alphabetical sorting (keys follow declaration order). The aptitudes block is a nested sub-dict. Confirm whether the six new fields should be flat at the top level or nested under a `"lifecycle"` sub-key. **Recommendation:** Keep flat (consistent with existing `last_updated_tick`, `cohesion_radius` pattern) — no sub-key nesting.

### R5 — `slots=True` and `field(default_factory=...)` for mutable defaults
`member_ids: Set[int]` uses `field(default_factory=...)` implicitly (passed as required). `roles` uses `field(default_factory=dict)`. The new fields use immutable defaults (`0`, `None`, `()`) so `default_factory` is **not** needed. Confirm `grievance_log: Tuple[str, ...] = ()` — the empty tuple is a valid immutable default in frozen dataclasses.

---

## Anti-Drift Hazards

1. **`_canonical_cache` not updated** — If the six fields are added to `GroupRecord.__init__` but not to `to_canonical_dict()`, downstream serialization (replay, telemetry, NarrativeLedger) silently omits them. The cache returns a stale dict. Guard: test that every new field name appears as a key in `to_canonical_dict()` output.

2. **Mutable default for `grievance_log`** — Using `List` instead of `Tuple` will raise `ValueError: mutable default is not allowed for field` in a frozen dataclass. If this error is suppressed by a `field(default_factory=list)`, the frozen contract is violated because the list is mutable inside the "frozen" instance. Guard: test that `grievance_log` is an instance of `tuple`, not `list`.

3. **E41B begins implementation before E41A is merged** — E41B reads `formation_tick` and `last_leadership_check_tick`. If E41A is incomplete, E41B will fail on `AttributeError`. Ticket ordering constraint: E41B must not begin until E41A passes all tests and is committed.

4. **Existing `GroupRecord` constructions in tests omit new fields** — All six new fields have defaults. Existing test constructions like `GroupRecord(id=100, leader_id=1, member_ids={1,2}, anchor=(0,0))` remain valid. No test breakage expected. Guard: run `tests/unit/social/test_groups.py` and `tests/unit/domains/cooperation/` after adding fields.

5. **`to_canonical_dict()` determinism for `grievance_log`** — `list(self.grievance_log)` preserves insertion order (tuples are ordered). This is deterministic as long as grievance entries are appended in a consistent order. The tuple does not need sorting (unlike `member_ids` or `roles`).
