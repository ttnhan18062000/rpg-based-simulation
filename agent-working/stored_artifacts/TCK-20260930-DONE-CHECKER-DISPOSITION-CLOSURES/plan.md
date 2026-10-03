---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES

1. `tools/ticket_field_values.py`: `DISPOSITION_VALUES`, `has_body_section`,
   `check_disposition_rationale`, `check_disposition_fields`; `check_ticket_field_values` appends
   the disposition result only when a `## Disposition` exists (single-item return shape kept).
2. `tools/gate_checks/done_checker_static.py`: `_disposition_migration_result` consulted first by
   `check_migration_complete`; `check_registry_entry_regenerated(regenerate=True)` with read-only
   mode; `run_finalize_selfcheck(regenerate_registry=True)`; CLI `--regenerate-registry`.
3. `docs/guides/delivery_process.md`: one Disposition subsection plus the read-only CLI note.
4. Tests in `test_ticket_field_values.py` and `test_done_checker_static.py`.
5. Scope 5: once rpg-feature-planning adds both sections to its two closures, run the checker
   against those tickets' content and record the result in the ticket.
