---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-UPDATE-DISCIPLINE
artifact_type: test_plan
tags: [workflows, documentation]
---

# Test Plan — TCK-20260802-DOC-UPDATE-DISCIPLINE

## Regression Surface

Existing tests that must keep passing unmodified:

- `tests/tools/test_doc_staleness_check.py` — all 9 tests (behavior_changed=false passes,
  test-only-change passes, src/-with-no-docs FAILs, workflow-js-with-no-docs FAILs, both
  happy-path-with-docs PASS, no-files-changed PASS, non-.js-under-.claude/workflows PASS, CLI
  MARKER: contract tests).
- `tests/tools/test_doc_staleness_gate_wiring.py` — all 5 static-source tests (invocation ordering,
  single pushEvent, no reason_code, writeMonitoring-before-return ordering, bash() invocation line
  contract).

## New Tests Required

**`tests/tools/test_doc_staleness_check.py`** (extend):
- `test_config_path_change_with_behavior_changed_true_and_no_docs_path_fails` — `files_changed=
  ["config/simulation_quality/scoring_weights.yaml"]`, `behavior_changed=True` → `FAIL`, evidence
  mentions the config path.
- `test_config_path_change_with_behavior_changed_true_and_a_docs_path_passes` — same but with a
  `docs/` path present → `PASS`.
- `test_docs_to_update_all_present_no_advisory` — `files_changed` includes every path in
  `docs_to_update` → result list has no `ADVISORY` entry.
- `test_docs_to_update_missing_path_adds_advisory_not_fail` — `docs_to_update` includes a path not
  in `files_changed`, but a docs/ path IS present (existing gate PASSes) → result list has a `PASS`
  entry (unchanged) plus a separate `ADVISORY` entry naming the missing path; overall list does NOT
  contain a `FAIL`.
- `test_docs_to_update_empty_list_no_advisory` — `docs_to_update=[]` (or omitted) → no `ADVISORY`
  entry, output identical in shape to pre-change behavior.
- `test_docs_to_update_ignored_when_fail_branch_taken` — `behavior_changed=True`, a flagged path,
  no docs/ path at all, AND a non-empty `docs_to_update` → still exactly one `FAIL` entry, no
  `ADVISORY` entry appended (FAIL returns early, by design).
- CLI: `test_cli_docs_to_update_sentinel_parses_correctly` — subprocess call with
  `["true", "src/foo.py", "docs/engine/x.md", "--docs-to-update", "docs/engine/y.md"]` → MARKER:
  JSON includes an `ADVISORY` entry mentioning `docs/engine/y.md`.
- CLI backward-compat: confirm the two existing CLI tests
  (`test_cli_entrypoint_prints_marker_prefixed_json`,
  `test_cli_entrypoint_passes_when_docs_path_included`) still pass with zero code changes to the
  test file itself (no `--docs-to-update` token present in either call).

**`tests/tools/test_doc_staleness_gate_wiring.py`** (extend):
- `test_docs_to_update_args_passed_to_doc_staleness_invocation` — static source check that the
  bash() invocation line (or the block immediately preceding it) references
  `investigation.docs_to_update` / `docsToUpdateArgs`.
- Re-verify (no code change needed, just re-run) the existing single-`pushEvent`/no-`reason_code`/
  `writeMonitoring`-ordering tests still pass against the modified block — these are the tests most
  at risk of breaking from the advisory-summary refactor (Step 5 of plan.md).

**New file `tests/tools/test_finalize_knowledge_index_refresh.py`** (static source test, mirrors
`test_doc_staleness_gate_wiring.py`'s pattern — no JS test runner exists for `.claude/workflows/*.js`):
- `test_finalize_runs_knowledge_index_update_after_selfcheck` — `make knowledge-index-update`
  appears in `implement-ticket.js`, positioned after `run_finalize_selfcheck` and before the final
  `return { status: 'DONE', ...}`.
- `test_knowledge_index_refresh_is_fail_open` — the block containing `knowledge-index-update` does
  not contain a `return` statement with a new blocking status (confirms it can't regress `DONE`).
- `test_knowledge_index_refresh_is_orchestrator_bash_not_agent_prompt` — `make knowledge-index-update`
  does not appear inside the Finalize `agent(...)` prompt string (between the Finalize
  `phase('Finalize')` call and its closing `{ label: 'finalize' }`) — must be a top-level `bash()`
  call, not agent-prompt text (reliability requirement from `docs/ai/ticket-lifecycle.md`'s existing
  caveat).

**`.claude/agents/investigator.md`**: no automated test exists for agent prompt-doc files in this
repo (confirmed — no `tests/` coverage of `.claude/agents/*.md` content). Verified by manual review
only: the `## Docs Requiring Update` section and `docs_to_update` return field are present and
match the JS schema field name exactly.

## Scoped Pytest Commands

```
pytest tests/tools/test_doc_staleness_check.py tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_finalize_knowledge_index_refresh.py -v
```

## Anti-Drift Test Guards

- The `test_docs_to_update_ignored_when_fail_branch_taken` case guards against accidentally
  reordering the check so `ADVISORY` gets appended even when `FAIL` already fired — that would
  silently change the returned list's shape and could confuse anything doing
  `results.find(r => r.status === 'FAIL')` expecting a single-entry list on failure.
  (`implement-ticket.js`'s own lookup uses `.find`, which is safe either way, but the Python-level
  contract should stay exactly-one-entry-on-FAIL for clarity.)
- `test_knowledge_index_refresh_is_orchestrator_bash_not_agent_prompt` guards specifically against
  reintroducing the exact reliability failure mode `docs/ai/ticket-lifecycle.md`'s Reliability
  caveat already documents for the post-Test cleanup checkpoint — the whole point of this step is to
  close a silently-skipped gap, so it must not become another one.
