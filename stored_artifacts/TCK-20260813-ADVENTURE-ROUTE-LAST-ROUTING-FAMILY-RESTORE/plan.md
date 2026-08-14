---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE
artifact_type: plan
tags: [adventure, agency, cognition, observability, schema]
---

# Implementation Plan — TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE

## Summary

Restore `last_routing_family`/`last_routing_tick` emission for winning `ADVENTURE_ROUTE`
candidates by adding a dedicated `last_routing_family_set: Optional[str]` /
`last_routing_tick_set: Optional[int]` scalar pair to `StrategicUpdate`
(`src/core/updates.py`), following the existing `overload_source_set`/`overload_tick_set` /
`current_project_id_set` "set last-write-wins" convention exactly. Thread the value through two
call sites in `src/systems/strategic_systems/intelligence.py`: the `ADVENTURE_ROUTE`-conditional
extra kwarg at the shared `switch_up` return site (`:1604-1618`, mirroring
`TCK-20260812-COMMITTED-INTENTION-SEQUENCE`'s live `extra_ci` precedent at the same site), and the
outer refine-loop merge site (`:917-927`) which today only assigns `ent_upd.strategic` and must
also copy the resolved values into `ent_upd.property_updates["last_routing_family"]` /
`["last_routing_tick"]` — the exact keys `event_shapers.py:751`/`event_extractor.py:~595` already
read. No changes to `StrategicPatch.apply()`, `fingerprint.py`, `builder.py`, or
`capacity_enforcement.py` — confirmed unneeded because the destination is
`EntityUpdate.property_updates` → `entity.identity.properties` (via `IdentityPatch.apply()`,
`patches.py:213-215`, applied unconditionally, confirmed by direct read), not a new
`StrategicComponent` durable field. The route family must be copied with `.value` (a plain string
from the `RouteFamily(str, Enum)` mixin), never the raw enum, matching the deleted phase's exact
pre-deletion contract. Six new/extended unit tests close the zero-coverage gap on both
`evaluate_strategic_intent()`'s `StrategicUpdate` output and the previously-untested outer
`evaluate_all_strategic_intents()` refine loop. After the code change, a fresh
`tools/calibrate_simq.py` run against `simq_routing_test`/`hero_guild_routing` produces new AGENCY
numbers that recalibrate 6 `grade_anchors.json` run_keys back up (AGENCY sub-object only,
COGNITION on the seed123 pair untouched), and four docs are updated in the same session:
`intentional_divergences.md` §2.41, `infrastructure.yaml` INFRA-237, `adventure_contract.md`
(added to scope — not in the ticket's original Related Docs, a real gap Investigate found), and
`eval_matrix_results.md`'s AGENCY Cross-World Design Note plus its two dated NOTE blocks (folded
into this ticket, not deferred, since AC3's own required fresh `calibrate_simq.py` run already
produces the exact numbers this doc needs).

## Steps

### Step 1 — Add `last_routing_family_set`/`last_routing_tick_set` to `StrategicUpdate`

**Files:** `src/core/updates.py`

**Change:** In the `StrategicUpdate` dataclass (`updates.py:473-517`, confirmed by direct read this
session), add two new fields immediately after the existing `# Overload` pair
(`overload_source_set: Optional[str] = None` / `overload_tick_set: Optional[int] = None`, at
`updates.py:509-510`):

```python
    # Routing (adventure-route observability restore)
    last_routing_family_set: Optional[str] = None
    last_routing_tick_set: Optional[int] = None
```

Update `is_noop()` (`updates.py:518-532`) to also require both new fields be `None`, matching the
existing `self.overload_source_set is None and self.overload_tick_set is None` clause shape
(`updates.py:529-530`) — append `self.last_routing_family_set is None and
self.last_routing_tick_set is None` to the boolean chain.

Update `merge()` (`updates.py:534-572`) to add the "set last-write-wins" line for both fields,
matching `overload_source_set`'s own line exactly (`updates.py:566-567`):

```python
            last_routing_family_set=other.last_routing_family_set if other.last_routing_family_set is not None else self.last_routing_family_set,
            last_routing_tick_set=other.last_routing_tick_set if other.last_routing_tick_set is not None else self.last_routing_tick_set,
```

**Do NOT touch:** any other field in `StrategicUpdate`, `is_noop()`'s existing clauses, or
`merge()`'s existing per-field lines — this is a pure addition, not a restructuring. Do not add a
general-purpose `Dict[str, Any]` field on `StrategicUpdate` (investigation.md Risk #1 resolved this
question already — a dedicated scalar pair is correct, not a general carrier).

**Verify:** `test_strategic_update_last_routing_family_set_is_noop_default`,
`test_strategic_update_merge_last_routing_family_last_write_wins` (Step 6 below).

---

### Step 2 — Thread the route family through the `switch_up` return site

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:** At the shared materialization return site (`intelligence.py:1604-1618`, confirmed by
direct read this session — the exact code today is):

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

Add a second, disjoint extra-kwarg dict, gated on `best_candidate.kind == GoalKind.ADVENTURE_ROUTE`
(re-reading `best_candidate.metadata.get("route_family")` again here — confirmed at
`adventure_scorer.py:217`, `metadata={"route_family": family, ...}`, that `family` is stored as the
**raw `RouteFamily` enum member**, never `.value`-converted at the metadata-construction site, so
the `.value` conversion must happen here, at the consumption site):

```python
                extra_routing = {}
                if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
                    route_family = best_candidate.metadata.get("route_family")
                    if route_family is not None:
                        extra_routing["last_routing_family_set"] = route_family.value
                        extra_routing["last_routing_tick_set"] = current_tick
                return replace(switch_up,
                    boredom_delta=boredom_upd,
                    leads_add_or_update=memory_upd.leads_add_or_update,
                    leads_remove=memory_upd.leads_remove,
                    **extra_ci,
                    **extra_routing
                )
```

`route_family.value` is required, not `str(route_family)` or the bare enum — `RouteFamily(str,
Enum)` (`src/domains/adventure/schema.py:16`, confirmed) means `str(RouteFamily.RECOVER)` yields
`"RouteFamily.RECOVER"`, not `"recover"`, in this codebase's Python version; only `.value` matches
the deleted phase's exact pre-deletion contract (`result.selected.family.value`,
`git show 1825f914^:src/domains/adventure/phase.py`).

