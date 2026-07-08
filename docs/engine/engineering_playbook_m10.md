---
status: active
layer: engine
authority: P1
audience: developer
---

# Engineering Playbook — Milestone 10

## Purpose

Authoritative laws for extending and maintaining the simulation engine at Milestone 10.
Supersedes earlier milestone playbooks. See `engineering_playbook.md` for the full text.

## Extension Rules

### 1. New Subsystem Declaration

Any new subsystem must explicitly declare its resource and semantic boundaries in its
contract documentation. Required fields: authoritative status, resource budget, retention
policy, and degradability profile.

### 2. TDD Extension Loop

All new features must follow: Contract Test → Minimal Implementation → Scenario Test →
Certification. No implementation may precede a contract definition.

### 3. State Management Laws

Only state required for deterministic simulation belongs in `AuthoritativeState`. All
durable mutations must flow through the authoritative apply path.

## Project Guardrails

- **Unbounded Collections**: No list or dict may grow without a defined `max_size`.
- **Alternate Authority**: No side-channel state may influence simulation outcomes.
- **Honest Language**: All performance metrics must be bound to `(Profile, Scenario, Hardware Class)`.
- **Ad-hoc Threading**: Concurrency must be managed by the Scheduler and WorkerPool.

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
