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
        # "orchestrator": TCK-20260915-MONITORING-ANOMALY-VALIDATOR found this flagged as "drift"
        # at 401 occurrences spanning 2026-06 through 2026-09 (still actively used) -- an even
        # larger, longer-running instance of the exact same "claude" pattern above: a
        # hand-orchestrating session's own natural label for a phase it performed directly, not a
        # delegated subagent. Not grep-confirmed from a workflow .js file (impossible -- it is by
        # definition never emitted by the automated pipeline), verified instead by direct
        # corpus-usage-pattern investigation, the same evidentiary standard this epic used
        # throughout. Registering it here (rather than ratcheting it as an anomaly) is the correct
        # fix: a 4-month-old, still-growing, self-describing convention is a registry gap, not a
        # defect.
        "orchestrator",
        # "context-packet-wrapper": the advisory shadow context-packet call site's own agent
        # literal (TCK-20260729-SHADOW-PACKET-CALL-SITE), grep-confirmed at
        # .claude/workflows/implement-ticket.js:632 (`e.get('agent') == 'context-packet-wrapper'`)
        # -- a real, intentional, already-documented mechanism (see docs/agent-monitoring/schema.md's
        # seq field row), not drift.
        "context-packet-wrapper",
        # "implement-ticket": 138 events under a TCK-* (implement-ticket) run_id record their own
        # agent literally as "implement-ticket" -- the workflow's own name used as a
        # self-referential "the orchestrator of this workflow did it directly" label, semantically
        # the same concept as "orchestrator"/"claude" above, just spelled after the workflow
        # instead of describing the role generically. Registered for the same reason.
        "implement-ticket",
        # "architecture-reviewer-shadow": the shadow-reviewer mechanism's own agent literal for
        # the Architecture-Verify phase's advisory candidate-model call, grep-confirmed at
        # .claude/workflows/implement-ticket.js:1074/:1099. Originally built opt-in behind
        # SHADOW_REVIEWER_LOGGING_ENABLED by TCK-20260904-SHADOW-REVIEWER-LOGGING;
        # TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON flipped it to opt-out/default-on,
        # which is what turned this from occasional to every-ticket volume and pushed the real
        # corpus count over AGENT_DRIFT_CEILING. Registered here by
        # TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP -- a real, intentional, already-documented
        # mechanism (see docs/agent-monitoring/schema.md's Shadow-reviewer-event field family
        # section), not drift.
        "architecture-reviewer-shadow",
        # "security-reviewer-shadow": the same shadow-reviewer mechanism's agent literal for the
        # Security-Review phase's advisory candidate-model call, grep-confirmed at
        # .claude/workflows/implement-ticket.js:1519/:1539. Same origin/registration history as
        # "architecture-reviewer-shadow" above -- TCK-20260904-SHADOW-REVIEWER-LOGGING (opt-in),
        # TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON (opt-out/default-on), registered here
        # by TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP.
        "security-reviewer-shadow",
    },
    "create-tickets": {
        "create-tickets", "structure", "ticket-scoper", "link-epic",
        # "concern-investigator": TCK-20260915-MONITORING-ANOMALY-VALIDATOR found this flagged as
        # drift under create-tickets.js's own CREATE-TICKETS-* run_ids -- the real, documented
        # subagent for that workflow's Structure phase (see .claude/agents/concern-investigator.md's
        # own description: "returns structured JSON findings for create-tickets.js's Structure
        # phase"), simply missing from this registry until now. One further occurrence under a
        # single historical TCK-prefixed run (TCK-20260709-CONCERN-INVESTIGATOR-AGENT, a
        # one-off ticket about building this very agent) is left as accepted residual drift, not
        # registered under implement-ticket -- it was never a repeating pattern there.
        "concern-investigator",
        # "orchestrator": same hand-orchestration pseudo-agent convention registered under
        # implement-ticket above, also found under CREATE-TICKETS-* run_ids (3 occurrences) --
        # same mechanism, different workflow.
        "orchestrator",
        # "write-sequence": create-tickets.js's Write phase's own writeSidecar()/pushEvent label,
        # grep-confirmed at .claude/workflows/create-tickets.js:844
        # (`await writeSidecar(events.length + 1, 'Write', 'write-sequence')`) and :856
        # (`{ label: 'write-sequence', phase: 'Write' }`) -- one of the 4 real, documented
        # writeSidecar call sites named in docs/agent-monitoring/schema.md (comprehend, structure,
        # write-sequence, link-epic). A real, intentional label, not drift.
        "write-sequence",
    },
    "implement-epic": {
        "implement-ticket",
        # "implement-epic": 16 events under a FOLDER-*/EPIC-* run_id record their own agent as
        # "implement-epic" -- the same self-referential workflow-name-as-agent-label pattern
        # registered for "implement-ticket" above, just for this workflow's own batch/epic runs.
        "implement-epic",
    },
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
