---
name: CompactSimulationResult
description: Compact heavy log files and archive unnecessary telemetry outputs from past runs.
allowed_actions:
  - scan_telemetry_logs
  - filter_event_logs
  - write_compact_json
  - archive_raw_payloads
forbidden_actions:
  - delete_without_compaction
  - purge_all_history
input_schema:
  mode: "generic | specific"
  session_id: "string"
output_artifacts:
  - registration/runs/{run_id}/compact_event_log.json
---

# CompactSimulationResult Workflow
Detailed steps for result compaction...
