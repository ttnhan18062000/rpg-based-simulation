---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-CLAN-STATE-SCHEMA
artifact_type: investigation
tags: [faction, social]
---

# Investigation — TCK-20260831-CLAN-STATE-SCHEMA

## Current Behavior

### FactionState (the pattern to reuse) — `src/core/state.py:609-645`
`@dataclass(frozen=True, slots=True)`, decorator at L608, class body L609-645:
```python
faction_id: str
territory: Tuple[str, ...] = ()
resources: Dict[str, int] = field(default_factory=dict)
diplomatic_relations: Dict[str, DiplomaticState] = field(default_factory=dict)
active_doctrines: Tuple[str, ...] = ()
military_strength: float = 1.0
tension_level: float = 0.0
_canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
```
- `to_canonical_dict()` (L620-633): cache-guarded, returns a fully sorted flat dict (`dict(sorted(self.resources.items()))`, `{k: v.value for k, v ...}` for the enum-valued dict), populates `_canonical_cache` via `object.__setattr__` (the approved frozen-dataclass bypass).
- `from_dict()` (L635-645): classmethod, `tuple(d.get("territory", []))` — explicit list→tuple conversion for the two `Tuple[str, ...]` fields (JSON round-trips tuples as lists), `DiplomaticState(v)` reconstruction for the enum dict.
- Neighbor in the file: `GroupRecord` (L550-605) immediately precedes it — same `frozen=True, slots=True` + `_canonical_cache` pattern, but uses `Set[int]` for `member_ids` (sorted at serialization time in `to_canonical_dict()`, L582) rather than a `Tuple`.

Confirmed: ticket's cited line range `src/core/state.py:609-645` is exactly correct — this is the entire `FactionState` class body.

### AuthoritativeState.factions — `src/core/state.py:1157`
`factions: Dict[str, "FactionState"] = field(default_factory=dict)` is a top-level field on `AuthoritativeState`, threaded through `to_readonly()` (L1234, `factions=ReadOnlyDict(self.factions)`) and through `apply.py`'s constructor call (see below). **This ticket's scope does not add an equivalent `clans` field to `AuthoritativeState`, a `ClanUpdate` type, or any `apply.py` wiring** — the ticket AC and Scope are schema-dataclass-only. Confirmed no `clan`/`Clan` symbol exists anywhere in `src/core/state.py`, `src/core/updates.py`, or `src/engine/apply.py` today (grepped).

### FactionState apply-path (context only, not touched by this ticket) — `src/engine/apply.py:338-364`
```python
new_factions = dict(getattr(prior_state, "factions", {}))
for fu in update.faction_updates:
    if fu.is_noop():
        continue
    existing = new_factions.get(fu.faction_id)
    if existing is None:
        existing = FactionState(faction_id=fu.faction_id)
    new_tension = existing.tension_level + fu.tension_delta
    new_ms = fu.military_strength_set if fu.military_strength_set is not None else existing.military_strength
    new_territory = (set(existing.territory) | set(fu.territory_add)) - set(fu.territory_remove)   # L348
    ...
    new_factions[fu.faction_id] = replace(existing, tension_level=max(0.0, min(1.0, new_tension)),
        military_strength=new_ms, territory=tuple(sorted(new_territory)), ...)
```
**Confirmed: L348's `new_territory` computation is a plain `set` union/difference — no adjacency, no neighbor graph, no geographic contiguity check of any kind.** `RegionState` (`src/core/state.py:236`) itself has **no** `adjacent_region_ids`/`neighbors`/`borders` field at all (grepped the class body directly) — there is no data structure anywhere in the codebase today from which a contiguity check could even be computed for `territory`/`home_region_ids`. This directly confirms the ticket's Assumption/Open Question #2.

### Group dissolution-on-leader-death (SOC-176/189) — `src/systems/world_systems/groups.py:81-108`
**Correction to ticket's Related Code Areas**: the ticket lists `src/systems/social_systems/groups.py`, which does not exist. The actual file is `src/systems/world_systems/groups.py` (`GroupSystem.update_groups`). `src/systems/social_systems/` contains `party_lifecycle.py` (read) and `party_composition.py`, not `groups.py`. Flagging as a gap in the ticket's Related Code Areas — Plan/Implementer should read `src/systems/world_systems/groups.py`, not the non-existent path.

