---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
artifact_type: investigation
tags: [agent-monitoring, observability, process-improvement]
---

# Investigation — TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING

## Current Behavior

**`tools/agent-monitoring/retrieval_baseline_metrics.py`** (one-off/periodic snapshot script,
explicitly *not* part of the recurring weekly retro per its own module docstring, lines 5-13):
- `SEARCH_TOOL_NAMES` (lines 36-40): `frozenset({"mcp__knowledge-search__search_docs",
  "ToolSearch", "WebSearch"})`.
- `build_search_count_section(tools)` (lines 65-88): counts `tools.jsonl` rows whose `tool` is in
  `SEARCH_TOOL_NAMES`, grouped `per_run` (`None` → literal `"unattributed"`), plus `total`. Ships a
  `derivation` string.
- `build_raw_investigation_count_section(tools)` (lines 170-210): counts rows with `tool == "Read"`,
  same `per_run`/`total` shape, plus `read_to_search_ratio` = `round(total / search_total, 4)` when
  `search_total > 0`, else an explicit `"undefined: zero search_count.total in corpus..."` string
  (never a fabricated/divide-by-zero value). Real last-observed corpus values per the ticket:
  `raw_investigation_count.total = 18594`, `search_count.total = 1924`, `ratio = 9.66`.
- `build_baseline_report(runs, events, tools)` (lines 213-224) assembles both sections plus five
  others into one JSON report, printed to stdout by `main()`; never writes into `agent-monitoring/`.
- `load_all_sources()` (lines 50-53) composes `generate_retro._load_runs_and_events()` +
  `generate_retro.load_jsonl(DEFAULT_TOOLS_FILE)` — this module imports FROM `generate_retro.py`
  (line 21: `from generate_retro import (DEFAULT_TOOLS_FILE, _is_gate_fail,
  _load_runs_and_events, _resolve_status, load_jsonl)`), never the reverse. This import direction is
  load-bearing — see Risks below.

**`tools/agent-monitoring/generate_retro.py`** (recurring weekly retro; `generate()` is the sole
Markdown-rendering consumer):
- `_is_search_or_graphify_call()` / `_is_grep_call()` (lines 225-248): generate_retro.py's **own**,
  deliberately separate search/grep vocabulary — the docstring at line 227-229 states explicitly:
  "Deliberately independent of retrieval_baseline_metrics.py's SEARCH_TOOL_NAMES (a different
  vocabulary for a different metric) — do not import or reuse that constant here." This is an
  existing, intentional divergence between the two files' search-tool definitions (`SEARCH_TOOL_NAMES`
  = `{search_docs, ToolSearch, WebSearch}` vs. `_is_search_or_graphify_call` = `{search_docs, Bash
  with input_summary.startswith("graphify")}`).
- `compute_tool_safety_metrics(events, tools)` (lines 769-846): builds `investigate_pairs` from
  `events` where `_normalize_phase(e) == "Investigate"`, then `pair_tool_rows` (a `defaultdict(list)`
  keyed by `(run_id, seq)`, line 796-800) holding every `tools.jsonl` row belonging to that
  Investigate-phase pair. `per_pair_compliance` (lines 802-813) is computed from `pair_tool_rows` —
  **this dict already has, per pair, every tool row including any `Read` rows; nothing new needs to
  be loaded to compute a per-pair Read count.** Returns `{"search_before_grep": {...,
  "per_pair_compliance": {"run_id::seq": bool, ...}}, "parity_write_safety": {...}}`.
- `generate(runs, events, label, week_str=None, tickets_root=None, tools=None)` (lines 849-1271):
  calls `compute_retro_metrics`, `compute_retrieval_metrics`, `compute_shadow_baseline_comparison`,
  `compute_tool_safety_metrics`, then renders each section's Markdown, gated by an `if` on that
  section's own nonzero-data condition (e.g. line 1237 `if sbg["investigate_pair_count"]:`) so an
  empty period omits the section entirely rather than rendering it empty — this is the established
  convention every new section must follow.
- `main()` (lines 1274-1319): loads `all_runs, all_events = _load_runs_and_events()` and
  `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` (unconditionally, regardless of `--days`/`--week`/
  `--all`), filters `runs`/`events`/`tools` to the period, calls `generate(...)`, writes
  `agent-monitoring/retro/RETRO-<label>.md`, then calls `_update_index(all_runs)`.
