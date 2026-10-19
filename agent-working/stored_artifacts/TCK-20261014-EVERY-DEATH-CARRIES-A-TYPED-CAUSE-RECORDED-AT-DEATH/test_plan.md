---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH
date: 2026-10-15
tags: []
---

# Test Plan: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH

Written at close. Unit: DeathRecord per cause (old age, killing hit, starvation with a remembered attacker, hazard with its region hazard kind), the authoritative apply and the canonical state, round trip, merge, last-attacker semantics (damaging hit only; no recency). Observer: each hp loss source, unattributed, deaths tallied once, silent when not live. Projection helper test. Behaviour neutrality: base 7888c5457 vs branch, 3 worlds, seed 42, 5000 ticks, audit_mode, PYTHONHASHSEED=0: projected digests, alive/dead/cause counts and movement_count identical; every dead body has a record. Sweep of core, engine, progression, observability, kernel, combat, lab, resource, kernel integration, certification.
