---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-MIGRATION
artifact_type: plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-MIGRATION

## Summary

Write a new one-time migration script, `tools/agent-monitoring/migrate_monitoring_data.py`, that
generalizes `tools/agent-monitoring/migrate_tools_shards.py` (274 lines, read in full) from one
source (`tools.jsonl`) to three (`runs.jsonl`, `events.jsonl`, the already-sharded `tools/`
directory), expressing the two genuinely different strategies the investigation identified as two
distinct code paths rather than one forced-uniform loop: (1) `runs`/`events` are each one
monolithic file that needs per-line re-bucketing by a field-priority-ordered timestamp lookup on
each record, and (2) `tools` is a set of already-correctly-bucketed shard files that needs pure
filename-based relocation, with zero per-line re-bucketing. Both paths converge on the same reused
rename-aside + single-`write_lines()`-call primitive (`write_week_bucket`, generalized to take a
`source` + `data_dir` instead of a hardcoded `shard_dir`/`tools-` filename prefix) for the actual
write step, and the same reused full-corpus (non-sampled) verification primitive
(`verify_migration`, generalized the same way), run independently per source. Verification must
pass for all 3 sources, captured in the ticket's Test Summary, strictly before the `git rm` of any
of the 3 legacy paths — the script itself never calls `git rm`. The plan also updates the 3
existing test assertions the ticket's own `.gitattributes` edit breaks, adds a new test file
mirroring `test_migrate_tools_shards.py`'s own structure, and updates 3 now-stale "remains
present... until a future migration ticket" sentences in `docs/agent-monitoring/schema.md` (this
ticket is that future migration ticket). The Agent Ops Dashboard's `ingest.py` hardcoded legacy
paths are left untouched (out of scope, children 3/4's job) — this plan accepts and documents the
resulting transient dashboard-goes-empty gap rather than expanding scope to fix it.

## Steps

### Step 1 — Script skeleton + generalized shared primitives (no source-specific logic yet)

**Files:** `tools/agent-monitoring/migrate_monitoring_data.py` (new)

**Change:**
Create the new script. Reuse, via import, rather than duplicate:
- `_parse_ts_to_week` and `UNKNOWN_WEEK_KEY` from `migrate_tools_shards.py` (confirmed
  field-name-agnostic — takes a raw string, never touches `record.get(...)` itself —
  `tools/agent-monitoring/migrate_tools_shards.py:48-63`, `:45`). Import directly:
  `from migrate_tools_shards import _parse_ts_to_week, UNKNOWN_WEEK_KEY`.
- `write_lines` from `writer.py` directly (`tools/agent-monitoring/writer.py:137-162` —
  confirmed: one lock acquisition per batch call via `_acquire_lock`/`_release_lock`
  (`writer.py:143-161`), appends in `"a"` mode, never raises, returns `bool`).

Add two new generalized primitives that replace the hardcoded-shape pieces of the reference
implementation (per investigation's function-by-function read):

```python
def _target_path_for_week(week_key: str, source: str, data_dir: Path) -> Path:
    return data_dir / week_key / f"{source}.jsonl"
```
This replaces `_shard_path_for_week` (`migrate_tools_shards.py:82-83`, which hardcodes the
`tools-{week_key}.jsonl` flat-directory shape) with the per-week-directory,
per-source-file shape child 1 established (`agent-monitoring/data/<week>/<source>.jsonl`).

```python
def write_week_bucket(week_key, lines, source, data_dir) -> tuple[bool, list[str]]:
    ...
```
A direct copy of `migrate_tools_shards.py:86-139`'s rename-aside + combined-`write_lines()`
algorithm, mechanically changed only to call `_target_path_for_week(week_key, source, data_dir)`
in place of `_shard_path_for_week(week_key, shard_dir)`. Per investigation
(`migrate_tools_shards.py:86-139` docstring and body), the merge/reconciliation logic itself
(Case A direct write; Case B read live snapshot → `os.replace` rename-aside → one combined
`write_lines()` call → reconcile trailing suffix → delete backup, raising `RuntimeError` and
aborting with the backup left in place on any mismatch) needs zero behavioral change — only the
path-computation call site changes.

```python
def verify_migration(source_lines, buckets, source, data_dir, live_snapshots) -> dict:
    ...
```
A direct copy of `migrate_tools_shards.py:142-214`, same mechanical change (calls
`_target_path_for_week` instead of `_shard_path_for_week`). Returns the same keys
(`original_total`, `migrated_total`, `explained_delta`, `reconciles_exactly`,
`content_preserved`, `content_mismatches`, `all_lines_parse`, `parse_failures`,
`per_shard_counts`, `week_count`, `verification_passed`) — run once per source with that
source's own `source_lines`/`buckets`/`live_snapshots`, never combined across sources (the
ticket's own AC requires "line-count and content reconciliation both pass per source").

**Other writers to the shared resource this primitive touches (`agent-monitoring/data/<week>/
<source>.jsonl`):** `record_run.py` (writes `runs`), `record_events.py` (writes `events`),
`post_tool_hook.py` (writes `tools`) — all via child 1's write-path cutover, all through
`writer.py::write_line`/`write_lines` with the same lock-file protocol
(`writer.py:45-68` `_acquire_lock`). `write_week_bucket`'s Case B reads the live snapshot via a
plain unlocked `target_path.read_text()` (`migrate_tools_shards.py:116`, unchanged by this
generalization) and renames the file aside via unlocked `os.replace`
(`migrate_tools_shards.py:118`) *before* acquiring the lock for its own combined `write_lines()`
call — this is an inherited race window from the reference implementation, not new to this
ticket: a concurrent live writer's `write_lines()` call landing between the rename-aside and this
script's own `write_lines()` call would recreate `target_path` with its own line first (via its
own lock acquisition against the now-briefly-absent file), and this script's subsequent combined
write would then *append after* that live line rather than before it, violating the
migrated-first ordering AC for that one race window. This is the same theoretical race the prior
epic's `write_week_bucket` already carries and already implicitly accepted (its own docstring at
`migrate_tools_shards.py:92-94` frames "minimizing the window between snapshot and rename" as the
existing mitigation, not full prevention) — this plan reuses that primitive unmodified rather
than re-engineering a fix that would go beyond this ticket's scope (the ticket's own Scope text
requires reuse, not a redesign). Do not silently reduce the exposure by adding new locking here;
that would be a scope-expanding change to `write_week_bucket`'s contract not authorized by this
ticket.

