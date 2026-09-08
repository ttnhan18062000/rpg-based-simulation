---
status: authoritative
layer: world
authority: P1
audience: agent
last_verified: 2026-09-07
---

# Culture Drift Contract

**Status**: AUTHORITATIVE — E62A–E62C complete.
**Tickets**: E62A (CultureState model), E62B (CultureDeriver + Exporter/Importer), E62C (CulturalBiasApplicator + MotivationBiasService extension).

---

## Purpose

The Culture/Myth Drift system tracks region-level cultural identity derived from
accumulated narrative history. Over long campaigns, regional cultures develop distinct
values driven by their history of calamities, hero deaths, resource crises, and wars.

Cultural state persists across episodes in `CampaignState.region_cultures` and
produces measurable differences in entity motivation scoring (per-region, transient) —
true today in test coverage (`test_two_regions_diverge_after_5_episodes`), and, as of
`TCK-20260904-SETTLEMENT-CULTURE-READ`, also true via a real read-side production consumer
(see Integration Points). It is not yet true via any per-tick in-episode entity-decision
path: `MotivationBiasService.compute_bias_multiplier()` remains uncalled in production.

---

## CultureState Model (E62A)

Defined in `src/domains/culture/model.py`.

```
CultureState(frozen=True, slots=True)
  fatalism:                   float   — 0.0–1.0; calamity + high-trauma history
  hero_veneration:            float   — 0.0–1.0; HERO entity deaths of high significance
  resource_scarcity_memory:   float   — 0.0–1.0; INFLATION_SPIRAL + sustained depletion
  faction_conflict_exposure:  float   — 0.0–1.0; war_declared + territory_transferred + faction_destroyed

CultureCarryForward(frozen=True, slots=True)
  region_id:       str
  culture:         CultureState
  derived_episode: int   — episode in which this snapshot was last derived
```

All axes default to 0.0 (no cultural signal). Clamped to [0.0, 1.0] by derivation.
Stored in `CampaignState.region_cultures: Dict[str, CultureCarryForward]` (str keys).

---

## Derivation (E62B)

### Source

`CultureDeriver.derive(hierarchy, entity_names=None) -> Dict[str, CultureState]`

Defined in `src/domains/culture/deriver.py`. Pure/stateless — no durable state.
Consumes `ChronicleHierarchy.events` (chronicle-worthy NarrativeLedgerEntry objects).

### Axis Rules

| Event type | Axis incremented | Condition |
|---|---|---|
| `calamity` | `fatalism` | always |
| `entity_death` | `fatalism` | payload["cause"] == "calamity" or "trauma" in cause |
| `entity_death` | `hero_veneration` | payload["entity_role"] == "HERO" |
| `INFLATION_SPIRAL` | `resource_scarcity_memory` | always |
| `war_declared` | `faction_conflict_exposure` | always |
| `territory_transferred` | `faction_conflict_exposure` | always |
| `faction_destroyed` | `faction_conflict_exposure` | always |

A single `entity_death` entry can contribute to both `fatalism` and `hero_veneration`.

### Normalisation

```
axis_value = min(1.0, raw_sum / NORMALISE_DENOMINATOR)
NORMALISE_DENOMINATOR = 3.0
```

Three high-significance events (significance≈1.0) saturate an axis at 1.0.

### Region Attribution

- `entry.payload.get("region_id")` — primary attribution key
- Fallback: entries without `region_id` accumulate into key `"__global__"`

### Episode-Boundary Wiring

`CultureDriftExporter.export(campaign_state, hierarchy, episode_index)` is called
from `CampaignOrchestrator._advance_state()` after `narrative_ledger.extend()`.
`ChronicleGrouper().group(list(self._state.narrative_ledger))` produces the hierarchy.

Existing entries for regions not observed in the current episode persist unchanged.

---

## Cultural Bias Overlay (E62C)

### CulturalBiasApplicator

`CulturalBiasApplicator.compute_culture_delta(culture, tags) -> float`

Defined in `src/domains/culture/applicator.py`. Pure/stateless.

Returns an **additive delta** to the `MotivationBiasService` result. The overlay is
transient — it is never stored in the entity's durable `MotivationModel`.

`CULTURE_ACTIVATION_THRESHOLD = 0.3` — axes below this produce no effect.

### Delta Rules

| Axis (> 0.3) | Tags | Delta |
|---|---|---|
| `fatalism` | `caution`, `recovery`, `flee` | +fatalism × 0.4 each |
| `fatalism` | `pride`, `combat`, `aggressive` | -fatalism × 0.3 each |
| `hero_veneration` | `loyalty`, `party`, `combat` | +hero_veneration × 0.4 each |
| `resource_scarcity_memory` | `survival`, `recovery`, `caution` | +scarcity × 0.4 each |
| `faction_conflict_exposure` | `caution` | +conflict × 0.3 |
| `faction_conflict_exposure` | `loyalty` | -conflict × 0.2 |

Final delta is bounded: `max(-0.5, min(1.0, delta))`.

### MotivationBiasService Extension

`compute_bias_multiplier(entity, tags, culture_values=None) -> float`

Backward-compatible (all existing call sites with 2 args continue to work).
When `culture_values` is provided, `CulturalBiasApplicator.compute_culture_delta()`
result is added before the final `max(0.1, multiplier)` clamp.

---

## Acceptance Signal

In a 5-episode campaign, two regions with different narrative histories produce
measurably different entity behavioral distributions in episode 5. Specifically:

