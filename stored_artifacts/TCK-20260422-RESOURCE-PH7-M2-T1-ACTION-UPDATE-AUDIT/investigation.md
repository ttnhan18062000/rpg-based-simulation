# Audit: Phase 7 Action/Update Substrate

## 1. Current Implementation State (`src_v2`)

### 1.1 Already Closed / Hardened
- **Typed Update Buckets**: `StateUpdate` and `EntityUpdate` in `src_v2/core/updates.py` are already well-defined, frozen dataclasses using slots. They support disaggregated update domains (Combat, Social, Inventory, etc.).
- **Worker Result Loop**: `WorkerResult` correctly carries an `EntityUpdate` back to the kernel.

### 1.2 Identified Gaps (Critical)

#### Gap A: Missing Action Proposal Model (Intent)
- **Problem**: There is no `ActionProposal` class in `src_v2`. The simulation lacks an explicit representation of "Intent" (Actor + Verb + Target + Reason).
- **Impact**: The kernel is forced to perform "Intent Routing" (e.g. `InteractionUpdate` and `MovementUpdate` generation) inside `_phase_resolution`, which violates the separation of worker thought and authoritative mutation.
- **Affected Files**: `src_v2/core/updates.py` (needs pairing with Intent), `src_v2/engine/kernel.py` (needs to move routing logic to workers).

#### Gap B: Missing Reason/Target Normalization
- **Problem**: `EntityUpdate` lacks a `reason` field. Legacy `ActionProposal` carried a strictly typed `ActionReason`.
- **Impact**: Replay and diagnostic auditing cannot explain *why* a mutation occurred without expensive inference.
- **Affected Files**: `src_v2/core/updates.py`.

#### Gap C: Update Domain Fuzzy Boundaries
- **Problem**: Some fields in `EntityUpdate` are still "flat" (e.g. `readiness_delta`, `active`, `new_position`) instead of being grouped into typed domain buckets (e.g. `PhysicalUpdate` or `SpatialUpdate`).
- **Impact**: Harder to enforce partial rejection or domain-specific constraints.
- **Affected Files**: `src_v2/core/updates.py`.

#### Gap D: Worker-side Direct Mutation Shortcuts
- **Problem**: Workers (currently represented by `src_v2/engine/worker_manager.py` and `src_v2/engine/executor.py`) have access to the `AuthoritativeState` (read-only), but the protocol for producing `EntityUpdate` is still being refined.
- **Impact**: Risk of workers bypassing the intent-proposal model if not strictly enforced by the protocol.

## 2. Legacy Coercion Audit
- **Legacy `ActionProposal`**: Actor + Verb + Target + Reason + Updates.
- **Legacy `IntentUpdate`**: Typed subclasses for each domain.
- **Normalization Required**: V2 must adopt a similar structure but optimized for the `ApplyPath` and `ReplayManager`.

## 3. Roadmap for Milestone 2 Closure
1. **Task 2**: Implement `src_v2/core/actions.py` with `ActionProposal`.
2. **Task 3**: Refine `EntityUpdate` to disaggregate remaining flat fields into domains.
3. **Task 4**: Add `ActionReason` enum/model and integrate into `ActionProposal`.
4. **Task 5**: Update `Kernel` to consume `ActionProposal` and remove internal "Intent Routing".
