---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
artifact_type: plan
tags: [agent-monitoring, process-improvement, hooks]
---

# Plan — TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP

## Steps

1. **`.claude/settings.json`**: add a new `PreToolUse` entry, matcher `Edit|Write`, implementing the case-statement hook from investigation.md (path-scoped to `tickets/`, `staging_artifacts/`, `src/`, `tests/`, `docs/`; fires only when `tickets/inprogress/*.md` exists AND `.claude/current_run`'s `run_id` is empty/missing).
2. **`.claude/skills/implement-ticket/SKILL.md`**: add an explicit row to the JS→tool translation table naming `writeSidecar(seq, phase, agent)` directly — not just relying on the generic "orchestrator-run bash()" row — so it's visible on a skim, not just implied.
3. **`.claude/skills/implement-epic/SKILL.md`**: check whether it needs the same explicit mention (it delegates to implement-ticket's own pipeline per-child-ticket, so likely inherits the fix without its own edit — confirm during Implement, add only if the epic skill has its own separate phase-translation prose that also omits it).
4. No production Python code changes. No `record_events.py`/`compute_tool_stats()` changes (explicitly out of scope).

## Architecture self-check (architecture-reviewer agent unavailable this run — session-wide subagent spawn cap of 200 reached; performing the equivalent check directly instead of skipping it)

- **Durable state**: `.claude/current_run` and `.claude/settings.json` are both local orchestration/session config, not durable simulation/world state — no entity/world/registry model involved. N/A.
- **API boundaries**: no `src/api/` touched. N/A.
- **Authoritative mutation path**: N/A — no gameplay-affecting code touched.
- **Reason-string/metadata durable-meaning rule**: the hook's `additionalContext` string is ephemeral prompt-injection text, never persisted to `tools.jsonl`/`events.jsonl` — not durable state. N/A.

No architecture concerns identified. Low blast radius: a hooks-config JSON edit and two doc-prose edits, both easily reverted (hooks are read fresh each tool call, no caching/migration concern).

## Acceptance-criteria map

| AC | Step |
|---|---|
| investigation.md confirms sidecar shape + evaluates false-positive risk | Investigate (done) |
| concrete mitigation implemented | Steps 1-2 |
| real-kernel-adjacent verification: non-null run_id on a fresh hand-orchestrated run | This ticket's own remaining sidecar writes this session, plus tickets 2-5 |
| no backfill attempted | Confirmed in Completion Summary |
| scoped pytest passes (if hook/code change made) | Test phase: `tests/tools/test_post_tool_hook.py`, `test_codex_hook_payload_fixture.py`, `test_workflow_meta_conformance.py` |
