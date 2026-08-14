---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-UNIFICATION
artifact_type: investigation
tags: [monitoring, writer, unification]
---

# Investigation — TCK-20260721-MONITORING-WRITER-UNIFICATION

## Current Behavior

### The 3 writer call sites (read in full)

**`tools/agent-monitoring/post_tool_hook.py`** (87 lines) — a top-level script, not importable
as a module (reads `sys.stdin` on import), fired by the `PostToolUse` hook registered in
`.claude/settings.json:90` as `python3 tools/agent-monitoring/post_tool_hook.py 2>/dev/null ||
true`. Whole body wrapped in `try: ... except Exception: pass` (lines 24-86). Writes exactly one
record per invocation to `agent-monitoring/tools.jsonl` (line 78-83):
```python
with open(tools_file, "a") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    f.write(json.dumps(record, separators=(",", ":")) + "\n")
    fcntl.flock(f, fcntl.LOCK_UN)
```
This is the only one of the 3 sites with any locking today (`fcntl.flock`, POSIX-only,
added by `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`). Record shape: fixed 10-key dict
(`session_id, run_id, seq, phase, agent, ts, tool, input_summary, status, duration_ms`).

**`tools/agent-monitoring/record_run.py`** (73 lines) — CLI (`argparse`, `--data`), writes one
record to `agent-monitoring/runs.jsonl` (lines 65-66): `with open(RUNS_FILE, "a") as f:
f.write(...)`. **No locking at all.** Validates required fields first (`validate_record`,
sys.exit(1) + stderr `ERROR:` lines on failure — this exit-code contract is a public interface,
tested by `tests/tools/test_record_run.py` via `subprocess.run`, and must not change). Computes
`duration_s` server-side, always overriding caller input (line 62).

**`tools/agent-monitoring/record_events.py`** (152 lines) — CLI, writes a **batch** of 1+ records
to `agent-monitoring/events.jsonl` in one `open(...) as f:` block with a `for record in records:
f.write(...)` loop (lines 143-145). **No locking.** Validates each record, warns (never fails) on
phase/agent vocabulary drift via `vocabulary.py::infer_workflow`/`is_known_agent` (read-only
dependency — `vocabulary.py` needs no change for this ticket; it has zero provider-awareness and
none is asked for). Computes `tool_call_count`/`cost_proxy_score` server-side by reading real
`tools.jsonl` rows for `implement-ticket`-workflow run_ids (lines 34-67), always overriding caller
input.

**Behavioral asymmetries that must survive unification** (none are drive-by cleanup targets):
1. Only `post_tool_hook.py` locks today; `record_run.py`/`record_events.py` write unlocked. The
   new shared writer changes this for all 3 — a real behavior change to document, not silently
   absorb.
2. `post_tool_hook.py` never raises/exits nonzero under any circumstance (bare outer
   `except Exception: pass`, with **zero diagnostic output today** — the swallowed exception is
   not even printed to stderr). `record_run.py`/`record_events.py` do exit nonzero + print
   `ERROR:` to stderr on **validation** failure (checked *before* any writer lock is touched) —
   that CLI contract is exercised by both files' subprocess-based tests and is out of this
   ticket's scope to change.
3. `record_events.py` batches multiple JSONL lines under one Python `open()` call. If the shared
   writer's public API is "append one already-serialized line, holding the lock only for that one
   line" (the candidate module's exact shape, see below), calling it once per line means the
   batch's own N lines could interleave with a different process's lines between them — safe
   (no corruption, JSONL lines are independent) but not atomic as a batch. Whether the shared
   writer needs a `write_lines(list[str])` variant that holds one lock for the whole batch is an
   open question for Plan (see Risks).

### The candidate writer module — what exists vs. what's genuinely new

`docs/ai/monitoring_writer_decision.md` §3 recommends "Candidate 1" (evidence-gathering only,
explicitly not wired to production — see its own docstring). Its logic lives in
`tests/tools/test_monitoring_writer_lockfile_candidate.py` as **test-local, unimported helper
functions** (`_acquire_lock`, `_release_lock`, `_write_record_lockfile`), never added to
`tools/agent-monitoring/`. Exact mechanics extracted from that file:

