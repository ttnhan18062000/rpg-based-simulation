# Plan — TCK-20260703-SIMQ-UPLIFT3-BRANCH-B

## Scope confirmation (per 2026-07-03 ticket rewrite)

This ticket fixes **two** bugs together, per the ticket's own 2026-07-03 scope expansion:

1. `src/cognition/self_model_phase.py:47-52` (`SelfModelUpdatePhase.apply()`) hardcodes `events=[]`
   — re-verified against current `src/`, unchanged from the investigation snapshot.
2. `src/engine/pipeline.py:152` — `information_belief`'s call-site lambda does not use the
   established `u.merge(...)` pattern, so `InformationBeliefPhase`'s output silently replaces (not
   merges with) the tick's prior `StateUpdate`, wiping `self_model`'s same-tick write. **Root-cause
   correction, resolved with evidence**: the bug is NOT inside `InformationBeliefPhase.apply()`
   itself (that method already returns a clean, self-contained `StateUpdate` — its return-shape is
   structurally identical to `MilitaryConflictPhase.execute()`, which also returns a bare
   `StateUpdate` and relies on its **call site** to merge). The bug is entirely in
   `src/engine/pipeline.py:152`'s lambda, which calls `InformationBeliefPhase.apply(...)` directly
   instead of wrapping it in `u.merge(...)` the way lines 181, 211, and 221 do for
   `faction_awareness`/`diplomatic_transitions`/`military_conflict`. Fixing the call site achieves
   the identical effect with a strictly smaller blast radius (one line in `pipeline.py`, zero lines
   in `src/domains/information/phase.py`) and higher pattern fidelity (matches all 3 siblings
   exactly — none of them merge inside their own phase class either). This also means the ticket's
   Out-of-Scope guard "do not modify the 3 sibling phases' own logic" is trivially satisfied — they
   are not touched at all, and neither is `InformationBeliefPhase` itself.

Confirmed via direct source read (this session): `SelfModelUpdatePhase.apply(state, u)`
(`self_model_phase.py:33-64`) **already** takes `update` as a parameter and returns
`dataclass_replace(update, entity_updates=new_entity_updates)` — i.e. `self_model`'s own pipeline
wiring is already merge-safe; it is not part of Finding 4's defect. Only `information_belief`'s call
site is broken.

---

## Step 1 — Schema: `PendingSelfModelInformationEventSpec` on `WorldSpec`, mirrored onto
`WorldCompositionSpec`/`NormalizedWorldComposition` (third application of Pattern 6)

**Why a third field, not reuse of `pending_information_responses`:** confirmed by direct comparison
of `src.world.providers.information.InformationResponse` (`src/world/providers/information.py:23-31`
— Step 1's actual consumer via `KnowledgeModelService.assimilate()`) against
`pending_information_responses`' stored dict shape (`answer_kind` uppercase vocabulary
`KNOWN_FACT`/etc., consumed by `InformationResponseNormalizer.normalize()` — a different type).
Reusing the field would require two parallel vocabularies on one field; a separate field with its
own (lowercase) vocabulary is the established, precedented shape (Pattern 6, `docs/guidelines/design_patterns.md`
lines 342-350: "no catalog exists → direct passthrough, no merge, no membership validation").

**Exact consumer shape re-confirmed this session** — `InformationResponse`
(`src/world/providers/information.py:23-31`):
```python
@dataclass(frozen=True, slots=True)
class InformationResponse:
    answer_kind: str  # "known" | "partial" | "unknown" | "insufficient_gold"
    facts: Tuple[KnowledgeFact, ...] = field(default_factory=tuple)       # KnowledgeFact = provider-side transfer object, same file
    unknowns: Tuple[str, ...] = field(default_factory=tuple)             # plain subject strings
    suggested_leads: Tuple[LeadState, ...] = field(default_factory=tuple)
    certainty: float = 0.0
    source_id: Optional[str] = None
    cost_gold: int = 0
```
`KnowledgeModelService.assimilate()` (`src/cognition/knowledge_model.py:42-130`) reads every one of
these via `getattr(response, ...)` (attribute access, not dict-item access) — so the compile-time
construction for this field **must** build real `InformationResponse` dataclass instances (mirrors
the `information_source_profiles` precedent — typed objects constructed once at compile time — not
the `pending_information_responses` precedent — raw dicts consumed via `r["..."]` item access).
`InformationQueryRouter`/`InformationBeliefPhase` never touch this new field, so there is no
signature clash with Branch A's dict-shaped list.

**Deliberate scope narrowing (resolved, not an open question):** `suggested_leads` is intentionally
**excluded** from the new spec. `LeadState` (`src/core/strategic.py:205`) requires fields (`lead_id`,
`certainty` as a `LeadCertainty` enum, etc.) that have no bearing on this ticket's Acceptance
Criteria (`self_model.knowledge.unknowns` populated; Branch B reachable) — `KnowledgeModelService`
only turns leads into low-confidence `facts["lead.<subject>"]` entries, not `unknowns` entries, so
omitting them cannot block Branch B (Branch B reads `self_model.knowledge.unknowns` exclusively,
`src/domains/information/phase.py:85-89`). Adding compile-time `LeadState` seeding is a
disproportionate addition with zero AC benefit; the compiler always passes `suggested_leads=()` for
now. This is strictly additive to extend later — not a design dead-end.

**Files and changes:**

