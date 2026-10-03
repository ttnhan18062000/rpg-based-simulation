---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260709-CONCERN-INVESTIGATOR-AGENT
phase: done
date: 2026-07-09
tags: []
---

# TCK-20260709-CONCERN-INVESTIGATOR-AGENT

## Title
Add a dedicated, tool-scoped agent for create-tickets.js's pre-ticket Investigate phase

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`.claude/workflows/create-tickets.js`'s Investigate phase (the step that runs per-concern, before any ticket file exists, to gather file paths/constraints/AC signals feeding the Structure phase) currently dispatches `Agent(subagent_type: "general-purpose", ...)` with the full ~80-line context-scan-and-investigate protocol (semantic search → graphify → registry query → working_log grep → code read → test discovery → AC derivation → tier assessment) restated inline in every prompt. This was noticed while running the workflow by hand: five near-identical, long prompt blocks had to be authored to enforce the same mandatory ordering from `CLAUDE.md`'s Context Scan rule, with real risk that a future edit updates the protocol in one place (e.g. the `investigator` agent's own methodology) without the other (create-tickets.js's inline copy) staying in sync. Separately, `general-purpose` grants full `Edit`/`Write`/`Bash` access to a phase that should only be reading and returning structured findings — nothing in this phase is supposed to mutate repo files.

The existing `investigator` agent (`.claude/agents/investigator.md`) already encodes this exact discipline as its identity, but its contract doesn't fit here: it requires an existing `tickets/inprogress/{ticket_id}.md` and always writes `staging_artifacts/{ticket_id}/investigation.md` + `test_plan.md` to disk. create-tickets.js's Investigate phase runs *before* a ticket exists (it investigates a proposed "concern", not a ticket_id) and must return schema-validated JSON (`files_found`, `constraints`, `existing_tests`, `related_tickets`, `ac_signals`, `risks`, `is_duplicate`, `tier_recommendation`, `summary`) for the Structure phase to consume — not markdown files.