Confirmed code (`GroupSystem.update_groups`, L93-108):
```python
# Logic ID: SOC-176 (Party dissolves when leader is dead/missing)
# Logic ID: SOC-189 (Group dissolution test covers dead leader)
if (
    leader is None
    or not is_alive(group.leader_id)
    or not is_active(group.leader_id)
):
    groups_remove.append(g_id)
    for m_id in group.member_ids:
        entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
    continue
```
This is unconditional dissolution — there is no succession/re-election branch on leader death anywhere in this function. Confirmed distinct from `PartyLifecycleService.check_leadership()` (`src/systems/social_systems/party_lifecycle.py:43-119`, SOC-228), which only re-elects a leader on a **periodic interval** (`LEADERSHIP_CHECK_INTERVAL = 100` ticks) based on sociability drift — it never fires in response to a death event, and a dead leader is never a candidate (the group is already gone by the time a periodic check would run, since dissolution happens the same tick the leader dies/deactivates). Ticket's characterization ("Group's SOC-228 does NOT [fire on leader death] — dissolves instead per SOC-176/189") is confirmed accurate, with the added precision that SOC-228 doesn't fire on death *for any reason*, dead or not — it's a wholly separate periodic mechanism, not a "does not additionally trigger" nuance.

### PartyLifecycleService (`src/systems/social_systems/party_lifecycle.py`, read in full)
Two static methods, both pure/typed-return, never mutate `group`/`EntityState` directly:
- `check_leadership()` (L43-119, SOC-228): periodic re-election, lowest-id tiebreak, `LeadershipChangedEvent`.
- `check_defection()` (L142-199, SOC-230): grievance-threshold-based member removal; sets `dissolution_tick` only when membership drops to ≤1 after defection (not simply "leader died").

Neither method is a plausible home for clan succession-on-death logic even conceptually — both are Group-scoped, and Group's own dissolution law (SOC-176/189) already forecloses the "leader dies → re-elect" path structurally at the `GroupSystem.update_groups` level, before `PartyLifecycleService` ever runs. Any future Clan succession-on-death mechanism (idea 40/M4) would need its own equivalent of `GroupSystem`'s leader-liveness check, but branching to leader-reassignment instead of removal — it cannot reuse `check_leadership()`/`check_defection()` as-is.

### Prior art for member-lookup indexing (informational — not in this ticket's scope)
`EntityState.identity.group_id: Optional[int]` (`src/core/state.py:488`) is the dual-sided index Group uses: `GroupRecord.member_ids` (group→members) plus `IdentityComponent.group_id` (member→group, O(1) lookup). This directly answers the brainstorm doc's own open question ("is clan membership tracked only from ClanState's side, or does `EntityState.identity` also need a `clan_id` field") — Group's precedent is dual-sided. `docs/brainstorm/rpg_expected_schemas.html:620` already flags this as an open question for idea 36/40, not this ticket; **this ticket's scope (frozen dataclass + `to_canonical_dict`/`from_dict` only) does not touch `EntityState`/`IdentityComponent`**, so no `clan_id` field is added here. Noting the precedent for the Plan phase and for idea 40/M4, since it will need this exact pattern.

### Party Formation & Lifecycle test-count correction (ticket Scope item 3)
Grepped every test file referencing `PartyLifecycleService`, `GroupSystem`, `GroupRecord`, `PartyCompositionScorer`, or `PartyCoordinationSystem`: 21 files total repo-wide. Restricting to the 13 files most directly scoped to party/group lifecycle (`tests/unit/social/*.py` — 12 files — plus `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py`), counted `def test_` occurrences per file directly:

| File | test_ count |
|---|---|
| test_party_composition.py | 25 |
| test_party_lifecycle.py | 23 |
| test_group_lifecycle_fields.py | 10 |
| test_social_lifecycle.py | 6 |
| test_domain_7_social.py | 5 |
| test_social_party_regression.py | 4 |
| test_groups.py | 3 |
| test_multi_hero.py | 3 |
| test_party_agency.py | 3 |
| test_party_coordination.py | 2 |
| test_phantom_leader.py | 2 |
| test_social_phase7.py | 2 |
| test_phase7_party_cohesion_service.py | 2 |
| **Total** | **90** |

This confirms and slightly exceeds the ticket's own correction ("at least 9 real test files (~73 test functions), not 1 as previously stated") — the real, directly-counted figure is **13 files, 90 test functions** in the narrowest reasonable scoping, or 21 files if the broader cross-domain references (combat/movement/adventure tests that only incidentally touch groups) are included. The direction of the correction (many, not one) is fully confirmed; the ticket may understate slightly.