- `_update_index(all_runs)` (lines 1321-1343): **this is the actual "trended report-over-report"
  mechanism already in the codebase** — it re-derives each historical `RETRO-<week>.md` row's
  `Runs`/`DONE`/`Gate failures` counts fresh from `all_runs` (grouped by `iso_week`), not from any
  persisted per-report state, and writes `agent-monitoring/retro/index.md`. There is no other
  "trend" concept anywhere in this file (confirmed: no `trend`/`Trend` string exists in
  `generate_retro.py`, `docs/agent-monitoring/README.md`, or `docs/agent-monitoring/schema.md`).
  **`_update_index` currently only takes `all_runs`, not `all_tools`** — extending index.md with
  search/read-investigation columns requires threading `all_tools` (or a pre-filtered-by-week
  tools view) into this function.
- **Hard signature guard**: `tests/tools/test_generate_retro.py::test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`
  (line 955) asserts `list(inspect.signature(generate_retro._update_index).parameters) ==
  ["all_runs"]`. Adding an `all_tools` parameter for trending will break this test — a deliberate,
  justified update (the test's own purpose, per its name/docstring context, was pinning the
  SQLite-index-migration's call-site completeness, not permanently freezing the function's arity
  forever), not a "route around the gate" edit — but it must be updated consciously with a stated
  reason, not silently.

**`tools/parity_index.py`** (`entry`/`impact`/`health` read path, Gate A reviewed GO):
- `entry(entry_id, db_path=None)`, `impact(changed_path=None, test_path=None, symbol=None,
  db_path=None)`, `health(subsystem=None, priority=None, db_path=None)` (lines 550-708) — all
  read-only, `_connect_readonly` (mode=ro). `main()`'s CLI subcommands are `build`, `entry`,
  `impact`, `health`, `check-staleness` (lines 711-780).
- **Confirmed zero real call sites for `entry`/`impact`/`health`, verified two ways:**
  1. Source grep across the whole repo (`grep -rn "parity_index\.\(entry\|impact\|health\)"`) finds
     only `tools/parity_index.py` itself and test files (`tests/tools/test_gate_a_readpath_review.py`,
     which imports `parity_index as pi` to test the module directly, not to call it from a real
     workflow site).
  2. `tools/parity_ledger_writer.py` (landed this session by
     `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`) line 45: `from parity_index import
     DEFAULT_LEDGER_DIR, DEFAULT_DB_PATH, build` — **imports `build` only, not `entry`/`impact`/
     `health`.** That ticket's own Implementation Notes (tickets/done/) confirm it calls
     `parity_index.build()` in-process after a validated write, plus a separate visible
     `python3 tools/parity_index.py build` Bash call in `parity-updater.md` — the write-safety
     concern, not the read path. This does **not** count as an entry/impact/health call site.
  3. Direct scan of the real `agent-monitoring/tools.jsonl` (106,441 rows; 139 rows mention
     `parity_index.py` at all) shows every `Bash` invocation of `parity_index.py` is `build`,
     `build --help`, `--help`, or a `pytest`/`git`/`sed`/`head` command referencing the file's own
     source — **zero rows invoke `entry`, `impact`, or `health` as a subcommand.**
- **Ticket premise confirmed accurate: 0/N real call sites today**, where N should be defined as
  the denominator this section's own detection pattern scans (see Anti-Drift Hazards).

## Mechanics / Engine Constraints

