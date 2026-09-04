---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-MIGRATION
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality, schema]
---

# Investigation — TCK-20260903-MONITORING-DATA-MIGRATION

## Current Behavior

### Real corpus state at investigation time (direct `ls`/`wc -l`, not trusted from the ticket)

- `agent-monitoring/runs.jsonl`: **1,388 lines**, 400,959 bytes (~391KB). Tail record dated
  `2026-09-02T18:38:59Z` — confirms no post-cutover appends (child 1 landed 2026-09-03, writes now go
  to `agent-monitoring/data/<week>/runs.jsonl`).
- `agent-monitoring/events.jsonl`: **9,018 lines**, 3,329,705 bytes (~3.2MB). Same freeze confirmed.
- `agent-monitoring/tools/`: 13 week-shard files (`tools-2026-W24.jsonl` through `tools-2026-W36.jsonl`)
  totaling **180,292 lines**, plus `tools-unknown-week.jsonl` (1 line, 480 bytes, already counted in
  the 180,292 total — it's the last file `wc -l` lists). Grand total across all sources: **190,698
  lines**. This is comparable order-of-magnitude to `migrate_tools_shards.py`'s own prior real run
  (179,243 lines / 64MB, per `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/plan.md`), so
  the established full-file-`read_text().splitlines()`-in-memory approach remains safe; no streaming
  is needed.
- `agent-monitoring/data/2026-W36/` currently contains **only `tools.jsonl`** (3,853 lines) — no
  `runs.jsonl`/`events.jsonl` yet exist under any `agent-monitoring/data/*/` folder at investigation
  time. This is because child 1's write-path cutover only just landed and no `record_run.py`/
  `record_events.py` invocation has fired yet in this session since the cutover. **This is
  time-sensitive**: by the time this ticket is actually implemented, `runs`/`events` current-week
  files may well exist too (any ticket work performed via `implement-ticket.js` after child 1 landed
  will create them). The migration script must not assume `runs`/`events` are always Case A (no live
  file) just because that's true right now — `write_week_bucket()`'s existing Case A/B branch
  (`target_path.exists()` check) already handles this generically; do not special-case it.

### `tools/agent-monitoring/migrate_tools_shards.py` — the reference implementation to generalize

Read in full (274 lines). Function-by-function:

- **`_parse_ts_to_week(ts: str) -> str`** (lines 48-63): tolerant ISO-8601 → `%G-W%V` parser. Tries
  `datetime.fromisoformat(ts.replace("Z", "+00:00"))` first, falls back to
  `datetime.fromisoformat(ts)` bare, and returns `UNKNOWN_WEEK_KEY` (`"unknown-week"`, line 45) if
  both raise. Never raises itself. **Directly reusable unmodified** for `runs`/`events`
  re-bucketing — it is field-name-agnostic (takes a raw `ts` string, caller extracts the field).

- **`bucket_lines_by_week(lines: list[str]) -> dict[str, list[str]]`** (lines 66-79): single forward
  pass, `json.loads()` each line, reads `record.get("ts")`, buckets via `dict.setdefault(key,
  []).append(line)` — preserves original file order within each bucket, never re-sorts. **Hardcodes
  the field name `"ts"` at line 76** (`ts = record.get("ts")`) — this is the one piece that must be
  parameterized (or duplicated with a different field name) to generalize to `runs.jsonl`'s
  `start_ts` field. `events.jsonl` already uses `ts`, so it can reuse this function as-is; `runs`
  needs either a `field` parameter added or a near-identical sibling function.

- **`_shard_path_for_week(week_key, shard_dir) -> Path`** (lines 82-83): `shard_dir /
  f"tools-{week_key}.jsonl"` — **hardcodes the `tools-` filename prefix and the flat
  `tools/tools-<week>.jsonl` shape**. This is the other piece requiring genuine change: the new
  target shape is `agent-monitoring/data/<week>/<source>.jsonl` (a per-week *directory* containing
  one file per source, not a flat directory of prefixed filenames). A generalized
  `_target_path_for_week(week_key, source, data_dir)` would be `data_dir / week_key /
  f"{source}.jsonl"`.

- **`write_week_bucket(week_key, lines, shard_dir) -> tuple[bool, list[str]]`** (lines 86-139): the
  reusable rename-aside + combined-write algorithm the ticket explicitly requires generalizing, not
  reinventing:
  - `target_path.parent.mkdir(parents=True, exist_ok=True)` (line 110) — must run before
    `write_lines()`'s own internal mkdir, because `writer.py::_acquire_lock()` (line 115 there)
    creates the lock file via `os.open(..., O_CREAT | O_EXCL | O_WRONLY)` *before* `write_line`'s own
    `target_path.parent.mkdir()` (writer.py line 120) ever runs — an `os.open` against a
    not-yet-existing parent directory raises `FileNotFoundError`, uncaught by `_acquire_lock`'s own
    `except FileExistsError`. Same load-bearing ordering `record_run.py`/`record_events.py`/
    `post_tool_hook.py` already rely on (confirmed identically in
    `stored_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/investigation.md`'s "writer.py —
    confirmed unmodified-but-load-bearing" section).
  - **Case A** (`not target_path.exists() or target_path.stat().st_size == 0`, line 112): one direct
    `write_lines(target_path, lines)` call, returns `(ok, [])`.
  - **Case B** (target has live content): read `live_snapshot = target_path.read_text().splitlines()`
    (line 116), `os.replace(target_path, backup_path)` to rename the live file aside (line 118, atomic
    on the same filesystem), then `combined = lines + live_snapshot` (migrated-first, line-order
    preserved) written as **one single** `write_lines(target_path, combined)` call (line 121) — never
    two separate appends, which would violate `write_lines()`'s "one lock = one contiguous batch"
    contract and could interleave with a concurrent live writer between the two calls. After the
    write, it re-reads the file and reconciles that the trailing `len(live_snapshot)` lines exactly
    equal `live_snapshot` (lines 128-136) before deleting the backup (line 138) — raises
    `RuntimeError` and aborts (leaving the backup in place) on any mismatch, rather than silently
    proceeding.
  - This function is **already fully generic on `shard_dir`/`target_path`** — nothing about it
    assumes the `tools-<week>.jsonl` filename shape except via `_shard_path_for_week()`'s call at
    line 103. Generalizing means either (a) passing a pre-computed `target_path` directly instead of
    `(week_key, shard_dir)`, or (b) adding a `source` parameter and computing the path internally via
    a generalized path-helper. Either is a small, mechanical change — the merge/reconciliation logic
    itself needs zero modification.

- **`verify_migration(source_lines, buckets, shard_dir, live_snapshots) -> dict`** (lines 142-214):
  full-corpus (not sampled) verification. For each bucket: re-reads the shard's actual on-disk
  content, splits off the trailing `live_snapshot`-length suffix (if any) and compares it byte-exact
  to the pre-migration snapshot, compares the remaining "migrated part" to the exact bucketed lines
  in memory, and re-`json.loads()`s every persisted line to confirm it still round-trips. Returns a
  dict with `original_total`, `migrated_total`, `explained_delta` (= sum of live-snapshot lengths),
  `reconciles_exactly` (`migrated_total == original_total + explained_delta`), `content_preserved`,
  `all_lines_parse`, `per_shard_counts`, and an overall `verification_passed` boolean. **Also fully
  generic on `shard_dir`/path shape** via its reuse of `_shard_path_for_week()` — same generalization
  point as `write_week_bucket()`. For 3 sources this needs to run once per source (or be extended
  with a `source` dimension) since `runs`/`events`/`tools` are verified against 3 independent
  `original_total`s, not one combined figure — the ticket's own AC ("line-count and content
  reconciliation both pass **per source**, reported in Test Summary") already requires this.

- **`main()`** (lines 217-273): orchestrates read → bucket → per-week `write_week_bucket()` loop →
  `verify_migration()` → conditional `git rm`-readiness message (never calls `git rm` itself — that
  stays a separate, explicit, human-reviewed step, matching this ticket's own AC/Assumptions
  language "Retire... means remove from the working tree via a real commit... this is a working-tree
  change... only"). For 3 sources, `main()` needs to become a loop over `("runs", "start_ts")`,
  `("events", "ts")`, and a **distinct, non-bucketing** code path for `tools` (see below) — genuinely
  3 different orchestration shapes sharing the same per-week write/verify primitives, not one
  uniform loop body.

### The two genuinely different migration strategies (confirmed by direct data read, not assumed)

1. **`runs`/`events`: per-line re-bucketing from one monolithic file.** Confirmed via direct sampling
   above: `agent-monitoring/runs.jsonl` records carry a `start_ts` field (standard schema) or one of
   several legacy alternates; `agent-monitoring/events.jsonl` records carry `ts`. Both need
   `bucket_lines_by_week()`-style per-line `json.loads()` + field extraction + ISO-week computation,
   exactly like the prior epic's `tools.jsonl` migration did for `ts`.
2. **`tools`: pure relocation, not re-bucketing.** Confirmed via direct `ls`: every existing
   `agent-monitoring/tools/tools-YYYY-Www.jsonl` filename already encodes its own correct week
   (`tools-2026-W24.jsonl` … `tools-2026-W36.jsonl`, plus `tools-unknown-week.jsonl`). The prior
   epic's `migrate_tools_shards.py` already did the per-line `ts`-based bucketing once; re-parsing
   every line's `ts` again here would be redundant work and a needless second opportunity to
   introduce a bucketing bug. The week key for each shard is extracted directly from the filename
   (`"tools-2026-W24.jsonl"` → `"2026-W24"`, mirroring `_run_migration_against_copy()`'s own
   `real_shard_path.stem[len("tools-"):]` slicing pattern in the test file, lines 216-217) and its
   **entire file content becomes the "bucket"** for `write_week_bucket()` — no `json.loads()` of
   individual tool-call rows is needed for bucketing purposes at all (though the zero-data-loss
   verification step still round-trips each line through `json.loads()`, same as the other two
   sources, per the AC).

### Malformed / missing-timestamp historical rows — quantified by direct full-corpus scan (not sampled)

`docs/agent-monitoring/schema.md`'s "Known Limitations" section (lines 496-522) documents **6 legacy
`runs.jsonl` schema generations** lacking `end_ts` (not `start_ts`) — a different concern (run
completion detection) from this ticket's bucketing-field concern, but confirms legacy shape
heterogeneity is expected and already precedented as accepted, not "repaired."

A direct full-corpus Python scan (not sampling) found:

- **`runs.jsonl`** (1,388 total records): **105 records (7.6%) missing `start_ts`**, but **0 records
  missing every timestamp-like field** — every one of the 105 carries at least one usable alternate:
  `ts` (39), `started_at` (41), `completed_at` (21), `ts_start` (7), `ts_end` (7) — counts overlap
  (some legacy records carry more than one alternate field, e.g. both `started_at` and
  `completed_at`), and a further 16 of those 105 carry only a `timestamp` field (the `TCK-20260618-
  AUDIT-D*` legacy generation, e.g. line 146: `{"run_id": "TCK-20260618-AUDIT-D10-TESTS", ...,
  "timestamp": "2026-06-18T00:00:00Z", ...}`). **Zero JSON-parse failures** across all 1,388 lines.
- **`events.jsonl`** (9,018 total records): **55 records (0.6%) missing `ts`**, of which **22
  records genuinely carry no timestamp-like field at all** (checked against the same fallback
  priority list: `ts`, `start_ts`, `ts_start`, `started_at`, `completed_at`, `ts_end`,
  `finished_at`, `timestamp` — none present). Sample confirmed shapes: pure `event_type`/`details`
  payload records with no time field whatsoever (e.g. line 154:
  `{"run_id": "TCK-20260610-AUDIT-EVENT-SEQUENCE", "event_type": "implementation_complete",
  "details": {...}}`), and one record with an **explicit `"ts": null`** (line 982:
  `{"run_id": "TCK-20260619-E53Ab-DECISION-PHASE", "seq": 10, ..., "ts": null, ...}` — `.get("ts")`
  returns `None`, falsy, correctly routed to fallback by the existing `if not ts else` pattern
  `bucket_lines_by_week()` already uses at line 77). The remaining 33 of the 55 carry a `timestamp`
  field usable as a fallback.

**Concrete, evidence-backed fallback rule recommendation** (the ticket leaves this as an
implementation decision — this investigation supplies the real distribution to design against, not a
hypothetical): route by `start_ts`/`ts` first; if absent/falsy, fall back through a short, explicit
priority list of legacy alternates actually observed in the real data (`ts`/`timestamp` for `runs`;
`timestamp` for `events`) before finally routing to the shared `UNKNOWN_WEEK_KEY` (`"unknown-week"`)
fallback bucket — this keeps the true "no usable timestamp at all" bucket to the smallest evidence-
backed size: **0 for `runs.jsonl`, 22 for `events.jsonl`** (not 105/55, which would be the naive
"only check the primary field" count). This mirrors the prior epic's own precedent exactly (its
`_parse_ts_to_week` already tries 2 format variants before giving up) but extends it to alternate
*field names*, not just alternate *timestamp formats* — a genuinely new piece of logic
`_parse_ts_to_week()` itself doesn't need to change for, since it only ever receives a string; the
field-priority selection is bucketing-level logic, one layer up.

### `.gitattributes` — confirmed exact current state (5 lines + comment block, matching the ticket's citation)

```
agent-monitoring/runs.jsonl merge=union
agent-monitoring/events.jsonl merge=union
agent-monitoring/tools/*.jsonl merge=union
agent-monitoring/data/*/*.jsonl merge=union
tickets/working_log.csv merge=union
```
(plus the pre-existing 5-line explanatory comment above these, and the `docs/REGISTRY.yaml`-exclusion
comment below — both unrelated to this ticket, confirmed unchanged). The 3 lines this ticket must
remove (`agent-monitoring/runs.jsonl merge=union`, `agent-monitoring/events.jsonl merge=union`,
`agent-monitoring/tools/*.jsonl merge=union`) and the 1 line to keep
(`agent-monitoring/data/*/*.jsonl merge=union`, added by child 1) are confirmed present exactly as
the ticket states — no drift.

### Zero-data-loss verification test precedent — `tests/tools/test_migrate_tools_shards.py` (287 lines)

Structure (confirmed by direct read):
- **Synthetic-fixture unit tests** (lines 40-179): `bucket_lines_by_week` ordering/malformed-routing/
  fallback/format-variant tests, and `write_week_bucket` Case A/B tests including the exact "migrated
  rows precede live rows" assertion (`test_current_week_shard_migrated_rows_precede_existing_live_
  rows`, lines 102-123) and the "exactly one `write_lines()` call per week bucket, combined not
  split" assertion (`test_migration_uses_write_lines_one_lock_per_week_batch`, lines 138-178, using a
  `monkeypatch.setattr(migrate_tools_shards, "write_lines", _spy_write_lines)` spy).
- **Real-corpus integration tests** (lines 181-269): `_run_migration_against_copy()` (lines 185-229)
  is the key precedent this ticket's own test file should follow — it copies the **real**
  `agent-monitoring/tools.jsonl` (and, if present, the real live shard files matching whatever weeks
  the source buckets into) into `tmp_path`, runs the full bucket→write→verify pipeline there, and
  **skips (not fails)** once the real source file no longer exists (`pytest.skip(...)`, lines 200-205)
  — an explicit, documented acknowledgment that after the real one-time migration retires the source,
  this integration test becomes structurally unrunnable and that is the *intended* end state, not a
  regression. `test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved` (lines
  232-249) does a `collections.Counter` multiset-equality check (catching drops *and* duplicates,
  preserving genuine duplicate lines). `test_full_corpus_verification_reports_exact_not_approximate_
  counts` (lines 252-268) asserts `explained_delta > 0` when live snapshots exist — an explicit guard
  against the Case B merge path silently stopping being exercised.
- **Architecture guards** (lines 271-287), run only after retirement: confirm the source file no
  longer exists, and confirm `.gitattributes` no longer references it.

**Direct conflict already found in this existing test file** (not hypothetical — confirmed by
reading the exact assertions): `test_gitattributes_no_longer_references_retired_tools_jsonl_path`
(lines 283-286) currently asserts:
```python
assert "agent-monitoring/tools.jsonl merge=union" not in content
assert "agent-monitoring/tools/*.jsonl merge=union" in content
```
The second assertion **will start failing** once this ticket removes the
`agent-monitoring/tools/*.jsonl merge=union` line (this ticket retires the entire `tools/` directory,
not just the monolithic file the prior epic retired) — this existing test must be updated as part of
this ticket's own change, not left to break silently. See Test Plan's Regression Surface.

### `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/` — cross-worktree `git rm` runbook, re-verified accurate

Confirmed by direct read of `plan.md` and `investigation.md`: the documented resolution for a
modify/delete conflict is "take the deletion side (`git rm <path>` at the conflict), and if that
other branch's interim rows need to be preserved, re-run this same script against that branch's
pre-merge copy of the file (or a targeted subset of its new lines) before finalizing the merge." This
runbook is generic to any append-only-log `git rm` and directly extends to all 3 of this ticket's
retired paths. **Re-confirmed the underlying risk is live, not hypothetical**: `git worktree list`
shows 5 other active worktrees beyond this one and `main` at investigation time
(`docs-build-lastupdate-metadata-overhead` [branch `m1-quick-wins`],
`m2-foundational-systems-tickets` [branch `m4-institutions-economic-signals-implementation`, locked],
`m2-idea43-temporal-note` [branch `worldcompiler-place-wiring`, locked],
`rpg-codex-temporal-axis-plan-sync` [branch `brainstorm-idea-cross-index`]) — a real, current
multi-worktree exposure surface for whichever of these branches later merges past this ticket's
commit without having first rebased onto it.

### A cross-consumer risk not previously flagged anywhere in the ticket text (new finding)

`src/api/agent_ops_dashboard/ingest.py` (`INFRA-275` in `docs/parity_ledger/infrastructure.yaml`,
`status: verified`) hardcodes the 3 legacy monolithic paths at lines 474-476:
```python
self._runs_file = repo_root / "agent-monitoring" / "runs.jsonl"
self._events_file = repo_root / "agent-monitoring" / "events.jsonl"
self._tools_file = repo_root / "agent-monitoring" / "tools.jsonl"
```
This consumer is explicitly Out of Scope for this ticket (children 3/4's job, per the ticket's own
Out of Scope section: "Updating any consumer... to read the new layout"). Its `_mtime()` helper
(lines 498-499: `p.stat().st_mtime if p.exists() else 0.0`) gracefully tolerates a missing file — **no
crash** — but the practical effect is that once this ticket's `git rm` retires all 3 legacy paths, the
Agent Ops Dashboard backend will silently read **zero** rows for `runs`/`events`/`tools` (all three
sources at once, not a partial degradation) until children 3/4 land and repoint `ingest.py` at the
new glob shape. This is meaningfully different from child 1's transient-gap precedent: child 1 left
the legacy files **present and readable** (just frozen, no new appends), so `ingest.py` kept working
correctly on stale-but-real data throughout its own transient gap. This ticket's `git rm` makes the
data **physically absent**, not merely stale — the dashboard's degradation window is a real
functional regression (empty dashboard), not a staleness window. See Risks and Open Questions.

## Mechanics / Engine Constraints

This ticket is pure tooling/observability infrastructure (`agent-monitoring/` migration script) — no
`docs/mechanics/` chapter or `docs/engine/` contract governs JSONL file layout or migration
mechanics. No Mechanics Bible or engine-contract constraint applies, consistent with child 1's own
investigation finding the same for the write-path cutover.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: three locations currently state, verbatim or near-verbatim, that
  the corresponding legacy physical shape "remains present in the working tree, frozen... until a
  future migration ticket folds it into the unified layout" — this ticket **is** that future
  migration ticket, so each of these three statements becomes stale/wrong the moment this ticket's
  `git rm` step lands (not merely incomplete — a reader would be told a file "remains present" that
  no longer exists). Confirmed present at these exact locations by direct read: (1) the
  `## agent-monitoring/runs.jsonl` section's write-path paragraph (~lines 111-120, "The historical
  monolithic `agent-monitoring/runs.jsonl` remains present in the working tree, frozen... until a
  future migration ticket folds it into the unified layout"); (2) the `## agent-monitoring/
  events.jsonl` section's equivalent paragraph (~lines 139-147, same phrasing pattern); (3) the
  `## agent-monitoring/tools.jsonl` section's equivalent paragraph (~lines 367-375, "The prior
  epic's `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards remain present in the working tree,
  frozen... until a future migration ticket folds them into the unified layout"). Each needs updating
  to state the migration is complete: the legacy path no longer exists in the working tree, full
  history remains recoverable via `git log --follow -- <path>`, matching the wording pattern the
  prior epic's own migration used for the `tools.jsonl` section when it landed (visible in the same
  file's existing `## agent-monitoring/tools.jsonl` section describing `TCK-20260902-MONITORING-
  SHARD-MIGRATION`'s retirement of the monolithic file). **This is not explicitly listed in the
  ticket's own Scope section** (unlike child 1, whose Scope text named `schema.md` directly) — flagged
  here because leaving these three sentences unedited would make the doc actively incorrect about
  physical state this same ticket changes, which is exactly the class of gap Investigate exists to
  catch even when a ticket's own Scope text doesn't enumerate it.

The `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` doc (an archived
design-rationale doc cited in the ticket's own Related Docs) is not required to change for this
ticket: it documents that this corpus's historical data-quality caveats (malformed/missing-timestamp
rows) are accepted-as-is design precedent, a still-true statement this migration's own route-only,
non-repairing approach continues to honor — nothing in this ticket's scope invalidates that
rationale.

`docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry (Agent Ops Dashboard backend) is not
required to change for this ticket either, on a narrower technical basis than the archive doc above:
this ticket does not modify `src/api/agent_ops_dashboard/ingest.py` itself (out of scope, children
3/4's job), and the entry's `v2_evidence` citations of `ingest.py`'s actual code remain accurate —
the code still does exactly what the entry describes. The *practical* consequence (the dashboard
going empty for these 3 sources once the legacy files are `git rm`'d) is a real, evidence-backed risk
this investigation flags below, but it is a functional-behavior risk of this ticket's own retirement
step landing ahead of children 3/4, not a doc-vs-code parity drift this ticket itself introduces into
`ingest.py`'s own code — updating `INFRA-275`'s status is more appropriately children 3/4's own
Parity-phase responsibility once they change `ingest.py`'s actual read path.

## Parity Ledger Overlap

None of the 8 parity ledger files (`substrate.yaml`, `combat_movement.yaml`, `strategic_cognition.yaml`,
`town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`,
`infrastructure.yaml`) has an entry whose `text` describes agent-monitoring physical file-layout
shape as its subject matter — `infrastructure.yaml`'s `INFRA-275` entry (discussed above) describes
the Agent Ops Dashboard backend's *implementation*, which cites but does not itself define the
legacy paths' existence, and is unaffected in its own `v2_evidence` accuracy by this ticket. No P0
entries are touched by this ticket.

## Prior Work

- `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/` — the direct reference implementation
  and reusable rename-aside/`write_lines()`-batch algorithm this ticket generalizes from 1 source to
  3, and the cross-worktree `git rm` merge-conflict runbook this ticket extends to all 3 retired
  paths (re-verified accurate above, not merely cited).
- `stored_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/` (child 1, hard prerequisite,
  landed 2026-09-03 per `tickets/done/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY.md`) —
  established the exact `agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl` target shape
  this migration must land historical data into, confirmed the write-time (not `start_ts`) bucketing
  decision for the *live* write path (a decision the current ticket's historical-migration script
  does **not** inherit — the ticket's own scope is explicit that historical `runs`/`events` rows
  bucket by their own `start_ts`/`ts` field, since write-time has no meaning for records already
  written in the past; these are two different, correctly-different bucketing rules for two
  different data sources, not an inconsistency), and fixed the `TOOLS_FILE` read-path bug in
  `record_events.py::compute_tool_stats()` that this ticket's migration does not touch.
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s original design
  rationale (shared `write_line`/`write_lines`, replacing 3 ad hoc lock implementations). Reused
  unmodified by this ticket, as the ticket's own scope requires ("`write_lines()`, reused
  unmodified").

## Risks and Open Questions

- **New, previously-unflagged risk: retiring all 3 legacy paths breaks the Agent Ops Dashboard's
  monitoring stats until children 3/4 land** (see Current Behavior's dedicated section above for the
  full evidence trail: `ingest.py:474-476` hardcodes the exact 3 paths this ticket `git rm`s;
  `_mtime()` tolerates absence without crashing, but the practical effect is the dashboard silently
  reads zero rows for `runs`/`events`/`tools` simultaneously). This is not this ticket's own
  implementation bug — it is a real, structural cross-ticket sequencing risk. **This investigation
  does not decide the resolution** (that's a planning/orchestration call, not an investigation one):
  options include (a) accept the gap as documented and explicitly recommend landing children 3/4
  promptly, mirroring the ticket's own existing "recommend the implementer land and merge this
  epic's PR promptly" guidance for the cross-worktree conflict-surface risk, or (b) resequence
  children 3/4 ahead of or immediately alongside this ticket's retirement step. Flagging as a real
  open question for Plan to resolve explicitly, not silently assume away.
- **The exact fallback-field priority list for `runs`/`events` bucketing is a real design decision,
  not fully pre-specified by the ticket** — this investigation supplies the concrete evidence (105/
  1,388 `runs.jsonl` records and 55/9,018 `events.jsonl` records missing their primary field, with
  the exact alternate-field distribution quantified above) but the implementer/planner must still
  decide and document the exact priority order (this investigation's recommendation: primary field →
  `timestamp` → other observed alternates → `UNKNOWN_WEEK_KEY`), per the ticket's own explicit
  framing ("Decide and document the exact fallback rule").
- **Case B (live-current-week merge) may or may not be exercised for `runs`/`events` depending on
  exactly when this ticket is implemented** — confirmed at investigation time only `tools.jsonl`
  exists under `agent-monitoring/data/2026-W36/`; `runs.jsonl`/`events.jsonl` do not yet exist there.
  If any `implement-ticket`/`implement-epic`/`create-tickets`/`simq-audit` run completes between now
  and this ticket's actual implementation, those files will exist and Case B will apply to them too.
  The generalized `write_week_bucket()` must handle this generically (it already does, via the
  `target_path.exists()` check) — do not write implementation code, tests, or a runbook comment that
  assumes `runs`/`events` are always Case A.
- **No acceptance criterion references behavior that doesn't exist yet** — every piece of source data
  (`runs.jsonl`, `events.jsonl`, all `tools/tools-*.jsonl` shards), every reference implementation
  function, and every reused test pattern cited by the ticket was confirmed present and accurate by
  direct read; no gap between the ticket's citations and reality was found beyond the two items
  flagged above (the dashboard risk, and the existing-test-conflict below).

## Anti-Drift Hazards

- **Do not re-parse `tools` shard content per-line for bucketing.** The prior epic's migration already
  did that work once, correctly, and the shard filenames already encode the correct week — treat
  `tools` as pure file relocation (whole-file content = one bucket, keyed by filename parse), not a
  second `json.loads()`-per-line bucketing pass. Per-line `json.loads()` is still required (and
  correct) for the zero-data-loss *verification* step (round-trip check), just not for *bucketing*.
- **Do not conflate the live write path's write-time bucketing decision (child 1) with this ticket's
  historical-record-field bucketing.** `runs.jsonl`'s live writer now buckets by write-time "now",
  confirmed and correctly ratified in child 1's plan.md Decision 5 — but this ticket's migration
  script buckets *historical* pre-cutover `runs.jsonl` rows by each row's own `start_ts` field
  (per this ticket's own scope text), because "now" has no meaning for a record written in the past.
  These are two independently-correct rules for two different code paths (live writer vs. one-time
  historical migration) — do not "fix" the migration script to use write-time-of-migration-run
  bucketing by analogy to child 1; that would silently misplace every historical record into
  whatever week the migration script happens to run in.
- **Update `tests/tools/test_migrate_tools_shards.py::test_gitattributes_no_longer_references_
  retired_tools_jsonl_path` (lines 283-286) as part of this ticket** — its current second assertion
  (`assert "agent-monitoring/tools/*.jsonl merge=union" in content`) directly contradicts this
  ticket's own required `.gitattributes` change (removing that exact line) and will fail once this
  ticket's `.gitattributes` edit lands. This is not a pre-existing bug to route around; it is this
  ticket's own scope correctly superseding a still-in-tree prior-epic test assertion — update it, do
  not delete or weaken it without replacement.
- **`tests/integrity/test_merge_union_gitattributes.py` has two additional assertions this ticket's
  own `.gitattributes` change will break** (confirmed by direct read, not previously cited in the
  ticket text): `test_gitattributes_lines_present_for_three_legacy_union_merge_paths` (lines 85-99)
  asserts `agent-monitoring/runs.jsonl merge=union` and `agent-monitoring/events.jsonl merge=union`
  are present; `test_gitattributes_line_present_for_shard_glob` (lines 102-111) asserts
  `agent-monitoring/tools/*.jsonl merge=union` is present. Both must be updated in this ticket's own
  diff (see Test Plan) — the git-level `test_concurrent_branch_appends_merge_without_conflict_
  markers` parametrized test (lines 42-83) is unaffected since it builds its own throwaway
  `.gitattributes` inline per test case and does not read the real repo's file.
- **Never truncate or directly overwrite a live shard file** — `write_week_bucket()`'s Case B path
  (rename-aside → combined write → reconcile trailing suffix → delete backup) is the only sanctioned
  mechanism; do not add a shortcut that writes historical lines with a plain append (`"a"` mode) after
  the fact, since that would place migrated rows *after* live rows, violating the AC's explicit
  chronological-order requirement.
- **Do not repair or normalize any malformed line's content** — route-only, exactly like the prior
  epic's migration; the 22 genuinely-timestamp-less `events.jsonl` records and any others routed to
  the fallback bucket must be persisted byte-for-byte unchanged, just relocated.
