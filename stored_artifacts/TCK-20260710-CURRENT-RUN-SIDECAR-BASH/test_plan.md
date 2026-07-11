---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-CURRENT-RUN-SIDECAR-BASH
artifact_type: test_plan
tags: [agent-monitoring, workflows, data-quality]
---

# Test Plan — TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Regression Surface

No JS test runner exists for `.claude/workflows/*.js` in this repo — these files execute only
inside the Claude Code orchestration runtime, not under `pytest` or any `package.json` test
script. The regression surface is therefore entirely the Python tooling this ticket's diff is
adjacent to (must keep passing unmodified) plus the one Python test family whose *pattern* this
ticket's new test should reuse.

**Unit (`tests/tools/`)** — must keep passing, unmodified by this ticket:
- `tests/tools/test_tag_skill_mapping_check.py` — reused pattern (see New Tests Required); the
  underlying `tools/tag_skill_mapping_check.py` module itself is not touched by this ticket, so
  its own tests must show zero diff-caused regressions.
- `tests/tools/test_validate_agent_monitoring.py` — validates `docs/agent-monitoring/schema.md` /
  `tools/agent-monitoring/vocabulary.py` alignment; this ticket edits `schema.md`'s
  sidecar-attribution section (AC #4), so this suite is the closest thing to a doc/code parity
  check already in place — must still pass after the doc edit.
- `tests/tools/test_record_events.py`, `tests/tools/test_record_run.py` — `record_events.py`/
  `record_run.py` themselves are explicitly Out of Scope; these confirm zero regression from
  unrelated proximity.
- `tests/tools/test_cost_proxy.py` — `cost_proxy_score` computation is untouched; confirms no
  regression in the formula this ticket's fix feeds data into.
- `tests/tools/test_done_checker_static.py`, `tests/tools/test_architecture_reviewer_static.py`,
  `tests/tools/test_parity_updater_static.py`, `tests/tools/test_mechanics_auditor_static.py` —
  the existing static-check modules whose `bash()`-call-then-agent-judges shape this ticket's fix
  mirrors (not modified by this ticket, but good regression proof the underlying pattern is
  stable).

**Integration / arena-combat:** none — this ticket touches no `src/` simulation code, so there is
no integration or arena-combat regression surface.

## New Tests Required

Per AC #1 (Step 0b prompt text replaced by orchestrator-side `bash()` at every applicable call
site) and AC #4 (schema.md doc parity). AC #2 and AC #3 are only partially pytest-verifiable — see
notes below each.

**Category: unit / static-text regression** (new file, e.g.
`tests/tools/test_current_run_sidecar_orchestrator.py`, reusing the raw-source-text-parsing
pattern established by `tests/tools/test_tag_skill_mapping_check.py` — read
`.claude/workflows/implement-ticket.js` as plain text via `Path.read_text()`, never execute it):

