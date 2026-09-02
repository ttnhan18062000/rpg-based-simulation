---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-MIGRATION
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality, schema]
---

# Investigation — TCK-20260902-MONITORING-SHARD-MIGRATION

## Current Behavior

### `agent-monitoring/tools.jsonl` (source file, real measurement 2026-09-02)

- **Exact current line count: 179,243** (`wc -l agent-monitoring/tools.jsonl`), not the ticket's
  stated 179,096 — grown by 147 lines, consistent with the ticket's own warning that it kept
  receiving appends from this same session's tool calls until child ticket 1's cutover commit
  (`7aadcc2d`) took effect mid-session. **Any migration script must re-read the file's line count
  at run time, never hardcode 179,096 or 179,243** — both are already stale by the time an
  implementer runs the script.
- File size: 64MB.
- First line (line 1) has **no `ts` field at all** — it is a different record shape entirely (an
  `implement-epic` run summary: `{"tool": "implement-epic", "last_run": "2026-06-28T04:10:00Z",
  "result": "...", "tickets": [...]}`), not a tool-call record. This is the single line in the
  whole file lacking `ts`.
- Last line (line 179,243) is a live tool-call record from this investigation's own session
  (`ts: 2026-09-02T14:21:31.803950Z`), confirming the file was still receiving appends until very
  recently (child 1's cutover commit landed partway through this same session).
- Real ISO-week span (computed from every line's own `ts`, `%G-W%V`), **13 distinct weeks**, not
  "one or two":

  | Week | Rows |
  |---|---|
  | 2026-W24 | 1,430 |
  | 2026-W25 | 11,106 |
  | 2026-W26 | 8,536 |
  | 2026-W27 | 13,660 |
  | 2026-W28 | 13,444 |
  | 2026-W29 | 14,115 |
  | 2026-W30 | 3,979 |
  | 2026-W31 | 12,769 |
  | 2026-W32 | 14,882 |
  | 2026-W33 | 23,550 |
  | 2026-W34 | 23,034 |
  | 2026-W35 | 29,510 |
  | 2026-W36 | 9,227 |

  Sum = 179,242 (the +1 to reach 179,243 is the single missing-`ts` line 1, which cannot be
  week-bucketed and must go to a fallback bucket — see Risks/recommendation below). Earliest `ts`:
  `2026-06-13T17:23:37.173746Z`; latest: `2026-09-02T14:21:31.803950Z`.

### `agent-monitoring/tools/tools-2026-W36.jsonl` (child 1's live shard, real measurement)

- **Exact current line count: 96** — real, growing, post-cutover rows written by this very
  session's tool calls via `write_line()` (single-line append) from `post_tool_hook.py`
  (`tools/agent-monitoring/post_tool_hook.py:159`,
  `tools_file = Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"`). File size 45KB.
  This is a **live, actively-growing target** — any migration run must merge the historical
  2026-W36 bucket (9,227 rows from `tools.jsonl`) **before** these 96+ live rows, not overwrite or
  interleave them, and must tolerate the count still climbing between investigation and
  implementation.

### `tools/agent-monitoring/writer.py::write_lines()` (lines 137–162, read in full)

```python
def write_lines(target_path: Path, lines: list[str]) -> bool:
    lock_path = _lock_path_for(target_path)
    try:
        _acquire_lock(lock_path)
    except Exception as e:
        _write_diagnostic(target_path, "lock_acquire", e)
        return False
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a") as f:
            for line in lines:
                f.write(line + "\n")
    except Exception as e:
        _write_diagnostic(target_path, "write", e)
        return False
    finally:
        try:
            _release_lock(lock_path)
        except Exception as e:
            _write_diagnostic(target_path, "lock_release", e)
    return True
```

Confirmed exact contract:
- **Signature**: `write_lines(target_path: Path, lines: list[str]) -> bool`.
- **Appends, never overwrites/truncates**: opens with `"a"` (append mode), not `"w"`.
- **One lock acquisition for the whole batch**: `_acquire_lock(lock_path)` is called once before
  the loop, `_release_lock` once after — the loop over `lines` happens entirely inside that single
  lock window, so the whole batch lands as one contiguous block with no other writer able to
  interleave mid-batch. This exactly satisfies the ticket's "one lock acquisition per batch,
  preserving its existing 'one batch write = one contiguous block of lines' guarantee" requirement.
- Never raises to the caller (`bool` return, diagnostic sidecar on failure) — same contract as
  `write_line()`.
- Because appending happens for the *current week's* shard, calling `write_lines()` for the
  2026-W36 bucket after the file already has live rows is exactly the "append historical rows onto
  an already-non-empty file" case the ticket describes — no special-casing needed in `writer.py`
  itself, only in the migration script's own read-then-decide-what-to-append logic (it must not
  re-read/rewrite the file's existing content, only append the new historical block after it).

### `docs/agent-monitoring/schema.md` Known Limitations (tools.jsonl-specific portion, read in full)

The file's global "## Known Limitations" section (lines 459–485) is entirely about `runs.jsonl`
legacy schema generations (5+ shapes) — **not** about `tools.jsonl`. The `tools.jsonl`-specific
data-quality caveat lives earlier, in the "Derived SQLite Index" section (lines 34–38):

> `tools.jsonl` rows missing a `tool` field (a handful of confirmed off-schema records) are
> excluded from the `tools` table with a stderr warning, never coerced.

This is corroborated by `docs/parity_ledger/infrastructure.yaml` entry INFRA-290 (~line 6331),
which names the **exact single confirmed instance** as of 2026-07-28: a `TCK-20260716-SIMQ-...-
SWEEP seq=4` row with a valid `run_id`+`seq` but no `tool` field, shifting
`compute_tool_count_drift_report`'s "Mismatches" count from 487 to 488. `tests/tools/
test_validate_agent_monitoring.py::test_tools_row_missing_tool_field_is_a_known_bounded_divergence`
documents this against a synthetic fixture (not the real file).

### Real full-corpus scan performed for this investigation (179,243 lines, Python `json.loads`)

- **`json.loads` failures: 0 across all 179,243 lines.** Every line is syntactically valid JSON.
- **Missing `tool` field: exactly 2 lines** — line 21,117 (`{"run_id":
  "TCK-20260628-SIMQ-E1-FOUNDATION", "ts": "2026-06-29T05:34:06Z", "tools_used": [...],
  "files_written": 20, ...}` — a run-*summary* shaped record, also missing `seq`) and line 55,124
  (`{"session_id": "...", "run_id": "TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP", "seq":
  4, "ts": "2026-07-16T12:06:04"}` — this is the exact record INFRA-290/the test above document).
  Matches the doc's "a handful" characterization exactly (2, not dozens or hundreds).
- **Missing `run_id`: 1 line** (line 1, the `implement-epic` summary record above).
- **Missing `seq`: 2 lines** (line 1, and line 21,117).
- **Missing `ts`: 1 line** (line 1 only).
- No line combines "missing `ts`" with an otherwise-normal tool-call shape — the one `ts`-less
  line is also the one line with a completely different (run-summary, not tool-call) shape.

### `ts` format stability across the full historical file (real scan, all 179,243 lines)

- **179,240 / 179,243 lines (99.9983%)** use the exact format documented in schema.md:
  `%Y-%m-%dT%H:%M:%S.%fZ` (e.g. `2026-06-13T17:23:37.173746Z`).
- **2 lines** use a bare, timezone-less, no-fractional-seconds ISO shape:
  `2026-07-16T12:06:04` (line 55,124, the same missing-`tool` record above) — still parseable via
  `datetime.fromisoformat()` (naive, no explicit UTC marker) and still round-trips to a correct
  ISO week (`2026-W29`) once bucketed.
- **1 line** has no `ts` at all (line 1).
- **0 lines failed to parse** as a datetime once a `fromisoformat`-style parser (with `Z` →
  `+00:00` substitution, falling back to naive parsing when no explicit offset is present) is used
  — a bare `datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")` alone would fail on the 2 non-standard
  lines; the migration script must not use that single rigid format string.
- **Conclusion for the ticket's Assumption/Open Question #5**: `ts` format has been effectively
  stable across the whole historical file (prior format-changing tickets
  `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK` / `TCK-20260721-MONITORING-WRITER-UNIFICATION` /
  `TCK-20260719-LIVE-PHASE-AGENT-LABEL` changed the *locking mechanism* and *added new fields*
  `phase`/`agent`/execution-identity, not the `ts` field's own serialization format). The only
  drift found is 1 record with reduced precision, still ISO-8601-compatible.

### `.gitattributes` (read in full)

```
agent-monitoring/runs.jsonl merge=union
agent-monitoring/events.jsonl merge=union
agent-monitoring/tools.jsonl merge=union
agent-monitoring/tools/*.jsonl merge=union
tickets/working_log.csv merge=union
```

Both the legacy single-file line (to be removed by this ticket) and the shard-glob line (already
added by child 1, to be kept) currently coexist, exactly as child 1's own ticket described ("the
old line stays until a later ticket migrates/retires the legacy file" —
`tests/integrity/test_merge_union_gitattributes.py:100-104`'s own docstring, i.e. this ticket).

### Full-corpus `json.loads` timing (real measurement, not assumed)

Parsing every one of the 179,243 real lines with `json.loads` took **0.552 seconds** on this
machine. This directly answers the ticket's open question #7 in favor of **full-corpus, not
sampled, verification** — see Risks/Recommendations below.

## Mechanics / Engine Constraints

None. `agent-monitoring/` is pure Claude-Code-agent tooling infrastructure, not simulation
mechanics — it has no relationship to `docs/mechanics/` or `docs/engine/` law. Consistent with
child ticket 1's own investigation, which reached the same conclusion for the sibling write-path
ticket.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: the `## agent-monitoring/tools.jsonl` section's opening
  paragraph (line 341) currently reads *"The historical `agent-monitoring/tools.jsonl` (pre-cutover
  rows) remains present and unchanged, frozen — it receives no further appends, pending a future
  migration ticket."* This ticket **is** that migration — the sentence must be rewritten to state
  the file has been retired from the working tree, all its rows now live in
  `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards (plus whatever fallback-week file this
  ticket's Plan decides on for the one `ts`-less line), and its full history remains recoverable
  via `git log --follow` on the retired path.

The `docs/agent-monitoring/README.md` (path: `docs/agent-monitoring/README.md`) mentions of
`tools.jsonl` (the "What It Captures" bullet list, and the Navigation table row) are not required
to change by *this* ticket: they name the JSONL data family conceptually ("Every individual tool
call... (`tools.jsonl`)"), not a literal single-physical-file claim a consumer relies on for
correctness, and child ticket 3 (`TCK-20260902-MONITORING-SHARD-CONSUMERS`) already lists this
exact file in its own `Related Docs` — it is the ticket that changes how readers actually consume
the shard directory, so tightening this doc's data-source description alongside that read-path
change (rather than splitting it across two tickets) keeps the doc's before/after states coherent
in one place. This differs from child 1's judgment call on the same doc only in degree, not
direction: child 1 reasoned the file "still exists, is still readable"; that specific premise no
longer holds after this ticket retires the file, but the doc's own wording was never a
physical-path assertion in the first place, so the conclusion (defer to child 3) still holds.

The `docs/guides/agent_monitoring.md` guide (path: `docs/guides/agent_monitoring.md`) is not
required to change for this ticket: its `tools.jsonl` mentions describe report *semantics*
(the Tool Safety Audit and Parity Index Read-Path Usage sections), not the on-disk file layout —
unaffected by where the underlying rows physically live, same reasoning child 1 already
established for this doc.

`docs/ai/system_overview.md` §6 (path: `docs/ai/system_overview.md`) is not required to change by
this ticket: it is a high-level architecture summary sentence ("Agent activity is recorded in 3
append-only JSONL files under `agent-monitoring/`...") that child 1's own investigation already
flagged as becoming slightly imprecise, explicitly contingent on child tickets 2/3 landing
promptly — this ticket is exactly that landing. The remaining imprecision (shard files live one
directory deeper, in varying numbers rather than "3 files") is still a summary-level rounding, not
a claim any consumer parses programmatically, and child 3 already lists this doc in its own
`Related Docs` as the ticket that finishes the reader-side picture — bundling the final
one-sentence tightening there keeps it consistent with the rest of that doc's read-path
description rather than a partial edit now.

## Parity Ledger Overlap

None. Searched `docs/parity_ledger/infrastructure.yaml` (the "Replay, telemetry, observability,
workers" subsystem file) for any entry whose `text` asserts the physical single-file existence or
location of `agent-monitoring/tools.jsonl` as its parity claim — none exists, confirming child 1's
own prior finding still holds. The only `tools.jsonl`-path-adjacent entries (INFRA-289 through
INFRA-291) are about `query.py`/`validate.py`/`generate_retro.py`'s SQLite-index read-path
migrations, unrelated to physical file layout — none references a `test_path` that reads
`agent-monitoring/tools.jsonl` directly in a way this migration would break (see the reader-
breakage findings below, none of which are parity-ledger-tracked). Consistent with the established
repo pattern (confirmed by child 1's investigation): pure agent-monitoring tooling-infrastructure
tickets do not receive their own parity ledger entries. No P0 entries touched.

## Prior Work

- `stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/` (investigation.md, plan.md,
  test_plan.md) — child 1, already landed on this branch (commits `7aadcc2d`, `3bafffe0`). Its
  investigation explicitly named the reader gap this ticket must be aware of: `generate_retro.py`'s
  `DEFAULT_TOOLS_FILE` read-side default was judged safe to leave unchanged post-cutover
  specifically *because* "it still reads the frozen historical file" — child 1's own text. **This
  premise is exactly what this ticket invalidates** by retiring that file; see Risks below for the
  concrete, evidence-backed consequences that were not previously accounted for.
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `write_lines()`'s
  batch-write lock-window design/tradeoff, confirmed unmodified and reused as-is (per code read
  above).
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` — precedent
  cited by the ticket. Confirms the "historical data-quality caveats accepted as-is" framing (the
  archived doc explicitly frames `tools.jsonl`'s legacy shapes as excluded-with-warning, never
  repaired) and independently corroborates the "handful" (here: exactly 2) off-schema-record count
  via INFRA-290's own worked example.
- `tickets/todos/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-SHARD-CONSUMERS.md`
  (child 3, not yet started) — read to confirm its exact scope boundary. Its `Scope`/`Related Code
  Areas` sections name only `build_index.py`, `generate_retro.py`, `query.py`, `validate.py` — it
  does **not** mention `manifest.py`, `skill_usage_metric.py`, `weight_sensitivity_check.py`,
  `record_events.py`, or either of the two test files flagged below. This is not an oversight to
  fix silently — it is direct evidence that the reader-breakage findings below fall outside every
  currently-planned ticket in this epic and need an explicit decision from this ticket's Plan.

## Risks and Open Questions

**1. (Highest priority — new finding, not previously accounted for by child 1 or child 3's scope)
Retiring `tools.jsonl` breaks readers beyond the 4 that child 3 already plans to migrate**, because
child 1's own investigation justified leaving those 4 readers untouched specifically on the
assumption that `tools.jsonl` "still exists, is still readable" post-cutover — an assumption this
ticket removes. Real code/test evidence for each:

  - **Hard crash, not graceful degradation — `tools/agent-monitoring/manifest.py`**
    (`_FILES_BY_SOURCE` hardcodes `"tools.jsonl": "tools"`; `_scan_file()` does `open(path, "rb")`
    unconditionally, no existence check). `build_manifest()` and `capture_lines()` will raise
    `FileNotFoundError` once the file is gone. **4 real-corpus tests in
    `tests/tools/test_agent_monitoring_manifest.py`** run against the actual `agent-monitoring/`
    directory (never a tmp_path copy, by explicit design — the module's own docstring says so) and
    will fail: `test_build_manifest_shape_against_real_corpus` (asserts `len(records) == 3` and
    `set(filenames) == {"events.jsonl", "runs.jsonl", "tools.jsonl"}`),
    `test_manifest_cli_reproducible_byte_identical_across_two_runs`,
    `test_build_manifest_reproducible_byte_identical_direct_call`,
    `test_manifest_run_against_real_corpus_produces_zero_diff`.
  - **Hard crash — `tests/tools/test_skill_usage_metric.py`**: line 136 does
    `open(_REAL_TOOLS_FILE, encoding="utf-8")` unconditionally against
    `agent-monitoring/tools.jsonl` (no existence guard). Will raise `FileNotFoundError`.
  - **Silent, wider-than-before empty-data degradation (no crash) —
    `tools/agent-monitoring/generate_retro.py`, `validate.py`, `build_index.py`,
    `record_events.py`**: all route through a `path.exists()` guard (`load_jsonl()` in
    generate_retro.py/validate.py returns `[]` on a missing file; `record_events.py` line 59 checks
    `if TOOLS_FILE.exists():` before reading) so they will **not crash**, but they will now see
    **zero** `tools.jsonl` rows — not just "missing new post-cutover rows" as child 1's own
    investigation characterized the pre-this-ticket state, but the entire 179,243-row historical
    corpus becomes invisible to every stat these scripts derive from it (retro's tool-usage
    sections, `skill_usage_metric.py`'s per-skill counts, `weight_sensitivity_check.py`,
    `cost_proxy`/`tool_call_count` freshness checks, `build_index.py`'s `tools` table) — for the
    entire window between this ticket landing and child 3 landing. This is a strictly wider
    regression window than child 1 alone created, and it is not mentioned in this ticket's own Out
    of Scope or Acceptance Criteria.
  - **2 tests will fail for a certain, in-scope reason —
    `tests/integrity/test_merge_union_gitattributes.py`**:
    `test_gitattributes_lines_present_for_all_four_union_merge_paths` (asserts all 4 including
    `agent-monitoring/tools.jsonl merge=union`) and `test_gitattributes_line_present_for_shard_glob`
    (asserts both the shard-glob line *and* the legacy line are present — its own docstring already
    names this exact migration ticket as the one that will retire the legacy line). These two tests
    **must** be updated as a direct, certain consequence of this ticket's own in-scope
    `.gitattributes` edit — not a surprise, but must not be missed.
  - **Low-priority, non-breaking staleness — `tests/agent_replay/test_no_mutation_snapshot.py`**:
    `_WATCHED_GIT_PATHSPECS` hardcodes the literal string `"agent-monitoring/tools.jsonl"` for its
    `git status --porcelain -- <pathspecs>` fast-path check. A `git status` call against a
    nonexistent pathspec does not error (returns nothing for it), so this does not break, but the
    entry becomes a permanent no-op once the file is retired; `_watched_files()` (the fallback
    content-hash path) uses a glob (`agent-monitoring/*.jsonl`) so it self-heals automatically but
    still never picks up `agent-monitoring/tools/*.jsonl` (a pre-existing gap from child 1, not
    newly created here).

  **This is not this investigator's decision to make.** Plan must explicitly choose one of: (a)
  expand this ticket's scope to also fix `manifest.py`'s `_FILES_BY_SOURCE` (drop `tools.jsonl`, or
  point it at the shard directory) and update/quarantine the 5 real-corpus tests above that would
  otherwise hard-fail, accepting the silent-empty-data readers as a documented, bounded gap closed
  by child 3; (b) sequence child 3 to land immediately after this ticket in the same batch/session
  (SEQUENCE.md already orders it that way) and treat the interim window as acceptable given it is
  short; or (c) something else. Do not assume (a) or (b) — flag for Plan.

**2. Concurrent-worktree `.gitattributes`/`git rm` coordination risk (real, confirmed, not
theoretical).** This repository currently has 5 other checkouts of the same `.git` history besides
this worktree: the main checkout (branch `main`) plus 4 other active worktrees
(`m1-quick-wins`, `m3-family-species-implementation` [locked], `tactical-brain-readiness-doc-fix`
[locked], `brainstorm-idea-cross-index`). Checked via `git merge-base --is-ancestor
7aadcc2d <branch>` (child 1's cutover commit) against every one of them: **none** of the 5 has that
commit as an ancestor — every one of them is still on the pre-cutover `post_tool_hook.py`, meaning
any Claude Code session actively working in one of those worktrees right now is still appending
new rows directly to *its own local copy* of `agent-monitoring/tools.jsonl` (each worktree has an
independent physical working-tree file — no live file-handle race across worktrees, since they are
genuinely separate files on disk sharing only the `.git` object store). The real risk surfaces
later, at merge time: `merge=union` is a git *content*-merge driver — it is only invoked when a
path exists on both sides of a 3-way merge and git needs to reconcile *content* differences. A
path this branch deletes (`git rm agent-monitoring/tools.jsonl`) while another branch's history
still *modifies* that same path is a **modify/delete conflict**, a different git merge case
entirely that bypasses custom merge drivers altogether — git reports `CONFLICT (modify/delete):
agent-monitoring/tools.jsonl deleted in HEAD and modified in <branch>` and requires a human to
manually choose `git rm` or `git add` to resolve; it is never auto-resolved by `merge=union`. Any
of those 4 other worktrees' branches that later merges into a target already containing this
ticket's commit (after having appended more rows to its own `tools.jsonl` in the interim) will hit
this conflict. **Flagging for Plan**: this needs an explicit runbook line (e.g. "on a modify/delete
conflict for `agent-monitoring/tools.jsonl`, take the deletion and route the other branch's interim
rows through this ticket's own migration logic, or a follow-up mini-migration, rather than
resurrecting the monolithic file") rather than being silently assumed to be a non-issue.

**3. Fallback bucket for the single `ts`-less line.** Recommendation (not yet a decision — Plan's
call): route it to a dedicated `agent-monitoring/tools/tools-unknown-week.jsonl` file, mirroring
the **already-established, same-codebase convention** for exactly this failure mode —
`generate_retro.py::iso_week()` (line 123–128) already falls back to the literal string `"unknown"`
for any `ts` it cannot parse, and `_record_since_cutoff()`'s docstring (line 131–141) explicitly
names this as "iso_week()'s existing fail-to-'unknown' pattern." Reusing that exact, already-
documented convention (as a dedicated shard filename rather than a magic literal `"unknown"` week
string embedded in a `tools-unknown.jsonl` name) is lower-risk than inventing a new fallback (e.g.
falling back to file mtime, which would silently misattribute the row to whatever week the
migration script happened to run in, actively fabricating a false-precision week label for data
that is genuinely un-dated). With real data, this bucket would hold **exactly 1 row**
(the `implement-epic` summary line 1) — small enough that this is a low-consequence decision but
still one Plan should record explicitly, not leave implicit in code.

**4. Verification strategy: full-corpus, not sampled — recommended, backed by a real timing
measurement.** `json.loads`-parsing every one of the real file's 179,243 lines took **0.552
seconds** on this machine (measured for this investigation, not assumed from the archived design
doc's older 47k-line/"instant" framing). This is a one-time migration with a `git rm` as its
irreversible-from-the-working-tree final step — there is no performance argument for sampling, and
CLAUDE.md's "do not guess when uncertainty affects behavior or architecture" argues directly for
full-corpus verification given the cost is negligible. Recommend: (a) exact total original line
count vs. exact sum of all resulting shard line counts (not "approximately"); (b) per-week bucket
count reconciliation (the migration script's own bucketing pass output vs. a fresh read-back of
each written shard file); (c) full content-preservation check — every original line re-parsed via
`json.loads` and compared field-for-field (or byte-for-byte modulo trailing newline) against its
counterpart in the shard it landed in, for all 179,243 lines, not a sample.

**5. Live-growth race during migration.** Both `agent-monitoring/tools.jsonl` (until the ticket's
own `git rm`) and `agent-monitoring/tools/tools-2026-W36.jsonl` are still receiving real appends
from ongoing Claude Code sessions (including whichever session eventually implements this ticket).
The migration script must snapshot its own read of `tools.jsonl`'s line count/content at the start
of its run (not assume a static file) and must determine "already-existing 2026-W36 shard content"
by reading that file's current state at that same moment — appending after, never overwriting —
so a session concurrently appending to `tools.jsonl` while the migration script runs does not lose
that line (it would simply not yet be part of this migration's snapshot and would need a
documented "line count as of git commit `<sha>`" framing in Test Summary, not a claim of "the
entire file, forever").

## Anti-Drift Hazards

- **Do not touch `query.py`/`generate_retro.py`/`validate.py`/`build_index.py`'s read paths** —
  explicitly child 3's job (`TCK-20260902-MONITORING-SHARD-CONSUMERS`), and this ticket's own Out
  of Scope. It is tempting to "just fix the glob while I'm in here" once the reader-breakage
  finding above is understood — resist it; that is exactly the scope this ticket's Plan should
  either explicitly pull in (documented) or explicitly defer (documented), never silently absorb.
- **Do not repair or normalize the content of the 2 known off-schema lines** (missing `tool`,
  missing `run_id`/`seq`) beyond routing them to a correct week bucket by whatever `ts` they carry
  — explicitly Out of Scope. Route-only, content-preserving.
- **Do not backfill or coerce the 1 `ts`-less line's timestamp** — no schema upgrade, no inferred
  timestamp. Route it to the documented fallback bucket as-is.
- **Do not let the migration script re-derive or dedupe by `(run_id, seq)`** — this file has known
  historical pause/resume `seq`-collision duplicates (per schema.md's Known Limitations, in the
  `events`/`tools` index-table context) that a naive unique-key approach would crash on or silently
  drop; the migration's only ordering key is original append order within each `ts`-derived week
  bucket, never `(run_id, seq)` uniqueness.
- **Do not overwrite `agent-monitoring/tools/tools-2026-W36.jsonl`** — it must remain an append
  target (migrated historical rows written first, in one `write_lines()` batch, strictly before any
  of its current live rows in the final byte order) — never truncate-then-rewrite the whole file,
  which would also destroy this session's own already-recorded tool-call history.
- **Do not add a new `docs/parity_ledger/` entry for this migration** — established precedent (this
  investigation's own check, and child 1's) is that pure agent-monitoring tooling tickets do not
  get parity-ledger entries; adding one here would be inventing ledger scope, not following it.
- **Do not resolve the modify/delete `.gitattributes`/`tools.jsonl` merge-coordination risk (Risk
  #2) by silently assuming it away** — it is real, confirmed via `git merge-base --is-ancestor`
  against all 5 other live checkouts of this repo, not a hypothetical.
