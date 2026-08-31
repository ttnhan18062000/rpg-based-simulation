---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
artifact_type: investigation
tags: [adventure, cognition]
---

# Investigation — TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Context Search Note

Per Step 0c: `mcp__knowledge-search__search_docs` returned `{"error":"index not found"}` (the
knowledge-search MCP index is not built in this worktree). Fallback `python3
tools/knowledge_search.py query ... --top-k 5` also reported `knowledge index not found — run make
knowledge-index`. Both semantic-search tools were unavailable; this is disclosed rather than
silently skipped, per the hard rule. `graphify query "MemoryUpdatePhase pipeline causal memory
route scoring"` succeeded (BFS depth=2, 92 nodes) and correctly surfaced `MemoryUpdatePhase`
(`src/domains/memory/phase.py:24`), `CausalAttributionService` (`src/domains/memory/attribution.py:15`),
`SpatialMemoryUpdateService` (`src/domains/memory/spatial_update.py:23`), `CausalMemoryEntry`/
`CausalMemory`/`CognitionModel` (`src/core/cognition.py`), and the full `test_memory_informed_scoring.py`
test list — all of which were read directly as primary targets, matching the ticket's own Related
Code Areas.

## Current Behavior

**`MemoryUpdatePhase.run()`** (`src/domains/memory/phase.py:24-100`) — takes a raw
`Sequence[EntityState]`, `tick`, and a single `Optional[dict] trigger_event` (not a list). For each
active/alive entity it: (1) recalculates temporal urgencies via `TemporalPressureService`, (2) if
`trigger_event["entity_id"] == entity.id`, calls `CausalAttributionService.attribute()` to append a
bounded `CausalMemoryEntry` and, if `evt_kind in ("combat_loss", "near_death")`, marks the current
region dangerous via `SpatialMemoryUpdateService.mark_region_danger()`, (3) always updates
region-visit familiarity for the entity's current region. It returns a raw `List[EntityState]` — it
does **not** produce a `StateUpdate`/`EntityUpdate` and is never called from anywhere except its own
tests (confirmed: zero call sites in `src/` outside `src/domains/memory/phase.py` and
`tests/`). This matches the prior ticket's (`TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`) explicit
Scope Guard: "Do not wire `MemoryUpdatePhase`... file a follow-up ticket" — this ticket is that
follow-up, named directly in that plan (`plan.md:462-467`).

**`CausalAttributionService.attribute()`** (`src/domains/memory/attribution.py:18-77`) branches on
exactly 4 literal `event_kind` strings: `"combat_loss"`, `"failed_search"`, `"failed_craft"`,
`"party_abandoned"`. For `"combat_loss"` specifically (lines 29-55): checks `hp_pct = entity.combat.hp
/ entity.combat.max_hp < 0.3` → appends `"low_health"`/`"heal_first"`; `stamina < 20` →
`"low_stamina"`/`"rest_often"`; `weapon_dur < 0.2` → `"damaged_weapon"`/`"repair_weapon"`; **only if
none of those three fired** does it fall back to `"strong_enemy"`/`"avoid_enemy"` (line 50-52). This
fallback-only branch is the **only** source of the `"avoid_enemy"` advice string that
`AdventureRouteScorer.score()` actually reads.

**`AdventureRouteScorer.score()`** (`src/domains/adventure/scoring.py:236-253`, step "4c") reads
`entity.cognition.memory.causal.entries` and applies `memory_adjustment = -1.0` if any entry's
`future_advice` contains `"avoid_enemy"` (suppresses `HUNT_WEAK_ENEMY`), and `+1.0` if any contains
`"boost_party_trust"` (promotes `FORM_PARTY`). These are 2 of the 10 real `future_advice` values the
4 event kinds can produce. This scoring-side code is real, unit-tested (7 tests in
`tests/unit/domains/adventure/test_memory_informed_scoring.py`), and unaffected by this ticket
unless the mapping-extension question (see Risks) is resolved to extend it.

