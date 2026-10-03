---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
artifact_type: plan
tags: [social]
---

# Implementation Plan — TCK-20260904-CLAN-REPUTATION-ASSOCIATION

## Summary

Add `ClanState.clan_reputation: float` (default `1.0`, clamped `[0.0, 2.0]`, mirroring
`SocialComponent.public_reputation`'s own default/clamp at
`src/core/models/social.py:52` and `src/systems/social_systems/relationships.py:98-99`) as a
new durable field, written only through a new `ClanUpdate.clan_reputation_delta: float = 0.0`
field applied additively in `apply.py`'s existing clan-merge block
(`src/engine/apply.py:379-394`). Two real event sources produce this delta: party defection
(live-wired, since its real caller `GroupPhase.resolve()` already has full `state` access) and
contract betrayal (implemented at the pure-function level only, since its only production
caller never actually triggers the betrayal branch — a real, pre-existing gap, not something
this ticket's scope authorizes fixing). A new `ClanLifecycleService.find_clan_id_for_entity()`
static helper resolves entity→clan via a sorted O(n_clans) scan (no new index — clan counts are
small, no existing evidence they aren't). `appraise_contract()`'s no-bond ("stranger") branch
(`src/systems/social_systems/appraisal.py:42-45`) gets a documented additive-delta blend —
`public_trust*0.7 + history_trust*0.3 + (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` — that only
applies when `bond is None`; the bond branch (lines 39-41) stays untouched/clan-blind. This
formula is chosen specifically so it reduces bit-for-bit to the pre-ticket
`public_trust*0.7 + history_trust*0.3` formula whenever `clan_trust == 0.5` (no clan, or a clan
at neutral `clan_reputation`), preserving the P0 parity entry SOC-134
(`docs/parity_ledger/social_narrative.yaml:1438-1451`, pinning exactly this formula for the
no-bond branch) — see Step 7 for the full derivation. Both new deltas use a single shared,
documented constant (`-0.25`) rather than two arbitrarily-differentiated magnitudes, since the
schema card specifies no formula for either.

## Steps

### Step 1 — Add `ClanState.clan_reputation` field + serialization
**Files:** `src/core/state.py`
**Change:** Add `clan_reputation: float = 1.0` to the `ClanState` dataclass, immediately after
`tension_level: float = 0.0` (read at `src/core/state.py:762`, confirmed no existing
`clan_reputation` field on the class at lines 750-766). Add it to `to_canonical_dict()`
(state.py:768-783, insert `"clan_reputation": self.clan_reputation,` alongside
`"tension_level": self.tension_level,` at line 777) and `from_dict()` (state.py:785-797, insert
`clan_reputation=float(d.get("clan_reputation", 1.0)),` alongside the `tension_level=` line at
793). Default `1.0` and no explicit clamp-on-construction (matching `tension_level`'s own
pattern — `ClanState` itself never clamps; clamping happens at the apply-path merge step, see
Step 3) mirror `SocialComponent.public_reputation`'s default (`src/core/models/social.py:52`,
`= 1.0`) so a clan with no recorded reputation events reads as neutral, same semantic starting
point as an individual.
**Do NOT touch:** `home_region_ids`, `asset_ids`, `member_entity_ids`, `leader_entity_id`,
`founded_tick`, `dissolved_tick` — unrelated fields, no changes needed. Do not add any
`tension_level`-interaction or diplomacy/alliance field — that is idea 68 scope, guarded by the
test updated in Step 2.
**Verify:** `test_clan_state_clan_reputation_serialization_round_trip` (test_plan.md item 1).

### Step 2 — Update the idea-68 scope-creep guard test
**Files:** `tests/unit/domains/faction/test_clan_state.py`
**Change:** In `test_clan_state_no_new_idea68_fields` (lines 206-223, confirmed current literal
sets: `ClanState` = `{"clan_id", "name", "member_entity_ids", "home_region_ids", "asset_ids",
"tension_level", "leader_entity_id", "founded_tick", "dissolved_tick"}`; `ClanUpdate` =
`{"clan_id", "member_entity_ids_add", "member_entity_ids_remove", "leader_entity_id_set",
"dissolved_tick_set"}`), add `"clan_reputation"` to the `ClanState` set and
`"clan_reputation_delta"` to the `ClanUpdate` set. This is the only change to this test — do not
alter its structure, docstring intent, or add any other field to either literal set.
**Do NOT touch:** Any other assertion in `test_clan_state.py`.
**Verify:** `test_clan_state_no_new_idea68_fields` passes with the extended literals; this is
itself one of the "New Tests Required" items (test_plan.md item 2) and continues functioning as
the anti-idea-68 guard for any future addition.
**Depends on:** Step 1 (field must exist) and Step 3 (`ClanUpdate` field must exist).

### Step 3 — Add `ClanUpdate.clan_reputation_delta` + apply-path branch
**Files:** `src/core/updates.py`, `src/engine/apply.py`
**Change:** In `ClanUpdate` (`src/core/updates.py:957-972`), add
`clan_reputation_delta: float = 0.0` after `dissolved_tick_set: Optional[int] = None` (line
964). Extend `is_noop()` (lines 966-972) to also check `and self.clan_reputation_delta == 0.0`.
In `apply.py`'s clan-merge block (`src/engine/apply.py:379-394`), after computing `new_dissolved`
(line 389), add `new_reputation = max(0.0, min(2.0, existing.clan_reputation +
cu.clan_reputation_delta))` and pass `clan_reputation=new_reputation` into the `replace(existing,
...)` call at lines 390-394 — same additive-then-clamp pattern already used one block above for
`FactionState.tension_level` at `apply.py:371` (`max(0.0, min(1.0, new_tension))`), just with the
`[0.0, 2.0]` range matching `public_reputation`'s own clamp
(`src/systems/social_systems/relationships.py:99`).
**Concurrent writers to `StateUpdate.clan_updates` (the shared list this touches):** confirmed
via grep (`grep -n "clan_updates" src/`) there are exactly two writers today: (1)
`ClanLifecyclePhase.resolve()` (`src/engine/pipeline_phases/clan_lifecycle.py:93`, via
`update.merge(_StateUpdate(clan_updates=new_clan_updates))`), which appends via
`StateUpdate.merge()`'s `new_clan_updates.extend(cu for cu in other.clan_updates if not
cu.is_noop())` (`src/core/updates.py:1189-1191`) — additive, not replacing; (2) `apply.py`'s own
read-only consumption loop (`apply.py:381`, `for cu in update.clan_updates:`) — the sole
authoritative mutation point, unchanged by this step except for the new field/branch. Steps 4 and
5 below become the third and fourth *producers* into this same list (via `.merge()`/list-append,
not direct assignment) — this step only adds the field both of those steps' `ClanUpdate`
instances will populate; it does not itself add a new writer.
**Do NOT touch:** `member_entity_ids_add/remove`, `leader_entity_id_set`, `dissolved_tick_set`
merge logic (lines 387-389) — unchanged, no interaction with the new field.
**Verify:** Existing `test_clan_update_is_noop`, `test_clan_update_membership_add_remove`,
`test_state_update_merge_clan_updates`, `test_clan_state_persists_across_ticks` (test_plan.md
Regression Surface) must keep passing unmodified in behavior; new coverage folded into Steps 4/5's
tests (which exercise this branch end-to-end via `ApplyPath`).
**Depends on:** Step 1 (needs `ClanState.clan_reputation` to exist for `replace()` to accept it).

### Step 4 — Wire party-defection clan-reputation delta (live pipeline path)
**Files:** `src/systems/social_systems/clan_lifecycle.py`, `src/engine/pipeline_phases/groups.py`
**Change:** Add a new static helper `ClanLifecycleService.find_clan_id_for_entity(state:
AuthoritativeState, entity_id: int) -> Optional[str]` to `clan_lifecycle.py` (alongside the
existing `process_leave`/`process_succession`/`process_dissolution` static methods, following the
class's existing "pure-static service" convention documented at clan_lifecycle.py:29-32). Body:
`for clan_id, clan in sorted(state.clans.items()): if entity_id in clan.member_entity_ids: return
clan_id` then `return None` — sorted-by-`clan_id` iteration per the Determinism constraint
(mirrors the existing O(n_clans) pattern already used at
`src/engine/pipeline_phases/clan_lifecycle.py:71` for succession/dissolution, just made
reusable and explicitly sorted). In `GroupPhase.resolve()`
(`src/engine/pipeline_phases/groups.py:129-155`, confirmed via read: this loop already has full
`state` in scope, calls `PartyLifecycleService.check_defection(group, member_entity, tick)` at
line 129-131 and merges the returned `entity_upd`'s `notoriety_delta=2.0` at lines 153-155), add
immediately after the `if entity_upd is not None:` block (line 153-155): when `entity_upd is not
None` (i.e., a defection occurred), call `clan_id =
ClanLifecycleService.find_clan_id_for_entity(state, m_id)`; if `clan_id` is not `None`, append
`ClanUpdate(clan_id=clan_id, clan_reputation_delta=CLAN_REPUTATION_MISCONDUCT_DELTA)` (see
constant defined in Step 6) to a local `new_clan_updates: List[ClanUpdate] = []` list. After the
loop, change the final `return replace(update, groups_add_or_update=new_groups_add,
groups_remove=new_groups_remove, entity_updates=refined_entity_updates)` (lines 160-164) to also
pass `clan_updates=list(update.clan_updates) + new_clan_updates` — preserving whatever was
already in `update.clan_updates` on entry (confirmed empty at this point in the pipeline today,
since `groups` (`pipeline.py:402`) runs before `clan_lifecycle` (`pipeline.py:404`), the only
other writer — see Step 3's writer enumeration — but the explicit `list(update.clan_updates) +
...` form is required regardless so this doesn't silently regress if a future phase reordering
adds an earlier clan_updates writer).
**Do NOT touch:** `PartyLifecycleService.check_defection()` itself (`party_lifecycle.py:143-199`)
— it stays a pure function with no `state` access, unchanged; its existing `notoriety_delta=2.0`
entity-level output is untouched. Do not add a clan lookup inside `check_defection()` — the
lookup only happens in `GroupPhase.resolve()`, which has `state`.
**Verify:** `test_party_defection_produces_clan_reputation_clan_update` (test_plan.md item 4) —
assert via `ApplyPath.apply_partial`/`apply_generation` that a defecting clan member's clan's
`clan_reputation` actually decreases after a full apply cycle, not just that the raw `ClanUpdate`
object carries the delta. Also add the "no-clan" case (defector with no clan membership produces
no `ClanUpdate`, no crash) per the test plan's Anti-Drift Test Guards.
**Depends on:** Steps 1 and 3 (fields must exist).

### Step 5 — Contract-betrayal clan-reputation delta (pure-function level only — NOT live-wired) — DELIBERATE, CONFIRMED CHOICE
**Files:** `src/systems/social_systems/contracts.py`
**Change:** Add a new static method `ContractService.compute_betrayal_clan_reputation_update(
betrayer_id: int, state: AuthoritativeState, tick: int) -> Optional[ClanUpdate]` as a **separate**
function alongside `resolve_contract_outcome` — do **not** change `resolve_contract_outcome`'s
existing signature or its `Tuple[StrategicUpdate, List[SocialUpdate]]` return shape
(`src/systems/social_systems/contracts.py:183-190`, confirmed a 2-tuple return consumed by
`strat_up, bond_ups = ...`-style unpacking in every existing caller/test in
`test_contract_lifecycle.py`/`test_contract_lifecycle_phase7.py`/`test_social_contracts.py`/
`test_social_phase7.py`/`test_p1_semantic_hardening.py` per test_plan.md's Regression Surface —
changing it to a 3-tuple would break every one of those unpack sites, which the test plan requires
to "keep passing... unchanged"). The new method: `clan_id =
ClanLifecycleService.find_clan_id_for_entity(state, betrayer_id)` (import from
`src.systems.social_systems.clan_lifecycle`, reusing Step 4's helper — do not duplicate the scan
logic); if `clan_id` is `None`, return `None`; else return `ClanUpdate(clan_id=clan_id,
clan_reputation_delta=CLAN_REPUTATION_MISCONDUCT_DELTA)`.
**Live-pipeline reachability (disclosed, not fixed):** confirmed via read
(`src/systems/social_systems/contracts.py:264-300`) that `process_active_contracts()` — the only
production caller of `resolve_contract_outcome`, wired as pipeline phase `"active_contracts"`
(`src/engine/pipeline.py:407`) — always calls `resolve_contract_outcome(entity, c_id,
success=True, tick=current_tick)` (line 278) and never passes `betrayal=True`/`betrayer_id`. This
means `compute_betrayal_clan_reputation_update()` (and the `betrayal=True` branch of
`resolve_contract_outcome` itself, lines 227-231, which predates this ticket) has **no live
pipeline caller today** — it is only reachable from direct unit tests. This ticket does **not**
add a live betrayal trigger (that would be a real scope increase into `process_active_contracts`'
own decision logic for detecting betrayal, not named in this ticket's Scope) — this is a
disclosed, pre-existing gap, not a regression introduced here.

**This is a final, confirmed Plan-phase decision, not an open item carried forward to Implement.**
Re-confirmed on revision: wiring a live betrayal trigger into `process_active_contracts()` remains
out of scope. The ticket's Scope section asks this ticket to make a contract-betrayal event *also
produce a `ClanUpdate`* — it does not ask this ticket to make the betrayal branch itself reachable
from the live pipeline for the first time. Making it reachable would require new betrayal-detection
decision logic inside `process_active_contracts()` (deciding *when* a contract counts as
betrayed), which is a materially different, larger piece of work than this ticket's stated Scope
and is not named anywhere in it. The implementer must not treat this gap as something to
opportunistically fix while touching `contracts.py` in this step — the fix here is limited to
adding `compute_betrayal_clan_reputation_update()` as a new, separate, pure function and proving it
correct at the unit level (see Verify below); the unreachability itself is left exactly as found,
called out explicitly in the new test's own docstring so a future reader does not mistake
pure-function coverage for live-pipeline coverage.
**Do NOT touch:** `resolve_contract_outcome`'s signature, return type, or its existing
`notoriety_delta=0.5`/`betrayal_increment=1` behavior (lines 229-233) — unchanged. Do not modify
`process_active_contracts()` to start passing `betrayal=True` — out of scope (see above).
**Verify:** `test_contract_betrayal_produces_clan_reputation_clan_update` (test_plan.md item 3),
calling `resolve_contract_outcome(betrayal=True, betrayer_id=...)` for the existing entity-level
assertions AND separately calling `compute_betrayal_clan_reputation_update(betrayer_id, state,
tick)` for the new `ClanUpdate` assertion, then feeding that `ClanUpdate` through
`StateUpdate(clan_updates=[...])` → `ApplyPath.apply_partial`/`apply_generation` to prove the
applied-state change (matching the party-defection test's verification style at AC2, even though
no live pipeline phase invokes this path today — the test's docstring/comment must say so
explicitly). Also cover the no-clan case (betrayer with no clan → `None` returned, no crash).
**Depends on:** Steps 1, 3, and 4 (reuses `find_clan_id_for_entity` from Step 4).

### Step 6 — Define the shared reputation-delta constant
**Files:** `src/systems/social_systems/contracts.py` or a shared location referenced by both Step
4 and Step 5 (recommend a module-level constant in `src/systems/social_systems/clan_lifecycle.py`
next to `ClanLifecycleService`, e.g. `CLAN_REPUTATION_MISCONDUCT_DELTA = -0.25`, imported by both
`groups.py`/`clan_lifecycle.py` (Step 4) and `contracts.py` (Step 5), rather than defining it
twice).
**Change:** `CLAN_REPUTATION_MISCONDUCT_DELTA: float = -0.25`. Rationale (schema card
`rpg_expected_schemas.html:884` proposes no magnitude for either trigger — this is a genuine
Plan-phase decision, not left to Implement): a single shared negative constant, rather than two
independently-tuned magnitudes for betrayal vs. defection, since nothing in the source docs
distinguishes their relative severity at the clan level; `-0.25` is roughly an eighth of
`clan_reputation`'s full `[0.0, 2.0]` range (mirroring `public_reputation`'s own range) — clearly
measurable/nonzero in a single-event test without one betrayal or defection alone driving a clan's
reputation to its floor, consistent with `clan_reputation` representing a *slow-moving aggregate*
across a clan's whole membership rather than a per-member scalar.
**Do NOT touch:** `SocialUpdate.notoriety_delta` magnitudes (`0.5` at contracts.py:231, `2.0` at
party_lifecycle.py:196) — those are pre-existing entity-level constants, unrelated and unchanged.
**Verify:** Covered implicitly by Steps 4/5's tests asserting a nonzero, negative
`clan_reputation` delta.
**Depends on:** None (can be done first, referenced by Steps 4/5).

### Step 7 — Stranger-judgment clan-reputation blend
**Files:** `src/systems/social_systems/appraisal.py`, `docs/parity_ledger/social_narrative.yaml`
**Change:** In `appraise_contract()`'s `else` branch (no-`SocialBond` case,
`src/systems/social_systems/appraisal.py:42-45`, confirmed current code via read: `history_trust =
entity.social.trust_history.get(source_id, 0.5)` then `trust_score = (public_trust * 0.7) +
(history_trust * 0.3)`), add a clan lookup and an **additive delta term appended to the existing
formula**, not a re-weighted three-term blend: `clan_id =
ClanLifecycleService.find_clan_id_for_entity(state, source_id)` (import from
`src.systems.social_systems.clan_lifecycle`, reusing Step 4's helper — `state:
AuthoritativeState` is already an existing parameter of `appraise_contract()`, confirmed at
`appraisal.py:23`, so no signature change is needed here); `clan_trust = (state.clans[clan_id
].clan_reputation / 2.0) if clan_id else 0.5` (neutral default when the member has no clan,
mirroring `public_trust`'s own `0.0 to 1.0` normalization at line 37, and mirroring
`ClanState.clan_reputation`'s own neutral default of `1.0` from Step 1, which normalizes to
`1.0/2.0 = 0.5`); replace the `trust_score` line with:

```
trust_score = (public_trust * 0.7) + (history_trust * 0.3) + (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT
```

with `CLAN_INFLUENCE_WEIGHT: float = 0.2` defined as a new named module-level constant in
`appraisal.py` (alongside the existing `trust_score < 0.2` threshold literal at line 48, or as a
class-level constant on `SocialAppraisalSystem` — implementer's choice of exact placement, no
functional difference). **Corrected shape, superseding an earlier revision of this plan that used
a re-weighted three-term blend (`public_trust*0.5 + clan_trust*0.2 + history_trust*0.3`) — that
formula silently broke a P0 parity entry** (see below) because it changed `public_trust`'s and
`history_trust`'s own weights (0.7→0.5, 0.3 stayed but the sum was redistributed), which shifts
`trust_score` even when the observed member has no clan or a neutral-reputation clan. The
additive-delta shape keeps `public_trust*0.7 + history_trust*0.3` **completely intact** as the
base term and only adds a signed correction that is exactly `0.0` at the neutral point.

**P0 parity preservation — SOC-134 (`docs/parity_ledger/social_narrative.yaml:1438-1451`,
`priority: P0`, `status: verified`):** pins `appraise_contract()`'s no-bond branch to exactly
`trust_score = public_trust * 0.7 + history_trust * 0.3`, verified by
`tests/unit/social/test_parity_soc_134.py::TestSocialAppraisalWithNarrative` (confirmed via read:
`test_high_public_reputation_source_accepted` and `test_zero_public_reputation_source_rejected`,
`test_parity_soc_134.py:29-71` — neither test's `source` entity is given a clan via
`V2EntityBuilder`, so `find_clan_id_for_entity` returns `None` and `clan_trust` takes its neutral
default `0.5`). **Algebraic proof of neutral-case preservation:** at `clan_trust = 0.5`,
`(clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT = (0.5 - 0.5) * 0.2 = 0.0 * 0.2 = 0.0`, and
`trust_score = (public_trust * 0.7) + (history_trust * 0.3) + 0.0`, which is bit-for-bit identical
to the pinned formula for every value of `public_trust`/`history_trust` (adding exact `0.0`
in IEEE-754 float arithmetic never changes the addend). This holds both for the "no clan"
case (`clan_id is None` → `clan_trust = 0.5` by the explicit `else 0.5` default) and for a
clan at its own neutral default (`ClanState.clan_reputation = 1.0` from Step 1 → `clan_trust =
1.0 / 2.0 = 0.5`) — both collapse to the same `0.0` delta. Concretely re-verified against SOC-134's
own two test cases: `test_zero_public_reputation_source_rejected`
(`public_trust=0.0`, `history_trust=0.5` default) → `0.0*0.7 + 0.5*0.3 + 0.0 = 0.15 < 0.2` →
still `CANCELLED`/`TOTAL_DISTRUST`, unchanged; `test_high_public_reputation_source_accepted`
(`public_trust=1.0`, `history_trust=0.5` default) → `1.0*0.7 + 0.5*0.3 + 0.0 = 0.85`, still well
above threshold, unchanged.

**`CLAN_INFLUENCE_WEIGHT = 0.2` rationale** (the Plan-phase-chosen concrete value for the schema
card's unanchored `reputation_weight_on_stranger_judgment` field,
`rpg_expected_schemas.html:884`, flagged "New, open question"): `0.2` is carried over from this
plan's own earlier (flawed) three-term blend, which had assigned `clan_trust` a `0.2` share of a
1.0-sum blend — reusing the same magnitude here preserves the originally-intended *maximum size*
of clan influence (a full swing of `clan_trust` from its floor `0.0` to its ceiling `1.0` now
shifts `trust_score` by at most `±0.1`, i.e. `(1.0-0.5)*0.2` in either direction) while fixing the
mechanism that caused the parity break — no other weight redistribution happens, so `public_trust`
and `history_trust` keep their exact `0.7`/`0.3` shares at all times, clan-neutral or not.

**Parity ledger update required (Parity phase, not this plan's own step list — flagged here so
Implement/Parity know it's expected):** SOC-134's `v2_evidence`
(`social_narrative.yaml:1448-1451`) currently reads only `trust_score = public_trust * 0.7 +
history_trust * 0.3`; once this step lands, `v2_evidence` must be updated to describe the new
formula shape (`public_trust * 0.7 + history_trust * 0.3 + (clan_trust - 0.5) *
CLAN_INFLUENCE_WEIGHT`, noting the delta term is `0.0` at the documented no-clan case so the
pinned test's asserted behavior is unchanged) — **`status` stays `verified`, does NOT change**,
since the behavior at SOC-134's own documented (no-clan) case is unchanged; only the
`v2_evidence` text needs to stay accurate about the formula's real current shape for future
readers. This is a `v2_evidence`-text update, not a new entry — the parity-updater agent (Parity
phase) should treat SOC-134 as touched-but-still-verified, distinct from Step 6's Docs Requiring
Update item for a new `SOC-268`+ entry covering `clan_reputation` itself.
**Do NOT touch:** The `if bond:` branch (lines 39-41) — must remain exactly `trust_score =
(bond.sentiment + 1.0) / 2.0`, clan-blind, per the ticket's AC3 "distinguishably different"
requirement and the investigation's explicit warning against blending clan reputation into the
direct-history branch. Do NOT touch `_appraise_clan()` (appraisal.py:360-372, the `ContractKind.CLAN`
join-offer path) — a different, unrelated code path per investigation. Do NOT change SOC-134's
`status` field in the parity ledger — it stays `verified`.
**Verify:** `test_stranger_judgment_incorporates_clan_reputation` (test_plan.md item 5) — assert a
distinguishably different `trust_score` for low vs. high `clan_reputation` on the observed
member's clan when `bond is None`, AND an explicit regression assertion that the `bond`-present
branch's `trust_score` is unaffected by `clan_reputation` (test_plan.md's Anti-Drift Test Guards,
"easiest part of this ticket to accidentally get backwards"). **Additionally, and non-negotiably
for this step's completion:** the full existing `tests/unit/social/test_parity_soc_134.py` suite
(`TestSocialAppraisalWithNarrative::test_high_public_reputation_source_accepted` and
`::test_zero_public_reputation_source_rejected`) must pass **unmodified** — no edits to that test
file are permitted as part of this step; if either test fails after this change, the formula
implementation has a bug (most likely a sign error in the delta term or a wrong neutral
constant), not a reason to touch the P0-pinned test.
**Depends on:** Step 1 (`clan_reputation` field must exist), Step 4 (reuses
`find_clan_id_for_entity`).

### Step 8 — Determinism test for the reverse-lookup / aggregation path
**Files:** `tests/unit/domains/faction/test_clan_reputation_association.py` (new file, per
test_plan.md's recommended location)
**Change:** No production code change — this step adds
`test_clan_reputation_aggregation_is_deterministic` (test_plan.md item 6): construct an
`AuthoritativeState` fixture with multiple clans and multiple qualifying members, with
`state.clans` built in non-sorted insertion order, and assert `find_clan_id_for_entity()` /
the Step 4 and Step 5 `ClanUpdate`-producing call sites produce bit-identical output across
repeated calls regardless of dict insertion order (exercises `find_clan_id_for_entity`'s
`sorted(state.clans.items())` from Step 4).
**Do NOT touch:** Any production file — this step is test-only.
**Verify:** The new test itself, run as part of `pytest tests/unit/domains/faction/ ...`
(test_plan.md's Scoped Pytest Commands).
**Depends on:** Steps 1, 3, 4, 5 (all production code the test exercises).

### Step 9 — AC5 source-text guard: no writes to member `public_reputation`
**Files:** `tests/architecture/test_social_write_paths.py` (extend) or a new
`tests/architecture/test_clan_reputation_write_paths.py`
**Change:** Add `test_no_writes_to_member_public_reputation_from_clan_reputation_code`
(test_plan.md item 7): using `inspect.getsource()` on the specific new/modified functions from
Steps 4, 5, 7 (`GroupPhase.resolve`, `ClanLifecycleService.find_clan_id_for_entity`,
`ContractService.compute_betrayal_clan_reputation_update`, `appraise_contract`), assert none of
their source text contains a `public_reputation=` write (a *write*, i.e. keyword-argument
assignment — `appraise_contract`'s existing *read* of `source_entity.social.public_reputation` at
line 37 is not a write and must not trip this guard). Follow the same technique as the existing
`test_reputation_seed_write_path_does_not_reference_reputation_update_service` pattern already in
this file (per investigation's Anti-Drift Hazards).
**Do NOT touch:** The existing repo-wide scan/allowlist in `test_social_write_paths.py` beyond
adding this one new test function (or, if placed in a new file, no changes to the existing file at
all) — this file's existing tests are regression-only per test_plan.md.
**Verify:** The new test itself; `test_social_write_paths.py`'s existing tests must keep passing
unmodified (test_plan.md Regression Surface).
**Depends on:** Steps 4, 5, 7 (the functions it inspects must exist).

## Scope Guards

- Do not mutate any individual member's own `SocialComponent.public_reputation` or
  `regional_reputation` anywhere in this ticket's new code (Out of Scope, AC5).
- Do not wire through `ReputationUpdateService`, `PublicReputationProfile`, or
  `QuestResolutionSystem`'s quest-completion path (Out of Scope; `ReputationUpdateService
  .process_witnessed_event()` is confirmed dead code per investigation — do not resurrect it).
- Do not add a live pipeline trigger that makes `process_active_contracts()` start passing
  `betrayal=True`/`betrayer_id` to `resolve_contract_outcome()` — this ticket's Scope names the
  betrayal *event* as something to wire a `ClanUpdate` onto, not to make the betrayal branch
  itself reachable; that would be a genuine scope increase (investigation's Open Question (a),
  resolved here as "leave the trigger-wiring gap out of scope, disclose it").
- Do not touch idea 60's `SocialComponent.regional_reputation` field or its write path
  (`RelationshipService.process_update()`), and do not touch idea 53's birth-seed write
  (`V2EntityBuilder.birth_record()`) — sibling/prerequisite tickets, confirmed structurally
  unrelated (investigation's Risks section).
- Do not touch `ClanLifecycleService.process_leave`/`process_succession`/`process_dissolution`
  logic, `ClanLifecyclePhase`'s JOIN_CLAN/LEAVE_CLAN handling, or any `member_entity_ids`/
  `leader_entity_id`/`dissolved_tick`/`tension_level` merge logic in `apply.py` — unrelated to
  `clan_reputation`.
- Do not touch `_appraise_clan()` (`ContractKind.CLAN` join-offer appraisal) — a different code
  path from the general stranger-judgment blend this ticket modifies.
- Do not add a new entity→clan index/registry as durable state — the O(n_clans) scan
  (`find_clan_id_for_entity`) is the Plan-phase decision (investigation's Open Question (b)); an
  index would itself need its own typed-model/lifecycle treatment, out of proportion to a `float`
  field addition, and no evidence in this repo's fixtures suggests clan counts are large enough to
  need one.
- Do not add `ClanState`/`clan_reputation` coverage to `src/replay/fingerprint.py` — confirmed
  `ClanState` has zero references there today, and nothing in this ticket changes that (investigation:
  "CONFIRMED — ClanState has no replay/fingerprint coverage today").
- Do not add any `tension_level`-interaction, diplomacy, or inter-clan-relations field — idea 68
  scope, guarded by the updated `test_clan_state_no_new_idea68_fields`.
- Sorted iteration only: any scan over `state.clans` or `member_entity_ids` must use
  `sorted(...)`, never raw dict/tuple iteration order (Determinism constraint, CLAUDE.md).
- Do not implement Step 7's blend as a re-weighted three-term sum that changes `public_trust`'s or
  `history_trust`'s own coefficients (e.g. `public_trust*0.5 + clan_trust*0.2 +
  history_trust*0.3`) — that shape breaks the P0 parity entry SOC-134
  (`docs/parity_ledger/social_narrative.yaml:1438-1451`) and its pinned test
  (`tests/unit/social/test_parity_soc_134.py`). Step 7's formula must be the additive-delta form
  (base formula unchanged, `+ (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` appended) — see Step 7
  for the full derivation. Do not edit `test_parity_soc_134.py` to work around a formula that
  fails it — that is the Gate Integrity violation CLAUDE.md and this project's review process
  explicitly forbid.

## Dependency Map

- Step 1 (ClanState field) — no dependencies. Do first.
- Step 6 (shared constant) — no dependencies. Can be done in parallel with Step 1.
- Step 3 (ClanUpdate field + apply.py branch) — depends on Step 1.
- Step 2 (idea-68 guard test update) — depends on Steps 1 and 3.
- Step 4 (party-defection live wiring, adds `find_clan_id_for_entity`) — depends on Steps 1, 3, 6.
- Step 5 (contract-betrayal pure-function wiring) — depends on Steps 1, 3, 4, 6 (reuses Step 4's
  helper).
- Step 7 (stranger-judgment blend) — depends on Steps 1, 4 (reuses `find_clan_id_for_entity`).
- Step 8 (determinism test) — depends on Steps 1, 3, 4, 5.
- Step 9 (AC5 guard test) — depends on Steps 4, 5, 7.

Recommended implementation order: 1 → 6 → 3 → 2 → 4 → 5 → 7 → 8 → 9.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| ClanState gains `clan_reputation: float` with round-trip test coverage | Step 1 | `test_clan_state_clan_reputation_serialization_round_trip` |
| A contract-betrayal or party-defection event producing a `SocialUpdate` reputation delta also produces a measurable `ClanUpdate` change to `clans[clan_id].clan_reputation`, applied only through `apply.py`'s `clan_updates` path — **revised verification method**: the party-defection half is verified end-to-end through the live pipeline (`GroupPhase.resolve()` → `apply.py`); the contract-betrayal half is verified only at the pure-function level (`compute_betrayal_clan_reputation_update()` + `apply.py`), with an explicit, disclosed note that no live pipeline phase invokes `resolve_contract_outcome(betrayal=True, ...)` today (a pre-existing gap, not introduced by this ticket) | Steps 3, 4, 5, 6 | `test_party_defection_produces_clan_reputation_clan_update` (live-pipeline-verifiable); `test_contract_betrayal_produces_clan_reputation_clan_update` (pure-function + apply.py, unreachability disclosed in the test's own docstring) |
| A stranger with no personal trust/familiarity history reads a caution/trust prior incorporating the member's clan's `clan_reputation`, distinguishable from judging a member with direct history | Step 7 | `test_stranger_judgment_incorporates_clan_reputation` |
| (Guard, not a ticket AC by itself, but required by the P0 parity entry the ticket's own AC3 change touches) SOC-134's pinned no-bond formula (`public_trust*0.7 + history_trust*0.3`) must remain exactly reproduced at the neutral/no-clan case — Step 7's formula is algebraically required to reduce to it, not just informally similar | Step 7 | `tests/unit/social/test_parity_soc_134.py::TestSocialAppraisalWithNarrative::test_high_public_reputation_source_accepted` and `::test_zero_public_reputation_source_rejected`, both run **unmodified** |
| Any propagation/aggregation over `member_entity_ids` produces bit-identical `ClanUpdate` output across repeated runs | Steps 4, 5 (implementation), Step 8 (verification) | `test_clan_reputation_aggregation_is_deterministic` |
| Zero writes to any individual member's own `SocialComponent.public_reputation`, verified by a source-text guard test | Steps 4, 5, 7 (implementation stays clean), Step 9 (guard) | `test_no_writes_to_member_public_reputation_from_clan_reputation_code` |

**Note on the second AC's revision:** the ticket's own AC text says "A contract-betrayal or
party-defection event... also produces a measurable ClanUpdate change... verified by a new test"
without specifying the verification must be live-pipeline-reachable. Given the investigation's
confirmed finding that `resolve_contract_outcome(betrayal=True, ...)` has no live pipeline caller
today (a pre-existing condition, not something this ticket is scoped to fix), this plan satisfies
the AC's letter for both trigger types and its live-pipeline spirit for party-defection, while
disclosing the betrayal path's current unreachability rather than silently treating pure-function
coverage as equivalent to live-pipeline coverage. This is a Plan-phase interpretation, not a
unilateral scope decision — flagged here for visibility.

## Anti-Drift Notes

- **SOC-134 (P0 parity, `docs/parity_ledger/social_narrative.yaml:1438-1451`) is the single
  highest-risk regression surface in this plan.** Step 7's formula must be implemented exactly as
  written — `public_trust*0.7 + history_trust*0.3 + (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` —
  never as a re-weighted three-term blend that changes `public_trust`'s or `history_trust`'s own
  coefficients. Any implementer temptation to "simplify" this back into a single three-term sum
  (e.g. `public_trust*0.5 + clan_trust*0.2 + history_trust*0.3`) must be rejected: that shape was
  tried and rejected during this plan's own review specifically because it flips
  `test_zero_public_reputation_source_rejected`'s outcome from `CANCELLED` to `ACCEPTED` (`0.0*0.5
  + 0.5*0.2 + 0.5*0.3 = 0.25 ≥ 0.2` vs. the pinned `0.0*0.7 + 0.5*0.3 = 0.15 < 0.2`). If
  `tests/unit/social/test_parity_soc_134.py` fails after this change, do not edit that test — the
  formula implementation is wrong (per the project's Gate Integrity rule: a failing P0-pinned test
  is correct information to report and fix at the source, never a gate to route around).
- `test_clan_state_no_new_idea68_fields` (Step 2) is an intentional, in-scope update, not the
  idea-68 scope creep it guards against — do not extend it with anything beyond
  `clan_reputation`/`clan_reputation_delta`.
- `ClanLifecyclePhase` runs after `groups`, before `active_contracts`
  (`pipeline.py:402/404/407`). Both new `ClanUpdate` producers (Step 4 in `groups`, and Step 5's
  function if ever wired live in a future ticket) would read the same start-of-tick `state.clans`
  snapshot — same one-tick-lag pattern already established for `ClanLifecycleService
  .process_dissolution()`. Do not "fix" this into an intra-tick read-your-own-write pattern; it
  doesn't exist elsewhere in this pipeline and isn't this ticket's job to introduce.
- `_appraise_clan()`'s shared trust prelude (appraisal.py:47-54) is a different code path from the
  `appraise_contract()` blend this ticket modifies (Step 7) — do not conflate them.
- The additive-delta stranger-judgment formula (Step 7) applies **only** in the no-`SocialBond`
  branch, and only as an appended `+ (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT` term — the base
  `public_trust*0.7 + history_trust*0.3` term must stay textually intact and unmodified so the
  formula's neutral-case reduction to SOC-134's pinned parity value is visually obvious in a diff,
  not just algebraically true. Confirm via the explicit regression assertion in Step 7's test that
  the bond-present branch's `trust_score` formula is byte-for-byte unchanged.
- `resolve_contract_outcome`'s return signature must stay a 2-tuple
  (`Tuple[StrategicUpdate, List[SocialUpdate]]`) — every existing caller/test unpacks exactly two
  values; Step 5's new method is deliberately separate to avoid breaking this.
- `find_clan_id_for_entity` (Step 4) must be written once and reused by Steps 5 and 7 — do not
  duplicate the O(n_clans) scan logic in three places.
- **Step 5's pure-function-only scope for contract betrayal is a final, confirmed decision, not an
  open item.** Do not use Step 5's work as a pretext to also wire `process_active_contracts()` to
  start passing `betrayal=True` — that remains a separate, larger, out-of-scope change (see Step
  5's "DELIBERATE, CONFIRMED CHOICE" heading and its re-confirmation note).

## Unresolved Questions

None. All open questions raised in `investigation.md` (idea-60 dependency load-bearing-ness,
contract-betrayal live-trigger wiring, entity→clan reverse-lookup mechanism, stranger-judgment
blend formula, replay/fingerprint coverage) were resolved during this Plan phase with documented
reasoning above (see Summary, Step 5's "Live-pipeline reachability" note, Step 6, Step 7, and
Scope Guards), and this revision re-confirms both of them explicitly:

- **AC2's verification-method interpretation (pure-function-only coverage for the contract-betrayal
  half) stands as final.** This was re-examined during this revision (prompted by an
  architecture-review finding on a different part of the plan) and confirmed correct: wiring a
  live betrayal trigger into `process_active_contracts()` would require new betrayal-detection
  decision logic not named anywhere in this ticket's Scope, and is explicitly called out in Step 5
  and in Scope Guards as out of scope. This is not left open for the ticket owner to revisit —
  it is this plan's settled position, disclosed transparently rather than silently assumed.
- **Step 7's formula was corrected during this revision** to fix a real P0 parity regression (see
  Step 7) and is now algebraically verified against SOC-134's pinned formula and its two existing
  test cases. This is also settled, not open.

No item in this plan requires a human decision before Implement proceeds.