> Mean motivation multiplier for `caution` tag differs between a "calamity region"
> (high fatalism) and a "hero region" (high hero_veneration) by >0.1.

Test: `tests/integration/culture/test_culture_drift_acceptance.py`
→ `test_two_regions_diverge_after_5_episodes`

---

## Integration Points

| Component | File | Role |
|---|---|---|
| `CultureState` | `src/domains/culture/model.py` | Data model |
| `CultureCarryForward` | `src/domains/culture/model.py` | Per-region carry-forward |
| `CultureDeriver` | `src/domains/culture/deriver.py` | ChronicleHierarchy → CultureState |
| `CultureDriftExporter` | `src/domains/culture/exporter.py` | Episode-end persistence hook |
| `CultureDriftImporter` | `src/domains/culture/exporter.py` | Thin lookup (region_id → CultureState) |
| `CulturalBiasApplicator` | `src/domains/culture/applicator.py` | CultureState → motivation delta |
| `MotivationBiasService` | `src/domains/motivation/service.py` | Extended with culture_values param |
| `CampaignState.region_cultures` | `src/domains/campaigns/state.py` | Cross-episode persistence |
| `SettlementPersonalityService` | `src/domains/culture/settlement_personality.py` | CultureState → named settlement-personality descriptor (idea 61, `TCK-20260904-SETTLEMENT-CULTURE-READ`) |
| `CampaignOrchestrator.describe_settlement_personality()` | `src/domains/campaigns/orchestrator.py` | Orchestrator-layer read: composes `CultureDriftImporter.get_culture()` + `SettlementPersonalityService` |
| `GET /api/v1/campaigns/{id}/regions/{id}/personality` | `src/api/routes/campaigns.py` | REST read (first non-Campaign-mode-episode-machinery consumer of `region_cultures`) |
| `LoyaltyDriftService` | `src/systems/social_systems/loyalty_drift.py` | CultureState.faction_conflict_exposure → loyalty-pressure signal (idea 56, `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`) |
| `PartyLifecycleService.effective_defection_threshold()` | `src/systems/social_systems/party_lifecycle.py` | Consumes `LoyaltyDriftService`'s output via an optional `loyalty_pressure` parameter — lowers the grievance threshold idea 39's `check_defection()`/`Faction.NEUTRAL` mutation trigger reads |

Prior to `TCK-20260904-SETTLEMENT-CULTURE-READ`, this contract's Integration Points table stopped at
`CultureDriftImporter` with no listed caller — the three rows above close that gap.

### Idea 56 — Drifting Loyalty (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`)

Reuses `faction_conflict_exposure` and `CultureDriftImporter.get_culture()` exactly as they already
exist — no new Culture Drift derivation/bias-application logic. `LoyaltyDriftService.compute_loyalty_pressure(campaign_state, region_id)`
returns the region's carried-forward `faction_conflict_exposure` (`0.0` if unpopulated), keyed by the
entity's *current* region (`entity.navigation.region_id`, real and live-populated for every entity) —
not `StrategicComponent.home_region_id`, which is populated only for bosses until idea 59
(`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`) lands.

`effective_defection_threshold(group, loyalty_pressure=0.0)` subtracts `round(loyalty_pressure * 2)`
from the threshold (mirroring `composition_score`'s own bonus shape, opposite sign), floored at `1`.
Default `0.0` is fully backward-compatible with every pre-existing caller.

**Gap closed, 2026-09-07 (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`)**: `GroupPhase.resolve()`
(`src/engine/pipeline_phases/groups.py`), the one live per-tick caller of
`effective_defection_threshold()`/`check_defection()`, now reads a real, non-default `loyalty_pressure`
via a new `AuthoritativeState.region_loyalty_pressure: Dict[str, float]` field —
`CampaignOrchestrator._build_initial_state()` snapshots it once per episode from
`CampaignState.region_cultures` (sorted iteration for determinism), and `GroupPhase.resolve()` resolves
each group's real region from its own anchor position (`SpatialQueryService.get_region_at()`) to look
it up. This signal is now live in any Campaign-mode run past episode 0 — not a no-op — proven
end-to-end via `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` (in addition to
the pre-existing `tests/integration/culture/test_loyalty_drift_campaign.py`). It stays at the exact
pre-bridge `0.0` default only for a group whose anchor resolves to no region, a region with no
`region_cultures` entry yet (episode 0), or the separate `SimulationAnalysisRunner` single-episode
path (which never populates `region_loyalty_pressure` at all — Campaign-mode only). See parity ledger
`SOC-276` for the bridge mechanism itself, and `SOC-274` for this amendment's own cross-reference.

Idea 57 (`FameDeriver`/`LegendFact`, the Dormant Mechanism Closure epic's other shared-blocker idea)
remains unaddressed — its real consumer chain (`PerceptionUpdatePhase`, `MotivationBiasService`) has
zero real production callers anywhere in `src/` today, a materially larger, separate gap than a
CampaignState-to-AuthoritativeState data bridge; not fixed by this ticket, tracked separately.

---

## Parity Ledger References

| ID | Description |
|---|---|
| WORLD-CULT-001 | CultureState serializes/deserializes with full round-trip fidelity |
| WORLD-CULT-002 | CultureDeriver axis derivation rules match contract table |
| WORLD-CULT-003 | CulturalBiasApplicator delta rules: fatalism>0.3 raises caution multiplier |