1. **`test_no_step_0b_agent_prompt_sidecar_text_remains`**
   Category: unit (static-text regression).
   Verifies: the literal pattern
   `Step 0b: run \`python3 -c "import json; open('.claude/current_run'` no longer appears
   anywhere in `.claude/workflows/implement-ticket.js`'s raw source text — i.e. the agent-prompt
   free-text instruction is fully gone from all 9 original call sites (investigate, plan,
   architecture-review, implement, architecture-verify, test-scope-and-run, parity-update,
   security-review, done-check).
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py`.

2. **`test_sidecar_bash_write_precedes_each_covered_agent_call`**
   Category: unit (static-text, line-order regression).
   Verifies: for each `await agent(` call site the plan designates as in-scope (the 9 original
   sites plus Finalize, and whichever resolution Open Question #1/#2 lands on for Scope/
   implement-epic.js/create-tickets.js), a `bash(` call writing `.claude/current_run` appears in
   the source text at a strictly lower line number than the corresponding `await agent(` call, and
   with no other `await agent(` call interleaved between the write and its paired call (protects
   against a write being attributed to the wrong upcoming agent if call sites are reordered later).
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py`.

3. **`test_finalize_call_site_still_registers_sidecar`**
   Category: unit (static-text regression).
   Verifies: Finalize's call site (previously the file's only combined single-line `Step 0`) still
   has a sidecar-write `bash()` call preceding it after the refactor, and that no stray/unused
   `ts`-capture text was introduced there (Finalize's `pushEvent` call passes no `ts` argument and
   its `agent()` call has no `schema` — this must remain true).
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py`.

4. **`test_writeMonitoring_call_has_no_preceding_sidecar_write`**
   Category: unit (static-text regression) / architecture guard.
   Verifies: the `monitoring-write`-labeled `agent()` call (line ~195) is **not** preceded by a
   `.claude/current_run` write — protects the "must remain sidecar-free by design" decision
   (Risks #3 in investigation.md) from accidental "completion" by a future refactor that
   mechanically iterates over every `await agent(` site.
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py`.

5. **`test_tid_and_seq_passed_as_argv_not_json_embedded`**
   Category: unit (static-text regression) / architecture guard.
   Verifies: the relocated sidecar-write `bash()` call passes `run_id`/`seq` via `sys.argv`
   elements (mirroring `tagCheckOutput`/`archCheckOutput`/`p0ScanOutput`'s established
   individually-quoted-argv convention), not embedded as a JSON blob directly inside the
   `python3 -c "..."` string — enforces the ticket's explicit instruction and the documented
   rationale in the `p0ScanOutput` comment block (implement-ticket.js:756-763) about shell quote
   corruption.
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py`.

6. **Scope/implement-epic.js/create-tickets.js tests — conditional on plan's resolution of
   investigation.md's Open Questions #1 and #2.** If the plan extends sidecar coverage to the
   Scope (`ticket-scoper`) call site and/or to `implement-epic.js`/`create-tickets.js`, each
   newly-covered call site needs an equivalent instance of tests 1-2 above, scoped to that file. If
   the plan instead documents an explicit deferral (per the ticket's own "explicitly resolve... or
   document deferring it with rationale" requirement), no new test is required for the deferred
   file(s) — but `docs/agent-monitoring/schema.md`'s AC #4 update must still say so explicitly
   (test 7 below).
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py` (or a file-specific sibling if
   the plan splits coverage that way).

7. **`test_schema_doc_no_longer_describes_agent_self_report_mechanism`**
   Category: unit (doc/code parity).
   Verifies: `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events"
   section (currently: *"Each agent prompt includes an early Bash step that writes..."*) has been
   updated to describe the orchestrator-side `bash()` mechanism instead, and that the doc's
   statement about `create-tickets.js`'s gap (and, depending on Open Question #2's resolution,
   `implement-epic.js`'s previously-undocumented identical gap) is accurate post-fix. Could extend
   `tests/tools/test_validate_agent_monitoring.py` if that module already asserts doc content, or
   be a new lightweight text-search assertion.
   Lives in: `tests/tools/test_current_run_sidecar_orchestrator.py` or
   `tests/tools/test_validate_agent_monitoring.py` (whichever the implementer finds has the
   better-fitting existing fixture setup).

**Category: integration / manual verification (cannot be pytest-automated)**

8. **Live end-to-end workflow run — satisfies AC #2's literal wording.**
   Category: integration (manual, not pytest).
   Verifies: running `/implement-ticket` (or `/implement-epic`) end-to-end after this fix lands
   produces non-null/non-empty `tool_call_count`/`cost_proxy_score` in
   `agent-monitoring/events.jsonl` for every phase — with the Step 0b prompt text now structurally
   absent from every prompt (not just "the agent happened to comply this time," which is exactly
   the failure mode this ticket exists to eliminate). This cannot be expressed as a `pytest`
   assertion since it requires actually dispatching agent calls through the Claude Code runtime.
   Must be documented as a manual verification step in the ticket's own Test Summary / Completion
   Summary at close (see investigation.md Risks #4) — do not claim AC #2 is "tested" by test 1-2
   alone; those only prove the structural precondition, not the runtime outcome.

## Scoped Pytest Commands

```
pytest tests/tools/test_tag_skill_mapping_check.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_cost_proxy.py -v
```

Plus, once the new test file exists:

```
pytest tests/tools/test_current_run_sidecar_orchestrator.py -v
```

Never `pytest tests/` — this ticket's diff is confined to `.claude/workflows/*.js` orchestration
text and `docs/agent-monitoring/schema.md`; scope stays within `tests/tools/` (no `src/` or
simulation-domain tests are relevant).

## Anti-Drift Test Guards

- **`test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`** — asserts the exact
  `Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`...` text is still present, byte-identical, at all 9
  original two-line call sites after the diff. Proves this ticket's edit didn't slurp sibling
  ticket `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`'s (C2) adjacent scope — the two `Step 0`/
  `Step 0b` lines sit immediately next to each other at every one of these 9 sites, making
  accidental co-editing the single highest-probability drift risk for this ticket.
- **`test_record_events_required_fields_unchanged`** — asserts `record_events.py`'s `REQUIRED`
  field set (or equivalent validation surface) is unmodified — guards the ticket's explicit
  Out-of-Scope boundary ("Any change to record_events.py's REQUIRED-field validation logic itself
  ... is out of scope").
  Reuses `tests/tools/test_record_events.py`'s existing fixtures if a suitable assertion already
  exists there; otherwise add as a single new assertion rather than a new test file.
- **`test_writeMonitoring_step5_sidecar_clear_still_present`** — asserts the
  `printf '{}' > .claude/current_run` clear step inside `writeMonitoring` (implement-ticket.js
  Step 5, line ~236-237) is still present, unchanged, and unreordered relative to Steps 1-4 — this
  is the only sidecar-clearing mechanism in the file; losing it silently while refactoring nearby
  sidecar-write code would leave stale `run_id`/`seq` bleeding into the next run's Scope-phase
  tool calls (compounding, not fixing, investigation.md Risks #1).
- **`test_idea_doc_four_related_ideas_untouched`** — not a strict necessity as an automated test,
  but recommend a plan.md checklist item (not a pytest assertion) confirming none of the 4
  "related, smaller ideas" from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`
  (asymmetric gate coverage, cross-retro trend detection, tag→skill dedup consolidation,
  `working_log.csv` backfill) were touched — these are explicitly Out of Scope and the tag→skill
  dedup idea in particular references the same `implement-ticket.js` file this ticket edits.
