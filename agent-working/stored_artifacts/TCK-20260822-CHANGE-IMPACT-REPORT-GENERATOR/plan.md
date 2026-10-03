---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR
artifact_type: plan
tags: [architecture, testing]
---

# Implementation Plan — TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR

## Summary

Add one new module, `tools/pr_impact_report.py`, that batches `tools/code_health_impact.py`'s
existing `build_impact_report()` (confirmed 13-key return dict at
`tools/code_health_impact.py:468-482`) across one or more target paths and renders the result as a
Markdown report (`format_pr_impact_report()`) or as JSON (the batch dict returned by
`build_pr_impact_report()` is already fully JSON-serializable — no separate JSON formatter
function is needed). The module follows the `build_<x>()`/`format_<x>()`/`main()` triad already
established by `codebase_health_baseline.py`, `code_health_impact.py`, and
`codebase_health_snapshot.py`. Per the investigation's resolved conclusion (re-verified
independently against D24 §M item 11's literal text, "built on top of Phase 3's impact model" —
Phase 3 is the impact command, not the Phase 4 snapshot mechanism), this module has **no
dependency on `tools/codebase_health_snapshot.py`** — it renders from `build_impact_report()`
output alone, and AC #4's graceful-degradation clause is satisfied by there being no snapshot
integration to degrade from. Every one of the 13 real `build_impact_report()` fields is rendered
verbatim, per-path; a per-path exception is caught and surfaces as a `"failed"` entry without
aborting the batch; degradation signals (`dependents_degraded`, `dependents_degradation_reason`,
`unresolved_symbols`) are preserved exactly, mirroring `format_impact_report()`'s own conditional
(`tools/code_health_impact.py:503-507`); the triage-aid framing text is carried verbatim in the
module docstring, a top-level `framing_note` field in the batch dict (so it survives into JSON
mode too), and the Markdown output's closing line; and no aggregate/combined score field is ever
introduced. One new Makefile target, `codebase-health-pr-impact`, is added (on-demand only, not
CI, `$(ARGS)` passthrough, matching `codebase-health-impact`'s exact form at `Makefile:290-291`).
Thirteen-plus new tests land in `tests/tools/test_pr_impact_report.py`, mirroring
`tests/tools/test_code_health_impact.py`'s fixture-graph/injected-`affected_runner`/
`_requires_graphify` conventions (confirmed at `tests/tools/test_code_health_impact.py:1-41`).
Finally, the epic doc's 4th Scope bullet (`docs/plans/codebase_health_observatory_tooling_epic.md`
lines 86-87) is struck through and resolved, correcting the "built on top of" phrasing to name the
impact command specifically and stating explicitly that no snapshot-history dependency was needed.

## Steps

### Step 1 — Module skeleton, imports, and provenance docstring

**Files:** tools/pr_impact_report.py (new)

**Change:** Create the module with the standard sibling shape:
```python
_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import code_health_impact as chi  # noqa: E402
```
This mirrors `tools/codebase_health_snapshot.py`'s own import-guard pattern for a same-directory
sibling module (both `pr_impact_report.py` and `code_health_impact.py` live directly in plain
`tools/`, no hyphenated-directory boundary — confirmed by directory listing, same situation as
`codebase_health_snapshot.py`'s import of `codebase_health_baseline`).

Import `chi.build_impact_report`, `chi.load_graph`, `chi.load_registry_entries`,
`chi.DEFAULT_GRAPH_PATH`, `chi.DEFAULT_AFFECTED_DEPTH`, `chi.run_graphify_affected` — all
confirmed to exist as public module-level names by direct read of
`tools/code_health_impact.py:73-76` (constants) and `:438-446`/`:345-350`/`:138-140` (functions).
Do not import anything from `tools/codebase_health_snapshot.py` — this is the direct, testable
enforcement point for the investigation's resolved "no snapshot dependency" conclusion (Anti-Drift
Hazards, investigation.md).

Module docstring must state, verbatim, both:
1. The triage-aid framing, copied exactly from `tools/code_health_impact.py:6-9`: "This is a
   **discovery/triage aid, not a certified coverage oracle** — every signal below is a best-effort
   heuristic and is presented as such; false positives/negatives are acceptable, silently
   presenting them as certain is not."
2. An explicit design-decision note (mirroring how `codebase_health_snapshot.py`'s own docstring
   documents its design decisions): this module has no dependency on
   `tools/codebase_health_snapshot.py`'s snapshot/scorecard mechanism — it renders exclusively from
   `chi.build_impact_report()`'s existing per-path output, batched across one or more target paths.
   Cite `TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR` and the epic
   (`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`).

Define:
```python
FRAMING_NOTE = (
    "discovery/triage aid, not a certified coverage oracle — verify before "
    "treating any of the below as complete."
)
```
(Reuses the exact closing-note wording `format_impact_report()` already prints at
`tools/code_health_impact.py:524-527`, so the two tools' framing text stays byte-identical rather
than drifting into two slightly different phrasings of the same caveat.)

