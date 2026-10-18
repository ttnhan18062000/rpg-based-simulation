---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT
date: 2026-10-16
tags: []
---

# Plan: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT

Read-only inventory (owner decision 80 (i)); no source change.
1. Static scan (AST) of every SimulationEvent construction, typed event class, factory call and event-type helper under src/: producer file:line, category, severity, source_system, payload keys, enclosing gates.
2. SimQ side: scorer EVENT_TYPES after quality_hub._translate (including the payload-conditional translators' outputs).
3. Measure: 3 worlds x seeds 42-46 x 5000 ticks, observability FULL, audit_mode, PYTHONHASHSEED=0; per-type counts from the recorder counter (taken before any filter), a kernel listener and the event file, with sampling evidence per run.
4. Render one table plus four flag sections and a per-seed TSV into the stored artifact.