1. `src/worldbuilding/schema.py` — add two new classes co-located directly after
   `PendingInformationResponseSpec` (current lines 75-96):
   ```python
   class SelfModelInformationFactSpec(BaseModel):
       """Maps 1:1 onto src.world.providers.information.KnowledgeFact (the provider-side transfer
       object in that same file — NOT src.core.self_model.KnowledgeFact, the entity-owned record,
       and NOT src.worldbuilding.schema's own PendingInformationResponseSpec vocabulary)."""
       model_config = ConfigDict(frozen=True)

       subject: str = Field(..., min_length=1)
       fact_type: str = Field(..., min_length=1, description="e.g. 'resource_source' | 'recipe_definition' | 'danger_rating'")
       details: Dict[str, Any] = Field(default_factory=dict)


   class PendingSelfModelInformationEventSpec(BaseModel):
       """Compile-time-seeded InformationResponse-shaped event for SelfModelUpdatePhase's Step 1
       (KnowledgeModelService.assimilate()) — the third application of the compile-time-seed
       pattern (docs/guidelines/design_patterns.md, Pattern 6), following
       information_source_profiles and pending_information_responses. Distinct from
       PendingInformationResponseSpec: this targets src.world.providers.information.InformationResponse's
       lowercase answer_kind vocabulary (Step 1's actual consumer), not
       InformationResponseNormalizer's uppercase vocabulary (Branch A's consumer)."""
       model_config = ConfigDict(frozen=True)

       target_population_id: str = Field(
           ..., min_length=1,
           description="Same addressing mechanism as PendingInformationResponseSpec.target_population_id "
                       "— resolved to a compiled actor_id via entity.properties['population_id'] matching."
       )
       answer_kind: Literal["known", "partial", "unknown", "insufficient_gold"] = Field(
           ..., description="Matches InformationResponse.answer_kind's lowercase vocabulary exactly "
                            "(src/world/providers/information.py:25). Do NOT use "
                            "PendingInformationResponseSpec's uppercase vocabulary "
                            "(KNOWN_FACT/PARTIAL_LEAD/RUMOR/CONTRADICTION) — different consumer, "
                            "different type, different casing."
       )
       facts: List[SelfModelInformationFactSpec] = Field(default_factory=list)
       unknowns: List[str] = Field(
           default_factory=list,
           description="Plain subject strings — maps directly onto InformationResponse.unknowns: "
                       "Tuple[str, ...]. NOT UnknownFact objects (that is Branch A's "
                       "NormalizedInformationResponse.unknowns shape, a different, incompatible type)."
       )
       certainty: float = Field(0.0, ge=0.0, le=1.0)
       source_id: Optional[str] = Field(None)
       cost_gold: int = Field(0, ge=0)
   ```
2. `WorldSpec` (current lines 170-184) gains, alongside `pending_information_responses` (line 182):
   ```python
   pending_self_model_information_events: List[PendingSelfModelInformationEventSpec] = Field(default_factory=list)
   ```
3. `src/worldassembly/schema.py` — extend the existing import line (current line 7) to include
   `PendingSelfModelInformationEventSpec`. `WorldCompositionSpec` (current lines 21-53) gains,
   alongside `pending_information_responses` (lines 48-53):
   ```python
   pending_self_model_information_events: List[PendingSelfModelInformationEventSpec] = Field(
       default_factory=list,
       description="Compile-time-seeded InformationResponse-shaped events for "
                   "SelfModelUpdatePhase's Step 1 (KnowledgeModelService.assimilate()). No global "
                   "catalog exists for this content (same reasoning as "
                   "information_source_profiles/pending_information_responses). Scoped to this "
                   "composition only."
   )
   ```
   `model_config` stays `frozen=True, extra="forbid")` — unchanged.
4. `NormalizedWorldComposition` (current lines 143-173) gains the **identical mirrored field**
   (verbatim same `Field(...)` block) — required by the `extra="forbid"` trap documented in Pattern
   6 (`WorldCompositionNormalizer.normalize()` does `composition.model_dump()` →
   `NormalizedWorldComposition(**data)`; an unmirrored field raises `ValidationError` on **every**
   `normalize()` call, for every world, not just the target one). Treat steps 3 and 4 as one atomic
   change, per Pattern 6's explicit warning.

**Dependency:** none (root of the change). Blocks Steps 2 and 3.