**Do NOT touch:** `tools/code_health_impact.py` — no edits to `build_impact_report()`,
`format_impact_report()`, or any constituent function. This step only imports from it as a
dependency. Do NOT import `tools/codebase_health_snapshot.py` for any reason.

**Verify:** No standalone test for this step alone; the no-import guard is verified by
`test_report_generator_has_no_import_of_codebase_health_snapshot_module` (Step 6).

### Step 2 — `build_pr_impact_report()`: per-path batching with failure isolation

**Files:** tools/pr_impact_report.py

**Change:** Add:
```python
def build_pr_impact_report(
    repo_root: Path,
    target_paths: list[str],
    depth: int = chi.DEFAULT_AFFECTED_DEPTH,
    graph: dict | None = None,
    graph_path: Path = chi.DEFAULT_GRAPH_PATH,
    registry_entries: list | None = None,
    affected_runner=chi.run_graphify_affected,
) -> dict:
```
Load `graph` once via `chi.load_graph(graph_path)` if not supplied, and `registry_entries` once
via `chi.load_registry_entries(repo_root / "docs" / "REGISTRY.yaml")` if not supplied — both
loaded a single time for the whole batch, then passed into every per-path
`chi.build_impact_report(...)` call via its existing `graph=`/`registry_entries=` parameters
(confirmed these are real, already-supported kwargs at `tools/code_health_impact.py:442-444`).
This avoids re-reading `graph.json`/`REGISTRY.yaml` from disk once per target path — a genuine
orchestration improvement, not new impact-computation logic (the per-path computation itself is
still 100% delegated to `chi.build_impact_report()`).

For each `target_path` in `target_paths`, call `chi.build_impact_report(repo_root, target_path,
depth=depth, graph=graph, graph_path=graph_path, registry_entries=registry_entries,
affected_runner=affected_runner)` inside a `try/except Exception`:
- On success: append `{"target_path": target_path, "status": "ok", "report": report, "error":
  None}` to an `entries` list. (`report["dependents_degraded"]` may be `True` here — that is a
  *within-report* signal preserved verbatim from `chi.build_impact_report()`'s own output, not a
  batch-level failure; `"status"` at the batch level only distinguishes whether the call raised.)
- On any exception: append `{"target_path": target_path, "status": "failed", "report": None,
  "error": str(exc)}`. Do not re-raise, do not abort the loop — this is the direct implementation
  of Scope bullet 6 / AC-adjacent "one degraded path does not silently fail the whole report."

**Confirmed via direct read that `chi.build_impact_report()` given a *valid, already-loaded*
`graph` dict does not itself raise for an unresolvable/nonexistent target path** — every internal
lookup degrades to an empty/zero default instead: `find_file_node()` returns `None` for no match
(`tools/code_health_impact.py:143-158`), `resolve_defined_symbols(graph, None)` returns `[]`
(`:161-172`), `find_dependents()` then takes its zero-symbols branch and returns
`degraded=True` with an explicit reason (`:211-223`) rather than raising;
`compute_edge_degree()` returns `0` for an empty `node_ids` set (`:377-390`);
`compute_churn_lines_changed(target_pathspec=target_path)` (`tools/codebase_health_baseline.py:
201-230`) calls `_run_git(["log", "--shortstat", ..., "--", target_pathspec, ...])`
(`tools/codebase_health_baseline.py:82-87`, `subprocess.run(..., check=True)`) — a nonexistent
git pathspec produces empty `git log` output, not a non-zero exit code, so no
`CalledProcessError` fires either. The realistic exception surface for the batch's `try/except` is
therefore narrower than "any bad path" — it is chiefly: (a) `affected_runner` raising
(e.g. `FileNotFoundError` if the `graphify` binary itself is missing from `PATH` when the default
`chi.run_graphify_affected` is used un-injected — `subprocess.run` with a missing executable
raises rather than returning a failed `CompletedProcess`), or (b) a caller-injected fixture
`affected_runner`/`graph` deliberately raising in a test. The `try/except Exception` is still the
correct, generic guard (Scope bullet 6 does not restrict itself to one specific exception type),
and the test plan's `test_one_degraded_or_failing_path_does_not_abort_the_whole_batch` exercises
this via an injected raising callable/graph, not by relying on `chi.build_impact_report()`'s
natural behavior for a bad path (which, per the above, degrades rather than raises).

Return:
```python
{
    "target_paths": list(target_paths),
    "entries": entries,
    "framing_note": FRAMING_NOTE,
}
```
No key here or anywhere else in this dict resembles `score`/`overall`/`combined`/`summary`/
`health_score` — `target_paths`, `entries`, `framing_note` are the entire top-level shape.

