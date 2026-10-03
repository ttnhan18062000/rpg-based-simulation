---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE
artifact_type: investigation
tags: [adventure, agency, cognition, observability, schema]
---

# Investigation — TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE

## Current Behavior

### The gap, re-verified against current HEAD

`AdventureDecisionPhase.apply()` was deleted by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`
(commit `1825f914`). Reading the pre-deletion source directly
(`git show 1825f914^:src/domains/adventure/phase.py`), its winning-route branch built a **complete
`EntityUpdate`** in one shot:

```python
strat_upd = StrategicIntelligenceSystem.evaluate_project_switch(hero, result.proposed_project, tick, state=state)
if strat_upd is None:
    continue
prop_upd = {"last_routing_tick": tick, "last_routing_family": result.selected.family.value}
entity_updates[hero.id] = EntityUpdate(entity_id=hero.id, strategic=strat_upd, property_updates=prop_upd)
```

Two facts from this pre-deletion read matter for the fix shape (not previously nailed down this
precisely by the originating ticket's Plan phase):

1. `property_updates["last_routing_family"]` was written as `result.selected.family.value` — the
   **`.value` string**, not the `RouteFamily` enum member itself. `RouteFamily` is a `str, Enum`
   mixin (`src/domains/adventure/schema.py:16`), so passing the raw enum instead of `.value` would
   still pass most `== "take_easy_quest"` string-equality checks and JSON-serialize correctly, but
   `str(enum_member)` differs from `enum_member.value` for `str`-mixin enums in this codebase's
   Python version (`str(RouteFamily.RECOVER)` → `"RouteFamily.RECOVER"`, not `"recover"`), and
   `GoalScore.metadata={"route_family": family, ...}` (`adventure_scorer.py:217`) stores the raw
   enum, not `.value`. **Implement must call `.value` explicitly when copying the metadata value
   into the new field/property, to exactly match the old contract** — this is a real, easy-to-miss
   footgun, not a hypothetical.
2. `strategic=strat_upd` and `property_updates=prop_upd` were **sibling fields on the same
   `EntityUpdate`**, built together inside one self-contained phase with full control over
   `EntityUpdate` construction. The current architecture has no equivalent single site: today,
   `evaluate_strategic_intent()` (called from `intelligence.py:922`) returns only a `StrategicUpdate`,
   and the outer refine loop (`intelligence.py:917-927`) merges it into `ent_upd.strategic` only. The
   route family is known *inside* `evaluate_strategic_intent()`'s `ADVENTURE_ROUTE` branch but the
   `EntityUpdate.property_updates` dict is only reachable at the *outer* call site — this is exactly
   the two-call-site threading problem the ticket's own Scope names.

### Current call graph, all line numbers re-verified this session

- `src/systems/strategic_systems/intelligence.py:917-927` — `evaluate_all_strategic_intents()`'s
  refine loop (confirmed exact function name via `grep`, not previously named in the ticket text).
  Merges `strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)` into
  `ent_upd.strategic` only:
  ```python
  ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
  strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
  if strat_up:
      existing_strat = ent_upd.strategic or StrategicUpdate()
      merged_strat = existing_strat.merge(strat_up)
      refined_entity_updates[e_id] = replace(ent_upd, strategic=merged_strat)
  ```
  Confirmed: never touches `ent_upd.property_updates`. Line numbers match the ticket's own citation
  exactly (917-927 today, unchanged since the originating ticket's snapshot).

- `src/systems/strategic_systems/intelligence.py:1478-1505` — the `ADVENTURE_ROUTE` win branch inside
  `evaluate_strategic_intent()` (ticket cited 1478-1495; current read shows the branch runs
  1478-1505, the extra 10 lines being the `(None, None)` defensive-return path, not new logic). Calls
  `RouteToProjectMapper.map_to_states(family=best_candidate.metadata.get("route_family"), ...)` at
  line 1488-1495. `family` here is a **`RouteFamily` enum member** (confirmed via
  `adventure_scorer.py:217`'s `metadata={"route_family": family, ...}`, where `family` is the
  function parameter typed `RouteFamily`, never `.value`-converted before insertion into metadata).

- `src/systems/strategic_systems/intelligence.py:1604-1618` — **the real materialization/return
  site**, one level below the branch dispatch, common to all three special `GoalKind`s (`ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/`REGION_STABILIZATION`):
  ```python
  switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick, state=state)
  if switch_up:
      extra_ci = {}
      if strat.committed_intentions and best_candidate.metadata.get("committed_intention_id") == strat.committed_intentions[0].intention_id:
          extra_ci["committed_intentions_add_or_update"] = [replace(strat.committed_intentions[0], status="active")]
      return replace(switch_up,
          boredom_delta=boredom_upd,
          leads_add_or_update=memory_upd.leads_add_or_update,
          leads_remove=memory_upd.leads_remove,
          **extra_ci
      )
  ```
  This is a **direct, live precedent** for exactly the shape this ticket needs: `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` already extended this identical `if switch_up: ... return replace(switch_up, ..., **extra_ci)` pattern to conditionally attach an extra `StrategicUpdate` field when `best_candidate` matches a specific condition. This ticket's fix is the same shape: when `best_candidate.kind == GoalKind.ADVENTURE_ROUTE`, additionally set the new
  `last_routing_family_set`/`last_routing_tick_set` fields (see Mechanics/Engine Constraints below for
  the exact proposed diff). `evaluate_project_switch()` itself (`intelligence.py:972-1066`, ticket's
  Out of Scope) is untouched by this change — only its caller's post-processing of the returned
  `switch_up` is touched, exactly as the CommittedIntention precedent did.
  **Important semantic note**: `switch_up` (hence the whole return) is only non-`None` when
  `evaluate_project_switch()` actually accepts the candidate (unlocked, or wins the
  retention-margin/urgency-floor comparison). A winning `best_candidate` that then loses inside
  `evaluate_project_switch()` (returns `None`) currently `continue`s the old phase's loop (equivalent
  today: falls through to the bandwidth-enforcement code at `:1620-1638`) — this matches the
  pre-deletion phase's own `if strat_upd is None: continue` behavior exactly, so gating the new field
  on `if switch_up:` reproduces the old "winning AND accepted" semantics precisely, not a broader or
  narrower one.

