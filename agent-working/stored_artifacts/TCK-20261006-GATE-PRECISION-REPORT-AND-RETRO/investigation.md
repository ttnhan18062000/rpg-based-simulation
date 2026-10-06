---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation
The retro already has a fail-soft pattern for a section with its own data source (`_session_layer_section`) and a dark-instrument wording in `session_layer_report._dark`; the Gates section reuses both shapes rather than adding a new one. `retro_provenance.py` is about duration provenance and has nothing to share. The n < 5 cut-off comes from the ticket as a starting value (`agent_evaluation_foundation_experiment.md:92`: do not claim more than the adjudicated rows support).
