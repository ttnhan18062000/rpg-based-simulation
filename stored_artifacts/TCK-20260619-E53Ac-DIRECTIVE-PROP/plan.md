# Plan — TCK-20260619-E53Ac-DIRECTIVE-PROP (v2 — post-review)

## Architecture Changes from Review

### ISSUE-1/2: Remove cadence guard from faction_decision
`faction_decision` must run every tick (no cadence gate) to guarantee determinism.
`FactionDecisionPhase.execute()` is a pure stateless computation — safe to run every tick.
The cadence guard was an optimization for E53Ab where directives weren't consumed downstream;
now they're an input to scoring, so they must be computed from the same state deterministically.

### ISSUE-3: Explicit typed params (not context dict)
Add `faction_directives` and `factions` as explicit keyword params to `AdventureDecisionPhase.apply()`.

### ISSUE-4: Extract directive-kind constants to shared module
Create `src/engine/faction_constants.py` with `DEFEND_BORDER`, `TRADE_ROUTE`, `COMMISSION_QUEST`.
Update `faction_decision.py` to import from there. Import from there in `scoring.py` at module level
(no lazy import). Eliminates circular import risk.

### ISSUE-5/6: Score magnitudes are ticket-mandated; RouteFamily proxy is intentional
+2.0/+1.5/+3.0 urgency boosts are explicitly specified in the ticket. Document as new behavior in
`04_strategic_cognition.md`. HUNT_WEAK_ENEMY is the correct proxy (no PATROL enum exists) — document.

### ISSUE-7: Pass state.factions directly
FactionState is a frozen dataclass; ReadOnlyDict is safe to iterate. No dict() copy needed.

---

## Step 1: Create src/engine/faction_constants.py
```python
DEFEND_BORDER = "DEFEND_BORDER"
TRADE_ROUTE = "TRADE_ROUTE"
COMMISSION_QUEST = "COMMISSION_QUEST"
```

## Step 2: Update src/engine/faction_decision.py
Replace module-level constant definitions with imports from faction_constants.py.

## Step 3: Move faction_decision block before adventure_decision in pipeline.py
Remove cadence guard. Always compute before adventure_decision:
```python
# --- Enhanced RPG Phase 8b: Faction Decision ---
t_start = time.perf_counter_ns()
from src.engine.faction_decision import FactionDecisionPhase
faction_directives: list = FactionDecisionPhase.execute(state, policy=None)
costs["faction_decision"] = (time.perf_counter_ns() - t_start) / 1e6

# --- Enhanced RPG Phase 3: Adventure Routing ---
t_start = time.perf_counter_ns()
from src.domains.adventure.phase import AdventureDecisionPhase
update = run_phase(
    "adventure_decision", update,
    lambda u: AdventureDecisionPhase.apply(
        state,
        faction_directives=faction_directives,
        factions=state.factions,
    ),
    "ENABLE_ADVENTURE_ROUTING",
)
costs["adventure_decision"] = (time.perf_counter_ns() - t_start) / 1e6
```

## Step 4: Update AdventureDecisionPhase.apply()
Add explicit typed keyword params:
```python
@staticmethod
def apply(
    state: AuthoritativeState,
    context: Optional[dict] = None,
    trace_writer: Optional[Any] = None,
    faction_directives: Optional[list] = None,
    factions: Optional[Any] = None,
) -> StateUpdate:
```
Pass through to decide():
```python
result = AdventureDecisionService.decide(
    hero, candidates, tick=tick,
    resource_nodes=state.resource_nodes,
    faction_directives=faction_directives,
    factions=factions,
)
```

## Step 5: Update AdventureDecisionService.decide()
Add optional params, pass to scorer:
```python
def decide(
    entity: EntityState,
    candidates: List[AdventureRouteOption],
    tick: int = 0,
    resource_nodes: Optional[Dict[int, ResourceNodeState]] = None,
    faction_directives: Optional[list] = None,
    factions: Optional[Any] = None,
) -> AdventureDecisionResult:
    ...
    scored = AdventureRouteScorer.score(
        entity, cand,
        resource_nodes=resource_nodes,
        faction_directives=faction_directives,
        factions=factions,
    )
```

## Step 6: Update AdventureRouteScorer.score()
1. Add top-level import: `from src.engine.faction_constants import DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST`
2. Add TYPE_CHECKING import for FactionDirective
3. Add params: `faction_directives: Optional[list] = None, factions: Optional[Any] = None`
4. Insert scoring block after urgency calculation (section 2):
```python
# ── 2b. Faction Directive Urgency Adjustments ─────────────────────────────
if faction_directives is not None:
    from src.core.enums import EntityRole as _ER
    if entity.identity.role == _ER.GUARD and route.family == RouteFamily.HUNT_WEAK_ENEMY:
        if any(d.directive_kind == DEFEND_BORDER for d in faction_directives):
            urgency += 2.0
    if (entity.identity.role == _ER.SHOPKEEPER
            and route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD)):
        if factions is not None and any(
            "allied" in fs.diplomatic_relations.values() for fs in factions.values()
        ):
            urgency += 1.5
    if entity.identity.role == _ER.HERO and route.family == RouteFamily.QUEST_OPPORTUNITY:
        if any(d.directive_kind == COMMISSION_QUEST for d in faction_directives):
            urgency += 3.0
```

## Step 7: Create docs/systems/faction_contract.md

## Step 8: Update docs/mechanics/04_strategic_cognition.md
Add "Faction Directive Scoring" subsection documenting:
- +2.0 urgency for GUARD/HUNT_WEAK_ENEMY when DEFEND_BORDER directive active
- +1.5 urgency for SHOPKEEPER/trade-routes when any faction has "allied" diplomatic_relations
- +3.0 urgency for HERO/QUEST_OPPORTUNITY when COMMISSION_QUEST directive active
- HUNT_WEAK_ENEMY as patrol proxy (no PATROL family exists)

## Step 9: Update docs/parity_ledger/strategic_cognition.yaml
Add FACTION-DIR-001 with status=verified.

## Step 10: Write tests
`tests/unit/faction/test_faction_directive_propagation.py` — 8 tests per test plan.

## Unresolved Questions
All resolved above.
