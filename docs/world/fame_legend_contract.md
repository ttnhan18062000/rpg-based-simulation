---
status: authoritative
layer: world
authority: P1
audience: agent
last_verified: 2026-09-05
---

# Fame & Legend Contract

**Status**: AUTHORITATIVE — TCK-20260905-FAME-DERIVER-LEGEND-FACT complete;
TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING (2026-09-07) adds the first live consumer.
**Ticket**: TCK-20260905-FAME-DERIVER-LEGEND-FACT (idea 57, "The Living Legend Feedback Loop").

---

## Purpose

The Living Legend Fame system tracks how much Chronicle-recorded fame a specific subject
(entity/faction/node id) has accumulated, and exposes a lazily-computed, threshold-gated
`LegendFact` once that fame is significant enough to be "a living legend." It is a direct
structural sibling of the Culture/Myth Drift system (`docs/world/culture_drift_contract.md`) and
the Chronicle Fidelity Drift system (`docs/world/chronicle_fidelity_contract.md`) — same 3-layer
Deriver/Model/Exporter-Importer pattern, same `ChronicleHierarchy` substrate, same
episode-boundary cadence — but keyed per-subject rather than per-region or per-event.

Fame state persists across episodes in `CampaignState.entity_fame`. `LegendFact` itself is
**not** durable — it is a lazy read-model reconstructed at query time from `FameCarryForward`.
It now has a real live consumer via route-bias scoring — see "Live Consumer: Route-Bias Scoring"
below — though perception/motivation-specific consumers remain unwired.

---

## FameState Model

Defined in `src/domains/fame/model.py`.

```
FameState(frozen=True, slots=True)
  fame: float — 0.0-1.0; 0.0 = no accumulated fame yet

FameCarryForward(frozen=True, slots=True)
  subject_id:      str            — the NarrativeLedgerEntry.subject_id this snapshot describes
  fame:            FameState
  derived_episode: int            — episode in which this snapshot was last derived
```

`fame` defaults to `0.0`. Clamped to `[0.0, 1.0]` by derivation.
Stored in `CampaignState.entity_fame: Dict[str, FameCarryForward]` (str keys).

Module import constraint: MUST NOT import from `src.engine` or `src.core.state` at module level
— same constraint `CultureState`/`FidelityState` uphold, enforced by
`tests/architecture/test_fame_legend_fact_distinctness.py`.

---

## Derivation

### Source

`FameDeriver.derive(hierarchy, entity_names=None) -> Dict[str, FameState]`

Defined in `src/domains/fame/deriver.py`. Pure/stateless — no durable state, no engine imports.
Consumes `hierarchy.events` (chronicle-worthy `NarrativeLedgerEntry` objects).

### Event Rule (Option B)

```
quest_completed                                   -> fame[subject_id] += entry.significance
entity_death, payload["entity_role"] == "HERO"    -> fame[subject_id] += entry.significance
```

No other event types contribute. Entries with a falsy `subject_id` do not accumulate fame and are
excluded from the result (fame is per-entity; an unattributed event has no entity to credit).

Normalisation: `fame = min(1.0, raw_sum / NORMALISE_DENOMINATOR)`, `NORMALISE_DENOMINATOR = 3.0`
— a fresh module-local constant, independent of `CultureDeriver`'s identically-valued constant.

### Keying

Per-subject, via `NarrativeLedgerEntry.subject_id` — deliberately distinct from
`FidelityCarryForward`'s per-event `entry_id` keying, to avoid any key collision.

### Episode-Boundary Wiring

`FameExporter.export(campaign_state, hierarchy, episode_index, entity_names=None)` is called from
`CampaignOrchestrator._advance_state()` immediately alongside `CultureDriftExporter.export()` and
`FidelityExporter.export()`, consuming the exact same
`ChronicleGrouper().group(list(self._state.narrative_ledger))` result — never a separately
(re)computed hierarchy.

Existing entries for subjects not observed in the current episode's hierarchy persist unchanged.

---

## LegendFact — Lazy, Non-Durable Read-Model

