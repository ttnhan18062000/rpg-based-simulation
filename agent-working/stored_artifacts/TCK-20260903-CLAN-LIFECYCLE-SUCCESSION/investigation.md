---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION
artifact_type: investigation
tags: [faction, social]
---

# Investigation — TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Current Behavior

### `ClanState` schema (schema-only today) — `src/core/state.py:678-718`
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
```
`to_canonical_dict()`/`from_dict()` at lines 691-718 mirror `FactionState`'s pattern exactly
(sorted tuple fields, `_canonical_cache`). **No assets/institutional-footprint field exists.**
Confirmed by direct read — the field list above is exhaustive.

### `FactionState` — the structurally closest wired precedent — `src/core/state.py:639-676`
Same shape family (`faction_id`, tuples, dict fields, `tension_level`), differs only in domain
fields (`territory`, `resources`, `diplomatic_relations`, `active_doctrines`,
`military_strength`). `FactionState` has no per-instance dissolution field — factions never
dissolve today, which is why the ticket's "zero assets" dissolution AC has no field to reuse from
`FactionState` either.

### `PartyLifecycleService.check_leadership()` — `src/systems/social_systems/party_lifecycle.py:43-119`
SOC-228. Pure sociability-margin comparison: elects `best_id` only when
`best_sociability - current_sociability >= 0.2` (line 94), tiebreak lowest entity id (line 88-91).
**Confirmed: no leader-liveness check anywhere in this function** — `current_sociability =
sociabilities.get(group.leader_id, 0.0)` (line 85) silently defaults to `0.0` if the leader isn't
in the scoreable-members map, which then makes *any* live candidate with sociability >= 0.2 win
election — but this only fires on the 100-tick interval gate (line 69), never immediately on
death, and requires a member list that's already filtered by group membership, not clan
membership. This function operates on `GroupRecord`/`group.member_ids`, not `ClanState` — it
cannot be reused directly for Clan succession; the ticket's own framing ("must be built fresh")
is correct.

### `GroupSystem.update_groups()` dissolve-on-dead-leader — `src/systems/world_systems/groups.py:75-108`
SOC-176/SOC-189. Runs per relevant group each tick (line 75, from `get_relevant_group_ids`
dirty-tracking). Leader liveness check at lines 93-97:
```python
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
Unconditional dissolution, no succession branch. `is_alive`/`is_active` (lines 32-57) correctly
read same-tick `current_update.entity_updates` before falling back to `state.entities` — this is
the same-tick-effective-state pattern the ticket's succession logic should also use (a leader who
dies earlier in the same tick must not still read as alive). This whole path is Group-specific
and explicitly out of scope — confirmed untouched by this ticket's scope.

### `AuthoritativeState`/`StateUpdate`/`apply.py` wiring — traced via `FactionState` (`FactionUpdate`, E53Aa)
`FactionState` is the closest real, already-wired precedent for a top-level dict-keyed durable
registry (as opposed to `MarriageState`, which is a per-entity `StrategicComponent.marriages`
record applied via `EntityUpdate.strategic` — a different shape entirely, not the right precedent
for `ClanState`, since `ClanState` is keyed by `clan_id` at the `AuthoritativeState` top level like
`FactionState` is keyed by `faction_id`, not by owning entity). Wiring touches exactly 6 points,
all confirmed by direct read:

1. **Field declaration** — `AuthoritativeState.factions: Dict[str, "FactionState"] = field(default_factory=dict)` (`src/core/state.py:1232`).
2. **Read-only view** — `AuthoritativeState.to_readonly()` wraps it: `factions=ReadOnlyDict(self.factions)` (`src/core/state.py:1314`).
3. **`StateUpdate.faction_updates: List[FactionUpdate] = field(default_factory=list)`** (`src/core/updates.py:999`).
4. **`StateUpdate.is_noop()`** includes `not self.faction_updates` in its all-fields-empty check (`src/core/updates.py:1025`).
5. **`StateUpdate.merge_many()`** — accumulator seeded (`new_faction_updates = list(self.faction_updates)`, line 1082), extended per merge skipping no-ops (`new_faction_updates.extend(fu for fu in other.faction_updates if not fu.is_noop())`, lines 1151-1153), and threaded into the final `replace(...)` call (`faction_updates=new_faction_updates`, line 1216).
6. **`src/engine/apply.py:351-377`** (`ApplyPath.apply_partial`, Epic 5.3Aa comment) — builds `new_factions = dict(getattr(prior_state, "factions", {}))`, loops `update.faction_updates` skipping `is_noop()`, creates a fresh `FactionState(faction_id=fu.faction_id)` if absent, applies each delta/set field via `dataclasses.replace(existing, ...)`, clamps `tension_level` to `[0.0, 1.0]`. The resulting `new_factions` dict is passed as a constructor kwarg to the new `AuthoritativeState(...)` at line 429 (`factions=new_factions`).