**Pipeline** (`src/engine/pipeline.py::AuthoritativeApplyPipeline.refine()`) — line 136:
`actor_validity` (PP-02) runs, then line 143: `self_model` (PP-03, gated by
`ENABLE_SELF_MODEL_COGNITION`). The ticket's proposed insertion point is the gap between these two
lines (136→143). Every phase in this stretch follows the same shape:
`update = run_phase("<name>", update, lambda u: <Phase>.apply(state, u), "<ENABLE_FLAG>")`, where
`<Phase>.apply(state, update) -> StateUpdate`. **`MemoryUpdatePhase` has no `.apply()` method and no
`StateUpdate`-shaped signature at all** — it is architecturally incompatible with `run_phase()` as
written today. `SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:32-74`) is the
directly-analogous, already-wired precedent: it iterates `state.entities.items()`, skips
inactive/dead, calls its own `.run()` per entity, and writes the result into
`EntityUpdate.self_model_bundle_set` (`src/core/updates.py:649`) via `dataclasses.replace`.

**`EntityUpdate`** (`src/core/updates.py:619-709`) has **no field for `entity.cognition`** — only
`self_model_bundle_set: Optional[Any]` for `entity.self_model` (a structurally distinct field on
`EntityState`, confirmed at `src/core/state.py:689-690`: `self_model: SelfModelBundle` and
`cognition: CognitionModel` are two separate top-level fields). Grepping all of `src/engine/`,
`src/domains/`, `src/cognition/` for any existing patch/update path that writes `entity.cognition`
confirms there is none — `entity.cognition` (subjective/memory/motivation/commitment/relationships)
is currently **write-only reachable via direct `dataclasses.replace()` inside test fixtures**, never
through the authoritative apply path. This is the concrete architectural gap this ticket must close,
not a pre-existing mechanism to just "call."

**Patch application** (`src/engine/patches.py`) — `SelfModelPatch` (lines 641-658) is the exact
template to mirror: `is_noop()`, `merge()`, and `apply(entity, changes)` which does
`changes["self_model"] = self.self_model_bundle_set`. `extract_patches()` (line 661-720) builds the
patch list per `EntityUpdate` field and is registered at the bottom (line 717-719). The final
`changes` dict is consumed by `ApplyPath._fast_replace_entity(entity, changes)`
(`src/engine/apply.py:440-456`), which performs the authoritative `dataclasses.replace(entity,
**changes)` — confirmed by call graph (`_apply_entity_update_to_dict` → `extract_patches` →
`patch.apply(entity, changes)` → `_fast_replace_entity`). A new `changes["cognition"] = ...` key
here would correctly land on `entity.cognition` the same way `self_model` does.

**Real combat-loss signal source** — `src/engine/domain/combat_actions.py::execute_attack()`
(lines 21-117) is the actual production call site for `CombatResolutionSystem.resolve_attack()`
(`src/engine/combat.py:129-243`), invoked from the `action_routing` phase
(`pipeline.py:237`, "Phase 3: Action & Movement Routing" — this runs **after** `self_model`,
`information_belief`, `cooperation`, `contracts/blacksmith`, and all the faction/diplomatic/military
phases, i.e. well after the ticket's proposed `MemoryUpdatePhase` insertion point in the *same*
tick). `combat_actions.py:96-108` builds `defender_up = EntityUpdate(..., combat=combat_up, ...)`
where `combat_up.alive_set` and `combat_up.damage_taken` are known. This is the correct real
producer site (see Risks/Design below for exactly what condition to key on and why).
`src/engine/pipeline_phases/hardening.py::NearDeathHardeningPhase.apply()` (runs near the *end* of
the tick, "near_death_hardening") independently computes an equivalent "survived critically low HP"
condition (`projected_hp <= 10% of max_hp`, lines 71-74) — a candidate reuse site, but see Risks for
why coupling the `combat_loss` trigger to *that specific* threshold defeats the `avoid_enemy`
fallback branch.

