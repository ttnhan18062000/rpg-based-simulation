---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE
artifact_type: test_plan
tags: [agent-monitoring, data-quality, hooks]
---

# Test Plan — TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE

In `tests/tools/test_monitoring_batch_identifier.py`, new section:

1. `test_reflog_recovers_real_branch_and_seeds_sidecar`
2. `test_reflog_all_sha_moves_falls_through_to_detached`
3. `test_reflog_absent_falls_through_to_detached`
4. `test_reflog_names_deleted_branch_still_used_not_validated`
5. `test_attached_head_short_circuits_before_reflog_is_consulted`
6. `test_detached_no_sidecar_no_reflog_still_reaches_detached_sha_with_warning`
7. `test_resolve_write_target_end_to_end_uses_reflog_recovered_branch`

Existing tests in that file re-run unmodified (AC3).
