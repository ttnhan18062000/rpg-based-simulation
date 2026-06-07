# Implementation Sequence — phase2028-repair-followup

Tickets in this batch have inter-dependencies. Run `/implement-epic` or
`/implement-ticket` in the order below to avoid implementing a ticket before
its dependencies are in place.

## Correct Order

```
Track A (mode + registry)
─────────────────────────
1. TCK-20260608-RUNTIME-MODE-EXPLICIT       (no deps in this batch)
2. TCK-20260608-ADAPTER-HEURISTIC-USAGE     (depends on: RUNTIME-MODE-EXPLICIT)
3. TCK-20260608-REGISTRY-PARITY-SPLIT       (depends on: RUNTIME-MODE-EXPLICIT, ADAPTER-HEURISTIC-USAGE)

Track B (combat rewards)
─────────────────────────
4. TCK-20260608-CLASSIFY-DEFEATED-TARGET    (no deps in this batch)
5. TCK-20260608-REWARD-TRACE-COVERAGE       (depends on: CLASSIFY-DEFEATED-TARGET)

Track C (module refs)
─────────────────────
6. TCK-20260608-NORMALIZED-MODULE-REFS      (no deps in this batch)
7. TCK-20260608-REAL-MODULE-SNAPSHOT        (depends on: NORMALIZED-MODULE-REFS)
```

Tracks B and C are independent of Track A and of each other — they can be
worked in parallel if multiple implementers are available. Within each track
the listed order is mandatory.

## Why Alphabetical Order Fails

`implement-epic` discovers files alphabetically. In that order
`ADAPTER-HEURISTIC-USAGE` (step 2) runs before `RUNTIME-MODE-EXPLICIT`
(step 1, last alphabetically) — this breaks the mode dependency.
`REGISTRY-PARITY-SPLIT` has the same problem.

**Workaround:** run `implement-epic` once per track in the correct order, or
run each ticket individually with `/implement-ticket ticket_id=<id>`.
