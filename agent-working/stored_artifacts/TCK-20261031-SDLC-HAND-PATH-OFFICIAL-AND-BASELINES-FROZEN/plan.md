---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN
artifact_type: plan
tags: [ai, governance, delivery]
---

# Plan: hand path official, path_note for owner_directed, baselines frozen

1. Add `PATH_REASONS_NEEDING_NOTE = ("other", "owner_directed")` to `tools/agent-monitoring/vocabulary.py`; use it in `record_run.py::_optional_field_errors` and the closure CLI check in `record_hand_orchestrated_closure.py`.
2. Tests: validator refuses a noted reason with a missing or empty note; other reasons need none; the CLI refuses `owner_directed` with no or blank note and writes nothing; an old row without a note still passes `validate.py::check_path_record`.
3. Docs: define each `path_reason` in `docs/agent-monitoring/schema.md` and align `monitoring-schema.yaml`; add section 7.1 to `session_layer_working_process.md`; add `SDLC_DECISION_RECORD.md` and `SDLC_BASELINES_FROZEN.md`.
4. Do not edit CLAUDE.md or settings; report that the closure example now misleads.
5. Run the scoped tests; the full `tests/tools` run waits for a lead slot.
