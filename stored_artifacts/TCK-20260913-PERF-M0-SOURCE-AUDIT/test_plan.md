---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260913-PERF-M0-SOURCE-AUDIT
date: 2026-10-02
tags: [performance, architecture]
---

# Test Plan: TCK-20260913-PERF-M0-SOURCE-AUDIT

No code is changed, so there is no pytest surface (the ticket says verification is manual and
registry-tooling-based).

1. Inventory table is reproducible: rerun the existence/tracked/registry script over the cited
   paths; every row must match the table.
2. Diff scope: `git status --short` and `git diff --stat` show only `tickets/`, `staging_artifacts/`,
   `stored_artifacts/`, `docs/REGISTRY.yaml` and `agent-monitoring/` for this ticket's own changes
   (the planner's separate plan-doc edits are expected and not mine).
3. `python3 tools/validate_frontmatter.py` on the ticket and the four artifacts.
4. `python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260913-PERF-M0-SOURCE-AUDIT`
   at close.
5. Mechanism-registry advisory at close (report-only).
