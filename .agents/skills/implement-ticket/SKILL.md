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

1. Read `.claude/workflows/implement-ticket.js` in full before doing anything else.
2. Execute each phase block in order, translating JS constructs to tool calls as follows:

| JS construct | What to do |
|---|---|
| `phase('Name')` | Announce the current phase to the user |
| `log(msg)` | Output the message to the user |
| `await agent(prompt, { agentType: 'name', schema: S })` | Spawn `Agent(subagent_type: "name", prompt: prompt)`; parse its JSON response and validate it matches schema S |
| `await agent(prompt, { label: 'L' })` | Spawn `Agent(prompt: prompt)` — no specific agent type; label is for monitoring context only |
| Gate condition (e.g. `if (review.verdict !== 'APPROVED') { ... return { status: ... } }`) | Check the agent's return value; if the gate fails, call writeMonitoring first, then stop and report the blocking status and re-run instruction to the user |
| `await writeMonitoring(finalStatus)` | Execute the monitoring write block defined in that function in the JS — mandatory at every exit point, including gate failures; use `python3 tools/agent-monitoring/record_run.py` and `record_events.py`, never write to those files directly |
| `return { status, ... }` | Report the final status and relevant fields to the user |

3. Carry all variables (`tier`, `tid`, `ticketInfo`, `startTs`, `events`, etc.) across phases exactly as the JS does.

## Pipeline (standard tier)

0. **Context search** (REQUIRED before Scope — before any file reads or grep):
   1. Call `mcp__knowledge-search__search_docs` with `query` = ticket title + request summary. Note returned doc paths, ticket IDs, and excerpts as warm-start candidates.
   2. Run `graphify query "<ticket title>"` — note returned code nodes as primary file targets for the Investigate phase.
   3. Fallback only if MCP unavailable: `python3 tools/knowledge_search.py query "<ticket title + request summary>" --top-k 5`
   Raw file reads and grep are follow-up steps only — use paths from steps 1–2 first.

1. **Scope** — create or load ticket; copy from `tickets/todos/**/` to `tickets/inprogress/` if needed
2. **Investigate** — produce `investigation.md` and `test_plan.md` (skipped for hotfix)
3. **Plan** — produce `plan.md` (skipped for hotfix)
4. **Review** — architecture review of the plan (gate, skipped for hotfix)
5. **Implement** — write code
6. **Architecture-Verify** — post-Implement deterministic backstop; re-invokes architecture-reviewer against the actual diff to check durable-state/API-boundary/reason-metadata rules (skipped for hotfix)
7. **Test** — run scoped pytest (gate)
8. **Parity** — update parity ledger
9. **Security-Review** — security gate, conditional: fires when the ticket's tags include `security` or `suggested_skills` includes `/security-review` (skipped otherwise — not tier-gated)
10. **Verify** — Definition-of-Done checklist (gate)
11. **Finalize** — move ticket to `tickets/done/`; remove todos source file (then move the entire parent `tickets/todos/{folder}/` to `tickets/done/{folder}/` if no other TCK-*.md files remain); append working_log; move `staging_artifacts/{tid}/` → `stored_artifacts/{tid}/`

Hotfix tier skips Investigate, Plan, Review, and Architecture-Verify.

## Notes

- `writeMonitoring` must be called at every exit — gate failures, DONE, and EPIC_SCOPED alike
- Never write to `agent-monitoring/runs.jsonl` or `events.jsonl` directly — always go through `record_run.py` / `record_events.py`
- Pass `ticket_id` to resume from an existing in-progress ticket (Scope phase re-loads it and skips creation)
