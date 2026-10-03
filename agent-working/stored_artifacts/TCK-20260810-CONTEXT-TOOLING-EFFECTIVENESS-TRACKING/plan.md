---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
artifact_type: plan
tags: [agent-monitoring, observability, process-improvement]
---

# Implementation Plan — TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING

## Summary

This plan wires three new, evidence-backed sections into `generate_retro.py`'s recurring weekly
report and index: (1) a trended search/raw-investigation section reusing
`retrieval_baseline_metrics.py`'s existing `search_count`/`raw_investigation_count`/
`read_to_search_ratio` logic, relocated into `generate_retro.py` to resolve a real circular-import
constraint while keeping the two files' numbers identical (Design Decision 1); (2) a
compliant-vs-non-compliant `Read`-count correlation subsection inside
`compute_tool_safety_metrics`, computed from data that function already builds
(`pair_tool_rows`), never a second pass over `tools`; (3) a `parity_index.py`
`entry`/`impact`/`health` call-count section that honestly reports 0 today with a
path-anchored regex detector designed to activate automatically once a real call site lands. It
also extends `_update_index`'s signature (Design Decision 2) to thread per-week tools data into
`agent-monitoring/retro/index.md`'s trend table, and updates all three doc locations
(`README.md`, `schema.md`, `docs/guides/agent_monitoring.md`'s Report Sections table) plus the two
overlapping parity ledger entries (INFRA-292, INFRA-315) in place.

## Design Decisions

### Decision 1 — Circular-import resolution

**Verified fact:** `retrieval_baseline_metrics.py:21-27` currently does
`from generate_retro import (DEFAULT_TOOLS_FILE, _is_gate_fail, _load_runs_and_events,
_resolve_status, load_jsonl)`. `generate_retro.py` contains no import of
`retrieval_baseline_metrics` anywhere (confirmed by reading the full import block,
`generate_retro.py:11-41`, and by `retrieval_baseline_metrics.py` being the only file that
references `generate_retro` by import).

**Rejected approach:** having `generate_retro.py` add `from retrieval_baseline_metrics import
SEARCH_TOOL_NAMES, build_search_count_section, build_raw_investigation_count_section` while
`retrieval_baseline_metrics.py` keeps its existing `from generate_retro import ...` line would
create a genuine two-file cycle (`generate_retro` → `retrieval_baseline_metrics` →
`generate_retro`), which fails at import time (partially-initialized module) regardless of which
script is invoked first. This direction of import does **not** already exist and **would**
recreate the circular dependency — confirmed by direct read, not assumed.

**Chosen approach:** relocate `SEARCH_TOOL_NAMES`, `build_search_count_section`, and
`build_raw_investigation_count_section` (verbatim, including their inline rationale comments) from
`retrieval_baseline_metrics.py` into `generate_retro.py`. `retrieval_baseline_metrics.py` then adds
these three names to its **existing** `from generate_retro import (...)` statement — the same
import edge that already exists today, just carrying three more names. This adds zero new edges to
the import graph, so no cycle is created. `generate_retro.py` becomes the single source of truth
(satisfying the ticket's "reusing rather than duplicating" instruction: the logic exists in exactly
one place, both files consume the same function objects), and every existing consumer of
`retrieval_baseline_metrics.build_search_count_section` / `build_raw_investigation_count_section`
(its own `build_baseline_report`, its own test file, its CLI) keeps working unchanged, because
`from generate_retro import build_search_count_section` binds that name into
`retrieval_baseline_metrics`'s own module namespace — callers importing it from
`retrieval_baseline_metrics` see no difference.

### Decision 2 — `_update_index` signature change

**Verified fact:** `tests/tools/test_generate_retro.py:955-962`
(`test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`) asserts two
things about `generate_retro._update_index`: (a) its source does not contain the literal string
`"load_jsonl(RUNS_FILE)"` (i.e., it never bypasses the passed-in, already-filtered data to read the
raw jsonl file directly — the actual migration-completeness property from
`TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`), and (b) `list(inspect.signature(...).parameters) ==
["all_runs"]` (the arity as of that migration).

**Chosen approach:** extend the signature to `_update_index(all_runs, all_tools=None)` — an
additional **optional** parameter (default `None`, treated as `[]` inside the function), not a
required second positional. This preserves property (a) unconditionally (the new code paths still
only ever touch `all_tools`/`all_runs` as passed in, never `load_jsonl(RUNS_FILE)` or
`load_jsonl(DEFAULT_TOOLS_FILE)` directly inside `_update_index`), and only changes property (b) in
the deliberate, disclosed way the investigation flagged as necessary. The single real call site
(`main()`, `generate_retro.py:1318`) is updated to pass `_update_index(all_runs, all_tools)`. The
old signature-pinning test is **replaced**, not silently deleted, by
`test_update_index_signature_change_is_deliberate_and_documented` (per test_plan.md), which asserts
the new two-parameter signature explicitly and re-asserts the `"load_jsonl(RUNS_FILE)"` absence, so
the property the original test actually cared about (no direct-jsonl-read bypass) is preserved and
still tested, while the arity pin is consciously updated with a stated reason in this plan and in
the replacement test's own docstring.

### Additional resolved judgment call — `parity_index.py` section's "N" denominator

Per investigation.md's open question (AC3's literal "0/N call sites" wording), this plan adds one
small denominator field, `bash_rows_scanned` (total `tool == "Bash"` rows in the `tools` list
passed to the section, i.e., the population the detector regex was run against), rather than
inventing a corpus-wide concept not used elsewhere in this file family. This satisfies AC3's "0/N"
wording literally without a new denominator abstraction — see Step 5.

