---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-CONSUMERS
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260902-MONITORING-SHARD-CONSUMERS

## Current Behavior

### Real on-disk state (confirmed)
`agent-monitoring/tools.jsonl` does not exist (`git rm`'d by child 2). `agent-monitoring/tools/`
contains 14 shard files: `tools-2026-W24.jsonl` through `tools-2026-W36.jsonl` (13 ISO-week shards,
zero-padded `%V`, e.g. `W24`) plus one fallback shard, `tools-unknown-week.jsonl`, for the single
historical row with no parseable `ts` (`tools/agent-monitoring/migrate_tools_shards.py:45,
UNKNOWN_WEEK_KEY = "unknown-week"` → `_shard_path_for_week()` at line 82-83 names it
`tools-unknown-week.jsonl`). Filename-lexical sort order (`"tools-2026-W24.jsonl" < ... <
"tools-2026-W36.jsonl" < "tools-unknown-week.jsonl"`) is chronological for the dated shards (digit
`'2'` < letter `'u'` in ASCII, and zero-padded `%V` sorts correctly within a year) with
`tools-unknown-week.jsonl` sorting last — acceptable since that shard's own rows are already
scrambled by construction (grab-bag of unparseable-`ts` lines from all over history), so its
position in file-processing order carries no chronological meaning either way.

### `tools/agent-monitoring/build_index.py`
- `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` — line 44, confirmed exact.
- `build(args)` (line 169-194): `tools_path = Path(args.tools_file)` (line 172) →
  `tools = load_jsonl(tools_path)` (line 177) → `_ingest_tools(conn, tools)` (line 188). Single-file
  read only; a glob is needed at this resolution step.
- `--tools-file` CLI arg (line 203) defaults to `str(DEFAULT_TOOLS_FILE)`.
- `load_jsonl` is imported from `validate.py`, not defined locally in this file — `validate.py`'s
  `load_jsonl(path)` returns `[]` if `path` doesn't exist (confirmed by reading `validate.py`), which
  is why running `build_index.py` unmodified today does not crash — it silently builds a `tools` table
  with **0 rows** instead. This is the actual mechanism of the "currently-broken interim state":
  no exception, just silent data loss.
- `test_build_index_never_touches_write_path_modules` (tests/tools/test_build_index.py:378-382)
  asserts the string `"writer"` never appears in `build_index.py`'s source — any glob-resolution
  helper added here must not import `tools/agent-monitoring/writer.py`. Not a problem: `Path.glob()`
  is stdlib, no `writer` import needed.
- **Existing `tests/tools/test_build_index.py` is NOT one of the 7 named xfailed tests and currently
  passes.** Its `_make_corpus()`/`_args()` helpers (lines 97-121) construct a single literal
  `tmp_path / "tools.jsonl"` file and pass it via `tools_file=str(paths["tools_path"])`. If the fix
  makes `args.tools_file`/`DEFAULT_TOOLS_FILE` mean "must be a directory to glob," these currently-
  green tests would need rewriting. **Recommended fix design (dual-mode, backward-compatible):**
  resolve `tools_path` via a small helper — if `tools_path.is_dir()`, `sorted(tools_path.glob("tools-*.jsonl"))`
  and concatenate `load_jsonl()` over each; otherwise (a literal file path, existing or not) fall back
  to `load_jsonl(tools_path)` unchanged. Then: (a) `DEFAULT_TOOLS_FILE` becomes
  `Path("agent-monitoring/tools")` (the shard directory) so the real CLI default globs correctly;
  (b) `test_build_index.py`'s existing single-file fixtures keep passing unmodified, since a literal
  file path still hits the fallback branch exactly as today; (c) the ticket's own required new AC2
  test (2+ shard files under a temp `agent-monitoring/tools/`-shaped dir) exercises the directory
  branch. This is the single design decision this ticket's Plan phase must ratify.

### `tools/agent-monitoring/generate_retro.py`
- `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` — line 57, confirmed exact (ticket
  says "line 57" — correct).
- `_index_is_stale(db_path)` (lines 70-81): loops `for source in (RUNS_FILE, EVENTS_FILE,
  DEFAULT_TOOLS_FILE): if source.exists() and source.stat().st_mtime > db_mtime: return True`. A
  single-file `.stat()` call; with `DEFAULT_TOOLS_FILE` now nonexistent as a file,
  `source.exists()` is `False` for the tools term forever, so this branch can never detect
  staleness caused by any shard write — permanently silent, reproducing exactly the bug class
  `TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS` was built to prevent, but now via the
  tools term specifically.
- `_load_runs_and_events()` (lines 84-120): on staleness, calls `build_index.build(SimpleNamespace(
  ..., tools_file=str(DEFAULT_TOOLS_FILE), ...))` (line 102) — this call site must pass whatever
  `build_index.build()` needs to resolve the full shard set (a directory path under the dual-mode
  design above, so no signature change needed on `build_index.build()`'s side beyond what's already
  planned there).
- **A third, previously-unlisted call site**: `main()` at line 2255, `all_tools =
  load_jsonl(DEFAULT_TOOLS_FILE)` — this feeds `_update_index()`'s per-week search/read/skill-
  invocation counts (`_update_index`, lines 2300-2340) AND is the direct source for the
  `test_correlation_real_corpus_produces_a_real_number` / `test_parity_index_readpath_call_count_matches_real_corpus_state`
  xfails (both call `generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)` directly — see
  below). This call site is not named in the ticket's Scope text but is squarely in-scope: it is a
  direct consumer of the same `DEFAULT_TOOLS_FILE`/`load_jsonl` pair the ticket already targets, and
  fixing `DEFAULT_TOOLS_FILE`'s value + `load_jsonl`'s dir-aware behavior (see Recommended Design
  below) fixes it automatically with zero code change at this call site.
- **Recommended design, mirroring `build_index.py`'s dual-mode approach**: make `load_jsonl(path)`
  itself dir-aware — `if path.is_dir(): return concatenated records from sorted(path.glob("tools-*.jsonl"))`,
  `else:` existing single-file behavior (including the existing `if not path.exists(): return []`
  branch, unchanged). `load_jsonl` is also used for `RUNS_FILE`/`EVENTS_FILE` (both remain single
  files, untouched) and is imported by `build_index.py` — no, wait: `build_index.py` imports
  `load_jsonl` from `validate.py`, a **separate, independent definition** (confirmed: `build_index.py`
  line 33-38 imports `load_jsonl` from `validate`, not from `generate_retro`). So `generate_retro.py`'s
  `load_jsonl` and `validate.py`'s `load_jsonl` are two distinct functions today and must each
  independently gain the same dir-aware branch (or one could be extracted to a shared location — see
  Risks). Making `load_jsonl` itself dir-aware, rather than only `DEFAULT_TOOLS_FILE`'s resolution,
  is what lets the untouched call site at line 2255 (`load_jsonl(DEFAULT_TOOLS_FILE)`) and
  `skill_usage_metric.py`'s `load_jsonl(DEFAULT_TOOLS_FILE)` (line 33) both pick up the fix for free
  by only repointing `DEFAULT_TOOLS_FILE` to `Path("agent-monitoring/tools")`.
- **`_index_is_stale()`'s fix**: the ticket's own wording — "a stale-but-not-newest shard must still
  correctly trigger a rebuild" — means the comparison cannot use only the chronologically-newest-
  named shard's mtime (a write to an *older* week's shard, e.g. a late correction, must also count).
  Correct design: for the tools source, compute `max(f.stat().st_mtime for f in
  sorted(tools_dir.glob("tools-*.jsonl")))` (or `DEFAULT_TOOLS_FILE.stat().st_mtime` unchanged if
  `DEFAULT_TOOLS_FILE` is a literal file, preserving dual-mode symmetry with `build_index.py`) and
  compare that max against `db_mtime`, exactly like the single-file case generalizes to "any member
  of this source is newer." **3 currently-passing tests monkeypatch `DEFAULT_TOOLS_FILE` to a single
  tmp file** (`test_generate_retro_builds_index_on_demand_when_missing`,
  `test_generate_retro_rebuilds_stale_index_not_just_missing_index`,
  `test_index_is_stale_false_when_index_newer_than_all_sources` — tests/tools/test_generate_retro.py
  lines 896-986) — the dual-mode (dir-or-file) design keeps these green unmodified, since
  monkeypatching a literal `tmp_path / "tools.jsonl"` file hits the non-dir fallback branch exactly
  as today.

