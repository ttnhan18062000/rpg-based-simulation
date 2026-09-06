#!/usr/bin/env python3
"""SubagentStop/Stop hook: blocks a turn from ending while background work is still in flight.

TCK-20260904-TEST-SCOPER-HANG-GUARD: CLAUDE.md's own prose Hard Rule ("never end your turn
while your own run_in_background command is still running") recurred as a real failure mode
four times despite being propagated verbatim to 16 agent role files. This script is the
deterministic enforcement the epic's guardrail_enforcement_epic.md M3 milestone requires.

Field names below are NOT guessed. This ticket's Step 1 spike found both live-capture avenues
(a nested `claude` invocation, and a throwaway `.claude/settings.local.json` diagnostic hook
registered against a real dispatched subagent) blocked by this sandbox's own auto-mode
classifier -- so the real payload shape was instead extracted directly from the installed
Claude Code binary's own zod validation schema and control-flow code (version 2.1.261, see
tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.json for the exact byte-offset
citations). That extraction is the literal, currently-enforced contract every real
Stop/SubagentStop payload must satisfy -- stronger evidence than a single live-fired example,
since it is the schema that PRODUCES every instance, not one instance of it.

The harness's own schema already carries a `background_tasks` array (populated from a live
per-session task registry, not reconstructed from transcript text) describing exactly this:
"In-flight background work (running/pending + backgrounded) registered in this session. Lets
hooks distinguish 'session is done' from 'session is paused waiting for background work to wake
it'. Empty array when nothing is in flight." This makes a transcript-JSONL-parsing heuristic
(the architecture investigation.md/plan.md hypothesized before this evidence existed)
unnecessary: this script reads payload["background_tasks"] directly instead.

The harness computes this same `background_tasks` value identically for both `Stop` and
`SubagentStop` (one shared expression feeds both branches in the real control-flow code) -- it
is a session-scoped signal by the harness's own design, not scoped to one particular subagent.
A universal, unfiltered check (matching plan.md's Summary decision #1: no agent_type filtering)
is therefore the intended usage of this field, not an approximation of it.
"""
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

try:
    stop_hook_active = bool(payload.get("stop_hook_active"))
    background_tasks = payload.get("background_tasks") or []
    if not isinstance(background_tasks, list):
        background_tasks = []
except Exception:
    sys.exit(0)

if stop_hook_active:
    # Harness's own documented intent (confirmed in the binary's control-flow code, see module
    # docstring): a Stop/SubagentStop hook must return success while stop_hook_active is true,
    # or it risks hitting the harness's own consecutive-block cap
    # (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP) instead of a clean allow.
    sys.exit(0)

if not background_tasks:
    sys.exit(0)

try:
    pending_descriptions = [
        (task.get("description") or task.get("command") or task.get("id") or "unnamed task")
        for task in background_tasks
        if isinstance(task, dict)
    ]
    reason = (
        "Turn ending while background work is still in flight: "
        + "; ".join(pending_descriptions)
        + ". Poll it to completion (or wait in the foreground) before ending your turn -- see "
        "CLAUDE.md's Hard Rules and this agent's own Background Commands section."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
except Exception:
    pass

sys.exit(2)
