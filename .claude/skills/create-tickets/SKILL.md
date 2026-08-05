# create-tickets

Parse a natural-language proposal document into investigation-backed TCK-*.md ticket files, ready for `/implement-epic`.

The proposal can be written by anyone — developer, BA, tester — in any natural markdown format. The workflow does the investigation work so the author doesn't have to.

## Usage

```
/create-tickets source=docs/plans/proposal.md
/create-tickets source=docs/plans/proposal.md structure=docs/plans/ticket_plan_structure.md
/create-tickets source=docs/plans/proposal.md output=tickets/todos/phase29-repair/
/create-tickets source=docs/plans/proposal.md epic_id=TCK-20260608-PHASE29-EPIC
```

## Input

Parse the user's input to extract:

- `source` — path to the source markdown document (required). If the user provides a bare file path with no `source=` prefix, treat it as `source`.
- `structure` — path to a ticket plan structure / template doc (optional). Guides concern granularity and scope conventions.
- `output` — output folder override (optional). Inferred from the proposal content if omitted.
- `epic_id` — existing epic ticket ID to link the created tickets to (optional).

## Action

**Do not call the Workflow tool — it is not available.** Execute the workflow directly:

1. Read `.claude/workflows/create-tickets.js` in full before doing anything else — it is the authoritative source; this file is a translation aid and can drift from it (see TCK-20260804-CREATE-TICKETS-SKILL-SYNC, which corrected exactly that). If the two ever disagree, the JS wins.
2. Execute each phase block in order, translating JS constructs to tool calls as follows:

| JS construct | What to do |
|---|---|
| `phase('Name')` | Announce the current phase to the user |
| `log(msg)` | Output the message to the user |
| `await agent(prompt, { agentType: 'name', schema: S })` | Spawn `Agent(subagent_type: "name", prompt: prompt)`; parse its JSON response and validate it matches schema S |
| `await agent(prompt, { label: 'L' })` | Spawn `Agent(prompt: prompt)` — no specific agent type; label is for monitoring context only |
| Orchestrator-run `await bash(...)` (no `agent()` wrapper) | Run the exact command yourself via Bash — never delegate to a sub-agent prompt, never skip it |
| `await writeMonitoring(finalStatus)` | Execute the monitoring write block defined in that function in the JS — mandatory at every exit point; use `python3 tools/agent-monitoring/record_run.py` and `record_events.py`, never write to those files directly |
| `return { status, ... }` | Report the final status and relevant fields to the user |

3. Carry all variables (`comprehension`, `validInvestigations`, `structured`, `outputFolder`, etc.) across phases exactly as the JS does.
4. **Do not skip or abbreviate the Investigate phase** — the investigation steps are the core value of this skill.

## Pipeline

1. **Comprehend** — reads the proposal as natural language, extracts discrete concerns without enforcing ticket schema. Preserves the author's intent and framing.

2. **Investigate** — per concern: find real file paths, doc constraints, existing tests, and derive testable AC signals. **Required order — do not skip steps:**

   **Step 0 — Semantic retrieval (REQUIRED FIRST):**
   - Call `mcp__knowledge-search__search_docs` with the concern title + description as query.
   - Run `graphify query "<concern title>"` for code structure and relationships.
   - Run `python3 tools/knowledge_search.py query "<concern>" --top-k 5` as fallback if MCP unavailable.
   - Note all returned ticket IDs and file paths as warm-start candidates before doing any grep.

   **Step 1 — Knowledge graph:**
   - Read `graphify-out/GRAPH_REPORT.md` for community structure (which community owns this domain?).
   - Use node names from graphify as primary file targets.

   **Step 2 — Docs and REGISTRY.yaml:**
   - Query `docs/REGISTRY.yaml` for entries in the relevant layer.
   - Read highest-authority matching docs (P0 first).

   **Step 3 — Prior ticket history:**
   - `grep -i "<keyword>" tickets/working_log.csv` for domain keywords.
   - Read `stored_artifacts/<ticket_id>/investigation.md` for up to 3 matching prior tickets.

   **Step 4 — Code files (follow-up only):**
   - Use node names and paths from Step 1 as primary targets. Read up to 3 relevant files.
   - Only fall back to `grep -r "<noun>" src/ --include="*.py" -l` if Step 0-1 returned no usable paths.

   **Step 5 — Existing tests:**
   - Find test files for modules found in Step 4.

   **Step 6 — Derive AC signals** from concern + code behavior + doc constraints + test patterns.

3. **Structure** — one synthesis agent takes all investigation results and produces properly-formed ticket fields: real file paths from grep, concrete ACs from code evidence, correct tier from scope, author's intent preserved in request_summary. After the agent returns, two orchestrator-run checks narrow the batch before Write — never delegate either to a sub-agent:
   - **`short_scope` dedup** (`create-tickets.js:559-574`, plain JS logic, no bash call): if the Structure agent produced two tasks with the same `short_scope` despite instructions, drop the second silently and log a `WARNING:` — do not write duplicate files.
   - **Tag-registry gate** (`create-tickets.js:576-614`, orchestrator-run bash): run `python3 -c "...from tag_registry import check_tags_registered; ..."` against the full batch's tag set. Any task carrying a tag `check_tags_registered()` flags as unregistered is filtered OUT of the write set (not written), a `blocked`-status event is pushed, and a log line tells the user to register the tag (`python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`) and re-run to pick up the skipped concern. This narrows the batch — it does **not** abort the whole run over one task's tag.
4. **Write** — creates `TCK-YYYYMMDD-<SHORT-SCOPE>.md` per task into the output folder (parallel), using only the tasks that survived both checks above.
5. **Link** — if `epic_id` given, appends the new ticket IDs to the epic's `## Related Tickets` section.

## Notes

- The proposal author does NOT need to provide file paths or acceptance criteria — the Investigate phase derives them from the codebase
- Output folder defaults to `tickets/todos/<inferred-name>/` — inferred from the proposal topic
- Concerns already fully covered by existing tickets are detected in Investigate and skipped (reported as duplicates)
- Concerns are split or merged based on what investigation reveals about the actual code structure
- If intra-batch ticket dependencies are detected, a `SEQUENCE.md` is written to enforce implementation order
- After creation, run `/implement-epic folder=<output_folder>` to implement the tickets
