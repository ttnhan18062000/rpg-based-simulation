---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-COST-PROXY-EPIC-TICKETS
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20260904-COST-PROXY-EPIC-TICKETS

## Regression Surface

Existing tests that must keep passing (all confirmed currently passing via
`.venv/bin/python3 -m pytest` — 51/51 across these 3 files as a baseline; the repo's bare `python3`
lacks `pydantic` and cannot run these at all, use the project venv):

**Unit — `tools/agent-monitoring/`**
- `tests/tools/test_record_events.py` — all existing tests, especially:
  - `test_compute_tool_stats_only_targets_implement_ticket_workflow` (L264) — must be re-examined:
    once the filter widens, its own name becomes misleading (it no longer "only" targets
    implement-ticket) and its mixed-batch assertion (`EPIC-TCK-MIXED-BATCH` must NOT appear in the
    result) will need to flip once implement-epic is included — see New Tests Required.
  - `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` (L249) — WILL break by
    design once the filter widens (see below); must be rewritten, not left passing by accident.
  - All non-`compute_tool_stats`-related tests (`validate_record`, `warn_vocabulary_drift`,
    summary truncation, unified week-folder writing) — unrelated to this change, must stay green.
- `tests/tools/test_cost_proxy.py` — `compute_cost_proxy_score()` formula itself is explicitly out
  of scope per the ticket's own "Out of Scope" bullet; must remain 100% unmodified and passing.
- `tests/tools/test_current_run_sidecar_orchestrator.py` — all existing tests target
  `implement-ticket.js` specifically; must stay green untouched, especially
  `test_writeMonitoring_call_has_no_preceding_sidecar_write` (the precedent this ticket's L131
  decision must not silently contradict) and `test_finalize_call_site_still_registers_sidecar`
  (confirms the dual-write `writeSidecar` shape stays intact — the shape any new
  implement-epic.js/create-tickets.js sidecar writer must mirror).
