---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71
artifact_type: investigation
tags: []
---

# investigation — TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71

- Baseline probe (frontier_living_world and urban_political, seeds 42-46, 5000 ticks, 10 runs): 0 conquests, 0 liberations, 0 strongholds; lowest influence -15 (bandit_road, unowned); owned regions +80 to +130. The step is dormant in the baseline.
- The designer's "-50" assumed no recovery path; `LIBERATION_THRESHOLD = +50` already exists for an invader-owned region. rpg-planner ruled to keep +50.
- A second ownership writer (`engine/world_dynamics.py`) flips on the same two lines and is untouched.
- The Aura of Despair read (`world/environment.py`) still looks for stronghold-kind entities.
- docs_to_update: docs/mechanics/05_world_evolution.md, docs/guidelines/intentional_divergences.md, docs/parity_ledger/progression.yaml.