Defined in `src/domains/fame/legend.py`.

```
FAME_THRESHOLD: float = 0.5   # anchored to CHRONICLE_THRESHOLD, src/domains/chronicle/significance.py

LegendFact(frozen=True, slots=True)
  subject_id:  str
  fame:        float               — plain snapshot, not a live FameState reference
  entity_name: Optional[str] = None
```

`LegendFactService.for_entity(campaign_state, subject_id, entity_name=None) -> Optional[LegendFact]`
calls `FameImporter.get_fame(...)` and returns `None` if no `FameState` exists or `.fame <
FAME_THRESHOLD`; otherwise constructs and returns a `LegendFact`. This is a **lazy, query-time**
construction — there is no `CampaignState.legend_facts` field, and `LegendFact` is never persisted.
It is fully and deterministically reconstructible from `FameCarryForward` (the actual durable
record), so per the Durable State Rule it needs no second persisted record of its own.

`LegendFactService.to_world_signal(fact, position=(0.0, 0.0)) -> WorldSignal` wraps a `LegendFact`
as a `WorldSignal(kind="legend_fact", base_relevance=fact.fame, danger_level=0.0, is_novel=False)`
for perception discoverability. `position` is an explicit parameter (default `(0.0, 0.0)`) because
fame has no location concept of its own.

### Distinctness from `LEGENDARY_ARRIVAL`

`LegendFact` is never confused with the pre-existing, unrelated `LegendaryArrivalEvent`/
`LEGENDARY_ARRIVAL` faction-reputation consequence event
(`src/systems/social_systems/consequence_events.py`, `src/observability/events.py`), which reads
`CampaignState.social_memories[...].faction_reputation` — a structurally distinct mechanism.
`LegendFact`'s only real input is `FameImporter.get_fame(...)`. Enforced by
`tests/architecture/test_fame_legend_fact_distinctness.py`.

---

## Live Consumer: Route-Bias Scoring (TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING, 2026-09-07)