`FactionUpdate` (`src/core/updates.py:921-941`) is the typed mutation record shape to mirror for
`ClanUpdate`: one dataclass field per mutable `ClanState` field, plus `is_noop()`. No `DirtySet`
integration exists for factions anywhere in `src/core/dirty.py` (confirmed — zero hits for
`"faction"` in that file), so `ClanState` wiring does not need dirty-tracking either; this keeps
the wiring scope to exactly the 6 points above, no more.

**Not part of the wiring surface, confirmed by direct check:** `AuthoritativeState` has no
top-level `to_canonical_dict()`/`from_dict()` that enumerates `factions` (no such method exists on
the class at all — grep found none), and `src/replay/fingerprint.py` does not reference
`factions`/`faction` either. So `ClanState` wiring does not need to touch state-level
serialization or the fingerprint determinism check beyond what `FactionState` already didn't need.

### `SocialAppraisalSystem.appraise_contract()` — `src/systems/social_systems/appraisal.py:19-87`
Shared trust hard-cancel prelude, confirmed at **lines 47-54** (ticket says 48-54; line 47 is the
comment immediately above the first `if`):
```python
# Persistent Distrust for betrayers
if trust_score < 0.2 or (bond and bond.sentiment < -0.8):
    return ContractStatus.CANCELLED, ReasonCode.TOTAL_DISTRUST, {}

# Betrayal history check
if entity.social.betrayal_count > 0:
    if trust_score < 0.4:
        return ContractStatus.CANCELLED, ReasonCode.BETRAYAL_HISTORY, {}
```
Then a `contract.kind ==` dispatch chain (lines 57-87) routes to per-kind `_appraise_*` methods.
`TEACH`/`MARRIAGE`/`TEAM_UP` (lines 81-86, 75-76) are the "prelude-only, always accept once trust
passes" precedent the ticket cites — `_appraise_teach`/`_appraise_marriage` are one-line
`return ContractStatus.ACCEPTED, ReasonCode.X_ACCEPTED, {}` bodies (lines 333-341, 343-354).
`ContractKind` (`src/core/strategic.py:73-87`) has no `CLAN` member yet — must be added.

**Direction and durable-write pattern**, traced end-to-end via `CoreActions.execute_propose_marriage()`
(`src/engine/domain/core_actions.py:400-455`, dispatched from `"PROPOSE_MARRIAGE"` in
`src/engine/domain/action_router.py:61-62`):
1. Build a transient `ContractState(kind=ContractKind.MARRIAGE, source_id=proposer, target_id=target, status=OFFERED)`.
2. Call `appraise_contract(target, temp_contract, context)` — **the target appraises the source**, same direction `execute_recruit`/`execute_team_up`/`execute_trade` use.
3. On `ACCEPTED`, build the durable record and return typed `EntityUpdate`/`StateUpdate` objects — never a direct mutation.

For Clan joining specifically, step 3's durable-write target is **not** the `MarriageState`
per-entity pattern (`StrategicComponent.marriages` via `EntityUpdate.strategic`) — `ClanState` is
a top-level dict-keyed registry like `FactionState`, so joining/leaving should write a `ClanUpdate`
into `StateUpdate.clan_updates` (mirroring `FactionUpdate`/`StateUpdate.faction_updates`), not an
`EntityUpdate.strategic` field. This is a plan-phase design decision, not yet made in source —
flagged under Risks below since the ticket doesn't say which action-dispatch entry point
(`action_router.py`) will host `CLAN_JOIN`/`CLAN_LEAVE`, only that appraisal must route through
`appraise_contract()`.