## Mechanics / Engine Constraints

- **`docs/mechanics/` has no dedicated Faction/Clan/Party chapter.** Faction mechanics (territory, diplomatic relations, tension) appear only incidentally inside `05_world_evolution.md` (region ownership, hazard endurance) — no chapter documents `FactionState`'s shape or a formula governing it. Party/Group lifecycle law lives outside `docs/mechanics/` entirely, in `docs/simulation/domains/party_contract.md` (see below), which is not one of the 6 Mechanics Bible chapters.
- **`docs/simulation/domains/party_contract.md`** (read in full) documents `GroupRecord`'s fields and `PartyLifecycleService`'s leadership/defection rules (SOC-228/230) but **does not document the leader-death dissolution rule (SOC-176/189)** — that logic lives in `GroupSystem.update_groups` (a different phase) and is undocumented in this file. This is a pre-existing gap unrelated to this ticket (Group, not Clan), noted for completeness but not something this ticket is scoped to fix.
- **Frozen/slots dataclass law** (implicit engine convention, consistent across `GroupRecord`/`FactionState`/`RegionState`): every new durable-state-shaped dataclass in `state.py` uses `@dataclass(frozen=True, slots=True)`, a `_canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)` trailing field, `object.__setattr__` to populate the cache inside `to_canonical_dict()`, and `Tuple[str, ...]` (not `List`) for any field representing an ordered/hashable collection of ids intended to round-trip through JSON. `ClanState` must follow this exactly per the ticket's own instruction ("following FactionState's exact pattern").
- **Note on the brainstorm doc's field types**: `docs/brainstorm/rpg_expected_schemas.html:610-617` lists `member_entity_ids`/`home_region_ids` as `List[str]` in its proposal table. This is the HTML doc's informal notation, not a binding type — the ticket text explicitly says to follow `FactionState`'s **exact pattern**, and `FactionState.territory` is `Tuple[str, ...]`, not `List[str]`. Recommend `Tuple[str, ...]` for both `member_entity_ids` and `home_region_ids` for consistency with `FactionState`/frozen-dataclass conventions (an `int`/`str` id type also needs pinning down at Plan time — `FactionState.territory` holds region ids as `str`, and `GroupRecord.member_ids` holds entity ids as `int`; the ticket's own field name `member_entity_ids` and `EntityState.id: int` suggest entity ids should be `int`, matching `GroupRecord`, not `str`).

## Docs Requiring Update

- `docs/parity_ledger/social_narrative.yaml`: ticket AC requires a new dedicated parity entry (not reusing SOC-166/228/230) for the new `ClanState` dataclass shape. Next available sequential numeric id in this shard is `SOC-256` (highest existing is `SOC-255`, confirmed by scanning all `^- id: SOC-[0-9]+` entries) — use `tools/gate_checks/parity_updater_static.py::next_available_id(shard_filename="social_narrative.yaml")` to confirm at implementation time rather than hardcoding, since another ticket may land first.
- `docs/guidelines/intentional_divergences.md`: this ticket's own Scope requires a grounded decision on the leader-death-succession question, and requires an entry here **if diverging** from Group's behavior. Recommendation (see Risks and Open Questions below): **Clan should diverge from Group** (succession/leader-reassignment intent, not unconditional dissolution) — so this doc requires a new entry. Recommend `Status: DEFERRED` (matching the existing "World Assembly / Service Assembly — Stabilized — DEFERRED" precedent in this same file) since the actual succession-execution logic is out of this ticket's scope (owned by idea 40/M4) — this ticket only records the schema-level intent/decision, not a ratified runtime behavior with a `Verification` test path yet.

