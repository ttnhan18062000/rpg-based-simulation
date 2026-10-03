---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-SCHEMA-RECORDER
artifact_type: plan
tags: [cognition, schema, recorder]
---

# plan.md - Schema & Recorder Plan

Define the JSON schemas and trigger policy for entity strategic cognition snapshots.

## Key Actions
1. Implement schema definition for `cognition_graph_snapshots.jsonl` in `src/observability/cognition/schema.py`.
2. Define the trigger policies (`CognitionCapturePolicy`) deciding *when* a snapshot should be taken based on specific anomaly events (like quest stalls, navigation stuck, resource drops) or strategic updates (like current project or objective swaps).
3. Build the read-only snapshot recorder (`ObservabilityCognitionRecorder`) utilizing `CognitionGraphExporter`.
4. Register the recorder hook in the post-commit observability cycle.