### `tools/agent-monitoring/manifest.py` (NOT in the ticket's original Related Code Areas — real gap)
- `_FILES_BY_SOURCE = {"events.jsonl": "events", "runs.jsonl": "runs", "tools.jsonl": "tools"}`
  (lines 23-27) — confirmed hardcoded, exactly as child 2's implementer reported.
- `_scan_file(path, source)` (lines 30-59) does `with open(path, "rb") as f:` unconditionally — for
  the `"tools.jsonl"` entry this resolves to `agent_monitoring_dir / "tools.jsonl"`, which no longer
  exists → `FileNotFoundError`, uncaught. Confirmed by direct reading, not just trusting the prior
  report.
- `build_manifest(agent_monitoring_dir)` (lines 62-66) iterates `sorted(_FILES_BY_SOURCE.items())`
  calling `_scan_file` once per filename → 3 manifest records, one per physical file today.
- `capture_lines(agent_monitoring_dir)` (lines 69-83) has the identical unconditional
  `open(agent_monitoring_dir / filename, ...)` pattern for the same 3 filenames — same crash risk,
  though no test currently exercises it against the real corpus (grep found no test call site for
  `capture_lines` in `tests/tools/test_agent_monitoring_manifest.py`; it may only be used by another
  ticket's test file or be currently dead-in-tests — Plan should confirm before assuming it's covered).