### `tests/unit/domains/faction/test_clan_state.py::test_clan_state_does_not_touch_authoritative_state` (lines 70-75)
```python
def test_clan_state_does_not_touch_authoritative_state():
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

    assert "clan" not in {f.name.lower() for f in dataclasses.fields(AuthoritativeState)}
    assert "clan" not in {f.name.lower() for f in dataclasses.fields(StateUpdate)}
```
This is a **substring** check (`"clan" not in {...}`), not an exact-name check — it will fail the
moment any field whose lowercased name contains the substring `"clan"` is added to either
dataclass (e.g. `clans`, `clan_updates` — both natural names following the `factions`/
`faction_updates` precedent both contain `"clan"`). Once wiring lands per the `FactionState`
precedent above, this assertion becomes false by construction and the test must be replaced, not
merely edited to keep passing — replacing it with an assertion in the opposite direction
(mirroring `test_faction_state.py::test_authoritative_state_has_factions_field`, lines 43-58) is
the correct fix:
```python
def test_clan_state_is_wired_into_authoritative_state():
    from src.core.state import AuthoritativeState, ClanState
    from src.core.updates import StateUpdate

    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "clans")
    assert state.clans == {}
    field_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    assert "clans" in field_names

    update_field_names = {f.name for f in dataclasses.fields(StateUpdate)}
    assert "clan_updates" in update_field_names
```
(Exact field names `clans`/`clan_updates` are the Plan phase's call, following the
`factions`/`faction_updates` naming precedent — this investigation does not invent them
authoritatively, only recommends the precedent-consistent name.) This satisfies AC 6 exactly.
`test_clan_state_does_not_share_faction_state_identity` (lines 78-82) is unaffected by wiring and
should be left as-is.

## Mechanics / Engine Constraints

- **`docs/core/state.md`** — "Durable State Rule" (also restated in this project's own
  `CLAUDE.md`): anything surviving beyond the current tick must have a typed model, a stable
  `AuthoritativeState` location, a defined lifecycle, and tests. `ClanState` already has the typed
  model (TCK-20260831-CLAN-STATE-SCHEMA); this ticket must give it the stable location + lifecycle
  + tests the rule requires — that is the wiring itself.
- **`docs/core/update_intents.md`** ("Purpose"/"Intent lifecycle" sections) — durable changes must
  be expressed as frozen typed intents produced by read-only decision logic and applied only via
  the authoritative apply-path. `ClanUpdate` (mirroring `FactionUpdate`) is the typed-intent shape
  this constrains; direct `ClanState` field mutation anywhere outside `apply.py` would violate this.
- **Architecture Rule ("Durable State Rule" / "Authoritative Pipeline")** — decision logic
  (`SocialAppraisalSystem.appraise_contract()`, a succession-check service) reads state and returns
  typed updates; only `apply.py` commits them. This governs both the joining/leaving contract path
  and the succession/dissolution logic — neither may mutate `ClanState` in place.
- **`docs/mechanics/04_strategic_cognition.md` §8 "Marriage Proposal Law"** — the direct structural
  precedent for how a new `ContractKind` + `SocialAppraisalSystem` dispatch branch is documented
  (Gate / Direction / Durable record / Out of scope / Source subsections). Clan joining should be
  documented the same way, as a new numbered section in this same chapter (Clan is a social-contract
  mechanic living in the strategic-cognition domain, same as marriage/teach/team-up).
- **`docs/guidelines/intentional_divergences.md` §2.48** — already the authoritative record framing
  succession-vs-dissolution as an *Intentional Gameplay Change*; its own "Unblock condition" text
  names this exact ticket. The ticket's AC to flip DEFERRED→RATIFIED is directly required by this
  entry's own stated unblock condition, not a new obligation invented here.

## Docs Requiring Update

- `docs/guidelines/intentional_divergences.md`: §2.48's own text names this ticket as the unblock
  condition — its `Verification` field must be updated with the real landed test path and its
  Status flipped `DEFERRED` → `RATIFIED` (ticket AC, explicit).
- `docs/parity_ledger/social_narrative.yaml`: a new dedicated entry is required (ticket AC,
  explicit) — confirmed the highest existing `SOC-` id in this file is `SOC-262`, so the next free
  id is `SOC-263` (confirmed unused anywhere in `docs/`/`tests/`/`src/` via grep). Must follow the
  schema at `docs/parity_ledger/schema.json` (`id` pattern `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$` — `SOC-263`
  fits) and the `SOC-228`/`SOC-230` entries' prose style (verified logic ID + emitted-event +
  affected-file summary, `proof_type: parity`, `test_path` naming the new test module).
