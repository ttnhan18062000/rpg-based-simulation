---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 5 Truth Package

This document serves as the authoritative container for the truth state of `src` at the conclusion of Phase 5. It consolidates scattered notes on divergences, limitations, and unsupported logic to provide a clean entry baseline for Phase 6.

## 1. Truth Surface Map

The Phase 5 truth is split into three primary artifacts:

- **[Divergence Log](../engine/divergence_log.md)**: Every intentional shift from legacy `src` behavior.
- **[Known Limitations](../engine/known_limitations.md)**: What the engine cannot do or does only partially in the current slice.
- **[Support Boundary](../engine/phase5_exit_support_boundary.md)**: The final restatement of exactly what is "Officially Supported."

## 2. Decision Rationale Standard

All records in this package adhere to the `src_principle.md` standards:

- **No Implied Parity**: If it isn't listed, it isn't supported.
- **Explicit Rationale**: Every divergence must be classified (Bug Fix, Contract Hardening, etc.).
- **Evidence-Backed**: Status claims must link to current V2 tests or proof artifacts.

## 3. Immediate Priorities for Phase 6

This package identifies the following "truth gaps" that Milestone 2 must inventory for the replacement ledger:

1.  **AI Tactics**: Legacy AI tactical behaviors (cover seeking, flanking) are currently ignored by the supported slice.
2.  **Social Contracts**: Betrayal, reputation, and social learning logic from `src` are currently unsupported.
3.  **World Calamities**: Regional hazards and calamities are not yet integrated into the V2 substrate.

---
*Created: 2026-04-21 as the formal Phase 6 Entry Gate Truth Package.*
