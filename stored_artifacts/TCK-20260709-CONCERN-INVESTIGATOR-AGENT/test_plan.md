---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260709-CONCERN-INVESTIGATOR-AGENT
artifact_type: test_plan
tags: [ai, investigator, workflows]
---

# Test Plan — TCK-20260709-CONCERN-INVESTIGATOR-AGENT

## Regression Surface

This ticket touches `.claude/agents/*.md` (adds one new file) and `.claude/workflows/create-tickets.js` (Investigate-phase prompt only). These are agent-prompt/DSL files, not imported Python/JS modules — there is no `pytest`-collectible unit-test surface that directly imports either file. Regression protection here is (a) static consistency checks that parse these files as text/data, and (b) a live functional smoke test (not pytest — see "Scoped Pytest Commands" below for why).

- **unit**
  - `tests/tools/test_tag_skill_mapping_check.py` — **must still pass**. `tools/tag_skill_mapping_check.py` parses `.claude/workflows/create-tickets.js`'s `suggested_skills` tag→skill arrow-list (Structure phase, lines 599-608) via `extract_pairs_arrow_list`. This ticket's edit target (Investigate phase, lines 296-412) is adjacent in the same file — this test is the concrete regression guard against accidentally corrupting the unrelated Structure-phase table while shrinking the Investigate-phase prompt.
  - No existing test parses or validates `.claude/agents/*.md` frontmatter or body content (confirmed: `tests/tools/test_add_frontmatter_live.py` only covers `docs/` frontmatter classification via `tools/add_frontmatter_live.py`, an unrelated tool for a different file population — not a gap introduced by this ticket, a pre-existing gap that `TCK-20260707-SUBAGENT-FRONTMATTER`'s own Test Summary also relied on manual/live verification for, not pytest).
- **integration**
  - None directly applicable — `tests/integration/lab_agent/*` covers the unrelated `src/lab/` agentic simulation lab workflows (`prepare-simulation-execution`, `register-simulation-result`, etc.), not `create-tickets.js`/`implement-ticket.js`. No integration test harness exists for `.claude/workflows/*.js` DSL scripts (they are interpreted live by the executing agent per `SKILL.md`'s JS→tool-call translation table, not run as real Node/JS programs — confirmed no test runner imports `.claude/workflows/`).
- **arena-combat**
  - Not applicable — no combat/simulation code touched.

## New Tests Required

Per acceptance criteria:

1. **AC #1 — `.claude/agents/concern-investigator.md` exists, encodes the mandatory context-scan ordering, and does not grant Edit/Write/NotebookEdit**
   - Test name: `test_concern_investigator_agent_file_exists_and_has_frontmatter`
   - Category: unit (static/text assertion, new test module)
   - Verifies: file exists at `.claude/agents/concern-investigator.md`; frontmatter block parses as valid YAML with `name: concern-investigator` and a non-empty `description`; if a `tools:` field is added per the plan's resolution of the tool-scoping open question (see investigation.md Risk #1), assert the parsed `tools:` list does **not** contain `Edit`, `Write`, or `NotebookEdit`.
   - Where: new file, `tests/tools/test_concern_investigator_agent_definition.py` (mirrors the structure of `tests/tools/test_tag_skill_mapping_check.py` — parses the `.md` file as data, no code import).
   - Note: this test can assert the frontmatter *declares* the restriction; it cannot assert the harness *enforces* it (no pytest-accessible way to invoke `Agent(subagent_type=...)` and inspect its live tool grants — that requires the manual live smoke test called out in "Anti-Drift Test Guards" below and in investigation.md Risk #1).
   - Test name: `test_concern_investigator_encodes_context_scan_ordering`
   - Category: unit
   - Verifies: the file body contains, in order (by string index), references to `search_docs` (or `mcp__knowledge-search__search_docs`), `graphify query`, `docs/REGISTRY.yaml`, and `tickets/working_log.csv` — mirroring the ordering assertion pattern already used for prose consistency elsewhere in this repo's tooling tests (e.g., `extract_pairs_*` functions treat file text as structured data to parse).
   - Where: same new file as above.

2. **AC #2 — `create-tickets.js`'s Investigate phase invokes `agentType: 'concern-investigator'`, prompt reduced to concern-specific substitutions**
   - Test name: `test_investigate_phase_uses_concern_investigator_agent_type`
   - Category: unit (regex/string assertion against the `.js` source text, same technique `tag_skill_mapping_check.py` already uses for this exact file)
   - Verifies: the `agent(...)` call inside the `pipeline(comprehension.concerns, ...)` block (currently `create-tickets.js:296-412`) contains `agentType: 'concern-investigator'`; the prompt template no longer contains the full Step 0–7 methodology headers (`"Step 0: Semantic prior-work retrieval"`, `"Step 1: Knowledge graph"`, etc.) that are being moved into the new agent's system prompt — i.e., assert their *absence* post-change as a positive signal the extraction happened, not just the new field's presence.
   - Where: `tests/tools/test_concern_investigator_agent_definition.py` (same new file) or a new `tests/tools/test_create_tickets_investigate_dispatch.py` if the file grows large — implementer's judgment, per file-size convention observed elsewhere in `tests/tools/`.

3. **AC #3 — schema-conformant JSON output unchanged (`INVESTIGATION_SCHEMA`)**
   - This is a **behavioral** AC that cannot be verified by pytest (no JS execution harness for `.claude/workflows/*.js`, and the schema itself is unchanged data, not code — `git diff` on `INVESTIGATION_SCHEMA`'s definition, lines 210-263, showing zero changes is the correct verification, not a new test).
   - Test name: `test_investigation_schema_definition_unchanged` (defensive char-string invariant, optional but recommended given this is the one AC most likely to silently regress if a future edit touches the wrong block)
   - Category: unit
   - Verifies: `INVESTIGATION_SCHEMA`'s `required` array (line 212) still contains all 10 original field names (`concern_id, files_found, constraints, existing_tests, related_tickets, ac_signals, risks, is_duplicate, tier_recommendation, summary`) — a regex/string containment check against the source.
   - Where: same new test file.
   - The **real** verification for this AC is the manual end-to-end run named in the AC text itself ("Running create-tickets end-to-end on a sample proposal") — see Anti-Drift Test Guards below; this is a live-agent action, not a pytest command.

4. **AC #4 — `docs/ai/agents.md` documents `concern-investigator` under a distinct heading**
   - Test name: none required as automated pytest — this repo's existing pattern for `docs/ai/agents.md` freshness is manual audit (see `TCK-20260706-DOCS-CONSISTENCY-PASS`'s precedent: "Audited every doc claiming to exhaustively list the gate/report vocabulary... fixed 3 genuinely stale spots"), not an automated doc-drift test. No existing test parses `docs/ai/agents.md`'s heading structure.
   - If the implementer wants machine verification anyway: `test_agents_doc_has_concern_investigator_heading` (unit, asserts `### \`concern-investigator\`` heading string is present and appears under a heading distinct from `### \`investigator\``, i.e. not nested under it) — optional, not required by existing repo convention.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_tag_skill_mapping_check.py tests/tools/test_concern_investigator_agent_definition.py -v
```

Add `tests/tools/test_create_tickets_investigate_dispatch.py` to the command above if the implementer splits that test into its own file per the note under AC #2.

Do **not** run `pytest tests/` — scope is confined to `tests/tools/`. No `src/` files are touched by this ticket, so no `tests/unit/`, `tests/integration/`, or `tests/simulation_quality/` paths are in scope.

## Anti-Drift Test Guards

- **`test_tag_skill_mapping_check.py` (existing, must stay green)** — the concrete guard against the Investigate-phase edit accidentally corrupting the adjacent, unrelated Structure-phase `suggested_skills` tag→skill table in the same file (`create-tickets.js:599-608`). If this test starts failing after this ticket's implementation, the diff touched more of the file than intended — a direct scope-creep signal.
- **Manual live smoke test (not pytest, but a mandatory verification step per AC #1 and the investigation's Risk #1/#2)**: after adding `.claude/agents/concern-investigator.md`, confirm via a session restart + a trivial `Agent(subagent_type: "concern-investigator", prompt: "reply with SMOKE_OK, do nothing else")` call that (a) the type resolves at all (mirrors `TCK-20260707`'s exact smoke-test method), and (b) if a `tools:` frontmatter restriction was added, that the live Agent-type listing (system reminder available at session start, same mechanism used in this investigation to read `investigator`'s/`architecture-reviewer`'s current `(Tools: All tools)` annotation) now shows the restricted list for `concern-investigator` instead of `All tools`. This is the only way to confirm AC #1's tool-scoping claim is real rather than a frontmatter field the harness silently ignores.
- **Manual end-to-end run (not pytest, required by AC #3's own wording)**: run `create-tickets.js` against a small sample proposal doc and confirm the Investigate phase's returned JSON still validates against `INVESTIGATION_SCHEMA` (all 10 required fields present, correct types) with `agentType: 'concern-investigator'` now driving the call instead of the unscoped default. A schema validation failure here would mean the prompt-shrinking in Scope item 3 accidentally dropped a field the schema still requires.
- **Existing-12-agents non-regression**: no test currently parses `.claude/agents/*.md` as a set, so there is no automated guard against accidentally modifying one of the other 12 files' frontmatter while adding the 13th. Manual `git diff --stat` check (the same technique `TCK-20260707`'s and `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`'s Test Summaries both relied on) should confirm only `concern-investigator.md` is added and `create-tickets.js`/`docs/ai/agents.md` are modified — no other `.claude/agents/*.md` file touched.