- `docs/mechanics/04_strategic_cognition.md`: needs a new numbered section (the file's highest
  numbered section today is "8. Marriage Proposal Law", so this would be "9. Clan Lifecycle Law" or
  similar) documenting Gate/Direction/Durable-record/Out-of-scope/Source for clan joining
  (`ContractKind.CLAN` + `appraise_contract()`), leaving, succession, and dissolution — this is a
  brand-new feature per this project's CLAUDE.md ("new logic/features/settings" require doc
  coverage the same as changes to existing behavior), and §8's own subsection shape is the direct
  structural precedent to reuse.

The `docs/systems/faction_contract.md` (path: `docs/systems/faction_contract.md`, under `docs/`)
is not required to change for this ticket: it documents `FactionState`/`FactionUpdate`/
`FactionDirective` and the Epic 5.3 faction-war/diplomacy pipeline specifically, and its own
opening line scopes it to "E53Aa–E53D complete." `ClanState` is a structurally similar but
identity-distinct class (confirmed via `test_clan_state_does_not_share_faction_state_identity`,
already passing and unaffected by this ticket) with no diplomacy/war/territory mechanics — it does
not belong in a doc scoped to the Faction system's own epic family.

`docs/core/state.md` (path: `docs/core/state.md`) is not required to change for this ticket: its
one mention of `"factions"` (line 77) is inside an illustrative, non-exhaustive list of
`ReadOnlyDict`-cached collections (`entities`, `buildings`, `quests`, `items`, `factions`) used to
explain the zero-allocation caching mechanism in general — it does not exhaustively enumerate every
`AuthoritativeState` collection (e.g. `groups`, `corpses`, `chests` are also absent from that same
list), so omitting `clans` from it is consistent with the doc's existing style, not a gap this
ticket introduces.

`docs/core/update_intents.md` (path: `docs/core/update_intents.md`) is not required to change for
this ticket: it documents the general intent-lifecycle contract (creation/apply-path law) without
enumerating specific per-subsystem intent types — `FactionUpdate` itself is not named there either
(confirmed via grep, zero hits), so `ClanUpdate` following the same unnamed-instance pattern is
consistent with the doc's existing scope, not a new gap.

## Parity Ledger Overlap

- **SOC-228** (`status: verified`, `priority: P1`) — `PartyLifecycleService.check_leadership()`.
  Documents Group's sociability-margin election exactly as it exists today; this ticket's Clan
  succession logic is explicitly a *different, margin-free* rule per its own AC, so SOC-228's text
  must **not** be edited to describe Clan behavior — it stays describing Group behavior verbatim.
  The ticket's own scope statement (SOC-166/228/230/256 explicitly not reused) confirms this reading.
- **SOC-176/SOC-189** (Group dissolve-on-dead-leader, `groups.py:93-108`) — out of scope, unmodified,
  confirmed by direct read; no parity ledger edit needed for these entries.
- **SOC-256** (`status: verified`, `priority: P2`) — the `ClanState` schema-only entry from
  TCK-20260831-CLAN-STATE-SCHEMA. Its own text explicitly states "not wired into
  AuthoritativeState, StateUpdate, or apply.py in this ticket — lifecycle actions... are owned by
  a separate, later ticket (idea 40/M4)" — i.e. this ticket. SOC-256 itself does not need editing
  (it accurately describes what TCK-20260831 delivered); the new wiring/lifecycle logic gets its
  own new entry (SOC-263, see Docs Requiring Update) rather than mutating SOC-256's historical
  scope description.
- **No P0 entries overlap this ticket's scope** — SOC-166/228/230/256 are P0/P1/P1/P2 respectively
  but none require edits (see above), so there is no P0 test_path gate blocking this ticket beyond
  its own new SOC-263 entry, which — once added at `status: verified` after implementation —
  requires its own passing `test_path` per schema (any `status: verified`/`divergent` entry
  requires non-null `v2_evidence` + `test_path`, confirmed via `docs/parity_ledger/schema.json`'s
  `allOf` conditional).

## Prior Work

- **`stored_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/`** (investigation.md, plan.md, test_plan.md) —
  the immediate predecessor; delivered the schema-only `ClanState` class and
  `test_clan_state.py`'s 5 tests. Its investigation.md documents the same `FactionState`
  serialization-pattern reuse this ticket's wiring extends further.
