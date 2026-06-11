---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 7 — Optimization Cleanup After Truth Is Proven

## Goal

Only after Milestones 1–6 pass, start improving actual performance.

## Candidate optimizations

| Area                 | Narrow implementation logic                                                             | Risk                           |
| -------------------- | --------------------------------------------------------------------------------------- | ------------------------------ |
| Spatial node search  | Replace O(N) harvesting node scan with `SpatialQueryService` for large worlds.          | Medium                         |
| Goal scoring         | Cache nearest tavern/inn/town service per tick or region.                               | Medium                         |
| Resource interaction | Avoid scanning all nodes/entities when DirtySet says only a subset moved or interacted. | High unless DirtySet is proven |
| Strategic system     | Process dirty strategic entities first; background sweep on cadence.                    | High                           |
| ApplyPath            | Continue no-op detection and identity preservation.                                     | Low                            |
| Worker chunking      | Tune chunk size based on measured executor overhead.                                    | Medium                         |
| Serialization/API    | Avoid full snapshot for UI unless explicitly requested; use paging/delta.               | Low                            |

The source already contains optimized identity preservation/no-op style code in the apply path, so future work should extend that pattern, not add random caches everywhere. 

## Tasks

| Task                                            | Narrow implementation logic |
| ----------------------------------------------- | --------------------------- |
| M7.1 Pick one bottleneck from phase report      |                             |
| M7.2 Write a failing perf characterization test |                             |
| M7.3 Write semantic parity test first           |                             |
| M7.4 Implement only one optimization            |                             |
| M7.5 Compare optimized vs baseline              |                             |
| M7.6 Update audit ledger                        |                             |
| M7.7 Repeat only if gain is real                |                             |

## Acceptance checklist

```text
[ ] Optimization target is chosen from measured phase data.
[ ] Semantic parity test exists before implementation.
[ ] Perf test shows improvement above noise threshold.
[ ] Memory does not regress beyond threshold.
[ ] No checklist law is downgraded.
[ ] Audit ledger records before/after numbers.
```

## Exit condition

Optimization work becomes evidence-driven instead of speculative.

---