**`WorldEvent`/`recent_world_events`** (`src/domains/world_emergence/schema.py:15-58`,
`src/core/state.py:1151`) — the existing generic, already-wired, one-tick-lag cross-domain event
channel. Any phase can append to `StateUpdate.world_events_add` (used today by
`military_conflict.py`, `world_dynamics.py`, `world_emergence/services.py`, etc.); `apply.py:320-325`
merges `prior_events + update.world_events_add` into `state.recent_world_events` (windowed to 500),
which is then read by phases at the *start* of the *next* tick (documented precedent:
`pipeline.py:184-186`, "recent_world_events reflects last tick's window — one-tick lag is inherent
(state frozen)", used identically by `faction_awareness`). `WorldEventCategory` (lines 15-49) already
has `NEAR_DEATH` and `PARTY_ABANDONED` members, but **neither is ever actually constructed anywhere
in `src/`** (confirmed by grep — both are orphaned enum values, not live producers). No
`COMBAT_LOSS` category exists yet.

## Mechanics / Engine Constraints

- **`docs/engine/kernel.md`** — "The 7-Phase Kernel Loop" table: `Resolution` = "Collapse all
  proposals through the `AuthoritativeApplyPipeline`" (Synchronous). `refine()`'s internal
  ~30-phase sequence (this ticket's insertion point) lives entirely inside this one kernel phase.
  The "Law of Ticks" / Deterministic Order note ("entities are processed in a deterministic order,
  usually sorted by ID") constrains `MemoryUpdatePhase.apply()`'s new iteration — it must follow
  `SelfModelUpdatePhase.apply()`'s pattern of iterating `state.entities.items()` (already
  insertion-order/dict-order stable per existing precedent) rather than an unsorted structure.
- **Durable State Rule (project CLAUDE.md / Architecture Rule)**: "Decision logic reads state. It
  does not authoritatively mutate durable state... Durable changes must be represented through typed
  records/updates." `MemoryUpdatePhase.run()` returning raw `EntityState` objects directly violates
  this if called as-is from `refine()`. It must be wrapped in a `.apply(state, update) -> StateUpdate`
  method (mirroring `SelfModelUpdatePhase.apply()`) that writes into a new typed `EntityUpdate` field,
  never mutating `state.entities` in place.
- **`docs/mechanics/04_strategic_cognition.md` §6.11** (added by
  `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`) already documents the exact fallback-branch
  constraint: "`combat_loss` (fallback branch — fires only when none of `hp_pct < 0.3` /
  `stamina < 20` / `weapon_dur < 0.2` triggered) → `avoid_enemy` → `HUNT_WEAK_ENEMY` → Suppress →
  `−1.0`" (line 535). This is binding: any live `combat_loss` producer that structurally guarantees
  `hp_pct < 0.3` (e.g. tying it to the near-death-hardening threshold) can **never** reach this
  fallback, and the ticket's AC ("AdventureRouteScorer.score() produces a nonzero memory_adjustment")
  would then be unreachable via that producer for the `avoid_enemy`/`HUNT_WEAK_ENEMY` path (it would
  remain reachable for `party_abandoned`/`boost_party_trust` if that trigger were also built, but
  this ticket only commits to one producer).
- **`docs/simulation/domains/memory_contract.md`** §"What It May Mutate" (line 152): "`entity.cognition.memory.causal`
  — Append `CausalMemoryEntry`; evict oldest if at capacity — `dataclasses.replace`" — the capacity
  eviction (30 entries, FIFO, `src/core/cognition.py:260`) must be preserved by whatever wrapper is
  built; `MemoryUpdatePhase.run()` already implements this correctly (line 72-74) and should not be
  reimplemented, only wrapped.

## Docs Requiring Update

- `docs/simulation/domains/memory_contract.md`: line 173's Adventure-domain Domain Interactions row currently states "this is not yet observable in any live run: `MemoryUpdatePhase`... has zero call sites in `src/engine/pipeline.py`" — this becomes false once the call site is registered and must be corrected to describe the new live wiring (and the one-tick-lag semantics of the trigger producer, since that is new, non-obvious behavior a future reader needs).
- `docs/mechanics/04_strategic_cognition.md`: §6.11's "Not yet live" callout (line 546, "measurement is possible until `MemoryUpdatePhase` is wired into the pipeline") and the "not yet observable in a live run" framing must be updated once wired; if the recommended producer design (see Risks) is adopted, the fallback-branch constraint description itself does not change, only its live-reachability status.
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-227's `v2_evidence` (line 2555-2557) explicitly states "not yet observable in a live run since `MemoryUpdatePhase` has zero pipeline call sites" — this must be updated once wired, with a `test_path` addition covering the new end-to-end scenario test (AC3).

The `docs/engine/kernel.md` doc (path: `docs/engine/kernel.md`, under `docs/`) is not required to
change for this ticket: it documents the 7-phase kernel loop at a level of abstraction (Init /
Scheduling / Collection / Resolution / Cleanup / Advancement / Persistence) that does not enumerate
`AuthoritativeApplyPipeline.refine()`'s internal ~30 sub-phases by name — `self_model`,
`information_belief`, `cooperation`, etc. are none of them individually named in `kernel.md` either,
so adding `memory_update` alongside them does not create any new inconsistency with this doc.

## Parity Ledger Overlap

- **STRAT-227** (`docs/parity_ledger/strategic_cognition.yaml:2523-2568`), `status: verified`,
  `priority: P1`. Text and `v2_evidence` explicitly disclose the `memory_adjustment` term as "not yet
  observable in a live run since `MemoryUpdatePhase` has zero pipeline call sites
  (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING)". This is the single parity entry this ticket touches.
  `priority: P1`, not `P0`, so a passing `test_path` is required practice but not a hard DoD gate;
  `test_path` already lists 4 existing test files and should gain the new end-to-end scenario test.
  No other parity-ledger file (`town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`,
  `world_dynamics.yaml`, `infrastructure.yaml`, `combat_movement.yaml`, `substrate.yaml`) references
  `MemoryUpdatePhase`, `CausalAttributionService`, or `SpatialMemoryUpdateService` (confirmed by
  repo-wide grep across `docs/parity_ledger/`) — no new sibling entry is needed unless the planner
  decides the new `memory_update` pipeline phase itself (as opposed to the scoring-side term already
  covered by STRAT-227) warrants a dedicated entry; recommend extending STRAT-227 in place, matching
  how the prior ticket handled it (see Prior Work), rather than creating a new entry, since the
  underlying formula/constants are unchanged — only their live-reachability status changes.

## Prior Work

- **`TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`** (done, `tickets/done/`, artifacts in
  `stored_artifacts/TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING/`) — built the scoring-side
  `memory_adjustment` term this ticket's wiring will finally make observable. Its own
  `plan.md` Scope Guards (lines 452-467) explicitly refused to wire `MemoryUpdatePhase` into the
  pipeline, citing exactly the same three sub-problems this ticket's scope enumerates (pipeline
  registration + cadence decision, and a real `trigger_event` producer), and named this exact
  follow-up ticket by pattern (`TCK-YYYYMMDD-MEMORY-UPDATE-PHASE-PIPELINE-WIRING`). Its
  `plan.md:476-478` also lists the 8 deliberately-unmapped `future_advice` strings
  (`heal_first`, `rest_often`, `repair_weapon`, `seek_trusted_guide`, `verify_intel`, `acquire_mats`,
  `train_blacksmith`, `realign_directive`) — directly relevant to the mapping-extension open question
  below.
