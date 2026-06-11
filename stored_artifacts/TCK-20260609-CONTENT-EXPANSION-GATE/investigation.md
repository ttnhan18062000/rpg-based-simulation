---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260609-CONTENT-EXPANSION-GATE
artifact_type: investigation
tags: [content, expansion, gate]
---


# Investigation

12 gate conditions identified. Items requiring WorldAssemblyResolver.assemble() will xfail
due to CAT-REL-099. Correct field names from schema inspection:
- ContentFamilySpec.repository_index (not .attr)
- SimulationScenarioDefinition fields: id, world_composition, perspective (not *_id suffix)

Current baseline: 11 pass, 1 xfail. Gate passes — expansion may proceed.