This block is gated on `if switch_up:` — i.e. only when `evaluate_project_switch()` actually
accepts the candidate — reproducing the pre-deletion phase's own `if strat_upd is None: continue`
semantics exactly (a winning `best_candidate` that then loses inside `evaluate_project_switch()`
must NOT set the new fields). It is also gated on `best_candidate.kind == GoalKind.ADVENTURE_ROUTE`
so `SOCIAL_CONTRACT`/`REGION_STABILIZATION` candidates sharing this same return site are unaffected
— no analogous observability gap exists for those two `GoalKind`s (investigation.md Anti-Drift
Hazards, confirmed no `contract_id`/`region_id`-derived key is read by `event_shapers.py` or
`event_extractor.py`).

**Other writer to this same `**kwargs` expansion:** `extra_ci` (from
`TCK-20260812-COMMITTED-INTENTION-SEQUENCE`) populates `committed_intentions_add_or_update` into
the identical `replace(switch_up, ..., **extra_ci)` call this step also extends. `extra_ci` and
`extra_routing` write disjoint `StrategicUpdate` field names
(`committed_intentions_add_or_update` vs. `last_routing_family_set`/`last_routing_tick_set`) so
Python's double-`**kwargs`-expansion into one `replace()` call cannot collide as long as both dicts
stay key-disjoint — do not rename either dict's keys to overlap. `test_committed_intention_
materialization.py`'s full pass (Regression Surface, unchanged) is the existing guard that would
catch a collision.

**Do NOT touch:** `evaluate_project_switch()`'s own body (`intelligence.py:972-1066`) — this step
only touches its caller's post-processing of the already-returned `switch_up`. Do not add the
`extra_routing` gate to the `SOCIAL_CONTRACT`/`REGION_STABILIZATION` branches above (`:1506-1577`).

**Verify:** `test_adventure_route_win_thread_family_into_strategic_update`,
`test_adventure_route_defer_family_does_not_set_routing_family`,
`test_adventure_route_win_that_loses_project_switch_does_not_set_routing_family` (Step 6 below).

---

### Step 3 — Copy the resolved value into `EntityUpdate.property_updates` at the outer refine loop

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:** At the outer refine-loop merge site (`intelligence.py:917-927`, confirmed by direct
read this session — the exact code today is):

```python
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
            if strat_up:
                existing_strat = ent_upd.strategic or StrategicUpdate()
                merged_strat = existing_strat.merge(strat_up)
                refined_entity_updates[e_id] = replace(ent_upd, strategic=merged_strat)
```

Extend the `if strat_up:` block to also compute and merge `property_updates`:

```python
            if strat_up:
                existing_strat = ent_upd.strategic or StrategicUpdate()
                merged_strat = existing_strat.merge(strat_up)
                prop_updates = dict(ent_upd.property_updates)
                if strat_up.last_routing_family_set is not None:
                    prop_updates["last_routing_family"] = strat_up.last_routing_family_set
                if strat_up.last_routing_tick_set is not None:
                    prop_updates["last_routing_tick"] = strat_up.last_routing_tick_set
                refined_entity_updates[e_id] = replace(ent_upd, strategic=merged_strat, property_updates=prop_updates)
