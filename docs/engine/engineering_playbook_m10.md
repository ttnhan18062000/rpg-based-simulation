# Engineering Playbook: Resource-Safe Engine Maintenance

## Purpose
This document establishes the authoritative laws for extending and maintaining the simulation engine. It ensures that future contributions do not quietly reintroduce resource leaks, implicit dependencies, or unbounded state.

## Extension Rules

### 1. New Subsystem Declaration
Any new subsystem must explicitly declare its resource and semantic boundaries in its contract documentation:
- **Authoritative Status**: Is the subsystem state part of the hashable, deterministic `AuthoritativeState`?
- **Resource Budget**: What is the maximum RAM and CPU overhead per tick?
- **Retention Policy**: What happens when internal buffers (queues, logs) overflow? (e.g., Drop Oldest, Pause Producer).
- **Degradability**: How does the subsystem behave in `CONSTRAINED` or `DEGRADED` modes?

### 2. TDD Extension Loop
All new features must follow this exact sequence:
1. **Contract Test**: Define the observability and safety boundaries first.
2. **Minimal Implementation**: The leanest possible logic to satisfy the contract.
3. **Scenario Test**: Multi-tick validation of deterministic behavior.
4. **Certification**: Verification against the `CertificationHarness` for hardware-class bounds.

### 3. State Management Laws
- **The Authoritative Filter**: Only state required for deterministic simulation belongs in `AuthoritativeState`. Telemetry, diagnostics, and UI-only data must be kept in non-authoritative "Shadow State".
- **Immutable Transitions**: All durable state mutations must flow through the authoritative `apply` path. Local modifications in AI or decision logic are strictly for proposal generation.

## Project Guardrails

### Forbidden Patterns
- **Unbounded Collections**: No `list` or `dict` may grow without a defined `max_size` or retention policy.
- **Alternate Authority**: No side-channel state (static variables, global registries) may influence simulation outcomes.
- **Honest Language Rules**: No documentation or PR may claim "unlimited speed" or "unbound performance". All metrics must be bound to a specific `(Profile, Scenario, Hardware Class)` bundle.
- **Ad-hoc Threading**: Any concurrency must be managed by the `Scheduler` and constrained by the `WorkerPool` bounds.

## Extension Templates

### Runtime Profile Template
```markdown
## Profile: [Name]
- Hardware Class: [CLASS_A|CLASS_B|CLASS_C]
- Max RAM: [X] MB
- Max CPU: [Y]%
- Max Worker Count: [N]
- Retention Policy: [Policy Name]
```

### Certification Scenario Template
```markdown
## Scenario: [ID]
- Objective: [Describe pressure target]
- Duration: [Ticks]
- Expected Failure: [FailureKind|NONE]
- Recovery Required: [Yes/No]
- Sampling Cadence: [Ticks]
```

### Subsystem Contract Template
```markdown
## Subsystem: [Name]
- **Authoritative Status**: [YES/NO] (Must be YES if impacting simulation)
- **State Partition**: [State category in runtime_state_contract_m3.md]
- **Resource Budget**:
  - Max RSS: [X] MB
  - Max Compute: [Y] ms / tick
- **Retention / Overflow Policy**: [e.g. DROP_OLDEST, BLOCK]
- **Degradation Laws**:
  - CONSTRAINED: [Behavior change]
  - DEGRADED: [Behavior change]
  - SURVIVAL: [Behavior change]
```
