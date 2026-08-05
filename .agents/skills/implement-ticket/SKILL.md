---
name: implement-ticket
description: 'Full ticket implementation workflow orchestrator — scope through finalize.'
---
# implement-ticket

Run the full ticket implementation pipeline for a single ticket.

## Usage

```
/implement-ticket ticket_id=TCK-20260607-MY-TICKET
/implement-ticket request="add pagination to the world listing endpoint"
/implement-ticket ticket_id=TCK-20260607-MY-TICKET tier=hotfix
```

## Input

Parse the user's input to extract:

- `ticket_id` — existing ticket ID to resume (e.g. `TCK-20260607-MY-TICKET`); looks for it in `tickets/inprogress/`, `tickets/done/`, or `tickets/todos/**/`
- `request` — natural language description of a new ticket to create and implement
- `tier` — optional override: `hotfix` (skip Investigate/Plan/Review), `standard` (full pipeline), `epic` (scope only)

If the input is a bare TCK-... ID, treat it as `ticket_id`.
If the input is a natural language sentence, treat it as `request`.

## Action

**Do not call the Workflow tool — it is not available.** Execute the workflow directly:

1. Read `.claude/workflows/implement-ticket.js` in full before doing anything else — it is the authoritative source; this file is a translation aid, not a replacement, and can drift from it (see TCK-20260804-SKILL-JS-PHASE-SYNC, which corrected exactly that after the two were found out of sync). If the two ever disagree, the JS wins — update this file to match, don't follow this file over the JS.
2. Execute each phase block in order, translating JS constructs to tool calls as follows:

