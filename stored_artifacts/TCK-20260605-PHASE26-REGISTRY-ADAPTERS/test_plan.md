# Test Plan - Phase 26

1. Unit tests for each of the new registry adapters. We can put them in `tests/unit/core/test_registry_adapters.py`.
2. Parity tests verifying that all catalog entries mapped via adapters are successfully registered. Place in `tests/unit/core/test_registry_parity.py`.
3. Run existing tests to ensure no regressions.
