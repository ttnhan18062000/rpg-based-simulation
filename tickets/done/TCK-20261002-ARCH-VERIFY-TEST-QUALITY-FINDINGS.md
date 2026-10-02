---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS
phase: done
date: 2026-10-02
tags: [agent-monitoring, workflows]
---

# TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS

## Title
Architecture-Verify can carry `test_quality_findings` into the monitoring evidence, and the skill path's output-format tail is generated from the schema

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Requirement from test-architecture-reviewer (relayed by test-architecture-implementer), brief from `agent-working-design`
(`.claude/handover/drafts/arch-verify-test-quality-findings/README.md`):
`architecture-reviewer.md` already requires a separate advisory `test_quality_findings` list, but `ARCH_VERIFY_SCHEMA` has
no such key, the Architecture-Verify event has no place for a list, and the skill path (`SKILL.md`) says nothing about the
output format, so a hand-orchestrated run improvised a format tail that may itself have steered the reviewer to put its
remark in `notes`. Three parts in one change: (1) schema key, (2) carry-through into the events shard, (3) a rule plus helper
so a skill-path format tail is generated from the schema's key list and never hand-written.

## Scope
1. `ARCH_VERIFY_SCHEMA` (`.claude/workflows/implement-ticket.js`): optional `test_quality_findings` (array of strings; empty valid).
   Additive, no verdict effect, no gate.
2. Carry-through, option (a): an optional `test_quality_findings` field on the Architecture-Verify event row, set by `pushEvent` for
   both outcomes; `record_events.py` validates its shape; `record_hand_orchestrated_closure.py` carries it per event so the
   hand-orchestrated path also keeps it; documented in `docs/agent-monitoring/schema.md`.
3. `tools/agent-monitoring/schema_format_tail.py`: reads a named `*_SCHEMA` from the workflow JS and prints the output-format
   sentence (all property names, schema order). Both `implement-ticket` SKILL.md copies get the rule (generated, recorded
   verbatim, nothing appended when the native runtime enforces the schema).

