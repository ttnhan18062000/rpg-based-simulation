---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-DECISION
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement]
---

# Implementation Plan — TCK-20260721-MONITORING-WRITER-DECISION

## Summary

This ticket produces one new durable decision-record doc, `docs/ai/monitoring_writer_decision.md`
(following the `docs/ai/agents_dir_disposition.md` / `docs/ai/codex_capability_matrix.md`
sibling precedent), plus one new isolated, committed stress-test file,
`tests/tools/test_monitoring_writer_lockfile_candidate.py`. The plan resolves all five
Plan-phase questions the investigation deliberately left open, directly from repo evidence —
none require human/stakeholder input beyond what the investigation already gathered:

1. **Supported-platform set = {Linux}**, evidenced empirically from this environment and this
   repo's Linux-only CI (`ubuntu-latest` on every job). Windows and macOS are explicitly
   recorded as **NOT APPROVED / BLOCKED — no evidence**, using the AC's own built-in escape
   valve, rather than silently narrowed out of the set or falsely claimed as covered.
2. **Non-POSIX-locking mechanism = `os.O_CREAT | os.O_EXCL` atomic lock-file creation**,
   scoring it as the concrete mechanism for candidate design 1 ("lock-file protocol w/ bounded
   retry + stale-lock recovery" — one of the source plan's own three named candidates). No new
   dependency, runs identically on POSIX and Windows Python builds per stdlib `os` module
   semantics, and is directly stress-testable from this Linux-only environment.
3. **Execution-identity format**: `execution_id = "{provider}-{ticket_id}-{unix_ts_ms}-{8hex}"`
   (stdlib `secrets.token_hex(4)`, no new dependency), immutable and unique per execution;
   `run_id` retained as the human-readable run reference (today's existing format, unchanged
   shape); `ticket_id` promoted to an explicit top-level field so it remains the stable
   cross-run join key once the same ticket can be executed by multiple providers or multiple
   times — `execution_id` is never reused as a join key, `ticket_id` is.
4. **Stress harness gets committed to `tests/tools/`** as a forward-looking regression guard,
   following this batch's own established precedent (`AGENTS-DIR-DISPOSITION` and
   `CODEX-CAPABILITY-MATRIX` both added durable `tests/` files, not staging-only artifacts).
5. **Decision-record location = `docs/ai/monitoring_writer_decision.md`**, matching the
   `docs/ai/codex_capability_matrix.md` / `docs/ai/agents_dir_disposition.md` naming and
   frontmatter pattern from the same batch.

The doc and the harness are built in that order — harness first, so its actual pass/fail
result and invocation count can be cited as evidence inside the doc rather than promised
before it exists. No file under `tools/agent-monitoring/` and no `agent-monitoring/*.jsonl`
file is touched anywhere in this plan; the harness targets only a `tmp_path` fixture and
carries its own defensive guard against ever resolving to the real corpus.

## Steps

### Step 1 — Confirm regression baseline before any change
**Files:** none (verification only)
**Change:** Run:
```
.venv/bin/python3 -m pytest tests/tools/ -v
```
Confirm all currently-collected tests pass (including the four `test_post_tool_hook.py` tests
and `test_validate_agent_monitoring.py`, `test_monitoring_bypass_fix.py` named in
`test_plan.md`'s Regression Surface) before writing anything, so any later failure is
attributable to this ticket's own additions, not pre-existing drift.
**Do NOT touch:** Any file. Read-only verification.
**Verify:** Command exits 0, no failures.

### Step 2 — Build and run the concurrent-writer stress harness for the recommended design
**Files:** `tests/tools/test_monitoring_writer_lockfile_candidate.py` (new file)
**Change:** Implement a self-contained, test-local (not imported from `tools/`) atomic
lock-file writer mirroring `tests/tools/test_post_tool_hook.py`'s harness shape but using
`os.O_CREAT | os.O_EXCL` instead of `fcntl.flock`:
- `_acquire_lock(lock_path, stale_after_s=5.0, max_retries=200, retry_sleep_s=0.005)`: attempt
  `os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`; on `FileExistsError`, check the
  existing lock file's `mtime` age — if older than `stale_after_s`, remove it (stale-lock
  recovery) and retry; otherwise back off and retry up to `max_retries`; raise on exhaustion.