## Steps

### Step 1 — Relocate search/raw-investigation logic into `generate_retro.py`

**Files:** `tools/agent-monitoring/generate_retro.py`, `tools/agent-monitoring/retrieval_baseline_metrics.py`

**Change:** Move `SEARCH_TOOL_NAMES` (currently `retrieval_baseline_metrics.py:36-40`, including its
preceding rationale comment at lines 31-35), `build_search_count_section`
(`retrieval_baseline_metrics.py:65-88`), and `build_raw_investigation_count_section`
(`retrieval_baseline_metrics.py:170-210`, including its internal call to
`build_search_count_section(tools)` at line 181, unchanged) verbatim into `generate_retro.py`,
placed near the other `_is_*`/`compute_*` predicate helpers (after `_is_parity_index_build_call`,
`generate_retro.py:258-267`, before `compute_tool_safety_metrics`). In
`retrieval_baseline_metrics.py`, replace the removed definitions with three added names on the
existing import statement at line 21: `from generate_retro import (DEFAULT_TOOLS_FILE,
SEARCH_TOOL_NAMES, _is_gate_fail, _load_runs_and_events, _resolve_status,
build_raw_investigation_count_section, build_search_count_section, load_jsonl)`. Update
`retrieval_baseline_metrics.py`'s module docstring (lines 5-9) to list these three names among what
it composes from `generate_retro.py`, matching the docstring's own already-stated design intent
("compose existing functions from generate_retro.py... never reimplementing any of their logic").
`build_baseline_report` (`retrieval_baseline_metrics.py:213-224`) is untouched — it still calls
`build_search_count_section(tools)`/`build_raw_investigation_count_section(tools)`, now resolving
to the imported names instead of local definitions, with identical behavior.

**Do NOT touch:** `SEARCH_TOOL_NAMES`'s membership (`{mcp__knowledge-search__search_docs,
ToolSearch, WebSearch}`) or the Bash-exclusion rationale in either function's derivation string —
only the file each lives in changes, not the semantics (ticket Out of Scope). Do not touch
`classify_provenance`/`_assert_safe_output_path` imports or `build_legacy_schema_notes`,
`build_duration_section`, `build_gate_outcome_section`, `build_review_rework_section`,
`build_context_tokens_section` — all stay in `retrieval_baseline_metrics.py` unmodified. Do not
touch `generate_retro.py`'s own, deliberately-separate `_is_search_or_graphify_call`/`_is_grep_call`
predicates (`generate_retro.py:225-248`) — those remain a distinct vocabulary for the Tool Safety
Audit's search-before-grep compliance check, per that function's own docstring; this relocation
does not merge or reconcile the two vocabularies.

**Verify:** `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`,
`test_baseline_report_search_count_derivation_matches_stated_fields`,
`test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`,
`test_baseline_report_raw_investigation_count_ratio_never_silent_if_present`,
`test_baseline_report_raw_investigation_count_plausible_on_real_corpus`,
`test_baseline_report_tool_causes_zero_diff_on_real_corpus`,
`test_baseline_report_cli_runs_against_real_corpus_and_prints_json` (all existing, must pass
unchanged — proves the relocation is behavior-preserving).

---

### Step 2 — Wire the trended search/raw-investigation section into `generate()`

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:** Add `compute_search_investigation_trend(tools: list[dict]) -> dict` in
`generate_retro.py`, directly beside `compute_tool_safety_metrics`, returning
`{"search_count": build_search_count_section(tools), "raw_investigation_count":
build_raw_investigation_count_section(tools)}` — a thin wrapper calling the two relocated
functions from Step 1 by name, adding no new filtering logic of its own. In `generate()`
(`generate_retro.py:849-`), call `sit = compute_search_investigation_trend(tools or [])` alongside
the other `compute_*` calls (next to line 857's `tool_safety = compute_tool_safety_metrics(...)`),
and render a new `## Search & Investigation Effort` section, placed after the existing `## Shadow
vs. Baseline Retrieval Comparison` section and before `## Tool Safety Audit` (matching the existing
section ordering convention of retrieval-adjacent sections grouping together). Render two
subsections: `### Search Calls (Follow-Up Search Tooling)` showing `sit["search_count"]["total"]`,
and `### Raw Investigation (Read) Calls` showing `sit["raw_investigation_count"]["total"]` and
`sit["raw_investigation_count"]["read_to_search_ratio"]`. Gate the whole section on
`(sit["search_count"]["total"] + sit["raw_investigation_count"]["total"]) > 0`, omitted entirely
(not rendered empty) otherwise — matching the existing conditional-render convention shared by
Retrieval Quality, Shadow vs. Baseline, and Tool Safety Audit.

