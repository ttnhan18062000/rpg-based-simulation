---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE
artifact_type: investigation
tags: [observability]
---

# Investigation — TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE

Finding: `tools/calibrate_simq.py` already replayed `simulation_events.jsonl` through a fresh `QualityHub` (`_replay_jsonl_through_hub`), but the replay dropped `related_entity_ids`, returned 0 events for a missing file and wrote a wall-clock `generated_at`. `tools/simq_long_run_observation.py` reused the private helpers; the compare/anchor tools (`evaluate_simq`, `simq_reanchor`, `simq_audit_rows`) read calibration output. The live feed (in-process worker and broker consumer) calls `hub.on_envelope` directly. Scorers do not read `related_entity_ids` (grep of src/simulation_quality). The file is written by `EventRecorder._write_envelope_to_file` from the same envelopes the live worker receives.

docs_to_update: none (no mechanic or contract changed; the divergence is the report's `generated_at`, recorded in the ticket).