- **`test_build_manifest_shape_against_real_corpus`** (the AC1 shape test) asserts
  `len(records) == 3` and `set(filenames) == {"events.jsonl", "runs.jsonl", "tools.jsonl"}` — this
  fixes the required output shape: **the fix must keep exactly 3 manifest records, with the "tools"
  entry remaining a single aggregate record still labeled `"tools.jsonl"`** (not one record per
  shard file). This is a hard constraint on the fix design, not a free choice.
- **Recommended fix**: change `_scan_file`'s call site for the `"tools"` source only — when
  `source == "tools"` (or filename == "tools.jsonl"), instead of opening one file, iterate
  `sorted((agent_monitoring_dir / "tools").glob("tools-*.jsonl"))` and stream each shard through the
  same per-line hashing/parsing loop `_scan_file` already does, accumulating one combined
  `parsed_ok`/`parse_errors`/`legacy_warning_count`/single running `hashlib.sha256()` across all
  shards in sorted order, and `byte_size` = sum of each shard's `path.stat().st_size`. Output the
  same `{"file": "tools.jsonl", ...}` record shape unchanged. `line_count` stays
  `parsed_ok + parse_errors` (already file-count-agnostic). Determinism requires the glob be
  explicitly sorted (`Path.glob()` does not guarantee sort order across all filesystems) — both for
  `test_manifest_cli_reproducible_byte_identical_across_two_runs` and
  `test_build_manifest_reproducible_byte_identical_direct_call` to keep passing once un-xfailed.
- `test_manifest_source_never_calls_full_file_read_methods` (line 93-106, **currently passing, NOT
  one of the 7 xfails**) is an AST guard banning `read_text`/`read_bytes`/`readlines`/`read` calls
  anywhere in `manifest.py`'s source — `Path.glob()` and `open(..., "rb")` + line iteration are both
  unaffected by this guard, so the streaming-per-line design above stays compliant automatically.
- `test_manifest_run_against_real_corpus_produces_zero_diff` (xfailed) uses
  `_content_hash_snapshot()` (test file lines 121-127), which hardcodes
  `_WATCHED_JSONL_FILES = ["events.jsonl", "runs.jsonl", "tools.jsonl"]` and does
  `path.read_bytes()` on `_REAL_AGENT_MONITORING_DIR / filename` for each — `agent-monitoring/tools.jsonl`
  doesn't exist, so this test-helper itself needs updating (not just marker removal) to watch the
  shard directory's files for the zero-mutation content-hash check to mean anything post-migration.
  **This is test-helper maintenance required to fix the test for real, not a marker-routing
  workaround** — flagged explicitly in Test Plan.

### `tools/agent-monitoring/skill_usage_metric.py` (NOT in the ticket's original Related Code Areas — real gap)
- `main()` (lines 28-41): `tools = load_jsonl(DEFAULT_TOOLS_FILE)` (line 33) — both names imported
  directly from `generate_retro.py` (line 24:
  `from generate_retro import DEFAULT_TOOLS_FILE, build_skill_usage_section, load_jsonl`). **No
  separate hardcoded path constant of its own** — this module has zero independent fix surface; it
  inherits whatever `generate_retro.DEFAULT_TOOLS_FILE`/`load_jsonl` resolve to. Confirmed by direct
  reading: the entire file is 46 lines, and the only reference to the retired path is this single
  import-and-call.
