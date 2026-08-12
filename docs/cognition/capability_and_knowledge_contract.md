---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Capability Estimation and Knowledge Model Contract

**Source:** `src/cognition/capability_estimate.py`, `src/cognition/knowledge_model.py`
**Related docs:** [README.md](README.md), [self_model_contract.md](self_model_contract.md), [docs/simulation/domains/adventure_contract.md](../simulation/domains/adventure_contract.md)

---

## Capability Estimation — `capability_estimate.py`

### Purpose

`CapabilityEstimateService.estimate()` produces the entity's **subjective assessment of what it can do**: can it fight this enemy, travel to this region, gather this resource, craft this recipe? These estimates are subjective — they are based on the entity's current stats and what it was told, not ground truth.

### Scoped estimation

Capability estimation is **caller-scoped** — the caller provides a `CapabilityContext` specifying exactly which capabilities to estimate. The service does not scan the world.

```python
CapabilityContext:
    combat_enemies: Tuple[str, ...]      # enemy type ids to estimate combat against
    travel_regions: Tuple[str, ...]      # region ids to estimate travel safety for
    gather_resources: Tuple[str, ...]    # resource ids to estimate gathering feasibility
    craft_recipes: Tuple[str, ...]       # recipe ids to estimate crafting feasibility
```

If `context is None`, returns an empty `CapabilityEstimateComponent`.

### Estimation formulas

**Combat:**
```python
base_power = (atk + defense × 0.5) / max(1.0, enemy_level × 5 + danger × 20)
raw_estimate = min(1.0, base_power × 1.5)
raw_estimate *= hp_fraction          # wounded → less capable
raw_estimate *= (0.7 + 0.3 × stamina_fraction)  # tired → slightly less capable
confidence = 0.9 if known enemy type else 0.5
confidence *= (hp_fraction × 0.5 + 0.5)  # lower HP → less confident about self
```

**Travel:**
```python
safety = (1.0 − region_danger) × hp_fraction × (0.7 + 0.3 × stamina_fraction)
confidence = 0.85 if known region else 0.4
```

**Gather:**
```python
estimate = (0.8 if has_required_tool else 0.2) × hp_fraction
confidence = 0.8 if tool requirement specified else 0.6
```

**Craft:**
```python
if missing any required item OR insufficient gold:
    estimate = 0.0, confidence = 0.9  # we know we can't
else:
    estimate = 0.85, confidence = 0.9  # materials present
# unknown recipe: estimate = 0.3, confidence = 0.3
```

### CapabilityEstimate record

Each estimate stored as `CapabilityEstimate(capability_key, estimate, confidence, source, last_updated_tick)`.

`capability_key` format: `"combat.enemy_type.{enemy_id}"`, `"travel.region.{region_id}"`, `"gather.resource.{resource_id}"`, `"craft.recipe.{recipe_id}"`.

### How adventure routing uses capability estimates

As of `TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`, `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) calls `CapabilityEstimateService.estimate()` directly, ad hoc, for `GATHER_RESOURCE` and `CRAFT_UPGRADE` routes with a resolvable capability key — the resulting `CapabilityEstimate.estimate` value feeds `confidence_bonus` (replacing the flat `route.confidence × 0.15` term for those two families only), NOT a blocker-generation threshold mechanism. There is no `−2.0` capability-blocker penalty anywhere in `scoring.py` — that prior claim was aspirational and inaccurate. This call is scorer-local and ad hoc: it does not go through `SelfModelUpdatePhase`, and `entity.self_model.capabilities.estimates` remains empty in production (see `docs/mechanics/04_strategic_cognition.md` §6.12's closing disclosure), because `SelfModelUpdatePhase.apply()` never passes a `capability_context` to `run()`. Unlike `memory_adjustment`'s "Not yet live" callout (§6.11), this term IS live and observable via a real `generate() → score()` chain today — only `entity.self_model.capabilities` itself stays unpopulated, not the scorer-local read of it.

### Confidence decay

The subsystem does not implement active confidence decay — estimates are static until re-computed. The `last_updated_tick` field allows consumers to check freshness.

---

## Knowledge Model — `knowledge_model.py`

### Purpose

`KnowledgeModelService.assimilate()` converts what information providers tell the entity into the entity's **owned knowledge records**. This is NOT the entity's beliefs about uncertain world state (that is `belief.py`) — this is structured factual knowledge: "resource node X exists at location Y with certainty Z".

### Critical invariant

Hidden world truth is NEVER injected. Only what the `InformationResponse` returned is assimilated. This preserves information opacity — entities cannot know things they weren't told.

### Assimilation mapping

| answer_kind | What gets assimilated |
|---|---|
| `"known"` | KnowledgeFact(s) with full certainty from response |
| `"partial"` | KnowledgeFact(s) where available + UnknownFact(s) for the rest |
| `"unknown"` | UnknownFact(s) only (entity learned there's a gap) |
| `"insufficient_gold"` | Nothing — entity couldn't pay for the information |

### Knowledge records

```python
KnowledgeFact:
    subject: str        # what the fact is about
    fact_type: str      # kind of fact (location, threat_level, owner, etc.)
    details: Dict       # fact payload
    certainty: float    # 0.0–1.0 (from response)
    source_id: int      # which entity/provider told us
    recorded_tick: int

UnknownFact:
    subject: str        # what we know we don't know about
    reason: str         # why it's unknown
    recorded_tick: int
```

### Merge semantics

`assimilate()` starts from the entity's current `KnowledgeModelComponent` and adds/updates. It does NOT remove existing knowledge — knowledge accumulates.

If a fact for the same subject+fact_type already exists, it is overwritten with the new response data. The `recorded_tick` field tracks when the update happened.

### When knowledge is assimilated

Only when `SelfModelUpdatePhase.run()` detects `InformationResponse` events in the tick's event log. If the entity received no information responses this tick, knowledge is unchanged (dirty check skips re-processing).

### Trace events

- `KnowledgeFactLearnedEvent` — emitted when a new fact is learned or updated (detected by `recorded_tick` change)
- `KnowledgeUnknownRecordedEvent` — emitted when a new unknown is recorded

Both events are collected by the orchestrator and routed to the warehouse/history API.

---

## Regression tests

- `tests/unit/cognition/test_phase2_capability_estimate_service.py` — combat/travel/gather/craft formulas, scoped context, None context → empty
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` — assimilation by answer_kind, accumulation (no removal), certainty propagation, insufficient_gold no-op
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py` — KnowledgeFactLearnedEvent emitted on fact update, trace event emission coverage

---

## Extension rules

1. To add a new capability domain (e.g., social/negotiation estimate): add to `CapabilityContext`, add estimation logic in `CapabilityEstimateService.estimate()`, define a `capability_key` format string, update the adventure domain if it should use the new capability for routing.
2. To add confidence decay: add a decay method to `CapabilityEstimateService` that ages estimates by `last_updated_tick`. Call it in `SelfModelUpdatePhase.run()` before Step 4.
3. To add a new fact type to the knowledge model: extend the `fact_type` values used by providers. The knowledge model is generic — no changes to `knowledge_model.py` are needed unless the merge semantics for the new type differ.
4. Never inject world truth directly into the knowledge model — all knowledge must arrive via `InformationResponse`. This is the information opacity invariant.
