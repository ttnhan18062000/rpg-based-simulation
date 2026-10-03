---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP

## Docs Requiring Update

- `docs/simulation_quality/event_type_coverage.md`: register the new event(s) (Implement phase)
- `docs/event_ledger/entity.yaml`: flip `ENTITY-014` to `observed` (Implement phase)

## Real mutation sources for `EquipmentUpdate`

`grep -n "EquipmentUpdate(" src/` returns 7 hits. Verified each for real reachability, same
methodology as the sibling vitals/attributes tickets.

| Site | Verdict | Evidence |
|---|---|---|
| `src/engine/evolution.py:76` (goblin-kind species evolution gear grant) | **LIVE, narrow** | `EvolutionSystem` is unconditionally pipeline-wired (`pipeline.py:23`, confirmed in the sibling attributes ticket). Slot assignment only fires when `evolved` is True (crossing evolution-level thresholds 10/25/50) AND `"goblin" in new_kind.lower()` — a narrow but real, unconditional-flag-free path. |
| `src/domains/progression/resolver.py:43` (`EQUIP_ITEM` → hardcoded `iron_sword`) | **GATED OFF** | Routed through `ConversionIntentResolver.resolve`, called only by `ProgressionConversionPhase.execute` (`src/domains/progression/phase.py`), wired into the pipeline behind `ENABLE_PROGRESSION_EVOLUTION` (`pipeline.py:326`). `src/domains/optimization/feature_flags.py:20` sets this flag `OFF` by default; `grep -rln "ENABLE_PROGRESSION_EVOLUTION" config/simulation_quality/profiles/` returns zero hits — no shipped profile overrides it. Corpus-wide off, same reachability class as `ENABLE_COMBAT_ENGAGEMENT`. |
| `src/engine/combat.py:114/124` (`_get_durability_decay`, attacker/defender) | **GATED OFF** | Inside `CombatResolutionSystem.resolve_attack` — combat is corpus-wide gated off (`ENABLE_COMBAT_ENGAGEMENT`, `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`), same as the sibling vitals ticket's wound events. |
| `src/engine/domain/core_actions.py:238` (`execute_repair`) | **GATED OFF** | Routed via `action_router.py`'s `"REPAIR"` action, driven by `action_intent.py`'s `IntentExecutionService` dispatch on `intent.kind == "REPAIR_GEAR"`. `grep -rln "REPAIR_GEAR" src/` shows it is produced *only* inside `src/domains/progression/{generator,resolver,selector,schema}.py` — the same `ENABLE_PROGRESSION_EVOLUTION`-gated conversion domain as `EQUIP_ITEM` above. `grep -rln "REPAIR_GEAR\|EQUIP_ITEM" src/ai/` returns zero hits — no broader strategic/goal system produces these intents independently. `resolver.py`'s own separate `REPAIR_GEAR` branch (mapping to a `BLACKSMITH_REPAIR` `TaskUpdate`, not directly to `EquipmentUpdate`) is additionally a dead end on its own: `grep -rln "BLACKSMITH_REPAIR" src/` shows nothing ever consumes that task-kind to complete it. |
| `src/core/equipment.py:239` (`EquipmentService.auto_equip`) | **DEAD CODE** | `grep -rln "EquipmentService" src/` returns zero hits outside its own file — zero real callers anywhere. Only referenced by `tests/unit/resource/test_equipment_ranking.py` / `test_equipment_chests_storage.py`. |
| `src/core/equipment.py:265` (`EquipmentService.repair_equipment`) | **DEAD CODE** | Same class, same zero-caller verdict as above. |

**Conclusion**: every equipment-mutating producer with real narrative weight (item swap on
combat-hit, repair, generic equip-from-inventory) is either gated off corpus-wide
(`ENABLE_COMBAT_ENGAGEMENT` / `ENABLE_PROGRESSION_EVOLUTION`, both off in every shipped profile)
or dead code. Only `evolution.py`'s narrow goblin-evolution gear grant is genuinely live and
unconditional — same overall shape as the attributes ticket's finding (1 live-but-narrow, several
gated/dead).

## Tangential finding (disclosed, NOT fixed — out of scope): durability scale mismatch bug

