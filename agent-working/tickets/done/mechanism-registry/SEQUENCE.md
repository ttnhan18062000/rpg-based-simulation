# Implementation Sequence — mechanism-registry

Tickets must be implemented in this order. `implement-epic` reads this file to override alphabetical
order. `TCK-20260915-EPIC-MECHANISM-REGISTRY` is the epic-tier parent and is not implemented
directly — it tracks the four below.

## Order

1. TCK-20260915-MECHANISM-REGISTRY-FOUNDATION  (no deps in this batch)
2. TCK-20260915-MECHANISM-VERIFICATION-AXIS  (depends on: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION)
3. TCK-20260915-MECHANISM-PRIORITY-DERIVATION  (depends on: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION)
4. TCK-20260915-ARTIFACT-STATE-CONVERGENCE  (depends on: FOUNDATION + VERIFICATION-AXIS)

## Why This Order Matters

FOUNDATION creates the file everything else reads; nothing can proceed without it.

VERIFICATION-AXIS and PRIORITY-DERIVATION are independent of each other and touch different fields
(`verified` vs `depends_on`/`layer`). They may run in parallel or in either order — 2 before 3 only
because the verification axis is smaller and unblocks the more valuable question sooner ("has anyone
observed this working?" before "what order should we fix things in").

ARTIFACT-STATE-CONVERGENCE runs last and depends on VERIFICATION-AXIS as well as FOUNDATION, because
artifacts render `verified` alongside `state`; converging them before the field exists would mean
touching all five artifacts twice.

## Note on the fifth gap

A fifth issue was raised in scoping — *state is prose, not data* (roughly 100 distinct badge texts
across 147 badge instances). It has **no ticket** deliberately. Those texts are verification
statements sitting in a build-status field, and they migrate as part of
TCK-20260915-MECHANISM-VERIFICATION-AXIS. Adding badge classes to solve it directly is explicitly
rejected in `docs/plans/mechanism_registry_initiative.md` §2 Gap 2.