**Verification:**
- `PendingSelfModelInformationEventSpec(target_population_id="pop_1", answer_kind="unknown", unknowns=["material.moon_resin.source"])` constructs with `facts == []`, `certainty == 0.0`, `source_id is None`, `cost_gold == 0`.
- `PendingSelfModelInformationEventSpec(..., answer_kind="UNKNOWN")` (uppercase) raises `ValidationError` (Literal is lowercase-only) — regression guard against vocabulary confusion with `PendingInformationResponseSpec`.
- `WorldSpec.model_validate({... no pending_self_model_information_events key ...})` → `.pending_self_model_information_events == []`.
- `WorldCompositionNormalizer.normalize(...)` succeeds without raising for a composition with no `pending_self_model_information_events` key, and a composition with one entry round-trips it onto `NormalizedWorldComposition` unchanged. Add as a new assertion appended to `tests/unit/worldassembly/test_assembly.py::test_composition_normalization_shorthand_and_mixed` (line 716), matching the existing `pending_information_responses` coverage added by the prior ticket — not a new test function.
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_valid_minimal_world_spec_loads` must still pass unmodified.

---

## Step 2 — Resolver: composition-level passthrough

**File:** `src/worldassembly/resolver.py`, `WorldAssemblyResolver.assemble()`

**Change:** in the `world_spec = WorldSpec(...)` constructor call (current lines ~665-679,
alongside `pending_information_responses=list(normalized_comp.pending_information_responses)` at
line 674), add:
```python
pending_self_model_information_events=list(normalized_comp.pending_self_model_information_events),
```
Direct passthrough, no merge, no catalog — identical shape to Step 2 of the Branch A plan.

**Dependency:** requires Step 1. Independent of Step 3.

**Verification (new tests in `tests/unit/worldassembly/test_assembly.py`):**
- `test_resolver_passes_pending_self_model_information_events_from_composition`: a composition
  declaring 1 entry → `resolved.world_spec.pending_self_model_information_events` contains it,
  fields round-tripped unchanged.
- `test_resolver_no_pending_self_model_information_events_declared_yields_empty_list`: a composition
  with no key → `resolved.world_spec.pending_self_model_information_events == []` (regression guard
  — every world other than `urban_political` must be unaffected). Mirrors
  `test_resolver_no_pending_information_responses_declared_yields_empty_list` (`test_assembly.py:272`).

---

## Step 3 — Compiler: resolve `target_population_id` → actor_id, construct real `InformationResponse`
objects, seed `AuthoritativeState.pending_self_model_information_events`

**File:** `src/worldbuilding/compiler.py`

**Changes:**
1. Add an import near the existing `from src.domains.information.schema import InformationSourceProfile`
   (current line 28):
   ```python
   from src.world.providers.information import InformationResponse as _ProviderInformationResponse
   from src.world.providers.information import KnowledgeFact as _ProviderKnowledgeFact
   ```
   (aliased to avoid any ambiguity with `src.core.self_model.KnowledgeFact` or
   `src.core.quests`/other same-named imports already in this file — confirm no existing alias
   collision at implementation time.)
2. Insert directly after the existing `pending_information_responses` resolution block (current
   lines 426-452, ending with `pending_information_responses.append({...})`), reusing the same
   `entities` dict and the same `warnings` list (already declared at line 356, used at line 435 —
   no redeclaration):
   ```python
   # 6c. Resolve pending_self_model_information_events: target_population_id -> compiled actor_id,
   # construct real InformationResponse objects (Step 1's consumer needs attribute access, not
   # dict-item access — a different construction shape from 6b above).
   pending_self_model_information_events: List[Dict[str, Any]] = []
   for r in spec.pending_self_model_information_events:
       actor_id = next(
           (eid for eid, e in entities.items()
            if e.properties.get("population_id") == r.target_population_id),
           None,
       )
       if actor_id is None:
           warnings.append(
               f"pending_self_model_information_events target_population_id "
               f"'{r.target_population_id}' matched no compiled entity; entry skipped"
           )
           continue
       event = _ProviderInformationResponse(
           answer_kind=r.answer_kind,
           facts=tuple(
               _ProviderKnowledgeFact(subject=f.subject, fact_type=f.fact_type, details=dict(f.details))
               for f in r.facts
           ),
           unknowns=tuple(r.unknowns),
           suggested_leads=(),
           certainty=r.certainty,
           source_id=r.source_id,
           cost_gold=r.cost_gold,
       )
       pending_self_model_information_events.append({"actor_id": actor_id, "event": event})
   ```
3. Pass `pending_self_model_information_events=pending_self_model_information_events` into the
   single `AuthoritativeState(...)` constructor call (current lines 455-470, alongside
   `pending_information_responses=pending_information_responses` at line 469) — the one
   authoritative init point; no second seeding path added.

**Container shape decision (resolved with evidence):** the outer list is a list of
`{"actor_id": int, "event": InformationResponse}` dicts — outer shape mirrors
`pending_information_responses`' actor-id-addressed list-of-dicts (so `self_model_phase.py`'s read
logic can do the same simple `entry["actor_id"]` filtering `InformationBeliefPhase.apply()` already
does for `pending_responses`), while the inner `event` payload is a genuine typed
`InformationResponse` instance (mirrors `information_source_profiles`' typed-construction
precedent), because `KnowledgeModelService.assimilate()` requires attribute access. This is the
smallest hybrid that satisfies both established precedents without inventing a new wrapper class.

**Dependency:** requires Step 1 and the entity-compilation loop (pre-existing, unconditional
ordering). Independent of Step 2 — fully testable with a hand-built `WorldSpec` fixture.

**Verification (new tests in `tests/unit/worldbuilding/test_world_compiler.py`, following the exact
fixture style of `test_compiler_seeds_pending_information_responses_from_spec`, line 270):**
- `test_compiler_seeds_pending_self_model_information_events_from_spec`: hand-built `WorldSpec` with
  one population (`id="pop_test"`, count 1) and one
  `PendingSelfModelInformationEventSpec(target_population_id="pop_test", answer_kind="unknown", unknowns=["material.moon_resin.source"])`
  → `state.pending_self_model_information_events` has length 1; `entry["actor_id"]` equals the
  compiled entity's id; `entry["event"]` is an `InformationResponse` instance with
  `answer_kind == "unknown"`, `unknowns == ("material.moon_resin.source",)`, `facts == ()`,
  `suggested_leads == ()`.
- `test_compiler_pending_self_model_information_event_unmatched_population_is_skipped_with_warning`:
  unmatched `target_population_id` → `state.pending_self_model_information_events == []` and a
  warning recorded in `report["warnings"]`.
- `test_compiler_no_pending_self_model_information_events_declared_yields_empty_list`:
  `spec.pending_self_model_information_events == []` → same on `state`.
- Existing `test_compiler_minimal_world` and all `pending_information_responses`/
  `information_source_profiles` tests must still pass unmodified.

---

## Step 4 — Fix `self_model_phase.py`'s `events=[]` hardcoding

**File:** `src/cognition/self_model_phase.py`, `SelfModelUpdatePhase.apply()` (current lines 32-64)

**Current code (re-confirmed this session, unchanged from investigation):**
```python
    @staticmethod
    def apply(
        state: Any,  # AuthoritativeState
        update: Any,  # StateUpdate
    ) -> Any:  # StateUpdate
        new_entity_updates = dict(update.entity_updates)

        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            new_bundle = SelfModelUpdatePhase.run(
                entity=entity,
                state=state,
                events=[],
                tick=state.tick
            )
            ...
```

**Fix:** group the new compile-time-seeded events by `actor_id` once, before the loop, then pass
each entity's own events instead of `[]`:
```python
    @staticmethod
    def apply(
        state: Any,  # AuthoritativeState
        update: Any,  # StateUpdate
    ) -> Any:  # StateUpdate
        new_entity_updates = dict(update.entity_updates)

        # Group compile-time-seeded InformationResponse-shaped events by actor_id
        # (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B — third application of the compile-time-seed
        # pattern; see docs/guidelines/design_patterns.md Pattern 6).
        events_by_actor: Dict[int, List[Any]] = {}
        for entry in getattr(state, "pending_self_model_information_events", []):
            actor_id = entry.get("actor_id")
            event = entry.get("event")
            if actor_id is not None and event is not None:
                events_by_actor.setdefault(actor_id, []).append(event)

        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            new_bundle = SelfModelUpdatePhase.run(
                entity=entity,
                state=state,
                events=events_by_actor.get(entity_id, []),
                tick=state.tick
            )
            ...
