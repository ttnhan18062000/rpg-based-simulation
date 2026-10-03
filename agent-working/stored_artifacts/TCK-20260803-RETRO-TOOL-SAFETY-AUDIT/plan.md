---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-RETRO-TOOL-SAFETY-AUDIT
artifact_type: plan
tags: [agent-monitoring, retro]
---

# Implementation Plan — TCK-20260803-RETRO-TOOL-SAFETY-AUDIT

## Summary

Add one new pure function, `compute_tool_safety_metrics(events, tools)`, to
`tools/agent-monitoring/generate_retro.py` that computes two independent audits over
`agent-monitoring/tools.jsonl`: (1) search-before-grep hard-rule compliance, scoped to
`(run_id, seq)` pairs that a real `Investigate`-phase event in `events.jsonl` identifies, and
(2) `parity_index.py` write-safety (zero-tolerance count of `Edit`/`Write` calls into
`docs/parity_ledger/*.yaml` and zero-tolerance count of `parity_index.py build` invocations that
default to or explicitly target the real repo `parity-index/parity.db` path instead of a scratch
path). The function takes already-loaded data and performs no I/O itself, mirroring
`compute_retrieval_metrics`/`compute_shadow_baseline_comparison`. `tools.jsonl` loading is threaded
through `main()` (via the already-defined `load_jsonl(DEFAULT_TOOLS_FILE)`, no new import needed)
and passed into `generate()` through a new trailing, defaulted `tools=None` parameter, so no
existing `generate(runs, events, label)`-style call site breaks. A new conditionally-rendered
"## Tool Safety Audit" section is appended to `generate()`'s Markdown output (placed after "## Shadow
vs. Baseline Retrieval Comparison" and before "## Notes"), gated on whether any Investigate-phase
`(run_id, seq)` pair has tool-call data in the period — omitted entirely, never rendered empty, when
there is none. Finally, `docs/guides/agent_monitoring.md`'s Report Sections table gets a new row and
`docs/parity_ledger/infrastructure.yaml` gets a new `INFRA-315` entry, following the file's 4/5
majority convention for new `generate_retro.py` report sections.

**Design decisions (resolving investigation.md's flagged items; not genuinely blocking — decided
here per this ticket's own scope):**

1. **Parity ledger entry — add it.** Follow the majority (4/5) convention: INFRA-283, INFRA-284,
   INFRA-298, INFRA-300 all added an `infrastructure.yaml` entry for a new `generate_retro.py`
   report section; only INFRA-`TCK-20260708-RETRO-TAG-BREAKDOWN` skipped it. This ticket's change is
   the same shape (new pure `compute_*` function + new conditionally-rendered section), and the
   Authoritative Mechanics Rule's parity clause is about logic changes generally, not simulation
   mechanics specifically — this file already treats agent-orchestration tooling changes as
   in-scope for entries (INFRA-281 through INFRA-314 are all non-simulation tooling). Add
   `INFRA-315`.
2. **`generate()` signature — append a new trailing, defaulted parameter.** Add `tools=None` as the
   *last* parameter of `generate(runs, events, label, week_str=None, tickets_root=None, tools=None)`.
   This is strictly additive: every existing call site (`generate(runs, events, label)`,
   `generate(runs, events, label, week_str)`, any keyword-arg variant) keeps working unchanged.
   Inside `generate()`, default `tools` to `[]` when `None` before calling
   `compute_tool_safety_metrics(events, tools)`. `main()`'s own call site becomes
   `generate(runs, events, label, week_str, tools=tools)` (keyword, since `tickets_root` sits
   between `week_str` and `tools` positionally and `main()` never passes `tickets_root` today).
3. **Investigate-phase identification source — `events.jsonl`'s `phase` field, not
   `tools.jsonl`'s own `phase` field.** `tools.jsonl` rows do carry their own `phase` field
   (confirmed in `docs/agent-monitoring/schema.md`), but that field is `null` for records predating
   `TCK-20260719-LIVE-PHASE-AGENT-LABEL` and is a redundant, less-authoritative copy of the same
   information. `events.jsonl`'s `phase` field (via the existing `_normalize_phase(e)` helper,
   which already folds casing variants per `TCK-20260719-PHASE-AGENT-CASE-FOLD`) is the
   authoritative phase-transition record and matches the ticket's own Scope text ("cross-referenced
   against `events.jsonl`'s `phase` field the same way `compute_shadow_baseline_comparison` already
   cross-references event data"). Build the `(run_id, seq)` key set from `events.jsonl` only; filter
   `tools.jsonl` rows by membership in that key set. This has the side benefit of automatically,
   correctly excluding `tools.jsonl` rows with `seq: null` or `seq <= 0` (shadow-packet rows) without
   any special-case code, since `events.jsonl`'s `seq` is documented non-nullable and `>= 1` for real
   phase events — a row that can't match a key is simply skipped, never crashes.

