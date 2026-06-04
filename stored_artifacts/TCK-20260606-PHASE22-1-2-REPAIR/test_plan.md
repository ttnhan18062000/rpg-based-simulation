# Test Plan - Phase 22.1 & 22.2 Schema and Normalization Repair

We will verify our implementation by running the updated unit tests.

## Automated Tests

Run:
```bash
pytest tests/unit/worldassembly/test_assembly.py
```

Specifically check that:
- `test_unknown_field_in_real_world_module_fails` validates fail-closed behavior on real module files.
- `test_unknown_field_in_real_composition_fails` validates fail-closed behavior on real composition files.
- `test_real_composition_normalization_preserves_perspectives` validates that perspectives survive normalization and mixed structures fail.