**Do NOT touch:** the `## Tool Safety Audit` section's existing rendering code
(`generate_retro.py:1230-1263`) or its exact literal strings — this new section is inserted before
it, not merged into it. Do not change `_FIXED_CORPUS_EVENTS`/`_FIXED_CORPUS_RUNS`
(`tests/tools/test_generate_retro.py:965-989`) or the frozen `_FIXED_CORPUS_EXPECTED_REPORT`
literal — that fixture carries no `tools` argument to `generate()` in the frozen-output test, so
the new section's `> 0` gate must keep it omitted there; do not weaken the gate to make it always
render, which would break that byte-identical-output guard.

**Verify:** `test_search_read_investigation_section_wired_into_generate_output`,
`test_search_read_investigation_section_never_silent_has_derivation`,
`test_search_read_investigation_section_reuses_retrieval_baseline_metrics_not_reimplemented` (this
last one, per test_plan.md, is implemented as an AST check on
`compute_search_investigation_trend`'s source asserting it calls `build_search_count_section` and
`build_raw_investigation_count_section` by name and contains no independent `for record in
tools:`/`SEARCH_TOOL_NAMES`-filtering loop of its own — proving Step 1's relocation is genuinely
reused here, not reimplemented a second time), plus
`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` (must still
pass, confirming the frozen fixture's report is unaffected).

---

### Step 3 — Thread `all_tools` into `_update_index` and add trend columns to `index.md`

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:** Apply Design Decision 2: change `_update_index(all_runs)`
(`generate_retro.py:1321-1343`) to `_update_index(all_runs, all_tools=None)`, with
`all_tools = all_tools or []` at the top of the function body. Inside the function, alongside the
existing `runs_by_week = defaultdict(list)` grouping (line 1329-1331), build a parallel
`tools_by_week` mapping using the **same run-id-to-week association already computed for runs**:
for each week key already produced by `runs_by_week`, derive `week_run_ids = {r.get("run_id") for r
in week_runs}` and filter `all_tools` to rows whose `run_id` is in that set — this mirrors the
exact filtering pattern `main()` already uses per-period at `generate_retro.py:1296` and `:1305`
(`tools = [t for t in all_tools if t.get("run_id") in run_ids]`), reused here rather than a new
mechanism. For the `"ALL"` row, use `all_tools` directly (mirrors the existing `name == "ALL"` →
`all_runs` special case at line 1337). Extend the table header from `"| Report | Runs | DONE | Gate
failures |"` to `"| Report | Runs | DONE | Gate failures | Search Calls | Read Calls |"`, computing
each new cell via `build_search_count_section(week_tools)["total"]` and
`build_raw_investigation_count_section(week_tools)["total"]` (the same Step-1-relocated functions —
no new counting logic). Update `main()`'s call site (`generate_retro.py:1318`) from
`_update_index(all_runs)` to `_update_index(all_runs, all_tools)`.

**Do NOT touch:** the existing `Runs`/`DONE`/`Gate failures` column computation
(`_resolve_status`-based, lines 1338-1340) — additive columns only. Do not change how `week_runs`
itself is computed (line 1337) or the `"ALL"` special-case branch's existing behavior for those
three columns.

**Verify:** `test_index_md_trends_search_and_read_investigation_columns`,
`test_update_index_signature_change_is_deliberate_and_documented` (replaces
`test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` — delete the old
test in the same commit that adds the new one, per Design Decision 2; do not leave both).

---

### Step 4 — Add the compliant-vs-non-compliant Read-count correlation subsection

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:** Inside `compute_tool_safety_metrics` (`generate_retro.py:769-846`), after
`pair_tool_rows` is fully built (line 800) and `per_pair_compliance` is computed (lines 802-813,
still tuple-keyed at that point, before the string-key rendering at line 836), add:
`pair_read_counts = {key: sum(1 for r in rows if r.get("tool") == "Read") for key, rows in
pair_tool_rows.items()}` — reusing `pair_tool_rows`, the dict this function already built at line
796-800 to hold every tool row per Investigate-phase pair; this is not a second scan of `tools`.
Split `pair_read_counts` by `per_pair_compliance[key]` into `compliant_reads` and
`non_compliant_reads` lists. For each non-empty list compute `statistics.median`/`statistics.mean`
(module already imported at `generate_retro.py:14`); for an empty list, report `None` for both
median and average rather than calling `statistics.median([])` (which raises) or fabricating `0`.
Add a new top-level key to the function's return dict (alongside `search_before_grep` and
`parity_write_safety`): `"read_count_correlation": {"compliant_group": {"count": len(
compliant_reads), "median": ..., "average": ...}, "non_compliant_group": {"count":
len(non_compliant_reads), "median": ..., "average": ...}, "derivation": "..."}`. In `generate()`,
inside the existing `if sbg["investigate_pair_count"]:` block (`generate_retro.py:1237`, the same
gate — correlation data is keyed off the same Investigate pairs, no new gate needed), after the
existing `### Parity Ledger Write-Safety` subsection (lines 1252-1263), add a third subsection
`### Read-Count Correlation (Search-Before-Grep Compliance)` rendering both groups' count/median/
average (using `"n/a"` for `None`).

