# Milestone 13 Test Plan: Optimization Proof Report Verification

## 1. Automated Verification (`pytest`)
Execute the newly created optimization proof regression test:
```bash
pytest tests/perf/test_optimization_proof_report.py -v
```

### Validation Targets:
- **Metric Collection**: Asserts that `raw_entity_updates`, `compacted_entity_updates`, `movement_candidates`, `strategic_candidates`, and hit/miss rates are non-zero and correctly aggregated in benchmark output.
- **Compute Isolation**: Asserts that adding these metrics does not artificially inflate `tick_compute_ms`.
- **Speedup Enforcement**: Asserts that optimized performance meets or exceeds baseline speedup requirements across `MOVEMENT_1000`, `RESOURCE_1000`, `COMBAT_100`, `STRATEGIC_500`, `MIXED_1000`.

## 2. Report Generation Verification
Run the proof report generation script:
```bash
python scripts/generate_optimization_proof.py
```
Verify that `reports/perf/optimization_proof.json` and `reports/perf/optimization_proof.md` are correctly generated and formatted.
