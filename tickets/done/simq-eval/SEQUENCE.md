# SEQUENCE — simq-eval

Strict implementation order. Each ticket must be DONE before the next begins.

1. **TCK-20260702-SIMQ-EVAL-MATRIX** — expand calibration corpus to multi-seed/multi-tick matrix; establishes the run keys and anchor grades the harness covers
2. **TCK-20260702-SIMQ-EVAL-HARNESS** — implement `tools/evaluate_simq.py` and `make evaluate`; canonical scenario list is drawn from the expanded corpus produced by ticket 1

## Rationale

The harness (ticket 2) should incorporate the new run keys from the matrix (ticket 1) in its default scenario list. Running the harness before the matrix would give it an incomplete canonical set that would need immediate updating. Implement in order.