As of this ticket, `LegendFactService.for_entity()` has a real, live per-episode call site:
`CampaignOrchestrator._build_initial_state()` snapshots `CampaignState.entity_fame` into
`AuthoritativeState.entity_legend_facts: Dict[str, LegendFact]` once per episode (subjects below
`FAME_THRESHOLD` are excluded, per `for_entity()`'s own gate). `AdventureGoalScorer.score()`
(`src/ai/goals/adventure_scorer.py`) resolves the scoring entity's own bridged `LegendFact` via
`state.entity_legend_facts.get(str(entity.id))` and threads it through
`AdventureDecisionService.decide()` into `AdventureRouteScorer.score()`
(`src/domains/adventure/scoring.py`), which adds `legend_fact.fame * 0.30` to `personality_bias`
for `QUEST_OPPORTUNITY` routes — see `docs/mechanics/04_strategic_cognition.md` §6.4 "Living
Legend branch" for the full formula and `docs/parity_ledger/strategic_cognition.yaml` STRAT-227
for the parity citation. This bypasses `MotivationBiasService`/`DoctrineResolver` entirely
(confirmed dead legacy code, `docs/guidelines/intentional_divergences.md` §2.53) — the same
integration point idea 56/57's own Culture Drift signal already uses.

**Still not wired, disclosed not fixed by this ticket:**
- No live pipeline phase constructs `PerceptionUpdatePhase` (unchanged, zero call sites) —
  `LegendFactService.to_world_signal()` remains unconsumed; discoverability stays verified only at
  the `PerceptionFilterService.filter()` service level (`"legend_fact"` lands in the existing
  catch-all `perceived_opportunities` branch), not through a real per-tick perception pipeline call.
- No live call site exists for `MotivationBiasService.compute_bias_multiplier()` (unchanged,
  zero call sites outside its own module) — confirmed-dead, not revived (§2.53).
- `src/ai/coming_of_age.py`'s `_CANDIDATE_ROLES` is unchanged — no `ADVENTURER`/`HERO` bias exists.
- The bridge only populates for entities with an alive `EntityCarryForward` (episode N>0
  carry-forward path) — a fresh episode-0 `_build_initial_state()` early-return still yields a bare
  `AuthoritativeState()` with empty `entity_legend_facts`, matching `region_culture_states`'s own
  pre-existing episode-0 gap (out of this ticket's own scope to fix).

---

## Acceptance Signal

> `FameDeriver.derive()` on a hierarchy containing a `quest_completed` entry and a HERO
> `entity_death` entry for two different subject_ids produces two distinct non-zero `FameState`
> entries.

Test: `tests/unit/domains/fame/test_fame_deriver.py`
→ `test_fame_deriver_attributes_two_subjects_distinctly`

> A subject whose fame crosses `FAME_THRESHOLD` produces a `LegendFact` discoverable via
> `PerceptionFilterService.filter()`, while one below threshold produces none.

Test: `tests/unit/domains/fame/test_legend_fact.py`,
`tests/unit/domains/perception/test_legend_fact_discoverability.py`

Determinism: `FameDeriver.derive()` called twice with the same `ChronicleHierarchy` input produces
byte-identical output.

Test: `tests/unit/domains/fame/test_fame_deriver.py`
→ `test_fame_deriver_is_deterministic_byte_identical`

> A subject with a bridged `LegendFact` produces a measurably higher `AdventureRouteScorer.score()`
> result for a `QUEST_OPPORTUNITY` route than the same route scored without one, through the real
> `AdventureGoalScorer.score()` → `AdventureDecisionService.decide()` → `AdventureRouteScorer.score()`
> pipeline — not a hand-called pure function.

Test: `tests/unit/domains/adventure/test_legend_fact_route_bias.py`,
`tests/unit/ai/goals/test_adventure_goal_scorer.py`,
`tests/unit/domains/campaigns/test_fame_wiring.py`

---

## Integration Points

| Component | File | Role |
|---|---|---|
| `FameState` | `src/domains/fame/model.py` | Data model |
| `FameCarryForward` | `src/domains/fame/model.py` | Per-subject carry-forward |
| `FameDeriver` | `src/domains/fame/deriver.py` | ChronicleHierarchy → FameState |
| `FameExporter` | `src/domains/fame/exporter.py` | Episode-end persistence hook |
| `FameImporter` | `src/domains/fame/exporter.py` | Thin lookup (subject_id → FameState); live caller: `LegendFactService.for_entity()` |
| `LegendFact` | `src/domains/fame/legend.py` | Lazy, non-durable read-model above `FAME_THRESHOLD` |
| `LegendFactService` | `src/domains/fame/legend.py` | Query-time construction + `WorldSignal` conversion; called once per episode by `CampaignOrchestrator._build_initial_state()` |
| `CampaignState.entity_fame` | `src/domains/campaigns/state.py` | Cross-episode persistence |
| `CampaignOrchestrator._advance_state()` | `src/domains/campaigns/orchestrator.py` | Episode-boundary wiring, alongside `CultureDriftExporter`/`FidelityExporter` |
| `AuthoritativeState.entity_legend_facts` | `src/core/state.py` | Per-tick-reachable snapshot, populated once per episode by `CampaignOrchestrator._build_initial_state()` |
| `AdventureGoalScorer.score()` | `src/ai/goals/adventure_scorer.py` | Resolves the entity's own bridged `LegendFact` and threads it into `AdventureDecisionService.decide()` |
| `AdventureRouteScorer.score()` | `src/domains/adventure/scoring.py` | Living Legend `personality_bias` branch (§6.4 of `docs/mechanics/04_strategic_cognition.md`) |

---

## Parity Ledger References

| ID | Description |
|---|---|
| WORLD-FAME-001 | FameDeriver's Option B derivation rule and episode-boundary wiring match this contract |
| WORLD-FAME-002 | Determinism guarantee, CampaignState serialization round-trip, and LegendFact threshold-gating |
| STRAT-227 (`docs/parity_ledger/strategic_cognition.yaml`) | Living Legend `personality_bias` branch formula/weight in `AdventureRouteScorer.score()` |
