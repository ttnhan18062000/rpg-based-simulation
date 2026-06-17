---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [domains, information, belief, trust, contract]
---

# Information Domain Contract

**Source:** `src/domains/information/` (10 files)  
**Pipeline phase:** the Information / Belief Processing stage  
**Authoritative status:** NOT authoritative — reads state, returns typed update records.

---

## Purpose

The information domain manages an entity's belief system: how new information is received, validated against existing knowledge, assimilated or contradicted, and how source trust is updated over time. It bridges the runtime simulation to `src/core/strategic` types (`KnowledgeFact`, `LeadState`, `SourceTrustEntry`, `BlockerState`).

---

## Information Source Kinds

`InformationSourceKind` enum: `GUIDE`, `GUILD`, `BLACKSMITH`, `TRAVELER`. Used to weight initial trust for a new information source.

---

## Sub-Service Contracts

### assimilation.py — Belief Assimilation
Receives new information (a `KnowledgeFact`) and current entity knowledge state. Returns an assimilation record: whether the fact was accepted, partially accepted, or rejected (contradicted).

### trust.py — Source Trust Update
`SourceTrustUpdateService.update(entity, source_entity_id, outcome, current_tick)`

- Outcomes: `CONFIRMED`, `PARTIALLY_CONFIRMED`, `CONTRADICTED`, `NOT_VERIFIABLE`
- Trust values are clamped to `[0.0, 1.0]` — never exceed bounds
- Adjustments are **gradual** — no single outcome causes a full trust flip
- Returns updated `SourceTrustEntry` — caller applies it; this service does not write to state

### contradiction.py — Contradiction Detection
Compares a new `KnowledgeFact` against existing entity knowledge. Returns a contradiction record if the new fact conflicts with a known fact. Contradiction records are passed to the pipeline — entity may update beliefs or flag the source as unreliable.

### normalizer.py — Information Normalisation
Normalises raw information (cleans, deduplicates, standardises format) before assimilation. Input: raw data from perception or NPC interaction. Output: normalised `KnowledgeFact`.

### router.py — Information Router
Routes an incoming information event to the appropriate processor (assimilation, contradiction, or trust update) based on the information kind and source. Single entry point for the Information / Belief Processing pipeline call.

### bridge.py — Core Strategic Bridge
Translates domain-level results into `src/core/strategic` types (`LeadState`, `BlockerState`). Keeps the domain decoupled from the core state schema.

### route_impact.py — Route Impact Assessment
Evaluates how new geographic or entity information impacts known routes and travel plans.

---

## Trust Propagation Rules

1. Trust starts at a source-kind-dependent initial value (GUILD > BLACKSMITH > TRAVELER > GUIDE for most entity types).
2. Each `CONFIRMED` outcome increases trust by a small delta (implementation-defined, configurable).
3. Each `CONTRADICTED` outcome decreases trust by a larger delta (contradictions are weighted more).
4. `NOT_VERIFIABLE` outcomes have no effect on trust.
5. Trust is clamped to `[0.0, 1.0]` after every update.
6. Trust is per `(entity, source_entity_id)` pair — not global.

---

## Knowledge Assimilation Constraints

- An entity only assimilates facts from sources whose trust ≥ the entity's assimilation threshold.
- Contradicted facts are not assimilated; they are marked as `CONTRADICTED` in the belief record.
- Facts with `UnknownFact` status are placeholders; they do not count as confirmed knowledge.

---

## Authoritative Pipeline Integration

The Information / Belief Processing stage calls `router.py` for each entity that received information events this tick. The router dispatches to assimilation, contradiction, and trust update services. Results are returned as typed records to the pipeline for application. The domain does not write to `AuthoritativeState`.

---

## Constraints

- Must not import from other domain packages.
- Trust values must always be clamped to `[0.0, 1.0]` — never store raw deltas.
- `KnowledgeFact` and `SourceTrustEntry` are immutable core types — return new instances, do not mutate.
