---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65
artifact_type: plan
phase: done
date: 2026-10-12
tags: []
---

# plan: TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65

Add `src/engine/natural_healing.py` (one table, `heal_period`, `hp_gain`) and one call in the life-due branch of `ApplyPath._compute_entity_changes`. Rate 1 HP per round(9600/max_hp) ticks awake, round(4800/max_hp) asleep or resting; none at hunger >= 95; period doubled while weakened by hunger or sleep debt. No new state. Docs: Bible 01 paragraph, divergence 2.116, parity PROG-131, mechanisms note. Measure paired against rpg-single-pr before baseline v1.
