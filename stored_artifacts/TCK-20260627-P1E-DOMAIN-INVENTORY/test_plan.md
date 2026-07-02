# Test Plan — TCK-20260627-P1E-DOMAIN-INVENTORY

## Scope
Documentation-only ticket. No behavior change. No code change.

## Verification Steps

### 1. Document completeness hand-count
- Count phases in `docs/audits/D19_domain_phase_inventory.md` pipeline table.
- Count `run_phase(` calls in `src/engine/pipeline.py` + 1 for `faction_decision` (direct call).
- Expected: 37 pipeline phases documented (30 active + 7 feature-gated).
- Count world_dynamics sub-phases against `src/engine/world_dynamics.py`.
- Expected: 15 sub-phases documented (7 every-tick + 8 cadence-gated).

### 2. Contributor guardrail tests
Run: `pytest tests/docs/ -x`
- If no `tests/docs/` directory exists, the test plan passes vacuously (no doc tests defined).
- Pass criterion: zero test failures.

### 3. Knowledge index update
Run: `make knowledge-index-update`
- Pass criterion: command exits 0.

### 4. REGISTRY.yaml entry
- Confirm `docs/REGISTRY.yaml` contains an entry for `docs/audits/D19_domain_phase_inventory.md`.
- Entry must have: `type: doc`, `status: active`, `layer: architecture`, `authority: P1`.

## Pass Criteria
- [ ] Phase count in D19 matches pipeline.py hand-count (37 pipeline + 15 world_dynamics sub-phases)
- [ ] `pytest tests/docs/ -x` exits 0 (or no tests/docs/ directory)
- [ ] `make knowledge-index-update` exits 0
- [ ] REGISTRY.yaml contains D19 entry