- `tests/tools/test_validate_agent_monitoring.py` — vocabulary single-source-of-truth guard; must
  confirm `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` for `implement-epic`/`create-tickets` are unaffected
  by this change (this ticket does not touch `vocabulary.py`'s phase/agent vocab, only
  `record_events.py`'s filter).

**Integration**
- A live `implement-epic` and a live `create-tickets` run producing real
  `agent-monitoring/data/<week>/{events,tools}.jsonl` rows is the acceptance-criteria-level
  integration surface, but is not a repeatable pytest — covered by the acceptance criteria directly
  ("a real implement-epic run's events.jsonl rows have non-null ... matching real
  (run_id,seq)-grouped tools.jsonl rows"). The scoped pytest commands below verify the deterministic
  compute logic in isolation; a real run is the final acceptance check, not a unit test.

**Arena-combat**: not applicable — this ticket touches no combat/mechanics code.

## New Tests Required

1. **`test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets`**
   (rename/replace of `test_compute_tool_stats_only_targets_implement_ticket_workflow`)
   - Category: unit
   - Verifies: a 3-way mixed batch — one `TCK-...` record, one `EPIC-...` record, one
     `CREATE-TICKETS-...` record, each with a matching `tools.jsonl` fixture row — all three
     compute non-null `(tool_call_count, cost_proxy_score)` tuples, and a `SIMQ-AUDIT-...` record in
     the same batch is still excluded (asserts the widened filter is a membership check against
     exactly `{implement-ticket, implement-epic, create-tickets}`, not "any known workflow" and not
     "not None").
   - Location: `tests/tools/test_record_events.py`

2. **`test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl`**
   (rewrite of `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar`, per the
   ticket's own Acceptance Criteria — "updated (not left contradicting) to assert non-null values
   with a corrected docstring/comment reflecting the reversed design decision")
   - Category: unit
   - Verifies: `EPIC-`/`FOLDER-`/`CREATE-TICKETS-` prefixed records with real matching
     `tools.jsonl` fixture rows (via `_write_tools_jsonl`) now compute real non-null
     `(tool_call_count, cost_proxy_score)` values — mirroring
     `test_compute_tool_stats_only_targets_implement_ticket_workflow`'s existing fixture pattern
     applied to the newly-included workflows. Docstring must explicitly state this reverses
     `TCK-20260719-COST-PROXY-WRITE-PATH`'s prior exclusion and why (scope-discipline, not a
     technical constraint — see investigation.md's Prior Work section).
   - Location: `tests/tools/test_record_events.py`

3. **`test_zero_tool_call_no_sidecar_paths_compute_zero_not_null`** (covers investigation.md Risk 5
   — implement-epic.js's 2 fire-and-forget bash-only early-return paths)
   - Category: unit
   - Verifies: an `EPIC-...`/`FOLDER-...` record at `seq: 1` with **no** matching `tools.jsonl`
     rows at all computes to `(0, 0.0)`, not an omitted key and not an error — this is the correct,
     intentional behavior for the 2 non-standard call sites (L184-193, L209-219 in
     implement-epic.js) that never call `agent()` and so never get a `writeSidecar()` call.
   - Location: `tests/tools/test_record_events.py`

4. **Static source-text guard(s) for the actual implemented call-site coverage** — the concrete test
   name(s) depend on the implementer's chosen `writeSidecar`-equivalent shape for each file, but at
   minimum:
   - **Architecture guard**: `create-tickets.js`'s `writeMonitoring` `agent()` call (L131 region,
     `label: 'monitoring-write'`) either (a) explicitly excluded from sidecar coverage — assert no
     sidecar-write call precedes it, mirroring
     `test_writeMonitoring_call_has_no_preceding_sidecar_write`'s exact pattern against
     `create-tickets.js` instead of `implement-ticket.js` — or (b) if the implementer deliberately
     chooses to cover it anyway, a test explicitly documenting and justifying that deviation from
     the `implement-ticket.js` precedent. One of these two must exist; silence on this point is not
     acceptable given the direct precedent conflict identified in investigation.md.
   - **Architecture guard**: every real, non-fan-out `agent()` call site in `implement-epic.js`
     (86, 287, 316, 353) and `create-tickets.js` (156, 439, 796, 818) that IS given sidecar coverage
     has its sidecar-write call immediately preceding the corresponding `agent()` call — same
     adjacency-proof pattern as `tests/tools/test_current_run_sidecar_orchestrator.py`'s existing
     `test_sidecar_bash_write_precedes_each_covered_agent_call`, applied to the two newly-covered
     files.
   - **Architecture guard**: the new sidecar writer(s) in `implement-epic.js`/`create-tickets.js`
     write both the unscoped `.claude/current_run` file AND the session-scoped
     `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` copy — mirroring
     `test_write_sidecar_also_writes_session_scoped_copy`'s exact assertion shape, applied to the
     new writer function(s). A single-file sidecar writer here would silently reintroduce the
     cross-session collision `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` fixed.
   - Location: new test module (e.g. `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py`)
     or an added section in `tests/tools/test_current_run_sidecar_orchestrator.py` — implementer's
     call, but should not scatter static source-text assertions for these 2 files across unrelated
     test files.

5. **Fan-out `seq` collision guard** (covers investigation.md Risk 4 — create-tickets.js L304/L659)
   - Category: unit / architecture guard
   - Verifies: if the implementer adds sidecar coverage to the two `pipeline()`-based fan-out sites
     (`investigate:${concern.id}`, `write:${task.short_scope}`), each fan-out iteration is assigned
     a distinct `seq` before its `agent()` call — either by static source-text inspection (each
     iteration's `writeSidecar`-equivalent call reads a per-item index, not a shared counter
     variable mutated across awaited-in-parallel iterations) or, if the implementer instead
     concludes `pipeline()` is effectively sequential in this harness and no collision is possible,
     a test/comment recording that conclusion explicitly rather than leaving it unstated. Do not
     accept an implementation that adds fan-out sidecar coverage with no test addressing this risk.
   - Location: same module as item 4.

6. **Mixed-batch independence test** (explicit Acceptance-Criteria item: "confirms
   implement-ticket/implement-epic/create-tickets buckets compute independently without
   cross-contamination")
   - Category: unit
   - Verifies: a single `--data` batch containing one record from each of the 3 covered workflows,
     each with its own distinct `tools.jsonl` fixture rows under different `(run_id, seq)` keys,
     computes exactly the right values for each — no cross-bucket leakage (e.g. an implement-epic
     record's `tools.jsonl` rows never counted toward an implement-ticket record's stats or vice
     versa). This can likely be folded into test #1 above rather than written as a fully separate
     test, but must exist somewhere as an explicit, named assertion.
   - Location: `tests/tools/test_record_events.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_record_events.py tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py -q
```

Add the new sidecar-orchestrator-guard module if created separately:
```
.venv/bin/python3 -m pytest tests/tools/test_record_events.py tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py -q
```

Never `pytest tests/` — this ticket's blast radius is `tools/agent-monitoring/record_events.py` and
the two orchestrator `.js` files; scope to `tests/tools/` monitoring-related modules only. Use the
project's `.venv/bin/python3`, not bare `python3` (bare `python3` lacks `pydantic` and cannot even
collect `tests/conftest.py` in this environment — confirmed during this investigation).

## Anti-Drift Test Guards

- **`simq-audit` non-interference**: any new membership-set test for `compute_tool_stats()`'s widened
  filter must include a `SIMQ-AUDIT-...` record in the same batch and assert it is excluded from the
  result — guards against a future "just check `infer_workflow(...) is not None`" simplification
  that would silently start overriding `simq-audit.js`'s own separate (still LLM-computed, still
  unfixed) TOOL_STATS values.
- **`test_cost_proxy.py` untouched**: the formula (`compute_cost_proxy_score`) itself is explicitly
  out of scope; a diff touching `cost_proxy.py`'s weights or formula logic is scope creep and should
  fail review even if `test_cost_proxy.py` still happens to pass.
- **No historical backfill**: no new test should assert that pre-existing (already-written) null
  `implement-epic`/`create-tickets` event rows in `agent-monitoring/data/*/events.jsonl` get
  retroactively populated — that is explicit Out of Scope. A test asserting forward-only behavior
  (only newly-written records after this ships are affected) is correct; a test asserting a backfill
  script exists or ran is scope creep.
- **`writeMonitoring`/L131 precedent guard**: whichever way the L131 open question (investigation.md)
  is resolved, a test must exist that makes the decision explicit and would fail if a future,
  unrelated change silently added or removed sidecar coverage there without updating the test —
  this is the single highest-risk silent-regression point identified in this ticket, since it
  directly parallels a pattern (`writeMonitoring`'s own untracked `agent()` call) that has already
  had one empirically-confirmed ~35% mis-attribution bug (`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`)
  in the `implement-ticket.js` analog.
- **implement-epic.js's 2 non-standard bash-only sites stay bash-only**: a test should assert these
  two early-return paths (`request` mode with no children yet; `ticketIds.length === 0`) still write
  their `record_events.py` call via direct `bash()`, not via a newly-introduced `agent()` wrapper —
  converting them to agent() calls just to give them sidecar coverage would be an unnecessary,
  unscoped behavior change to code paths that currently work correctly and terminate the workflow
  immediately after.
