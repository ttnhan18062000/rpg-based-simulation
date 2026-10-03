---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY
date: 2026-10-03
tags: [performance, architecture, determinism]
---

# Investigation: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY

- 14 call sites in `src/`: 9 callers (kernel x5, compiler x2, certification harness x2) plus one
  hand-rolled SHA-256 (`harness._write_full_evidence`), and 5 delegations inside the mechanisms.
- `CanonicalHashScheduler` governs only the two harness calls; `BudgetedCanonicalHasher` governs
  nothing; the kernel's per-tick and shutdown hashes are ungoverned.
- Per-tick persistence hashes the post-advancement state (tick T+1); the REFINED_UPDATE fingerprint
  describes the pre-advancement state (tick T).
- 22 state dataclasses cache `to_canonical_dict()`; that is the only stale-value path under the flat hash.
- Seven document statements disagree with the code (document section 6).
- Nothing in `src/` reads the `TICK_END` or `REFINED_UPDATE` payloads; what reads the replay files was not traced.
