---
status: active
ticket_id: TCK-20260619-E51E-REST-API
artifact_type: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E51E-REST-API

## Context

E51E adds REST surface for the Chronicle pipeline (E51A–E51D). The prior epic
tickets are all DONE as of 2026-06-22. Unblocked.

## Existing Patterns

### API Route Pattern (campaigns.py)
- `APIRouter(prefix="/campaigns", tags=[...])`
- Module-level registry dict: `Dict[str, CampaignState]` with `register_*` / `_clear_registry()` helpers
- Route handlers are `async def`, `anyio`-testable by calling directly
- No raw domain models in responses — all go through presenter layer

### Presenter Pattern (presenters/campaigns.py)
- Pydantic `BaseModel` subclasses as response types
- `from_domain(cls, entry)` factory using attribute access (no circular import)
- Response model annotated on `@router.get(..., response_model=<Model>)`

### server.py Registration
- `from src.api.routes import <module>` then `app.include_router(<module>.router, prefix="/api/v1")`
- Chronicle router will follow the same pattern

## Chronicle JSON Schema (from renderer.py)

```json
{
  "campaign_id": "str",
  "eras": [{"id": "str", "ordinal": int, "name": "str", "significance": float, "episode_ids": ["str"]}],
  "episodes": [{"id": "str", "index": int, "significance": float, "incident_ids": ["str"]}],
  "named_milestones": [{"name": "str", "tick": int, "episode": int, "event_type": "str", "significance": float, "entry_id": "str"}]
}
```

## Data Loading Strategy

`chronicle.json` is written to `output_dir/chronicle.json` by `ChronicleCompiler.compile()`.
The REST layer needs to load from a per-campaign directory.
Pattern: registry dict `Dict[str, dict]` keyed by campaign_id, populated via
`register_chronicle(campaign_id, chronicle_data)` — mirrors campaigns.py.
No filesystem reads during tests; tests inject via registry directly.

## Era Summary Endpoint

`GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary`
- Looks up era by `era_id` (e.g. `"era:0"`) inside the registered chronicle dict
- Returns: `{era_id, name, milestone_count, named_milestones: [str, ...]}`
- `named_milestones` = names from `named_milestones` array where `episode` matches
  the episodes of that era (via `episode_ids` in the era object)

## Decisions

1. Registry pattern (same as campaigns.py) — no filesystem reads in tests, clean injection.
2. Presenter Pydantic models in `src/api/presenters/chronicle.py` (new file).
3. No circular imports — presenters only use dicts from the registry (not domain objects).
4. Era milestones: collect all `named_milestones` whose `episode` index is in any
   of the era's `episode_ids` (episode IDs have form `"episode:{index}"`, so parse the index).
