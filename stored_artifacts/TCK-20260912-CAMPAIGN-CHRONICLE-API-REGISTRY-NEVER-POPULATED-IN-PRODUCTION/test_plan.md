# Test Plan — TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION

## New tests (`tests/api/test_inert_route_gating.py`, shared with the sibling ticket)

- `test_campaign_chronicle_api_disabled_by_default`: default `RuntimeProfile` — both
  `/api/v1/campaigns/{id}/history` and `/api/v1/chronicle/{id}` return FastAPI's own generic 404.
- `test_campaign_chronicle_api_reachable_when_enabled`: `enable_campaign_chronicle_api=True` —
  both routes reached, giving the handler's own real domain-level 404 (distinguishable by response
  body from the "route not mounted" 404 above).

## Regression

- `tests/api/` full suite (153 passed) — confirms `test_campaign_history_api.py`/
  `test_chronicle_api.py` (direct-handler-call tests) are unaffected.
- `tests/tools/test_parity_index.py`, `test_parity_index_baseline.py`, `test_parity_ledger_scan.py`,
  `test_parity_ledger_writer.py` (97 passed) — confirms the two parity ledger corrections
  (`INFRA-219`, `SOC-CHRON-005`) are schema-valid and the derived index rebuilt cleanly.
