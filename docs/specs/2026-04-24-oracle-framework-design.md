---
status: archive
authority: P2
audience: historical
layer: misc
original_date: 2026-04-24
---

# Legacy Oracle Framework Design

## 1. Goal
To provide a deterministic, bit-identical "Source of Truth" for V2 implementation verification. The framework allows V2 parity tests to run against pre-recorded results from the legacy engine, eliminating the need to run both engines simultaneously during every test run.

## 2. Components

### 2.1 Oracle Schema
Oracles are stored as JSON fixtures. Each file contains a set of "cases" (Input/Output pairs).

```json
{
  "oracle_id": "string",
  "domain": "string",
  "function": "string",
  "cases": [
    {
      "input": {},
      "expected": {}
    }
  ]
}
```

### 2.2 Generator Tool (`tools/parity/generate_legacy_oracle.py`)
A command-line tool that:
1. Dynamically imports legacy `src`.
2. Uses "Input Factories" to generate test vectors.
3. Executes legacy functions and records results.
4. Saves to `tests/oracles/`.

### 2.3 Loader Utility (`tests/parity/helpers/oracle_loader.py`)
A helper for `pytest` suites to:
1. Locate domain-specific oracles.
2. Provide a clean interface for `@pytest.mark.parametrize`.
3. Validate that the loaded oracle matches the expected function signature.

## 3. Workflow
1. **Define Contract**: Identify a legacy function to port (e.g., `compute_attribute_bonus`).
2. **Generate Truth**: Run the generator to capture 100+ cases of that function's behavior in legacy.
3. **Implement V2**: Write the V2 version in `src`.
4. **Differential Test**: Write a V2 test that loads the oracle and asserts that `v2_output == legacy_output`.

## 4. Maintenance
Oracles are considered **Immutable Truth**. If a legacy bug is discovered and we *intend* to change it in V2, we mark the test as `intentional_divergence` and document the rationale in the Parity Ledger, rather than modifying the oracle data itself.