4. Follow-up serving the same evidence purpose (asked by agent-working-design after test-architecture-reviewer's sign-off; shipped in this batch, not parked):
   `tools/agent-monitoring/arch_verify_read_check.py`, a report-only checker that prints, per test file the branch changed, whether a `Read` row
   attributed to the Architecture-Verify phase names it (READ / POSSIBLY-READ / NOT-READ / UNATTRIBUTED). No schema field, no prompt change.

## Out of Scope
- The Architecture-Verify prompt wording and `.claude/agents/architecture-reviewer.md` (test-architecture's evidence rule).
- Judging whether the reviewer's list is good (the reviewer's call). Running the real `implement-ticket` Workflow (needs the user's opt-in).
- Reconciling the two SKILL.md copies in general (the `.agents/` copy is older); only the new rule is added to both, with the drift noted.

## Acceptance Criteria
- AC1: `ARCH_VERIFY_SCHEMA` has optional `test_quality_findings` (array of strings) and it is not in `required`.
- AC2: an Architecture-Verify event pushed with findings carries every item in `test_quality_findings` (strings verbatim, other items as JSON strings, with `test_quality_findings_normalized` counting any non-verbatim item); without a reply the key is absent; `summary` stays <= 200 chars.
- AC3: `record_events.py` accepts the field when it is a list of strings (and the optional normalized count when a non-negative integer) and rejects another shape; the closure tool carries it through to the events shard.
- AC4: `schema_format_tail.py` output lists every `ARCH_VERIFY_SCHEMA` property name in schema order (including `test_quality_findings`), pinned against the real JS file so a schema change cannot drift.
- AC5: both SKILL.md copies state the rule; `docs/agent-monitoring/schema.md` documents the field.
- AC7: the checker separates the four classes, never says NOT-READ when the phase has no attributed rows, matches a path cut at 120 chars only as POSSIBLY-READ, ignores the shadow reviewer, and states its limits (Bash reads leave no Read row; attribution needs the sidecar) in its docstring.
- AC6: monitoring writes never fail the workflow because of the new field (fail-open unchanged).

## Related Tickets
- TCK-20260804-SKILL-JS-PHASE-SYNC (skill/JS drift tracking)
- TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX

## Related Docs
- docs/agent-monitoring/schema.md
- .claude/skills/implement-ticket/SKILL.md

## Related Stored Artifacts
- stored_artifacts/TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS/ (after close)

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/schema_format_tail.py
- tools/agent-monitoring/arch_verify_read_check.py
- .claude/skills/implement-ticket/SKILL.md, .agents/skills/implement-ticket/SKILL.md

## Assumptions / Open Questions
- test-architecture-implementer confirmed no conflicting edits (2026-10-02) and will not start its run 2 until this lands.
- Diff goes to test-architecture-implementer for review before merge.

## Implementation Notes
- Carry-through option (a), chosen over (b) an extra event row (phantom agent, shifts `agent_count`/seq semantics for every consumer) and (c) a side file (new write path and location convention, invisible to events consumers). Reasoning in `investigation.md`.
- Found while investigating: `record_hand_orchestrated_closure.build_records` rebuilt events from a fixed key list and dropped extras, so the field is carried there too; that is the path the test-architecture hand-orchestrated run actually uses.
- `pushEvent` gained an optional 8th parameter. Review fix (test-architecture-implementer, PR #282): the first cut kept only string items and dropped the rest, but the reviewer's own definition says only "a list" and a shadow reviewer returned objects, so an object-valued list would have vanished and "key absent" would have looked like "reviewer found nothing". Now **no item is dropped**: a string is kept as is, any other item as its JSON string, a non-array reply is wrapped as a one-item list; only an empty/null item is dropped. `test_quality_findings_normalized` (int, present only when something was not carried verbatim) says how many items were serialized, wrapped, quote-swapped or dropped. An absent key means no reply at all; `[]` means the reviewer read the tests and found nothing. The `'` to typographic-apostrophe swap stays (`writeMonitoring` embeds the events JSON in one single-quoted shell argument) and is now documented in `schema.md` and counted.
- `schema_format_tail.py` brace-matches the real JS (skipping strings/comments, handling quoted keys) and fails loudly on an unknown schema. It reproduces the key list for all 10 `*_SCHEMA` constants checked by hand; only ARCH_VERIFY_SCHEMA is pinned.
- Not touched, per test-architecture's evidence rule: the Architecture-Verify prompt text and `.claude/agents/architecture-reviewer.md`. The `.agents/` SKILL.md copy is an older fork; the rule is mirrored in both and the drift stays tracked by TCK-20260804-SKILL-JS-PHASE-SYNC.
- Known limit: on the native runtime the monitoring agent must echo the new event key. It already echoes other keys, but that can only be proven by a real run (needs the user's opt-in), so it is tested at the record_events/closure boundary and by executing pushEvent in node.

- Checker finding (not in the brief): `post_tool_hook.py` records a Read row's `input_summary` as the ABSOLUTE `file_path` cut to 120 chars. Measured on 2026-10-02: 15,921 of 43,776 Read rows (36%) are cut and 12,645 (29%) have no `run_id`. A long worktree prefix cuts many test paths, so a cut row can only ever be POSSIBLY-READ. An earlier message to design called the cut "harmless for test paths"; that was wrong and is corrected here. A fix at the source (record the repo-relative path) would remove the ambiguity but changes recorded data and is not done here. Checked against the real shards: a real run's reviewer rows give READ for a file it read and NOT-READ for a made-up one.

## Test Summary
`tests/tools/test_arch_verify_read_check.py`: 9 passed (new). `tests/tools/test_arch_verify_test_quality_findings.py`: 24 passed after the review fix (new; imports a module absent on origin/main, and its schema/doc pins fail there). Full `tests/tools` + `tests/docs`: 3500 passed, 1 failed (`test_generate_registry` real-tree drift, expected before the ticket-close registry regeneration; it passes after it). `test_workflow_runtime_acorn_parse.py`: 3 passed (the edited workflow still parses under acorn).

## Files Changed
- .claude/workflows/implement-ticket.js (schema key, `cleanFindings`, `pushEvent` param, two call sites)
- tools/agent-monitoring/schema_format_tail.py (new)
- tools/agent-monitoring/arch_verify_read_check.py (new), tests/tools/test_arch_verify_read_check.py (new)
- tools/agent-monitoring/record_events.py, tools/agent-monitoring/record_hand_orchestrated_closure.py
- tests/tools/test_arch_verify_test_quality_findings.py (new)
- docs/agent-monitoring/schema.md
- .claude/skills/implement-ticket/SKILL.md, .agents/skills/implement-ticket/SKILL.md

## Completion Summary
Architecture-Verify can carry the reviewer's advisory `test_quality_findings` into the events shard on both the pipeline and hand-orchestrated paths without hand copying, and a skill-path output-format tail is now generated from the schema key list.