```
No new imports needed — `Dict`/`List`/`Any` are already imported at the top of the file
(`from typing import List, Optional, Tuple, Dict, Any`, current line 12).

**Scope guard:** `SelfModelUpdatePhase.run()`'s own internal event-handling logic
(`self_model_phase.py:66-210`, `for event in events: if hasattr(event, "answer_kind"): ...`) is
**not** touched — it already correctly handles a non-empty `events` list (proven by
`tests/unit/cognition/test_phase2_self_model_phase.py`'s existing event-assimilation test using a
real `InformationResponse` instance directly). Only `.apply()`'s sourcing of `events` changes.

**Dependency:** requires Steps 1-3 (the new `AuthoritativeState` field must exist and be
populated). Independent of Step 5 (the `information_belief` pipeline-wiring fix) at the code level,
but Step 5 is required for this fix's effect to survive materialization whenever
`ENABLE_BELIEF_ASSIMILATION` is also on (Finding 4).

**Verification:** covered by Step 6's tests. Existing
`tests/unit/cognition/test_phase2_self_model_phase.py` tests call `SelfModelUpdatePhase.run()`
directly (not `.apply()`), so none of them exercise `.apply()`'s event-sourcing at all — they remain
unaffected and must still pass unmodified.

---

## Step 5 — Fix `information_belief`'s pipeline-wiring clobber (Finding 4)

**File:** `src/engine/pipeline.py`, line 152 (re-confirmed this session, unchanged from
investigation)

**Current code:**
```python
        update = run_phase("information_belief", update, lambda u: InformationBeliefPhase.apply(state, source_profiles, pending_resps), "ENABLE_BELIEF_ASSIMILATION")
```

**Fix — mirror the exact `u.merge(...)` shape already used by the 3 sibling phases in this same
file** (`faction_awareness`, line 181: `lambda u: u.merge(_SU_fa(faction_updates=...))`;
`diplomatic_transitions`, line 211: `lambda u: u.merge(_SU_dt(faction_updates=..., world_events_add=...))`;
`military_conflict`, line 221: `lambda u: u.merge(MilitaryConflictPhase.execute(state))`):
```python
        update = run_phase("information_belief", update, lambda u: u.merge(InformationBeliefPhase.apply(state, source_profiles, pending_resps)), "ENABLE_BELIEF_ASSIMILATION")
```

This is the smallest possible fix: one line, no signature change to `InformationBeliefPhase.apply()`
(it keeps returning a bare `StateUpdate`, exactly like `MilitaryConflictPhase.execute()`), zero
lines changed in `src/domains/information/phase.py`. `StateUpdate.merge()`
(`src/core/updates.py:946-950`, delegating to `merge_many`) correctly merges `entity_updates` per
entity via `EntityUpdate.merge()` (`src/core/updates.py:663-697`, confirmed this session by direct
read: `new_entity_updates[e_id] = new_entity_updates[e_id].merge(upd) if e_id in new_entity_updates else upd`,
`updates.py:1015-1016`) — two different entities' `EntityUpdate`s never collide; the same entity's
`self_model_bundle_set` "prefers the later non-None set" (`updates.py:694`), which is correct here
since `information_belief` runs strictly after `self_model` in `refine()`'s phase order and only
overwrites `self_model_bundle_set` for entities it actually processes (Branch A processing an
entity, or a hand-authored `self_model_bundle_set` inside Branch A's own per-entity assimilation
path) — entities `information_belief` does not touch keep `self_model`'s write intact via the
`else: ...upd` branch.

**Dependency:** independent of Steps 1-4 at the code level (this is a pre-existing pipeline-wiring
bug, not introduced by the compile-time plumbing), but required for Step 4's fix to be observable
whenever `ENABLE_BELIEF_ASSIMILATION` is also on — which is required for Branch B (living inside
`InformationBeliefPhase.apply()`) to fire at all. Blocks Step 6's Branch-B-reachability test and
Step 7's regression sweep (both require both flags ON simultaneously without clobbering).

**Verification:** covered by Step 6, plus a regression check that `tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts`
(the existing test exercising `ENABLE_BELIEF_ASSIMILATION=ON` alone, `ENABLE_SELF_MODEL_COGNITION`
untouched/OFF) still passes unmodified — this fix is a no-op whenever `self_model`'s phase-skip
branch returns `upd` unchanged (the `u` being merged is then `upd` itself contributing nothing new
beyond what `information_belief` computed, since `self_model`'s skip branch never wrote anything to
`upd` in the first place).

---

## Step 6 — Content: seed `urban_political`'s `pop_1` (NOT `pop_0`) with a
`pending_self_model_information_events` entry

**Reuse-vs-new determination (resolved with evidence — this is the concrete answer to the ticket's
Scope item 4 question):** `pop_0` already carries a `pending_information_responses` entry (Branch
A's seed, `data/worlds/urban_political/world.yaml:44-54`, subject `bandit_road_danger`,
`answer_kind: KNOWN_FACT`). Both `pending_information_responses` and (the new)
`pending_self_model_information_events` fire at the same tick (tick 0, the initial compiled state —
neither field is carried forward by `apply_generation()`, see Step 8's persistence decision below).
At tick 0, `self_model` (PP-02/03) runs **before** `information_belief` (PP-04) in `refine()`'s
phase order (`pipeline.py:143` vs. `pipeline.py:152`, confirmed this session). If `pop_0` were also
given a Step-1 event, `self_model_phase` would populate `pop_0.self_model.knowledge.unknowns` — but
then `information_belief` runs and, for `pop_0`, finds `resp_by_actor` already has an entry (Branch
A's seed) and takes the `if actor_resps:` branch (`phase.py:56-81`), which sets
`entity_updates[pop_0.id]` **before** the `if actor.id not in entity_updates:` guard on Branch B
(`phase.py:84`) is ever checked — so Branch B's `elif` would never execute for `pop_0`, no matter
how the merge-clobbering fix (Step 5) lands. **Reusing `pop_0` would make Branch B provably
unreachable for the seeded entity, defeating the ticket's Acceptance Criteria.** `pop_1` (the second
of `hero_adventurers`' three compiled population entries — `pop_0`, `pop_1`, `pop_2`, each `count:
1`, confirmed present in `data/worlds/urban_political/resolved/world.resolved.yaml:163-177`) has no
Branch A entry, so it falls straight through to Branch B's `elif` once its `self_model.knowledge.unknowns`
is populated. **Chosen actor: `pop_1`.**

**Chosen event content:**
```yaml
pending_self_model_information_events:
  - target_population_id: "pop_1"
    answer_kind: "unknown"
    unknowns:
      - "material.moon_resin.source"
    certainty: 0.0
    source_id: null
    cost_gold: 0