**Do NOT touch:** `migrate_tools_shards.py` itself (imported from, not modified — the prior
epic's own script and its still-passing test suite are reused as regression coverage per
test_plan.md's Regression Surface, not edited).

**Verify:** No standalone test yet (no source wired in); the primitives are exercised by Step 2's
and later steps' tests. (Contributes to `test_case_b_merge_precedes_live_rows_for_all_three_
sources` and `test_migration_uses_one_write_lines_call_per_week_per_source` once at least one
source is wired in Step 2 — write both tests here once the `runs` source exists, extend them in
Steps 3/4 as `events`/`tools` are added, rather than writing throwaway single-source versions
now.)

---

### Step 2 — `runs` source: field-priority bucketing

**Files:** `tools/agent-monitoring/migrate_monitoring_data.py`,
`tests/tools/test_migrate_monitoring_data.py` (new)

**Change:**
Add the evidence-backed fallback field-priority list for `runs.jsonl`, derived directly from
investigation's full-corpus scan (`staging_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/
investigation.md`'s "Malformed / missing-timestamp historical rows" section: 105/1,388 records
missing `start_ts`, but 0 missing every timestamp-like field when checked against the full
8-field list `ts`, `start_ts`, `ts_start`, `started_at`, `completed_at`, `ts_end`, `finished_at`,
`timestamp` — the same 8-field list the investigation used to get the 0-count for `runs.jsonl`
and the 22-count for `events.jsonl`):

```python
RUNS_FIELD_PRIORITY = [
    "start_ts", "ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]
```

Add a generalized bucketing function replacing the hardcoded `"ts"` field name in
`bucket_lines_by_week` (`migrate_tools_shards.py:66-79`, which hardcodes `record.get("ts")` at
line 76 — investigation's own finding: "this is the one piece that must be parameterized... to
generalize to `runs.jsonl`'s `start_ts` field"):

```python
def bucket_lines_by_week_multi_field(lines: list[str], field_priority: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for line in lines:
        record = json.loads(line)
        value = next((record.get(f) for f in field_priority if record.get(f)), None)
        key = UNKNOWN_WEEK_KEY if not value else _parse_ts_to_week(value)
        buckets.setdefault(key, []).append(line)
    return buckets
```
Preserves the same single-forward-pass, never-re-sorted ordering guarantee as the reference
`bucket_lines_by_week` (`migrate_tools_shards.py:66-79` docstring). Route-only: never repairs or
normalizes a record's content, matching the ticket's explicit Out of Scope
("Repairing or normalizing the content of any malformed historical line beyond routing it to a
correct week bucket").

**Do NOT touch:** `events`/`tools` handling (added in Steps 3/4) — this step wires `runs` only.

**Verify:**
- `test_runs_bucket_by_start_ts_preserving_order` (unit) — synthetic records grouped by `start_ts`
  ISO week, original order preserved within each bucket.
- `test_runs_and_events_fallback_field_priority_documented_and_correct` (unit, `runs` half) —
  a record missing `start_ts` but carrying `timestamp` (mirroring the real
  `TCK-20260618-AUDIT-D10-TESTS` shape, investigation.md line ~152) routes via the fallback, not
  to `unknown-week`.

---

### Step 3 — `events` source: field-priority bucketing

**Files:** `tools/agent-monitoring/migrate_monitoring_data.py`,
`tests/tools/test_migrate_monitoring_data.py`

**Change:**
Add the `events.jsonl` fallback priority list (same 8-field evidence base, primary field `ts`
first):

```python
EVENTS_FIELD_PRIORITY = [
    "ts", "start_ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]
```

Reuse `bucket_lines_by_week_multi_field` from Step 2 (already field-priority-generic — no new
function needed). Confirm the falsy-value short-circuit (`record.get(f)` in the `next(...)`
generator expression) correctly handles the two real confirmed shapes from investigation: (a) an
explicit `"ts": null"` record (investigation.md, `events.jsonl` line 982) — `record.get("ts")`
returns `None`, falsy, generator moves to the next field in priority order; (b) a record with no
timestamp-like field at all (investigation.md, `events.jsonl` line 154, pure
`event_type`/`details` payload) — every field in the priority list returns `None` via
`.get()`'s default, `value` stays `None`, routes to `UNKNOWN_WEEK_KEY`.

**Do NOT touch:** `tools` handling (Step 4).

**Verify:**
- `test_events_bucket_by_ts_preserving_order` (unit).
- `test_runs_and_events_fallback_field_priority_documented_and_correct` (unit, `events` half) —
  the `"ts": null"` record and the no-timestamp-field record both route to `UNKNOWN_WEEK_KEY`; a
  record missing `ts` but carrying `timestamp` (33 of the 55 real cases per investigation) routes
  via the fallback correctly.

---

### Step 4 — `tools` source: filename-based relocation (no per-line re-bucketing)

**Files:** `tools/agent-monitoring/migrate_monitoring_data.py`,
`tests/tools/test_migrate_monitoring_data.py`

**Change:**
Add a relocation function that is deliberately *not* a bucketing function — it never calls
`json.loads()` on any line for the purpose of determining a target week:

```python
def relocate_tools_shards(tools_dir: Path) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for shard_path in sorted(tools_dir.glob("tools-*.jsonl")):
        week_key = shard_path.stem[len("tools-"):]
        buckets[week_key] = shard_path.read_text().splitlines()
    return buckets
```
`shard_path.stem[len("tools-"):]` mirrors the existing test file's own filename-parsing pattern
(`tests/tools/test_migrate_tools_shards.py:216-217`, confirmed by investigation) —
`"tools-2026-W24.jsonl"` → `"2026-W24"`, and `"tools-unknown-week.jsonl"` →
`"unknown-week"` (equal to `UNKNOWN_WEEK_KEY` by construction — the prior epic's own migration
already used this exact fallback bucket name for its own filename, per investigation's confirmed
`tools/tools-unknown-week.jsonl`, 1 line). Each shard's *entire* file content becomes one bucket —
this is the concrete implementation of the ticket's own explicit instruction ("Relocates `tools`
shards by parsing the ISO week directly out of each existing shard's filename... no re-bucketing
of individual `tools` records needed") and investigation's Anti-Drift Hazard ("Do not re-parse
`tools` shard content per-line for bucketing").

Per-line `json.loads()` for the `tools` source only happens later, inside `verify_migration`'s
existing round-trip check (`migrate_tools_shards.py:192-196`, reused unmodified via Step 1's
generalized `verify_migration`) — that check exists to prove content preservation, not to compute
bucket membership, and this distinction must not collapse.

**Do NOT touch:** Do not add any per-line `ts` extraction or `_parse_ts_to_week` call inside
`relocate_tools_shards` — this is the single most likely scope-creep failure mode per
investigation's Anti-Drift Hazards and test_plan.md's own Anti-Drift Test Guards section.

**Verify:**
- `test_tools_shard_relocation_parses_week_from_filename_not_content` (unit) — target week comes
  from the filename; assert via spy/monkeypatch that no per-line week-computation function
  (`_parse_ts_to_week`, `bucket_lines_by_week_multi_field`) is called during this step.
- `test_tools_relocation_is_route_only_not_re_bucketed` (integration, real-corpus copy) — every
  line inside a given `tools-YYYY-Www.jsonl` shard lands in the *same* target week folder
  regardless of that line's own `ts` content, including any line whose own `ts` falls in a
  different ISO week than its shard's filename claims.

---

### Step 5 — `main()` orchestration: wire all 3 sources through the shared write/verify primitives

**Files:** `tools/agent-monitoring/migrate_monitoring_data.py`,
`tests/tools/test_migrate_monitoring_data.py`

**Change:**
Implement `main()` as 3 genuinely distinct orchestration blocks sharing the Step 1 primitives —
not one uniform loop body, per investigation's explicit finding ("genuinely 3 different
orchestration shapes sharing the same per-week write/verify primitives, not one uniform loop
body"):

```python
def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    data_dir = repo_root / "agent-monitoring" / "data"
    reports = {}

    # runs
    runs_path = repo_root / "agent-monitoring" / "runs.jsonl"
    reports["runs"] = _migrate_rebucketed_source(
        runs_path, "runs", RUNS_FIELD_PRIORITY, data_dir
    )

    # events
    events_path = repo_root / "agent-monitoring" / "events.jsonl"
    reports["events"] = _migrate_rebucketed_source(
        events_path, "events", EVENTS_FIELD_PRIORITY, data_dir
    )

    # tools — relocation, not re-bucketing
    tools_dir = repo_root / "agent-monitoring" / "tools"
    reports["tools"] = _migrate_tools_relocation(tools_dir, data_dir)

    print(json.dumps(reports, indent=2, sort_keys=True))
    all_passed = all(r["verification_passed"] for r in reports.values())
    if not all_passed:
        print("VERIFICATION FAILED for at least one source — DO NOT run any git rm. "
              "Investigate the mismatches above before proceeding.", file=sys.stderr)
        return 1
    print("VERIFICATION PASSED for all 3 sources. None of the 3 legacy paths have been "
          "touched by this script — retirement (git rm) is a separate, explicit step to "
          "run only now that this report is captured in the ticket's Test Summary.")
    return 0
```

`_migrate_rebucketed_source(source_path, source, field_priority, data_dir)` factors the shared
runs/events sequence (abort-if-missing → read lines → `bucket_lines_by_week_multi_field` →
per-week `write_week_bucket` loop, collecting `live_snapshots` → `verify_migration`) so Step 2's
and Step 3's logic aren't duplicated verbatim in `main()`. `_migrate_tools_relocation(tools_dir,
data_dir)` runs the parallel sequence for the relocation path (abort-if-missing →
`relocate_tools_shards` → per-week `write_week_bucket` loop → `verify_migration`). Both helpers
follow the reference `main()`'s existing abort/print/exit-code conventions
(`migrate_tools_shards.py:217-269`) per source, never proceeding past a failed source's
verification to attempt the others' `git rm`-readiness message.

**Do NOT touch:** Do not add a `git rm` call anywhere in this script — matches the reference
implementation's explicit design (`migrate_tools_shards.py:8-9`, `:264-268`: "This script never
calls `git rm` itself") and the ticket's own Assumptions ("'Retire' means remove from the working
tree via a real commit... a working-tree change... only").

**Verify:**
- `test_every_pre_cutover_line_lands_in_exactly_one_file_per_source_content_preserved`
  (integration, real-corpus copy, `collections.Counter` multiset equality per source).
- `test_full_corpus_verification_reports_exact_counts_per_source` (integration, real-corpus copy)
  — `reconciles_exactly`/`content_preserved`/`all_lines_parse` all `True` per source;
  `explained_delta > 0` for whichever source(s) have live current-week content at test-run time
  (checked dynamically, never hardcoded, per investigation's own time-sensitivity note that only
  `tools` is confirmed to have live content as of investigation time).

---

### Step 6 — Execute the migration for real against the actual historical corpus (no `git rm` yet)

**Files:** None (script execution only); `tickets/inprogress/TCK-20260903-MONITORING-DATA-
MIGRATION.md`'s Test Summary section (captures the printed report).

**Change:** Run `python3 tools/agent-monitoring/migrate_monitoring_data.py` for real, against the
actual `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and
`agent-monitoring/tools/` — this is the actual one-time data migration this ticket exists to
perform, not a test. Confirm the printed JSON report shows `verification_passed: true` for all 3
sources (`runs`, `events`, `tools`) and paste/summarize the report into the ticket's Test Summary
section, per the ticket's own AC ("The migration script's own zero-data-loss verification run
against the real historical data... is captured in Test Summary before any file is retired").
This step **must** run after Step 5's `main()` is complete and its own tests (Step 5's Verify
list) pass, and **must** complete successfully before Step 7 runs.

**Do NOT touch:** Do not run `git rm` as part of this step, even if the report is clean — that is
Step 7, a distinct, explicit, human-reviewed action.

**Verify:** The printed report itself (`verification_passed: true` for `runs`, `events`, and
`tools` independently) — not a pytest test; this is the gating manual/operational check before
Step 7.

---

### Step 7 — Retire the 3 legacy paths via `git rm`

**Files:** `agent-monitoring/runs.jsonl` (removed), `agent-monitoring/events.jsonl` (removed),
`agent-monitoring/tools/` (removed, entire directory).

**Change:** Once Step 6's verification report shows `verification_passed: true` for all 3
sources, run:
```
git rm agent-monitoring/runs.jsonl agent-monitoring/events.jsonl
git rm -r agent-monitoring/tools/
```
Naming all 3 paths explicitly here (not describing the pattern abstractly once) is a direct,
explicit requirement of the ticket's own Assumptions/Open Questions "Decision" paragraph (ticket
body, "Explicitly re-evaluated, not silently carried forward" bullet) — do not reuse any
runbook language that mentions only `tools.jsonl`. Full content remains recoverable via
`git log --follow -- <path>` for each of the 3 — this is a supersession of physical layout, not
data loss (matches the prior epic's own explicit distinction, `migrate_tools_shards.py:6-9`,
carried forward per the ticket's own Scope text).

**Cross-worktree conflict runbook (cite, do not re-litigate — ticket body Assumptions section
already ratifies this):** if any other active worktree/branch (5 confirmed live at investigation
time: `docs-build-lastupdate-metadata-overhead`, `m2-foundational-systems-tickets`,
`m2-idea43-temporal-note`, `rpg-codex-temporal-axis-plan-sync`, plus `main`) merges past this
commit without first rebasing onto it and has appended new rows to any of the 3 now-deleted
paths in the interim, the merge will raise `CONFLICT (modify/delete)` for that path (`merge=union`
does not apply to modify/delete conflicts). Resolution: take the deletion side (`git rm <path>` at
the conflict) and, if that branch's interim rows need to be preserved, re-run this same migration
script against that branch's pre-merge copy of the file (or the new lines only) before finalizing
the merge. Per the ticket's own ratified decision: land and merge this ticket's PR promptly once
Step 6 through Step 11 are complete, rather than letting it sit open — the exposure window here is
3x the prior epic's single-file exposure.

**Do NOT touch:** Do not delete git history — this is a working-tree `git rm` + commit only, per
the ticket's explicit Out of Scope.

**Verify:** `test_legacy_paths_removed_after_migration` (architecture guard) — none of
`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, `agent-monitoring/tools/` exist in
the working tree.

---

### Step 8 — `.gitattributes`: remove the 3 superseded lines

**Files:** `.gitattributes`

**Change:** Remove exactly these 3 lines, confirmed present today at `.gitattributes:6-8`:
```
agent-monitoring/runs.jsonl merge=union
agent-monitoring/events.jsonl merge=union
agent-monitoring/tools/*.jsonl merge=union
```
Keep `agent-monitoring/data/*/*.jsonl merge=union` (`.gitattributes:9`, added by child 1) and
`tickets/working_log.csv merge=union` (`.gitattributes:10`), plus the explanatory comment block
above (`.gitattributes:1-5`) and the `docs/REGISTRY.yaml`-exclusion comment below
(`.gitattributes:12-15`) — both unrelated to this ticket, confirmed unchanged by investigation.

**Do NOT touch:** The comment blocks, the `data/*/*.jsonl` line, or the `working_log.csv` line.

**Verify:** `test_gitattributes_no_longer_references_any_of_the_3_retired_paths` (new,
architecture guard) — none of the 3 removed lines present; `agent-monitoring/data/*/*.jsonl
merge=union` still present.

---

### Step 9 — Update the 2 existing test files this ticket's `.gitattributes` edit breaks

**Files:** `tests/tools/test_migrate_tools_shards.py`, `tests/integrity/
test_merge_union_gitattributes.py`

**Change:**
1. `tests/tools/test_migrate_tools_shards.py::test_gitattributes_no_longer_references_retired_
   tools_jsonl_path` (currently lines 283-286, confirmed by direct read):
   ```python
   assert "agent-monitoring/tools.jsonl merge=union" not in content
   assert "agent-monitoring/tools/*.jsonl merge=union" in content
   ```
   The second assertion must flip to `not in content`, since this ticket removes that exact line
   too (it retires the entire `tools/` directory, not just the monolithic file the prior epic
   retired). Update the docstring/comment context accordingly (it currently has none directly
   above this function, but the neighboring function's docstring implies the shard-glob line is
   permanent — that implication is now stale).

2. `tests/integrity/test_merge_union_gitattributes.py::test_gitattributes_lines_present_for_
   three_legacy_union_merge_paths` (lines 85-99, confirmed): currently asserts
   `agent-monitoring/runs.jsonl merge=union` and `agent-monitoring/events.jsonl merge=union` (plus
   `tickets/working_log.csv merge=union`, unaffected) are present. Rewrite to drop the 2
   retired-line assertions, keeping only the `tickets/working_log.csv` assertion (the function
   name `..._three_legacy_union_merge_paths` becomes inaccurate once only 1 remains — rename to
   reflect the new state, e.g. `test_gitattributes_line_present_for_working_log_csv`, and update
   the docstring to state all 3 monitoring-source legacy lines are now retired by this ticket,
   matching the docstring style the prior epic already used at line 89 ("`agent-monitoring/
   tools.jsonl` was removed from this list by TCK-20260902-MONITORING-SHARD-MIGRATION...")).

3. `tests/integrity/test_merge_union_gitattributes.py::test_gitattributes_line_present_for_
   shard_glob` (lines 102-111, confirmed): currently asserts `agent-monitoring/tools/*.jsonl
   merge=union` is present and `agent-monitoring/tools.jsonl merge=union` is absent. Rewrite to
   assert both the shard-glob line and the monolithic-file line are now absent, and (mirroring the
   file's own established pattern of one function per retired shape) add an assertion that
   `agent-monitoring/data/*/*.jsonl merge=union` is present — matching this ticket's own new
   architecture guard (`test_gitattributes_no_longer_references_any_of_the_3_retired_paths`, Step
   8) but kept here too since test_plan.md explicitly calls out "having both a
   `migrate_tools_shards`-local guard and a separate `tests/integrity/` guard" as the established,
   intentional precedent, not redundancy to eliminate.

**Do NOT touch:** `test_concurrent_branch_appends_merge_without_conflict_markers`
(`tests/integrity/test_merge_union_gitattributes.py:42-83`) — confirmed unaffected, builds its own
throwaway `.gitattributes` inline, does not read the real repo file.

**Verify:** All 3 updated test functions pass against the post-Step-8 `.gitattributes`.

---

### Step 10 — Update `docs/agent-monitoring/schema.md`'s 3 now-stale sections

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Update the 3 locations investigation confirmed by direct read, each currently stating
the corresponding legacy file "remains present in the working tree, frozen... until a future
migration ticket folds it into the unified layout" — this ticket **is** that future migration
ticket:
1. `## agent-monitoring/runs.jsonl` section, currently (`schema.md:116-119`): "The historical
   monolithic `agent-monitoring/runs.jsonl` remains present in the working tree, frozen, receiving
   no new appends after this cutover, until a future migration ticket folds it into the unified
   layout." → replace with language stating the migration is complete: the file no longer exists
   in the working tree as of `TCK-20260903-MONITORING-DATA-MIGRATION`; every pre-cutover row was
   migrated into its matching `agent-monitoring/data/YYYY-Www/runs.jsonl` bucket (bucketed by each
   row's own `start_ts`, with a documented field-priority fallback for the rare row missing it);
   full history remains recoverable via `git log --follow -- agent-monitoring/runs.jsonl`.
2. `## agent-monitoring/events.jsonl` section, currently (`schema.md:144-147`): same phrasing
   pattern for `events.jsonl` — same replacement pattern, `ts`-bucketed, `git log --follow --
   agent-monitoring/events.jsonl`.
3. `## agent-monitoring/tools.jsonl` section, currently (`schema.md:372-375`): "The prior epic's
   `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards remain present in the working tree,
   frozen, receiving no new appends after this cutover, until a future migration ticket folds them
   into the unified layout." → replace stating the shards were relocated (not re-bucketed) into
   `agent-monitoring/data/YYYY-Www/tools.jsonl` by this ticket, filename-week-parsed, full history
   recoverable via `git log --follow -- agent-monitoring/tools/`.

This is included in this ticket's scope (not deferred) per the same precedent child 1's own
ticket used (keeping docs in sync in the same session/ticket as the behavior change) — leaving
these 3 sentences unedited would make the doc actively state a false physical fact (a file
"remains present" that this same ticket's Step 7 makes absent), not merely incomplete.

**Do NOT touch:** The per-record schema/field tables in any of the 3 sections (unaffected — the
per-record schema itself doesn't change, only where records physically land, per the existing
doc's own repeated framing at `schema.md:118-119`, `:146-147`, `:374-375`). Do NOT touch
`docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` (investigation
confirmed no change required — its data-quality-caveats-accepted-as-is rationale remains true)
or `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry (investigation confirmed its
`v2_evidence` citations of `ingest.py` remain accurate — updating it is children 3/4's own
Parity-phase responsibility once they actually change `ingest.py`'s read path).

**Verify:** Manual doc-content check — no automated test asserts `schema.md` prose content in
this repo's existing suite; confirm by re-reading the 3 edited sections against Step 7's real
`git rm` having landed. Run `make knowledge-index-update` per project convention since
`docs/` was modified.

---

## Scope Guards

- Do not touch `record_run.py`, `record_events.py`, `post_tool_hook.py`, or `writer.py` — the live
  write path is child 1's completed work; this ticket only migrates historical pre-cutover data.
- Do not add a Make target, cron entry, or any other ongoing/scheduled re-run mechanism for
  `migrate_monitoring_data.py` — genuinely one-time, matching the reference script's own explicit
  design (`migrate_tools_shards.py:11-12`).
- Do not modify `src/api/agent_ops_dashboard/ingest.py` — hardcoded legacy paths at lines 474-476
  (per investigation) are explicitly out of scope (children 3/4's job); see Anti-Drift Notes for
  the ratified decision to accept the resulting transient gap rather than expand scope here.
- Do not repair, normalize, dedupe, or re-key any malformed/off-schema historical line's content —
  route-only, for all 3 sources, matching the ticket's explicit Out of Scope.
- Do not modify `migrate_tools_shards.py` itself — import from it, do not edit it; its own test
  suite (`tests/tools/test_migrate_tools_shards.py`, minus the 2 assertions Step 9 updates) stays
  passing unmodified as regression coverage.
- Do not delete git history — `git rm` + commit only.
- Do not update `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md`
  or `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry — investigation confirmed
  neither requires a change from this ticket's scope.
- Do not add any new automated cross-worktree coordination tooling for the `git rm` conflict
  risk — stays documented-runbook-only per the ticket's own ratified Assumptions decision.

## Dependency Map

- Step 1 (shared primitives) is a prerequisite for Steps 2, 3, 4 (each source's bucketing/
  relocation logic calls into Step 1's `write_week_bucket`/`verify_migration`).
- Steps 2, 3, 4 are mutually independent (different sources, different functions) and may be
  implemented in any order relative to each other, but all three must land before Step 5.
- Step 5 (orchestration) depends on Steps 2, 3, 4 all being complete.
- Step 6 (real execution) depends on Step 5 passing its own tests.
- Step 7 (`git rm`) depends strictly on Step 6's verification report showing
  `verification_passed: true` for all 3 sources — never run out of order.
- Step 8 (`.gitattributes` edit) logically follows Step 7 (reflects the retirement that just
  happened) but has no hard code dependency on it.
- Step 9 (existing test updates) depends on Step 8 (the tests assert against post-edit
  `.gitattributes` content).
- Step 10 (`schema.md` update) depends on Step 7 (states the retirement as an accomplished fact).
- The new test file `tests/tools/test_migrate_monitoring_data.py` is built incrementally across
  Steps 1-5 (unit + integration tests) and Steps 7-8 (architecture guards added once their
  preconditions exist), matching `test_migrate_tools_shards.py`'s own structure.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Every pre-cutover line present exactly once in resulting `agent-monitoring/data/<week>/<source>.jsonl` | Steps 1-5 | `test_every_pre_cutover_line_lands_in_exactly_one_file_per_source_content_preserved` |
| No line duplicated or dropped; line-count + content reconciliation per source reported in Test Summary | Steps 5, 6 | `test_full_corpus_verification_reports_exact_counts_per_source`; Step 6's captured report |
| Records remain in original chronological (append) order within each resulting file | Step 1 (`write_week_bucket` Case A/B ordering) | `test_case_b_merge_precedes_live_rows_for_all_three_sources` |
| Live-row week folders (child 1 cutover) get migrated rows before live rows, per source independently | Step 5 | `test_case_b_merge_precedes_live_rows_for_all_three_sources`, `test_migration_uses_one_write_lines_call_per_week_per_source` |
| `runs.jsonl`, `events.jsonl`, `tools/` no longer exist in the working tree; history recoverable via `git log --follow` | Step 7 | `test_legacy_paths_removed_after_migration` |
| `.gitattributes` no longer references the 3 retired paths; unified glob remains | Step 8 | `test_gitattributes_no_longer_references_any_of_the_3_retired_paths`, updated `test_merge_union_gitattributes.py` tests (Step 9) |
| Zero-data-loss verification run against real historical data captured in Test Summary before retirement | Step 6 (before Step 7) | Manual — printed report pasted into ticket Test Summary |

## Anti-Drift Notes

- **Do not collapse the two migration strategies into one uniform loop.** `runs`/`events` require
  per-line `json.loads()` + field-priority timestamp extraction (Steps 2/3); `tools` requires pure
  filename-based relocation with zero per-line bucketing (Step 4). A future implementer
  "simplifying" `tools` to reuse `bucket_lines_by_week_multi_field` would silently reshuffle any
  line whose own `ts` disagrees with its shard filename's claimed week — exactly the scenario
  `test_tools_relocation_is_route_only_not_re_bucketed` exists to catch.
- **Do not conflate live-write-path bucketing (child 1, write-time "now") with this ticket's
  historical-record bucketing (each row's own `start_ts`/`ts` field).** These are two
  independently-correct rules for two different code paths — "fixing" the migration script to use
  write-time-of-migration-run bucketing by analogy to child 1 would misplace every historical
  record into whatever week the migration script happens to run in.
- **Run Step 6's real verification strictly before Step 7's `git rm` — never after, never
  interleaved.** The script itself never calls `git rm` (Step 5's `main()` design deliberately
  omits it, matching the reference implementation). If Step 6's report shows
  `verification_passed: false` for any source, stop — do not proceed to Step 7 for the other 2
  sources either, since the ticket retires all 3 paths together in one commit.
- **Decision (dashboard-goes-dark gap, ratified):** `src/api/agent_ops_dashboard/ingest.py`
  hardcodes the 3 legacy paths (lines 474-476 per investigation) and will read zero rows for all 3
  sources once Step 7's `git rm` lands, until children 3/4 repoint it. This plan does **not**
  expand scope to fix `ingest.py` — that is explicitly Out of Scope per the ticket's own text.
  Accepted as a documented transient gap, justified by: (a) `SEQUENCE.md`'s framing that children
  3-6 land immediately after this ticket, not as a standalone release; (b) the user's own explicit
  authorization to parallelize children 3-6 right after this ticket lands; (c) Step 7's own
  runbook note recommending prompt PR landing, which directly shortens this exact gap's window.
  This is a real functional regression window (unlike child 1's stale-but-present precedent), not
  a false equivalence — flagged explicitly here so the implementer does not mistake silence for
  "no risk," and so Finalize does not need to rediscover it.
- **Decision (schema.md staleness, ratified):** Included in this ticket's scope (Step 10) even
  though the ticket's own Scope text doesn't name `schema.md` directly, because leaving the 3
  "remains present... until a future migration ticket" sentences unedited would make the doc
  actively false about physical state this same ticket changes. Matches child 1's own precedent
  of keeping docs in sync in the same ticket as the behavior change.
- **The fallback field-priority lists (Steps 2/3) are a real decision made here, not left open**:
  `RUNS_FIELD_PRIORITY` and `EVENTS_FIELD_PRIORITY` both use the same evidence-backed 8-field list
  investigation's full-corpus scan validated (achieving 0 truly-timestamp-less `runs.jsonl`
  records and 22 truly-timestamp-less `events.jsonl` records), reordered only by which field is
  primary for that source. Do not narrow this list to fewer fields by analogy to the
  investigation's shorthand recommendation text ("ts/timestamp for runs") — that shorthand does
  not by itself reproduce the 0-count investigation actually verified; the full 8-field list is
  what achieves it.
- **`write_week_bucket`'s inherited race window (Step 1) is a known, accepted tradeoff, not a new
  gap to silently fix or silently ignore** — enumerated explicitly in Step 1's Change text. Do not
  add new locking around the snapshot-read/rename-aside sequence as part of this ticket; that
  would exceed the ticket's reuse-not-reinvent scope.

## Deviations (discovered during Implement, post-Step-7)

- **The Test Plan's "Regression Surface" claim that `tests/tools/test_agent_monitoring_manifest.py`
  and friends "construct their fixtures/caches against `tmp_path`-scoped repo roots... unaffected
  by this ticket's retirement of the real `runs.jsonl`/`events.jsonl`/`tools/` paths" is factually
  incorrect for a broader set of tests than investigation identified.** After Step 7's `git rm` and
  Step 8's `.gitattributes` edit, the broad regression pass
  (`pytest tests/tools/ tests/integrity/ -k "monitoring or gitattributes or agent_ops_dashboard or
  migrate or writer"`) surfaced **7 newly-failing tests across 3 files**, all confirmed by direct
  read to construct paths against the **real** `agent-monitoring/` directory
  (`_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"` / `_REAL_MONITORING_DIR`), not
  `tmp_path`:
  - `tests/tools/test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_
    current_and_agree_with_validate` and `::test_recent_events_records_remain_parseable` — this
    file's own docstring states it does a "round-trip readability test against real, recent
    runs.jsonl/events.jsonl records"; not listed anywhere in the Test Plan's Regression Surface at
    all (a coverage gap, not just a mischaracterization).
  - `tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`,
    `::test_manifest_cli_reproducible_byte_identical_across_two_runs`,
    `::test_build_manifest_reproducible_byte_identical_direct_call`,
    `::test_manifest_run_against_real_corpus_produces_zero_diff` — `build_manifest()` reads
    `_WATCHED_JSONL_FILES = ["events.jsonl", "runs.jsonl", "tools.jsonl"]` directly against
    `_REAL_AGENT_MONITORING_DIR`, which this ticket's Step 7 makes absent for all 3 (this is exactly
    `manifest.py`, explicitly named in the ticket's own Out of Scope text as a children-3/4
    consumer — the test-level consequence just wasn't traced through in Investigate).
  - `tests/tools/test_done_ticket_monitoring_coverage.py::test_live_corpus_does_not_false_positive_
    this_sessions_own_recent_tickets` — re-derives coverage "against the real, current runs.jsonl"
    per its own comment; fails once that file no longer exists.
  - (A separate, unrelated 8th failure, `test_kgmcp_phase3_pilot_acceptance_measurement.py::test_
    zero_mutation_of_agent_monitoring_and_manifest_across_full_run`, is a pre-existing
    resource-budget `TimeoutError` reading `docs/REGISTRY.yaml` via a live gateway call — marked
    `@pytest.mark.extra_slow`/`@pytest.mark.slow`, unrelated to this ticket's file retirement;
    confirmed by traceback, not caused by this migration.)

  **This is the same class of risk this plan already explicitly accepted for
  `src/api/agent_ops_dashboard/ingest.py`** (see this file's Anti-Drift Notes, "dashboard-goes-dark
  gap, ratified") — a real consumer/test dependency on the 3 now-retired physical paths, left broken
  until children 3/4 repoint the underlying tools (`legacy_reader.py`, `build_index.py`'s
  `build_manifest()`, and whatever `test_done_ticket_monitoring_coverage.py`'s own tool reads) at
  the new `agent-monitoring/data/<week>/<source>.jsonl` layout. It is broader than the plan
  originally scoped (investigation only traced `ingest.py`, not these 3 test files/7 tests), but the
  same ratified decision applies: do not fix the consumers here (out of scope, children 3/4's job),
  do not revert the migration (Step 6's verification passed cleanly for all 3 sources, and the
  ticket's own AC requires retirement once it does) — flag explicitly so Finalize/the next
  implementer does not mistake this for a new, unexplained regression. No test file or consumer
  tool was modified to route around this; nothing here is a silent workaround.