## Steps

### Step 1 — Add `compute_tool_safety_metrics()` skeleton + search-before-grep sub-check
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:**
- Add two small module-level pure helper predicates, placed near `_normalize_phase`/`_normalize_agent`
  (around line 207, after `_normalize_agent`):
  ```python
  def _is_search_or_graphify_call(tool_row):
      """True if this tools.jsonl row satisfies the CLAUDE.md search-before-grep hard rule:
      mcp__knowledge-search__search_docs, or a Bash call invoking graphify. Deliberately
      independent of retrieval_baseline_metrics.py's SEARCH_TOOL_NAMES (a different vocabulary
      for a different metric) — do not import or reuse that constant here."""
      tool = tool_row.get("tool")
      if tool == "mcp__knowledge-search__search_docs":
          return True
      if tool == "Bash":
          summary = tool_row.get("input_summary") or ""
          return summary.startswith("graphify")
      return False


  def _is_grep_call(tool_row):
      """True if this tools.jsonl row is a Grep tool call or a Bash call whose input_summary
      contains 'grep'."""
      tool = tool_row.get("tool")
      if tool == "Grep":
          return True
      if tool == "Bash":
          summary = tool_row.get("input_summary") or ""
          return "grep" in summary
      return False
  ```
- Add `compute_tool_safety_metrics(events: list[dict], tools: list[dict]) -> dict` after
  `compute_shadow_baseline_comparison` (after line 696). Build the Investigate-phase key set from
  `events`, group `tools` rows by `(run_id, seq)` preserving `tools.jsonl`'s natural append-order
  (no re-sort needed — the file is written in call order), and compute per-pair compliance:
  ```python
  def compute_tool_safety_metrics(events: list[dict], tools: list[dict]) -> dict:
      investigate_pairs = {
          (e.get("run_id"), e.get("seq"))
          for e in events
          if _normalize_phase(e) == "Investigate"
          and e.get("run_id") is not None
          and e.get("seq") is not None
      }

      pair_tool_rows = defaultdict(list)
      for row in tools:
          key = (row.get("run_id"), row.get("seq"))
          if key in investigate_pairs:
              pair_tool_rows[key].append(row)

      per_pair_compliance = {}
      for key, rows in pair_tool_rows.items():
          first_search_idx = next(
              (i for i, r in enumerate(rows) if _is_search_or_graphify_call(r)), None
          )
          first_grep_idx = next((i for i, r in enumerate(rows) if _is_grep_call(r)), None)
          if first_grep_idx is None:
              per_pair_compliance[key] = True
          elif first_search_idx is None:
              per_pair_compliance[key] = False
          else:
              per_pair_compliance[key] = first_search_idx < first_grep_idx

      investigate_pair_count = len(per_pair_compliance)
      compliant_count = sum(1 for v in per_pair_compliance.values() if v)

      return {
          "search_before_grep": {
              "investigate_pair_count": investigate_pair_count,
              "compliant_count": compliant_count,
              "compliance_rate": (
                  compliant_count / investigate_pair_count if investigate_pair_count else None
              ),
              "per_pair_compliance": {
                  f"{run_id}::{seq}": compliant
                  for (run_id, seq), compliant in per_pair_compliance.items()
              },
          },
          "parity_write_safety": {
              "parity_ledger_yaml_write_count": 0,
              "unsafe_parity_build_count": 0,
              "parity_ledger_yaml_write_examples": [],
              "unsafe_parity_build_examples": [],
          },
      }
  ```
  (`parity_write_safety` is stubbed to zero here; Step 2 fills it in.)
