---
status: authoritative
layer: world
authority: P1
audience: agent
last_verified: 2026-09-05
---

# Chronicle Fidelity Contract

**Status**: AUTHORITATIVE — TCK-20260905-CHRONICLE-FIDELITY-DRIFT complete.
**Ticket**: TCK-20260905-CHRONICLE-FIDELITY-DRIFT (idea 62, "Generations Misremember").

---

## Purpose

The Chronicle Fidelity Drift system tracks how far a specific recorded event's remembered
accuracy has degraded, purely as a function of Era-distance from the current Era. It is a direct
structural sibling of the Culture/Myth Drift system (`docs/world/culture_drift_contract.md`) —
same 3-layer Deriver/Model/Exporter-Importer pattern, same `ChronicleHierarchy` substrate, same
episode-boundary cadence — but keyed per-event rather than per-region, and with no accumulated
axis semantics.

Fidelity state persists across episodes in `CampaignState.historical_drift`. As of
`TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (2026-09-07) this has a real live consumer via
`AdventureRouteScorer.score()`'s `personality_bias` mechanism. See "Live Consumer" below.

---

## FidelityState Model

Defined in `src/domains/fidelity/model.py`.

```
FidelityState(frozen=True, slots=True)
  fidelity: float — 0.0-1.0; 1.0 = fully accurate (just recorded / current Era)

FidelityCarryForward(frozen=True, slots=True)
  entry_id:        str            — the NarrativeLedgerEntry.entry_id this snapshot describes
  fidelity:        FidelityState
  derived_episode: int            — episode in which this snapshot was last derived
```

`fidelity` defaults to `1.0`. Clamped to `[0.0, 1.0]` by derivation.
Stored in `CampaignState.historical_drift: Dict[str, FidelityCarryForward]` (str keys).

Module import constraint: MUST NOT import from `src.engine` or `src.core.state` at module level
— same constraint `CultureState`/`CultureCarryForward` uphold, enforced by
`tests/architecture/test_fidelity_write_paths.py`.

---

## Derivation

### Source

`FidelityDeriver.derive(hierarchy) -> Dict[str, FidelityState]`

Defined in `src/domains/fidelity/deriver.py`. Pure/stateless — no durable state, no engine
imports. Consumes `hierarchy.events` and `hierarchy.eras` (chronicle-worthy `NarrativeLedgerEntry`
objects and their Era grouping).

### Era-Distance Rule

Era membership is resolved by walking `hierarchy.eras` → `Era.episodes` → `Episode.index` to
build an `episode_index -> era_ordinal` map, **never** by `episode // ERA_EPISODE_MIN`
arithmetic — that computation silently diverges from the real era membership whenever any
episode in the campaign has zero chronicle-worthy events, because `Era.episodes` batches only the
already-filtered episode list (`ChronicleGrouper._group_eras()`), not raw episode-index values.

```
era_distance = current_era_ordinal - event_era_ordinal
fidelity = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)
FIDELITY_DECAY_PER_ERA = 0.2
```

`current_era_ordinal` is `hierarchy.eras[-1].ordinal` — the highest ordinal, safe without a
`max()` scan since `ChronicleGrouper._group_eras()` appends eras in ascending ordinal order
starting at 0.

Same-era events (`era_distance == 0`) always resolve to `fidelity = 1.0`.

### Keying

Per-event, via `NarrativeLedgerEntry.entry_id` (deterministic, globally unique dedup key, format
`"{episode}:{tick}:{event_type}:{subject_id}"`). Legacy records with `entry_id == ""` reconstruct
the same deterministic format from `entry.episode`/`entry.tick`/`entry.event_type`/
`entry.subject_id`, avoiding a silent key collision on an empty string.

This is deliberately per-event rather than per-region or per-subject, to avoid any key collision
with idea 57's planned `entity_fame: Dict[str, FameCarryForward]` (keyed by `subject_id`), and to
match the design intent — a specific recorded event's story degrading, not a region- or
subject-level aggregate.

### Episode-Boundary Wiring

`FidelityExporter.export(campaign_state, hierarchy, episode_index)` is called from
`CampaignOrchestrator._advance_state()` immediately alongside `CultureDriftExporter.export()`,
consuming the exact same `ChronicleGrouper().group(list(self._state.narrative_ledger))` result —
never a separately (re)computed hierarchy.

Existing entries for events not observed in the current episode's hierarchy persist unchanged.

---

## Live Consumer

As of `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (2026-09-07): `CampaignOrchestrator.
_build_initial_state()` snapshots `historical_drift` into `AuthoritativeState.event_fidelity`
(`Dict[str, float]`, entry_id → fidelity scalar only — not the full `FidelityCarryForward`
record), carried forward every tick by `ApplyPath.apply_generation()`. `AdventureGoalScorer.
score()` threads it into `AdventureRouteScorer.score()`'s Belief Institution `personality_bias`
branch (see `docs/world/belief_institution_contract.md`), which scales a belief institution's own
`belief_strength` contribution by the matching `origin_event_id`'s current fidelity — a belief
formed around a heavily-mythologized/decayed-fidelity event carries less real-history weight than
one still close to the original record. `FidelityImporter.get_fidelity()` itself
(`src/domains/fidelity/exporter.py`) remains unused by this wiring (the bridge reads
`historical_drift` directly, matching `region_culture_states`/`entity_legend_facts`'s own
established bridge pattern) — it stays available as a direct lookup helper for any future
per-entry consumer.

---

## Acceptance Signal

> Given a `ChronicleHierarchy` with events spanning 2 or more Eras, `FidelityDeriver.derive()`
> produces a fidelity value for an event that is strictly lower the further that event's Era is
> from the current Era.

Test: `tests/unit/domains/chronicle/test_fidelity_deriver.py`
→ `test_fidelity_lowers_with_era_distance`

Determinism: `FidelityDeriver.derive()` called twice with the same `ChronicleHierarchy` input
produces byte-identical output.

Test: `tests/unit/domains/chronicle/test_fidelity_deriver.py`
→ `test_fidelity_derive_is_deterministic_byte_identical`

---

## Integration Points

| Component | File | Role |
|---|---|---|
| `FidelityState` | `src/domains/fidelity/model.py` | Data model |
| `FidelityCarryForward` | `src/domains/fidelity/model.py` | Per-event carry-forward |
| `FidelityDeriver` | `src/domains/fidelity/deriver.py` | ChronicleHierarchy → FidelityState |
| `FidelityExporter` | `src/domains/fidelity/exporter.py` | Episode-end persistence hook |
| `FidelityImporter` | `src/domains/fidelity/exporter.py` | Thin lookup (entry_id → FidelityState); unused by the live wiring, available for future per-entry consumers |
| `CampaignState.historical_drift` | `src/domains/campaigns/state.py` | Cross-episode persistence |
| `CampaignOrchestrator._advance_state()` | `src/domains/campaigns/orchestrator.py` | Episode-boundary wiring, alongside `CultureDriftExporter.export()` |
| `AuthoritativeState.event_fidelity` | `src/core/state.py` | Per-tick bridged snapshot (entry_id → fidelity scalar), populated by `CampaignOrchestrator._build_initial_state()` |
| `AdventureRouteScorer.score()` | `src/domains/adventure/scoring.py` | Live consumer — scales the Belief Institution `personality_bias` branch |

---

## Parity Ledger References

| ID | Description |
|---|---|
| WORLD-FIDELITY-001 | FidelityDeriver's era-distance derivation and episode-boundary wiring match this contract |
| WORLD-FIDELITY-002 | Determinism guarantee and CampaignState serialization round-trip |
