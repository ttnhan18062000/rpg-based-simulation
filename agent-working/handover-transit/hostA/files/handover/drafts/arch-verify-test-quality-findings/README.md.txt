# Brief: Architecture-Verify cannot carry `test_quality_findings` (design -> implementer; requirement from test-architecture)
Requirement owner: test-architecture-reviewer (relayed by test-architecture-implementer, 2026-10-02). We own HOW it is built.
Base: origin/main. Tier: standard (touches the workflow, the event schema and the skill path). Layer ai, tags delivery/agent-monitoring (check the tag registry).

## Verified facts (design session, against origin/main)
- `ARCH_VERIFY_SCHEMA` (.claude/workflows/implement-ticket.js ~1097) has verdict, violations, summary, ts, verified_by. No `test_quality_findings`. Extra keys are not forbidden.
- `.claude/agents/architecture-reviewer.md:~123` already requires a separate `test_quality_findings` list (advisory, diff-scoped to changed tests, clean = empty list).
- The Architecture-Verify prompt calls itself "a narrow verification", and its Return list names only verdict/violations/summary/verified_by. DO NOT edit that wording or the agent file (test-architecture rule).
- `archVerify` is read only for verdict/violations/summary; the Architecture-Verify `pushEvent(...)` (events row: seq, phase, agent, status, summary<=200 chars, ts, tool_call_count, reason_code) has no place for a list. `docs/agent-monitoring/schema.md` documents the event fields.
- Skill path (`.claude/skills/implement-ticket/SKILL.md`, and a DIFFERENT copy at `.agents/skills/implement-ticket/SKILL.md`): "Spawn Agent(subagent_type, prompt); parse its JSON response and validate it matches schema S". It says nothing about how to tell the agent the output format, so the hand-orchestrated run improvised a format tail ("Return your answer as a single JSON object with keys: verdict, violations, summary, verified_by, ts"), which test-architecture disclosed may itself have steered the reviewer to put its remark in `notes`.

## Required (all three, in one change)
1. **Schema**: add optional `test_quality_findings` (array of strings, empty valid) to ARCH_VERIFY_SCHEMA. Additive, no verdict effect, no gate.
2. **Carry-through**: the next run's list must reach the monitoring evidence without hand copying (Finalize/closure record). Options, you choose and justify:
   a) new optional event field on the Architecture-Verify event (needs schema.md + validator allowance; list survives verbatim);
   b) an extra event row for the phase carrying the list in a documented field;
   c) a side file under the run's artifacts written by the JS/closure path.
   Constraint: `summary` stays <=200 chars; monitoring writes must never fail the workflow; do not widen `agent` vocabulary.
3. **Skill-path format tail derived mechanically**: add to SKILL.md (both copies, after checking why they differ) a rule that any output-format text the orchestrator appends is generated from the phase's schema key list (ALL property names, in schema order, including `test_quality_findings`), never hand-written, and recorded verbatim; if the native runtime enforces the schema, append nothing. Ideally a small helper the skill can call so the sentence is not improvised.

## Test-architecture's next-run protocol (do not break)
"Unmodified" = no checklist-specific sentence anywhere; format text only from the schema key list. Success on the next run is the production reviewer returning the list AND showing it read the changed test files; that is the reviewer's to judge, not ours to engineer.

## Process
- Conflict-check with test-architecture (via their implementer) BEFORE editing implement-ticket.js or the agent file; send them the diff for review before merge.
- Do not run the real `implement-ticket` Workflow to test (needs the user's opt-in); unit-test the schema/helper and any new event field, and use a fixture for the skill-path format helper.
- Parity/docs: update docs/agent-monitoring/schema.md if an event field is added; add a note where the skill/JS drift is tracked (TCK-20260804-SKILL-JS-PHASE-SYNC).
- Push/PR per the standing grant; one batch, merge is the user's.