The `docs/simulation/domains/party_contract.md` doc (path: `docs/simulation/domains/party_contract.md`) is not required to change for this ticket: it documents `GroupRecord`/`PartyLifecycleService` only, and this ticket does not touch either — it only defines a new, separate `ClanState` dataclass. (It does have its own pre-existing SOC-176/189 documentation gap, noted above under Mechanics/Engine Constraints, but fixing that is not this ticket's scope.)

The `docs/brainstorm/rpg_expected_schemas.html` doc (path: `docs/brainstorm/rpg_expected_schemas.html`) is not required to change for this ticket: it is a forward-looking brainstorm/roadmap tracking doc (status badges like "New"/"gated"), not an authoritative Mechanics Bible or engine contract page — its role is to track what's proposed, not to be kept in lockstep parity with landed code the way `docs/mechanics/`/`docs/parity_ledger/` are. Updating its status badges once `ClanState` lands is a reasonable follow-up but is not gated by `check_docs_to_update_coverage` and is not part of this ticket's stated Scope/AC.

The `docs/parity_ledger/faction.yaml` doc (path: `docs/parity_ledger/faction.yaml`) is not required to change for this ticket, despite documenting `FactionState` itself (see Parity Ledger Overlap below for why this is worth flagging as an open question rather than a silent decision) — the ticket's Related Docs and Scope explicitly name `social_narrative.yaml`, not `faction.yaml`, as the target shard.

## Parity Ledger Overlap

- **SOC-166** (`status: verified`, P0, "Contract party has founder/leader.") — Group-scoped, not reused per ticket's explicit instruction. Confirmed exists at line 1768.
- **SOC-228** (`status: verified`, P1, `PartyLifecycleService.check_leadership()` sociability election) — confirmed exists at line 2436, describes periodic re-election only, no death-triggered succession. Not reused per ticket's explicit instruction.
- **SOC-230** (`status: verified`, P1, `PartyLifecycleService.check_defection()` grievance-threshold defection) — confirmed exists at line 2485. Not reused per ticket's explicit instruction.
- **SOC-176 / SOC-189** (`status: verified`, P0/P0, "Party dissolves when leader is dead/missing" / "Group dissolution test covers dead leader") — confirmed at lines 1868 and 2001. This is the entry pair that establishes Group's no-succession behavior, cited correctly by the ticket.
- **New entry required**: `SOC-256` (or the id `next_available_id` computes at implementation time) in `social_narrative.yaml`, documenting `ClanState`'s frozen-dataclass shape and `to_canonical_dict`/`from_dict` round-trip — the schema-only equivalent of `FAC-001`'s role for `FactionState` (see below). Priority should be **P2** (schema/shape only, no apply-path/durable-persistence claim yet — unlike `FAC-001` which is P1 because it covers actual tick-to-tick persistence via `AuthoritativeState.factions`). A P0/P1 claim would be premature since `ClanState` is not wired into `AuthoritativeState` by this ticket.
- **Open question flagged for Plan, not decided here**: `docs/parity_ledger/faction.yaml` is the shard that documents `FactionState` itself (`FAC-001` through `FAC-014`, `FACTION-TENSION-001`) and — as of `TCK-20260826-PARITY-FACTION-CANONICAL-SCAN` (done, confirmed landed: `tools/parity_ledger_scan.py`'s `CANONICAL_LEDGER_FILES` tuple now includes `"faction.yaml"` as its 9th, most-recently-appended element) — is now fully canonical/gate-checked exactly like `social_narrative.yaml`. Given `ClanState` reuses `FactionState`'s shape "almost verbatim," `faction.yaml` would arguably be the more natural home for a `ClanState`-shape entry than `social_narrative.yaml`. However, the ticket's own Scope and Related Docs are explicit and unambiguous about `social_narrative.yaml` — this investigation does not override that explicit instruction, but flags it so the Plan phase can consciously ratify (not silently inherit) the `social_narrative.yaml` choice.

## Prior Work

- **`TCK-20260619-E53Aa-FACTION-STATE`** (done, `stored_artifacts/` read in full) — the direct precedent this ticket's Request Summary points to. Built `FactionState`, `FactionUpdate`, `AuthoritativeState.factions`, and the `apply.py` wiring together as one ticket (schema + full durable-state wiring), unlike this ticket which is schema-only by explicit scope choice. Its investigation.md correctly flagged (and its test suite guards) the `apply.py` constructor-omission hazard — relevant context for idea 40/M4's future wiring ticket, not this one.
- **`TCK-20260826-PARITY-FACTION-CANONICAL-SCAN`** (done) — landed the `faction.yaml`-as-canonical fix referenced above under Parity Ledger Overlap. Directly relevant to the `social_narrative.yaml` vs `faction.yaml` open question.
- **`TCK-20260619-E41B-LEADERSHIP`** / **`TCK-20260619-E41D-DEFECTION-ESCORT`** — built `PartyLifecycleService.check_leadership()`/`check_defection()` (SOC-228/230), read in full above via `party_lifecycle.py`.
- No `stored_artifacts/` entry for any prior Clan-specific ticket exists — confirmed via `ls stored_artifacts/ | grep -i clan` (no hits). This is genuinely the first `ClanState`-focused ticket.

## Risks and Open Questions

1. **Succession-on-death decision (ticket-mandated open question, resolved here with a recommendation)**: Recommend **Clan diverges from Group** — succession (leader reassignment) rather than unconditional dissolution — because (a) the brainstorm doc's own stated rationale for `dissolved_tick` is explicitly framed around avoiding "cross-generational Clans silently break[ing]" (`rpg_expected_schemas.html:617`), implying Clans are meant to be multi-generational political entities unlike small adventuring parties; (b) a `leader_entity_id: Optional[str]` field that can never be reassigned without dissolving the whole entity provides no signal beyond what `dissolved_tick` alone already gives. This is a **recommendation for Plan to ratify**, not an implemented behavior — the actual succession logic is out of this ticket's scope (idea 40/M4). If Plan overrides this recommendation and decides Clan should mirror Group's dissolve-on-death behavior instead, no `intentional_divergences.md` entry is needed and the "Docs Requiring Update" bullet above should be dropped.
2. **Territory contiguity (ticket-mandated open question, resolved here with a recommendation)**: Recommend **no contiguity enforcement** — `home_region_ids` should permit non-contiguous holdings, matching `FactionState.territory`'s existing precedent exactly. Confirmed via direct code read that (a) `apply.py:348`'s territory merge is a plain set union/difference with zero adjacency logic, and (b) `RegionState` has no adjacency/neighbor field of any kind to even compute contiguity from. Since this ticket reuses FactionState's shape "almost verbatim" per its own Request Summary, inheriting the same lack-of-constraint is the lowest-risk, most consistent choice — building contiguity validation would require a net-new region-adjacency data model that doesn't exist anywhere in the codebase today, which is well beyond this ticket's schema-only scope.
3. **`social_narrative.yaml` vs `faction.yaml` for the new parity entry** — see Parity Ledger Overlap above. Not blocking (ticket is explicit), but Plan should consciously confirm rather than silently accept.
4. **Field id types** (`member_entity_ids` as `int` vs `str`, `home_region_ids` as `str`) need explicit pinning at Plan time — see Mechanics/Engine Constraints note above. Getting this wrong would create an inconsistency with `GroupRecord.member_ids: Set[int]` (entity ids are `int` throughout the rest of the codebase) if `ClanState` used `str` entity ids instead.
5. **Related Code Areas gap**: `src/systems/social_systems/groups.py` does not exist (see Current Behavior). If Plan/Implementer copy this path forward uninspected, they'll hit a file-not-found. The real file is `src/systems/world_systems/groups.py`.

## Anti-Drift Hazards

- **Do not add `clans: Dict[str, ClanState]` to `AuthoritativeState`, a `ClanUpdate` type, or any `apply.py`/`StateUpdate.merge_many()`/`is_noop()` wiring in this ticket.** That is explicitly idea 40/M4's job (Out of Scope section, and to avoid the exact same-dataclass race the ticket calls out). This ticket's implementation should look like a standalone dataclass definition plus its own unit test file — nothing touches `AuthoritativeState`, `StateUpdate`, or `apply.py`.
- **Do not implement succession-on-death or dissolution logic.** Recording the *decision* (via `intentional_divergences.md` if diverging) is in scope; writing the code that executes it is not.
- **Do not reuse SOC-166/228/230** for the new parity entry — ticket is explicit that this must be a dedicated, new entry.
- **Do not silently redirect the parity entry to `faction.yaml`** even though it may be the more natural home — flag it (done above), let Plan decide explicitly.
- **Do not touch `Faction(IntEnum)`** (`src/core/enums.py`) or `EntityState.identity.faction: int` — these are the existing, unrelated entity-level faction concept (numeric enum, membership-agnostic) and must not be confused with the new `ClanState`/`FactionState` (str-keyed, durable, membership/territory-bearing) concept, mirroring the exact same anti-drift hazard the E53Aa investigation already flagged for `FactionState`.
- **Do not add an `EntityState.identity.clan_id` field.** The dual-sided lookup precedent (Group's `identity.group_id`) is genuinely relevant future context for idea 40/M4, but adding it here would touch `EntityState`/`IdentityComponent`, outside this ticket's dataclass-only scope.