**Do NOT touch:** `investigate_pairs` (lines 788-794) or the `first_search_idx`/`first_grep_idx`
compliance logic (lines 804-813) — read `pair_tool_rows`/`per_pair_compliance` as already computed,
do not re-derive either. Do not touch the existing `### Search-Before-Grep Compliance (Investigate
Phase)` or `### Parity Ledger Write-Safety` subsections' literal rendered text
(`generate_retro.py:1241-1263`) — the new subsection is appended after them, inside the same `if`
block, not interleaved.

**Verify:** `test_correlation_computes_read_count_per_investigate_pair`,
`test_correlation_median_average_split_by_compliance`,
`test_correlation_reuses_per_pair_compliance_not_a_second_pass` (AST guard — asserts the new code
does not contain a second `investigate_pairs = {`/`pair_tool_rows = defaultdict` derivation
anywhere in the file), `test_correlation_section_omitted_when_no_investigate_pairs`,
`test_correlation_handles_single_group_empty_gracefully`,
`test_correlation_real_corpus_produces_a_real_number`, plus the full existing
`compute_tool_safety_metrics` suite (`test_tool_safety_function_never_crashes_on_malformed_rows`,
`test_tool_safety_function_is_pure_no_file_io`, and all `search_before_grep`/
`parity_write_safety` tests at `tests/tools/test_generate_retro.py:1599-1801`) and
`test_new_section_rendered_in_generate_output_when_investigate_tool_data_present`/
`test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data` (existing, must pass
unmodified — this step only appends after their pinned assertions).

---

### Step 5 — Add the `parity_index.py` read-path call-count section

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:** Add `import re` to `generate_retro.py`'s import block (currently
`generate_retro.py:11-18`; `re` is not already imported). Add a module-level compiled pattern
`_PARITY_INDEX_READPATH_RE = re.compile(r'(?:^|/)parity_index\.py\s+(entry|impact|health)\b')` and
a predicate `_is_parity_index_readpath_call(tool_row)`, placed beside
`_is_parity_index_build_call` (`generate_retro.py:258-267`): return `False` unless
`tool_row.get("tool") == "Bash"` (mirrors the existing guard on `_is_parity_index_build_call`,
line 264), then `bool(_PARITY_INDEX_READPATH_RE.search(tool_row.get("input_summary") or ""))`. The
anchor `(?:^|/)` requires `parity_index.py` to be preceded by a path separator or string-start —
this is what excludes `tests/tools/test_parity_index.py` (the filename is `test_parity_index.py`,
so the character immediately before `parity_index.py` is `_`, not `/`, so the anchor never
matches), and requiring `entry|impact|health` as the token immediately following `parity_index.py`
excludes `--help`, `git log -- ... parity_index.py`, and `sed -n '1,60p' tools/parity_index.py`
(nothing meeting the subcommand shape follows the script path in any of those). Add
`compute_parity_index_readpath_call_count(tools: list[dict]) -> dict`, returning `{"count": len(
matches), "bash_rows_scanned": <count of tool == "Bash" rows in tools>, "examples": matches[:5],
"derivation": "..."}` where the derivation string states the 0-today finding and cites
`TCK-20260731-PARITY-READPATH-GATE`'s Gate A review. In `generate()`, call this function and render
a new `## Parity Index Read-Path Usage` section, placed after `## Tool Safety Audit` and before
`## Notes`. **Do not gate this section on any nonzero condition — always render it**, since "0
today" is itself the reportable finding (ticket Scope, explicit) and gating it out would prevent
AC3's "explicitly reports 0/N call sites today" from ever being visible in a report; this is a
deliberate, stated exception to the conditional-render convention every other section uses.

