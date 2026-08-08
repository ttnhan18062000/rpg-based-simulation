---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC
artifact_type: investigation
tags: [observability, engine, combat, simulation-quality, performance]
---

# investigation.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC

## Summary

This epic does not re-investigate whether the migration is sound — that question was already
answered with real evidence by `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE` (DONE).
This epic's own investigation is narrower: **how to decompose and sequence the implementation so a
hot-path engine change can be checked carefully at every step**, per the user's explicit
instruction.

## Why this needs multiple, gated child tickets rather than one implementation ticket

`ApplyPath.apply_generation()` (the new emission point) runs once per entity-update per tick, for
every tick of every simulation run in this repo — it is among the hottest code paths that exists.
The original flat plan (`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-
FACTION`) bundled: registry design, 3 domain shapers, shadow-mode wiring, corpus-wide comparison,
performance re-validation, and the actual cutover — all in one ticket's Implement step. That shape
has two real risks:

1. **A design flaw discovered while building the 3rd shaper would already have COMBAT and ECONOMY
   built on the same flawed assumption**, with no natural checkpoint to catch it before all 3 are
   done.
2. **No dedicated, hard gate exists between "the code is written" and "the code is live."** A
   single Implement step that writes the shapers, wires them, validates them, and cuts over all in
   one pass makes it too easy for the mandatory-verification step to become a formality rather than
   a real, structurally-required decision point.

## Decomposition rationale

- **Fix-first (child 1)**: the current diff-based extractor has a confirmed bug
  (`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`). Comparing new shader output
  against a known-buggy baseline in the shadow-validation step would produce meaningless
  "divergence" (the new path being right and the old path being wrong would look identical to a
  real bug in the new path). Fix the baseline first.
- **Pilot-one-domain-first (child 2)**: COMBAT is the domain with the deepest investigation history
  this session (the confirmed bug, the outcome_kind tagging already in place, the most scrutiny).
  Proving the registry pattern here first, in isolation, means any structural problem with the
  registry design itself is caught while only one domain's shaper exists to fix — not three.
- **Extend once proven (child 3)**: ECONOMY and FACTION reuse child 2's now-validated registry
  mechanism; combining them is reasonable since neither introduces new architectural risk once the
  pattern is proven — they're two more instances of the same shape, not two more design decisions.
- **Hard validation gate (child 4)**: shadow-mode comparison across the real calibration corpus,
  plus a re-run of the existing performance harness, as its own ticket — not a sub-step folded into
  cutover. This is the ticket the user's "check it carefully" instruction is most directly aimed
  at: it exists specifically so there is a real DONE/NOT-DONE checkpoint between "built" and "live,"
  with its own Verify gate independent of the cutover ticket's.
- **Cutover last, alone (child 5)**: the one genuinely irreversible step (removing the old code
  path) gets its own ticket, its own Review/Architecture-Verify pass, and cannot start until child
  4 is DONE — enforced by `SEQUENCE.md`'s explicit ordering note, not just convention.

## Risk register (carried into each child ticket's own Investigate phase, not resolved here)

- Whether SHADOW-mode dual construction (old diffing + new shaper, both running, only one
  delivering) adds measurable overhead during the transition window itself — child 4's perf
  re-validation must check this explicitly, not just the final cutover state.
