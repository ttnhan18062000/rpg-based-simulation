# RPG Engine: Unsupported Logic Register

This document tracks legacy RPG logic that is explicitly NOT supported in V2. Every row in the logic checklist marked as `UNSUPPORTED` must link to an entry here explaining why the behavior is omitted.

## Unsupported Entries

### UNS-001: Legacy Sound Trigger System
- **Law**: `RPG-INFRA-NNN`
- **Rationale**: V2 is a headless logic engine. Audio triggers are the responsibility of the presentation layer/frontend.
- **Status**: DROPPED

### UNS-002: Direct Memory Mutation Exploits
- **Law**: `RPG-AUTH-NNN`
- **Rationale**: Legacy engine allowed direct memory access for certain "magic" effects. V2 enforces authoritative state boundaries; all effects must flow through `StateUpdate`.
- **Status**: DROPPED

### UNS-003: Permadeath Succession and Heirlooms
- **Law**: `RPG-LIFE-NNN` (Task 10.3)
- **Rationale**: V2 focuses on the deterministic simulation kernel. Succession and narrative legacy are high-level meta-game concepts better handled by a campaign manager or world-manager layer.
- **Status**: OUT_OF_SCOPE

### UNS-004: Nemesis Milestone Creation
- **Law**: `RPG-SOC-NNN` (Task 10.4)
- **Rationale**: While social state is tracked, the automatic generation of "narrative milestones" is a meta-logic feature that depends on non-deterministic event tagging. V2 provides the state hooks but does not implement the milestone generation logic.
- **Status**: OUT_OF_SCOPE
