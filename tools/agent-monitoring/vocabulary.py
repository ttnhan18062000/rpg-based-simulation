"""
Canonical phase/agent/tier vocabulary for agent-monitoring writers and validators.

Single source of truth — record_events.py's warn-only vocabulary check and
validate.py's drift-report both import from here. Do not duplicate these sets
elsewhere (see tests/tools/test_validate_agent_monitoring.py's single-source
guard, TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT).

Every phase/agent value below was confirmed by grepping each workflow's actual
`phase(...)`/`pushEvent(...)` call sites in `.claude/workflows/*.js` — not
copied from docs/agent-monitoring/schema.md's prose tables, which were already
found to be stale (missing simq-audit's workflow entirely, and missing
implement-ticket's Architecture-Verify phase) before this module was written.
"""

CANONICAL_TIERS = {"hotfix", "standard", "epic", "n/a"}

# Keyed by workflow name. Built from each workflow's actual phase(...)/pushEvent(...)
# call sites (grepped directly), not from schema.md's already-drifted prose tables.
WORKFLOW_PHASES = {
    "implement-ticket": {
        "Scope", "Investigate", "Plan", "Review", "Implement", "Architecture-Verify",
        "Document-Update", "Test", "Parity", "Security-Review", "Verify", "Finalize",
    },
    "create-tickets": {"Comprehend", "Investigate", "Structure", "Write", "Link"},
    "implement-epic": {"Implement"},
    "simq-audit": {
        "Recalibrate", "Classify Drift", "Update Anchors", "Sync Docs",
        "Parity Check", "Verify", "Report",
    },
}

# Keyed by workflow name. Includes both .claude/agents/*.md subagent filenames
# actually invoked by that workflow AND legitimate orchestrator pseudo-agent
# names (e.g. 'workflow', 'implement-ticket-orchestrator') — these are NOT
# drift, they are the orchestrator itself logging an event with no delegated
# subagent. Confirmed by grepping every pushEvent(...) call site in each
# .claude/workflows/*.js file.
WORKFLOW_AGENTS = {
    "implement-ticket": {
        "ticket-scoper", "investigator", "planner", "architecture-reviewer",
        "implementer", "doc-updater", "test-scoper", "parity-updater", "security-reviewer",
        "done-checker", "finalizer", "implement-ticket-orchestrator",
        # "claude": the real, dominant hand-orchestration literal (45 of ~91 non-standard
        # agent values in events.jsonl history, confirmed via direct query) -- used when a
        # session runs implement-ticket.js phases directly with no subagent dispatch (e.g.
        # after the subagent spawn cap is reached), same category as the
        # "implement-ticket-orchestrator" pseudo-agent above: a real orchestrator identity
        # logging its own event, not drift (TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION).
        "claude",
    },
    "create-tickets": {"create-tickets", "structure", "ticket-scoper", "link-epic"},
    "implement-epic": {"implement-ticket"},
    "simq-audit": {
        "workflow", "drift-classifier", "anchor-updater", "doc-syncer",
        "parity-updater", "done-checker", "ticket-scoper",
    },
}

# create-tickets.js's Investigate phase invokes one ticket-scoper-style subagent
# per concern with a dynamically built label `investigate:${concern.id}`
# (create-tickets.js's pushEvent('Investigate', `investigate:${inv.concern_id}`, ...)
# call site) — a stable literal *prefix* family, not a fixed set of literals, so
# it cannot be enumerated in WORKFLOW_AGENTS without producing one spurious
# warning per distinct concern_id ever seen. This is the same "legitimate,
# confirmed-by-grep, not a guess" category as the orchestrator pseudo-agent
# names above, just prefix-shaped instead of a fixed literal.
WORKFLOW_AGENT_PREFIXES = {
    "create-tickets": ("investigate:",),
}


def is_known_agent(workflow: str, agent: str) -> bool:
    """True if `agent` is a recognized literal or prefix-family member for `workflow`."""
    if agent in WORKFLOW_AGENTS.get(workflow, set()):
        return True
    return any(agent.startswith(prefix) for prefix in WORKFLOW_AGENT_PREFIXES.get(workflow, ()))


def infer_workflow(run_id: str) -> str | None:
    """Infer which workflow produced a run_id, from its prefix.

    Confirmed disjoint prefixes (read directly from each workflow's .js file's
    run_id-construction code, not guessed):
      - simq-audit.js:125       runId = 'SIMQ-AUDIT-' + ...
      - implement-epic.js:216   batchRunId = 'EPIC-' + epicId | 'FOLDER-' + folder...
      - create-tickets.js:98    runId = 'CREATE-TICKETS-' + sourceSlug
      - implement-ticket.js     run_id is the literal ticket_id, 'TCK-...'

    Returns None if run_id matches no known prefix (e.g. a future 5th workflow) —
    callers must treat None as "skip the check silently," never as an error.
    """
    if run_id.startswith("SIMQ-AUDIT-"):
        return "simq-audit"
    if run_id.startswith("EPIC-") or run_id.startswith("FOLDER-"):
        return "implement-epic"
    if run_id.startswith("CREATE-TICKETS-"):
        return "create-tickets"
    if run_id.startswith("TCK-"):
        return "implement-ticket"
    return None