- Whether any of the 3 domains' typed update records have edge cases not covered by this session's
  investigation-level reads (e.g. `CombatUpdate.merge()`'s aggregation logic, not fully traced) —
  each shaper-building child ticket's own Investigate phase must verify against the real code, not
  just this epic's summary.

## Full event-coverage audit (2026-08-06, done before any child ticket implementation began)

Per explicit user instruction: the push migration must not silently miss any event
`event_extractor.py` currently defines for COMBAT/ECONOMY/FACTION. Every `event_type` string and
typed event class constructed anywhere in `event_extractor.py` was enumerated (77 string-literal
sites + 6 typed event classes: `LifecycleEvent`, `MovementEvent`, `CombatDamageEvent`,
`CombatKillEvent`, `GoldTransactionEvent`, `QuestEvent`), then each COMBAT/ECONOMY/FACTION-relevant
one was traced to its exact detection mechanism to determine push-readiness. **This materially
corrects the parent ticket's (`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`) coverage
audit**, which checked only 1 event per domain and concluded "COMBAT/ECONOMY/FACTION already
push-ready" — true for most events in each domain, but not all.

**Scope boundary confirmed**: only events `event_extractor.py`'s `extract()` itself constructs are
in scope. `alliance_formed`/`leadership_changed` (referenced in `quality_hub.py`'s translation
table) are constructed elsewhere entirely — `alliance_formed` via
`CampaignOrchestrator._emit_chronicle_events()` (`src/domains/campaigns/orchestrator.py`, already
calls `EventRecorder.record()` directly — already push-based, unrelated to this migration) and
`leadership_changed` via `src/systems/social_systems/party_lifecycle.py` (a different
return-value/collection pattern). Neither needs migration or deferral — they were never part of
`event_extractor.py`'s diffing to begin with.

### COMBAT

| Event | Mechanism | Verdict |
|---|---|---|
| `combat_initiated` | `entity_updates[eid].combat.attacker_id` (typed record) | **MIGRATE** |
| `combat_damage` | same | **MIGRATE** |
| `combat_kill`→`entity_killed` | same, keyed on `lifecycle.active` transition | **MIGRATE** |
| `near_death_survival` | same | **MIGRATE** |
| `hazard_drain_applied` | same typed record, different branch (`outcome_kind=="HAZARD"`) — WORLD-scored, not COMBAT, but physically colocated and mechanically identical | **DECISION POINT** — migrate alongside COMBAT (simplifies cutover, same pattern) or defer to a WORLD-scope Phase 2; child 2 must decide explicitly, not silently either way |
| `hero_death_unrecorded` | colocated with kill detection, NARRATIVE-scored | same decision point as `hazard_drain_applied` |
| `demographic_mortality` (despawn branch) | reuses the `_real_combat_update` helper (from the just-landed hotfix) but is a structurally distinct branch (entity removed from `entities` dict, not merely `lifecycle.active=False`) covering non-combat death causes too | **DECISION POINT**, lean toward defer (broader than combat) — decide explicitly |
| `combat_resolved` | **never constructed anywhere in the codebase** — referenced only in `combat.py`'s scorer `EVENT_TYPES`/`score()` and the quality contract doc | **DEAD — disclose, no migration action** (nothing exists to migrate) |
| `attrition_threshold_crossed` | same — dead, scorer-only | **DEAD — disclose, no migration action** |
| `combat_hard_law_violation` | `kernel.py`'s hard-law-violation translation path (`_LAW_ID_TO_EVENT_TYPE`), not `event_extractor.py` | **OUT OF SCOPE** — separate mechanism entirely |

### ECONOMY

| Event | Mechanism | Verdict |
|---|---|---|
| `resource_harvested` | `entity_updates[eid].intent_results[].source_kind=="NODE"` (typed record) | **MIGRATE** |
| `item_crafted` | same, `source_kind=="CRAFTING"` | **MIGRATE** |
| `shop_transaction` / `trade_executed` | same, `source_kind in ("SHOP_BUY","SHOP_SELL")` | **MIGRATE** |
| `quest_reward_dispensed` | same, `source_kind=="QUEST"` | **MIGRATE** |
| `gold_sink_fired` | same, `source_kind in _GOLD_SINK_KINDS` | **MIGRATE** |
| `paid_information_transaction` / `paid_info_transaction` / `paid_info_changed_goal` (category=strategy, colocated) | same, `source_kind=="INFORMATION_PURCHASE"` | **MIGRATE** (colocation of `paid_info_changed_goal` is a minor decision point — same intent_results read, trivial to include) |
| `gold_transaction`→`gold_transferred` | **pure `entity.inventory.gold` state diff** (`prior_ent.inventory.gold` vs `entity.inventory.gold`) — no typed update record backs this at all | **DEFER** — no `ResourceTransferIntent`-equivalent exists for direct gold-field mutation; would need new instrumentation |
| `resource_node_depleted` | **pure `state.resource_nodes` dict diff** (`prior_state.resource_nodes[id].remaining_charges` vs current) — not per-entity, not update-record-driven at all | **DEFER** — no typed per-node update record exists |
| `resource_node_regenerated` | same mechanism as above (intentionally unscored per the code's own comment, but still an existing defined event) | **DEFER**, same reason |
| `node_recharged` | same mechanism, WORLD-scored (out of this epic's 3-domain scope regardless) — scorer handler is itself a no-op today | **DEFER**, same reason |
| `conservation_law_verified` | **derived from other events already appended to the same tick's `events` list**, gated `tick % 50 == 0` — a meta/aggregate check, not a single update-record read | **DEFER** — needs an end-of-tick aggregation design, structurally different from a per-update shaper |
| `conservation_law_violated` | hard-law translation path (`LAW-GOLD-NONNEGATIVE`) | **OUT OF SCOPE** |

### FACTION

| Event | Mechanism | Verdict |
|---|---|---|
| `diplomatic_transition` | `update.faction_updates[].diplomatic_relations_set` (typed record) | **MIGRATE** |
| `alliance_proposed` | same, plus a read of `prior_state.factions[fid].diplomatic_relations` to detect the pre-transition state — confirmed `ApplyPath.apply_generation(state, update, ...)` already receives the pre-mutation `state` as its own parameter, so this read is available at the apply layer without new plumbing | **MIGRATE** |
| `alliance_accepted` | `update.faction_updates[].diplomatic_relations_set`, `new_state=="ALLIED"` | **MIGRATE** |
| `territory_ownership_changed` | `update.faction_updates[].territory_add` | **MIGRATE** |
| `resource_seized` | same, plus `upd.tension_delta > 0` | **MIGRATE** |
| `faction_tension_delta` | `update.faction_updates[].tension_delta` | **MIGRATE** |
| `war_declared` | `update.world_events_add[]`, `WorldEventCategory.FACTION_WAR_DECLARED` (typed record) | **MIGRATE** |
| `military_conflict_resolved` | same, `TERRITORY_TRANSFERRED`/`WAR_ENDED_EXHAUSTION` | **MIGRATE** |
| `faction_extinct` | **full entity-census scan**: iterates every entity in `current_state.entities` AND `prior_state.entities` to determine which factions have zero living members now vs. had ≥1 before — not a single update-record read at all, a population-wide computation | **DEFER** — would need incrementally-tracked per-faction living-member counts (new state-tracking machinery) to become push-based; keeping this on the diffing path is not just easier, it's a real architectural gap the diffing model happens to paper over cheaply |

### Summary counts

- COMBAT: 4 clean migrate, 3 colocation decision points (lean migrate for 2, lean defer for 1), 2
  dead (disclose only), 1 out of scope.
- ECONOMY: 7 clean migrate (1 with a trivial colocation note), 5 defer (2 distinct mechanisms: pure
  state-diff with no typed record, and meta/aggregate-derived), 1 out of scope.
- FACTION: 8 clean migrate, 1 defer (population-census mechanism).

**No event is silently dropped.** Every deferred event is named above with its specific reason and
carried forward into the relevant child ticket's own scope as an explicit "Deferred (not
implemented, not skipped)" list — see child 2/3 ticket updates.

## Design refinement: dispatch point does not require touching `apply.py`/`apply_plan.py` at all

Traced `ApplyPath.apply_generation()`'s internals (`src/engine/apply.py:179+`,
`ApplyPlanBuilder.build_plan()` in `src/engine/apply_plan.py`) to find the literal per-entity
dispatch point originally assumed necessary. Found something better: **every "MIGRATE"-verdict
event above can be derived from `prior_state` + `update` alone — the exact two objects already
passed into `ApplyPath.apply_generation(prior_state, update, ...)` as its own input parameters,
before any state reconstruction happens.** `CombatUpdate` already carries `hp_delta`,
`alive_set: Optional[bool]`, `attacker_id`, `outcome_kind` — sufficient to derive
`combat_initiated`/`combat_damage`/`near_death_survival`/`entity_killed` from `prior_ent.combat.hp`
(known before apply) + the update's own delta fields, with no need to read the post-mutation
entity at all. Same for FACTION (`update.faction_updates`/`update.world_events_add`, plus
`prior_state.factions` for `alliance_proposed`) and the ECONOMY events driven by
`intent_results`/`source_kind`.

**This means the shaper registry does not need to hook into `ApplyPath.apply_generation()` or
`ApplyPlanBuilder`'s reconstruction internals at all** — the hottest, most performance-sensitive
files in the engine stay completely untouched by this migration. Confirmed via `kernel.py:720-731`:
`apply_generation()` is called, then `_phase_observability(prior_state, update)` runs immediately
after — `_phase_observability` internally calls `EventExtractor.extract(prior_state, self._state,
update, obs_mode)`, reading `self._state` (the already-materialized post-apply state) only because
`EventExtractor` is diff-based by design. **The shaper registry can be called from the exact same
site, at the exact same point in the tick, using only `prior_state` and `update` — ignoring
`self._state`/`current_state` entirely for every migrated event.** This is a strictly lower-risk
design than originally scoped: no change to `apply.py`, `apply_plan.py`, or the tick's call
ordering — only a new function invoked alongside the existing `EventExtractor.extract()` call in
`kernel.py`'s `_phase_observability()`, reading different (typed-record) inputs to produce the
same event types. Revises child 2/3's `Related Code Areas` accordingly — `src/engine/apply.py` is
no longer a modification target, only a reference for confirming this design's soundness.
