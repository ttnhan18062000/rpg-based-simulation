# Implementation Sequence — session-layer-followups

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-10 by lead-planner as a handoff to the agent-working
seats. agent-working-planner may re-scope or re-order; these are findings, not a dispatch.

## Order

Re-ordered 2026-10-11 by agent-working-planner. Batch 1 = items 1-4; batch 2 = item 5 (plus Epic E's E4).
Items 1 and 4 touch `tools/sessions/session_start_hook.py` / `launch.py`, like PR #491: start them only
after #491 is merged and the batch branch is based on that main.

1. TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED  (no deps; hotfix; manifest edit)
2. TCK-20261011-PR-ATTRIBUTION-OFF-AT-SOURCE  (no deps; hotfix; issue #495; governing file)
3. TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE  (depends on: PR #491 merged; hotfix; live on host ubuntu)
4. TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES  (depends on: 3; standard; issue #498)
5. TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD  (depends on: 3; next batch)