**Do NOT touch:** `compute_retrieval_metrics`, `compute_shadow_baseline_comparison`,
`retrieval_baseline_metrics.py`'s `SEARCH_TOOL_NAMES` (do not import or reference it — it is a
different vocabulary for a different metric per the investigation's Anti-Drift Hazard). Do not add
any `load_jsonl`/file-open call inside this function.
**Verify:** New tests in `tests/tools/test_generate_retro.py`:
`test_search_before_grep_compliance_true_when_search_docs_precedes_grep`,
`test_search_before_grep_compliance_true_when_graphify_bash_call_precedes_grep`,
`test_search_before_grep_compliance_false_when_grep_tool_precedes_search_docs`,
`test_search_before_grep_compliance_false_when_bash_grep_precedes_search_docs`,
`test_search_before_grep_compliance_rate_aggregated_across_multiple_investigate_pairs`,
`test_search_before_grep_ignores_non_investigate_phase_tool_calls`.

### Step 2 — Fill in parity write-safety sub-check
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:** Add two more helper predicates next to the Step 1 helpers:
```python
def _is_parity_ledger_yaml_write(tool_row):
    if tool_row.get("tool") not in ("Edit", "Write"):
        return False
    summary = tool_row.get("input_summary") or ""
    return "docs/parity_ledger/" in summary and ".yaml" in summary


def _is_unsafe_parity_build_call(tool_row):
    if tool_row.get("tool") != "Bash":
        return False
    summary = tool_row.get("input_summary") or ""
    if "parity_index.py" not in summary or "build" not in summary:
        return False
    if "--db-path" not in summary:
        return True  # no override -> defaults to the real repo parity-index/parity.db path
    return "parity-index/parity.db" in summary
```
Replace the Step 1 stub inside `compute_tool_safety_metrics` with the real computation:
```python
    parity_yaml_writes = [r for r in tools if _is_parity_ledger_yaml_write(r)]
    unsafe_parity_builds = [r for r in tools if _is_unsafe_parity_build_call(r)]

    ...
        "parity_write_safety": {
            "parity_ledger_yaml_write_count": len(parity_yaml_writes),
            "unsafe_parity_build_count": len(unsafe_parity_builds),
            "parity_ledger_yaml_write_examples": parity_yaml_writes[:5],
            "unsafe_parity_build_examples": unsafe_parity_builds[:5],
        },
```
Note this sub-check is **not** scoped to Investigate-phase pairs — it scans the whole `tools`
argument as passed in, per the ticket's Scope text ("across the whole period").
**Do NOT touch:** the `search_before_grep` block from Step 1. Do not widen either predicate beyond
`docs/parity_ledger/*.yaml` / `parity_index.py build` — no `.gitignore`, `Makefile`, or other
protected-path check (explicitly Out of Scope).
**Verify:** `test_parity_write_safety_zero_violations_on_clean_fixture`,
`test_parity_write_safety_detects_edit_targeting_parity_ledger_yaml`,
`test_parity_write_safety_detects_build_targeting_real_repo_path`.