None. This ticket touches only `tools/agent-monitoring/` observability tooling and
`tools/parity_index.py`'s already-existing read path — no `src/` simulation code, no Mechanics
Bible chapter, no engine contract governs agent-monitoring tooling itself (consistent with the
sibling `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s identical finding).

## Docs Requiring Update

- `docs/agent-monitoring/README.md`: the "Baseline Metrics Snapshot (one-off)" section (lines
  50-59) currently states `retrieval_baseline_metrics.py` sections are `distinct from the recurring
  weekly retro above` — once `search_count`/`raw_investigation_count`/`read_to_search_ratio` are
  wired into `generate_retro.py`'s recurring report, this line becomes inaccurate/incomplete and
  needs a cross-reference distinguishing the one-off JSON snapshot from the new recurring
  Markdown-rendered trend.
- `docs/agent-monitoring/schema.md`: no existing "recurring report sections" listing lives here
  (confirmed by grepping section headers) — likely does not need a structural change, but the
  `tools.jsonl` "Fields" section (or "Known Limitations") should get one sentence if the
  `parity_index.py` call-count detection pattern introduces any new documented field-matching
  convention (mirrors how `_is_parity_index_build_call`'s convention is not separately documented
  in schema.md either — judgment call for Plan, not a hard requirement).
- `docs/guides/agent_monitoring.md`: **this is the actual "Report Sections" table** (line 55-70)
  that documents every recurring retro section row-by-row, including the existing precedent this
  ticket extends (`## Tool Safety Audit` row, line 70, `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`). It
  is **not listed in the ticket's own "Related Docs" section** — this is a real gap in the ticket's
  own scoping, not a judgment call to skip. Three new/extended rows are needed here: the wired
  search/read-investigation trend section, the compliant-vs-non-compliant correlation section, and
  the `parity_index.py` call-count section — following the exact prose-density and disclosure
  convention every existing row already uses (e.g. the Tool Safety Audit row explicitly states "Both
  counts should read 0 — a nonzero count is a real ... violation, not noise").

If none apply: N/A — the above three do apply; this ticket is not a "None." case.

## Parity Ledger Overlap

- **INFRA-292** (`docs/parity_ledger/infrastructure.yaml`, line 6301, `status: verified`,
  `priority: P2`, `test_path: tests/tools/test_retrieval_baseline_metrics.py`) — covers
  `retrieval_baseline_metrics.py`'s report sections including `search_count`/
  `raw_investigation_count`. This ticket reuses (not modifies) that module's existing section
  functions, but if Plan's chosen resolution to the circular-import constraint (see Risks) touches
  `retrieval_baseline_metrics.py`'s file structure at all, INFRA-292's `v2_evidence` needs an
  in-place amendment — following the exact precedent `TCK-20260804-EXPANSION-RATE-WIRING` used to
  amend `INFRA-297` (append a descriptive clause, do not renumber, do not create a new INFRA-3xx
  entry for a minor additive extension of the same module).
- **INFRA-315** (`docs/parity_ledger/infrastructure.yaml`, line 7511, `status: verified`,
  `priority: P2`, `test_path: tests/tools/test_generate_retro.py`) — covers
  `compute_tool_safety_metrics`/`parity_write_safety` in `generate_retro.py`. This ticket's
  correlation section is designed to reuse `compute_tool_safety_metrics`'s `per_pair_compliance`
  (per the ticket's own Scope) — if implemented as an extension of that function's return shape (vs.
  a separate new function), INFRA-315's `v2_evidence` needs the same kind of in-place amendment.
  Note: `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`'s own Finalize pass explicitly checked
  INFRA-315 for staleness and found it NOT stale, "since its v2_evidence cites only
  tools/agent-monitoring/generate_retro.py, which this ticket does not modify" — this ticket *does*
  modify `generate_retro.py`, so that exemption does not carry over here.
- No P0 entries touched by this ticket's scope (both INFRA-292 and INFRA-315 are P2) — no
  passing-`test_path` gate requirement beyond the existing scoped pytest regression surface.
- No parity ledger entry exists anywhere for `tools/parity_index.py`'s `entry`/`impact`/`health`
  functions themselves (grepped all 9 `docs/parity_ledger/*.yaml` shards for `parity_index` —
  only `infrastructure.yaml` mentions it, and only for the `build`/write-safety concern). This is
  expected and correct: this ticket only counts calls into that path, it does not change or newly
  document the path's own behavior, so no new/updated parity ledger entry is required for
  `parity_index.py` itself.

## Prior Work

- `TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC` (DONE) — built `raw_investigation_count`/
  `read_to_search_ratio` in `retrieval_baseline_metrics.py`, explicitly deferring recurring-report
  wiring: `stored_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/` confirms the
  never-silent/derivation-matches-fields test conventions this ticket's new tests must mirror
  (`test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent`,
  `test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`,
  `test_baseline_report_raw_investigation_count_ratio_never_silent_if_present`,
  `test_baseline_report_raw_investigation_count_plausible_on_real_corpus`).
- `TCK-20260804-EXPANSION-RATE-WIRING` (DONE) — the closest sibling "wiring" precedent by name, but
  its actual shape (optional never-fabricated kwarg pass-through on 3 `wrap_*()` emitters) is a
  different kind of wiring than this ticket needs (report-section rendering, not event-schema
  plumbing). Its real transferable precedents are: (1) the in-place parity-ledger-entry amendment
  convention (used above for INFRA-292/INFRA-315), and (2) explicit acknowledgment when a wired
  metric's real-world value stays at a "boring" baseline (there, `expansion_rate` stays 0.0%; here,
  the `parity_index.py` call-count section is expected to stay at 0/N until a future ticket adds a
  real call site — same "honest, disclosed, not a bug" framing applies).
- `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT` (referenced via `compute_tool_safety_metrics`'s own
  docstring/tests, not separately re-read as a done ticket here since its code is the direct object
  of extension) — established the `## Tool Safety Audit` section's conditional-render pattern
  (`if sbg["investigate_pair_count"]:`) and the "state a derivation, never a silent number"
  convention this ticket's new sections must follow identically.
- `TCK-20260731-PARITY-READPATH-GATE` (DONE) — produced `docs/ai/parity_readpath_gate_a_decision.md`
  (Gate A: GO, 66.7% vs 4.8% recall). Confirms `entry`/`impact`/`health` were reviewed and approved
  for eventual use, but explicitly scoped read-path *wiring* to a future Phase-3 ticket — consistent
  with this ticket's Out of Scope ("Wiring parity_index.py's read path into any actual workflow call
  site... is a future, separately-scoped Phase-3 ticket").
- `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` (DONE, this session) — confirmed via direct read of
  its Implementation Notes that it added exactly one new `parity_index.py` call site
  (`build`, in-process), not `entry`/`impact`/`health`. Does not change this ticket's "0 real call
  sites" premise.
- `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (DONE, this session) — closed a real
  search-before-grep gap for hand-orchestrated (non-`investigator`-agent) Investigate-phase work,
  landing a fix in `.claude/skills/implement-ticket/SKILL.md` step 2, plus a new
  `## Investigate-Step Search-Before-Grep Callout` section in `docs/guides/agent_monitoring.md`
  (immediately before `## Makefile Targets`). This is the exact fix whose real-world effect this
  ticket's correlation section is designed to make visible — its own AC3 says as much verbatim. It
  also already establishes the precedent of editing `docs/guides/agent_monitoring.md` for a
  Tool-Safety-Audit-adjacent change, reinforcing the Docs Requiring Update finding above.

## Risks and Open Questions

- **Blocking architectural constraint — circular import direction (not previously identified by
  the ticket's own Assumptions section, which only flagged the correlation section's placement).**
  `retrieval_baseline_metrics.py` imports FROM `generate_retro.py` (`from generate_retro import
  DEFAULT_TOOLS_FILE, _is_gate_fail, _load_runs_and_events, _resolve_status, load_jsonl`). If
  `generate_retro.py` were to `from retrieval_baseline_metrics import build_search_count_section,
  build_raw_investigation_count_section, SEARCH_TOOL_NAMES` to satisfy AC1's "wire ... into the
  recurring report ... reusing rather than duplicating retrieval_baseline_metrics.py's logic," this
  creates a circular import (`generate_retro` → `retrieval_baseline_metrics` → `generate_retro`),
  which fails at import time. Plan must explicitly choose one of two resolutions (not decided here,
  per the Uncertainty Rule):
  1. Extract `SEARCH_TOOL_NAMES`/`build_search_count_section`/`build_raw_investigation_count_section`
     into `generate_retro.py` itself (or a new shared module both files import from), with
     `retrieval_baseline_metrics.py` importing them back — matching the direction its own docstring
     already establishes ("compose existing functions from generate_retro.py... never reimplementing
     any of their logic").
  2. Keep both files' vocabularies genuinely separate (as `_is_search_or_graphify_call`/
     `_is_grep_call` already are, by explicit design, from `SEARCH_TOOL_NAMES`) and have
     `generate_retro.py` compute its own trend section using its own existing
     `_is_search_or_graphify_call` predicate over `tools`, accepting that the two "search count"
     numbers (one-off snapshot vs. recurring trend) may diverge slightly in vocabulary — this
     directly conflicts with AC1's literal "reusing rather than duplicating" instruction, so is the
     less-preferred option unless Plan finds a concrete reason option 1 is unsafe.
  Either resolution is a legitimate, disclosed choice — but this is a real blocking design decision
  for Plan to make explicitly and justify, not paper over.
- **`_update_index`'s hard signature guard test** (`test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`,
  pins params to exactly `["all_runs"]`) must be deliberately updated if the trended index.md table
  requires per-week tools data — a conscious, justified test change, not a silent bypass per
  CLAUDE.md's rule against editing artifacts/tests merely to make a gate pass. The investigation
  does not resolve whether index.md is even the right home for the trend (vs. a per-report-only
  section with no index.md column) — Plan must decide and state which "trended report-over-report"
  means concretely (index.md table columns, matching the existing DONE/Gate-failures precedent, is
  the closest existing mechanism and is recommended, but is not mandated here).
- **The correlation section's placement is resolved by evidence, contrary to the ticket's own
  "not decided here" framing**: `per_pair_compliance` is computed and owned entirely inside
  `compute_tool_safety_metrics()` in `generate_retro.py`; `retrieval_baseline_metrics.py` has no
  per-pair concept at all (it only ever computes corpus-wide totals). Per the ticket's own
  instruction ("follow whichever file already owns the relevant per-pair data"), the correlation
  section belongs in `generate_retro.py`, either as an extension of `compute_tool_safety_metrics`'s
  return dict or a new sibling function in the same file that accepts `pair_tool_rows`/
  `per_pair_compliance` — not as new code in `retrieval_baseline_metrics.py`. This should not be
  reopened as an undecided question in Plan.
- **`parity_index.py` call-count detection pattern design is not yet specified** — mirroring
  `_is_parity_index_build_call`'s Bash-input_summary-substring pattern (`"parity_index.py" in
  summary and "build" in summary`) for `entry`/`impact`/`health` risks false-negatives/positives
  from word-boundary issues (e.g. a `--help` call, a `git log -- ... parity_index.py` call, or a
  `pytest tests/tools/test_parity_index.py -k impact` call, all of which currently exist in the
  corpus per the direct tools.jsonl scan above) if the pattern isn't scoped carefully to a real
  subcommand invocation shape. Plan must specify the exact matching rule and back it with tests
  covering the corpus's actual false-positive-prone patterns already observed (headers, `--help`,
  `git`/`pytest`/`sed` commands mentioning the filename).
- **Denominator (`N`) for "0/N call sites" is undefined by the ticket text** — AC3 says "explicitly
  reports 0/N call sites today" without specifying what N counts. Plan must define N concretely
  (candidates: total `tools.jsonl` rows scanned in the period, total Bash rows scanned, or omit N
  entirely and just report a `count` + `derivation`, matching `build_search_count_section`'s
  existing `total`-only shape with no implicit denominator). Recommend matching the existing
  `search_count`/`raw_investigation_count` shape (a plain `total` count with a `derivation` string)
  rather than inventing a new N-denominator concept not used anywhere else in this file family,
  unless Plan has a concrete reason a denominator adds real value here.

## Anti-Drift Hazards

- Do not let the new `parity_index.py` call-count section's "activates automatically once a real
  call site exists" requirement (ticket Scope, explicit) turn into a hardcoded `if count == 0:
  "not implemented"` branch — the section must be a genuine live count over `tools.jsonl`'s current
  data at report-generation time, exactly like every other section in this file, so a future ticket
  adding a real call site needs zero code change here to start reporting a nonzero number.
- Do not silently revisit `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design or
  Bash-exclusion rationale while resolving the circular-import constraint above — the ticket's Out
  of Scope explicitly protects that design's *semantics* (which tool names count, why Bash is
  excluded); only the *file location* of the constant/functions is open for Plan's circular-import
  resolution, not the underlying logic.