- `src/domains/adventure/mapper.py:31-47` (`RouteToProjectMapper._MAP`) — re-confirmed: 15
  `RouteFamily` entries map onto `ProjectKind`s with real collisions (`RECOVER`/`OWN_SURVIVAL` both →
  `ProjectKind.RECOVERY`; `TAKE_EASY_QUEST`/`QUEST_OPPORTUNITY` both → `ProjectKind.QUEST`;
  `BUY_UPGRADE`/`SELL_LOOT_FOR_GOLD` both → `ProjectKind.PREPARATION`). The committed
  `ProjectState.kind` cannot be reversed into the original `RouteFamily` at the outer merge site —
  confirmed still true, unchanged since the originating ticket's analysis.

- `src/observability/event_shapers.py:750-773` (live path, `StrategyShaper.shape()`,
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` defaults ON) and `src/observability/event_extractor.py:594-618`
  (rollback path) — both re-read this session, line numbers unchanged from the ticket's citation.
  Both read `prop = getattr(e_upd, "property_updates", None) or {}` then
  `prop.get("last_routing_family")` — i.e. they read **`EntityUpdate.property_updates` directly**,
  not `entity.strategic` or any `StrategicComponent` field. **This is the key design fact**: the
  destination the fix must reach is `EntityUpdate.property_updates`, not a new durable
  `StrategicComponent` field. No changes are needed to either observability file — the read side is
  already correct and was never broken; only the write side is missing.

### How `EntityUpdate.property_updates` becomes durable (traced this session, not previously documented in either ticket)

`property_updates` durably lands in **`entity.identity.properties`**, via `IdentityPatch.apply()`
(`src/engine/patches.py:213-215`: `props = dict(new_id.properties); if self.property_updates:
props.update(self.property_updates)`). This is the same mechanism every other existing
`property_updates` writer already uses (`last_defer_reason`, `last_assimilated_tick`,
`last_assimilated_subject`, escape-tag markers in `movement.py`, evolution markers in
`evolution.py`). `last_routing_family`/`last_routing_tick` were **never** `StrategicComponent`
fields, even before the deletion — they were always transient per-tick `identity.properties` writes.
This materially resolves the ticket's own "Assumptions / Open Questions" item about field shape (see
Mechanics/Engine Constraints below).

## Mechanics / Engine Constraints

### `docs/core/update_intents.md` — full read, authoritative for this shape decision

The doc's **Extension rules** section (lines 204-221) gives the canonical checklist for adding a new
intent field:
1. Define the field, `is_noop()`, `merge()` on the sub-intent dataclass.
2. Add the slot to `EntityUpdate`/`StateUpdate`.
3. Update `EntityUpdate.merge()`/`is_noop()`.
4. Update `StateUpdate.compact()` if relevant.
5. Update `DirtySet.from_update()`/`DirtySetBuilder.mark_from_update()`.
6. Document in this file's taxonomy tables.
7. Add tests.

For **this** ticket, step 2 does not apply in the "new top-level slot" sense — the new field lives
*inside* the existing `StrategicUpdate` sub-intent (`updates.py:474-517`), which is already a slot on
`EntityUpdate` (`strategic: Optional[StrategicUpdate]`). This is the same shape as the existing
`overload_source_set`/`overload_tick_set` pair (`updates.py:509-510`) and `current_project_id_set`/
`current_objective_id_set` — a pair of `Optional[str]`/`Optional[int]` "last-write-wins" scalar
fields, not a new collection. Per the Merge semantics table (update_intents.md lines 141-153), this
is the **"Set last-write-wins"** rule, matching `current_project_id_set`'s own documented example.

**Step 5 (DirtySet) does not need a code change.** `DirtySet.from_update()`/`mark_from_update()`
(`src/core/dirty.py:112-173, 237-329`) mark an entity "strategic"-dirty via a generic truthy check —
`if e_upd.strategic or e_upd.task or e_upd.interaction or e_upd.quest:` (`dirty.py:162, 329`) — not a
per-field check. Since the new fields live inside the existing `strategic` sub-intent, any tick that
sets them already makes `e_upd.strategic` truthy and non-noop, so the dirty-set entry is produced
automatically with zero new code. Verified by direct read this session (`grep -n "e_upd.strategic"
src/core/dirty.py`).

### `StrategicPatch.apply()` does NOT need a change — and this is corroborated by a real, independently-found pre-existing gap

Read `src/engine/patches.py:402-479` (`StrategicPatch.apply()`) in full this session. It durably
applies: all the dict-keyed collections (`blockers`, `leads`, `directives`, `projects`, `concerns`,
`candidate_zones`, `hypotheses`, `contracts`, `beliefs`), `turning_points`, `boredom`,
`source_trust`, `committed_intentions` (added by `TCK-20260812-COMMITTED-INTENTION-SEQUENCE`), and
`current_project_id_set`/`current_objective_id_set` (lines 476-477). **It does NOT apply
`overload_source_set`/`overload_tick_set` at all** — confirmed by grep across the whole file: no
occurrence of either name in `patches.py`. `StrategicComponent.primary_overload_source`/
`last_overload_tick` (`src/core/strategic.py:385-386`) are real durable fields, populated by
`V2EntityBuilder.strategic()` for test construction and read by
`src/systems/strategic_systems/cognition_export.py:132` and `src/api/presenters/state_presenter.py:71`
— but the only production writers (`detour.py:245-246`, `capacity_enforcement.py:184-185`,
`world_systems/events.py:156-157`) populate `StrategicUpdate.overload_source_set`/`overload_tick_set`,
which flows through `merge()` but is **silently dropped** at the sole authoritative apply site. This
looks like a real, pre-existing, independently-discovered bug — `entity.strategic.primary_overload_source`
appears to never be durably set via this path today. **This is flagged as a Risk below, not fixed
here** (explicitly out of this ticket's scope), but it is directly relevant precedent: it demonstrates
that adding an `_set` field to `StrategicUpdate` is only useful if the intended *destination* also
gets a corresponding write. For `last_routing_family`/`last_routing_tick`, the intended destination is
**not** `entity.strategic` — it is `EntityUpdate.property_updates` (confirmed above) — so
`StrategicPatch.apply()` is correctly out of scope for this fix, but only because of that distinction,
not by default. Do not conflate this ticket's field with a `StrategicComponent`-durable field; it must
not repeat the overload pattern's mistake of being written to `StrategicUpdate` and then never
reaching any real destination.

### `src/replay/fingerprint.py` and `src/core/builder.py` — confirmed NOT needed (unlike the `CommittedIntention` precedent)

Per `TCK-20260812-COMMITTED-INTENTION-SEQUENCE`'s stored plan.md (Decision 1), that ticket needed 5
additional files beyond its named Scope (`updates.py`, `patches.py`, `fingerprint.py`,
`capacity_enforcement.py`, `builder.py`) because it added a **new durable `StrategicComponent`
collection field** requiring order-preserving merge, replay-fingerprint inclusion, and capacity
enforcement. This ticket's fix is materially simpler and does **not** need the fingerprint or
capacity-enforcement files, confirmed by direct checks this session:
- `src/replay/fingerprint.py` has `_inventory_identity`, `_strategic_identity`, `_group_identity` —
  no `_identity_identity`/properties-dict fingerprint helper exists at all. `identity.properties`
  (the destination dict) is **not** part of the replay fingerprint today (confirmed by reading the
  full method list) — a pre-existing condition unrelated to and unaffected by this ticket. No
  fingerprint change needed or possible for a `property_updates`-only write.
- `src/core/builder.py`'s `V2EntityBuilder.identity(properties={...})` (line 184) and
  `.properties(values)` (line 690) already accept arbitrary property dicts for test construction — no
  new builder parameter is needed to construct an entity with a pre-set
  `last_routing_family`/`last_routing_tick` property for tests.
- `src/engine/pipeline_phases/capacity_enforcement.py` — not applicable; there is no
  collection/cap concept for a scalar last-write-wins field.

**Net effect: only `src/core/updates.py` (new field + `is_noop()` + `merge()`) and
`src/systems/strategic_systems/intelligence.py` (two call sites: the `ADVENTURE_ROUTE`-conditional
extra kwarg at the `switch_up` return site `:1604-1618`, and the outer refine-loop site `:917-927`
copying the resolved value into `ent_upd.property_updates`) need code changes.** This is a real,
positive finding beyond what either the ticket text or the originating ticket's Plan phase had
fully resolved — Plan should adopt this as the target file list rather than assuming the
`CommittedIntention` ticket's broader 7-file footprint applies here.

### `docs/guidelines/intentional_divergences.md` §2.41 — re-read in full, current line 998-1058

Confirmed unchanged since the originating ticket landed it (broadened disclosure paragraph at lines
1026-1056 already cites this ticket by ID as the tracked follow-up). The `last_defer_reason` half
(lines 1000-1025, "Rationale: Bounded") is unaffected by this ticket and stays as-is — the sub-floor
discard citation `intelligence.py:1450` is **still accurate**, re-verified this session
(`if g_score.utility < 20.0 or (g_score.target_id is None and g_score.target_pos is None): continue`
is exactly at line 1450 today, matching the ticket's own citation exactly, no drift since the prior
ticket's snapshot).

## Docs Requiring Update

- `docs/guidelines/intentional_divergences.md`: §2.41 (lines 998-1058) needs a further update once
  this fix lands — the "Broadened disclosure" paragraph currently states the `last_routing_family`
  restoration "is deliberately **not** ported as part of this recalibration-only ticket... tracked
  instead by `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`"; once restored, this needs a
  dated addendum stating the restoration landed, with the final field shape and file list, matching
  this ticket's own Scope item.
- `docs/parity_ledger/infrastructure.yaml`: INFRA-237's `support_boundary` (lines 2937-3004) already
  carries two addenda (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`,
  `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`) — this ticket's Scope item asks for a
  third addendum recording the fix and the fresh AGENCY re-measurement.
