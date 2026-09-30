---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT
artifact_type: investigation
tags: [workflows, create-tickets, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT

Most of the blocking-condition investigation was already done by `agent-working-design` before
this ticket was handed off (confirmed-by-trying, restated verbatim in the ticket's Request
Summary — not re-derived here). This document covers what this ticket's own implementation pass
additionally found while making the changes.

## Confirmed blockers (as handed off, verified again before editing)

Ran an acorn parse check (`frontend/node_modules/acorn`, from the main checkout — this worktree's
own `frontend/node_modules/` is not installed; symlinked locally for verification, gitignored) with
`{ecmaVersion: 'latest', sourceType: 'module', allowReturnOutsideFunction: true,
allowAwaitOutsideFunction: true}` against `create-tickets.js` before any edit:

```
create-tickets.js PARSE_FAIL: Unexpected token (613:10)
```

Line 613 was `(see \`python3 tools/tag_registry.py list\`)` inside the Structure-phase prompt's
outer template literal — an unescaped nested backtick. After escaping it and re-parsing, a second
failure surfaced at line 778 (`\`python3 tools/layer_registry.py list\`` inside the Write-phase
prompt), confirming the ticket's claim that both sites needed fixing, not just the first one the
parser reports (acorn stops at the first syntax error per file).

## `bash(` call sites (re-confirmed via grep after understanding the file)

Exactly 4, matching the ticket's count:
- `captureTs()` (was line ~131) — used once, at the Comprehend-phase entry.
- `writeSidecar()` (was line ~161) — the function itself has 1 `bash()` call; it's invoked 4 times
  (comprehend, structure, write-sequence, link-epic).
- `clearSidecar()` (was line ~187) — 1 `bash()` call, invoked once inside `writeMonitoring`.
- The tag-registry check (was line ~679) — 1 `bash()` call, invoked once (conditionally, only
  when the batch has any tags at all).

## New finding: `execution_mode` semantics needed clarifying before the code change

The ticket's Scope item 4 says `execution_mode` becomes `"workflow"` "for native runs." Read
literally, that could suggest branching on whether the *current* execution is native vs.
hand-narrated. That's not possible — and not needed. `create-tickets.js`'s own JS source is never
actually interpreted at all during hand-narration (an LLM reads the file and manually issues the
equivalent tool calls without executing the JS) — so this exact code path, including the literal
string passed to `record_run.py --data`, only ever runs for real when the native `Workflow` tool
executes the script. The literal can therefore simply be `"workflow"` unconditionally; hand-
narration (kept only as a fallback per Scope item 5) is instructed separately, in `SKILL.md`, to
use `"pipeline"` instead when that fallback path is taken — this is now stated explicitly in the
rewritten `SKILL.md` rather than left implicit.

## New finding: `test_run_execution_mode_field_wiring.py` and `test_step0_ts_orchestrator.py` pin
the exact old literals this ticket removes

`test_every_record_run_call_site_sets_execution_mode_pipeline` asserted `"execution_mode":"pipeline"`
for every `record_run.py` call site in all 4 workflow files, including `create-tickets.js`'s one
site — this needed to become per-file (`create-tickets.js` → `"workflow"`, the other 3 unchanged).
`test_ts_capture_bash_precedes_each_covered_agent_call` and
`test_captureTs_helper_defined_once_after_writeSidecar` both asserted `create-tickets.js` *has* a
`captureTs()` helper and a `startTs = comprehendTs || null` reassignment — both needed to flip to
asserting their *absence*, since `captureTs()` was removed entirely (the native runtime has no
`bash()` for it to call) rather than kept as unreachable dead code.

## New finding: two golden/fixture tests pin the exact rendered "By execution mode" table text

`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` and
`test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture` both compare
`generate()`'s full report output against a literal `_FIXED_CORPUS_EXPECTED_REPORT` string —
adding the "Native workflow" row to the rendered table (Scope item 4) broke both until that
literal was updated to include the new row. Found only by running the full
`test_generate_retro.py` suite, not by reading `generate_retro.py` alone.

## Real, incidental finding: this worktree's test run folds other sessions' pending monitoring
shards into the canonical files

Running `pytest tests/tools/test_generate_retro.py` (specifically the real-corpus tests that call
`generate_retro._load_source()`/trigger an on-demand index rebuild) consolidated 10 other
sessions' per-branch `agent-monitoring/data/2026-W{39,40}/*.jsonl` shard files into the canonical
week files and deleted the originals — a known, previously-documented trap (see
`.claude/handover/agent-working-design.md`'s own "Traps" section: "running generate_retro.py or
done_checker_static.py in a review checkout folds the pending shards into the canonical files
(restore them; they're not branch defects)"). Restored via `git checkout --` on all 10 paths;
their content was safely folded into the canonical files first, so nothing was lost — only the
per-branch shard *files'* continued existence needed restoring, per that established precedent.

## Pilot proposal selection

Needed a real, small, not-yet-ticketed proposal to run the native pilot against (Scope item 6).
Checked two natural candidates first and found both already fully shipped (a useful finding in its
own right, written up as `docs/plans/idea_stale_planning_doc_status_after_ship.md` and piloted
into `TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR` as the pilot's real output):
- `docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md` (`status: idea`) —
  already shipped as `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` /
  `TCK-20260822-DASHBOARD-DURATION-GAP-AWARE`, never archived or status-updated.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` items 3–4 —
  already shipped as `TCK-20260904-WORKING-LOG-CSV-PARSER` /
  `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`, still marked "ready, schedule later."

## Related Tickets / Docs
Per the ticket's own Related Tickets / Related Docs sections — not duplicated here.
