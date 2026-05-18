# Staging Test Plan — Optimization Documentation and Invariant Ledger

## 1. Test Verification
We will run the entire suite of optimization unit, integration, and certification tests to prove absolute stability across all mechanisms:
- `pytest tests/unit/optimization/` (Verifying individual mechanisms: spatial indexing, dirty tracking, compaction, patches, caches, and profiles).
- `pytest tests/integration/optimization/` (Verifying apply plan parity, cache bounds, patch apply parity, full scan phase compliance, phase skipping parity, and profile-specific behavior).
- `pytest tests/certification/` (Verifying long-run stability and production readiness).

## 2. Invariant Ledger Test Citations
We will ensure that every invariant documented in `docs/performance/optimization_invariants.md` directly references specific, passing test suites in the repository.
