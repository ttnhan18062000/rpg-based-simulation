# Test Plan — TCK-20260627-P2F-CANON-HASH-DOC

## Tier

Hotfix — documentation-only change.

## No code changes

No source behavior is modified. No new tests needed.

## Verification approach

1. Read the final `docs/engine/known_limitations.md` and verify:
   - Section added describing canonical hash conditionality by runtime mode.
   - Table covers NORMAL/CONSTRAINED/DEGRADED/SURVIVAL modes.
   - "SKIPPED" meaning is explained.
   - fingerprint() scope and limitations are documented.

2. Read the final `docs/engine/kernel.md` and verify:
   - Phase 7 (Persistence) section explains the two-tier hash behavior.

3. Run `pytest tests/docs/ -x -q` — passes (no broken doc references).

4. Run `make knowledge-index-update` — successful (index updated for changed docs).

## Existing tests that cover the subject matter

- `tests/integration/kernel/test_determinism_suite.py` — verifies canonical hash equality across runs (unchanged behavior)
- `tests/unit/engine/test_hash_scheduler.py` — verifies `CanonicalHashScheduler` sanctioned-boundary enforcement (INFRA-197)
- `tests/unit/engine/test_resource_budget_gate.py` — covers `BudgetedCanonicalHasher` (INFRA-196)
