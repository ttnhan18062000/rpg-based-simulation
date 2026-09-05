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

Fidelity state persists across episodes in `CampaignState.historical_drift`. This ships with
**no live consumer yet**: idea 63 ("Belief Grows Around Real History") is the intended eventual
reader, not yet built. See "No Live Consumer" below.

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

## No Live Consumer

`FidelityImporter.get_fidelity(campaign_state, entry_id) -> Optional[FidelityState]` is a thin,
`None`-safe lookup helper defined in `src/domains/fidelity/exporter.py`. It has **no live call
site** as of this ticket — idea 63 ("Belief Grows Around Real History") is the intended eventual
reader, and possibly future feud/national-myth mechanics. This is a disclosed, accepted gap
(matching the sibling `TCK-20260904-LINEAGE-DEATH-DISPATCH`'s own write-no-read disclosure
pattern), not a hidden incompleteness.

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
| `FidelityImporter` | `src/domains/fidelity/exporter.py` | Thin lookup (entry_id → FidelityState); no live caller yet |
| `CampaignState.historical_drift` | `src/domains/campaigns/state.py` | Cross-episode persistence |
| `CampaignOrchestrator._advance_state()` | `src/domains/campaigns/orchestrator.py` | Episode-boundary wiring, alongside `CultureDriftExporter.export()` |

---

## Parity Ledger References

| ID | Description |
|---|---|
| WORLD-FIDELITY-001 | FidelityDeriver's era-distance derivation and episode-boundary wiring match this contract |
| WORLD-FIDELITY-002 | Determinism guarantee and CampaignState serialization round-trip |