```
`answer_kind: "unknown"` (not `"known"`/`"partial"`) is chosen deliberately: `KnowledgeModelService.assimilate()`
(`knowledge_model.py:93-101`) only ever populates `unknowns` from the response's own `unknowns`
tuple, regardless of `answer_kind` — but `"unknown"` is the cleanest, most literal choice for
"nothing is known yet, this is a gap the entity is aware of," and produces no `facts` entry to
reason about in tests. Subject `"material.moon_resin.source"` is reused verbatim from the existing
in-repo example (`src/core/self_model.py:67`'s `UnknownFact.subject` docstring example and
`src/world/providers/information.py`'s own `GuideInformationProvider` partial-response example,
lines ~67-69) — thematically consistent, not a new invented vocabulary term.

**Branch B routing confirmed reachable with this exact content (traced this session):**
`InformationBeliefPhase.apply()`'s Branch B (`phase.py:84-105`) hardcodes
`InformationQuery(subject=first_unk.subject, kind="material_source")` (`phase.py:90`) regardless of
the original event's `answer_kind`/`query_kind` — so any populated `unknowns` entry routes as a
`material_source` query. `InformationQueryRouter.matches_scope()` (`router.py:44-50`) matches
`kind == "material_source"` against `"common_resource_sources" in scopes`. `urban_political`'s
existing `town_notice_board` profile (`world.yaml:28-35`) has
`knowledge_scopes: ["regional_danger", "common_resource_sources"]` and `cost_gold: 0` (within the
router's default `budget_max_gold=100`) — it is a valid, already-seeded candidate; **no new
`information_source_profiles` content is required.**

**Files:**
- `data/worlds/urban_political/world.yaml` (composition — hand-edited): add the
  `pending_self_model_information_events` block above, alongside the existing
  `pending_information_responses` block (lines 44-54).
- `data/worlds/urban_political/resolved/world.resolved.yaml` (regenerated, **not** hand-edited):
  ```bash
  python -m src.worldbuilding.cli resolve urban_political
  ```
  Diff-review: only the new `pending_self_model_information_events:` block (and incidental
  provenance/timestamp fields) should change — everything else byte-identical.

**Dependency:** requires Steps 1-5 complete, or the new YAML key is rejected
(`extra="forbid"` prior to Step 1) or silently unused/mis-resolved (prior to Step 2/3).

**Verification:**
- `test_urban_political_resolved_world_seeds_one_pending_self_model_information_event` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`, mirrors
  `test_urban_political_resolved_world_seeds_one_pending_information_response`, line 345): load the
  resolved YAML, compile with a fixed seed, assert `len(state.pending_self_model_information_events) == 1`,
  the entry's `actor_id` matches the compiled `pop_1` entity's id (cross-check via
  `state.entities[actor_id].properties["population_id"] == "pop_1"`), and the `event`'s
  `answer_kind`/`unknowns` match the content above exactly.
- `python -m src.worldbuilding.cli validate urban_political --strict` is **not** expected to exit
  0 — same pre-existing `[WORLD-UNEXPECTED-SECTION]` gap the FACTION/INFORMATION/
  INFORMATION-BELIEF-TRIGGER plans already documented for composition-level fields predating the
  `--strict` validator's section allowlist. Confirm this is the same pre-existing gap, not a new
  regression.

---

## Step 7 — Persistence decision: single-fire, not carried forward (explicit, per Pattern 6's
"known pitfall")

Per Pattern 6's explicit instruction ("decide explicitly... grep `src/engine/apply.py`'s final
`AuthoritativeState(...)` call for the new field's keyword"): **`pending_self_model_information_events`
is NOT added to `ApplyPath.apply_generation()`'s carry-forward logic.** This mirrors
`pending_information_responses`/`information_source_profiles` (neither is carried forward,
confirmed this session absent from `apply.py`), not `factions` (which is explicitly carried
forward). Rationale: this is a compile-time inbox, not a per-tick mutable record; a bounded,
single-fire assimilation at tick 0 is sufficient to satisfy this ticket's Acceptance Criteria
(`self_model.knowledge.unknowns` populated in at least one calibration scenario; Branch B reachable
once) and matches the exact precedent `INFRA-257`/`docs/guidelines/intentional_divergences.md` §2.23
already established for the sibling field. No code change to `src/engine/apply.py` is required or
intended.

**Verification:** a new test (see Step 8 item 2) explicitly confirms
`state.pending_self_model_information_events == []` from the first `apply_generation()` call
onward, mirroring `test_pending_information_response_fires_exactly_once_not_carried_forward`.

---

## Step 8 — Tests

**Files:** `tests/unit/cognition/test_phase2_self_model_phase.py`,
`tests/unit/worldbuilding/test_world_compiler.py`, `tests/unit/worldassembly/test_assembly.py`,
`tests/integration/domains/test_fused_loop.py` (or a new
`tests/integration/domains/information/test_self_model_belief_branch_b.py` if the existing file's
fixture style does not fit cleanly — confirm at implementation time which file already hosts the
`_create_state()`/`V2EntityBuilder` fixture pattern closest to this need; `test_fused_loop.py` is the
strongest existing precedent per Step 5/6's citations of `test_belief_assimilation_persists_facts`,
lines 167-217).

1. **Schema/compiler/resolver unit tests** — per Steps 1-3's Verification sections above (schema
   round-trip + `Literal` rejection test, compiler seeding/skip/empty tests, resolver
   passthrough/empty tests). All new, isolated, no pipeline involvement.