**Do NOT touch:** `_is_parity_index_build_call`/`_is_unsafe_parity_build_call`
(`generate_retro.py:258-276`) or `compute_tool_safety_metrics`'s `parity_write_safety` computation
(lines 818-826, 840-845) — this is a separate detector for a separate concern (read-path usage vs.
build-path write-safety); do not merge them or make one call the other. Do not wire
`_is_parity_index_readpath_call` into any actual `.claude/workflows/*.js` file or add any new call
site to `parity_index.py`'s `entry`/`impact`/`health` functions themselves anywhere in this
ticket's diff — this ticket counts calls, it does not add any (ticket Out of Scope, explicit).

**Verify:** `test_parity_index_readpath_call_count_zero_on_current_corpus`,
`test_parity_index_readpath_detection_matches_real_call_when_present`,
`test_parity_index_readpath_detection_false_positive_guards` (must cover all four corpus-observed
false-positive shapes: `python3 tools/parity_index.py --help`, `git log -- ... tools/parity_index.py`,
`pytest tests/tools/test_parity_index.py -k impact`, `sed -n '1,60p' tools/parity_index.py`),
`test_parity_index_readpath_section_never_silent_has_derivation`, plus the full
`tests/tools/test_parity_index.py`/`tests/tools/test_parity_ledger_writer.py` regression run
(unmodified — confirms no accidental edit to `parity_index.py` itself, since this step only reads
`tools.jsonl` rows about it).

---

### Step 6 — Update documentation

