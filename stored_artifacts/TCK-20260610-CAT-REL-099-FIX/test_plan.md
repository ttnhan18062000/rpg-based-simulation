# Test Plan — TCK-20260610-CAT-REL-099-FIX

## Regression Surface

Existing tests that must continue to pass:
- `tests/integration/content/test_strict_world_matrix.py` — pre-assembly rows (currently passing); full-assembly rows (currently xfail → should pass after fix)
- `tests/integration/content/test_expansion_gate.py` — gate item 11 (currently xfail → should pass after fix)
- `tests/integration/scenarios/test_scenario_setup_resolver.py` — happy-path test (currently xfail → should pass after fix)
- `tests/unit/content/test_catalog_validator.py` (if exists) — validator unit tests must still pass
- `tests/integration/worldassembly/test_real_content_world_modules.py` — must continue to pass

## New Tests Required

No new test file needed — the fix is a data correction that directly causes previously xfailed tests to pass.

After removing the `_PREEXISTING_CAT_BUG` xfail markers:
- `test_strict_world_matrix.py` full-assembly rows must pass (not xfail, not skip)
- `test_expansion_gate.py` gate item 11 must pass
- `test_scenario_setup_resolver.py` happy-path test must pass

## Scoped Pytest Commands

```bash
# Verify validator no longer fires CAT-REL-099
pytest tests/unit/content/ -x -q 2>/dev/null || pytest tests/integration/content/ -k "validator" -x -q

# Verify expansion gate is now 12/12
pytest tests/integration/content/test_expansion_gate.py -v

# Verify strict matrix full-assembly rows pass
pytest tests/integration/content/test_strict_world_matrix.py -v

# Verify scenario resolver happy path passes
pytest tests/integration/scenarios/test_scenario_setup_resolver.py -v

# Full worldassembly integration smoke
pytest tests/integration/worldassembly/ -x -q
```

## Anti-Drift Test Guards

- After fix, `_PREEXISTING_CAT_BUG` xfail markers must be removed from all three test files
- If any test still xfails after the data fix, investigate separately — do not leave CAT-REL-099 xfail markers as catch-all
