---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH
date: 2026-10-15
tags: []
---

# Plan: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH

Written at close. rpg-planner approved (A) an observability ledger for the typed source of every hp loss and (B) a durable DeathRecord on LifecycleComponent written only by resolve_lifecycle through LifecycleUpdate.death_record_set, plus CombatComponent.last_attacker_id written by the combat patch. Both new fields sit in the canonical state; the step is proven behaviour-neutral by projection, not by leaving them out of the fingerprint. No last_attacker_tick (the combat patch has no tick; no reader needs it).