**Files:** `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
`docs/guides/agent_monitoring.md`

**Change:**
- `docs/agent-monitoring/README.md`'s `## Baseline Metrics Snapshot (one-off)` section (lines
  50-59) currently states its sections are "distinct from the recurring weekly retro above" without
  qualification. Add one sentence noting that as of this ticket, `search_count`'s and
  `raw_investigation_count`'s underlying logic now also lives in `generate_retro.py` (Step 1) and
  feeds a new recurring `## Search & Investigation Effort` report section and `index.md` trend
  columns — the one-off JSON snapshot cadence and the recurring Markdown cadence remain two
  different outputs (`retrieval_baseline_metrics.py` still never writes into
  `agent-monitoring/retro/`), but the *numbers* are now shared/reused, not the *cadence* merged
  (per investigation.md's Anti-Drift Hazards — do not conflate the two).
- `docs/agent-monitoring/schema.md`: add one sentence (in the `tools.jsonl` Fields or Known
  Limitations section, matching how `_is_parity_index_build_call`'s convention is not separately
  documented there either) describing the `_is_parity_index_readpath_call` path-anchored-regex
  detection convention at a high level, so a future reader knows this class of detector exists.
- `docs/guides/agent_monitoring.md`'s `## Report Sections` table (lines 55-70): add three new rows
  in the same prose-density/disclosure style as the existing `## Tool Safety Audit` row (line 70):
  one row for `## Search & Investigation Effort` (what the ratio means, that it's corpus-wide not
  per-run, cross-reference to `docs/parity_ledger/infrastructure.yaml`'s INFRA-292), one row noting
  the `### Read-Count Correlation` subsection's meaning (a real evidence signal, not a causal
  claim — explicitly state it answers "does compliance correlate with lower Read-effort," not
  "prove it causes it"), and one row for `## Parity Index Read-Path Usage` stating it is always
  rendered (unlike every other conditionally-gated section) and that 0 is the expected/correct
  value until a real call site lands.

**Do NOT touch:** any other row in the Report Sections table, or `docs/agent-monitoring/README.md`'s
other sections (`## Security Gate Firing Check` etc.) — additive documentation only.

**Verify:** No automated test covers doc prose directly; verified by re-reading the edited
sections against the actual rendered section headers/behavior from Steps 2, 4, 5 for consistency
(manual cross-check, part of this step, not a separate step).

---

### Step 7 — Amend overlapping parity ledger entries

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Per CLAUDE.md's Authoritative Mechanics Rule ("if logic changes, update... the parity
ledger entry... in the same session") and investigation.md's Parity Ledger Overlap findings, amend
both entries in place — append a descriptive clause to each `v2_evidence` field, following the
`TCK-20260804-EXPANSION-RATE-WIRING` → `INFRA-297` precedent (append, do not renumber, do not
create a new INFRA-3xx entry for an additive extension of the same module):
- **INFRA-292** (`docs/parity_ledger/infrastructure.yaml:6301-6317`): its `v2_evidence` cites exact
  line ranges in `retrieval_baseline_metrics.py` (`:21-29`, `:50-53`, `:56-88`, etc.) that shift once
  `SEARCH_TOOL_NAMES`/`build_search_count_section`/`build_raw_investigation_count_section` move out
  in Step 1. Append a clause noting the relocation into `generate_retro.py` (Design Decision 1),
  that `retrieval_baseline_metrics.py` now re-imports these names rather than defining them, and
  that behavior is unchanged (proven by Step 1's Verify tests staying green).
- **INFRA-315** (`docs/parity_ledger/infrastructure.yaml:7511-`): its `v2_evidence` describes
  `compute_tool_safety_metrics`'s return shape as exactly `{"search_before_grep": ...,
  "parity_write_safety": ...}`. Append a clause noting the Step 4 addition of a third top-level key,
  `"read_count_correlation"`, and the `generate()` rendering gaining a third subsection under `##
  Tool Safety Audit`.

Both entries stay `status: verified`, `priority: P2` — no status change, no new P0 gate
requirement (investigation.md confirms this).

**Do NOT touch:** any other `INFRA-*` entry, or the `status`/`priority`/`text` fields of INFRA-292/
INFRA-315 — `v2_evidence` amendment only, matching the cited precedent's scope.

**Verify:** `test_path` for both entries (`tests/tools/test_retrieval_baseline_metrics.py` and
`tests/tools/test_generate_retro.py` respectively) already covered by Steps 1-4's Verify lists;
this step adds no new test, only ledger-doc parity.

---

### Step 8 — Cross-cutting tests and full scoped regression

**Files:** `tests/tools/test_generate_retro.py`, `tests/tools/test_retrieval_baseline_metrics.py`

**Change:** Add the two cross-cutting tests from test_plan.md:
`test_all_new_sections_have_derivation_key` (table-driven over
`compute_search_investigation_trend`, the `read_count_correlation` sub-dict, and
`compute_parity_index_readpath_call_count`, asserting each carries a `"derivation"` key) and
`test_new_sections_never_write_any_file` (AST guard over the same three, mirroring
`test_tool_safety_function_is_pure_no_file_io`'s style — no `write_lines`/`write_line`/file-mode
strings/`EVENTS_FILE`/`RUNS_FILE`/`DEFAULT_TOOLS_FILE`/`load_jsonl` references in their source).
Then run the full scoped regression from test_plan.md's Scoped Pytest Commands section:
```
.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py tests/tools/test_retrieval_baseline_metrics.py -v
.venv/bin/python3 -m pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py -v
.venv/bin/python3 tools/agent-monitoring/generate_retro.py --all
```
Confirm all pass and the real `--all` run against the live corpus produces the three new sections
with real, non-fabricated numbers (satisfying AC1/AC2/AC3's "real corpus" requirement directly).

**Do NOT touch:** any other test file. Do not run the full `pytest tests/` suite (CLAUDE.md Testing
Rule) — scope stays exactly the three commands above.

**Verify:** All commands above exit 0; the generated `agent-monitoring/retro/RETRO-ALL.md` and
`agent-monitoring/retro/index.md` contain the three new sections/columns with real numbers
(inspected manually as part of this step, then the run artifacts are cleaned per CLAUDE.md's After
Work checklist — `data/runs/`/`reports/release_proof/` cleanup does not apply here since this is
`agent-monitoring/retro/` output, which is real, persisted tooling output, not throwaway run data;
do not delete `agent-monitoring/retro/RETRO-ALL.md` or `index.md` after this step — they are the
intended durable output of `generate_retro.py --all` and already exist as a committed artifact
class in this repo).

## Scope Guards

- Do not change `retrieval_baseline_metrics.py`'s `SEARCH_TOOL_NAMES` membership or its
  Bash-exclusion rationale — only its file location changes (Step 1), never its semantics.
- Do not wire `parity_index.py`'s `entry`/`impact`/`health` functions into any real
  `.claude/workflows/*.js` file, agent prompt, or skill — this ticket only counts existing calls
  via `tools.jsonl`, it adds zero new call sites (ticket Out of Scope, explicit).
- Do not backfill a correlation number for historical weeks predating this ticket's code landing —
  Step 4's correlation section computes live from whatever `tools`/`events` are passed to
  `generate()` at report-generation time; no retroactive fabrication.
- Do not touch `generate_retro.py`'s own `_is_search_or_graphify_call`/`_is_grep_call` predicates
  or their deliberate vocabulary divergence from `SEARCH_TOOL_NAMES` — Step 1's relocation moves
  `SEARCH_TOOL_NAMES` into the same file as these predicates but does not reconcile or merge the
  two vocabularies.
- Do not delete `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`
  silently — Step 3 explicitly replaces it with a test that preserves the original's
  no-direct-jsonl-read property while consciously updating the arity assertion.
- Do not modify `parity_index.py` itself anywhere in this ticket's diff (confirmed via Step 5's
  regression run of `tests/tools/test_parity_index.py`, which must stay byte-identical/passing).
- Do not renumber or create new `INFRA-3xx` parity ledger entries for this ticket's changes to
  already-ledgered modules — amend INFRA-292/INFRA-315 in place (Step 7).
- Do not add an `N`-denominator concept anywhere except the one narrowly-scoped
  `bash_rows_scanned` field in Step 5 — `search_count`/`raw_investigation_count`/the correlation
  section stay `total`-only, matching their existing shape.

## Dependency Map

- Step 1 must land before Step 2 (Step 2's `compute_search_investigation_trend` calls the
  relocated functions by name).
- Step 2 must land before Step 3 (Step 3's `index.md` columns call the same relocated functions;
  landing order avoids a transient state where `_update_index` references functions not yet
  available at module scope — in practice both are in the same file after Step 1, so this is a
  sequencing/testing convenience, not a hard technical blocker).
- Step 4 is independent of Steps 1-3 (touches `compute_tool_safety_metrics`, a different function
  entirely) — may be implemented in parallel or in any order relative to them.
- Step 5 is independent of Steps 1-4 (new predicate/function, no shared state with the others).
- Step 6 (docs) depends on Steps 2, 4, and 5 being complete — it documents their final section
  headers/behavior and would need rework if those steps' rendered text changes after Step 6 lands.
- Step 7 (parity ledger) depends on Steps 1 and 4 being complete — it cites their final line ranges
  and return-shape changes.
- Step 8 depends on all prior steps — it is the final consolidated regression pass.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — trended search/read-investigation section, real corpus, non-fabricated | Steps 1, 2, 3 | `test_search_read_investigation_section_wired_into_generate_output`, `test_index_md_trends_search_and_read_investigation_columns`, real `--all` run in Step 8 |
| AC2 — compliant-vs-non-compliant Read-count correlation, real `(run_id, seq)` pairs | Step 4 | `test_correlation_computes_read_count_per_investigate_pair`, `test_correlation_median_average_split_by_compliance`, `test_correlation_real_corpus_produces_a_real_number` |
| AC3 — `parity_index.py` call-count section, 0/N today, derivation, auto-activates | Step 5 | `test_parity_index_readpath_call_count_zero_on_current_corpus`, `test_parity_index_readpath_detection_matches_real_call_when_present`, `test_parity_index_readpath_detection_false_positive_guards` |
| AC4 — every new section has a `"derivation"` (or equivalent) string | Steps 2, 4, 5, 8 | `test_search_read_investigation_section_never_silent_has_derivation`, `test_parity_index_readpath_section_never_silent_has_derivation`, `test_all_new_sections_have_derivation_key` |
| AC5 — new tests mirror existing never-silent/derivation-matches/real-corpus-zero-diff patterns | Steps 1-5, 8 | Full new-test list in test_plan.md; existing `test_baseline_report_*`/`test_tool_safety_function_*` suites staying green in the same steps |
| AC6 — `docs/agent-monitoring/README.md`/`schema.md` updated | Step 6 (also updates `docs/guides/agent_monitoring.md`, the actual per-section documentation home discovered during investigation, beyond the ticket's own literal Related Docs list) | Manual cross-check (no automated doc test exists in this repo) |

## Anti-Drift Notes

- **Circular import**: the naive "have `generate_retro.py` import from
  `retrieval_baseline_metrics.py`" approach is unsafe and was rejected with evidence (Design
  Decision 1) — do not revert to it mid-implementation if Step 1's relocation feels like extra
  work; the relocation is the only resolution that adds zero new import edges.
- **`_update_index` arity**: the signature change is deliberate and disclosed (Design Decision 2)
  — do not "fix" the failing old signature-pin test by reverting the new parameter; replace the
  test per Step 3, and do not leave both the old and new signature-pinning tests in the file
  simultaneously (that would be a silent duplicate, not a conscious replacement).
- **Correlation section placement**: already resolved by evidence in investigation.md — it belongs
  in `generate_retro.py`'s `compute_tool_safety_metrics` (Step 4), not as new code in
  `retrieval_baseline_metrics.py`, because `per_pair_compliance`/`pair_tool_rows` are owned entirely
  by that function and `retrieval_baseline_metrics.py` has no per-pair concept at all. Do not
  reopen this as an undecided question during implementation.
- **`parity_index.py` detector false positives**: the regex anchor
  `(?:^|/)parity_index\.py\s+(entry|impact|health)\b` is specifically designed against the four
  real corpus-observed false-positive shapes (`--help`, `git log --`, `pytest -k`, `sed`) — if a
  fifth false-positive shape surfaces during Step 5's real-corpus test
  (`test_parity_index_readpath_call_count_zero_on_current_corpus` asserting `count == 0` today),
  tighten the regex rather than adding a denylist of literal strings, to keep the detector
  generalizable to the real call site this section is designed to pick up automatically once one
  exists.
- **Parity Index section always renders**: this is a deliberate, stated exception to the
  conditional-render convention (Step 5) — do not "fix" it to match the other sections' gating
  during review; 0 is itself the reportable finding per the ticket's explicit Scope text.
- **Do not conflate cadences**: `retrieval_baseline_metrics.py` remains a one-off/periodic snapshot
  tool that never writes into `agent-monitoring/retro/`; only the underlying *numbers* it prints are
  now shared with `generate_retro.py`'s recurring cadence (Step 1), not the cadence itself. Step 6's
  README update must preserve this distinction, not blur it.

## Deviations

Implementation followed all 8 steps as specified. Two points not fully anticipated by this plan's
text, both resolved without changing the plan's substance:

1. **Step 4's `read_count_correlation` key placement.** This plan's Step 4 prose describes adding
   the key "alongside `search_before_grep` and `parity_write_safety`" (i.e. top-level, a sibling of
   both), which is what was implemented — `compute_tool_safety_metrics` now returns
   `{"search_before_grep": ..., "parity_write_safety": ..., "read_count_correlation": ...}`. No
   deviation; flagged only because an earlier implementation draft briefly nested it inside
   `search_before_grep` before being corrected to match this plan's literal spec — the corrected,
   plan-conformant top-level placement is what shipped and is what INFRA-315's amended
   `v2_evidence` (Step 7) describes.

2. **Step 5's always-on section forces a frozen-fixture test update not explicitly called out by
   this plan.** Step 2's "Do NOT touch... the frozen `_FIXED_CORPUS_EXPECTED_REPORT` literal" note
   was written specifically about the `> 0`-gated `## Search & Investigation Effort` section (which
   is correctly still omitted on the zero-tools fixture, unaffected). It did not anticipate that
   Step 5's own explicit "always render, never gate" design (also in this plan, same section) would
   necessarily add new lines to that same frozen literal, since the Parity Index Read-Path Usage
   section is never omitted regardless of fixture data. This is a necessary, disclosed consequence
   of Step 5's own stated design, not a new decision — `_FIXED_CORPUS_EXPECTED_REPORT` in
   `test_generate_retro.py` was updated to include the new section's exact rendered text (0/0 Bash
   rows scanned on the fixture's empty `tools` list), and both tests asserting against that literal
   (`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`,
   `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture`) pass against the
   updated literal.

3. **Step 7's `write_entry()` call reformats the entire `infrastructure.yaml` shard, not just the
   two amended entries.** Not anticipated by this plan (or by the sibling
   `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` ticket that built the tool, whose own tests
   exercised it against small fixture files, not the real 2014-entry shard). `write_entry()`'s
   `yaml.safe_dump(entries, sort_keys=False)` call re-serializes every entry in the shard using
   PyYAML's default dumper style, which differs from the file's original hand-authored/
   previously-tooled style (block-scalar `>` folding, unicode escaping) — producing a large
   line-level `git diff` even though only `INFRA-292`/`INFRA-315` changed semantically. Verified via
   a direct `yaml.safe_load` comparison of `git show HEAD:...` against the post-write file that
   every entry other than those two (including `INFRA-331`, added earlier in this session by the
   sibling write-safety-tool ticket, unrelated to this diff) is byte-for-byte identical in parsed
   content — only YAML surface syntax changed. This is an inherent property of the now-mandated
   write path (used per this plan's explicit instruction to prefer `write_entry()` over raw
   Read/Edit), not a defect introduced by this ticket's own logic, and does not violate the Scope
   Guards' "do not touch any other INFRA-* entry" instruction in substance (no other entry's data
   changed) — flagged here as a real, previously-undetected side effect worth a future tooling
   fix (e.g. a targeted single-entry text patch instead of a full-file re-dump) rather than left
   undocumented.