```python
def _acquire_lock(lock_path, stale_after_s=5.0, max_retries=200, retry_sleep_s=0.005):
    for _ in range(max_retries):
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            age_s = time.time() - os.path.getmtime(lock_path)   # FileNotFoundError -> retry
            if age_s > stale_after_s:
                os.remove(lock_path)   # FileNotFoundError tolerated
                continue
            time.sleep(retry_sleep_s)
    raise TimeoutError(...)   # after max_retries (200) exhausted
```
- **Lock file naming**: `<target_path>.lock` (sibling file, caller-supplied path — the tests use
  `tools.jsonl.lock` next to `tools.jsonl`).
- **Retry/backoff**: fixed `retry_sleep_s=0.005` (5ms) between retries, up to `max_retries=200` —
  no exponential backoff, ~1s worst-case total wait before giving up.
- **Stale-lock threshold**: `stale_after_s=5.0` — a lock file older than 5s (by `mtime`) is
  removed and acquisition retried immediately (no extra sleep for that iteration).
- **On a write that fails after acquiring the lock**: `_write_record_lockfile`'s `try/finally`
  always releases the lock (`os.remove(lock_path)`) even if the `open(target_path, "a")`/`write()`
  inside raises — the exception itself is **not caught**, it propagates to the caller. Nothing
  in the candidate handles "lock acquired but write failed" as a distinct case; it only guarantees
  the lock doesn't leak. **Whether the production writer should swallow this exception (to satisfy
  this ticket's own "writer failures must not block the workflow" AC) or let it propagate for the
  caller to catch is not specified by the candidate and is a real Plan decision** (see Risks).
- **Corpus-path guard**: `_assert_not_real_corpus` refuses to operate on any path resolving under
  `<repo_root>/agent-monitoring/` — this was a deliberate test-safety guard for the
  evidence-gathering ticket ("never opens any path under the real `agent-monitoring/` directory")
  and must NOT be carried into the production module verbatim (the production module's entire
  purpose is to write under `agent-monitoring/`).
- Stress-test evidence already gathered (do not re-derive): 10 threads × 20 iterations = 200
  concurrent invocations, 3/3 passed, 0 corrupted/lost/duplicated/interleaved lines.

**What "promote to production" concretely requires**: this is not a literal import-and-reuse —
the candidate is single-record-only, has no production-shaped API (no execution_id/provider
awareness needed at this layer, but needs a stable public function name/signature 3 call sites
will import), and carries a guard that inverts the intended target. A new production module under
`tools/agent-monitoring/` (exact filename not yet decided — see Risks) must be written that reuses
the *mechanics* (lock-file naming, retry/backoff/stale-threshold constants, O_CREAT|O_EXCL
semantics) verbatim, but is a new module, not a relocated file.

### `docs/agent-monitoring/schema.md` — legacy shape count (confirmed, not re-derived)

Exactly **5 documented legacy `runs.jsonl` generations** (`Known Limitations` section, lines
313-327) plus **1 permanently-documented single-record exception**
(`TCK-20260623-TYPE-CHECKER`, deliberately not allowlisted):
1. `started_at`/`finished_at`/`status`/`phases_completed`/`notes`
2. `final_status` present, `end_ts` absent
3. `ts_start`/`ts_end`/`result`/`agent`
4. `completed_at`/`status`
5. `FOLDER-*`/`EPIC-*` batch wrappers, bare `status`
6. (exception, not allowlisted) `outcome`/`phase`, no `end_ts`/`final_status`/`status`

`tools/agent-monitoring/legacy_reader.py::classify_provenance` (built by
`TCK-20260721-BASELINE-MONITORING-MANIFEST`) already structurally encodes all 6 shapes plus
`events.jsonl`'s 2 known gaps (`reason_code` absent, `tool_call_count` absent) and `tools.jsonl`'s
2 (`interactive_null`, `phase`/`agent` absent) — this is read-only classification tooling, not a
writer, and this ticket must not modify it (not in Related Code Areas).