- `docs/simulation/domains/adventure_contract.md`: **not named in the ticket's own Related Docs — a
  real gap this investigation found.** Lines 55-63 ("What It Owns") and line 210 ("What It May
  Mutate") both currently state, in strikethrough/negated form, that `last_routing_tick`/
  `last_routing_family` are **not** written today and cite this exact ticket ID as the pending fix
  ("currently none of these are written... See... `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`").
  Once the fix lands this doc will be actively wrong (claiming a gap that no longer exists) unless
  corrected in the same session — both the "What It Owns" bullet and the "What It May Mutate" table
  row need updating to describe the restored, real write path (through the new `StrategicUpdate`
  field, not directly via `AdventureGoalScorer.score()`). Also note: this doc's "What It May Mutate"
  table row additionally claims `candidate_count`/`selected score` were historically part of
  `property_updates` — re-checking the pre-deletion source (`phase.py:171-178`) shows those two
  values were only ever passed to the **decision-trace writer** (`trace_records`, a separate
  local dict passed to `_writer.write_trace()`), never written into `property_updates`. This is a
  pre-existing doc overclaim, not introduced by this ticket, but the correcting edit should not carry
  the inaccuracy forward — only `last_routing_tick`/`last_routing_family` were ever `property_updates`
  keys.
- `docs/simulation_quality/eval_matrix_results.md`: the "AGENCY — Cross-World Design Note" section
  (currently lines 597-702, re-read in full this session) states, current-HEAD-accurately, that
  `simq_routing_test`/`hero_guild_routing` "now grade AGENCY=C at all 3 seeds... because the
  emission-side `last_routing_family` write no longer exists." Once restored and recalibrated back to
  A, this section (and the two dated 2026-08-13 NOTE blocks in the `simq_routing_test`/
  `hero_guild_routing` subsections) becomes stale and must be corrected in the same session — this
  doc is in the ticket's own Related Docs list but not its Scope list; Plan should decide whether to
  fold the correcting edit into this ticket (recommended, since AC3 already requires a fresh
  `calibrate_simq.py` run that will produce the exact new numbers this doc needs) or file it as a
  fast-follow.
- `tests/simulation_quality/fixtures/grade_anchors.json`: not a docs/ path, but flagged since it is
  the primary durable-truth artifact this ticket must recalibrate back up — see Parity Ledger
  Overlap below for the exact 6 run_keys.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml` INFRA-237 (`AgencyScorer` coverage) — `status: verified`,
  P1. Its `support_boundary` addenda directly track this exact restoration; needs the third addendum
  per Scope. Not P0, so no `test_path`-blocking gate is triggered by this entry, but the addendum
  content must be updated in the same session per the Authoritative Mechanics Rule.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-226 — re-checked; this entry is about a
  bravery-weighted `combat_engage`/`combat_retreat` utility differential (`GoalRegistry`'s
  `CombatEngageScorer`/`CombatRetreatScorer`), unrelated to `last_routing_family` despite being cited
  in `adventure_contract.md`'s "Decisions Made" section for a different reason (route→project
  mapping). No action needed on this entry.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-236 — cited by
  `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase`
  (`tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py:48-56`), pins that
  `STRAT-236`'s `v2_evidence` text does not reference the deleted phase. This ticket's changes do not
  touch `STRAT-236` or `_threat_resolved()`/the lock-expiry check it documents — confirmed no
  overlap.
- No `docs/parity_ledger/*.yaml` entry currently exists specifically for the `last_routing_family`
  write path itself (same conclusion the originating ticket reached) — INFRA-237 remains the correct
  entry to carry the addendum; a new entry is not warranted since AGENCY scoring logic itself is
  unaffected (`AgencyScorer`'s own unit tests bypass the emission wiring entirely, confirmed still
  true this session).

## Prior Work

- `stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/` — the immediate
  parent ticket. Its investigation.md Risk #1 and plan.md Decision 1 independently derived the same
  `StrategicUpdate`-schema-change conclusion this investigation re-confirms; its Deviations section
  additionally found and disclosed (not fixed) `hero_guild_routing_seed456_500t`'s ECONOMY/
  PROGRESSION drift and `simq_routing_test_seed456_500t`'s PROGRESSION drift, both explicitly out of
  this ticket's scope (tracked by `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`).
- `stored_artifacts/TCK-20260812-COMMITTED-INTENTION-SEQUENCE/` — the direct structural precedent for
  extending `StrategicUpdate` and threading a new field through `evaluate_strategic_intent()`'s
  win-transition site. Its Design Decision 5 code sample (`if switch_up: extra_ci = {}; ...; return
  replace(switch_up, ..., **extra_ci)`) is the exact pattern this ticket's fix should reuse for a
  `last_routing_family`-conditional kwarg. Its Decision 1 "5 additional files" finding does **not**
  fully apply here — see Mechanics/Engine Constraints above for the file-by-file re-derivation of why
  `patches.py`/`fingerprint.py`/`builder.py`/`capacity_enforcement.py` are not needed for this
  ticket's narrower, scalar-field, `property_updates`-destined fix.
- `tickets/done/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md` — the root-cause deletion ticket.
  Pre-deletion source (`git show 1825f914^:src/domains/adventure/phase.py`) is the ground truth this
  investigation re-read directly for the exact old contract (see Current Behavior above).
- `docs/simulation/domains/adventure_contract.md` — already anticipates this exact ticket by name
  (lines 55-63, 210) but is not in the ticket's own Related Docs — see Docs Requiring Update.

## Risks and Open Questions

1. **Field-shape decision, now resolved by this investigation, not left to Plan as originally
   framed.** The ticket's own Assumptions/Open Questions asks Plan to weigh "a dedicated
   `last_routing_family`/`last_routing_tick` pair vs. a general `property_updates`-equivalent field
   on `StrategicUpdate`." This investigation's direct trace shows the correct answer is the
   **dedicated pair, following the existing `overload_source_set`/`overload_tick_set` /
   `current_project_id_set` "set" convention** (`Optional[str]`, `Optional[int]`, last-write-wins
   merge) — not a general `Dict[str, Any]` field on `StrategicUpdate` (no such general field exists
   on `StrategicUpdate` today, and adding one would duplicate `EntityUpdate.property_updates`'s
   existing purpose one layer up, a real architectural redundancy). Plan should adopt this as decided,
   not re-litigate it, unless it finds a concrete reason this investigation missed.
2. **The `overload_source_set`/`overload_tick_set` dead-write gap (found this session) is a real,
   separate, pre-existing bug — explicitly NOT in this ticket's scope to fix**, but it is directly
   adjacent code Implement will be reading closely (the `if switch_up:` block at
   `intelligence.py:1620-1638` that constructs the bandwidth-enforcement `StrategicUpdate` using these
   same two fields). Flagging so Implement does not accidentally "fix" it as a drive-by (scope creep)
   or, conversely, mistake it as proof the new field's own mechanism is broken (it uses a materially
   different, already-durable destination — `property_updates` → `identity.properties`, not
   `entity.strategic` directly).
3. **`docs/simulation/domains/adventure_contract.md` is not in the ticket's own Related Docs list**
   despite directly, currently, and by-name anticipating this exact ticket. Plan should add it to the
   ticket's Related Docs and Scope before Implement starts, not discover it mid-implementation.
4. **`docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design Note correction is
   in Related Docs but not named in Scope.** Plan must explicitly decide whether the correcting edit
   (AGENCY back to A description) is folded into this ticket (recommended — AC3's own required fresh
   `calibrate_simq.py` run will produce the exact numbers needed) or deferred; do not leave it
   silently unaddressed either way.
5. **No existing test exercises `evaluate_all_strategic_intents()` (the outer refine-loop function
   containing the `intelligence.py:917-927` merge site) at all** — confirmed by a repo-wide grep
   returning zero hits. The new regression test required by AC2 must therefore either add fresh
   coverage for this function directly (constructing a `StateUpdate`/`AuthoritativeState` and
   asserting on `result.entity_updates[eid].property_updates`), or the ticket's AC2 must be satisfied
   at the `evaluate_strategic_intent()` level only (asserting the new `StrategicUpdate` fields are
   set) plus a second, narrower assertion that the outer merge site correctly copies them into
   `property_updates` — Plan should decide which, but the current zero-coverage state is a real gap,
   not an oversight of this investigation.
6. **`RouteFamily.value` vs. raw enum discipline (see Current Behavior) is a genuine implementation
   risk**, not a style nit — passing the raw `RouteFamily` enum instead of `.value` into the new
   field/property would silently diverge from the pre-deletion contract in log/repr contexts even
   though most equality/JSON paths would still "work," making it the kind of bug that passes tests
   built loosely (`== "take_easy_quest"` string comparisons) but fails a byte-for-byte
   `test_defer_property_name_constant_matches_phase_and_extractor`-style guard if Implement adds one
   for the family value too.

## Anti-Drift Hazards

- **Do not touch `evaluate_project_switch()`'s own body (`intelligence.py:972-1066`)** — ticket's
  Out of Scope explicitly forbids this; the fix belongs entirely in its caller's post-processing of
  the already-returned `switch_up`, exactly mirroring the `CommittedIntention` ticket's own
  `if switch_up: extra_ci = {}; ...` precedent, which also never touched
  `evaluate_project_switch()`'s body.
- **Do not port `last_defer_reason`.** Out of Scope explicitly excludes it; the sub-floor discard
  argument at `intelligence.py:1450` remains valid and unchanged.
- **Do not "fix" the independently-found `overload_source_set`/`overload_tick_set` dead-write gap**
  (Risk #2) as part of this ticket — it is a different destination (`entity.strategic` vs.
  `property_updates`) and a different, unscoped bug.
- **Do not widen the new `StrategicUpdate` field(s) into a general-purpose carrier** for other
  `GoalKind` branches' metadata (`SOCIAL_CONTRACT`'s `contract_id`, `REGION_STABILIZATION`'s
  `region_id`, etc.) — ticket's own Assumptions/Open Questions explicitly scopes this to
  `ADVENTURE_ROUTE` only "unless Investigate finds a directly analogous case." No analogous
  observability gap was found for the other two branches during this investigation (neither
  `event_shapers.py` nor `event_extractor.py` reads any `contract_id`/`region_id`-derived
  `property_updates` key) — do not speculatively generalize.
- **`tests/simulation_quality/test_agency_scorer.py` and
  `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` must stay green
  unmodified** — the former bypasses the emission wiring entirely (constructs synthetic envelopes
  directly), the latter's 4 guards (byte-identical helper signatures, no phase.py reference, STRAT-236
  v2_evidence, adventure_contract.md's "## Engine Phase" section only) do not overlap this ticket's
  planned edits to adventure_contract.md's "What It Owns"/"What It May Mutate" sections (a different,
  non-overlapping section of the same file — confirmed by reading the guard's own section-slicing
  logic, which starts at `"## Engine Phase"` and stops at the next `"\n## "`).
- **`grade_anchors.json` recalibration must only touch the `AGENCY` sub-object** of the 6 named
  run_keys (`simq_routing_test`/`hero_guild_routing` × seeds 42/123/456, `_500t`) — the seed123 pair's
  `COGNITION` sub-object was recalibrated down by the parent ticket for an **unrelated** cause
  (§2.40's interruption-bypass generalization, commit `3d992dd0`) and must **not** be touched by this
  ticket, even though the same two run_keys are being edited for `AGENCY`. Verified current state
  this session: all 6 run_keys currently read `AGENCY: {"grade": "C", "score": 0.0}` in
  `tests/simulation_quality/fixtures/grade_anchors.json` — this is the confirmed "before" state Plan's
  own fresh Implement-time re-verification (mirroring the parent ticket's Step 1 precedent) must
  re-check immediately before writing new values, not copy this investigation's snapshot verbatim.
- **`docs/parity_ledger/infrastructure.yaml` INFRA-237's `v2_evidence`/`test_path`/`status` must not
  change** — this remains an emission-side/observability fix, not an `AgencyScorer` logic change; only
  `support_boundary` gets a new addendum, matching the two prior addenda's own precedent of
  append-only, non-destructive editing.
