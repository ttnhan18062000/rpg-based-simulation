# Investigation: Phase 5 — Information / Belief / Source-Trust Loop

This document outlines codebase findings, data structures, and architectural bounds relevant for Phase 5.

## Core Findings

- **Source Trust**: Attachment is mapped via `StrategicComponent.source_trust` as `SourceTrustEntry(entity_id, trust, interactions, last_outcome)`. We will adjust these values directly.
- **Knowledge facts**: `KnowledgeModelComponent` under `SelfModelBundle` holds `facts` and `unknowns` keyed by string subjects.
- **Leads & certainty**: Clues are mapped as `LeadState(id, kind, subject, detail, discovered_tick, certainty)`. Certainty is `LeadCertainty` (VAGUE, APPROXIMATE, PRECISE, EXHAUSTED).
- **Phase 3 Route scoring integration**: Phase 3 scorer evaluates route choices. We will feed impact hints or strategic updates (e.g. resolving material blockers or adding high-certainty resource leads) to naturally redirect route scorers.
