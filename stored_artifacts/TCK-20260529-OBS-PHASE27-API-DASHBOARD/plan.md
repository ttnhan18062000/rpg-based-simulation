# Plan — Phase 27 API & Dashboard Integration

We will carry out:
1. **Extend Artifact Repository & Retention**:
   - Update `src/observability/reporting/artifact_repository.py` to resolve paths for behavior artifacts.
   - Update `src/observability/reporting/retention.py` to delete behavior files when pruning.
2. **Extend Warehouse Schema**:
   - Update local dataset adapter and models in `src/observability/warehouse/` to include behavior tables and paginated querying.
3. **Add Query APIs**:
   - In `src/api/server.py`, add `/api/v1/behavior/*` endpoints.
4. **Dashboard Panels**:
   - Extend the UI in `src/api/server.py` to display beautiful behavior panels when behavior scorecards are present.