### Step 3 — Graceful-degradation and purity guard tests
**Files:** `tests/tools/test_generate_retro.py`
**Change:** No production code change — add the two architecture/robustness tests against the
now-complete `compute_tool_safety_metrics`:
- `test_tool_safety_function_never_crashes_on_malformed_rows`: fixture with rows missing
  `input_summary`, missing `seq` (`None`), rows with no matching Investigate-phase
  `(run_id, seq)`, and `seq <= 0` (shadow-packet) rows — assert no exception and that these rows
  are excluded from `per_pair_compliance`/violation counts, not silently miscounted.
- `test_tool_safety_function_is_pure_no_file_io`: mirrors
  `test_function_is_read_only_no_write_call_or_file_open_in_write_mode`
  (`tests/tools/test_generate_retro.py:1136`) via `inspect.getsource(compute_tool_safety_metrics)`,
  asserting absence of `write_lines(`, `write_line(`, `"w")`/`'w')`, `"a")`/`'a')`, `EVENTS_FILE`,
  `RUNS_FILE`, `DEFAULT_TOOLS_FILE`, `load_jsonl`, `DEFAULT_DB_PATH`.
**Do NOT touch:** production code in this step.
**Verify:** the two tests named above pass.

### Step 4 — Thread `tools.jsonl` loading through `main()` into `generate()`
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:**
- Change `generate()`'s signature (line 699) to
  `def generate(runs, events, label, week_str=None, tickets_root=None, tools=None):` and, at the
  top of the function body (after the docstring, before `metrics = compute_retro_metrics(...)`),
  add `tools = tools or []` then
  `tool_safety = compute_tool_safety_metrics(events, tools)`.
- In `main()` (line 1088+): after `all_runs, all_events = _load_runs_and_events()` (line 1095), add
  `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` (both `load_jsonl` and `DEFAULT_TOOLS_FILE` are
  already defined in this module at lines 60 and 54 respectively — no new import required).
- In each of the three branches (`--all`, `--days`, default/`--week`), add the matching `tools`
  window-filter alongside the existing `events` filter, reusing the same `run_ids` set already
  computed for events:
  - `--all` branch (line 1097-1102): `tools = all_tools`.
  - `--days` branch (line 1103-1110): after `events = [e for e in all_events if e.get("run_id") in
    run_ids]`, add `tools = [t for t in all_tools if t.get("run_id") in run_ids]`.
  - default/`--week` branch (line 1111-1117): same addition after its own `events = ...` line.
- Change the `generate()` call site (line 1119) from `generate(runs, events, label, week_str)` to
  `generate(runs, events, label, week_str, tools=tools)`.
**Do NOT touch:** `_load_runs_and_events()` itself, the SQLite index build path, or
`retrieval_baseline_metrics.py::load_all_sources()` (this ticket does not need to import from that
module — `load_jsonl`/`DEFAULT_TOOLS_FILE` already live in `generate_retro.py`).
**Verify:** existing `tests/tools/test_generate_retro.py` calls to `generate(runs, events, label)`
(no `tools` arg) still pass unmodified — run the full existing suite as regression proof (no new
test needed for this step specifically; it is proven by the absence of new failures plus Step 5's
rendering tests, which exercise the threaded parameter end-to-end).

