# Implementation Sequence — session-layer-followups

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-10 by lead-planner as a handoff to the agent-working
seats. agent-working-planner may re-scope or re-order; these are findings, not a dispatch.

## Order

Items 1-4 landed in PR #506 (batch 1, 2026-10-11): TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED,
TCK-20261011-PR-ATTRIBUTION-OFF-AT-SOURCE, TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE,
TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES. Batch 2 (2026-10-11) is the two items below plus
`agent-working/tickets/todos/session-lead/SEQUENCE.md` items 1-2, in one batch PR.

1. TCK-20261011-GRAPHIFY-TOOLS-OWNED  (no deps; hotfix; manifest edit)
2. TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD  (no deps now; standard; includes placements outside .claude/worktrees)

Batch 3 (2026-10-12, issues #520 and #517), one batch PR:

3. TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS  (no deps; hotfix; verify on u24desktop; lead reviews the Makefile diff)
4. TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD  (no deps; standard; .mcp.json unchanged)
