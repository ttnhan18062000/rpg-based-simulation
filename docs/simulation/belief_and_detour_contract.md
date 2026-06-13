---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Belief and Detour Contract

**Source:** `src/systems/strategic_systems/belief.py`, `src/systems/strategic_systems/detour.py`, `src/systems/strategic_systems/redirection.py`
**Related docs:** [intelligence_system_contract.md](intelligence_system_contract.md), [docs/specs/2026-05-27-belief-integration-design.md](../specs/2026-05-27-belief-integration-design.md) (design spec), [docs/strategy/bounded_cognition_contract.md](../strategy/bounded_cognition_contract.md)

---

## Purpose

Beliefs are an entity's uncertain claims about world state. Detours are temporary deviations from the primary project to resolve a blocker. Together they enable entities to act on incomplete information (belief) and adapt to obstacles (detour) without abandoning long-term goals.

---

## Belief System — `belief.py`

Compliance IDs: LEG-RPG-150, LEG-RPG-125

### Belief data model

```python
BeliefEntry:
    id: str
    subject: str          # what the belief is about (entity ID, region ID, item ID)
    claim: str            # the specific assertion
    certainty: float      # 0.0 to 1.0
    source: str           # 'observation' | 'rumor' | 'deduction'
    source_entity_id: Optional[int]
    created_tick: int
    last_refreshed_tick: int
    contradictions: int   # how many times contradicted
```

Beliefs coexist with `LeadState` (typed strategic markers) and `HypothesisState` (multi-belief inferences). A belief is the raw claim; a lead is the actionable pointer derived from it.

### Belief formation

| Source | Certainty | Lead certainty |
|---|---|---|
| Direct observation | 1.0 | PRECISE |
| Rumor (from another entity) | 0.3 | VAGUE |
| Deduction (inferred) | varies | APPROXIMATE |

`process_observation()` creates certainty=1.0 belief + PRECISE lead.
`process_rumor()` creates certainty=0.3 belief + VAGUE lead.

### Contradiction degradation (LEG-RPG-125)

When contradicting evidence arrives, `apply_contradiction(lead_id, evidence)` demotes both the lead and its associated belief:

Lead certainty demotion: PRECISE → APPROXIMATE → VAGUE → EXHAUSTED

Belief certainty: `certainty -= 0.3` per contradiction; `contradictions += 1`

Supporting hypotheses lose confidence: `confidence -= 0.2` per contradiction.

### Staleness decay (LEG-RPG-150)

`decay_stale_beliefs()` runs each strategic pass. Leads not refreshed within `stale_threshold` ticks (default: 50) lose certainty:
- APPROXIMATE → VAGUE
- VAGUE → EXHAUSTED
- PRECISE leads decay SLOWER (direct observations are more durable)
- EXHAUSTED leads are skipped (already dead)

### Routing effects

Beliefs affect routing indirectly: `BeliefCycleSystem.estimate_threat(region_id)` aggregates danger-related beliefs and leads to compute a float threat estimate. This estimate feeds the adventure domain's route scoring as a risk modifier.

### Design spec vs current implementation

The design spec (`docs/specs/2026-05-27-belief-integration-design.md`) proposed:
- Belief clustering (grouping related beliefs into compound hypotheses) — **partially implemented** via `HypothesisState`, but automatic clustering logic is not wired
- Social belief sharing (entities broadcast beliefs to nearby allies) — **not implemented**; only `process_rumor()` supports incoming rumors
- Belief-driven quest generation — **not implemented**; current implementation feeds threat estimation only

---

## Detour System — `detour.py`

Compliance IDs: STRAT-006, STRAT-008, STRAT-009, STRAT-204–STRAT-212

### What a detour is

A detour is a **temporary deviation** from the entity's primary project to pursue a lead that could resolve a blocker. The primary project is preserved (not replaced). After the detour resolves (or exhausts), the original project resumes.

Detours are **weaker than interruptions**: a strategic interruption replaces the current project; a detour pauses it and creates a temporary sub-objective.

### Trigger conditions

`DetourSuggestionSystem.suggest_detours()` generates detour candidates when:
1. There are **unresolved blockers** on the current project
2. There are **usable leads** that haven't been tested/failed 3+ times and aren't suppressed

Only leads with `certainty != EXHAUSTED` and `suppression_until_tick < current_tick` are considered.

### Detour scoring

```python
score = certainty_score(lead.certainty)  # PRECISE=1.0, APPROXIMATE=0.6, VAGUE=0.2
      + source_trust_bonus               # from SourceTrustEntry
      - distance_penalty                 # lead target far from current position
```

Results are limited to `CognitionProfile.detour_breadth` candidates.

### Project preservation

When a detour is accepted:
- Primary project status → PAUSED
- Detour objective added to `entity.strategic.objectives` with DETOUR kind
- `current_project_id` remains the primary project; a detour flag marks the active objective as a detour

### Duration and suppression

Leads that are tested and fail get `failure_count += 1`. After 3 failures, the lead is no longer usable for detours. `suppress_exhausted_leads()` marks leads with `suppression_until_tick` to prevent immediate retry.

`enforce_bandwidth()` prevents detour nesting beyond `CognitionProfile.detour_depth`.

### Resumption

After a detour objective completes (FULFILLED or EXHAUSTED), `StrategicIntelligenceSystem.resume_project()` restores the primary project to ACTIVE status.

---

## Redirection — `redirection.py`

`StrategicRedirectionSystem.enforce()` is a separate and stronger mechanism than detours. A redirection:
- Replaces the current project entirely (no preservation)
- Is applied by the engine when a governance rule or forced event overrides the entity's autonomous decision
- Example triggers: calamity event forcing evacuation, governance policy forcing a specific action

**Redirection vs detour:**
| Aspect | Detour | Redirection |
|---|---|---|
| Primary project | Paused, preserved | Replaced |
| Who triggers | Entity's own strategic evaluation | Engine governance rules |
| Resumption | Automatic after detour resolves | No automatic resumption |
| Strength | Weaker than interruption | Stronger than interruption |

---

## Mutation rules

All three systems return `StrategicUpdate` — they never mutate `AuthoritativeState` directly.

---

## Regression tests

- `tests/unit/test_belief_cycle.py` — decay, contradiction degradation, certainty thresholds
- `tests/unit/test_detour_suggestion.py` — blocker+lead pairing, scoring, bandwidth enforcement
- `tests/integration/test_detour_lifecycle.py` — full cycle: blocker → detour → resolution → project resume

---

## Extension rules

1. To add a new belief source: add a formation method following `process_observation()` / `process_rumor()` patterns. Always produce both a `BeliefEntry` and a `LeadState`.
2. To implement social belief sharing (currently missing): add a `broadcast_belief()` method that produces a `SocialUpdate` with the belief content. Do not add broadcast logic to `BeliefCycleSystem` directly — it must stay a pure decision system.
3. To add a new detour trigger: add a condition in `DetourSuggestionSystem.suggest_detours()`. Ensure new triggers respect `detour_breadth` limits.
4. Never call `StrategicRedirectionSystem.enforce()` from domain code — redirections are governance-layer operations only.