- Do not compute the correlation section's per-pair Read count from a fresh, separate scan of
  `tools` — reuse `pair_tool_rows` (already grouped per `(run_id, seq)` inside
  `compute_tool_safety_metrics`) rather than re-filtering `tools` by `(run_id, seq)` a second time,
  which would be exactly the kind of "fourth loader" duplication
  `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader` guards against in spirit for
  the sibling file.
- Do not conflate `retrieval_baseline_metrics.py`'s one-off/periodic JSON snapshot cadence with
  `generate_retro.py`'s recurring weekly Markdown cadence when writing the README.md update — the
  existing docs are careful to keep these two conceptually distinct ("distinct from the recurring
  weekly retro cadence... does not write into agent-monitoring/retro/"); the new wiring makes the
  *numbers* shared/reused, not the *cadence* merged into one tool.
- Every new section must follow the existing conditional-render convention (omit the whole section
  when the period's underlying data is empty, never render an empty/zero-value section header) —
  confirmed as the pattern for Retrieval Quality, Shadow vs. Baseline, and Tool Safety Audit; a
  new section that always renders (even at 0/0) would be an inconsistency, unless Plan explicitly
  decides the `parity_index.py` call-count section should always render (defensible, since "0 today"
  is itself the reportable finding, unlike e.g. Tool Safety Audit which has nothing meaningful to
  say about a period with zero Investigate-phase data at all) — state the decision either way.
