# Phase 10 Cross-Phase Boundary Notes

This document distinguishes the four distinct types of work occurring during the final stages of the V2 engine replacement.

## 1. Semantic Recovery (Phases 5-9)
- **Nature**: Implementing gameplay logic (combat, movement, town, cognition, social).
- **Status**: **CLOSED**. All P0/P1 semantic features are implemented and verified.
- **Phase 10 Role**: Consumer of stable semantics. Phase 10 will not add new gameplay rules.

## 2. Compatibility Closure (Phase 10)
- **Nature**: Closing the system-surface gap (CLI, Env, Observability, API).
- **Focus**: Making V2 a drop-in replacement for the *system surface*.
- **Boundary**: Ends at the edge of the engine. Does not include consumer-side refactoring.

## 3. Proof Ratification (Phase 11)
- **Nature**: Broad verification, stress testing, and official characterization.
- **Focus**: Proving that the compatibility and semantics are correct under load and edge cases.
- **Dependency**: Blocked by Phase 10 completion.

## 4. Consumer Cutover (Phase 12)
- **Nature**: Switching the actual product/consumers to use V2.
- **Focus**: Retirement of legacy `src` paths in the broader application.
- **Dependency**: Blocked by Phase 11 ratification.