2. **`SelfModelUpdatePhase.apply()` sources real events from the new field, isolated from Finding 4
   (direct-pipeline test, `ENABLE_BELIEF_ASSIMILATION` OFF).** Mirrors
   `test_belief_assimilation_persists_facts`'s fixture style (`test_fused_loop.py:167-217`): build a
   `_create_state([actor])` with `entity.id` matching a hand-constructed
   `pending_self_model_information_events` entry (`{"actor_id": 1, "event": InformationResponse(answer_kind="unknown", unknowns=("material.moon_resin.source",))}`),
   set `state.feature_flags = {"ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON}` (leave
   `ENABLE_BELIEF_ASSIMILATION` unset/OFF — isolates Step 4's fix from Step 5's fix). Call
   `AuthoritativeApplyPipeline.refine(state, StateUpdate())` directly. Assert:
   - `refined.entity_updates[1].self_model_bundle_set.knowledge.unknowns["material.moon_resin.source"]`
     exists and is an `UnknownFact` with `reason == "provider_unknown"`.
   - A second, unrelated entity with no seeded event still gets a valid (possibly no-op/dirty-check-skipped)
     `self_model_bundle_set` — confirms the fix does not regress entities without a seeded event.
   - Apply to state: `next_state = ApplyPath.apply_generation(state, refined, next_tick=2)`; assert
     `next_state.entities[1].self_model.knowledge.unknowns["material.moon_resin.source"]` is present
     — proves durability across a tick boundary, not just an in-flight `EntityUpdate` (mirrors
     `test_belief_assimilation_persists_facts`'s own materialization check, lines 211-216).
   - `next_state.pending_self_model_information_events == []` (or, if `refine()`/`apply_generation()`
     never carried it in the first place, confirm it is simply absent/default on `next_state`) — the
     single-fire regression guard from Step 7.

3. **Finding-4-fix-proving test (required, per ticket AC): both flags ON simultaneously, self_model's
   write is NOT wiped.** Construct a state with **two** entities: entity A has a seeded
   `pending_self_model_information_events` entry (any subject, any actor without a Branch A pending
   response), entity B is unrelated (no seeded event of any kind — this is the regression-catching
   entity per the test plan's anti-drift guard, "must also assert on `entity_updates` for at least
   one *other*, unrelated entity"). Set
   `state.feature_flags = {"ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON, "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON}`.
   Call `AuthoritativeApplyPipeline.refine(state, StateUpdate())`. Assert:
   - Entity A's `self_model_bundle_set.knowledge.unknowns` is populated (Step 4's fix fired).
   - Entity B's `self_model_bundle_set` is present and non-None in `refined.entity_updates` (proves
     `information_belief`'s merge — Step 5's fix — did not wipe an entity it never touched).
   - Before Step 5's fix (documented as a "prior-behavior" assertion inside the test's docstring, not
     a separate xfail test — the fix is being landed in this same ticket, not deferred): this exact
     scenario is the one the investigation empirically confirmed wipes `refined.entity_updates` to
     `{}` entirely (investigation Finding 4, "2 entities, no pending responses/unknowns" reproduction).
     This test is the direct regression guard against Finding 4 ever being reintroduced.