- `tests/tools/test_skill_usage_metric.py::test_reuses_generate_retro_loader_not_a_second_loader`
  (lines 47-50, **currently passing, NOT one of the 7 xfails**) asserts `load_jsonl` and
  `DEFAULT_TOOLS_FILE` are both imported by name — this pins the "reuse `generate_retro`'s loader
  pair, never reimplement" architecture, and constrains the fix to changing `generate_retro.py`'s
  definitions, not introducing a new/differently-named loader that `skill_usage_metric.py` would
  switch to. The dual-mode dir-aware `load_jsonl` design above satisfies this without any change to
  `skill_usage_metric.py` itself.
- `tests/tools/test_skill_usage_metric.py::test_cli_runs_against_real_corpus_and_prints_json` (line
  173, **currently passing, NOT xfailed**) and `::test_causes_zero_diff_on_real_corpus` (line 183,
  **currently passing, NOT xfailed**) both currently pass vacuously today: `load_jsonl(DEFAULT_TOOLS_FILE)`
  returns `[]` (file doesn't exist → `generate_retro.load_jsonl`'s existing `if not path.exists():
  return []` branch), so the CLI runs and produces an (empty but well-formed) report, and no mutation
  occurs. These will keep passing after the fix too (now returning a real, non-empty report) — no
  test change needed for these two, only stronger real coverage as a side effect.
- **`test_live_corpus_matches_independently_derived_counts`** (the xfailed one,
  test_skill_usage_metric.py:155-170): its own helper `_independently_derive_counts()` (lines
  133-152) does `_REAL_TOOLS_FILE = _REAL_AGENT_MONITORING_DIR / "tools.jsonl"` (module-level
  constant, line 23) then `with open(_REAL_TOOLS_FILE, encoding="utf-8") as f:` (line 138) — this
  raises `FileNotFoundError` today (confirmed: this is why the test is in the xfail list — it
  errors, not merely fails an assertion; `strict=True` xfail catches both). **Fixing this test for
  real requires updating `_independently_derive_counts()`/`_REAL_TOOLS_FILE` to iterate the sorted
  shard glob too** — again, real test-helper maintenance, not a marker-only fix.

### `tools/agent-monitoring/query.py` and `tools/agent-monitoring/validate.py` — confirmed no-op, ticket's claim holds
- `query.py`: only reference to any monitoring path is `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")`
  (line 25) and its use in `open_index()`/`main()`'s `--db-path` arg (lines 29, 145). Zero
  `tools.jsonl`/`tools_file` references anywhere in the file (grep confirmed, zero matches).
- `validate.py`: `compute_drift_report(runs, events)` (line 88), `compute_tool_count_drift_report(events,
  tools)` (line 151), `compute_multi_invocation_collision_report(events)` (line 197) are all pure
  functions taking already-loaded lists as parameters — none opens a file itself. `main()` reads
  `runs`/`events`/`tools` exclusively via `conn.execute("SELECT raw_json FROM tools ORDER BY id")`
  (line 54, alongside identical `runs`/`events` queries at lines 44/49) against the SQLite index
  built by `build_index.py`. The only literal path constant in the file is the same
  `DEFAULT_DB_PATH`. **Confirmed: both files are purely index-consumers, genuinely unaffected by the
  shard-file-layout change.** Fixing `build_index.py`'s glob resolution is sufficient — `validate.py`'s
  drift reports will automatically reflect the full sharded corpus with zero code changes to
  `validate.py` itself, once the `tools` table it reads from is correctly populated.
- `tests/tools/test_query.py` and `tests/tools/test_validate_agent_monitoring.py`: grepped for
  `tools.jsonl`/`tools_file`/`DEFAULT_TOOLS_FILE` — all matches in `test_validate_agent_monitoring.py`
  are either (a) assertion strings checking `validate.py`'s own report text, which literally says
  "tools.jsonl row count" as a display label (unaffected — that's `validate.py`'s own output
  wording, not a file read), or (b) `tools` lists passed in-memory as test fixtures. No real
  file-read dependency on the old path in either test file. AC's "query.py's existing test suite
  still passes unmodified" and "validate.py's drift-report functions produce identical results" are
  both expected to hold with zero changes to either file.

