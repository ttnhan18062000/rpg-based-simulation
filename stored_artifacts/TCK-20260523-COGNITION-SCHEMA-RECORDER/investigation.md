# investigation.md - Exporter & Strategic Components

The existing `CognitionGraphExporter` defined in `src/systems/strategic_systems/cognition_export.py` exposes:
- Directives
- Projects
- Objectives
- Blockers
- Leads
- Concerns
- Hypotheses
- Metadata (current project/objective ID, overload source, and limits profile).

This is read-only and does not mutate strategic state. Our snapshot schema must align with these fields, mapping `entity.id`, `tick`, and trigger `reason` perfectly.