**`load_jsonl`** is defined once, in `tools/agent-monitoring/validate.py:170-182` — a tolerant
per-line loader (`json.loads` per line, `except json.JSONDecodeError: print WARNING, continue`,
never raises on one bad line). `tools/agent-monitoring/generate_retro.py` and
`tools/agent-monitoring/query.py` each define their **own separate** `load_jsonl` (found via
grep — not the same function object; out of scope to unify per this ticket's explicit "no changes
to query.py/generate_retro.py" boundary). `src/api/agent_ops_dashboard/ingest.py:94` does
`load_jsonl = validate.load_jsonl` — a direct reuse (not a reimplementation), confirmed by
that line's own comment: "AC #3 asserts these are the same function objects as their source
modules." Since `load_jsonl` is already fully tolerant of arbitrary/malformed JSON per line
and additive fields never change existing keys, "every legacy record shape still loads
successfully" is **already true today** for anything already in the corpus — what actually needs
a **new** regression test is: (a) a fixture file containing one line of each of the 6 legacy
shapes plus one line carrying the new `execution_id`/`provider` fields, asserting `load_jsonl`
returns all 7 records with zero exceptions, and (b) confirming `ingest.py`'s
`load_jsonl_counted` wrapper (which subtracts valid-count from line-count to report unparsed
lines) doesn't misclassify any of the 6 legacy shapes as "unparsed."

### `src/api/agent_ops_dashboard/ingest.py` (893 lines, read in full)

Zero provider/execution_id handling anywhere — confirmed by reading the whole file. Read-only
cache layer (`DashboardCache`, single `threading.RLock()` guarding every method, mtime-based
rebuild). Relevant structure for this ticket's minimal-diff extension:
- `_rebuild()` (lines 491-546) is the one place `runs_all`/`events_all`/`tools_all` are loaded
  and grouped (`_group_runs_by_id`, `tools_by_seq`, `tools_by_run_recent`). Grouping/filtering by
  `provider`/`execution_id` would extend this method and `get_runs()` (lines 613-639, which
  already filters by `status`/`workflow`/`since` via simple `if x is not None and field !=
  x: continue` guards — the same pattern extends trivially to `provider`/`execution_id`).
- `_build_run_summary()` (lines 332-358) and the `RunSummary`/`RunDetail` Pydantic models
  (`src/api/agent_ops_dashboard/models.py`, not yet read in this investigation — Plan should read
  it before scoping the model change) are where `provider`/`execution_id` fields would need to be
  added as `Optional[str] = None` to avoid breaking every existing legacy-record path.
  `_resolve_final_status()` (lines 187-200) is the established precedent for "prefer new field,
  fall back through legacy shapes, never raise" — the same pattern should govern
  provider/execution_id resolution (`record.get("provider")` / `record.get("execution_id")`,
  `None` for every legacy record, surfaced as an explicit `"legacy"` or `"unknown"` label per this
  ticket's own AC wording, not silently `None`).
- **No existing tests reference provider/execution_id** — confirmed via `grep` across
  `tests/tools/test_agent_ops_dashboard_*.py` (8 files, largest 642 lines,
  `test_agent_ops_dashboard_ingest.py`). This is genuinely new test surface, not an update to an
  existing assertion.

### Out-of-band diagnostic surface — no existing precedent, and stderr has a real wiring problem

Grepped `tools/agent-monitoring/` for `health`/`diagnostic` — zero hits. No file in this repo
today implements a "diagnostic surface separate from the main write path" pattern for monitoring
tooling. This is genuinely new design work, exactly as the ticket's own Assumptions section says.

**Concrete finding relevant to Plan's choice**: `.claude/settings.json:90` registers the
`PostToolUse` hook as `python3 tools/agent-monitoring/post_tool_hook.py 2>/dev/null || true` —
**stderr is discarded at the shell level for this call site**, and the exit code is masked by
`|| true`. Several of `record_run.py`/`record_events.py`'s own defensive call sites in
`.claude/workflows/implement-ticket.js`/`implement-epic.js` (lines 179, 182, 38, 176, 179, 202)
are similarly wrapped in `... 2>/dev/null || true`. The main "happy path" call sites (e.g.
`implement-ticket.js:316,319`) are *not* stderr-suppressed, but are literal Bash instructions
executed by an LLM-driven Finalize agent — stderr there is visible only in that agent's own
transcript, never durably captured anywhere. **Structured stderr output, as literally named in
the ticket's AC, is not a reliable diagnostic surface for at least the `post_tool_hook.py` call
site as currently wired** — using it would require also changing `.claude/settings.json`'s hook
command (removing `2>/dev/null`), which is a wiring change beyond "writer module," or accepting
that `post_tool_hook.py`'s failures stay invisible exactly as they are today. This is strong,
concrete evidence favoring a separate local diagnostic/health file for at least that call site;
flagged as an open question for Plan rather than assumed, per the launcher's explicit instruction.

## Mechanics / Engine Constraints

Not applicable. This ticket touches only `tools/agent-monitoring/`,
`src/api/agent_ops_dashboard/`, and their tests — no `src/` simulation code, no
`docs/mechanics/` chapter, no `docs/engine/` contract governs monitoring/observability tooling.

## Parity Ledger Overlap

None. Grepped all 8 `docs/parity_ledger/*.yaml` files for `monitoring|writer|jsonl|lock|fcntl|
flock` and for the predecessor ticket ID `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK` —
zero hits anywhere. The parity ledger tracks simulation-mechanics/engine-contract parity
(`docs/mechanics/`, `docs/engine/`); agent-monitoring tooling is process infrastructure outside
its domain, consistent with how the sibling ticket
`stored_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/investigation.md` reports the same
"not applicable" finding for equivalent tooling. No P0 parity entry is at risk from this ticket.

## Prior Work

- **`TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`** (hotfix, DONE, no stored staging
  artifacts — hotfix tier requires none) — added the `fcntl.flock` mechanism this ticket now
  replaces. Its own Out of Scope section explicitly deferred "redesigning `tools.jsonl`'s format
  ... this ticket is a minimal concurrency guard ... not a structural replacement" — this ticket
  is exactly that deferred structural replacement. Its ticket file documents the corruption
  mechanism this ticket must not regress (two processes' raw `write()` calls interleaving
  mid-line on a shared `O_APPEND` handle).
- **`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`** — investigated and *disproved* a
  different concurrency hypothesis for the same subsystem (sidecar-based run_id/seq
  misattribution was actually two deterministic non-concurrency gaps, not a race). Relevant
  context: not every "monitoring data looks wrong" symptom in this area is a concurrency bug —
  worth keeping in mind when writing the stress test's assertions (assert on byte/line integrity,
  not on attribution correctness, which is a different subsystem).
- **`TCK-20260709-AGENT-MONITORING-DURATION`** / **`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`**
  — established `record_run.py`/`record_events.py`'s current validate-then-compute-then-write
  shape (required-field validation, server-computed `duration_s`/`tool_call_count`/
  `cost_proxy_score` always overriding caller input). The shared writer must slot in *after* this
  existing validate/compute logic, not replace it.
- **`TCK-20260718-STATUS-DRIFT-REPAIR`** — the one documented exception to strict append-only
  behavior (audited, line-scoped casing correction on 7 records). Relevant precedent for how this
  repo treats "we found something wrong in old data" — never a bulk rewrite, always an
  individually-audited, narrowly-scoped substitution. Not directly actionable for this ticket but
  useful precedent if the exit-criterion manifest diff surfaces something unexpected.
- **`TCK-20260721-BASELINE-MONITORING-MANIFEST`** (hard predecessor, DONE) —
  `tools/agent-monitoring/manifest.py` provides exactly the entry/exit-criterion tooling this
  ticket needs (see Risks/Open Questions #4 below for the reuse-vs-new-function analysis).
- **`docs/architecture/agent_orchestration_contract.md`** ("Execution Identity (Consumed Input)"
  section, lines 116-160) quotes `monitoring_writer_decision.md` §2 verbatim and additionally
  states that **`ticket_id` is promoted to an explicit top-level schema field** as part of the
  same execution-identity model that `execution_id`/`provider` belong to — the ADR treats all
  three fields as one indivisible model. This ticket's own AC text only names `execution_id` +
  `provider` as the two additive fields to add — `ticket_id` is not mentioned. This is a real
  scope-boundary question for Plan (see Risks #1).

## Risks and Open Questions

1. **Does this ticket also add `ticket_id` as an explicit top-level field, or only
   `execution_id`/`provider`?** The ADR (`docs/architecture/agent_orchestration_contract.md:150-156`)
   treats `ticket_id`-as-top-level-field as part of the same already-decided Execution Identity
   Model as `execution_id`/`provider` — but this ticket's own Scope/AC text lists only
   `execution_id`/`provider`. Today `ticket_id` is only implicit inside `run_id`'s string shape
   for `implement-ticket` runs (and absent/different for `implement-epic`/`create-tickets`
   `run_id` shapes). **Flagging, not assuming**: Plan must decide whether adding `ticket_id` is
   in this ticket's scope (consistent with the ADR's model) or explicitly deferred (since the
   AC text omits it) — implementing only 2 of the ADR's 3 fields without a stated reason would
   leave the schema half-migrated.

2. **What exception-handling contract does the shared writer itself provide?** The candidate
   module lets a write-after-lock-acquired failure propagate uncaught (see Current Behavior
   above). This ticket's own AC requires "writer failures do not raise/propagate to fail the
   calling workflow." Does the shared writer module itself catch and swallow (returning e.g. a
   bool/result object) with the *diagnostic-surface write* is the caller's job, or does the
   writer module do both (catch, write diagnostic, return silently)? Either shape is defensible,
   but `post_tool_hook.py`'s outer `except Exception: pass` and `record_run.py`/`record_events.py`'s
   argparse+sys.exit CLI contracts are different enough (one already silent, two already
   exit-nonzero-on-failure with stderr) that "writer swallows everything itself" vs "writer raises
   a typed exception the caller decides how to handle" produces genuinely different integration
   code at 2 of the 3 call sites. Not resolvable from the candidate alone — a Plan decision.

3. **`record_events.py`'s batch-write atomicity.** If the shared writer's public API is
   single-line ("append this one already-serialized record, under one lock acquisition"),
   `record_events.py` calling it N times for an N-record batch means the batch's own lines are no
   longer guaranteed contiguous in the file (another process's single-record write could
   interleave between them) — never corrupting, but changing today's implicit "one batch write =
   contiguous lines" property. Whether that property is relied on anywhere downstream (not found
   in this investigation, but not exhaustively verified against every reader) and whether the
   shared writer needs a `write_lines(list[str])` batch variant is a Plan decision, not something
   to assume either way.