`src/domains/progression/gaps.py:50-56` (`repair_gap` detection) and
`src/engine/gold_sink.py:158-166` (`_count_degraded_slots`, REPAIR_FEE) both compare
`entity.equipment.durability` values against a **0.0–1.0** normalized scale (`worst_durability
< 0.5`, `durability.get(slot, 1.0) < 0.5`). But the real mutation code uses a **0–100** scale
throughout: `src/core/equipment.py::repair_equipment` defaults missing durability to `100.0`;
`src/engine/combat.py::_get_durability_decay` applies `-1.0`/`-0.5` per hit;
`src/engine/domain/core_actions.py::execute_repair` sets `repair_deltas[slot] = 100.0`. Any real
durability value read from state (e.g. `95.0`) is never `< 0.5`, so `repair_gap`'s severity
scoring and `REPAIR_FEE`'s gold-sink trigger are both silently unreachable in practice — a
pre-existing mechanics-correctness bug, not introduced by this ticket. Not fixed here: it lives
in `gaps.py`/`gold_sink.py` (an apply/detection-logic correctness question), out of scope for an
observability ticket, and (per the table above) the durability-decay/repair producers that would
even generate a meaningful non-100 value are themselves currently gated off, so nothing regresses
by leaving this as a disclosed, unfixed finding.

## Event design

Post-tick STATE diffing, same methodology as the sibling tickets: `entity.equipment.slots:
Dict[EquipSlot, str|None]` and `entity.equipment.durability: Dict[EquipSlot, float]`
(`EquipmentComponent`, `src/core/state.py:647-650`).

Two events, matching the ticket's own suggested design:

- **`item_equipped`** / **`item_unequipped`** — per slot, per real change. `item_equipped` when a
  slot's item id changes to a non-None value (payload includes `previous_item_id` when it was a
  swap, not a fresh equip); `item_unequipped` when a slot's item id changes to `None`. Severity
  `INFO` — a routine gearing action, no existing narrative-significance signal to lean on.
- **`equipment_durability_changed`** — per slot, per real delta (not per-tick — durability only
  changes on discrete combat-hit or repair actions per the mutation-source table above, never on
  an unconditional per-tick decay, so full-delta coverage does not create `movement`/`biological`-
  class volume; the ticket's own original "not per-tick" caution was based on an assumption not
  borne out by the real producers). Severity grounded in the real 0–100 scale (correcting the
  disclosed scale-mismatch bug's *intent*, not its buggy code): `INFO` for a repair/increase or a
  decrease that stays `>= 50.0`; `WARNING` for a decrease that drops below `50.0` but stays
  `> 0.0`; `CRITICAL` for a decrease that reaches `<= 0.0` (item fully broken). The `50.0`
  threshold is not invented — it is the same intent already designed into `gaps.py`/`gold_sink.py`
  (both compare against `0.5`), just applied on the field's actual real-world scale instead of the
  mismatched one those two call sites use.

## Real-verification (actual result, not just the plan)

Attempted a real `Kernel.tick_once()` loop first, per the plan below. Checked directly during
Implement (not assumed): `sandbox_world` has **zero** goblin-kind entities at all
(`[e for e in state.entities.values() if "goblin" in e.kind.lower()]` → empty), so the one live,
unconditional producer (`evolution.py`'s goblin-evolution gear grant) cannot fire in this world
regardless of tick budget — confirmed via a real, non-mocked 1000-tick loop producing zero
`item_equipped`/`item_unequipped`/`equipment_durability_changed` events. Fell back to this repo's
own precedented hand-built-state pattern for both event types (real `EquipmentComponent` objects
constructed by hand, diffed through the real `EventExtractor.extract()` function directly), same
fallback class as `wound_sustained` (vitals ticket) and `attribute_changed` (attributes ticket).

(Original plan, superseded by the above: attempt a real tick loop first since one producer is
live and unconditional, on the theory that `sandbox_world` might contain a goblin-kind entity
that could reach evolution level 10 within a reasonable tick budget; fall back to hand-built
state only if that didn't pan out.)

## Classification (per explicit user direction — precise, not binary)

Currently: `docs/event_ledger/entity.yaml` `ENTITY-014` = `silent`. After this ticket: `observed`,
classified `unscored_intentional` (`docs/simulation_quality/event_type_coverage.md` §5) — the
ticket's own Out of Scope flags ECONOMY pillar as a plausible future candidate, not decided here.
