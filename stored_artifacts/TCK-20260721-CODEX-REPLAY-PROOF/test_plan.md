---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PROOF
artifact_type: test_plan
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260721-CODEX-REPLAY-PROOF

## Regression Surface

This ticket creates new, isolated files only (a fixture spec doc, at least one fixture data file,
a replay runner script, and its tests). Nothing in `.claude/workflows/implement-ticket.js`,
`tools/agent-monitoring/*.py`, or `tools/gate_checks/*.py` is modified — so the regression surface
is about proving those files stay untouched and their read-only use is correct, not about
re-running their own full suites end-to-end.

**Unit / static (must keep passing — the runner imports these read-only):**
- `tests/tools/test_plan_gate_static.py` (if it exists — covers `plan_gate_static.py`)
- `tests/tools/test_parity_ledger_scan.py` / equivalent for `parity_ledger_scan.py`
- `tests/tools/test_architecture_reviewer_static.py` (if it exists)
- `tests/tools/test_done_checker_static.py`
- `tests/tools/test_tag_registry.py` (covers `tag_registry.check_tags_registered`)

**Integration / process-boundary (must keep passing — proves the forbidden scripts' own behavior
is unaffected by this ticket, even though this ticket never calls them):**
- `tests/tools/test_post_tool_hook.py`
- `tests/tools/test_monitoring_bypass_fix.py`

**Monitoring corpus integrity (must keep passing — same class of guarantee this ticket's own
snapshot test extends):**
- Any existing `tests/tools/test_*.py` that asserts `agent-monitoring/*.jsonl` append-only
  behavior or schema validity (e.g. a `validate.py`-adjacent test, if present under
  `tests/tools/`).

Run `grep -rl "record_run\|record_events\|post_tool_hook\|pre_tool_hook" tests/tools/*.py` at
Implement/Test time to get the exact current list — the file inventory above is derived from what
was read during Investigate and may miss a file added after this investigation.

## New Tests Required

Per AC #1-5, each maps to at least one concrete new test:

1. **`test_fixture_envelope_schema_validates_required_fields`**
   Category: unit
   Verifies: the fixture-loading/validation function (part of the replay runner module) accepts a
   well-formed fixture matching the versioned envelope spec, and correctly identifies each
   AC-required field (phase, agent, recorded input, recorded output, transition/outcome, envelope
   `version`).
   Location: `tests/tools/test_replay_fixture_envelope.py` (new)

2. **`test_real_fixture_set_loads_and_validates`**
   Category: integration
   Verifies: the at least-one real, checked-in fixture set (AC #1) — derived from a real completed
   ticket's `tickets/done/` + `stored_artifacts/` + `agent-monitoring/events.jsonl` slice, per the
   investigation's recommendation (`TCK-20260721-ORCHESTRATION-CONTRACT-ADR` or whichever ticket
   Plan phase selects) — loads without error and passes envelope validation. This is the test that
   proves the checked-in fixture is not a synthetic stub.
   Location: `tests/tools/test_replay_fixture_envelope.py` (new)

