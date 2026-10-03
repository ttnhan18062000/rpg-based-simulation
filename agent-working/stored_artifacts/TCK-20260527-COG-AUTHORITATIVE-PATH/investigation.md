---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-AUTHORITATIVE-PATH
artifact_type: investigation
tags: [cog, authoritative, path]
---

# Investigation: Authoritative Strategic Path

Our investigation confirmed:
1. `CognitionDomain.execute_brain()` is triggered when `ENTITY_BRAIN` work is processed. It returns only emotional appraisals and tactical intents (setting `strategic=None`), making it read-only regarding strategic updates.
2. `StrategicIntelligenceSystem.fused_strategic_pass()` runs in Phase 7 of the tick pipeline. It manages strategic projects, goals, detours, and capacity trimming.
3. This completely splits strategic brain power (authoritative planning) from tactical execution. 

We will document these system boundaries in the code and add robust verification tests.
