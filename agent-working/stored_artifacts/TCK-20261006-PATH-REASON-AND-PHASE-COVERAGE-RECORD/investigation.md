---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation
The run row is written by `record_run.py --data` in both paths (the pipeline through its monitoring agent's Step 3, the hand tool through `build_records`), so the run fields are optional keys on that record with enum checks in `validate_record`. `implement-ticket.yaml` marks Document-Update `full` for hotfix too, and the usual six-phase hand hotfix shape does not log it; with the plan as the source that shows as `phases_omitted: [Document-Update]`. That is the reading working, left for the report, not special-cased. The pipeline writes its run row through an agent prompt that cannot import Python, so `phases_omitted` goes through a small CLI (`path_record.py --tier --phases`) the prompt runs.
