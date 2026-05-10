# Test Plan

## Per Domain
After each domain migration, run:
```bash
python3 -m pytest tests/<domain>/ -q --tb=short
```
Verify: no new failures, all previously-passing tests still pass.

## Final Verification
```bash
python3 -m pytest tests/ -q --tb=no
```
Target: 0 failures, 0 errors.

## Regression Guard
After all domains, add `tests/integrity/test_no_legacy_builder_api.py` (plan item 10).