- **`TCK-20260529-COG-PHASE13-MEMORY`** (done) — original build of the memory domain
  (`TemporalModel`/`CausalMemory`/`SpatialMemory`, the 3 services, and `MemoryUpdatePhase` itself).
  Its own Scope never included pipeline wiring — "Orchestrate integration checks inside a dedicated
  memory pipeline phase" (i.e. build the phase class) is listed, but no pipeline.py registration.
  Confirms the phase was always built as a standalone, testable unit awaiting a caller — consistent
  with this investigation's finding of zero call sites.
- **`TCK-20260824-WIRE-ORPHANED-MECHANISMS`** (referenced as a sibling ticket, not read in full since
  its scope explicitly excludes `MemoryUpdatePhase`) — this confirms `MemoryUpdatePhase` is a known,
  separately-tracked orphaned-mechanism class, and this ticket is its designated owner.
- **Pattern precedent for the typed-update wrapper**: `SelfModelUpdatePhase.apply()`
  (`src/cognition/self_model_phase.py:32-74`) is the closest structural analog (an
  `EntityState`-list-processing service wrapped for `StateUpdate` integration) and should be copied
  almost verbatim for `MemoryUpdatePhase.apply()`.
- **Pattern precedent for the one-tick-lag signal**: `faction_awareness`
  (`pipeline.py:184-193`) already documents and uses exactly the "read `recent_world_events` from the
  prior tick, frozen state" pattern this ticket's recommended `combat_loss` producer design requires.
