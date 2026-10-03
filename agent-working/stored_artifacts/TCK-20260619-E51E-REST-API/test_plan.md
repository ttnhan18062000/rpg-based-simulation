---
status: active
ticket_id: TCK-20260619-E51E-REST-API
artifact_type: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E51E-REST-API

## Test File
`tests/api/test_chronicle_api.py`

## Test Cases

### TC-1: test_chronicle_rest_endpoint_returns_structured_json (AC-1)
- Register chronicle dict with eras, episodes, named_milestones
- Call `get_chronicle(campaign_id=...)` directly
- Assert response has `campaign_id`, `eras`, `episodes`, `named_milestones`
- Assert eras are `ChronicleEraPresenter` instances (not raw dicts)
- Assert all keys present

### TC-2: test_era_summary_endpoint_returns_milestone_names (AC-2)
- Chronicle dict with ≥1 era containing named_milestones
- Call `get_era_summary(campaign_id, era_id=...)`
- Assert `era_id`, `name`, `milestone_count`, `named_milestones: [str, ...]`
- Assert milestone names are strings

### TC-3: test_chronicle_404_unknown_campaign
- No registration
- `get_chronicle("nonexistent")` → `HTTPException(404)`

### TC-4: test_era_summary_404_unknown_era
- Register chronicle, call with `era_id="era:99"` (not present)
- → `HTTPException(404)` with era_id in detail

### TC-5: test_chronicle_empty_eras
- Register chronicle dict with empty eras/episodes/named_milestones
- `get_chronicle(...)` → `eras=[], episodes=[], named_milestones=[]`

## Run Command
```bash
pytest tests/api/test_chronicle_api.py -x -v
```
