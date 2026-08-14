---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-DECISION
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260721-MONITORING-WRITER-DECISION

## Regression Surface

This ticket is decision/evidence-only — it must produce zero diffs to any production
monitoring writer path. The regression surface below exists to *prove* that non-touching,
not because this ticket's own deliverable requires these suites to be re-run for its own
correctness.

**Unit / hook tests (must remain byte-for-byte unaffected — confirm via `git status` after
implementation, not by re-running and expecting different results):**
- `tests/tools/test_post_tool_hook.py` — all 4 tests
  (`test_single_writer_produces_one_well_formed_line`,
  `test_phase_and_agent_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`,
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`,
  `test_locking_failure_does_not_propagate`) must still pass, unmodified, since
  `post_tool_hook.py` is not touched by this ticket.
- `tests/tools/test_validate_agent_monitoring.py` — must still pass; `validate.py` is
  read-only against the real corpus and not modified by this ticket.
- `tests/tools/test_monitoring_bypass_fix.py` — must still pass; unrelated to writer
  concurrency but shares the `tests/tools/` monitoring-tooling domain.

**Integration:** none in scope — this ticket has no `src/` engine surface.

**Arena-combat:** not applicable — no combat/mechanics code is touched.

## New Tests Required

Per the acceptance criteria, the concrete deliverable is a stress-test harness (methodology +
results) for the *recommended* candidate writer design, run against an isolated throwaway
fixture — explicitly **not** `agent-monitoring/tools.jsonl` and **not**
`post_tool_hook.py` itself (that file must not change). The harness is new, isolated code
written as part of this ticket's own investigation/decision-record deliverable, not a change
to any existing test file.

1. **Concurrent-writer stress harness for the recommended design (mirrors
   `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`'s methodology)**
   - Category: integration-style stress test (isolated fixture, not part of the committed
     `tests/` suite unless the Plan phase decides to commit it as a permanent regression
     guard for the *eventual* follow-on implementation ticket — Plan should make this call
     explicitly, since committing it now would pre-empt the follow-on ticket's own test
     authorship).
   - What it verifies: at minimum 150 concurrent write attempts (matching
     `TCK-20260716`'s 10 threads × 15 iterations shape, or an equivalent/larger N — the AC's
     floor, not a ceiling) against a **throwaway temp-directory fixture file** using the
     *recommended* design's actual locking/serialization mechanism (not `fcntl`, since AC
     requires "at least one non-POSIX-locking mechanism"), asserting: (a) every resulting
     line is independently valid JSON (no interleaving/truncation), (b) all expected records
     are present with none lost/duplicated/merged, (c) append-only ordering is preserved
     (no line is rewritten or reordered), (d) a deliberately-malformed partial line injected
     into the fixture before the stress run is rejected/skipped by a downstream reader rather
     than corrupting subsequent parsing (covers the "malformed-partial-line rejection"
     scoring criterion empirically, not just by design argument).
   - Where it should live: `staging_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/`
     (e.g. a `harness/` or `evidence/` subdirectory) as isolated, non-`tests/`-tree code —
     unless Plan explicitly decides a subset should be promoted into `tests/tools/` as a
     forward-looking regression guard for the not-yet-built future writer (a legitimate but
     separate decision from "does this ticket's evidence deliverable need this harness to
     exist").
   - Must run against a `tmp_path`/temp-directory fixture path, constructed the same way
     `tests/tools/test_post_tool_hook.py::_run_hook` isolates its `cwd` — never against
     `agent-monitoring/tools.jsonl`.

2. **Platform-coverage completeness check (documentation-shaped, not code)**
   - Category: decision-record / evidence-completeness guard, not an executable test.
   - What it verifies: that the recommended design's evidence section explicitly enumerates
     every platform in the Plan-phase-defined supported-platform set, and that any platform
     without empirical stress-test results from *this* environment is explicitly marked
     NOT APPROVED / BLOCKED rather than silently omitted or asserted without evidence. This
     is a reviewer/self-check item for the decision-record artifact itself (analogous to
     `TCK-20260721-CODEX-CAPABILITY-MATRIX`'s practice of distinguishing "documented" from
     "fixture-confirmed" per matrix row), not a pytest-collected test.
   - Where it lives: as a checklist/table inside the writer-decision artifact itself (exact
     filename/location is a Plan-phase decision, not fixed by this test plan).

3. **(Conditional, only if the Plan phase decides to commit the harness as a permanent
   fixture) Architecture-guard test asserting the harness never targets the real corpus**
   - Category: architecture guard.
   - What it verifies: if the stress harness is promoted into `tests/`, a companion
     assertion/guard (or a code-review-time convention, if a runtime guard is impractical)
     confirms its target path is always a `tmp_path`-derived path, never a path resolving to
     the real `agent-monitoring/` directory — protecting against a future edit accidentally
     pointing the harness at production data.
   - Where it should live: same file as the harness itself, if committed.

No other new tests are required — AC1 (schema-generation inventory), AC2 (execution-identity
decision), and AC3 (design comparison table) are decision-record/documentation outputs, not
executable assertions, consistent with the `TCK-20260721-AGENTS-DIR-DISPOSITION` precedent
(classification-only deliverables express their verdict in `investigation.md`/the decision
doc, not in new test files).

## Scoped Pytest Commands

Confirm zero regression in the adjacent monitoring-tooling domain (proves non-interference,
not this ticket's own correctness):

```
.venv/bin/python3 -m pytest tests/tools/ -v
```

If the Plan phase commits the new stress harness into `tests/`, additionally scope to it
specifically once its path is known, e.g.:

```
.venv/bin/python3 -m pytest tests/tools/test_<harness-name>.py -v
```

Never `pytest tests/` — scoped to `tests/tools/` only, the sole domain this ticket's Related
Code Areas and containment rule touch. If the harness is kept isolated under
`staging_artifacts/` instead (not committed to `tests/`), it is run directly via its own
`python3 <harness_script>.py` invocation, documented in the artifact itself, rather than via
pytest collection.

## Anti-Drift Test Guards

- **A `git status` / `git diff --stat` check after implementation must show zero changes to
  `tools/agent-monitoring/post_tool_hook.py`, any other file under `tools/agent-monitoring/`,
  and zero changes to any `agent-monitoring/*.jsonl` file.** This is the single most
  important anti-drift guard for this ticket — the containment rule's core promise. Verify
  explicitly as part of closing this ticket, not just implicitly by "I didn't mean to touch
  it."
- **The stress harness must never open `agent-monitoring/tools.jsonl` (or `runs.jsonl`/
  `events.jsonl`) in any mode, including read-only "just checking."** Hardcode/parametrize
  the fixture path from a `tmp_path`-style construction only; a guard worth adding to the
  harness itself: assert the target path's resolved absolute path does NOT contain
  `agent-monitoring/` relative to the real repo root before any write, as a defensive
  self-check (mirrors the spirit of `TCK-20260713-MONITORING-SQLITE-INDEX`'s AC requiring
  byte-identical source files before/after its own read-only index build).
- **Existing `tests/tools/test_post_tool_hook.py` must show zero diff and zero new failures.**
  If the recommended design's evidence work tempts a "let me also update the real hook to
  match" edit, that is the follow-on epic-gated ticket's job, not this one — a diff to this
  file is itself a signal of scope creep past this ticket's Out of Scope line.
- **The malformed-partial-line-rejection test must use a genuinely malformed line (not a
  valid-but-unexpected-schema line)** — conflating "malformed JSON" with "legacy schema
  variant" would misrepresent the design comparison's scoring criterion; `validate.py`'s
  existing `load_jsonl()` (lines 170-182: catches `json.JSONDecodeError` per line, warns,
  continues) is the precedent pattern for what "rejection" should look like — the new design
  should not require a working reader to crash or silently accept corrupted content.
- **Do not let the "at least one non-POSIX-locking mechanism" requirement get satisfied by
  merely asserting `fcntl` also happens to not run on Windows** — the evidence must
  demonstrate an actual alternative mechanism running successfully in this environment (e.g.
  `os.O_CREAT | os.O_EXCL` atomic lock-file creation, or `sqlite3` `BEGIN IMMEDIATE`
  transactions), not just document that the *current* mechanism is POSIX-only (that fact is
  already established by the predecessor ticket and this investigation).