- `_release_lock(lock_path)`: `os.remove(lock_path)`.
- `_write_record_lockfile(target_path, record, lock_path)`: acquire, append one
  `json.dumps(record, separators=(",", ":")) + "\n"` line to `target_path` in `"a"` mode,
  release — bounded retry + stale-lock recovery is the "lock-file protocol" candidate 1 names
  in the ticket's AC3 list.
- A defensive path guard, `_assert_not_real_corpus(path)`, asserting the resolved absolute
  path does not contain an `agent-monitoring` path segment relative to the repo root; call it
  at the top of every write helper before any file is touched (mirrors
  `test_plan.md`'s Anti-Drift Test Guards item on hardcoding the fixture path).
- `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines(tmp_path)`:
  10 threads x 20 iterations = 200 invocations (meets/exceeds the AC's 150-invocation floor)
  against one shared `tmp_path / "tools.jsonl"` fixture file and a shared `tmp_path /
  "tools.jsonl.lock"` lock path. Assert: every resulting line is independently valid JSON
  (`json.loads` per line succeeds), all 200 expected record markers are present with none
  lost/duplicated/merged, and the file was only ever appended to (byte length is monotonically
  non-decreasing across a few sampled checkpoints, if easy to instrument — otherwise assert via
  final-line-count == 200 exactly).
- `test_malformed_partial_line_is_rejected_by_downstream_reader(tmp_path)`: pre-seed the
  fixture file with one genuinely malformed line (a truncated JSON fragment, e.g.
  `'{"session_id": "abc", "run_i'` with no closing brace/newline-terminated valid JSON — not a
  valid-but-unexpected-schema line), then write several valid records via
  `_write_record_lockfile`, then run a small reader loop mirroring
  `tools/agent-monitoring/validate.py`'s `load_jsonl()` pattern (catch
  `json.JSONDecodeError` per line, skip and count as rejected, continue) and assert the
  malformed line is skipped/rejected while every valid line parses successfully.
- `test_lockfile_guard_rejects_real_agent_monitoring_path()`: call `_assert_not_real_corpus`
  with a path resolving under the real `agent-monitoring/` directory and assert it raises,
  proving the guard is live, not decorative.
Run:
```
.venv/bin/python3 -m pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v
```
Record the exact pass count and invocation count (200) for citation in Step 6's doc section.
**Do NOT touch:** `tools/agent-monitoring/post_tool_hook.py` or any other file under
`tools/agent-monitoring/`. Never open, read, or write any path containing `agent-monitoring/`
relative to the real repo root — every write in this file must go through a `tmp_path`
fixture. Do not add Windows- or macOS-specific test paths/skips implying platform coverage
that does not exist — this harness runs on Linux only and its evidence is scoped to Linux.
**Verify:** All new tests pass:
`.venv/bin/python3 -m pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v` →
4 passed.

### Step 3 — Write the doc's legacy-schema/identifier inventory section (AC1)
**Files:** `docs/ai/monitoring_writer_decision.md` (new file)
**Change:** Create the doc with frontmatter matching the sibling precedent: `status: active`,
`layer: ai`, `authority: P1`, `audience: developer`, `tags: [ai, agent-monitoring,
process-improvement]` (all already registered — reuse verbatim). Write:
1. **Header note**: this is a standalone decision/evidence artifact for
   `TCK-20260721-MONITORING-WRITER-DECISION`, bundling Open Decision #3 (execution identity)
   and #5 (concurrent-write strategy) per Codex's 2026-07-21 batch review; it decides and
   evidences, it does not implement — the writer design and execution-identity scheme are
   follow-on, epic-gated implementation work.
2. **Legacy Schema & Identifier Inventory** section (AC1) — synthesize, do not re-derive, by
   citing `docs/agent-monitoring/schema.md`'s Known Limitations section verbatim/by reference:
   the five legacy `runs.jsonl` generations (no `end_ts`: `started_at`/`finished_at`/`status`/
   `phases_completed`/`notes`; `final_status` present, `end_ts` absent; `ts_start`/`ts_end`/
   `result`/`agent`; `completed_at`/`status`; `FOLDER-*`/`EPIC-*` batch wrappers), the single
   exhaustively-audited exception (`TCK-20260623-TYPE-CHECKER`), the manual/ad hoc `run-{code}-
   {unix_ts}` and `-REDESIGN`-suffix `run_id` convention, `tools.jsonl`'s null `phase`/`agent`
   gap (pre-`TCK-20260719-LIVE-PHASE-AGENT-LABEL`), and `events.jsonl`'s null `tool_call_count`/
   `cost_proxy_score` gap (pre-cutover). Then name the **identifier gap** this ticket exists to
   close: `run_id` today doubles as both the execution key and the ticket-linkage key, which
   breaks once the same ticket can be executed by more than one provider — cite
   `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` as the
   source of this framing.
**Do NOT touch:** `docs/agent-monitoring/schema.md` itself — cite it, do not edit it (no
schema/behavior change is in scope). Do not touch any `agent-monitoring/*.jsonl` file.
**Verify:** Manual review — inventory section present, every legacy generation from
`schema.md`'s Known Limitations cited, no re-derivation drift (facts match the source
verbatim). No executable test covers doc content (decision-record deliverable, per
`test_plan.md`'s "No other new tests are required — AC1... decision-record/documentation
outputs, not executable assertions").

### Step 4 — Write the execution-identity model decision (AC2)
**Files:** `docs/ai/monitoring_writer_decision.md` (same file, append section)
**Change:** Add an **Execution Identity Model** section deciding, concretely:
- **Immutable per-execution key**: `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-
  {secrets.token_hex(4)}"` (stdlib `secrets` + `time`, no new dependency), e.g.
  `claude-code-TCK-20260721-MONITORING-WRITER-DECISION-1774276800123-a1b2c3d4`. Generated fresh
  once per workflow execution, never reused, never treated as a lookup/join key across runs.
- **Human-readable run reference**: `run_id` is retained in its current shape/format
  unchanged — it becomes a display/reference field, not the execution's primary key.
- **Stable cross-run join key**: `ticket_id` is promoted to an explicit top-level schema field
  (today it is implicit inside `run_id`'s string shape). All records for all executions of the
  same ticket, by any provider, share the same `ticket_id` value — this is the field
  `TCK-20260713-MONITORING-SQLITE-INDEX`'s eventual read-side index and
  `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s downstream contract should join on.
- State explicitly this is a **schema field proposal for a future implementation ticket** —
  no field is added to any real record by this ticket; illustrate the shape with a synthetic
  example line only (never an edit to a real historical record), consistent with
  `validate.py`'s existing "read-side absorbs legacy variance, write-side stays append-only"
  precedent (`LEGACY_COMPLETION_FIELDS` / `LEGACY_TERMINAL_STATUS_VALUES`).
**Do NOT touch:** Any real `agent-monitoring/*.jsonl` file — the example record must be
inline in the doc as fenced-code illustration, not written to any file.
**Verify:** Manual review — section states the exact `execution_id` format string, confirms
`run_id` is retained as reference (not replaced), and confirms `ticket_id` becomes the
explicit stable join key, matching the source plan's Open Decision #3 framing.

### Step 5 — Write the design comparison table (AC3), citing Step 2's harness evidence
**Files:** `docs/ai/monitoring_writer_decision.md` (same file, append section)
**Change:** Add a **Candidate Writer Design Comparison** section: a table scoring the three
candidates named in the ticket's own AC3 against the four required criteria (POSIX+Windows
portability, malformed-partial-line rejection, append-only preservation, safe two-writer
concurrency):
1. **Lock-file protocol w/ bounded retry + stale-lock recovery** (`os.O_CREAT | os.O_EXCL`) —
   **RECOMMENDED**. Portability: syscall-level, identical semantics on POSIX and Windows Python
   builds (no new dependency). Malformed-line rejection: relies on a downstream reader
   (`validate.py`-style `load_jsonl`), not the writer itself — same posture as the current
   design; demonstrated empirically by Step 2's
   `test_malformed_partial_line_is_rejected_by_downstream_reader`. Append-only preservation: by
   construction (writer only ever opens in append mode). Two-writer concurrency: demonstrated
   empirically by Step 2's 200-invocation concurrent test — cite the exact pass result and
   invocation count.
2. **Single local writer process/queue**: Portability: high (a queue/socket handoff is
   platform-neutral), but adds a long-lived background process as new operational surface —
   not stress-tested in this ticket (out of scope: no implementation). Concurrency: strong by
   design (single writer eliminates the race entirely) but at the cost of a new failure mode
   (queue process crash/backpressure) not evidenced here.
3. **Provider-local append journals + deterministic merger**: Portability: writer side is
   trivially portable (each provider only ever appends to its own file — no cross-process lock
   needed at write time at all). Concurrency: sidesteps the write-time race entirely by
   deferring merge to a separate read-side step, but shifts complexity to the merger's
   ordering/dedup logic, unevidenced here (no implementation in scope).
State plainly: candidate 1 is recommended because it directly reuses today's append-only
`tools.jsonl` shape with a minimal, dependency-free mechanism swap (`flock` →
`O_CREAT|O_EXCL`), it is the only candidate with direct stress-test evidence gathered in this
ticket, and it requires no new long-lived process or deferred-merge complexity. Candidates 2
and 3 are recorded as viable alternatives for a future implementation ticket to reconsider, not
ruled out.
**Do NOT touch:** No candidate is implemented — this step is a scored comparison only.
**Verify:** Manual review — table has 3 rows x 4 criteria, one row explicitly marked
RECOMMENDED, the concurrency and malformed-line-rejection cells for candidate 1 cite Step 2's
actual test names and results (not just asserted).

### Step 6 — Write the supported-platform-set definition and platform-coverage evidence (AC4)
**Files:** `docs/ai/monitoring_writer_decision.md` (same file, append section)
**Change:** Add a **Supported Development Platform Set & Evidence** section:
- **Supported-development-platform set: {Linux}.** Justify from repo evidence: this
  environment is Ubuntu 24.04.4 LTS / Linux 7.0.0-28-generic; `.github/workflows/test.yml` runs
  every job on `runs-on: ubuntu-latest` with no macOS or Windows runner anywhere in this repo's
  CI; no `wine`, no Windows Docker host, no `filelock`/`portalocker` dependency currently
  installed. Linux is the actual, already-established norm for both local dev and CI, not an
  arbitrarily narrowed scope.
- **Evidence table**, one row per platform in the set plus the two named-but-unevidenced
  platforms, per the AC's own explicit fallback clause:

  | Platform | Status | Evidence |
  |---|---|---|
  | Linux | APPROVED | Step 2's `tests/tools/test_monitoring_writer_lockfile_candidate.py`, 200 concurrent invocations, 0 corrupted/lost/duplicated lines, malformed-line rejection confirmed — cite exact pass count from Step 2's run. |
  | Windows | **NOT APPROVED / BLOCKED** | No empirical evidence — no Windows runner, no `wine`, no Windows Docker host available in this environment or this repo's CI. `os.O_CREAT \| os.O_EXCL` is documented as portable at the Python stdlib `os` module level, but this is a documentation citation, not a fixture-confirmed result, and is not sufficient for APPROVED status per this ticket's own evidentiary bar. |
  | macOS | **NOT APPROVED / BLOCKED** | Same — no macOS runner or hardware available; not evidenced. |

- State explicitly: this satisfies the AC's own escape-valve wording ("the ticket's own
  investigation may still begin on one platform, but the writer design is not approved... until
  evidence exists for every platform in the supported set") by defining the supported set
  honestly as {Linux} — the one platform genuinely testable from this environment and repo —
  rather than either quietly narrowing the AC's language to make it trivially pass with an
  under-scoped set, or overclaiming Windows/macOS coverage that was never run. If Windows or
  macOS support becomes a real product requirement, that is new evidence-gathering scope for a
  future ticket (e.g. via a Windows CI runner or VM), not something this ticket can honestly
  claim today.
- Add a **Platform-Coverage Completeness Self-Check** subsection (test_plan.md's item 2):
  confirm every platform in the defined set has empirical evidence (Linux: yes), and every
  named-but-out-of-set platform is explicitly marked rather than silently omitted (Windows,
  macOS: yes, both marked NOT APPROVED / BLOCKED above).
**Do NOT touch:** Do not mark Windows or macOS as APPROVED under any circumstance in this
ticket — no evidence exists. Do not omit them from the table either (silent omission is
explicitly the anti-drift hazard this step exists to avoid).
**Verify:** Manual review — table present with all three platform rows, Linux cites Step 2's
actual result, Windows/macOS both explicitly marked NOT APPROVED / BLOCKED with a stated
reason, self-check subsection present.

### Step 7 — Full scoped regression pass and containment verification
**Files:** none (verification only)
**Change:** Run:
```
.venv/bin/python3 -m pytest tests/tools/ -v
```
(covers all pre-existing `tests/tools/` suites plus the new
`test_monitoring_writer_lockfile_candidate.py`). Then run:
```
git status
git diff --stat
```
and confirm the only changes present are: `docs/ai/monitoring_writer_decision.md` (new),
`tests/tools/test_monitoring_writer_lockfile_candidate.py` (new), this ticket's own artifacts
(`tickets/inprogress/TCK-20260721-MONITORING-WRITER-DECISION.md`,
`staging_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/*`), and `agent-monitoring/`
(monitoring tool auto-update only). Nothing under `tools/agent-monitoring/*.py` and no
`agent-monitoring/*.jsonl` content diff (beyond the auto-appended monitoring records for this
very workflow run) should appear.
**Do NOT touch:** Nothing new here — pure verification. If anything outside the two new files
changed, that is scope creep — stop and investigate rather than editing further to "fix" it.
**Verify:** `pytest tests/tools/ -v` exits 0 with all tests passing (pre-existing count plus 4
new). `git diff --stat -- tools/agent-monitoring/` and
`git diff --stat -- 'agent-monitoring/*.jsonl'` both show no output (or only the expected
auto-appended monitoring lines from this run's own hook activity, never a rewritten/edited
existing line).

### Step 8 — Update the ticket body with the decision and results
**Files:** `tickets/inprogress/TCK-20260721-MONITORING-WRITER-DECISION.md`
**Change:** Fill in `## Implementation Notes` (summarize the doc's four sections and the five
Plan-phase decisions from this plan's Summary), `## Test Summary` (paste Step 7's pass counts,
including the 4 new harness tests), `## Files Changed` (the exact list from Step 7's `git
status`), and `## Completion Summary`. Check all five `## Acceptance Criteria` boxes. Do not
alter `## Scope`, `## Out of Scope`, or `## Related Tickets`.
**Do NOT touch:** Frontmatter fields other than what closure conventions require (`status`,
`phase`).
**Verify:** All five AC checkboxes ticked with content matching what Steps 2-7 actually
produced, not aspirational text.

## Scope Guards

- Do not modify `tools/agent-monitoring/post_tool_hook.py` or any other file under
  `tools/agent-monitoring/` — that is the direct target of the *next*, epic-gated
  implementation ticket, not this one.
- Do not modify or backfill any `agent-monitoring/*.jsonl` file (`runs.jsonl`,
  `events.jsonl`, `tools.jsonl`) — no historical cleanup, no reinterpretation of existing
  `run_id` values, no example record written to a real file (illustrations stay inline in the
  doc as fenced code).
- Do not implement the chosen writer design (`os.O_CREAT | os.O_EXCL` lock-file protocol) or
  the execution-identity scheme in any production path — this ticket decides and evidences
  only; wiring it into `post_tool_hook.py` is explicitly out of scope, gated by
  `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`.
- Do not claim Windows or macOS APPROVED status anywhere — no evidence exists from this
  environment; both must remain explicitly marked NOT APPROVED / BLOCKED.
- Do not conflate this ticket's execution-identity decision with
  `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s broader contract-format ADR — that ticket
  consumes this decision as an input, it does not re-decide it.
- Do not edit `docs/agent-monitoring/schema.md` — cite it, do not change it (no schema/behavior
  change is in scope for this ticket).
- Do not touch `tools/agent-monitoring/validate.py` — referenced only as a precedent pattern
  for the malformed-line-rejection test's reader loop, not modified.
- Do not run `pytest tests/` broadly — use only the scoped `tests/tools/` commands in Steps 1
  and 7.
- Do not implement or reference `filelock`/`portalocker` or any new third-party dependency —
  the chosen mechanism (`os.O_CREAT | os.O_EXCL`) is stdlib-only by design.
- Do not open or scope any provider-runtime implementation ticket — blocked until all five
  discovery outputs across `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` are complete and approved.

## Dependency Map

- Step 1 has no dependencies; run first to establish a clean baseline.
- Step 2 (harness) has no dependency on Step 1's outcome but should follow it for narrative
  safety; Step 2 must complete (with its actual pass/fail result recorded) before Steps 5 and 6
  are written, since both cite Step 2's evidence directly.
- Step 3 (AC1 inventory) and Step 4 (AC2 execution identity) are independent of Step 2 and of
  each other — both are pure synthesis/decision content with no dependency on harness results.
  They may be done in either order, both before or after Step 2.
- Step 5 (AC3 comparison table) depends on Step 2 (cites its concurrency-test evidence) and
  logically follows Steps 3-4 (same doc, later section) though it has no content dependency on
  them.
- Step 6 (AC4 platform evidence) depends on Step 2 (cites its Linux evidence directly) and
  should be written after Step 5 (same doc, adjacent sections).
- Step 7 (regression + containment check) depends on Steps 2-6 all being complete (verifies the
  final state, including the new harness file and the fully-written doc).
- Step 8 (ticket closure) depends on Step 7 (documents actual verified results, not planned
  ones).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — written inventory of legacy monitoring schema generations and identifier gaps, cross-referencing `docs/agent-monitoring/schema.md`'s Known Limitations | Step 3 | Manual doc review (decision-record deliverable, no executable test per test_plan.md) |
| AC2 — execution-identity model decided and recorded: immutable per-execution key, human-readable run reference, `ticket_id` as stable cross-run join key | Step 4 | Manual doc review |
| AC3 — side-by-side comparison of the 3 named candidate writer designs against the 4 required criteria | Step 5 (design content), Step 2 (empirical evidence cited by Step 5) | `.venv/bin/python3 -m pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v` → 4 passed; manual doc review for the table itself |
| AC4 — explicit supported-platform set defined, stress-test evidence (methodology + results, >=150 invocations) for the recommended design on every platform in that set, covering >=1 non-POSIX-locking mechanism, with unevidenced platforms explicitly marked NOT APPROVED / BLOCKED | Step 2 (evidence generation), Step 6 (platform-set definition + evidence table) | `.venv/bin/python3 -m pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v` → 4 passed (200 invocations, 0 corruption); manual doc review confirming Windows/macOS rows explicitly marked |
| AC5 — zero changes to `tools/agent-monitoring/post_tool_hook.py` or any other production monitoring writer path, zero changes to any `agent-monitoring/*.jsonl` data file | Step 7 | `git status` / `git diff --stat` showing only the two new files plus this ticket's own artifacts and `agent-monitoring/` auto-append |

## Anti-Drift Notes

- **The `os.O_CREAT | os.O_EXCL` mechanism must actually run and pass in Step 2 — documenting
  that it is "portable per stdlib docs" alone does not satisfy the AC.** `test_plan.md` is
  explicit: "the evidence must demonstrate an actual alternative mechanism running
  successfully in this environment... not just document that the current mechanism is
  POSIX-only." Step 2's tests are the load-bearing evidence; Steps 5-6 only cite them.
- **Do not let "every platform in the supported set" quietly become "the one platform I could
  test" without the explicit NOT APPROVED / BLOCKED marking.** The set is honestly {Linux};
  Windows and macOS are named and explicitly blocked, not silently dropped from the AC's
  wording. This is the single most anti-drift-sensitive decision in this ticket — Step 6 must
  not soften "NOT APPROVED / BLOCKED" into vaguer language like "future work" that could read
  as quiet omission.
- **The malformed-line test must use a genuinely malformed line, not a valid-but-legacy-shaped
  one.** Conflating "malformed JSON" with "old schema variant" would misrepresent what the
  rejection criterion is scoring — Step 2's fixture line must fail `json.loads` outright.
- **Do not implement the writer design.** The harness in Step 2 is test-only, self-contained
  code (`_acquire_lock`/`_release_lock`/`_write_record_lockfile` living inside the test file
  itself, not imported from or added to `tools/agent-monitoring/`). Resist the temptation to
  "also update the real hook since I'm already testing the mechanism" — that is the follow-on,
  epic-gated ticket's job.
- **`docs/agent-monitoring/schema.md`'s Known Limitations is the source of truth for AC1 — cite
  it, do not restate it independently.** Restating risks drift between two descriptions of the
  same facts; Step 3 must quote/reference, not re-derive.
- **`execution_id`'s format (Step 4) is a schema proposal, not a production change.** No real
  record gains this field as part of this ticket — only a synthetic illustrative example
  appears in the doc.
- **`TCK-20260713-MONITORING-SQLITE-INDEX` is related, not a dependency or a duplicate.** Its
  read-side normalization work is unaffected by and does not block this ticket; this ticket's
  execution-identity decision becomes a future input for that ticket's eventual builder, not
  the reverse.

## Deviations

- **Step 2 test count: 3 passed, not the "4 passed" the plan's Step 2 Verify line states.**
  The plan's own bulleted change list for Step 2 names exactly 3 test functions
  (`test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines`,
  `test_malformed_partial_line_is_rejected_by_downstream_reader`,
  `test_lockfile_guard_rejects_real_agent_monitoring_path`) — matching the ticket's own
  instruction of "200 invocations, a malformed-line-rejection test, AND a defensive guard
  test." The "4 passed" figure in the plan's Verify line and the Acceptance Criteria Map table
  appears to be a copy-paste artifact from `test_post_tool_hook.py`'s different (5-test) suite
  shape. Implemented exactly the 3 tests the plan's own bullet list specifies rather than
  padding with an artificial 4th test to match a miscounted number; all 3 pass. The AC3/AC4
  acceptance-criteria text itself only requires the harness to exist and produce evidence, not
  a specific test count, so this does not affect AC satisfaction.
- **Step 7 surfaced one additional, ticket-caused-but-out-of-scope test failure not anticipated
  by the plan:** `test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`
  failed after Step 3 added `docs/ai/monitoring_writer_decision.md`, because `docs/REGISTRY.yaml`
  had not yet been regenerated. Resolved per `CLAUDE.md`'s standing rule ("docs/REGISTRY.yaml is
  regenerated unconditionally... always stage the regenerated file") by running
  `make docs-registry` (mechanical, frontmatter-driven regen; touches only `docs/REGISTRY.yaml`,
  no agent-monitoring/writer-path involvement) and `make knowledge-index-update` (per CLAUDE.md's
  "if any files under docs/ were created or modified" rule). Re-ran `pytest tests/tools/ -v`
  afterward: back to exactly the Step 1 baseline's 6 pre-existing failures, with the 3 new
  harness tests added (998 passed total). This is a standard doc-registry mechanical step, not a
  scope or architecture deviation — no code outside `docs/REGISTRY.yaml`'s regeneration and the
  two ticket-scoped new files was touched.
