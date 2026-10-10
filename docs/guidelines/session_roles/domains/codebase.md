---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: codebase

Source of the codebase part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: codebase (code health: Python code standard, gates, baselines, code-craft roadmap). The planner holds roadmap direction and reviews batch PRs; `HOLD` work stays held until the user approves. Gates ratchet, never loosen. `test.yml` is testing's: edit our jobs only per decision 8.11, with a notice. Ask `rpg-planner` before touching RPG logic.