3. **`test_replay_runner_completes_against_real_fixture`**
   Category: integration
   Verifies: the replay runner/adapter executes the chosen implement-ticket slice (per Plan
   phase's scoped phase range) against the real fixture and completes without raising, reproducing
   the same phase sequence / transition outcomes the fixture records as having actually occurred.
   Location: `tests/replay/test_replay_runner.py` (new) or co-located next to the runner module,
   per whatever path Plan phase assigns the runner (e.g. `tools/agent-replay/`).

4. **`test_replay_runner_never_calls_forbidden_monitoring_scripts` (source-level, AC #2)**
   Category: architecture guard (static source-text scan — mirrors
   `tests/tools/test_monitoring_bypass_fix.py`'s established pattern of `Path.read_text()` +
   substring/AST scanning against a source file, applied here to the **replay runner's own new
   Python source**, not to `implement-ticket.js`).
   Verifies: reads the replay runner's own `.py` source text (and any helper module it imports
   from within the new fixture/runner package) and asserts:
   - none of the literal strings `"post_tool_hook.py"`, `"pre_tool_hook.py"`, `"record_run.py"`,
     `"record_events.py"` appear inside any `subprocess`/`os.system`/`bash`-style call construction
     anywhere in the source;
   - no `import record_run`, `from record_run import ...`, `import record_events`, `from
     record_events import ...`, `import post_tool_hook`, `import pre_tool_hook` (or equivalent
     `importlib.import_module(...)` calls naming those modules) exists anywhere in the source;
   - a fake/no-op recording function (e.g. `_fake_write_monitoring`, `_fake_hook_boundary`) *does*
     exist and *is* what the runner calls in place of the real writers.
   This is process-level (source-code) evidence, not output-diffing — must be a separate assertion
   from test #6 below, per the ticket's explicit "not merely by output-diffing" requirement.
   Location: `tests/replay/test_replay_runner_no_forbidden_calls.py` (new)

5. **`test_replay_runner_fails_clearly_on_missing_required_fixture_field` (AC #4)**
   Category: unit
   Verifies: given a fixture with one required envelope field deliberately removed (e.g. the
   recorded `output` for one phase, or the envelope `version` field), the runner raises an
   exception / exits non-zero with an error message naming the missing field — and does **not**
   proceed to replay any further phases, print a swallowed warning, or produce a "partial success"
   result. Parametrize over at least 2-3 distinct required fields to catch a validator that only
   checks one field and silently accepts the rest missing.
   Location: `tests/tools/test_replay_fixture_envelope.py` (new) or
   `tests/replay/test_replay_runner.py`, whichever module owns the validation entry point.

6. **`test_replay_run_produces_zero_diff_in_tickets_and_monitoring_corpus` (AC #3)**
   Category: integration / snapshot
   Verifies: runs `git status --porcelain -- tickets/ agent-monitoring/*.jsonl` (or, if the
   working tree may already be dirty from unrelated work, an explicit `git stash`/clean-check
   guard first, or a content-hash snapshot taken immediately before/after rather than relying on
   ambient git cleanliness) before invoking the replay runner **against the real repo tree** (not
   a `tmp_path` copy that could trivially "pass" by never touching anything real — see Anti-Drift
   Test Guards below), then re-checks after the run completes, and asserts the two snapshots are
   identical (byte-for-byte, per AC #3's literal wording). This directly mirrors
   `implement-ticket.js`'s own existing `touchedOutput = await bash('git status --porcelain --
   docs/parity_ledger/')` precedent (line 971) — reusing an established, already-working pattern
   in this exact codebase rather than inventing a new snapshot mechanism.
   Location: `tests/replay/test_replay_no_mutation_snapshot.py` (new)

7. **`test_fixture_envelope_shape_matches_adr_contract_representation` (AC #5)**
   Category: architecture guard
   Verifies: the fixture specification document (and/or the loader's format choice) is evaluated
   against `docs/architecture/agent_orchestration_contract.md`'s Decided sections — at minimum, a
   test/check that the envelope's chosen format (YAML per the investigation's recommendation, or
   whatever Plan phase confirms) is explicitly justified in the spec doc's own text with a
   citation to the ADR, not silently picked. This can be a documentation-content assertion (read
   the spec doc, assert it contains a cross-reference to
   `docs/architecture/agent_orchestration_contract.md`) rather than a runtime behavior test, since
   AC #5 is fundamentally a documentation/evaluation requirement.
   Location: `tests/tools/test_replay_fixture_spec_doc.py` (new) — static content check, similar in
   spirit to `tests/tools/test_monitoring_bypass_fix.py`'s doc/source cross-referencing style.

## Scoped Pytest Commands

```
pytest tests/tools/test_replay_fixture_envelope.py tests/tools/test_replay_fixture_spec_doc.py -v
pytest tests/replay/ -v
pytest tests/tools/test_monitoring_bypass_fix.py tests/tools/test_post_tool_hook.py -v
pytest tests/tools/test_plan_gate_static.py tests/tools/test_done_checker_static.py -v
```

Never `pytest tests/`. If Plan phase places the runner under a different path than
`tests/replay/` (e.g. colocated under `tests/tools/`), adjust the second command accordingly —
scope stays to the new replay-proof files plus the specific existing gate-check/hook tests the
runner depends on (read-only), never the full suite.

## Anti-Drift Test Guards

- **The no-mutation snapshot test (New Test #6) must run against the real repository tree, not an
  isolated `tmp_path` copy of it.** `tests/tools/test_post_tool_hook.py`'s `tmp_path`-isolated-cwd
  pattern exists to test the *hook itself*; reusing that isolation to run the replay proof against
  an empty/scratch directory would make the snapshot assertion vacuously true (nothing real to
  mutate) and would not actually prove the real `tickets/**`/`agent-monitoring/*.jsonl` were
  untouched. If test infrastructure concerns (parallel test runs, CI sandboxing) require some
  isolation, the test must additionally assert that the replay runner's hard-coded/configured
  target paths for the "must not mutate" check equal the real `tickets/` and `agent-monitoring/`
  paths relative to repo root — not merely that *some* directory came back unchanged.
- **New Test #4 (no forbidden calls) must not be satisfiable by an output-diff test alone.** A
  reviewer could be tempted to consider New Test #6 sufficient proof of AC #2 ("it produced no
  monitoring writes, therefore it must not have called the writers") — the ticket explicitly
  rejects this ("verified by process-level evidence... not merely by output-diffing"). Keep these
  two tests structurally separate; a PR/diff that only adds #6 and treats it as covering AC #2 is
  a gap, not a pass.
- **New Test #5 (fail-clearly on missing field) must assert a raised exception or non-zero exit,
  not a printed warning.** This repo's dominant existing convention (agent-monitoring writers,
  `writeMonitoring` in `implement-ticket.js`) is deliberately **fail-open** ("monitoring write
  failure must never fail the workflow" — CLAUDE.md hard rule). The replay runner is a **deliberate
  inversion** of that convention (AC #4: "fails clearly, not silently"). A test author reflexively
  copying the fail-open convention from elsewhere in this codebase would silently violate this AC —
  the test must catch that regression explicitly (e.g. `pytest.raises(...)` or asserting a non-zero
  `returncode`/`sys.exit` call, never merely asserting a log line was printed).
  
- **New Test #4's forbidden-call scan must include import-based bypass, not just subprocess-string
  matching.** A narrower implementation that only greps for the four filenames inside
  `subprocess.run(...)`/shell-command strings would pass a runner that instead does
  `from tools.agent_monitoring.record_run import main; main()` — a real, importable bypass, since
  `record_run.py`'s `main()` is a plain function, not stdin-gated like the two hook scripts. The
  test must scan for both invocation shapes.
- **Real-fixture test (New Test #2) must not silently accept a synthetic/invented fixture as
  satisfying AC #1's "at least one real recorded fixture set."** If Plan/Implement end up
  constructing the checked-in fixture from hand-written example data rather than a genuine
  completed ticket's real `tickets/done/` + `stored_artifacts/` + `events.jsonl` content, this test
  (or a sibling doc-content check) should fail or flag it — e.g. by asserting the fixture's
  `ticket_id`/`run_id` field matches a real entry actually present in `agent-monitoring/runs.jsonl`
  and a real file actually present under `tickets/done/`.
- **Do not let the "regression surface" list above cause this ticket to silently expand into
  modifying `tools/gate_checks/*.py` "to make it more replay-friendly."** If a new test reveals
  that a gate-check function is hard to call read-only from outside its current `bash -c` wrapper,
  that is a finding to report at Verify/Plan-deviation, not a license to refactor production gate
  logic under this ticket's Out-of-Scope containment rule.
