---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
artifact_type: investigation
tags: [social]
---

# Investigation — TCK-20260904-CLAN-REPUTATION-ASSOCIATION

## Current Behavior

**`ClanState` (src/core/state.py:751-797)** — frozen slots dataclass, fields: `clan_id`, `name`,
`member_entity_ids: Tuple[int,...]`, `home_region_ids`, `asset_ids`, `tension_level: float`,
`leader_entity_id`, `founded_tick`, `dissolved_tick`. `to_canonical_dict()`/`from_dict()` (state.py:768-797)
sort all tuple collections. **No `clan_reputation` field exists today.** `test_clan_state_no_new_idea68_fields`
(tests/unit/domains/faction/test_clan_state.py:206-223) asserts the *exact* field set of both `ClanState`
and `ClanUpdate` — adding `clan_reputation` will fail this test until it is updated as part of this ticket's
own scope (this is an intentional, in-scope field addition, not the idea-68 scope-creep the guard exists to
catch — the guard's assertion literal must be extended, not weakened).

**`ClanUpdate` (src/core/updates.py:958-972)** — typed mutation record: `clan_id`,
`member_entity_ids_add/remove`, `leader_entity_id_set`, `dissolved_tick_set`. `is_noop()` (updates.py:966-972)
checks only these four. No reputation-delta field exists. `StateUpdate.clan_updates: List[ClanUpdate]`
(updates.py:1032) is merged via `StateUpdate.merge()` (updates.py:1189-1190, filters `is_noop()`).

**Apply path — `src/engine/apply.py:379-394`** — the *only* sanctioned mutation point for `ClanState`.
Iterates `update.clan_updates`, skips `is_noop()`, looks up/creates the existing `ClanState`, computes
`new_members`, `new_leader`, `new_dissolved`, and calls `replace(existing, ...)`. Any new
`clan_reputation` field needs a corresponding branch here (additive delta pattern, mirroring how
`FactionState.tension_level` is clamped at apply.py:371, or `SocialComponent.notoriety_score`'s
additive-delta pattern in `RelationshipService.process_update()`).

**Reverse lookup gap — CONFIRMED, still absent.** Grepped `src/core/state.py` for `clan_id` outside
`ClanState` itself: zero hits. `IdentityComponent` (state.py:571-593) has `group_id: Optional[int]` for
Group/Party membership but no equivalent `clan_id` field. The only membership record is
`ClanState.member_entity_ids`. `ClanLifecyclePhase.resolve()` (src/engine/pipeline_phases/clan_lifecycle.py:71-89)
already does exactly the O(n_clans) pattern this ticket would need — it iterates `state.clans.items()`
each tick and cross-references `clan.member_entity_ids` against `state.entities`. No caching/indexing
of the reverse map exists anywhere in the codebase today (confirmed via `graphify query` — no
`ClanState` neighbor node represents an index).

**Real reputation-delta call sites this ticket's Scope names:**
- **Party defection — `PartyLifecycleService.check_defection()`** (src/systems/social_systems/party_lifecycle.py:143-166,
  hardcoded `notoriety_delta=2.0` at what is now line ~163). This is a **pure function** (group, entity, tick
  in; no `state` access) — it cannot itself resolve a clan_id. Its caller with real `state` access is
  **`GroupPhase.resolve()`** (src/engine/pipeline_phases/groups.py:129-154), which already loops
  `live_member_ids` and has `state` in scope. This is the correct real wiring point for a clan lookup +
  `ClanUpdate` append. Runs as pipeline phase `"groups"` (src/engine/pipeline.py:402).
- **Contract betrayal — `ContractService.resolve_contract_outcome()`** (src/systems/social_systems/contracts.py:183-259,
  the `betrayal and betrayer_id` branch at lines 227-231, `notoriety_delta=0.5`/`betrayal_increment=1`).
  **This branch is NOT reachable from any live pipeline phase today.** The only production caller,
  `ContractService.process_active_contracts()` (contracts.py:266-300, wired as pipeline phase
  `"active_contracts"` at pipeline.py:407), always calls `resolve_contract_outcome(entity, c_id, success=True, tick=...)`
  — `betrayal`/`betrayer_id` are never passed. The betrayal branch is exercised only by direct unit
  tests (`tests/unit/social/test_contract_lifecycle*.py`, `test_social_contracts.py`) calling the
  static method directly. **This is a real gap**, not an assumption: this ticket's AC2 "contract betrayal"
  path has no live production trigger to hook a `ClanUpdate` onto today. The implementation/test must
  either (a) extend `resolve_contract_outcome`'s own signature/return to optionally carry clan info,
  verified at the pure-function level (same precedent as `test_betrayal_consequence.py` testing
  `SocialAppraisalSystem.process_betrayal()` directly, which is itself also not wired to any pipeline
  phase caller), or (b) treat wiring a live betrayal trigger as separately out of scope and only test
  at the unit level. Flagged in Risks below — Plan phase must decide, not assumed here.

**Stranger-judgment read path — `SocialAppraisalSystem.appraise_contract()`** (src/systems/social_systems/appraisal.py:19-90).
Lines 29-45 are the exact blend formula:
```
public_trust = source_entity.social.public_reputation / 2.0   # 0.0 to 1.0
if bond:
    trust_score = (bond.sentiment + 1.0) / 2.0                # private history wins outright
else:
    history_trust = entity.social.trust_history.get(source_id, 0.5)
    trust_score = (public_trust * 0.7) + (history_trust * 0.3)   # "stranger" blend
```
The `else` branch (no `SocialBond`) is precisely the "no personal trust/familiarity history" stranger
case AC3 targets. Confirmed **unmodified since before idea 60** (see Risks — idea 60's own disclosed gap
note says it left this method untouched). This is where a `clan_reputation` blend term must be added,
distinguishable from the `if bond:` branch which must stay clan-blind (a member with direct history is
judged on that history, not diluted by clan reputation).

`_appraise_clan()` (appraisal.py:360-372) is the existing Clan-specific appraisal branch (used for
`ContractKind.CLAN` join offers) — always accepts once the shared trust prelude passes; it is a
different code path from the general stranger-judgment blend and is explicitly not in this ticket's scope
(joining logic, not general judgment of a member by an unrelated stranger).

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §10 "Clan Lifecycle Law"** (lines 1118-1207) is the sole
  Mechanics Bible documentation of `ClanState`'s wiring (idea 40/M4, SOC-264). It documents the
  join/leave/succession/dissolution mechanism and explicitly lists "Out of scope (deliberate): Idea 68
  (Inter-Clan Relations)... No Clan founding/creation logic... No personal inheritance/heir assignment."
  It does **not** mention idea 54/Guilt by Association at all — this ticket adds new law (a new
  `ClanState.clan_reputation` field and its read/write mechanism) that this chapter's existing "Source"
  list (lines 1197-1207) does not cover, so the chapter needs a new subsection.
- **Durable State Rule** (CLAUDE.md): `clan_reputation` must be a typed field with a stable
  `AuthoritativeState` location (satisfied: `AuthoritativeState.clans: Dict[str, ClanState]` already
  exists), a defined lifecycle (write only through `ClanUpdate` → `apply.py`'s clan-merge block, per
  Scope), inspection/debug visibility (via `to_canonical_dict()`), and tests.
- **SOC-217 (sole-authoritative-writer law)**, cross-referenced by SOC-267: the same discipline this
  ticket must follow for `ClanState` — apply.py's existing clan-merge block (apply.py:379-394) is the
  sole legal mutation point; direct `ClanState.clan_reputation=...` construction outside apply.py/tests
  is a violation, mirroring the `public_reputation`/`regional_reputation` guard pattern in
  `tests/architecture/test_social_write_paths.py`.
- **Determinism** (Scope item 5, CLAUDE.md "Do not break determinism"): any aggregation over
  `member_entity_ids` must iterate a fixed sorted order — `ClanState.to_canonical_dict()` already sorts
  `member_entity_ids` (state.py:774), and `apply.py`'s clan-merge already sorts `new_members` (apply.py:391);
  any new logic (e.g. an O(n_clans) reverse-lookup scan, or aggregating a clan's own reputation from
  members) must reuse `sorted(...)`, never raw dict/tuple iteration order.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §10 "Clan Lifecycle Law" is the only Bible chapter documenting `ClanState`; it has no coverage of the new `clan_reputation` field, its write mechanism (contract-betrayal/party-defection `ClanUpdate` deltas), or the stranger-judgment blend change in `appraise_contract()` — needs a new subsection (or an addendum to §10) once implemented.
- `docs/parity_ledger/social_narrative.yaml`: needs a new entry (next `SOC-268`+) recording the `ClanState.clan_reputation` schema addition, its write path, and the `appraise_contract()` blend change — per the existing Mechanics Bible & Parity Ledger Mapping row for idea 54 (`docs/brainstorm/rpg_feature_atlas.html:1054`: "None | social_narrative.yaml (+ infrastructure.yaml if same field) | Same replay-determinism caveat as 53"). The "infrastructure.yaml if same field" branch does **not** apply — `clan_reputation` is confirmed a structurally distinct new field on `ClanState`, not the same field idea 53/60 touch (see Risks).
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`: line 95 currently reads only "Gated on M2's idea 36 (Clan) existing as real state" with no status update — needs the same retroactive status-update annotation pattern already used for ideas 53/60 (lines 89-94) once this ticket ships, including a correction: lines 86-88's claim that idea 60 "changes the shape of the same field 53/54 write" is confirmed inaccurate for idea 54 specifically — idea 54 writes a new field on `ClanState`, not `SocialComponent.public_reputation`/`regional_reputation`.

The `docs/guidelines/intentional_divergences.md` doc (path: `docs/guidelines/intentional_divergences.md`) is not required to change for this ticket unless the implementation introduces a genuine behavioral divergence from documented legacy/Bible behavior — the additive `clan_reputation` field and stranger-judgment blend are new mechanics, not a divergence from an existing documented rule, so no entry is anticipated at investigation time; the Plan/Implement phase should re-confirm this if the chosen aggregation formula ends up conflicting with any existing documented reputation rule.

The `docs/brainstorm/rpg_expected_schemas.html` and `docs/brainstorm/rpg_feature_atlas.html` docs (paths as given) are living design-tracking docs, not authoritative Mechanics Bible/parity-ledger sources — updating them is a repo convention observed on sibling tickets (e.g. idea 60's retroactive status-update note at `rpg_feature_atlas.html:2677`) but not independently gate-checked the way `docs/mechanics/` and `docs/parity_ledger/` are; recommended as good practice during Finalize but not listed as a Format-1 required bullet here since `done-checker`'s static coverage check does not parse `docs/brainstorm/` paths from this section.

`docs/parity_ledger/faction.yaml` is not required to change: grepped for `clan`/`Clan` and found only an unrelated content string (`orc_clan`, content data, not a ClanState entry) — all real ClanState-related parity entries (SOC-256, SOC-264) live in `social_narrative.yaml`, not `faction.yaml`, confirming the existing pattern this ticket should follow.

## Parity Ledger Overlap

`docs/parity_ledger/social_narrative.yaml`:
- **SOC-256** (`status: verified`, `priority: P2`) — original `ClanState` schema shape (idea 36, TCK-20260831-CLAN-STATE-SCHEMA). Does not need to change (schema-only entry, predates lifecycle wiring) but is the baseline this ticket extends.
- **SOC-264** (`status: verified`, `priority: P1`) — `ClanState` wiring into `AuthoritativeState`/`StateUpdate`/`apply.py` (idea 40/M4, TCK-20260903-CLAN-LIFECYCLE-SUCCESSION). This entry's `v2_evidence` file list (state.py, updates.py, apply.py, appraisal.py, clan_lifecycle.py, pipeline_phases/clan_lifecycle.py, core_actions.py, events.py) will gain new touched files (`party_lifecycle.py`/`groups.py` for the defection hook, `contracts.py` for the betrayal hook) — **does not require a status change** (still accurately describes what it documents) but a doc-updater should consider whether a new entry vs. an amendment to SOC-264's `v2_evidence` is cleaner; recommend a **new** entry since this ticket adds new law (clan_reputation), not a correction to existing law.
- **SOC-266** (`status: verified`, `priority: P1`) — idea 60's `regional_reputation` entry. Confirms (see Risks) that idea 60's write path is `RelationshipService.process_update()` only, and does not touch `appraise_contract()` — direct evidence the idea-60 dependency is not load-bearing for this ticket's `appraise_contract()` change.
- **SOC-267** — idea 53's inherited-reputation-seed entry (`public_reputation` birth-seed). Same conclusion: writes a different field (`SocialComponent.public_reputation`) via a different mechanism (`V2EntityBuilder.birth_record()`), no overlap with `ClanState.clan_reputation`.
- No `P0` entries touched — SOC-256/264/266/267 are all `P1`/`P2`. No `test_path` currently points at a nonexistent file for any of these (all verified to exist during this investigation: `test_clan_state.py`, `test_clan_succession.py`, `test_clan_lifecycle.py`, `test_clan_appraisal.py`, `test_relationships.py`).

## Prior Work

- **TCK-20260831-CLAN-STATE-SCHEMA** (done) — added the base `ClanState` schema (SOC-256). No lifecycle wiring.
- **TCK-20260903-CLAN-LIFECYCLE-SUCCESSION** (done, SOC-264) — wired `ClanState` into the authoritative
  pipeline: `ClanUpdate`, `apply.py`'s clan-merge block, `ClanLifecyclePhase`, `ClanLifecycleService`
  (join/leave/succession/dissolution). This is the direct precedent this ticket's own `ClanUpdate`
  extension and apply.py branch should mirror exactly (additive-delta clamp pattern, typed-record-only
  mutation, sorted-collection determinism).
- **TCK-20260904-REPUTATION-LOCALITY-SCOPE** (done, idea 60, SOC-266) — added
  `SocialComponent.regional_reputation: Dict[str, float]`, additive to the retained `public_reputation`
  scalar, written solely through `RelationshipService.process_update()`. **Confirmed does not touch**
  `ClanState`, `appraise_contract()`, or any code this ticket needs to build on — see Risks/Open
  Questions for the full resolution of whether this ticket's stated dependency on it was load-bearing.
  Also introduced `tests/architecture/test_social_write_paths.py`, the precedent architecture-guard
  pattern for AC5's "zero writes to member `public_reputation`" test.
- **TCK-20260904-INHERITED-REPUTATION-SEED** (done, idea 53, SOC-267) — `public_reputation` birth-seed
  via `ReputationService.combine_public_reputation()` + `V2EntityBuilder.birth_record()`. Same conclusion:
  different field, different mechanism, no code overlap.

## Risks and Open Questions

- **RESOLVED — idea-60 dependency was not load-bearing.** The epic doc (`rpg_m5_memory_reputation_epic.md:86-88`)
  and feature atlas (`rpg_feature_atlas.html:2677`) both claim idea 60 "must sequence before or alongside
  53/54... since it changes the shape of the same field 53/54 write." This is verifiably **true for idea 53**
  (which writes `SocialComponent.public_reputation`, the same scalar idea 60 touches) but **false for idea 54**:
  this ticket's own field, `ClanState.clan_reputation`, lives on a structurally distinct dataclass
  (`ClanState`, not `SocialComponent`) that idea 60 never referenced (confirmed: SOC-266's `v2_evidence`
  lists only `social.py`, `updates.py`, `relationships.py`, `state.py`'s `EntityState.to_canonical_dict()`,
  and `fingerprint.py` — no `ClanState` mention). The one code location this ticket *does* need to modify
  that idea 60 also touches by proximity — `appraise_contract()` in `appraisal.py` — is confirmed
  **unmodified by idea 60** (explicitly disclosed as a still-open gap in idea 60's own status note:
  "`SocialAppraisalSystem.appraise_contract()` still reads only the global scalar, not the region-scoped
  field"). So `appraise_contract()` is in exactly the same state it would have been in had idea 60 never
  shipped. **Conclusion: the sequencing dependency was a hedge, not a real code constraint** — this ticket
  could have been implemented independently of idea 60's landing. This should be noted in the epic doc
  correction (see Docs Requiring Update) so future scoping doesn't repeat the same overstated claim.
- **OPEN — contract-betrayal path has no live pipeline trigger.** As detailed in Current Behavior,
  `resolve_contract_outcome(betrayal=True, ...)` is never called from any wired pipeline phase today.
  Plan phase must decide whether to (a) leave the betrayal-trigger-wiring gap out of scope and hook the
  `ClanUpdate` onto the pure function's own return value (tested at the unit level, consistent with
  existing test precedent), or (b) additionally wire a real trigger — the latter would be a meaningfully
  larger scope increase not currently in this ticket's Scope section and should be flagged back to the
  ticket owner if discovered to be required, not silently added.
- **OPEN — entity→clan reverse lookup mechanism.** Confirmed no index exists. Two real options: (1) plain
  `for cid, clan in sorted(state.clans.items()) if entity_id in clan.member_entity_ids` scan at each of
  the (currently two, possibly one if (a) above is chosen) call sites needing it, no new state; (2) a new
  index structure — out of proportion to a `float` field addition and risks its own staleness/durable-state
  questions (an index is itself a form of durable state needing the same typed-model/lifecycle treatment).
  Recommend (1) unless clan counts are shown to be large enough to matter — no evidence in this repo's
  scenarios/tests suggests clan counts anywhere near typical faction counts (2-6 in existing fixtures).
- **OPEN — `reputation_weight_on_stranger_judgment` has no anchor value.** The schema card
  (`rpg_expected_schemas.html:884`) flags this as `<span class="badge gap">New, open question</span>` with
  no proposed formula. Plan phase must pick a concrete blend weight (e.g. mirroring the existing
  `public_trust * 0.7 + history_trust * 0.3` split, perhaps `public_trust * 0.5 + clan_trust * 0.2 +
  history_trust * 0.3`) — this is a genuine open design question, not resolvable from source alone.
- **CONFIRMED — `ClanState` has no replay/fingerprint coverage today** (grepped `src/replay/fingerprint.py`
  for `ClanState`/`clans`/`clan_`: zero hits). `clan_reputation` therefore does **not** need
  `StateFingerprinter` coverage to preserve existing determinism guarantees — unlike idea 53/60's
  `public_reputation`/`regional_reputation`, which are both in the replay hash. This directly contradicts
  the schema mapping doc's blanket "Same replay-determinism caveat as 53" note
  (`rpg_feature_atlas.html:1054`) — that caveat does not actually apply here; flag as a doc inaccuracy
  worth correcting alongside the epic-doc fix above (non-blocking, informational).
- **OPEN — `test_clan_state_no_new_idea68_fields` will fail once `clan_reputation` is added**, by design
  (see Current Behavior / Anti-Drift Hazards). This is expected and must be updated as part of this
  ticket's implementation, not treated as a regression.

## Anti-Drift Hazards

- **`test_clan_state_no_new_idea68_fields`** (tests/unit/domains/faction/test_clan_state.py:206-223) is an
  explicit anti-scope-creep guard against idea 68 (Inter-Clan Relations). Adding `clan_reputation` to
  `ClanState`/`ClanUpdate` is in-scope for *this* ticket and requires updating this test's literal field-set
  assertions — but the implementer must not use this as license to add anything else (e.g. any
  `tension_level`-interaction field, which is explicitly idea 68 scope per `_appraise_clan()`'s own
  docstring at appraisal.py:369-370).
- **Do not wire through `ReputationUpdateService`/`PublicReputationProfile`/`QuestResolutionSystem`** — Scope
  explicitly excludes this. `ReputationUpdateService.process_witnessed_event()` (the `PublicReputationProfile`
  mutator) is confirmed dead code (zero call sites in `src/`, per `rpg_feature_atlas.html:2677` and this
  investigation's own grep) — do not resurrect it as a shortcut.
- **Do not mutate `SocialComponent.public_reputation` for clan-mates.** AC5 requires a source-text guard
  test confirming zero writes; the existing `tests/architecture/test_social_write_paths.py` pattern already
  scans all of `src/` for `public_reputation=`/`regional_reputation=` writes outside its allowlist — a new
  clan-reputation write path that accidentally also sets `public_reputation=` on a member would already be
  caught by that existing guard (defense in depth), but AC5 wants an explicit, ticket-scoped test on top.
- **`_appraise_clan()`'s trust prelude is shared** (appraisal.py:47-54, "the shared prelude... already
  expresses the entire trust gate") — the new stranger-judgment blend in `appraise_contract()`'s `else`
  branch (lines 42-45) must not be confused with or accidentally routed through `_appraise_clan()`, which
  handles CLAN-join contracts specifically, not general judgment of an unrelated clan member.
- **Sorted iteration is mandatory** wherever `member_entity_ids` (or any O(n_clans) `state.clans` scan) is
  touched — `apply.py`'s existing clan-merge block and `to_canonical_dict()` already establish this
  convention; any new reverse-lookup or aggregation code must not silently regress to raw dict/tuple
  iteration order (Python dict order is insertion-order-stable but not necessarily reproducible across
  different code paths that construct `state.clans` differently across a run vs. a replay).
- **`ClanLifecyclePhase` runs after `groups`, before `active_contracts`** (pipeline.py:402/404/407) — if the
  party-defection hook lands in `GroupPhase.resolve()` (before `clan_lifecycle`) and the contract-betrayal
  hook lands in the `active_contracts` phase (after `clan_lifecycle`), both read the **same** start-of-tick
  `state.clans` snapshot (phases don't see each other's same-tick `ClanUpdate`s applied yet — `apply.py`
  only commits at tick boundary) — this is consistent with the existing one-tick-lag pattern already
  documented for `ClanLifecycleService.process_dissolution()` (clan_lifecycle.py:141-145) and must not be
  "fixed" into some kind of intra-tick read-your-own-write pattern that doesn't exist elsewhere in this
  pipeline.