4. **Entry/exit-criterion manifest-diff mechanics — direct reuse confirmed, not a new function.**
   `tools/agent-monitoring/manifest.py::capture_lines(agent_monitoring_dir) ->
   dict[str, list[str]]` (line-lazy, single-pass, never a full `read_text()`) plus
   `assert_prefix_preserved(pre, post)` (asserts `post_lines[:len(pre_lines)] == pre_lines` per
   file, raising `AssertionError` naming the exact file on any rewrite/reorder/deletion) is
   **exactly** the entry/exit diff mechanism this ticket's Scope describes — it was built
   generically (a `dict[str, list[str]]` prefix-preservation check over all 3 files), not scoped
   to "one before/after snapshot around one specific action" as the launcher's briefing
   speculated. Reading its source confirms no modification is needed: call `capture_lines()`
   once before any writer-file change (entry), keep the result in memory or serialize it to a
   scratch path outside `agent-monitoring/`, then call `capture_lines()` again after all
   implementation work (exit) and pass both to `assert_prefix_preserved()`. `build_manifest()`
   (hash/line-count/legacy-classification per file) is a *coarser* secondary signal, useful for a
   human-readable before/after summary in the ticket's Implementation Notes, but
   `assert_prefix_preserved` is the actual pass/fail mechanism this ticket's exit criterion needs.
   No new manifest-tooling function is required for this ticket.

