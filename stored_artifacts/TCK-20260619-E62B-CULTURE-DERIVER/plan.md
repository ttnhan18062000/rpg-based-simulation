---
ticket_id: TCK-20260619-E62B-CULTURE-DERIVER
phase: plan
date: 2026-06-23
---

# Plan — TCK-20260619-E62B-CULTURE-DERIVER

## Files Created / Modified

| File | Action |
|---|---|
| `src/domains/culture/deriver.py` | New — CultureDeriver.derive() |
| `src/domains/culture/exporter.py` | New — CultureDriftExporter + CultureDriftImporter |
| `src/domains/campaigns/orchestrator.py` | Modified — _advance_state() wiring |
| `tests/unit/culture/test_culture_deriver.py` | New — 9 unit tests |
| `tests/unit/culture/test_culture_exporter.py` | New — 6 unit tests |

## Axis Derivation (NORMALISE_DENOMINATOR=3.0)

| Event type | Axis |
|---|---|
| calamity | fatalism |
| entity_death where cause=="calamity" or "trauma" in cause | fatalism |
| entity_death where entity_role=="HERO" | hero_veneration |
| INFLATION_SPIRAL | resource_scarcity_memory |
| war_declared, territory_transferred, faction_destroyed | faction_conflict_exposure |

Entity_death can contribute to BOTH fatalism AND hero_veneration in the same entry.