```

**Other writers to `EntityUpdate.property_updates` (enumerated this session, repo-wide grep for
`property_updates=`):** `src/actions/harvest.py:38`, `src/actions/loot.py`,
`src/domains/combat_engagement/phase.py:91`, `src/domains/cooperation/phase.py`,
`src/domains/cooperation/services.py`, `src/domains/information/phase.py`,
`src/domains/progression/phase.py:79-84`, `src/domains/world_emergence/phase.py`,
`src/engine/evolution.py:146-147`, `src/engine/movement.py:290`,
`src/engine/pipeline_phases/movement.py`, `src/systems/economy_systems/town_service.py:82`. None
of these writers use the keys `"last_routing_family"` or `"last_routing_tick"` (grep-confirmed —
these two key strings are unique to this fix), so there is no key-collision risk regardless of
which pipeline phase runs before or after `evaluate_all_strategic_intents()` (Phase 4.1) within the
same tick. The interaction that DOES matter: this step's `prop_updates = dict(ent_upd.property_
updates)` (copy-then-set) must not be replaced with a wholesale `property_updates={"last_routing_
family": ...}` construction, because `ent_upd` here is fetched from `refined_entity_updates`,
which already carries any earlier phase's `property_updates` writes for this same entity within
this same tick (`update.entity_updates`, passed into this function as the accumulated state so
far) — a wholesale replace would silently drop those. This matches the safe copy-and-extend pattern
`src/engine/evolution.py:146-147` (`{**ent_upd.property_updates, ...}`) and
`src/domains/progression/phase.py:79` (`dict(merged_upd.property_updates)`) already use, and
deliberately does NOT follow `src/actions/harvest.py:38` / `src/systems/economy_systems/
town_service.py:82`'s wholesale-construct pattern, which is only safe at those two call sites
because they are each known to be the sole/first writer for that particular `EntityUpdate` at that
point in the pipeline — an assumption that does not hold for the strategic-intelligence phase,
which runs after other phases have already populated `update.entity_updates`. Final consolidation
of multiple phases' `EntityUpdate`s for the same entity across the whole tick additionally goes
through `EntityUpdate.merge()`'s own dict-spread (`updates.py:702`,
`{**self.property_updates, **other.property_updates}`), which is a second, independent safety net
against key loss — but this step's own copy-then-set must not rely on that safety net alone, since
`refined_entity_updates[e_id] = replace(...)` directly overwrites the dict entry, not merges into
it, within this same function.

**Verification that the new field's apply path is NOT silently dropped (per the flagged
`overload_source_set`/`overload_tick_set` cautionary precedent):** unlike `overload_source_set`/
`overload_tick_set`, which are consumed by `StrategicPatch.apply()` and are silently unapplied
there (confirmed this session: `grep -n "overload_source_set\|overload_tick_set"
src/engine/patches.py` returns zero hits inside `StrategicPatch.apply()`,
`patches.py:402-479`), `last_routing_family_set`/`last_routing_tick_set` are consumed entirely
within `intelligence.py` at Step 3 and converted into plain `EntityUpdate.property_updates` dict
keys — they never need to reach `StrategicPatch.apply()` at all. Run `grep -n
"last_routing_family_set\|last_routing_tick_set" src/engine/patches.py` after this step and confirm
it returns **zero hits** — this is expected and correct (these two `StrategicUpdate` fields are
consumed one layer up, inside `intelligence.py`, before ever reaching `patches.py`), not a sign the
apply path is missing. The actual apply-path proof is functional, not textual: `IdentityPatch.apply()`
(`patches.py:170-215`, confirmed by direct read this session) applies `property_updates`
unconditionally via `props.update(self.property_updates)` at line 213-215 — no per-key filtering
exists there, unlike `StrategicPatch.apply()`'s explicit per-field dispatch that happens to omit
`overload_source_set`/`overload_tick_set`. Also confirmed: `IdentityPatch` is constructed directly
from `EntityUpdate.property_updates` at `patches.py:679`
(`property_updates=dict(update.property_updates)`), so once Step 3's `prop_updates` dict lands on
the returned `EntityUpdate`, it reaches `entity.identity.properties` with no further translation
step that could drop it. New Test 6 (Step 6 below) is the functional proof that closes the loop
end-to-end.

**Do NOT touch:** `StrategicPatch.apply()` (`patches.py:402-479`) — this ticket's field never
reaches it, by design; do not add `last_routing_family_set`/`last_routing_tick_set` handling there
under any circumstance (that would misread the destination — see investigation.md's explicit
warning against conflating this field with a `StrategicComponent`-durable field). Do not "fix" the
independently-found `overload_source_set`/`overload_tick_set` dead-write gap while reading this
adjacent code — it is a different destination and a different, unscoped bug (Anti-Drift Notes
below).

**Verify:** `test_adventure_route_win_property_updates_carries_last_routing_family` (Step 6 below).

---

### Step 4 — Recalibrate `grade_anchors.json` AGENCY for the 6 named run_keys

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`

**Change:** After Steps 1-3 land and pass their unit/integration tests, run
`tools/calibrate_simq.py` fresh against `simq_routing_test` and `hero_guild_routing` at seeds
42/123/456 (`_500t`), re-verifying the **actual current values immediately before writing them**
(per investigation.md's own instruction not to copy this investigation's or any prior snapshot
verbatim). For each of the 6 run_keys —
`simq_routing_test_seed42_500t`, `simq_routing_test_seed123_500t`,
`simq_routing_test_seed456_500t`, `hero_guild_routing_seed42_500t`,
`hero_guild_routing_seed123_500t`, `hero_guild_routing_seed456_500t` — update **only** the
`AGENCY` sub-object (`{"grade": ..., "score": ...}`) to the freshly-measured post-fix value.
Confirmed current "before" state this session (all 6 read `"AGENCY": {"grade": "C", "score":
0.0}"` today, matching investigation.md's snapshot with zero drift).

