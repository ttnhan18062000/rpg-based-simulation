---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan
1. `vocabulary.py`: `PATH_REASONS`, `SKIP_REASONS`.
2. New `path_record.py`: `phases_omitted(tier, recorded)` reads the `full` phases of the tier from `implement-ticket.yaml` at write time (`None` when the file cannot be read, so the field is left off rather than written as a false `[]`).
3. `record_run.py` / `record_events.py` validate the three fields; `validate.py` flags unknown stored values.
4. `record_hand_orchestrated_closure.py`: `--path-reason` (default `unstated`, one stderr hint), `--path-note` (required for `other`), `phases_omitted` computed from the events, `skip_reason` default `unstated` on a skipped event.
5. `implement-ticket.js`: `path_reason: pipeline_default` on the run write, `phases_omitted` through `path_record.py` in the monitoring step, `tier_plan` / `condition_false` on its skip sites.
6. Docs: `schema.md`, `monitoring-schema.yaml`; the CLAUDE.md closure example (owner approved the literal diff).

## Unresolved Questions

None.