| JS construct | What to do |
|---|---|
| `phase('Name')` | Announce the current phase to the user |
| `log(msg)` | Output the message to the user |
| `await agent(prompt, { agentType: 'name', schema: S })` | Spawn `Agent(subagent_type: "name", prompt: prompt)`; parse its JSON response and validate it matches schema S |
| `await agent(prompt, { label: 'L' })` | Spawn `Agent(prompt: prompt)` — no specific agent type; label is for monitoring context only |
| Gate condition (e.g. `if (review.verdict !== 'APPROVED') { ... return { status: ... } }`) | Check the agent's return value; if the gate fails, call writeMonitoring first, then stop and report the blocking status and re-run instruction to the user |
| Orchestrator-run `await bash(...)` (no `agent()` wrapper) | Run the exact command yourself via Bash — never delegate this to a sub-agent prompt, and never skip it because it "looks like a detail" (`implement-ticket.js`'s own comments repeatedly note that a bash-block instruction embedded only in agent prose has been observed to silently not execute — these steps must be issued as real, direct tool calls) |
| `await writeMonitoring(finalStatus)` | Execute the monitoring write block defined in that function in the JS — mandatory at every exit point, including gate failures; use `python3 tools/agent-monitoring/record_run.py` and `record_events.py`, never write to those files directly |
| `return { status, ... }` | Report the final status and relevant fields to the user |

3. Carry all variables (`tier`, `tid`, `ticketInfo`, `startTs`, `events`, etc.) across phases exactly as the JS does.

## Gate Integrity (hard rule)

**Never edit, delete from, or otherwise alter the content of an artifact a gate check reads, for the purpose of making that check pass.** This includes deleting a `## Unresolved Questions` heading, removing a flagged violation, or rewording text specifically to dodge a pattern match — whether you do it yourself or instruct a further sub-agent to do it. A gate's real outcome (`NEEDS_CHANGES`, `BLOCKED`, `NEEDS_HUMAN_INPUT`, `CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED`, `DOC_STALENESS_BLOCKED`, `TESTS_FAILED`, `SECURITY_BLOCKED`, `DOD_BLOCKED`, or any other status the JS defines) must always match what the artifact honestly says — if a phase produces a blocking result, that is correct information to report, not an obstacle to route around. Stop and report it exactly as the JS specifies, even when the blocking issue looks trivially resolvable to you; that judgment belongs to the human who gets notified by the resulting status, not to the orchestrating agent. This rule applies with equal force at every level of delegation — including any sub-agent you yourself spawn to carry out a phase.

## Pipeline (standard tier)

0. **Context search** (REQUIRED before Scope — before any file reads or grep):
   1. Call `mcp__knowledge-search__search_docs` with `query` = ticket title + request summary. Note returned doc paths, ticket IDs, and excerpts as warm-start candidates.
   2. Run `graphify query "<ticket title>"` — note returned code nodes as primary file targets for the Investigate phase.
   3. Fallback only if MCP unavailable: `python3 tools/knowledge_search.py query "<ticket title + request summary>" --top-k 5`
   Raw file reads and grep are follow-up steps only — use paths from steps 1–2 first.

1. **Scope** — create or load ticket; copy from `tickets/todos/**/` to `tickets/inprogress/` if needed
2. **Investigate** — produce `investigation.md` and `test_plan.md` (skipped for hotfix). At the end of this phase, also run the shadow context-packet call site (`implement-ticket.js:560-588`): an advisory, opt-in, fail-open bash block, gated `SHADOW_CONTEXT_PACKET_ENABLED=1` (off by default — check the env var, do not force it on), that calls `wrap_context_packet_assembly()` with an empty candidate set using the real `tid` as `run_id`. Run the exact block verbatim (including its `timeout 10s ... 2>/dev/null || true` fail-open wrapper and its negative-`seq` computation) — never simplify it, since the negative-seq math is what keeps it collision-safe against real phase events on resume. This step is skipped whenever Investigate itself is skipped (hotfix tier).
3. **Plan** — produce `plan.md` (skipped for hotfix)
4. **Review** — architecture review of the plan (gate, skipped for hotfix)
5. **Implement** — write code
6. **Document-Update** — runs unconditionally, every tier including hotfix, immediately after Implement and strictly before Architecture-Verify (`implement-ticket.js:774-838`) — this ordering is load-bearing, not cosmetic: the doc-updater agent's own reported `docs_updated` paths get merged into the doc-staleness gate's file list in the very next step, so running Document-Update after Architecture-Verify (as an earlier version of this skill's guidance implicitly allowed) means Architecture-Verify never sees Document-Update's own edits. Spawn `Agent(subagent_type: "doc-updater", ...)` per the JS prompt shape.
7. **Doc-staleness gate** (orchestrator-run, no agent call) — immediately after Document-Update: run `python3 tools/gate_checks/doc_staleness_check.py <behavior_changed> <files_changed...> [--docs-to-update <paths...>]` (`implement-ticket.js:839-905`). `FAIL` only when `behavior_changed` is true, at least one changed path starts with `src/`, `config/`, or is a `.claude/workflows/*.js` path, and zero changed paths start with `docs/`. A `FAIL` is a hard block — stop, call `writeMonitoring('DOC_STALENESS_BLOCKED')`, and report `DOC_STALENESS_BLOCKED` to the user with instructions to add a docs/ update and re-run. An `ADVISORY` result (a doc Investigate flagged wasn't actually touched) is non-blocking — log it, continue.
8. **Architecture-Verify** — post-Implement deterministic backstop; re-invokes architecture-reviewer against the actual diff (now including Document-Update's own changes) to check durable-state/API-boundary/reason-metadata rules (skipped for hotfix)
9. **Test** — run scoped pytest (gate). Immediately after Test passes, run the post-Test cleanup checkpoint (orchestrator-run, `implement-ticket.js:1047-1090`): `python3 -c "...from gate_checks.done_checker_static import clean_data_runs_early; ..."` — cleans `data/runs/`/`reports/release_proof/` artifacts from this session only (mtime-gated, never a blind `rm`) before Parity/Verify can see them stale. A `FAIL` here is a hard block (`DATA_RUNS_CLEAN_FAILED`).
10. **Parity** — update parity ledger. Skip-eligible only when both `implementation.files_changed` contains no `src/` path AND `behavior_changed` is false (with a lazy P0 safeguard scan via `tools/parity_ledger_scan.py::find_p0_intersection` on that skip path only). Otherwise: before the agent call, run `expected_subsystems_for_files()` (orchestrator-run bash, `implement-ticket.js:1147-1154`) and inject its output into the parity-updater prompt as a hint. After the agent call returns, run the cross-reference gate (`implement-ticket.js:1184-1219`): `cross_reference_touched()` against `git status --porcelain -- docs/parity_ledger/`'s real output. Any `FAIL` (a `src/` file mapped to a ledger subsystem with no corresponding ledger touch) is a hard block — `PARITY_INCOMPLETE`. An unparseable cross-ref result is non-blocking.
11. **Security-Review** — security gate, conditional: fires when the ticket's tags include `security` or `suggested_skills` includes `/security-review` (skipped otherwise — not tier-gated)
12. **Verify** — Definition-of-Done checklist (gate)
13. **Finalize** — move ticket to `tickets/done/`; remove todos source file (then move the entire parent `tickets/todos/{folder}/` to `tickets/done/{folder}/` if no other TCK-*.md files remain); append working_log; move `staging_artifacts/{tid}/` → `stored_artifacts/{tid}/`. After the Finalize agent's steps and the post-Finalize migration self-check both succeed: (a) if `git status --porcelain -- docs/` is non-empty, run `make knowledge-index-update` (orchestrator-run bash, fail-open — a failure here is a logged warning only, never a block, per `implement-ticket.js:1471-1490` and CLAUDE.md's "After Work" rule); (b) run the three advisory-only Finalize-tail checks, `check_monitoring_write_recorded`, `check_tag_drift`, and `check_workflow_meta_conformance` (aggregated via `summarize_conformance_results`, with `Security-Review` filtered out at this call site — `implement-ticket.js:1502-1581`) — all three are logged warnings only and can never block ticket close. Separately, `check_skill_doc_covers_meta_phases()` (`tools/gate_checks/workflow_meta_conformance.py`) verifies every hand-orchestration `SKILL.md` mentions all of its own workflow's declared `meta.phases` titles — this runs as a pytest test (`tests/tools/test_workflow_meta_conformance.py`), not as part of this workflow's own Finalize sequence.

Hotfix tier skips Investigate (and its shadow-packet step), Plan, Review, and Architecture-Verify. Document-Update, the doc-staleness gate, the post-Test cleanup checkpoint, Parity (with its gate), Security-Review (if the ticket's tags include `security` or `suggested_skills` includes `/security-review` — conditional on that, not on tier), and the post-Finalize steps all still run for hotfix — they are tier-unconditional in the JS.

## Notes

- `writeMonitoring` must be called at every exit — gate failures, DONE, and EPIC_SCOPED alike
- Never write to `agent-monitoring/runs.jsonl` or `events.jsonl` directly — always go through `record_run.py` / `record_events.py`
- Pass `ticket_id` to resume from an existing in-progress ticket (Scope phase re-loads it and skips creation)