**Other writer to this file:** `tests/simulation_quality/test_grade_regression.py` reads this file
as its comparison anchor but does not itself write it — `grade_anchors.json` is a hand/tool-edited
fixture, not runtime-generated. The only other recent writer is
`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` (the parent ticket), which wrote the
current `C/0.0` AGENCY values these 6 run_keys carry today and separately recalibrated the seed123
pair's `COGNITION` sub-object for an unrelated cause (§2.40's interruption-bypass generalization,
commit `3d992dd0`). This step's edit must touch each of the 6 run_keys' `AGENCY` sub-object only —
every other pillar sub-object (`COGNITION`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`,
`SOCIAL`, `INFORMATION`, `WORLD`, `NARRATIVE`) on all 6 run_keys must be left byte-identical to
their current values, confirmed this session via direct read (see the full 6-run_key JSON dump
captured during Investigate/Plan re-verification).

**Do NOT touch:** `COGNITION` on `simq_routing_test_seed123_500t` / `hero_guild_routing_
seed123_500t` (currently `{"grade": "C", "score": 0.0}` on both — parent ticket's unrelated fix,
different cause, different ticket). Do not extend `SCORE_TOLERANCE_OVERRIDES`
(`test_grade_regression.py:90-96`) for any of the 6 run_keys — a direct point-edit to the correct
freshly-measured value is the right shape, not a tolerance widening.

**Verify:**
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test_seed42_500t or simq_routing_test_seed123_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t or hero_guild_routing_seed123_500t or hero_guild_routing_seed456_500t"
```
plus AC3's own explicit requirement: a fresh `tools/calibrate_simq.py` run against
`simq_routing_test`/`hero_guild_routing` confirming `route_selected`/`action_executed`/
`route_family_first_use` actually fire.

---

### Step 5 — Update the four required docs

**Files:** `docs/guidelines/intentional_divergences.md`, `docs/parity_ledger/infrastructure.yaml`,
`docs/simulation/domains/adventure_contract.md`, `docs/simulation_quality/eval_matrix_results.md`

**Change:**

1. **`docs/guidelines/intentional_divergences.md` §2.41** (lines 998-1058, confirmed unchanged this
   session) — add a further dated addendum paragraph (after the existing "Broadened disclosure
   (TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT, 2026-08-13)" paragraph, lines
   1026-1056) stating: the `last_routing_family`/`last_routing_tick` half is now restored via a new
   `StrategicUpdate.last_routing_family_set`/`last_routing_tick_set` scalar pair
   (`src/core/updates.py`), threaded through `intelligence.py`'s `switch_up` return site and outer
   refine-loop merge site; cite this ticket ID and the final file list (`updates.py`,
   `intelligence.py` only). Explicitly restate that the `last_defer_reason` half remains
   `Bounded`/unaffected (do not edit that paragraph's own text).

2. **`docs/parity_ledger/infrastructure.yaml` INFRA-237** `support_boundary` (lines 2937-3004,
   confirmed unchanged this session) — append a third addendum (after the existing
   `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` and
   `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` addenda) recording: the emission-side
   gap is fixed, citing this ticket ID, and the freshly re-measured AGENCY grades for all 6 run_keys
   from Step 4's `calibrate_simq.py` run. Do NOT change this entry's `v2_evidence`, `test_path`, or
   `status` fields (investigation.md Anti-Drift Hazards — this remains emission-side, not an
   `AgencyScorer` logic change).

3. **`docs/simulation/domains/adventure_contract.md`** — add to this ticket's scope (confirmed by
   investigation.md Risk #3: this doc anticipates this exact ticket by name but was not in the
   ticket's own Related Docs). Two edits, both re-confirmed by direct read this session:
   - "What It Owns" (lines 51-65): rewrite the "Debug trace properties" bullet (lines 55-63,
     currently states `last_routing_tick`/`last_routing_family`/candidate count are **not**
     currently emitted, citing this ticket as the pending fix) to describe the restored real write
     path — through the new `StrategicUpdate.last_routing_family_set`/`last_routing_tick_set`
     fields, not directly via `AdventureGoalScorer.score()`.
   - "What It May Mutate" table (lines 203-212): rewrite the `EntityUpdate.property_updates` row
     (line 210, currently strikethrough-negated) to state `last_routing_tick`, `last_routing_family`
     are written on a winning, accepted `ADVENTURE_ROUTE` candidate. **Do not carry forward the
     pre-existing doc overclaim** that `candidate_count`/`selected score` were ever
     `property_updates` keys — investigation.md confirmed (re-reading pre-deletion
     `phase.py:171-178`) those two values were only ever passed to the decision-trace writer
     (`trace_records`), never to `property_updates`; the corrected row must name only
     `last_routing_tick`/`last_routing_family`.
   - Do not touch the "## Engine Phase" section — `test_delete_adventure_decision_phase_guards.py`'s
     guards scope only that section (confirmed by reading the guard's own section-slicing logic,
     starts at `"## Engine Phase"`, stops at next `"\n## "`), disjoint from these two edits.

4. **`docs/simulation_quality/eval_matrix_results.md`** — **decision: fold into this ticket, not
   defer.** Rationale: AC3 already requires a fresh `calibrate_simq.py` run (Step 4) that produces
   the exact new numbers this doc needs; deferring would require a follow-up ticket to restate
   numbers Step 4 already measured, adding process overhead with no informational benefit. Edit
   three locations, all confirmed present this session:
   - The "AGENCY — Cross-World Design Note" section (lines 597-702) — update the "Root cause
     (updated 2026-08-13...)" paragraph and its "AGENCY=C at all 3 seeds" claim to reflect restored
     AGENCY=A grades for `simq_routing_test`/`hero_guild_routing`, using Step 4's fresh numbers.
   - The dated `2026-08-13 (TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT)` NOTE block
     near line 461 (`simq_routing_test`'s subsection).
   - The matching dated NOTE block near line 1484-1488 (`hero_guild_routing`'s subsection).
   Do not edit the archetype-blocked table row for `dungeon_crawl`/`urban_political`/`sandbox_world`
   (line 266 and similar) — those worlds' AGENCY=C is `ENABLE_ADVENTURE_ROUTING=OFF`
   archetype-correctness, an unrelated, unaffected mechanism (confirmed by investigation.md and this
   session's own re-read).

**Other writer to these docs:** none of the four are concurrently edited by any other in-flight
ticket per the `Related Tickets`/registry check performed during Investigate; all four are
append-only or narrowly-scoped edits consistent with the two prior INFRA-237 addenda's own
non-destructive precedent.

**Do NOT touch:** `docs/parity_ledger/strategic_cognition.yaml` STRAT-226 or STRAT-236 (confirmed
unrelated by investigation.md's Parity Ledger Overlap section — no action needed on either entry).

**Verify:**
```
python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"
```
plus `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` (all 4 tests)
staying green, confirming the `adventure_contract.md` edits stayed inside the "What It
Owns"/"What It May Mutate" sections and did not touch "## Engine Phase".

---

### Step 6 — New tests

**Files:**
- `tests/unit/core/test_strategic_update_routing_family.py` (new)
- `tests/unit/strategic/test_adventure_route_materialization.py` (extend)
- `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py` (new)
- `tests/unit/observability/test_event_shapers_strategy.py` (extend)

**Change:** Add all 7 tests from test_plan.md's "New Tests Required" section, using the confirmed
fixture shapes from this session's direct reads:

1. `test_strategic_update_last_routing_family_set_is_noop_default` — default-constructed
   `StrategicUpdate()` has both new fields `None` and `is_noop() is True`.
2. `test_strategic_update_merge_last_routing_family_last_write_wins` — `merge()` last-write-wins
   semantics for both fields, including the no-op-update-leaves-unchanged case.
3. `test_adventure_route_win_thread_family_into_strategic_update` — extend
   `test_adventure_route_materialization.py` using its existing `_eligible`/
   `_fake_decide_factory` fixtures (confirmed present, lines 44-65 of that file) and
   `evaluate_strategic_intent(state, entity, force=True)` call shape (confirmed at line 82). Assert
   `result.last_routing_family_set == "take_easy_quest"` (bare string) AND
   `type(result.last_routing_family_set) is str` (not `isinstance`, since `RouteFamily` subclasses
   `str` and would pass `isinstance` even if `.value` were missed — this exact assertion is the
   guard against the `.value` discipline risk). Assert `result.last_routing_tick_set` equals the
   tick passed to `_state()`.
4. `test_adventure_route_defer_family_does_not_set_routing_family` — negative case using the
   existing `test_adventure_route_winner_preserves_none_none_handling_for_defer_family` fixture
   shape (lines 97-119, `RouteFamily.DEFER_WITH_REASON` metadata via `GoalRegistry.get_all_scores`
   monkeypatch); assert `last_routing_family_set is None` on the result.
5. `test_adventure_route_win_that_loses_project_switch_does_not_set_routing_family` — monkeypatch
   `StrategicIntelligenceSystem.evaluate_project_switch` to return `None` for a winning
   `ADVENTURE_ROUTE` `best_candidate`; assert `last_routing_family_set is None` on the result
   (proves the `if switch_up:` gate, not an unconditional set inside the `ADVENTURE_ROUTE` branch).
6. `test_adventure_route_win_property_updates_carries_last_routing_family` — new file, exercising
   `StrategicIntelligenceSystem.evaluate_all_strategic_intents()` (the outer refine loop,
   `intelligence.py:895-929`, confirmed zero existing coverage this session via repo-wide grep).
   **Decision on test target (per investigation.md Risk #5): build both — Test 3 (above) proves the
   `StrategicUpdate`-level field is set correctly by `evaluate_strategic_intent()`; this Test 6
   additionally proves the outer merge site correctly copies it into
   `EntityUpdate.property_updates`, which is AC2's literal requirement ("a committed `EntityUpdate`
   carrying `last_routing_family`").** Neither test alone fully covers Step 2 + Step 3 together —
   both are required. Construct a minimal `StateUpdate` (check `update_intents.md`'s documented
   shape and this file's own imports for the correct constructor signature before assuming reuse of
   `test_adventure_route_materialization.py`'s `_state`/`_entity` helpers, which build an
   `AuthoritativeState` directly, not a `StateUpdate` wrapper — the outer loop signature at
   `intelligence.py:895-929` takes `(state, update, cadence=...)` per its docstring, confirmed this
   session). Assert
   `result.entity_updates[hero.id].property_updates["last_routing_family"] == "take_easy_quest"`
   and `["last_routing_tick"] == <tick>`.
7. `test_agency_events_fire_end_to_end_for_winning_adventure_route` — extend
   `test_event_shapers_strategy.py`, feeding Test 6's `StateUpdate` output through
   `StrategyShaper.shape()` and asserting `route_selected`, `action_executed`, and
   `route_family_first_use` `SimulationEvent`s are emitted with `payload["family"] ==
   "take_easy_quest"`.

**Do NOT touch:** any existing test in `test_adventure_route_materialization.py`,
`test_score_normalization.py`, `test_committed_intention_materialization.py`,
`test_social_contract_materialization.py`, `test_region_stabilization_materialization.py`,
`test_event_shapers_strategy.py`, `test_event_extractor_agency2.py`,
`test_delete_adventure_decision_phase_guards.py`, or `test_agency_scorer.py` beyond the additive
extensions named above — all must stay green unmodified otherwise (test_plan.md Regression
Surface).

**Verify:** the full Scoped Pytest Commands block from test_plan.md, run individually per group
(never `pytest tests/` repo-wide, per CLAUDE.md Testing Rule).

## Scope Guards

- Do NOT fix the independently-found `overload_source_set`/`overload_tick_set` dead-write gap in
  `StrategicPatch.apply()` (`patches.py:402-479`) — flagged as a real, adjacent, pre-existing bug in
  investigation.md Risk #2, but explicitly out of this ticket's scope. Note it as a follow-up
  candidate in Anti-Drift Notes below, do not touch `patches.py` at all in this ticket.
- Do NOT change `last_defer_reason`'s `Bounded` status or its §2.41 rationale paragraph (lines
  1000-1025) — the sub-floor discard argument at `intelligence.py:1450` remains valid and unedited.
- Do NOT change `evaluate_project_switch()`'s own lock/margin/retention decision logic
  (`intelligence.py:972-1066`, STRAT-185/186/187) — only its caller's post-processing of the
  already-returned `switch_up` is touched (Steps 2-3).
- Do NOT change `RouteToProjectMapper._MAP`'s many-to-one `RouteFamily → ProjectKind` collision
  behavior (`src/domains/adventure/mapper.py:31-47`) — this ticket threads the family value through
  a separate channel (`StrategicUpdate` → `property_updates`) precisely because the mapper's
  collision makes reconstruction from `ProjectState.kind` impossible; the mapper itself is untouched.
- Do NOT widen `last_routing_family_set`/`last_routing_tick_set` into a general-purpose carrier for
  `SOCIAL_CONTRACT`'s `contract_id` or `REGION_STABILIZATION`'s `region_id` — no analogous
  observability gap was found for either (investigation.md, confirmed: neither `event_shapers.py`
  nor `event_extractor.py` reads any `contract_id`/`region_id`-derived `property_updates` key).
- Do NOT edit `docs/parity_ledger/strategic_cognition.yaml` STRAT-226 or STRAT-236 — confirmed
  unrelated by investigation.md's Parity Ledger Overlap section.
- Do NOT touch `COGNITION` on `simq_routing_test_seed123_500t` / `hero_guild_routing_
  seed123_500t` in `grade_anchors.json` — unrelated §2.40 cause, different ticket
  (`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` per the doc's own dated
  NOTE blocks).
- Do NOT touch `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` (ticket's own Out of Scope).
- Do NOT edit `docs/parity_ledger/infrastructure.yaml` INFRA-237's `v2_evidence`, `test_path`, or
  `status` — only `support_boundary` gets a third addendum.
- Do NOT touch `adventure_contract.md`'s "## Engine Phase" section — disjoint from the
  "What It Owns"/"What It May Mutate" edits this ticket makes there.

## Dependency Map

- Step 1 (schema field) has no dependency — first step, fully independent.
- Step 2 (switch_up site) depends on Step 1 (needs the new `StrategicUpdate` fields to exist to set
  them).
- Step 3 (outer merge site) depends on Step 2 (needs `strat_up.last_routing_family_set`/
  `last_routing_tick_set` to actually be populated by something before it can copy them).
- Step 6 (tests) depends on Steps 1-3 for Tests 3/4/5/6/7; Tests 1/2 depend only on Step 1.
- Step 4 (grade_anchors.json) depends on Steps 1-3 landing AND passing (Step 6's tests green) —
  `calibrate_simq.py` must run against working code, not before.
- Step 5 (docs) depends on Steps 1-4 all landing — the doc text describes the final field shape
  (Steps 1-3) and cites the freshly-measured numbers (Step 4's `calibrate_simq.py` output).
- Recommended implementation order: 1 → 2 → 3 → 6 (Tests 1-2 can run right after Step 1; Tests 3-7
  after Step 3) → 4 → 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `StrategicUpdate` carries the route family through a real schema field, with a defined lifecycle and `merge()` support | Step 1 | `test_strategic_update_last_routing_family_set_is_noop_default`, `test_strategic_update_merge_last_routing_family_last_write_wins` |
| A winning `ADVENTURE_ROUTE` candidate's materialization produces a committed `EntityUpdate` carrying `last_routing_family` | Steps 2, 3 | `test_adventure_route_win_thread_family_into_strategic_update`, `test_adventure_route_win_property_updates_carries_last_routing_family` |
| `route_selected`, `action_executed`, `route_family_first_use` events fire again for routing-capable worlds | Steps 2, 3 (code); Step 4 (fresh calibration run) | `test_agency_events_fire_end_to_end_for_winning_adventure_route`; fresh `tools/calibrate_simq.py` run against `simq_routing_test`/`hero_guild_routing` |
| `grade_anchors.json` AGENCY recalibrated for all affected run_keys | Step 4 | `pytest tests/simulation_quality/test_grade_regression.py -k "<6 run_keys>"` |
| `intentional_divergences.md` §2.41 and `infrastructure.yaml` INFRA-237 updated to record the restoration | Step 5 (items 1, 2) | `python3 -c "import yaml; yaml.safe_load(...)"` on infrastructure.yaml |
| No change to `last_defer_reason`'s `Bounded` status or `evaluate_project_switch()`'s decision logic | Scope Guards (enforced throughout Steps 2-3, 5) | `tests/unit/strategic/test_score_normalization.py`, `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py` (source-hash guard on `evaluate_project_switch()`), `test_event_extractor_agency2.py::TestAntiDriftGuards::test_defer_property_name_constant_matches_phase_and_extractor` |

## Anti-Drift Notes

- **`.value` discipline is the single highest-risk implementation detail.** `RouteFamily(str,
  Enum)` means most equality (`== "take_easy_quest"`) and JSON-serialization checks would silently
  pass even if the raw enum were stored instead of `.value` — only `type(x) is str` (not
  `isinstance`) and repr/log-context checks would catch it. Test 3's `type(...) is str` assertion is
  the load-bearing guard; do not weaken it to `isinstance` during implementation or review.
- **The `overload_source_set`/`overload_tick_set` dead-write gap in `StrategicPatch.apply()`
  (`patches.py:402-479`) is real, adjacent, and NOT fixed by this ticket.** Implement will read the
  `intelligence.py:1620-1638` bandwidth-enforcement block (which constructs a `StrategicUpdate`
  using these same two fields) while working on Step 2/3 — do not "fix" it as a drive-by, and do not
  mistake it as evidence this ticket's own field/mechanism is broken. The two fields use a
  materially different, already-durable destination (`property_updates` → `identity.properties` via
  `IdentityPatch.apply()`, confirmed unconditional) vs. `overload_source_set`/`overload_tick_set`'s
  destination (`entity.strategic` via `StrategicPatch.apply()`, confirmed silently unapplied). This
  gap is a legitimate candidate for a future, separately-scoped ticket — do not open one as part of
  closing this ticket unless the user asks; simply leave the existing flag in
  investigation.md/this plan as the record.
- **`grade_anchors.json`'s "before" state must be freshly re-verified at Step 4 implementation
  time, not copied from this plan's or investigation.md's snapshot** — matching the parent ticket's
  own Step-1 fresh-reverification precedent. The 6 run_keys' current `AGENCY: {"grade": "C",
  "score": 0.0}` values were re-confirmed this session (2026-08-13) via direct `grade_anchors.json`
  read, but Implement should re-check immediately before writing new values in case anything shifted
  between Plan and Implement.
- **Two disjoint `**kwargs` expansions now coexist in the same `replace(switch_up, ...)` call**
  (`extra_ci` from the CommittedIntention ticket, `extra_routing` from this ticket) — both must stay
  key-disjoint. `test_committed_intention_materialization.py`'s full pass is the regression guard;
  do not silence or skip it while validating this ticket's own changes.
- **Do not assume `test_adventure_route_materialization.py`'s `_state`/`_entity` helpers are
  directly reusable at the `evaluate_all_strategic_intents()` outer-loop level** — that function's
  signature takes `(state, update, cadence=...)`, i.e. a `StateUpdate` wrapper, not the bare
  `AuthoritativeState` those helpers build; check the actual constructor requirements before writing
  Test 6, per test_plan.md's own explicit warning on this point.

## Deviations (recorded during Implement, 2026-08-13)

1. **Step 3's target function was wrong — corrected to the actual live call site.** This plan's
   Step 3 (and the ticket body's own Request Summary / Related Code Areas) identified
   `StrategicIntelligenceSystem.evaluate_all_strategic_intents()` (`intelligence.py:884-929`) as
   "the outer refine-loop merge site... the only call site that merges a StrategicUpdate returned
   by evaluate_strategic_intent() into the tick's EntityUpdate." This is factually wrong: a
   repo-wide grep during Implement (`grep -rn "evaluate_all_strategic_intents" --include="*.py" .`)
   found this function referenced nowhere in `src/` — it is dead code, never wired into
   `src/engine/pipeline.py`. The actual live strategic-intelligence phase is
   `StrategicIntelligenceSystem.fused_strategic_pass()` (`intelligence.py:291-642`), wired via
   `src/engine/pipeline.py:333`
   (`run_phase("strategic_intelligence", update, lambda u:
   StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))`), which has its
   own, separate `strat_up` → `EntityUpdate` merge site at `intelligence.py:~627-635`
   (`final_upd = replace(ent_upd, identity=final_identity_upd, strategic=strat_up)`).
   Implement applied Step 3's copy-then-set `property_updates` fix at BOTH sites: the originally
   planned (but dead) `evaluate_all_strategic_intents()` site, and the corrected, actually-live
   `fused_strategic_pass()` site. A new dedicated test,
   `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`, exercises the real live path
   directly. This is the single most important correction from this plan — every claim in Steps
   1-2 and the Acceptance Criteria Map about "the outer refine-loop merge site" should be read as
   referring to `fused_strategic_pass()`'s merge site, not `evaluate_all_strategic_intents()`'s.

2. **AC3/AC4/AC5 are not satisfied — a second, unrelated, out-of-scope mechanism blocks event
   emission for the 6 named calibration run_keys, discovered during Implement's required AC3
   verification step.** With the write-path fix verified correct at the unit/integration level
   (Steps 1-3's tests all pass, including the corrected `fused_strategic_pass()` test above), a
   fresh `tools/calibrate_simq.py` run against all 6 run_keys
   (`simq_routing_test`/`hero_guild_routing` × seeds 42/123/456, `_500t`) still measures
   `AGENCY: {"grade": "C", "score": 0.0}`, `events=0` — byte-identical to the pre-fix state.
   DEBUG-level tracing of `evaluate_strategic_intent()`'s own tier-5 goal-selection log across full
   500-tick real-pipeline runs of both worlds, at every sampled seed, shows `ADVENTURE_ROUTE`'s
   utility (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, normalized onto the shared 0-100
   competition scale — observed ~20-26 in practice) never once outscoring `COMBAT_ENGAGE`
   (observed ~100-144) or `REGION_STABILIZATION` (observed flat 100.0), and one or the other is
   active on effectively every evaluated tick for every hero entity in both worlds (a goblin
   raiding party for `simq_routing_test`; additional region-stabilization pressure for
   `hero_guild_routing`). This is a separate, unrelated mechanism from the write-path bug this
   ticket fixes — the tier-5 goal-competition scale (`_score_scale_max()`,
   `intelligence.py:108-126`) interacting with `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s
   architecture change from an unconditional standalone phase (which never competed against other
   `GoalKind`s at all) to a competing `GoalScorer`. Altering that competition/scale logic is
   explicitly out of this ticket's scope (Scope Guards forbid touching
   `evaluate_project_switch()`'s decision logic, and the utility-scale constants are a level below
   even that) and would be exactly the "force an unrealistic entity route to fix a low pillar
   score" anti-pattern this project's guidance warns against. Consequently:
   - Step 4 (`grade_anchors.json` recalibration) was **not performed** — the 6 run_keys' current
     `AGENCY: {"grade": "C", "score": 0.0}` values are already the correct, freshly-measured
     numbers; there is nothing to recalibrate.
   - Step 5's `eval_matrix_results.md` edits were **not performed as originally planned** (i.e. not
     rewritten to claim a restored `A` grade). Instead, factual NOTE addenda were added recording
     that the write-path fix landed but did not change the measured grade, with the evidence trail
     and a recommendation for a follow-up ticket.
   - `docs/guidelines/intentional_divergences.md` §2.41 and `docs/parity_ledger/infrastructure.yaml`
     INFRA-237 were updated to accurately record both the genuine fix (write-path restored,
     verified) and this open finding (event emission still blocked, different cause, follow-up
     ticket recommended) — not to claim a restoration that measurement does not support.
   - `docs/simulation/domains/adventure_contract.md` was updated as planned (Step 5, item 3) since
     that edit only documents the write mechanism itself, not any claim about it firing in a
     specific world — unaffected by this finding.
   AC1 (`StrategicUpdate` schema field), AC2 (materialization produces a committed `EntityUpdate`
   carrying `last_routing_family`, verified by tests including the corrected live-path test), and
   AC6 (no change to `last_defer_reason`'s `Bounded` status or `evaluate_project_switch()`'s
   decision logic — confirmed by the unchanged, still-passing
   `test_evaluate_project_switch_source_hash_unchanged` guard) are satisfied. AC3, AC4, and AC5 are
   left unchecked in the ticket, with this section as the record of why.