4. **Branch B end-to-end reachability test (required, per ticket AC).** Load the actual compiled
   `urban_political` `AuthoritativeState` (via `WorldCompiler.compile()` against the resolved YAML —
   proves the full compile→pipeline path, not a hand-built state), with
   `feature_flags` overridden to `{"ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON}` (leave
   `ENABLE_BELIEF_ASSIMILATION` at its shipped `urban_political.yaml` value, `"ON"` — this is the
   real shipped combination for this one world, plus the test-scoped `ENABLE_SELF_MODEL_COGNITION`
   override per the ticket's Out-of-Scope guard). Call
   `AuthoritativeApplyPipeline.refine(state, StateUpdate())` for tick 0. Assert:
   - `pop_1`'s entity update has `self_model_bundle_set.knowledge.unknowns["material.moon_resin.source"]`
     populated (Step 4's fix, real compiled content).
   - `pop_1`'s entity update has `intent_results` containing the `ASK_INFORMATION`/`MOVE_TO`-style
     intent from `InformationIntentResolver.resolve()` (`phase.py:95`), and `property_updates`
     includes `last_routed_query_subject == "material.moon_resin.source"` and
     `last_routed_query_tick == 0` (`phase.py:101-104`) — proves Branch B actually fired, not just
     that `unknowns` was populated.
   - `pop_0`'s entity update (Branch A, unaffected by this ticket) still shows
     `last_assimilated_subject == "bandit_road_danger"` — confirms Branch A and Branch B coexist
     correctly in the same tick via the Step 5 merge fix, not just Branch B alone.

5. **Existing test suites unchanged.**
   `tests/unit/cognition/test_phase2_self_model_phase.py` (all existing tests — they call
   `SelfModelUpdatePhase.run()` directly, never `.apply()`, so are structurally unaffected by Step
   4's change) and `tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts`
   (exercises `ENABLE_BELIEF_ASSIMILATION` alone, `ENABLE_SELF_MODEL_COGNITION` untouched/OFF —
   Step 5's fix is a no-op here since `self_model`'s skip branch contributes nothing to merge) must
   pass unmodified.

**Scoped pytest commands:**
```bash
pytest tests/unit/cognition/ -v
pytest tests/unit/domains/information/ -v
pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ -v
pytest tests/integration/domains/test_fused_loop.py -v
pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -v
pytest tests/unit/cognition/ tests/unit/domains/information/ tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/integration/domains/test_fused_loop.py -v
```

---

## Step 9 — Regression sweep across all calibration worlds

**Calibration-world universe (resolved with evidence, this session):** `tests/simulation_quality/fixtures/grade_anchors.json`
tracks exactly 4 world families across all seed/tick variants: `dungeon_crawl`, `sandbox_world`,
`simq_routing_test`, `urban_political`. `data/worlds/` additionally contains
`frontier_extended`/`frontier_living_world`/`generated_frontier_3_42`/`highland_traverse`/
`swamp_border_world`/`wilderness_survival`, none of which appear in `grade_anchors.json` or have a
`config/simulation_quality/profiles/*.yaml` entry — these are not part of the calibration suite and
are out of this sweep's scope (consistent with the Branch A plan's own Step 10 universe). "All
calibration worlds" = these 4 families.

```bash
# Fix must be provably inert when ENABLE_SELF_MODEL_COGNITION stays at its shipped default (OFF)
# in every profile — confirm 0 unintended regressions across every scenario already in
# grade_anchors.json:
python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name urban_political

python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 42  --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 123 --name dungeon_crawl --profile dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 456 --name dungeon_crawl --profile dungeon_crawl

python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name sandbox_world
python3 tools/calibrate_simq.py --ticks 200  --seed 137 --name sandbox_world
python3 tools/calibrate_simq.py --ticks 200  --seed 999 --name sandbox_world
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name sandbox_world
python3 tools/calibrate_simq.py --ticks 2000 --seed 42  --name sandbox_world

python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name simq_routing_test --profile simq_routing_test
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name simq_routing_test --profile simq_routing_test
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name simq_routing_test --profile simq_routing_test

make evaluate --dry-run   # AC requires this to exit 0
```

**Expected outcome:** 0 unintended grade movement on every pillar/world/scenario, since
`ENABLE_SELF_MODEL_COGNITION` stays OFF in every shipped profile (`config/simulation_quality/profiles/*.yaml`
— re-confirm no profile sets it) and the new `pending_self_model_information_events` field is only
ever populated for `urban_political` (Step 6), and only observable when
`ENABLE_SELF_MODEL_COGNITION` is scoped ON — which no calibration run does. `urban_political`'s own
INFORMATION pillar (already `B`-grade per `INFRA-256`/`INFRA-257`) is expected to show **0** change
too — Branch A's already-shipped behavior does not change, and Branch B stays unreachable in the
real (unmodified) calibration profile since `ENABLE_SELF_MODEL_COGNITION` is not turned on there.

**Stop condition:** if any world/scenario shows unexpected grade movement, STOP and surface to a
human rather than expanding scope or tuning thresholds — mirrors the ticket's Out-of-Scope guard and
the Branch A plan's identical stop condition.

---

## Step 10 — Docs

1. **`docs/cognition/self_model_contract.md`** — accuracy check confirmed: "Dirty check" (lines
   69-76) and "Phase lifecycle" (lines 80-87) sections already describe the fixed behavior correctly
   ("No InformationResponse events arrived for this entity this tick" — true once Step 4 lands, was
   already vacuously true before since events was always `[]`). Add one clarifying sentence to the
   "Phase lifecycle" section naming the actual source of events post-fix, since neither doc
   currently says where events come from:
   ```markdown
   `SelfModelUpdatePhase.apply()` sources this tick's `events` from
   `AuthoritativeState.pending_self_model_information_events` (compile-time-seeded, filtered by
   `actor_id` — see `docs/parity_ledger/infrastructure.yaml::INFRA-259`), not a live event bus or
   provider call.
   ```
2. **`docs/cognition/README.md`** — same accuracy check: line 49-50 ("Step 1: Knowledge assimilation
   ... Only if InformationResponse events exist for this entity this tick") remains accurate
   verbatim; append one line after it citing the compile-time-seed source (same sentence as above,
   or a cross-reference to `self_model_contract.md`'s new sentence — avoid duplicating full prose in
   two places).
3. **`docs/guidelines/intentional_divergences.md`** — add a new entry (§2.24, appended directly
   after §2.23 at line 286, before the `---` separator at line 288), rationale class **Bounded**,
   documenting the identical single-fire mechanism for `pending_self_model_information_events`
   established in Step 7 above (mirror §2.23's structure: Subsystem, Old/New Behavior, Rationale,
   Verification test path, Note about calibration confirmation — though per Step 9, calibration runs
   do not exercise this path since `ENABLE_SELF_MODEL_COGNITION` stays OFF everywhere, so the "Note"
   subsection should say so explicitly rather than claim a `calibration_hits` measurement that
   cannot exist under the Out-of-Scope guard).
4. **Parity ledger — two new entries in `docs/parity_ledger/infrastructure.yaml`** (confirmed home:
   `infrastructure.yaml`, not `strategic_cognition.yaml` — re-confirmed this session by grepping both
   files: `infrastructure.yaml` already contains `INFRA-256`'s `support_boundary` explicitly naming
   "`SelfModelUpdatePhase.apply()` hardcodes `events=[]`" as the residual blocker for Branch B
   [`infrastructure.yaml:3064`], establishing this as the correct, already-established home for this
   exact fix; `strategic_cognition.yaml`'s only `self_model`-adjacent reference is an unrelated
   `UnknownFact` field note, not a Branch-B/events=[] discussion). **Confirmed next-free ID: `INFRA-259`**
   (highest existing ID in the file is `INFRA-258`, re-confirmed by direct grep this session, no
   gaps above it).
   - **`INFRA-259`** — the compile-time schema/compiler/resolver plumbing (Steps 1-4, 6-7):
     `pending_self_model_information_events` compile-time plumbing makes `SelfModelUpdatePhase.apply()`'s
     `events=[]` hardcoding fixed; `self_model.knowledge.unknowns` is populated for `urban_political`'s
     `pop_1` when `ENABLE_SELF_MODEL_COGNITION` is scoped ON (test-only override, never a shipped
     profile default). Cross-reference `INFRA-256`/`INFRA-257` and update their `support_boundary`
     text (see below). `status: verified`, `priority: P1`, `test_path` listing the new unit +
     direct-pipeline tests from Step 8.
   - **`INFRA-260`** — the `information_belief` pipeline-wiring merge fix (Step 5, Finding 4):
     `src/engine/pipeline.py`'s `information_belief` call site now wraps
     `InformationBeliefPhase.apply(...)` in `u.merge(...)`, matching `faction_awareness`/
     `diplomatic_transitions`/`military_conflict`'s established pattern; prior behavior silently
     replaced (not merged) the tick's prior `StateUpdate`, wiping any same-tick `self_model`
     contribution whenever `ENABLE_BELIEF_ASSIMILATION` was on. `status: verified`, `priority: P1`
     (this is the fix that makes Branch B durably reachable in combination with `INFRA-259`),
     `test_path` pointing at Step 8 item 3's fix-proving test. `divergence_note`: none needed — this
     is a straightforward bug fix, not an intentional behavior divergence.
   - **Update `INFRA-256`'s and `INFRA-257`'s `support_boundary` text**: both currently state "Branch
     B (`self_model.knowledge.unknowns`) remains unreachable... `SelfModelUpdatePhase.apply()`
     hardcodes `events=[]`" (`infrastructure.yaml:3037`, `3064`, `3086`, `3112`) — revise to state
     Branch B is now reachable (cross-referencing `INFRA-259`/`INFRA-260`) **only** when
     `ENABLE_SELF_MODEL_COGNITION` is explicitly turned on (still OFF in every shipped calibration
     profile) — do not overclaim unconditional reachability, per the investigation's own anti-drift
     hazard.
5. **`docs/simulation_quality/event_type_coverage.md`** — check whether `knowledge_fact_learned`/
   `knowledge_unknown_recorded` (the two `trace_events.py` events `SelfModelUpdatePhase.run()` emits,
   confirmed at `self_model_phase.py:110-118`, `124-131`) have existing rows; if so, confirm they
   remain accurate (still `calibration_hits == 0` under the shipped OFF default — this ticket does
   not change that measured fact, since `ENABLE_SELF_MODEL_COGNITION` is never turned on in a
   shipped profile). No row update needed unless an existing row makes a stronger claim than "0
   hits, flag off in every profile."

**Note:** `docs/REGISTRY.yaml` — if `make knowledge-index-update` is required per this repo's
Workflow Rule ("If any files under `docs/` were created or modified: run `make knowledge-index-update`"),
run it after Step 10's doc edits land, since `self_model_contract.md`, `README.md`, and
`intentional_divergences.md` are all under `docs/`.

---

## Cleanup (per Definition of Done)

- `rm -rf data/runs/* reports/release_proof/*` after Step 9's calibration sweep completes and any
  needed `quality_report.json`/anchor updates are captured.
- Stage `agent-monitoring/tools.jsonl` in the final commit (auto-updated by the workflow).

---

## Unresolved Questions

None. Every fork this session was resolved with direct evidence:
- **Fix location for Finding 4**: `src/engine/pipeline.py:152` (the call-site lambda), not inside
  `src/domains/information/phase.py` — confirmed by reading `InformationBeliefPhase.apply()`'s
  actual signature (no `update` parameter at all) and comparing against the 3 siblings' identical
  call-site-merge pattern in the same file.
- **New field vs. reuse of `pending_information_responses`**: a new field is required — confirmed by
  direct type/vocabulary comparison between `InformationResponse` (Step 1's consumer, lowercase,
  attribute-access) and the existing field's dict/uppercase shape (Branch A's consumer, item-access).
- **Reuse `pop_0` vs. seed a new entity for the Step-1 event**: `pop_1`, not `pop_0` — confirmed by
  tracing `InformationBeliefPhase.apply()`'s branch-selection order (`if actor_resps: ... elif ...:`)
  and showing `pop_0` would never reach the `elif` (Branch B) because Branch A's entry for `pop_0`
  always wins the `if` first.
- **Parity ledger home file**: `docs/parity_ledger/infrastructure.yaml`, not `strategic_cognition.yaml`
  — confirmed by grep: `infrastructure.yaml` already contains the exact residual-blocker language
  this ticket resolves (`INFRA-256`'s `support_boundary`, line 3064); `strategic_cognition.yaml` has
  no related discussion.
- **Next-free parity ledger ID**: `INFRA-259` (and `INFRA-260` for the second, adjacent fix) —
  confirmed by direct grep of all `INFRA-nnn` IDs in the file, highest is `INFRA-258`, no gaps.
- **Persistence (single-fire vs. carried-forward)**: single-fire, matching `pending_information_responses`/
  `information_source_profiles` precedent exactly — confirmed by grepping `src/engine/apply.py` for
  the new field's keyword (absent, by design, not added by this plan).

---

## Deviations (implementation session, 2026-07-04)

Steps 1-9 implemented exactly as specified above. Step 10 intentionally deferred to a separate
phase per this session's explicit instructions (not a deviation from the plan itself).

**New discovery not anticipated by this plan or its investigation (Finding 5):**
`EntityUpdate.self_model_bundle_set` is never materialized into durable `EntityState.self_model` by
`ApplyPath`. `src/engine/patches.py::extract_patches()` has no patch class reading
`update.self_model_bundle_set`, and `src/engine/apply.py:578`
(`changes.get("self_model", getattr(entity, "self_model", None))`) reads a `"self_model"` key that
nothing ever populates. Empirically confirmed this session: `refined.entity_updates[id]
.self_model_bundle_set.knowledge.unknowns` is correctly populated pre-materialization, but
`ApplyPath.apply_generation(...).entities[id].self_model.knowledge.unknowns` is empty afterward.
This is a **pre-existing, separate gap** affecting Branch A's already-shipped writes identically
(the existing `test_belief_assimilation_persists_facts` only ever asserted
`self_model.knowledge is not None`, never that its content changed — which is why this was never
caught). It is out of this ticket's Scope/Out-of-Scope (Steps 1-9 touch only event-sourcing
plumbing and the `information_belief` merge call site) and was **not** fixed here.

**Consequence for Step 8's test design:** the plan's Step 8 item 2 ("proves durability across a tick
boundary... `next_state.entities[1].self_model.knowledge.unknowns[...]` is present") and item 4
("real compiled `urban_political` state... `pop_1`'s entity update has `intent_results` containing
[a routed intent]... at tick 0") cannot be satisfied literally as written, given Finding 5 plus the
independent phase-order fact that `InformationBeliefPhase.apply()` reads the frozen `state`, not the
same-tick `update`, so self_model's write is never visible to `information_belief` within the same
`refine()` call regardless of Finding 5.

**Test design actually implemented** (`tests/integration/domains/test_fused_loop.py`), preserving
the plan's spirit (prove each fix's mechanism truthfully rather than assert a false end-to-end
claim):
- `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4` — Step 8 item 2,
  minus the now-provably-false durability assertion (replaced with an honest note + a weaker,
  true assertion, consistent with the existing `test_belief_assimilation_persists_facts` precedent).
- `test_information_belief_merge_preserves_self_model_writes_both_flags_on` — Step 8 item 3,
  implemented as specified; empirically verified the pre-fix `{}`-wipe by temporarily reverting
  `pipeline.py`'s fix during this session (then restoring it) rather than asserting it via docstring
  alone.
- `test_information_belief_branch_b_routes_query_when_unknown_precondition_met` — new test, not in
  the original plan: proves `InformationBeliefPhase`'s Branch B routing logic is reachable and
  coexists with the merge fix once its state-level precondition is met (a hand-built entity with
  `self_model.knowledge.unknowns` already present on `state`, plus a matching
  `information_source_profiles` entry). This isolates "is Branch B's routing logic itself correct"
  from "can self_model's same-tick write reach `state` in time" (Finding 5 + phase order).
- `test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist` — Step 8 item 4,
  using the real compiled `urban_political` resolved spec as specified, but asserting what is
  actually true: `pop_1`'s `self_model_bundle_set` is correctly populated with real compiled
  content, and `pop_0`'s Branch A assimilation fires correctly in the same tick (both survive the
  merge). The docstring documents honestly that Branch B's query-routing does not fire within this
  same tick 0 call, for the reasons above.

**Recommendation**: open a follow-up ticket to add `EntityUpdate.self_model_bundle_set`
materialization to `src/engine/apply.py`/`src/engine/patches.py` (a `SelfModelPatch` class,
analogous to the existing `StrategicPatch`/`SocialPatch` etc.) before Branch B (and, retroactively,
Branch A) can be considered durably reachable end-to-end via the real compile→pipeline→apply path.
