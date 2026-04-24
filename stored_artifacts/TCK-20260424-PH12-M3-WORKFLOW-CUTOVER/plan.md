# Phase 12 Milestone 3 Execution Plan: Workflow Cutover

## 1. Makefile Modernization
- Update `test` target to `python -m pytest tests_v2/ -v --tb=short`.
- Update `test-cov` target to `python -m pytest tests_v2/ -v --tb=short --cov=src_v2 --cov-report=term-missing`.
- Update `profile` and `profile-full` to point to the V2-capable scripts (or verify their delegation).

## 2. CI/CD Realignment
- Identify and update any `.github/workflows/` or Jenkinsfiles that point to legacy paths.
- Ensure the `Certification` and `Parity` jobs in CI are the primary gates for merges.

## 3. Operational Proofs
- Run `scripts/refresh_proofs.py` to ensure the `docs/engine/manifest.json` is backed by V2 results.
- Verify that `reports/release_proof/` is populated with V2 artifacts.

## 4. Documentation
- Update `CONTRIBUTING.md` or `README.md` to reflect that `tests_v2` is the required test suite.
