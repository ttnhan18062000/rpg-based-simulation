---
trigger: always_on
---

# Testing Rule

## General

- Run relevant existing tests before claiming completion. Do not run the entire test suite (`pytest tests/`) all at once, as full test runs take too long. Always scope test runs to the narrow domain under modification or use markers (`pytest -m "not slow"`).
- Add or update tests whenever behavior changes.
- Prefer deterministic, isolated, readable tests.
- Test meaningful behavior, not superficial coverage.

## Required Coverage

Cover:

- normal flow
- edge cases
- failure modes
- regression-prone paths

## Architecture Tests

When relevant, verify:

- read-only logic did not mutate live state
- authoritative application path was used
- typed records serialize/deserialize correctly
- snapshot/read-model behavior is stable
- presentation surfaces still work
- replay/telemetry/metrics stay consistent if affected