- **Pattern NOT applicable here**: "Pattern 6 — Compile-Time Pillar Activation Pattern"
  (`docs/guidelines/design_patterns.md:283-`) looks superficially similar (a durable-state field that
  is permanently empty because nothing populates it) but its fix shape is *compile-time* seeding from
  `world.yaml` content through `WorldCompiler.compile()` — the opposite of what this ticket's AC
  explicitly requires ("a real, live trigger_event producer... not just test dicts"). Do not reach
  for Pattern 6 here; the correct precedent is the `world_events_add`/`recent_world_events` live-event
  channel instead.

## Risks and Open Questions

**Recommendation — future_advice→RouteFamily mapping extension: do NOT extend it in this ticket.**
Rationale: the ticket's own Out-of-Scope section already frames this as a binary choice ("decide
whether to extend that mapping or purely wire the phase, not silently do both"), and
`TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`'s `plan.md` explicitly deferred all 8 remaining
`future_advice` strings to "a future ticket" with its own design-decision rationale per string — that
future ticket is `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`'s own continuation lineage, not this
one. This ticket's AC #3 ("AdventureRouteScorer.score() produces a nonzero memory_adjustment") is
**satisfiable without touching the mapping**, provided the trigger producer is designed to reach the
existing `avoid_enemy` fallback branch (see next point) — so there is no forcing function requiring
the mapping extension here. Extending the mapping is also a larger, separately-estimable piece of
work (8 more strings × design-decision-per-string, per the prior tic, `plan.md`) that would blur this
ticket's already-substantial scope (3 architectural sub-problems: typed-update wiring, a new producer,
and a signature redesign). Recommend the planner write this ticket to touch only
`src/domains/memory/phase.py`, `src/core/updates.py`, `src/engine/patches.py`,
`src/engine/pipeline.py`, `src/engine/domain/combat_actions.py` (or wherever the producer lands),
and `src/domains/world_emergence/schema.py` (new enum member) — not `src/domains/adventure/scoring.py`.

