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

Host-ubuntu twins `rpg-designer-ubuntu`, `rpg-planner-ubuntu`, `rpg-implementer-ubuntu` (TCK-20261025-RPG-UBUNTU-SEATS): until the owner and `rpg-planner` agree a lane split through `lead-planner-u24`, they take no work, no ticket filing and no dispatch, and every future ubuntu rpg dispatch posts a claim on #634 first. The card line above ("Only it messages rpg implementers") conflicts with `Dispatch from: rpg-planner-ubuntu` on the ubuntu implementer's card; it is left unchanged and resolved with the lane split.