**Other writers to shared resources this step touches:** `chi.load_graph()` reads
`graphify-out/graph.json` (never writes it); `chi.load_registry_entries()` reads
`docs/REGISTRY.yaml` (never writes it). Neither file is written by this module or by
`build_pr_impact_report()` — both are read-only inputs already produced by other, unrelated
pipelines (`graphify update .`, the Finalize-phase registry regeneration). There is no write
contention to manage: this step performs zero durable writes of any kind (no `agent-monitoring/`
write, no cache write, no mutation of either input file).

**Do NOT touch:** `chi.build_impact_report()`'s internals, `chi.find_dependents()`,
`chi.compute_churn_lines_changed()` — this step only calls the existing public function once per
path.

**Verify:**
- `test_multi_path_batch_report_includes_all_requested_paths`
- `test_one_degraded_or_failing_path_does_not_abort_the_whole_batch`
- `test_report_generator_does_not_reimplement_impact_computation`

### Step 3 — `format_pr_impact_report()`: Markdown renderer, all 13 fields, degradation-conditional

**Files:** tools/pr_impact_report.py

**Change:** Add `format_pr_impact_report(report: dict, max_dependents_shown: int = 40) -> str`,
a pure-presentation function over `build_pr_impact_report()`'s returned dict (never recomputes
anything). Renders, per entry in `report["entries"]`:

- A `## <target_path>` heading.
- If `status == "failed"`: a single line, `**Failed:** <error>` — clearly labeled, not silently
  omitted, and not counted as a degraded-but-successful entry.
