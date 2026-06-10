# Implementation Sequence — observability-worker-leak

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260610-KERNEL-TEST-TEARDOWN  (no deps in this batch)
2. TCK-20260610-MEMORY-DEBUG-TOOL  (no deps in this batch)
3. TCK-20260610-WORKER-SINGLETON-GUARD  (no deps in this batch)
4. TCK-20260610-THREAD-LEAK-CONFTEST  (depends on: TCK-20260610-KERNEL-TEST-TEARDOWN)

## Why This Order Matters

The thread-leak conftest sentinel (ticket 4) validates that the test suite runs clean after
the teardown fixes are applied. Implementing the sentinel before the teardown fixes would
cause it to fail on the very leaks it is meant to detect as regressions — not a useful signal.
The memory debug tool (ticket 2) is independent and can be built alongside the teardown fix;
it exposes importable helpers that the conftest sentinel can optionally reuse.
Tickets 1, 2, and 3 are independent of each other and can be implemented in any order;
the sequence above uses logical priority as the tiebreak.

Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
