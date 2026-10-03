---
ticket_id: TCK-20260619-E62A-CULTURE-MODEL
phase: plan
date: 2026-06-23
---

# Plan — TCK-20260619-E62A-CULTURE-MODEL

## Files Created / Modified

| File | Action |
|---|---|
| `src/domains/culture/__init__.py` | New (empty package marker) |
| `src/domains/culture/model.py` | New — CultureState + CultureCarryForward |
| `src/domains/campaigns/state.py` | Modified — import + field + to_dict + from_dict |
| `tests/unit/culture/__init__.py` | New (empty) |
| `tests/unit/culture/test_culture_model.py` | New — 5 unit tests |

## Design Decisions

- `slots=True` on both dataclasses for consistency with other frozen domain models
- `CultureState.from_dict()` uses `.get()` with 0.0 defaults for forward/backward compat
- `CampaignState.from_dict()` uses `d.get("region_cultures", {})` for backward compat
- No int↔str key conversion for region_cultures (region_id is always a str)
- Serialized dict keys sorted for determinism