- If `status == "ok"`: render **all 13** real fields from `entry["report"]`
  (`target_path, subsystem, dependents, dependents_degraded, dependents_degradation_reason,
  resolved_symbols, unresolved_symbols, required_tests, required_tests_registry_hit_count,
  architecture_rules, churn_lines_changed, edge_degree, criticality_tier` — confirmed exact key
  list and order via the literal `return {...}` block at `tools/code_health_impact.py:468-482`).
  This resolves investigation.md's flagged open item explicitly: render **all 13 real keys**, not
  the 7-field paraphrase from the ticket's own Scope bullet 2 — investigation.md's recommendation,
  adopted here without further debate, since omitting any of the 6 un-paraphrased fields
  (`target_path`, `resolved_symbols`, `required_tests_registry_hit_count`, `churn_lines_changed`,
  `edge_degree`, and treating `architecture_rules` as if it were two separate fields) would itself
  be a form of silently dropping data, which Scope bullet 3 explicitly forbids for the 3
  degradation-signal fields — there is no principled reason to apply a laxer standard to the other
  10 fields AC #1 also requires be "fully traceable."
  - `dependents`: same truncation convention as `format_impact_report()`
    (`tools/code_health_impact.py:492-499`) — show up to `max_dependents_shown`, note the total
    count and `+N more` suffix if truncated. Full list is always present in JSON mode.
  - **Reproduce `format_impact_report()`'s exact degradation conditional**
    (`tools/code_health_impact.py:503-507`): render `dependents_degradation_reason` when
    `dependents_degraded` is `True`; render the `unresolved_symbols` list as a "note:" line only
    when `dependents_degraded` is `False` and the list is non-empty — never print both a
    degradation-reason line and a stale/empty unresolved-symbols note for the same entry (the
    investigation's explicit anti-drift instruction).
  - When `dependents_degraded` is `False`, `dependents_degradation_reason` is `None`, and
    `unresolved_symbols` is `[]`: render cleanly (e.g. "(none found)"/omit the note line) — no
    literal `None`/`null` leaking into the Markdown text.
  - `resolved_symbols`, `required_tests`, `architecture_rules`: comma-joined lists, or an explicit
    "(none found)"-style placeholder when empty (mirroring `format_impact_report()`'s own
    empty-case phrasing at `:509-517`).
  - `required_tests_registry_hit_count`, `churn_lines_changed`, `edge_degree`,
    `criticality_tier`, `subsystem`: rendered as plain labeled lines.

After all entries, append one closing line containing `report["framing_note"]` verbatim (the
`FRAMING_NOTE` constant from Step 1) — this is the single Markdown-mode anchor point for the
triage-aid-framing test.

**Do NOT** call `chi.format_impact_report()` itself and relabel its output as this module's
Markdown/JSON artifact — investigation.md's Anti-Drift Hazards is explicit that
`format_impact_report()` is a template to study (truncation convention, degradation-conditional,
empty-case phrasing — all reused above), not a function to import and wrap silently, since AC #1
requires a rendered artifact in a genuinely different shape (Markdown headings/sections per path)
than `format_impact_report()`'s fixed-width single-path plain text.

**Do NOT touch:** `chi.format_impact_report()` — read only for convention, never imported or
called by this module.

**Verify:**
- `test_report_generator_renders_all_13_real_fields_from_build_impact_report`
- `test_report_preserves_dependents_degraded_and_reason_verbatim`
- `test_report_preserves_unresolved_symbols_list_verbatim`
- `test_report_does_not_silently_drop_degradation_fields_when_absent`
- `test_report_includes_discovery_triage_aid_framing_verbatim`
- `test_report_generator_output_is_well_formed_markdown_when_markdown_mode_requested`

### Step 4 — JSON output mode and the no-aggregate-score guard

**Files:** tools/pr_impact_report.py

**Change:** No new function is needed for JSON mode: `build_pr_impact_report()`'s returned dict
(Step 2) is already fully JSON-serializable as-is — every value is a `str`, `bool`, `int`, `list`,
`dict`, or `None` (confirmed by the real `chi.build_impact_report()` return-block types at
`tools/code_health_impact.py:468-482`; no `set` survives into the returned dict, since
`sort_dependents_src_first()` already converts the internal `set` to a sorted `list` before
`build_impact_report()`'s own return statement). JSON-mode output is simply
`json.dumps(build_pr_impact_report(...), indent=2)`, wired in `main()` (Step 5).

This is also where the no-aggregate-score guard is structurally enforced: the batch dict's
top-level keys (`target_paths`, `entries`, `framing_note`) and each entry's keys (`target_path`,
`status`, `report`, `error`) plus the nested 13-key `report` dict contain no key resembling
`score`/`overall`/`combined`/`summary`/`health_score` anywhere at any nesting level — confirmed by
enumerating every key introduced in Steps 1-3 above; none of the 13 real `chi.build_impact_report()`
keys match either (already verified clean by the sibling ticket's own equivalent audit of
`build_report()`'s keys, and re-confirmed here directly against the literal key list).

**Do NOT touch:** No source changes beyond what Steps 1-3 already produced; this step is purely a
verification/wiring step (the JSON path is "for free" from Step 2's dict shape).

**Verify:**
- `test_report_generator_output_is_valid_json_when_json_mode_requested`
- `test_report_output_has_no_aggregate_or_combined_score_field`

### Step 5 — `main()` CLI entrypoint: multi-path argparse, `--format`

**Files:** tools/pr_impact_report.py

**Change:** Add:
```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target_paths", nargs="+",
        help="One or more repo-relative source paths, e.g. src/engine/pipeline.py",
    )
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--depth", type=int, default=chi.DEFAULT_AFFECTED_DEPTH)
    parser.add_argument("--graph", type=Path, default=chi.DEFAULT_GRAPH_PATH)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)

    report = build_pr_impact_report(
        args.repo_root, args.target_paths, depth=args.depth, graph_path=args.graph,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_pr_impact_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
`nargs="+"` on a single positional is the chosen CLI shape (investigation.md's open item,
resolved here): no existing sibling module in this repo takes multiple positional paths to copy
verbatim, and `nargs="+"` is the standard argparse idiom for "one or more of the same positional
argument," simpler than repeated `--path` flags or stdin-based input and requiring no new
parsing convention.

**Do NOT touch:** `chi.main()` (`tools/code_health_impact.py:532-542`) — this step adds a wholly
separate `main()` in the new module; the existing single-path CLI is untouched.

**Verify:** `test_cli_accepts_multiple_target_paths`

### Step 6 — Architecture guard test: no import of `codebase_health_snapshot`

**Files:** tests/tools/test_pr_impact_report.py (new — this step contributes one test to it;
Step 8 lands the full file)

**Change:** Add `test_report_generator_has_no_import_of_codebase_health_snapshot_module`,
following the same literal-source-scan pattern `tests/tools/test_monitoring_writer.py:31-51` uses
(read the real `tools/pr_impact_report.py` source text via `inspect.getsource` or a direct file
read, assert neither `"import codebase_health_snapshot"` nor `"from codebase_health_snapshot"`
appears anywhere in it). This is the direct, automatable enforcement of the investigation's
resolved conclusion (investigation.md "Risks and Open Questions" — no real per-path dependency
exists between this module and `tools/codebase_health_snapshot.py`'s repo-wide-aggregate
snapshot mechanism). If this test ever starts failing because a future change adds that import,
that is the explicit signal to re-open the resolved Assumptions-section question, not to silently
update the test.

**Do NOT touch:** `tools/codebase_health_snapshot.py` itself — this test only scans
`tools/pr_impact_report.py`'s own source text.

**Verify:** `test_report_generator_has_no_import_of_codebase_health_snapshot_module` (this test
*is* its own verification).

### Step 7 — Makefile wiring

**Files:** Makefile

**Change:** Add one new target immediately after the existing `codebase-health-scorecard` target
(confirmed real, current text at `Makefile:293-296`), following the exact `## <description>
(on-demand only — not CI)` comment convention and `$(ARGS)` passthrough already used by
`codebase-health-impact` (`Makefile:290-291`, confirmed real text: `python3
tools/code_health_impact.py $(ARGS)`):
```
codebase-health-pr-impact: ## Print a batched PR/AI change-impact report for one or more source paths (pass ARGS="path1 path2 ...") (on-demand only — not CI)
	python3 tools/pr_impact_report.py $(ARGS)
```
Add `codebase-health-pr-impact` to the `.PHONY:` line (`Makefile:1`) — confirmed by direct read
that `codebase-health-snapshot`/`codebase-health-scorecard` are both already correctly present in
`.PHONY` (the sibling ticket's own fix), while `codebase-health-baseline`/`codebase-health-impact`
remain a pre-existing, out-of-scope omission this ticket does not touch.

**Other writers to `.PHONY:`:** none concurrent — a single static line in a version-controlled
file, edited serially by whichever ticket adds a new phony target (same conclusion the sibling
ticket's plan reached for the same line). This step only inserts one new name into the existing
space-separated list without disturbing any other entry.

**Do NOT touch:** the `codebase-health-baseline`/`codebase-health-impact` targets' own
pre-existing `.PHONY` omission — not this ticket's scope to fix.

**Verify:** `test_make_target_runs_successfully_against_real_repo`

### Step 8 — New test file: remaining tests

**Files:** tests/tools/test_pr_impact_report.py (new)

**Change:** Implement every remaining test enumerated in test_plan.md's "New Tests Required"
section not already covered by Steps 2-6 above, following
`tests/tools/test_code_health_impact.py:1-41`'s established conventions exactly: module-level
`_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"` + `sys.path.insert`, `import
pr_impact_report as pir` (and `import code_health_impact as chi` where a test needs to
cross-check against a directly-computed `build_impact_report()` dict), the identical
`_GRAPHIFY_AVAILABLE`/`_requires_graphify` skip-marker pattern (import or duplicate it from
`test_code_health_impact.py` — do not invent a second guard), and fixture-graph
(`_make_graph`-style) + injected `affected_runner` construction rather than hitting the real
`graphify` subprocess except in the one `@_requires_graphify`-marked Makefile end-to-end test.

Full test list for this file (13 tests total across Steps 2-8):
1. `test_report_generator_renders_all_13_real_fields_from_build_impact_report` (Step 3)
2. `test_report_generator_does_not_reimplement_impact_computation` (Step 2) — call
   `build_pr_impact_report()` against a fixture graph/target path, separately call
   `chi.build_impact_report()` directly against the same fixture inputs, assert every rendered
   value traces back to the directly-computed dict's own values with no independent
   recomputation.
3. `test_report_generator_output_is_valid_json_when_json_mode_requested` (Step 4) —
   `json.loads(json.dumps(build_pr_impact_report(...)))` round-trips without error.
4. `test_report_generator_output_is_well_formed_markdown_when_markdown_mode_requested` (Step 3)
5. `test_report_preserves_dependents_degraded_and_reason_verbatim` (Step 3)
6. `test_report_preserves_unresolved_symbols_list_verbatim` (Step 3)
7. `test_report_does_not_silently_drop_degradation_fields_when_absent` (Step 3)
8. `test_report_output_has_no_aggregate_or_combined_score_field` (Step 4) — assert on the
   *structured* dict's key set (recursively, across all nesting levels) as well as the rendered
   Markdown text, mirroring the sibling ticket's own stated rationale for auditing both.
9. `test_report_includes_discovery_triage_aid_framing_verbatim` (Step 3) — assert the literal
   `FRAMING_NOTE` text appears in both Markdown output and the JSON dict's `framing_note` field.
10. `test_report_generator_has_no_import_of_codebase_health_snapshot_module` (Step 6)
11. `test_multi_path_batch_report_includes_all_requested_paths` (Step 2)
12. `test_one_degraded_or_failing_path_does_not_abort_the_whole_batch` (Step 2) — use an injected
    `affected_runner`/`graph` fixture that raises for one specific target path (per Step 2's
    finding that `chi.build_impact_report()` does not naturally raise for a merely-unresolvable
    path given a valid graph — an injected failure is required to exercise the `except` branch
    genuinely), and separately/additionally a fixture where one path's dependents are degraded
    (`dependents_degraded=True`) to confirm that case does not abort the batch either. Assert the
    other paths' entries remain complete and correct.
13. `test_cli_accepts_multiple_target_paths` (Step 5)

Plus the Makefile end-to-end test from Step 7:
14. `test_make_target_runs_successfully_against_real_repo` — `@_requires_graphify`-marked,
    `subprocess.run(["make", "codebase-health-pr-impact", "ARGS=..."])` against 1-2 real paths in
    this repo, asserting `returncode == 0` and expected section markers appear in stdout.

**Do NOT touch:** `tests/tools/test_code_health_impact.py`,
`tests/tools/test_codebase_health_baseline.py`, `tests/tools/test_codebase_health_snapshot.py` —
all three are regression surface only (test_plan.md), read for pattern reference, never edited by
this ticket.

**Verify:** `pytest tests/tools/test_pr_impact_report.py -v` (all 14 tests pass), plus
`pytest tests/tools/ -k "pr_impact_report or code_health_impact or codebase_health" -v`
(regression surface, per test_plan.md's Scoped Pytest Commands).

### Step 9 — Epic doc bullet resolution

**Files:** docs/plans/codebase_health_observatory_tooling_epic.md

**Change:** Apply the exact `~~struck-through~~` + `**Resolved** (TICKET-ID, ...)` treatment
already used for the three sibling bullets above it (confirmed real text at lines 27-85 of this
file). The target bullet — confirmed exact current text at lines 86-87: "- PR/AI change-impact
report generator, built on top of the impact-model command above — the last item in sequence,
since it depends on everything before it." — gets struck through in full and followed by a
`**Resolved** (`TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR`, 2026-08-2X)` paragraph that:
1. Summarizes the new `tools/pr_impact_report.py` module, `build_pr_impact_report()`/
   `format_pr_impact_report()`/`main()`, the new `codebase-health-pr-impact` Makefile target.
2. **Explicitly corrects the "built on top of" phrasing**: states that this ticket is built on
   top of the Phase 3 impact command (`tools/code_health_impact.py::build_impact_report()`)
   specifically, not on top of the Phase 4 historical-snapshot mechanism
   (`tools/codebase_health_snapshot.py`) — matching D24 §M item 11's own literal wording ("built
   on top of Phase 3's impact model") — and that no snapshot-history dependency was required or
   built, per this ticket's own investigation.md.
3. Notes all 13 real `build_impact_report()` fields are rendered, degradation signals are
   preserved verbatim, and no aggregate/combined score field exists anywhere in either output
   mode — matching the level of implementation-summary detail the three existing resolved bullets
   already carry.

**Do NOT touch:** the three already-resolved bullets above it (lines 27-85), or the "Out of
scope" section (lines 89-92) — this step only resolves the one bullet this ticket's scope covers.

**Verify:** `pytest tests/docs/test_doc_integrity.py -v` (validates the doc still parses/any
path references remain valid); no dedicated unit test otherwise — verified by direct diff review
against the three sibling bullets' existing formatting during Verify phase.

### Step 10 — Confirm no parity ledger entry needed

**Files:** none (verification-only step, no file changes)

**Change:** No `docs/parity_ledger/*.yaml` entry is added or modified. Confirmed by
investigation.md's "Parity Ledger Overlap" section: grepped every `docs/parity_ledger/*.yaml` for
`code_health_impact`/`codebase_health`/`pr_impact_report`/`change.impact`/`graphify` in the
relevant sense — zero hits belonging to this tool family (the only hits are unrelated
`search_mcp.py`/KGMCP references in `infrastructure.yaml`). This ticket touches no `src/`
simulation path, no Mechanics Bible chapter, and no engine contract — same conclusion both
immediately-preceding sibling tickets in this epic reached for the identical reason. State this
explicitly in the Completion Summary when the ticket closes.

**Do NOT touch:** `docs/parity_ledger/` — no file in this directory is created or edited by this
ticket.

**Verify:** No test; this is a documented negative-confirmation step, re-stated at ticket close.

## Scope Guards

Explicit list of things this plan must not touch, per the ticket's Out of Scope section and
investigation.md's Anti-Drift Hazards:

- **`tools/code_health_impact.py`'s `build_impact_report()` and every constituent function it
  calls** — no edits, no re-implementation, no re-derivation anywhere in the new module. The new
  module only imports and calls `build_impact_report()` directly, once per target path.
- **`tools/codebase_health_snapshot.py`** — no import, no dependency, no "while I'm here" trend
  integration. This is the investigation's central resolved question; re-litigating it
  mid-implementation would violate both the Out-of-Scope section and the resolved conclusion.
  Directly enforced by `test_report_generator_has_no_import_of_codebase_health_snapshot_module`
  (Step 6).
- **Any aggregate/combined score field, anywhere in the output structure** — not just the printed
  Markdown text. Both `build_pr_impact_report()`'s returned dict (at every nesting level) and
  `format_pr_impact_report()`'s printed text must be auditable via a denylist-style key/substring
  check (`score`/`overall`/`combined`/`summary`/`health_score`) and contain none.
- **New CLI/git-diff-parsing logic to auto-enumerate changed paths from a PR diff** — this ticket
  accepts explicit target paths only (`nargs="+"`); diff-parsing is separate, unscoped surface
  area per the ticket's own Out of Scope section.
- **Choosing/changing the C1 scorecard dimension set** — `tools/codebase_health_snapshot.py`'s
  `EXPECTED_SNAPSHOT_KEYS`/dimension list is untouched; this ticket has no dependency on it at
  all (see above).
- **`chi.format_impact_report()`** — read only, as a template for truncation/degradation-phrasing
  conventions. Never imported or called; this module's own Markdown renderer is a genuinely
  separate function producing a genuinely different (multi-path, sectioned) shape.
- **CI wiring of the new Makefile target** — `codebase-health-pr-impact` is on-demand only,
  matching every sibling target's precedent; no `.github/workflows/*.yml` file is touched.
- **The `codebase-health-baseline`/`codebase-health-impact` targets' own pre-existing `.PHONY`
  omission** — not fixed by this ticket; only this ticket's own one new target is added to
  `.PHONY`.
- **`docs/parity_ledger/`** — no entry needed or added (Step 10).
- **The three already-resolved epic-doc bullets** (`docs/plans/codebase_health_observatory_tooling_epic.md`
  lines 27-85) and the "Out of scope" section (lines 89-92) — only the 4th bullet (lines 86-87) is
  edited.
- **`docs/audits/D24_codebase_health_observatory.md`** — frozen historical document, never edited
  by child tickets (confirmed precedent: unedited by either prior sibling ticket).

## Dependency Map

- Step 1 (skeleton/imports/docstring/`FRAMING_NOTE`) blocks Steps 2-6 (all reference `chi.*`
  imports or `FRAMING_NOTE`).
- Step 2 (`build_pr_impact_report`) and Step 3 (`format_pr_impact_report`) are sequenced but not
  functionally blocking beyond Step 1 — Step 3 consumes Step 2's dict shape, so Step 3 cannot be
  finished/tested until Step 2's shape is stable, but both can be drafted in parallel with the
  shape agreed up front (the shape is fully specified in Step 2's own text).
- Step 4 (JSON mode / no-aggregate guard) depends on Steps 2-3 (audits the shapes both produce).
- Step 5 (`main()`) depends on Steps 2-4 (composes all of them).
- Step 6 (no-import architecture-guard test) depends only on Step 1 (the module existing at all)
  — can be written and run as soon as Step 1 lands, independent of Steps 2-5's completeness.
- Step 7 (Makefile) depends on Step 5 (needs the final CLI invocation shape).
- Step 8 (remaining tests) depends on Steps 1-7 all being in place, though individual test groups
  can be written incrementally alongside each corresponding step (as noted per-test above).
- Step 9 (epic doc bullet) is independent of all other steps; do last, immediately before
  Finalize.
- Step 10 (parity confirmation) is independent of all other steps; a documentation-only
  confirmation, can be done at any point, restated at ticket close.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: entrypoint accepts one or more target paths, calls `build_impact_report()` per path, produces a rendered Markdown or JSON artifact fully traceable to `build_impact_report()`'s existing fields, no impact-computation logic duplicated outside `tools/code_health_impact.py` | Step 2 (`build_pr_impact_report`), Step 3 (Markdown renderer, all 13 fields), Step 4 (JSON mode) | `test_report_generator_renders_all_13_real_fields_from_build_impact_report`, `test_report_generator_does_not_reimplement_impact_computation`, `test_report_generator_output_is_valid_json_when_json_mode_requested`, `test_report_generator_output_is_well_formed_markdown_when_markdown_mode_requested` |
| AC #2: generated output preserves and surfaces `dependents_degraded`, `dependents_degradation_reason`, and `unresolved_symbols` verbatim rather than silently dropping them | Step 3 (degradation-conditional rendering) | `test_report_preserves_dependents_degraded_and_reason_verbatim`, `test_report_preserves_unresolved_symbols_list_verbatim`, `test_report_does_not_silently_drop_degradation_fields_when_absent` |
| AC #3: generated output never renders a single aggregate numeric 'health score' — only `criticality_tier`, `architecture_rules`, `required_tests` (existing tiered/qualitative fields) are surfaced | Step 2 (batch dict key shape), Step 4 (structural + textual denylist guard) | `test_report_output_has_no_aggregate_or_combined_score_field` |
| AC #4: if (and only if) design confirms a real dependency on C1's historical-snapshot data, degrade gracefully when no snapshot history exists for a path | Resolved as not applicable — investigation.md confirms no real per-path dependency exists; Step 1 (no import), Step 6 (enforcement) | `test_report_generator_has_no_import_of_codebase_health_snapshot_module` |

## Anti-Drift Notes

- **Do not add a snapshot/scorecard dependency "just in case."** The investigation resolved this
  explicitly as out of scope for this iteration (structural mismatch: `codebase_health_snapshot.py`'s
  14 keys are repo-wide aggregates with no per-path join key; D24 §L never proposed the
  dependency; §M's "built on top of" refers to Phase 3, not Phase 4). Re-litigating it
  mid-implementation — even a small "while I'm here" trend line — violates both the Out-of-Scope
  section and this ticket's own resolved conclusion. `test_report_generator_has_no_import_of_codebase_health_snapshot_module`
  is the standing automated guard; if it ever needs to be updated to allow the import, that is the
  explicit trigger to re-open the Assumptions-section question, not a routine test update.
- **Do not recompute or re-derive any of `build_impact_report()`'s 13 fields.**
  `test_report_generator_does_not_reimplement_impact_computation` is the standing regression
  guard — if it ever needs a mock/stub of `chi.build_impact_report()` itself to keep passing after
  a source change, AC #1 has been silently violated.
- **Render all 13 real fields, not the ticket's own 7-field paraphrase.** The ticket's Scope
  bullet 2 list ("subsystem, direct dependents, required tests, relevant invariants, architecture
  rules, criticality tier") is a paraphrase; the real return dict has 13 keys and no separate
  "relevant invariants" field exists (`architecture_rules` covers both phrases — confirmed, no
  second field). Omitting `target_path`, `resolved_symbols`, `required_tests_registry_hit_count`,
  `churn_lines_changed`, or `edge_degree` because they weren't named in the ticket's prose would be
  a silent, undetected scope narrowing.
- **Preserve the triage-aid framing text verbatim, not paraphrased away**, in three places: the
  new module's own docstring, the `FRAMING_NOTE` constant (byte-identical to
  `format_impact_report()`'s own closing-note wording at `tools/code_health_impact.py:524-527`),
  and both output modes (Markdown's closing line, JSON's `framing_note` key) — test for the
  literal phrase, not "some caveat exists."
- **Reproduce `format_impact_report()`'s exact degradation-vs-unresolved-symbols conditional**
  (`tools/code_health_impact.py:503-507`) — never print both a degradation-reason line and a
  stale/empty unresolved-symbols note for the same entry.
- **`chi.build_impact_report()` does not naturally raise for a merely-unresolvable target path**
  given a valid, already-loaded graph (confirmed by direct trace through `find_file_node` →
  `resolve_defined_symbols` → `find_dependents`'s zero-symbols branch, and through
  `compute_edge_degree`/`compute_churn_lines_changed`'s empty-input branches — all degrade to
  empty/zero defaults rather than raising). The batch's `try/except` is real, generic defense for
  Scope bullet 6 (an injected/fixture failure, or a missing `graphify` binary breaking
  `affected_runner`), but a test that wants to exercise the `"failed"` branch must inject a
  raising fixture — it cannot rely on merely passing a nonexistent path to trigger it, since that
  legitimately produces a `"status": "ok"` entry with `dependents_degraded=True` instead.
- **Never target the real `agent-monitoring/` or `graphify-out/` paths from a test, except the one
  `@_requires_graphify`-marked Makefile end-to-end test** — every other new test must use a
  fixture graph / injected `affected_runner`, exactly mirroring
  `tests/tools/test_code_health_impact.py`'s own established pattern.

## Deviations (recorded during Implement)

- **Step 3's degradation-conditional resolved with two, not one, rendering layers.** Step 3's text
  describes a single "reproduce `format_impact_report()`'s exact degradation conditional" behavior
  (render `dependents_degradation_reason` only when `dependents_degraded` is `True`; render
  `unresolved_symbols` as a "note:" line only when `dependents_degraded` is `False` and the list is
  non-empty) but separately requires "all 13 real fields" be rendered for full traceability
  (AC #1) and that `dependents_degraded`/`dependents_degradation_reason`/`unresolved_symbols` never
  be silently dropped (AC #2 / Scope bullet 3). Taken literally as one rule, these two requirements
  conflict for the case `dependents_degraded=True` with a non-empty `unresolved_symbols` (the "No
  unique node match" case) — the pure `format_impact_report()`-style conditional would suppress
  `unresolved_symbols` entirely from the output in that case, which is exactly the kind of silent
  drop AC #2 forbids. Resolved by rendering in two layers: (1) a `format_impact_report()`-faithful
  "dependents" summary line/note reproducing the exact conditional verbatim (never shows both a
  degradation-reason line and a stale/empty unresolved-symbols note together, matching the
  anti-drift instruction precisely), and (2) always-present, separately labeled raw field lines for
  `dependents_degraded`, `dependents_degradation_reason` (using a clean `(none)` placeholder instead
  of a literal `None` when absent), and `unresolved_symbols` (comma-joined list, or `(none)` when
  empty) — present regardless of the degraded state, so no field or value the underlying report
  actually carries is ever fully absent from the Markdown output. This satisfies both the
  conditional-reproduction requirement and the never-silently-drop requirement without contradiction;
  `test_report_preserves_dependents_degraded_and_reason_verbatim`,
  `test_report_preserves_unresolved_symbols_list_verbatim`, and
  `test_report_does_not_silently_drop_degradation_fields_when_absent` all pass against this
  two-layer rendering.
- **Markdown field order matches the canonical 13-key `build_impact_report()` return order exactly**
  (`target_path, subsystem, dependents, dependents_degraded, dependents_degradation_reason,
  resolved_symbols, unresolved_symbols, required_tests, required_tests_registry_hit_count,
  architecture_rules, churn_lines_changed, edge_degree, criticality_tier`) rather than any
  alternate grouping — not called out explicitly in Step 3's prose, but the most literal reading of
  "render all 13 real fields ... confirmed exact key list and order via the literal `return {...}`
  block."
