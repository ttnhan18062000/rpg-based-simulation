# Phase 11 Entry Support Boundary

This document defines the honest support boundary of the `src_v2` engine as of the start of Phase 11.

## 1. Supported Scope (Full Parity)

The following areas are fully supported and verified with 100% test stability:

- **Operational Surface**: CLI entrypoint, headless execution, configuration precedence, and environment isolation.
- **Observability**: Structured JSON logging, directory-based replay artifacts, and FastAPI-based metrics/health.
- **API & Protocol**: REST state/control endpoints and WebSocket state streaming (JSON/MessagePack).
- **Core Substrate**: Authoritative single-process kernel, deterministic tick loop, and typed state updates.
- **Strategic Cognition**: Bounded project management, lead learning, belief decay, and strategic detours.
- **Social Mechanics**: Trust-weighted recruitment, betrayal history, and familiarity-based appraisals.

## 2. Divergent Scope (Intentional Difference)

The following areas differ intentionally from legacy behavior to satisfy V2 principles:

- **Brokerless by Default**: V2 prioritizes in-process fallback over external message brokers for standard runs.
- **Sequential Reference**: Concurrency is treated as a bounded execution mode; the sequential path is the absolute semantic baseline.
- **Honest Allowed Failures**: Certification reports track observed failures even if they are whitelisted, preventing hidden regressions.

## 3. Unsupported Scope (Deferred or Retired)

The following legacy features are **NOT** implemented in `src_v2` and are excluded from ratification:

- **Legacy UI**: Old web-frontend integration (replaced by modern API/WS contracts).
- **External Redis Pub/Sub**: Replaced by in-process tick listeners for state streaming.
- **RPG Math Quirks**: Incidental ordering bugs in old combat math have been replaced by deterministic, typed formulas.
- **Deferred Gameplay**: Flanking, complex backstab mechanics, and specific building-interior simulations.

## 4. Known Limitations

- **Replay Size**: High-frequency logging during replays can exceed 100MB for very long runs (>10,000 ticks).
- **WebSocket Throughput**: MessagePack is mandatory for low-latency state streaming of entities > 500.

---
**Ratification Status**: OPEN
**Approval Gate**: Phase 11 Milestone 1