**Design (a) — how `MemoryUpdatePhase` integrates into `refine()`'s typed-update architecture:**
Add `MemoryUpdatePhase.apply(state: AuthoritativeState, update: StateUpdate) -> StateUpdate`,
mirroring `SelfModelUpdatePhase.apply()` line-for-line in structure: iterate
`state.entities.items()`, skip `not entity.lifecycle.active or not entity.combat.alive` (matching
`MemoryUpdatePhase.run()`'s own existing skip condition), call a per-entity variant of the existing
`run()` logic (either refactor `run()` to expose a per-entity helper, or call `run([entity], tick,
trigger_events=...)` and take `[0]`), and write the resulting new `CognitionModel` into
`new_entity_updates[entity_id] = replace(entity_up, cognition_bundle_set=new_cognition)`. This
requires two small, additive changes with no risk to existing fields:
1. `src/core/updates.py` `EntityUpdate` (line 619-651): add `cognition_bundle_set: Optional[Any] = None`
   (mirroring `self_model_bundle_set` at line 649) plus its `is_noop()` clause (line 672) and `merge()`
   clause (line 706) — exact copies of the `self_model_bundle_set` lines with the field name swapped.
2. `src/engine/patches.py`: add `CognitionPatch(ComponentPatch)` (mirroring `SelfModelPatch`,
   lines 641-658) with `apply(entity, changes)` setting `changes["cognition"] = self.cognition_bundle_set`,
   and register it in `extract_patches()` (line 717-719 pattern) as
   `if update.cognition_bundle_set is not None: patches.append(CognitionPatch(entity_id,
   cognition_bundle_set=update.cognition_bundle_set))`.
Register the phase call in `pipeline.py` between lines 136 and 143:
`update = run_phase("memory_update", update, lambda u: MemoryUpdatePhase.apply(state, u),
"ENABLE_MEMORY_UPDATE")` (see feature-flag note below).

**Feature-flag / cadence recommendation:** `FeatureFlagManager` (`src/domains/optimization/feature_flags.py`)
defaults every unregistered flag name to `FeatureMode.OFF` (line 120-121), and the codebase's stated
DEV-002 policy (referenced in comments at `feature_flags.py:77-78`) is default-OFF for new gated
phases that are pure additions (not replacing existing proven behavior) — every comparable
Enhanced-RPG phase added to `refine()` in this stretch (`self_model`, `information_belief`,
`information_intent_execution`, `cooperation`, `combat_engagement`, `world_emergence`,
`progression_conversion`) is registered with its own `ENABLE_*` flag. Recommend registering
`"ENABLE_MEMORY_UPDATE": FeatureMode.OFF` as the new default in `feature_flags.py`, consistent with
this pattern, rather than leaving `memory_update` ungated (ungated would make it always-on in every
existing corpus/SimQ run with no rollout control, which the prior ticket's plan flagged as an
"architecture-review-worthy decision this ticket's Scope does not authorize" — this ticket's Scope
does authorize it, but the safe default is still OFF with tests/scenarios explicitly enabling it).
This is a recommendation for the planner to confirm, not a blocking open question — no other Enhanced
RPG phase in this file skips the flag pattern, so following it is the path of least architectural
risk.

**Design (b) — recommended real trigger_event producer: `combat_loss`, built in
`src/engine/domain/combat_actions.py::execute_attack()`'s `defender_up` construction (lines 96-108),
NOT in `NearDeathHardeningPhase`.** Rationale (this is the central finding of this investigation):
`CausalAttributionService.attribute()`'s `"avoid_enemy"` advice — the only advice string
`AdventureRouteScorer.score()` currently reads for `combat_loss` — is reachable **only** via the
fallback branch, which fires **only when `hp_pct >= 0.3`** (among other conditions). If the producer
is tied to `NearDeathHardeningPhase`'s exact trigger condition (`projected_hp <= 10% of max_hp`,
`hardening.py:71-74`), then `hp_pct < 0.3` is true by construction on every single firing, so the
`"low_health"`/`"heal_first"` branch always wins and the fallback branch is **structurally
unreachable** — AC #3 ("AdventureRouteScorer.score() produces a nonzero memory_adjustment") would
then only be demonstrable by *also* extending the mapping to cover `heal_first` (contradicting the
recommendation above), or would require a contrived test fixture that never occurs from the real
producer. Instead, recommend: fire the `combat_loss` signal whenever the defender **survives and
takes damage** (`combat_up.alive_set is not False and combat_up.damage_taken > 0`), independent of
resulting HP fraction — this is a broader, more literal reading of "lost this combat exchange" (took
a hit, didn't prevent it) and naturally includes both severe cases (low HP → `heal_first`/etc.) and
mild cases (defender in otherwise-good shape → correctly reaches the `avoid_enemy` fallback,
satisfying AC #3 in the common/expected case without needing a special-cased test fixture). Emit this
as a new `WorldEvent(category=WorldEventCategory.COMBAT_LOSS, tick=state.tick,
region_id=target.navigation.region_id, subject=str(target.id))` appended to the `StateUpdate`'s
`world_events_add` returned from `ActionRoutingPhase`/`combat_actions.py`'s caller chain. This
requires adding one new enum member, `COMBAT_LOSS = "COMBAT_LOSS"`, to `WorldEventCategory`
(`src/domains/world_emergence/schema.py:15-49`) — a small, additive, precedented change (the enum has
grown incrementally by epic, e.g. E52A/E52B/E53Bd/E53Cc/E53Cd/E53Db/E52G tags in comments). Do **not**
reuse the existing unused `NEAR_DEATH` member for this — its name would misdescribe the broader
"took damage and survived" condition being recommended, and conflating the two would make future
maintenance (e.g. if someone later *does* want a true near-death signal) ambiguous.

**One-tick-lag consequence (must be documented, not a defect):** Because `action_routing` (where
combat resolves, `pipeline.py:237`) runs strictly *after* the proposed `memory_update` insertion
point (`pipeline.py:136-143`) within the same tick, a `combat_loss` `WorldEvent` produced during
tick N's `action_routing` is only visible in `state.recent_world_events` starting tick N+1 (after
`apply.py:320-325` merges it in). `MemoryUpdatePhase.apply()` must therefore read
`getattr(state, "recent_world_events", [])`, filter for `category == WorldEventCategory.COMBAT_LOSS`,
and build `trigger_events` dicts from them — the *previous* tick's combat losses, not the current
tick's. This exactly matches the already-documented `faction_awareness` precedent
(`pipeline.py:184-186`) and should be called out the same way in a comment at the new call site. An
end-to-end AC #3 scenario test must therefore run at least 2 ticks (one for the combat resolution,
one for the memory phase to consume the resulting `recent_world_events` entry).

