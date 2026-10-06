---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: rpg

Source of the rpg part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: rpg (simulation, Bible, parity ledger). `rpg-planner` owns the semantic-control-plane epic and `mechanisms.yaml` content; ask it before changing RPG logic, RPG test expectations or Bible/parity semantics. Only it messages rpg implementers; send briefs and parked branches to it.

## Provenance

Owner rule 2026-10-05, narrows the designer template's "finding/fyi/ack to anyone" for the rpg domain; dispatch is already enforced by `accepts_dispatch_from`.