5. **The existing `test_post_tool_hook.py::test_locking_failure_does_not_propagate` test is
   fcntl-specific and will silently stop testing anything once the writer changes.** It works by
   reading the hook's source as a string and prepending a shim that monkeypatches
   `fcntl.flock = _raise_flock` before executing the (still fcntl-importing) hook body. Once
   `post_tool_hook.py` stops importing `fcntl` (routes through the new O_CREAT|O_EXCL writer
   instead), this shim's monkeypatch becomes a no-op — the test would still pass, but it would no
   longer be testing failure-suppression at all (false-green regression risk during migration).
   **This test must be rewritten to target the new writer's actual failure surface** (e.g.
   monkeypatch `os.open` to raise, or monkeypatch the shared writer module's public append
   function directly), not left as-is. See Test Plan.

6. **4 assertions in `test_post_tool_hook.py` do exact-field-set equality**
   (`assert set(record.keys()) == _RECORD_FIELDS`, lines 62/86/104/132, where `_RECORD_FIELDS`
   is the fixed 10-key set). If `tools.jsonl` records also gain `execution_id`/`provider` (not
   settled — see #7), these 4 assertions break and must be updated as part of this ticket's
   implementation, not treated as unrelated collateral. Notably, **no equivalent exact-field-set
   assertion exists in `test_record_run.py`/`test_record_events.py`** — only the
   `tools.jsonl` writer's tests are this brittle.

7. **Does `tools.jsonl` (one record per tool call) get `execution_id`/`provider` at all, or only
   `runs.jsonl`/`events.jsonl`?** `monitoring_writer_decision.md`'s only concrete synthetic
   example (§2, "Synthetic illustration") is shaped like a `runs.jsonl` record
   (`execution_id`/`run_id`/`ticket_id`/`provider`/`start_ts`) — it never shows a `tools.jsonl`- or
   `events.jsonl`-shaped example. `tools.jsonl` already carries `run_id`/`seq` for its join to
   `events.jsonl`; whether it additionally needs `execution_id`/`provider` (useful for a live,
   still-running execution's tool calls to be attributable before its `events.jsonl` row lands)
   is not specified anywhere read in this investigation. This directly determines the scope of
   risk #6 above and must be an explicit Plan decision, not inferred.

## Anti-Drift Hazards

- **Do not literally import from `tests/tools/test_monitoring_writer_lockfile_candidate.py`.**
  Its helper functions are test-local by design (including a guard that actively refuses to
  operate on any real `agent-monitoring/` path) — the production module must be new code under
  `tools/agent-monitoring/` that reuses only the *mechanics* (constants, O_CREAT|O_EXCL sequence),
  never the module itself.
- **Do not touch `query.py`, `validate.py`, or `generate_retro.py`.** Explicitly out of scope
  (owned by the dependent `agent-monitoring-derived-index` batch). `validate.py::load_jsonl` may
  be *read* (it's already reused by `ingest.py`) but not modified, and not even its
  `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` allowlists need touching — additive
  new fields don't affect completion-detection logic.
- **Do not modify `tools/agent-monitoring/legacy_reader.py` or `manifest.py`** — both are owned
  by the completed predecessor ticket and are consumed read-only here (`capture_lines`,
  `assert_prefix_preserved`, `build_manifest`).
- **Do not silently change `record_run.py`/`record_events.py`'s CLI exit-code/stderr contract**
  for validation failures (missing required fields, invalid status, malformed `--data` JSON) —
  those are pre-existing, tested behaviors unrelated to the writer/locking layer being unified.
  Only the *append* step (after validation passes) should route through the new shared writer.
- **Do not let the new lock-file protocol leave a stray `.lock` file behind on the real
  `agent-monitoring/` directory** if a test or a real run crashes mid-write — the stale-lock
  recovery test must prove an abandoned lock file (mtime-backdated past `stale_after_s`) is
  removed and superseded, not merely that a fresh lock acquisition eventually succeeds by luck.
- **Do not implement the SQLite index, or provider/execution_id-aware reads in `query.py`/
  `validate.py`/`generate_retro.py`** — those are the explicitly out-of-scope dependent tickets;
  this ticket's `ingest.py` change is a dashboard-only grouping/filtering/labeling addition, not
  a general read-side migration.
- **Do not treat "out-of-band diagnostic surface" as solvable by simply not suppressing
  `2>/dev/null`** in `.claude/settings.json` without considering that several call sites
  (fallback bash calls in the JS workflows) already deliberately suppress stderr with
  `|| true` for their own reasons (never blocking the workflow on a monitoring-write failure) —
  changing that wiring has broader blast radius than the writer module itself and should be a
  deliberate, stated Plan decision, not an incidental side effect of choosing "stderr" as the
  diagnostic surface.