**Design (c) — `MemoryUpdatePhase.run()` signature redesign, and existing test-call-site impact
(confirmed, not hypothetical):** Change `trigger_event: Optional[dict] = None` to
`trigger_events: Optional[List[dict]] = None` (list, plural). Internally build
`trigger_by_entity = {t["entity_id"]: t for t in (trigger_events or [])}` and replace the current
linear `if trigger_event and trigger_event.get("entity_id") == entity.id:` check (line 57) with
`trigger = trigger_by_entity.get(entity.id)`. **Confirmed existing call sites requiring updates**
(grepped directly, not assumed): `tests/integration/domains/memory/test_phase13_memory_update_phase.py`
line 18 (`phase.run([entity], tick=10, trigger_event=trigger)` →
`trigger_events=[trigger]`) and `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`
line 25 (same pattern) — 2 files, 2 call sites total; both are simple keyword-argument renames
(`trigger_event=X` → `trigger_events=[X]`), no other logic changes needed since both tests use a
single trigger for a single entity. `test_phase13_memory_update_phase.py`'s second test
(`test_phase_updates_temporal_staleness_after_old_fact`, line 36) passes no trigger argument at all
and is unaffected by the rename (default `None` still works and produces an empty dict via
`trigger_by_entity = {}`). No production code calls `.run()` directly today (only the new `.apply()`
wrapper being built by this ticket would), so this is a fully-contained, fully-enumerated rename with
no unknown blast radius.

**Open question left genuinely unresolved (not blocking, flagged for planner):** should
`MemoryUpdatePhase.apply()`'s per-entity call reuse `run()` (looping internally, `O(1)` call but
`O(n)` list churn per invocation if called per-entity) or should `run()` itself be refactored so
`apply()` calls it once with the full entity list and full `trigger_events` list (matching the shape
`run()` already has, since it's already list-based)? The latter is more efficient and requires no
change to `run()`'s existing bulk-list contract beyond the signature rename above — recommend the
planner choose this (call `run(list(state.entities.values()), tick=state.tick,
trigger_events=trigger_events)` once, then map results back into `new_entity_updates` by `entity.id`)
rather than per-entity calls, since `run()` is already correctly bulk-shaped and per-entity calls
would be pure overhead with no correctness benefit.

## Anti-Drift Hazards

- **Do not let `MemoryUpdatePhase.apply()` write directly to `state.entities`** — it must go through
  `EntityUpdate.cognition_bundle_set` → `CognitionPatch` → `changes["cognition"]` →
  `_fast_replace_entity`, exactly like `self_model_bundle_set`. A direct mutation would violate the
  Durable State Rule and silently break replay/determinism guarantees documented in `kernel.md`.
- **Do not touch `AdventureRouteScorer.score()` or the `future_advice`→`RouteFamily` mapping** unless
  the planner explicitly overrides the recommendation above — this is the exact boundary the ticket's
  Out-of-Scope section protects, and touching it without an explicit decision record would silently
  do both things the ticket says not to.
- **Do not couple the new `combat_loss` producer to `NearDeathHardeningPhase`'s threshold** — this is
  the single most likely accidental-scope-narrowing mistake an implementer could make (it looks like
  free reuse of existing detection logic) and would silently make AC #3 unsatisfiable for the
  `avoid_enemy` path, per the fallback-branch analysis above.
- **Do not forget the one-tick-lag** when writing the AC #3 end-to-end scenario test — asserting
  `memory_adjustment != 0` in the *same* tick as the triggering combat resolution will fail even with
  a correct implementation, because `recent_world_events` is frozen-per-tick by design.
- **Do not widen `MemoryUpdatePhase.run()`'s existing skip condition** (`not entity.lifecycle.active
  or not entity.combat.alive`) — this is deliberate and must stay: an entity that died in the same
  tick's `action_routing` should not receive a `combat_loss` memory update from that death event next
  tick if it's no longer active (dead entities don't reason about the future).
- **Do not silently rename `trigger_event` → `trigger_events` without updating both confirmed test
  call sites** in the same commit — `done-checker`'s test-scope-coverage check would catch a broken
  import/call at CI, but fixing it reactively costs a round trip; both are enumerated above with exact
  line numbers.