## Scope
- Add a new agent definition (e.g. `.claude/agents/concern-investigator.md`) that owns the create-tickets.js Investigate-phase methodology as its system prompt: mandatory `search_docs` → `graphify query` → `docs/REGISTRY.yaml` → `tickets/working_log.csv` → code read → test discovery → AC-signal derivation ordering, matching `CLAUDE.md`'s Context Scan rule
- Scope its tool access to read/search only (mirror the `Explore` agent's restriction pattern: no `Edit`, `Write`, or file-mutating tools) since this phase never needs to change repo state
- Define its input/output contract explicitly as concern-scoped and JSON-returning (not ticket-ID-scoped, not file-writing) so it's structurally distinct from `investigator` rather than a reuse of it
- Update `.claude/workflows/create-tickets.js`'s Investigate phase (`await pipeline(comprehension.concerns, (concern) => agent(..., { label: ..., schema: INVESTIGATION_SCHEMA }))`) to pass `agentType: 'concern-investigator'` and shrink the per-concern prompt down to the concern-specific parameters, since the general methodology now lives in the agent's own system prompt
- Document the new agent in `docs/ai/agents.md` alongside the existing Ticket Lifecycle Agents section

## Out of Scope
- Changing `investigator`'s existing contract, output files, or its use within `implement-ticket.js`'s standard-tier pipeline
- Any change to the Structure, Write, or Link phases of `create-tickets.js`
- Retroactively re-running create-tickets on any already-created ticket batch

## Acceptance Criteria
- [ ] `.claude/agents/concern-investigator.md` exists, contains the mandatory context-scan ordering (search_docs first, then graphify, then registry, then grep) as durable system-prompt content, and does not grant `Edit`/`Write`/`NotebookEdit` tool access
- [ ] `.claude/workflows/create-tickets.js`'s Investigate phase invokes `agentType: 'concern-investigator'` instead of the current unscoped `general-purpose` default, and its per-concern prompt template is reduced to concern-specific substitutions (no longer restating the full protocol inline)
- [ ] Running create-tickets end-to-end on a sample proposal still produces JSON matching `INVESTIGATION_SCHEMA` (files_found, constraints, existing_tests, related_tickets, ac_signals, risks, is_duplicate, duplicate_of, tier_recommendation, summary) — the schema contract is unchanged, only how the agent is dispatched changes
- [ ] `docs/ai/agents.md` documents `concern-investigator` under a clearly distinct heading from `investigator`, stating explicitly when to use each (existing ticket + file artifacts vs. pre-ticket concern + structured return)

## Related Tickets
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
- TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL
- TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES
- TCK-20260709-REGISTRY-COUNT-STALE-DOCS
- TCK-20260704-CREATE-TICKETS-MONITORING

## Related Docs
- `docs/ai/agents.md`
- `.claude/agents/investigator.md`
- `.claude/workflows/create-tickets.js`
- `CLAUDE.md` (Context Scan Mandatory section)

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/create-tickets.js`
- `.claude/agents/investigator.md`
- `.claude/agents/architecture-reviewer.md` (reference example of a review-only, narrowly-scoped agent definition)

## Assumptions / Open Questions
- Assumes the project wants a distinct agent type rather than widening `investigator`'s contract to support two output modes — this was the explicit recommendation when the concern was raised, on single-responsibility and pipeline-safety grounds (don't risk the standard-tier ticket pipeline that already depends on `investigator`'s current file-writing behavior)
- Open question: should `concern-investigator` also be made available for direct/manual invocation outside `create-tickets.js` (e.g. ad hoc "investigate this idea before I write a ticket" use), or scoped strictly to the workflow's internal use? Left for planning to decide.
- This ticket originated from an observation made while manually executing `create-tickets.js`'s phases in a live session (not from a written proposal doc), rather than from a pre-existing bug report or user complaint — the "author's intent" is the investigator's own recommendation captured in conversation.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260709-CONCERN-INVESTIGATOR-AGENT/plan.md` Steps 1-4, in order.

1. **`.claude/agents/concern-investigator.md`** (new) — frontmatter uses the existing 12-agent `name`/`description` convention plus a new `tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs` field (first `tools:`-restricted custom agent in this repo; omits `Edit`/`Write`/`NotebookEdit`/`Agent`/`Artifact`/`ExitPlanMode`). Body extracts `create-tickets.js`'s prior Step 0-7 investigation methodology verbatim (same scripts, same fallback behavior, same Bad/Good AC-signal examples, same hotfix/standard tier split), reworded from JS template-literal interpolations (`${concern.title}`) to generic placeholder prose ("the concern's title", "the concern's registryLayers"). The `## Output` section copies `INVESTIGATION_SCHEMA`'s 10 fields and descriptions field-for-field.
2. **`.claude/workflows/create-tickets.js`** — Investigate-phase `agent(...)` call (line ~296-312) now passes `agentType: 'concern-investigator'`; prompt shrunk from ~115 lines to concern-specific substitutions only (id, title, description, domain_area, type_hint, priority_hint, raw_excerpts, registryLayers). `INVESTIGATION_SCHEMA` and `DOMAIN_TO_LAYERS` are byte-identical to before (verified by `git diff` and by the new schema-drift test).
3. **`tests/tools/test_concern_investigator_agent_definition.py`** (new) — 5 tests: frontmatter/tools-field shape, context-scan ordering (search_docs -> graphify -> REGISTRY.yaml -> working_log.csv), Investigate-phase dispatch uses the new agentType with old Step-header text absent, `INVESTIGATION_SCHEMA`'s required-field list unchanged, and `docs/ai/agents.md` has a distinct `concern-investigator` heading. All 5 pass, alongside the existing `test_tag_skill_mapping_check.py` regression guard (10 tests, all passing) confirming the create-tickets.js edit didn't bleed into the adjacent Structure-phase tag->skill table.
4. **`docs/ai/agents.md`** — new `### \`concern-investigator\`` subsection added between `### \`investigator\`` and `### \`planner\`` (Role / What it does / Inputs / Outputs / When to invoke directly, plus an explicit investigator-vs-concern-investigator contrast line), and a new row in the Agent Summary Table.

**Minor implementation detail (not a plan deviation):** the Inputs section's `registryLayers` bullet was worded as "REGISTRY.yaml layers" rather than "`docs/REGISTRY.yaml` layers" specifically so the literal string `docs/REGISTRY.yaml` first appears in the Methodology's Step 2 section, not earlier in Inputs — this keeps the context-scan-ordering test meaningful (it asserts `search_docs` -> `graphify query` -> `docs/REGISTRY.yaml` -> `tickets/working_log.csv` occur in that relative order in the methodology text). No content or meaning was lost; this is a phrasing choice made while writing the test in the same step.

**Runtime verification — superseded during Verify, documented here for the record:** At Implement time, the assumption (based on `TCK-20260707-SUBAGENT-FRONTMATTER`'s precedent) was that the harness does not hot-reload `.claude/agents/` mid-session, so live invocation was believed impossible within this run. That assumption turned out to be **wrong for this session**: shortly after Implement completed, the harness emitted a system-level notice that `concern-investigator` had become available as an `Agent` subagent type, without a session restart. During the Verify phase, `Agent(subagent_type: "concern-investigator", ...)` was actually invoked live against a real (synthetic, smoke-test) concern. Result: it dispatched successfully, followed its documented Step 0–7 methodology (search_docs → graphify → `docs/REGISTRY.yaml` → `tickets/working_log.csv` → code read → tests → AC-signal derivation, in that order), used only read-only tools (`Read`, `Bash` for read-only commands, MCP search, `graphify query`) — no `Edit`/`Write`/`NotebookEdit` call was attempted or needed — and returned valid JSON matching `INVESTIGATION_SCHEMA`'s exact field list. Both previously-open questions (does `tools:` enforcement hold at runtime; does the `agentType` string resolve) are now answered **yes**, by direct observation, not just static configuration. Hot-reload behavior may still vary across harness versions/sessions — the static tests remain the durable regression guard — but for this ticket, live verification is complete, not merely disclosed as pending.

`graphify update .` was run after the test file was added; it reported a pre-existing node-count mismatch warning (25661 vs 25662) unrelated to this change and requiring `--force` to override — not forced, since investigating/fixing the graph index is outside this ticket's scope.

## Test Summary

`.venv/bin/python3 -m pytest tests/tools/test_tag_skill_mapping_check.py tests/tools/test_concern_investigator_agent_definition.py -v` — 15 passed, 0 failed.

## Files Changed

- `.claude/agents/concern-investigator.md` (new)
- `.claude/workflows/create-tickets.js` (Investigate-phase dispatch only)
- `tests/tools/test_concern_investigator_agent_definition.py` (new)
- `docs/ai/agents.md` (new `concern-investigator` subsection + summary table row)

## Completion Summary

Added `.claude/agents/concern-investigator.md`, a read-only (`tools:` field excludes Edit/Write/NotebookEdit), JSON-returning agent that owns the pre-ticket investigation methodology previously duplicated inline in `create-tickets.js`'s Investigate phase. `create-tickets.js` now dispatches `agentType: 'concern-investigator'` with a shrunk, concern-specific prompt; `INVESTIGATION_SCHEMA` is unchanged. Documented in `docs/ai/agents.md` under its own heading, distinct from `investigator`. Static tests pass (15/15). Live verification (see Implementation Notes) confirmed via an actual smoke-test invocation during Verify: the agent dispatches correctly, stays read-only in practice, and returns schema-conformant JSON — both runtime-enforcement questions are answered, not just disclosed as open.