- **`stored_artifacts/TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT/`** — the direct precedent for "new
  `ContractKind` + `appraise_contract()` dispatch branch, no shared generic `ProposalState` base
  class" pattern the ticket's Scope section names explicitly. Its Decision 4 (referenced in
  `_appraise_marriage`'s own docstring) explains why no `eligibility_gate`/utility model was added
  beyond the shared trust prelude — the same reasoning likely applies to a Clan joining appraisal,
  though the Plan phase should confirm rather than assume, since Clan joining plausibly warrants a
  distinct gate (e.g. tension-level or existing-membership checks) that Marriage's 1:1 relationship
  model didn't need.
- **`docs/done tickets/TCK-20260619-E53Aa-FACTION-STATE`** — the original FactionState wiring
  ticket; `working_log.csv` entry: "FactionState/FactionUpdate typed models and wired factions into
  AuthoritativeState and apply-path; 10 new tests pass" — confirms 10 is roughly the right order of
  magnitude for a comparable wiring-plus-tests ticket, useful for Plan-phase sizing.
- **`TCK-20260619-E41B-LEADERSHIP`**/**`TCK-20260619-E41D-DEFECTION-ESCORT`** (Related Tickets) —
  the source tickets for `check_leadership`/`check_defection`, confirming SOC-228/SOC-230's origin
  and that they are Group-only, never touched Clan.
- **`TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`** (Related Tickets, Out of Scope) — personal
  inheritance/heir assignment is a distinct, already-shipped mechanic; not re-verified in depth
  here since the ticket explicitly excludes it, but flagged as a naming-collision risk below (Anti-
  Drift Hazards) since "succession" language could accidentally conflate the two systems in docs.

## Risks and Open Questions

1. **[Ticket-flagged, unresolved] "Zero assets" dissolution AC has no backing schema field.**
   Confirmed by direct read: `ClanState` has exactly 8 fields (`clan_id`, `name`,
   `member_entity_ids`, `home_region_ids`, `tension_level`, `leader_entity_id`, `founded_tick`,
   `dissolved_tick`) — none represent assets or an institutional footprint. Two real options, per
   the ticket's own Out-of-Scope guidance ("if out of reach this ticket, defer explicitly as an
   open question, never silently invent"):
   - **(a)** Add a minimal new `ClanState` field (e.g. `asset_ids: Tuple[int, ...] = ()`, or reuse
     an existing concept like counting `home_region_ids` as the "institutional footprint" measure
     — the AC never actually requires a *new* asset concept, only *some* asset/institutional
     measure, and `home_region_ids` already exists and is schema-present today). Reusing
     `home_region_ids` as the footprint measure is the smallest-diff option and needs zero schema
     change, but conflates "has territory" with "has assets," which may not match the ticket
     author's intent.
   - **(b)** Scope the dissolution AC down to `member_entity_ids`-only (dissolve when empty), and
     explicitly record in `intentional_divergences.md`/the ticket's Assumptions that the
     "AND assets empty" half is deferred to a follow-up ticket once a real asset/holdings concept
     exists elsewhere in the codebase (none was found in this investigation — confirmed no
     Clan-adjacent asset/holdings field anywhere in `src/core/state.py`).
   This investigation does **not** resolve this — it is squarely a Plan-phase decision the ticket
   itself defers, and doing so silently would violate the ticket's own explicit instruction.
2. **Which action-dispatch entry point hosts Clan join/leave** is undecided in source today —
   `action_router.py` has string-keyed dispatch (`"PROPOSE_MARRIAGE"`, etc.); Plan phase must pick
   `"JOIN_CLAN"`/`"LEAVE_CLAN"` (or equivalent) names and register them, following
   `execute_propose_marriage`'s shape but writing a `ClanUpdate` (registry-style) rather than an
   `EntityUpdate.strategic` (per-entity-style) durable record — see Current Behavior above.
3. **Succession trigger mechanism is unspecified**: unlike Group's `GroupSystem.update_groups()`
   (which runs every tick over `get_relevant_group_ids`), there is no existing per-tick Clan
   processing pass. Plan phase must decide whether Clan succession runs as a new phase in
   `pipeline.py` (mirroring `FactionDecisionPhase`/`FactionAwarenessService`'s Phase 8b/8c
   placement) or as a service invoked elsewhere. This is a real architectural sizing question the
   ticket's own Assumptions section already flags ("architecturally larger than a typical 'add a
   service function' change").
4. **`ContractKind.CLAN` naming and terms schema** are undecided — Plan phase must define what
   `contract.terms` a Clan-join offer carries (analogous to `daily_pay`/`risk_level` for
   recruitment, or the empty `{}` marriage uses).
5. **New `ReasonCode` members needed** (e.g. `CLAN_JOIN_ACCEPTED`/`CLAN_JOIN_DECLINED`) — confirmed
   `src/core/enums.py`'s `ReasonCode` has no Clan-related members today; must be added alongside
   the new `_appraise_clan()` dispatch branch.
6. **New event class(es) needed** for "leaving a Clan emits a Clan-specific event" (AC, explicit) —
   confirmed no `ClanLeftEvent`/`ClanSuccessionEvent`-equivalent exists in
   `src/observability/events.py` today; `LeadershipChangedEvent`/`BetrayalDesertionEvent` (lines
   276-324) are the direct structural precedent (frozen `SimulationEvent` subclass,
   `event_category="social"`, custom `__init__` building a default `message`). Confirmed no central
   event-type registry needs touching beyond the class definition itself (grep of
   `event_extractor.py`/`event_shapers.py`/`chronicle/naming.py` for the existing
   `leadership_changed`/`betrayal_desertion` strings returned zero hits — those event types aren't
   special-cased anywhere else), so a new Clan event class is low-blast-radius.

## Anti-Drift Hazards

- **Do not let SOC-228 (Group leadership) or the shared `check_leadership()` function get modified
  or reused for Clan succession.** The ticket is explicit that Clan succession has no 0.2-margin
  gate and must be built fresh; any temptation to add a `clan: bool` flag to
  `PartyLifecycleService.check_leadership()` to "reuse" it would silently change Group's own
  behavior parity (SOC-228 is `status: verified` today) and must be avoided.
- **Do not modify `GroupSystem.update_groups()`'s dead-leader dissolution branch
  (`groups.py:93-108`, SOC-176/SOC-189)** — confirmed untouched territory; any shared helper
  extraction between Group's dissolution and Clan's succession must not alter Group's existing
  unconditional-dissolution semantics.
- **Do not touch the shared trust-hardcancel prelude** (`appraisal.py` lines 47-54) when adding the
  `CLAN` dispatch branch — the AC says this explicitly, and it's shared by every other contract
  kind (RECRUITMENT/LOAN/TEACH/MARRIAGE/etc.); any Clan-specific gating (e.g. tension-level checks,
  already-a-member checks) belongs in a new `_appraise_clan()` method, not the shared prelude.
- **Do not conflate this ticket's "succession" (Clan `leader_entity_id` reassignment on death) with
  `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s "succession" (personal inheritance/heir assignment)** —
  both use the word "succession" but are unrelated systems on unrelated durable state
  (`ClanState.leader_entity_id` vs. whatever heir-assignment state that ticket introduced). Keep
  doc language (`intentional_divergences.md` §2.48 update, the new Mechanics Bible section)
  unambiguous about which "succession" is meant.
- **Idea 68 (Inter-Clan Relations) scope creep**: `ClanState.tension_level` already exists in the
  schema and is tempting to wire up more thoroughly than "what joining/leaving naturally touches"
  (ticket's own Out-of-Scope wording) — e.g. do not add inter-clan diplomacy, alliance, or
  war-adjacent logic mirroring `FactionState.diplomatic_relations`; that's explicitly idea 68.
- **`FactionUpdate`'s `tension_level` clamp-to-`[0.0,1.0]` pattern (`apply.py:371`) should be
  mirrored exactly for `ClanUpdate`'s `tension_level`-equivalent field**, if the Plan phase adds
  one — don't let Clan tension escape the `[0.0, 1.0]` invariant `FactionState` enforces, since
  `ClanState.tension_level`'s docstring gives no independent range and the schema ticket explicitly
  modeled it on `FactionState`.
- **The `test_clan_state_does_not_touch_authoritative_state` rename must not silently disappear
  as a regression check** — it should become the wired-equivalent positive assertion (see Current
  Behavior above), not simply be deleted, since it's the one test in the whole suite currently
  proving the wiring gap exists and needs to instead prove the wiring landed correctly.