### Step 5 — Render the "## Tool Safety Audit" section in `generate()`
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:** Insert a new block after the "## Shadow vs. Baseline Retrieval Comparison" block (after
line 1077, before the `# Notes (human-written)` comment at line 1079), gated on
`tool_safety["search_before_grep"]["investigate_pair_count"]` being nonzero (mirrors the existing
"gate on the thing this section is fundamentally about being nonzero, omit don't empty-render"
convention used by the Shadow/Baseline section at line 996):
```python
    # Tool Safety Audit (TCK-20260803-RETRO-TOOL-SAFETY-AUDIT): audits search-before-grep hard-rule
    # compliance (CLAUDE.md) during real Investigate phases, and parity_index.py write-safety
    # (zero-tolerance docs/parity_ledger/*.yaml write / real-path build invocation count).
    # Additive, separately-gated section — omitted entirely (not rendered empty) when the period
    # has zero real Investigate-phase tool-call data, matching the Shadow vs. Baseline section's
    # own gate.
    sbg = tool_safety["search_before_grep"]
    if sbg["investigate_pair_count"]:
        lines.append("## Tool Safety Audit")
        lines.append("")

        lines.append("### Search-Before-Grep Compliance (Investigate Phase)")
        lines.append("")
        rate = sbg["compliance_rate"]
        rate_str = "n/a" if rate is None else f"{rate * 100:.1f}%"
        lines.append(
            f"**Compliance rate:** {rate_str} "
            f"({sbg['compliant_count']}/{sbg['investigate_pair_count']} Investigate-phase calls)"
        )
        lines.append("")

        pws = tool_safety["parity_write_safety"]
        lines.append("### Parity Ledger Write-Safety")
        lines.append("")
        lines.append(
            f"**`docs/parity_ledger/*.yaml` write violations:** "
            f"{pws['parity_ledger_yaml_write_count']}"
        )
        lines.append(
            f"**Unsafe `parity_index.py build` invocations (real repo path):** "
            f"{pws['unsafe_parity_build_count']}"
        )
        lines.append("")
```
**Do NOT touch:** the "## Shadow vs. Baseline Retrieval Comparison" block, the "## Notes" block, or
the gating variable choice (do not gate on `parity_write_safety` counts — those are always reported,
even as 0, whenever the section renders at all; the section-level gate is `investigate_pair_count`
only, per AC3's literal wording).
**Verify:** `test_new_section_rendered_in_generate_output_when_investigate_tool_data_present`,
`test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data`.

### Step 6 — `docs/guides/agent_monitoring.md` Report Sections row
**Files:** `docs/guides/agent_monitoring.md`
**Change:** Add one new row to the "Report Sections" table (after the existing "Outliers" row,
line 69), matching the table's terse per-row style:
```
| **Tool Safety Audit** | Conditionally rendered — only appears when at least one Investigate-phase `(run_id, seq)` pair has `tools.jsonl` data in the period. Reports search-before-grep hard-rule (CLAUDE.md) compliance rate for real Investigate phases, and a zero-tolerance count of `docs/parity_ledger/*.yaml` write calls and unsafe `parity_index.py build` invocations (targeting the real repo path instead of a scratch path). Both counts should read 0 — a nonzero count is a real hard-rule/read-only-guarantee violation, not noise (`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`). |
```
**Do NOT touch:** any other row in this table, or the "Validation" section below it. Do not add a
row for "Retrieval Quality" or "Shadow vs. Baseline" — those rows are a pre-existing documentation
gap noted in investigation.md, out of this ticket's scope to fix.
**Verify:** manual read-through — no automated test covers doc table content; `make
knowledge-index-update` picks this up at Finalize since a `docs/` file changed.

### Step 7 — `docs/parity_ledger/infrastructure.yaml` new entry (Parity phase)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Add a new entry, `id: INFRA-315`, immediately after the current last entry
(`INFRA-314`, ending around line 7027+), following the exact field shape of `INFRA-300` (the
closest structural precedent — new pure `compute_*` function + new conditionally-rendered
section):
```yaml
- id: INFRA-315
  text: >
    TCK-20260803-RETRO-TOOL-SAFETY-AUDIT -- generate_retro.py gains
    compute_tool_safety_metrics(events, tools), a new pure function auditing (1) search-before-grep
    hard-rule compliance (CLAUDE.md) for tools.jsonl rows within Investigate-phase (run_id, seq)
    pairs identified via events.jsonl's phase field, and (2) parity_index.py write-safety -- a
    zero-tolerance count of Edit/Write calls into docs/parity_ledger/*.yaml and of
    `parity_index.py build` invocations targeting the real repo parity-index/parity.db path instead
    of a scratch path. generate() renders the result as a new, additively-appended
    "## Tool Safety Audit" section, placed after "## Shadow vs. Baseline Retrieval Comparison" and
    before "## Notes", gated on investigate_pair_count being nonzero -- omitted entirely, not
    rendered empty, when zero.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    tools/agent-monitoring/generate_retro.py (`def compute_tool_safety_metrics()` -- new function,
    partitions tools.jsonl rows by Investigate-phase (run_id, seq) membership derived from
    events.jsonl, returns {"search_before_grep": ..., "parity_write_safety": ...}).
    tools/agent-monitoring/generate_retro.py (`generate()` gains a trailing `tools=None` parameter
    and calls compute_tool_safety_metrics(events, tools); new conditionally-rendered
    "## Tool Safety Audit" section). tools/agent-monitoring/generate_retro.py (`main()` loads
    all_tools via load_jsonl(DEFAULT_TOOLS_FILE) and window-filters it alongside runs/events).
  proof_type: regression
  test_path: tests/tools/test_generate_retro.py
  divergence_note: null
  support_boundary: >
    Agent-orchestration/monitoring-pipeline tooling only -- no simulation behavior is involved.
    No `src/` file touched, no on-disk schema/corpus change, no new event-emission or call-site
    logic -- this is a pure read-only consumer of already-emitted tools.jsonl/events.jsonl data.
```
**Do NOT touch:** any existing entry (`INFRA-283` through `INFRA-314`). Do not renumber or reorder
existing entries — append only.
**Verify:** `python3 tools/parity_index.py build` (scratch `--db-path`, never the real repo path —
matching this ticket's own audited invariant) and any existing parity-ledger schema-validation
test/tool (e.g. `tools/validate_frontmatter.py`-adjacent or parity ledger schema check, if the repo
runs one in CI) still passes with the new entry present.

### Step 8 — Manual AC5 real-corpus verification (not a committed test)
**Files:** none (verification step only); record result in the ticket's `## Test Summary` section
at Finalize.
**Change:** Run `python3 tools/agent-monitoring/generate_retro.py --all` against this repo's real
`agent-monitoring/*.jsonl` data and confirm the new "## Tool Safety Audit" section's numbers match
the ticket's own hand-verified findings: 100% search-before-grep compliance across the 7 real
Investigate phases, 0 `docs/parity_ledger/*.yaml` write violations across the 4 parity runs, for the
equivalent all-time window. Do **not** commit a pytest assertion with these exact literal numbers
against the live, ever-growing real corpus (per test_plan.md's explicit recommendation) — this is a
one-time manual verification, documented in the ticket, not part of the automated suite.
**Do NOT touch:** do not add `test_generate_retro_real_corpus_matches_hand_verified_findings` (or
similarly named) as a hard-asserting pytest test against real data.
**Verify:** manual `--all` run output inspected and recorded in the ticket.

## Scope Guards

- Do not modify `tools/parity_index.py`, `tools/context_packet_assembler.py`, or any
  `PostToolUse`/`PreToolUse` hook that writes `tools.jsonl` (e.g.
  `tools/agent-monitoring/post_tool_hook.py`) — this ticket only reads existing log data.
- Do not retroactively re-audit or rewrite any historical `tools.jsonl`/`events.jsonl` row — the
  function is read-only over already-loaded lists; never write to any `agent-monitoring/*.jsonl`
  file from `compute_tool_safety_metrics` or its render path.
- Do not wire the new section into `.claude/workflows/implement-ticket.js`'s `phase(...)` gating —
  this stays a human-reviewed report section, never a blocking gate.
- Do not widen the write-safety check beyond `docs/parity_ledger/*.yaml` / `parity_index.py build`
  (no `.gitignore`, `Makefile`, or general protected-path audit).
- Do not import, reuse, or mutate `retrieval_baseline_metrics.py`'s `SEARCH_TOOL_NAMES` constant —
  it is a distinct vocabulary for a distinct metric (follow-up search count, not hard-rule
  compliance).
- Do not touch `compute_retrieval_metrics`, `compute_shadow_baseline_comparison`,
  `compute_retro_metrics`, `_resolve_status`, `_is_gate_fail`, `_is_legacy_event`, or any symbol
  `retrieval_baseline_metrics.py`/`build_index.py`/`test_agent_ops_dashboard_stats.py` imports from
  this module.
- Do not add the shadow-`ContextPacket` mechanism's "correctness" evaluation to this ticket —
  `compute_retrieval_metrics`'s own structural-emptiness gap is a separate, already-known,
  already-out-of-scope issue.
- Do not fix the pre-existing "Retrieval Quality"/"Shadow vs. Baseline" missing-rows gap in
  `docs/guides/agent_monitoring.md`'s Report Sections table — only add this ticket's own new row.

## Dependency Map

- Step 1 → Step 2 (same function; Step 2 replaces Step 1's stub) → Step 3 (guard tests need the
  complete function).
- Step 4 is independent of Steps 1-3 (pure signature/loading plumbing) but Step 5 depends on both
  Step 4 (needs `tool_safety` available inside `generate()`) and Steps 1-3 (needs the real
  computation, not the Step-1 stub).
- Step 6 and Step 7 (docs) are independent of each other and of Steps 1-5's code, but both describe
  the shipped behavior, so do them after Step 5 is finalized to avoid describing a moving target.
- Step 8 depends on all of Steps 1-7 being complete (it verifies the shipped, documented behavior
  against real data).

Suggested execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: new pure-computation function correctly reports search-before-grep compliance rate and parity write-safety violation count | Steps 1, 2 | Tests 1-9 (search-before-grep + parity write-safety fixture tests) |
| AC2: function never crashes on legacy/malformed rows | Step 3 | `test_tool_safety_function_never_crashes_on_malformed_rows` |
| AC3: `generate()` includes the new section, conditionally rendered | Steps 4, 5 | `test_new_section_rendered_in_generate_output_when_investigate_tool_data_present`, `test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data` |
| AC4: `docs/guides/agent_monitoring.md` Report Sections table has a new row | Step 6 | Manual read-through |
| AC5 (part 1): synthetic fixtures prove each check can detect a real violation, with passing/compliant contrast fixtures | Steps 1, 2 | Tests 3, 4, 8, 9 (violations) paired with tests 1, 2, 7 (compliant contrasts) |
| AC5 (part 2): real-corpus `--all` run matches hand-verified findings | Step 8 | Manual verification, recorded in ticket Test Summary |

## Anti-Drift Notes

- **`SEARCH_TOOL_NAMES` collision risk (investigation.md Anti-Drift Hazard):**
  `retrieval_baseline_metrics.py`'s `SEARCH_TOOL_NAMES = {"mcp__knowledge-search__search_docs",
  "ToolSearch", "WebSearch"}` answers "how many follow-up searches happened," not "was the
  search-before-grep hard rule honored." `ToolSearch`/`WebSearch` are not compliant substitutes for
  `search_docs`/`graphify` under CLAUDE.md's hard rule as the ticket defines it — `
  _is_search_or_graphify_call` (Step 1) must be its own, independent predicate, never import or
  reference `SEARCH_TOOL_NAMES`.
- **`_is_legacy_event`'s `agent is None` predicate is an `events.jsonl`-specific discriminator** —
  do not reuse it against `tools.jsonl` rows. `tools.jsonl` has its own, separate nullability story
  for `phase`/`agent` (schema.md), which this plan deliberately avoids depending on at all (Design
  Decision 3 above) by sourcing Investigate-phase identification exclusively from `events.jsonl`.
- **`seq` is not always `>= 1`.** The negative-`seq` shadow-packet convention (`context-packet-
  wrapper` rows) and `seq: null` (sidecar not yet written) both exist in real `tools.jsonl` data.
  This plan's design (Step 1: build the Investigate-phase key set from `events.jsonl` only, which
  has non-nullable, `>= 1` `seq` for real phase events) means these rows are structurally excluded
  by simply never matching any key — no explicit `if seq is None or seq <= 0: skip` branch is
  needed, but Step 3's malformed-row test must still assert this behavior explicitly rather than
  assume it holds.
- **Never make this section a workflow gate.** No `phase(...)` call in
  `.claude/workflows/implement-ticket.js` should ever reference `compute_tool_safety_metrics` or
  "Tool Safety Audit" — Verify/Finalize should grep-confirm this before closing the ticket (per
  test_plan.md's own anti-drift note).
- **The section-level render gate is `investigate_pair_count` only** (not a combined gate that also
  checks `parity_write_safety` counts) — this matches AC3's literal wording ("omitted ... when the
  period has zero real Investigate-phase tool-call data") and the Shadow-vs-Baseline section's own
  single-variable gate precedent. Do not invent a second, broader gating condition.
- **This ticket touches no `src/` code, no Mechanics Bible chapter, no Engine Contract, and no P0
  parity entry** — confirmed by investigation.md. `docs/parity_ledger/infrastructure.yaml`'s
  `INFRA-315` entry (Step 7) is `priority: P2`, matching every other entry in this new-report-
  section family (INFRA-283, INFRA-284, INFRA-298, INFRA-300).

## Deviations

No code step (1-7) deviated from this plan — every helper name, function signature, gating variable,
and section placement was implemented exactly as specified above, and all fixture-based tests in
Steps 1-3 and 5 pass.

**Step 8's real-corpus verification produced a result this plan did not anticipate.** Running
`python3 tools/agent-monitoring/generate_retro.py --all` against the real, whole-history
`agent-monitoring/*.jsonl` corpus (739 runs / 3973 events, not the "7 real Investigate phases" / "4
parity runs" this plan's Step 8 and the ticket's AC5 expected) produced 63.4% (71/112) search-before-
grep compliance and 355 `docs/parity_ledger/*.yaml` write matches (plus 1 flagged-unsafe build
invocation), not the expected 100%/0/0. This is not a code defect — every number is exactly what
Steps 1-2's logic, implemented to this plan's own literal spec, is supposed to compute. It is a gap
between this plan's Design Decision 3 discussion (which only addressed how to scope
`search_before_grep`, via Investigate-phase pairs) and an implicit assumption, never stated
explicitly in this plan, that `parity_write_safety`'s whole-period scan would land near zero at
real-corpus scale. In fact the whole-period scan (deliberately unscoped per Step 2's own text, "not
scoped to Investigate-phase pairs... scans the whole tools argument") correctly counts 355 completely
legitimate, expected `parity-updater`-agent edits to `docs/parity_ledger/*.yaml` from 114 unrelated
tickets' own Parity workflow phases — none of which involve `tools/parity_index.py` at all, the
actual tool this check exists to audit. The ticket's own Request Summary text ("Zero Edit/Write tool
calls ever targeted any docs/parity_ledger/*.yaml file across the 4 parity-epic runs") was scoped to
just the 4 `TCK-20260731-PARITY-INDEX-EPIC` child runs, a much narrower reading than "whole period."
Both readings are followed correctly from their respective source texts (Request Summary vs. Scope
text), but they are mutually inconsistent once run against the real corpus rather than a hand-picked
4-run sample — something no fixture test in Steps 1-3 could have caught, since fixtures are
necessarily small and hand-constructed to be either clean or violating by design.

No code was changed in response to this finding — narrowing `_is_parity_ledger_yaml_write`'s scope
(e.g. to only count writes co-occurring with a `parity_index.py`-touching tool call in the same run)
is a design decision outside this plan's approved scope, not a bug fix. See the ticket's
Implementation Notes and Completion Summary for the full finding, root-cause analysis (including a
separate, minor `input_summary`-truncation false-positive on the single flagged "unsafe build" row),
and the recommendation to open a follow-up ticket to resolve the scope/semantics gap.