### `tools/gate_checks/done_checker_static.py` — confirmed, zero references
Grepped directly: zero matches for `tools.jsonl`/`tools_file`/`agent-monitoring/tools` anywhere in
the file. Ticket's Out-of-Scope claim is accurate; no action needed, AC7 ("zero diff in this
ticket") should hold trivially by not touching the file.

## Mechanics / Engine Constraints

None — this is pure agent-orchestration/monitoring tooling (`docs/agent-monitoring/`), not a
simulation-behavior change. No `src/` file is touched, no Mechanics Bible chapter or engine contract
governs this reporting/index-building tooling's semantics (same category as the entire INFRA-28x
through INFRA-333 run of parity ledger entries covering this subsystem's prior migrations).

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: line 30's staleness-check description
  ("`(any of runs.jsonl/events.jsonl/tools.jsonl has a newer mtime than the index —`") describes a
  single-file-per-source mtime comparison that will no longer be accurate for the `tools` source once
  `_index_is_stale()` is extended to compare against the newest-by-mtime shard across
  `agent-monitoring/tools/tools-*.jsonl`; must be reworded to describe the multi-shard comparison.
- `docs/agent-monitoring/README.md`: the "What It Captures" bullets (lines 19-21) cite `(tools.jsonl)`
  in the same itemized, parenthetical-filename style used for `runs.jsonl`/`events.jsonl` (which
  remain literal single files) — this groups a now-multi-file data family with two still-single
  files under identical framing, which is exactly the misleading physical-file impression the
  ticket's Scope flags. Line 54's "same `runs.jsonl`/`events.jsonl`/`tools.jsonl` sources" phrase has
  the same issue. The Navigation table entry (line 148, "Full field reference for runs.jsonl,
  events.jsonl, and tools.jsonl") is the ticket's own named example.
- `docs/ai/system_overview.md` §6 (lines 229-244): explicitly states "Agent activity is recorded in
  3 append-only JSONL files under `agent-monitoring/`" and lists `tools.jsonl` as the third sibling
  file with a physical-record description ("one record per tool call, keyed to events via
  `run_id`+`seq`...") identical in style to the two genuinely-still-single-file entries above it.
  This is the most literal "3 files" claim of any doc in scope and must be reworded to describe 2
  single files plus the `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard family.
- `docs/parity_ledger/infrastructure.yaml` (INFRA-291 entry, line ~6360-6405): its `v2_evidence`
  field literally quotes `` `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` `` (line
  6390) as evidence for `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`'s claims about
  `generate_retro.py`'s data-loading layer. Once this ticket repoints `DEFAULT_TOOLS_FILE`, this
  quoted literal becomes factually stale (CLAUDE.md's Authoritative Mechanics Rule: "If logic
  changes, update the corresponding doc AND the parity ledger entry... in the same session" — this
  is exactly that case, even though the underlying migration this entry documents is otherwise
  unaffected). Recommend adding a short addendum/date-stamped note to `v2_evidence` rather than
  rewriting the whole entry, mirroring the pattern used elsewhere in this file for post-hoc
  corrections (e.g. INFRA-290's own note about a "genuine, narrow, non-gating output divergence
  found").

The following were considered and explicitly excluded:

`docs/guides/agent_monitoring.md` is not required to change for this ticket: its 2 references to
`tools.jsonl` (line 218, "lets `post_tool_hook.py` attribute `tools.jsonl` rows to a run"; line 262,
"`compute_tool_safety_metrics()` sees only the orchestrating run's own `tools.jsonl` rows") are both
logical/conceptual references to "tool-call data rows," matching the retained historical/logical
naming convention `docs/agent-monitoring/schema.md` itself keeps under its own `## agent-monitoring/tools.jsonl`
heading (schema.md line 337) even after fully documenting the new sharded physical layout in the
same section. Neither line in `agent_monitoring.md` makes a claim about physical single-file
storage location — grepped for "single file"/"one physical" framing across all 3 in-scope docs plus
this one; zero matches anywhere. No change needed.

`agent-monitoring/README.md` (repo-root, path `agent-monitoring/README.md` — distinct from
`docs/agent-monitoring/README.md`) has the identical stale "single tools.jsonl" framing at lines 13,
42, and a `### tools.jsonl` heading at line 44, but this path is outside the ticket's own Related
Docs / Scope list (which names only `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
`docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`), and it does not start with `docs/`
so it cannot be represented as a Format 1 machine-checked bullet under `check_docs_to_update_coverage`'s
`docs/[^\`]+` path regex regardless. Flagging this here as a real, closely-related, same-shaped gap
for Plan to decide whether to fold in as an easy bonus fix — it is not part of this investigation's
required doc list and is deliberately not written as a bullet.

`docs/parity_ledger/infrastructure.yaml`'s INFRA-333 entry (skill-usage retro-tracking) also
mentions `main() loads all_tools = load_jsonl(DEFAULT_TOOLS_FILE) once` (line 8738) but only
describes the call *shape*, not the literal path value — that description remains accurate
unchanged after the fix (same call site, same import names, only the underlying value/behavior of
`DEFAULT_TOOLS_FILE`/`load_jsonl` changes). No update needed for this entry.

## Parity Ledger Overlap

- `INFRA-291` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P2`) —
  directly touched; see Docs Requiring Update above. Not P0, no gating `test_path` re-run required
  by ledger rules, but should still be corrected per the Authoritative Mechanics Rule.
- `INFRA-289`/`INFRA-290` (`query.py`/`validate.py`'s original SQLite-index migrations, both
  `verified`/`P2`) — checked, not affected; neither cites a literal `tools.jsonl` path value that
  changes.
- `INFRA-333` (skill-usage retro-tracking wiring, `verified`/`P2`) — checked, not affected (see
  above).
- No `P0` entries in `docs/parity_ledger/infrastructure.yaml` were found referencing
  `tools.jsonl`/`DEFAULT_TOOLS_FILE`/`build_index.py`/`manifest.py`/`skill_usage_metric.py` in the
  grepped ranges — all touched entries are `P2`, so none carries the "P0 requires a passing
  `test_path`" hard requirement from CLAUDE.md.

## Prior Work

- `stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/`,
  `.../TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE/`, `.../TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE/`,
  `.../TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE/` — the original 4-ticket batch that built
  `build_index.py` and migrated `query.py`/`validate.py`/`generate_retro.py` to the derived SQLite
  index. This ticket extends that batch's file-*resolution* layer only; the index schema, the
  normalization functions (`_resolve_status`, `_record_is_complete`, etc.), and the query-layer
  design are all explicitly out of scope and confirmed untouched by this investigation.
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/` (child 2) — the one-time migration
  script and its verification report; `tools/agent-monitoring/migrate_tools_shards.py` (read in
  full) is the ground truth for shard filename conventions, the `tools-unknown-week.jsonl` fallback
  name, and the cross-worktree `git rm` merge-conflict runbook referenced in this ticket's own
  Request Summary.
- `tickets/done/TCK-20260902-MONITORING-SHARD-MIGRATION.md` — confirms child 2 has landed on this
  branch (14 real shard files present on disk, `agent-monitoring/tools.jsonl` absent), satisfying
  this ticket's hard prerequisite.

## Risks and Open Questions

1. **Scope-gap decision needed from Plan (flagged, not assumed):** `manifest.py` and
   `skill_usage_metric.py` are not in the ticket's original Scope/Related Code Areas text but are
   directly responsible for 5 of the 7 xfailed tests (4 in `test_agent_monitoring_manifest.py`, 1 in
   `test_skill_usage_metric.py`). **Recommendation: bring both files formally into this ticket's
   Scope** — the fix for `skill_usage_metric.py` is zero-code (it fully inherits `generate_retro.py`'s
   fix), and the fix for `manifest.py` is a small, self-contained change to `_scan_file`'s tools-source
   branch. There is no plausible way to satisfy "all 7 xfail markers removed, all 7 passing for
   real" (this ticket's own stated primary success condition) without touching `manifest.py`.
2. **`load_jsonl` duplication**: `generate_retro.py` and `validate.py` each define their own,
   independent `load_jsonl(path)` function (`build_index.py` imports `validate.py`'s copy;
   `skill_usage_metric.py` imports `generate_retro.py`'s copy). Both need the identical dir-aware
   glob branch added, in two places, or one needs to become the canonical definition the other
   imports from. This ticket's Out of Scope explicitly forbids "re-deriving... any other
   normalization logic already centralized" — adding the *same* small dir-glob branch to both
   existing functions (not restructuring which file owns canonical logic) is the minimal-risk
   choice; consolidating the two `load_jsonl`s into one shared definition is a larger refactor this
   ticket should not attempt.
3. **Glob determinism**: `Path.glob()` does not guarantee sorted output across all filesystems/
   Python versions. Every call site that globs `tools-*.jsonl` (in `build_index.py`,
   `generate_retro.py`'s `load_jsonl`, and `manifest.py`'s `_scan_file`) must explicitly wrap the
   glob in `sorted(...)` — required both for the ticket's own "sorted in filename order (chronological
   ISO-week order)" requirement and for the reproducibility tests
   (`test_manifest_cli_reproducible_byte_identical_across_two_runs`,
   `test_build_manifest_reproducible_byte_identical_direct_call`, and `build_index.py`'s own
   `test_build_twice_produces_same_row_counts`).
4. **`manifest.py`'s `capture_lines()` function** has the same unconditional single-file-open crash
   risk as `_scan_file` but no test currently exercises it against the real corpus in
   `test_agent_monitoring_manifest.py` — Plan should confirm whether any other test file (or a
   future consumer) calls it before deciding whether it needs the identical dir-aware fix in this
   ticket or can be deferred; leaving it broken-but-untested would be a latent gap, not a resolved
   one.
5. **`_content_hash_snapshot()`/`_WATCHED_JSONL_FILES` in `test_agent_monitoring_manifest.py`, and
   `_independently_derive_counts()`/`_REAL_TOOLS_FILE` in `test_skill_usage_metric.py`**, are test-
   helper code that itself hardcodes the retired single-file path and will raise/mis-hash if not
   updated alongside the marker removal. This is legitimate test-helper maintenance required to make
   the underlying test assertion meaningful again post-migration — explicitly not the same thing as
   editing a test's assertion to dodge a gate (CLAUDE.md's Gate Integrity rule), since the assertion
   itself is unchanged; only the fixture-construction helper that feeds it needs to track the new
   physical layout.

## Anti-Drift Hazards

- **Do not widen the glob beyond `tools-*.jsonl`.** The shard directory is exclusively tool-call
  shard data; a broader glob (e.g. `*.jsonl`) risks silently picking up an unrelated future file
  dropped in the same directory. `tools-*.jsonl` is correct and intentionally matches
  `tools-unknown-week.jsonl` too (a real, must-include data shard, not an edge case to filter out).
- **Do not filter out or special-case `tools-unknown-week.jsonl`.** It is real historical data (one
  confirmed row with unparseable `ts`), not a sentinel/error file — every build/manifest/skill-usage
  computation must include it exactly like any other shard.
- **Do not change `_ingest_tools()`'s off-schema-record skip logic** in `build_index.py` (lines
  140-166) — that's pure normalization logic, explicitly out of scope per the ticket's Out of Scope
  section ("Re-deriving `_resolve_status()`... or any other normalization logic already centralized").
  The fix here is file *resolution* only.
- **Do not let the `manifest.py` fix change the 3-record output shape.** The temptation to emit one
  manifest record per shard file must be resisted — `test_build_manifest_shape_against_real_corpus`
  hard-requires exactly 3 records with `filenames == sorted(filenames)` and the literal filename set
  `{"events.jsonl", "runs.jsonl", "tools.jsonl"}`. Aggregate across shards into one logical
  `"tools.jsonl"` record.
- **Do not touch `tools/gate_checks/done_checker_static.py`** — confirmed zero references, explicitly
  out of scope; touching it would fail this ticket's own AC7 ("zero diff in this ticket").
- **Do not touch `runs.jsonl`/`events.jsonl` reading logic** in any of the 4 primary files — those
  remain single physical files, completely unaffected by this migration; any change there is scope
  creep per the ticket's Out of Scope section.
- **Do not silently widen `_index_is_stale()`'s comparison to the shard directory's own mtime**
  instead of `max()` over each shard file's individual mtime. On many filesystems a directory's
  mtime updates when a file is *created or removed* inside it but not necessarily when an *existing*
  file inside it is appended to — using the directory's own mtime as a shortcut could silently miss
  exactly the "append to an existing, non-newest-by-name shard" staleness case the ticket's AC
  explicitly requires catching.
