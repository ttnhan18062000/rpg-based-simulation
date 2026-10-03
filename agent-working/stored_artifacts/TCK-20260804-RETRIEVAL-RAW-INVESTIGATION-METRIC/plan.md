---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC
artifact_type: plan
tags: [agent-monitoring, observability]
---

# Implementation Plan — TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC

## Summary

Add `build_raw_investigation_count_section(tools)` to
`tools/agent-monitoring/retrieval_baseline_metrics.py`, structurally mirroring
`build_search_count_section()` exactly (`per_run`/`total`/`derivation` keys, same
`run_id`-or-`"unattributed"` null-key convention, same single-pass-over-already-loaded-`tools`
discipline), filtering strictly to `record.get("tool") == "Read"`. The function additionally
returns a `read_to_search_ratio` field, computed **corpus-wide only** (never per-run) by calling
`build_search_count_section(tools)` internally to obtain the search total — this sidesteps the
per-run key-mismatch and division-by-zero risks investigation.md's Risk #2 flagged, without
inventing a silent default. The new function is inserted immediately after
`build_legacy_schema_notes` and immediately before `build_baseline_report`, wired into that
function's literal dict under the new key `"raw_investigation_count"`. The one existing test whose
exact-key-set assertion this wiring breaks
(`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`) is updated in the same step,
five new tests are added per test_plan.md, and both `docs/parity_ledger/infrastructure.yaml`
(`INFRA-292`) and `docs/agent-monitoring/README.md` are updated to reflect the new section.

## Resolved Decisions (were open in investigation.md — now settled)

### Decision 1 — `read_to_search_ratio` shape

**Computed, corpus-wide only, never per-run.** Lives as a fourth key inside
`build_raw_investigation_count_section(tools)`'s own return dict (sibling to `derivation`/
`per_run`/`total`), not as a separate top-level report key and not duplicated per-`run_id` inside
`per_run`.

Computation: the function calls `build_search_count_section(tools)` internally (already defined
earlier in the module; this is function composition on the same already-loaded `tools` parameter,
**not** a new/second data loader — no new `load_jsonl`/file-read call is added) to obtain
`search_total = build_search_count_section(tools)["total"]`. Then:

- If `search_total > 0`: `read_to_search_ratio = round(read_total / search_total, 4)` (a finite
  `float`).
- If `search_total == 0`: `read_to_search_ratio` is the literal string
  `"undefined: zero search_count.total in corpus, cannot compute a ratio without a fabricated denominator"`
  — never `0`, never `null`, never a raised `ZeroDivisionError`.

Rationale (must also appear, condensed, in the derivation string — see Step 1): `search_count`'s
`per_run` and this section's `per_run` are not guaranteed to share an identical key set (a run can
have `Read` calls with zero qualifying searches, or vice versa). A per-`run_id` ratio would force
either a `KeyError` on a missing key, a silent `.get(key, 0)` default that turns a zero-search run
into a `ZeroDivisionError` or an undefined ratio, or an arbitrary skip policy that quietly drops
some runs from the ratio with no disclosure. Computing corpus-wide only avoids all three failure
modes with one well-defined number (or one well-defined string), consistent with the "never a
fabricated or silent number" house convention `build_context_tokens_section`'s `status`/`reason`/
`citation` shape already establishes for the "cannot be computed as asked" case.

### Decision 2 — insertion point

**Confirmed: after `build_legacy_schema_notes` (current lines 157-167), before
`build_baseline_report` (current lines 170-180).** This is the last function before report
assembly. Inserting here means every existing function's line-range citation in `INFRA-292`'s
`v2_evidence` — `:21-29`, `:50-53`, `:56-88`, `:91-154`, `:157-167`'s portion of the combined
`:157-180` citation — stays byte-for-byte unchanged; only the citation covering
`build_baseline_report` itself (currently folded into the same `:157-180` range as
`build_legacy_schema_notes`) needs re-deriving, because `build_baseline_report`'s start line shifts
down by however many lines the new function occupies. No other function's citation shifts.

## Steps

### Step 1 — Add `build_raw_investigation_count_section(tools)`

**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`

**Change:** Insert a new top-level function directly after `build_legacy_schema_notes` (ends at the
line before the current `def build_baseline_report(...)`) and directly before
`build_baseline_report`. No new imports are needed — `defaultdict` is already imported at line 17.

Signature, matching `build_search_count_section(tools: list) -> dict` exactly:

```python
def build_raw_investigation_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") == "Read":
            # Same run_id=None -> "unattributed" convention as build_search_count_section
            # (see that function's inline comment) — reused verbatim, not reinvented.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1

    search_total = build_search_count_section(tools)["total"]
    if search_total > 0:
        ratio = round(total / search_total, 4)
    else:
        ratio = (
            "undefined: zero search_count.total in corpus, cannot compute a ratio "
            "without a fabricated denominator"
        )

    return {
        "derivation": (
            "Derived from tools.jsonl's literal `tool` field, filtered to `tool == \"Read\"` "
            "(the single most common non-Bash tool in this corpus). `Grep` is not counted "
            "because no distinct `Grep` tool name is ever recorded in this environment; "
            "grep-equivalent work runs through the catch-all `Bash` tool, which is excluded "
            "here for the same non-distinguishability rationale documented on "
            "SEARCH_TOOL_NAMES above (some Bash calls are search/grep-flavored by content, "
            "but that is not distinguishable by tool name alone). This section is therefore "
            "a proxy for raw investigation effort (how often the agent had to open a file "
            "directly to look), not a literal grep-call count. read_to_search_ratio is "
            "computed corpus-wide only (this section's total Read count divided by "
            "search_count's total, both derived from this same tools list), never per-run, "
            "because search_count.per_run and this section's per_run do not share an "
            "identical run_id key set in general; if search_count.total is 0 the ratio is "
            "the literal string above instead of a divided-by-zero or fabricated value."
        ),
        "per_run": dict(per_run),
        "total": total,
        "read_to_search_ratio": ratio,
    }
```

**Do NOT touch:** `SEARCH_TOOL_NAMES` (frozenset definition or its comment), `build_search_count_section`'s body (call it, do not modify it), `build_duration_section`, `build_gate_outcome_section`, `build_review_rework_section`, `build_legacy_schema_notes`, `load_all_sources`, `main()`. Do not add a `READ_TOOL_NAMES` constant or any other new module-level frozenset/set — the filter is the single literal comparison `record.get("tool") == "Read"` inline in the loop, exactly as scoped. Do not add a new import or a second `tools.jsonl` read/load call.

**Verify:** `test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent`, `test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`, `test_baseline_report_raw_investigation_count_ratio_never_silent_if_present` (Step 5).

### Step 2 — Wire the new section into `build_baseline_report()`

**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`

**Change:** In `build_baseline_report(runs, events, tools)`'s literal dict, add a new key
immediately after the existing `"search_count": build_search_count_section(tools),` line:

```python
"raw_investigation_count": build_raw_investigation_count_section(tools),
```

Key name is exactly `raw_investigation_count` (matches the ticket's own suggested name and
test_plan.md's example assertions). Do not rename `search_count` or reorder any other existing
key. `"ticket_id"` stays hardcoded to `"TCK-20260728-RETRIEVAL-BASELINE-METRICS"` — do not change
it to this ticket's ID (per investigation.md's explicit note: the script is being extended in
place, not re-scoped to a new ticket identity).

**Do NOT touch:** any other key in the `build_baseline_report` literal dict, its function
signature, or `main()`'s call to it.

**Verify:** `test_baseline_report_raw_investigation_count_wired_into_report`.

### Step 3 — Fix the existing exact-key-set test

**Files:** `tests/tools/test_retrieval_baseline_metrics.py` (lines 236-247,
`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`)

**Change:** Add `"raw_investigation_count"` to the literal set in the existing assertion:

```python
assert set(report.keys()) == {
    "ticket_id", "generated_note", "context_tokens", "search_count", "duration",
    "gate_outcome", "review_rework", "legacy_schema_notes", "raw_investigation_count",
}
```

Keep the `==` (exact-set) comparison — do not loosen it to `<=`/subset per test_plan.md's
Anti-Drift Test Guards (the exact-set design is deliberate, guarding against a future sixth
section being added without this test being updated too).

**Do NOT touch:** the rest of this test function (the `report["ticket_id"]` and
`report["context_tokens"]["status"]` assertions above it), or any other test in this file beyond
what Step 5 adds.

**Verify:** `test_baseline_report_cli_runs_against_real_corpus_and_prints_json` itself (run it; it
must pass, not just be edited).

### Step 4 — Import the new function in the test module

**Files:** `tests/tools/test_retrieval_baseline_metrics.py` (import block, lines 25-35)

**Change:** Add `build_raw_investigation_count_section` to the existing
`from retrieval_baseline_metrics import (...)` block, keeping the list alphabetically ordered as
it currently is:

```python
from retrieval_baseline_metrics import (  # noqa: E402
    SEARCH_TOOL_NAMES,
    build_baseline_report,
    build_context_tokens_section,
    build_duration_section,
    build_gate_outcome_section,
    build_legacy_schema_notes,
    build_raw_investigation_count_section,
    build_review_rework_section,
    build_search_count_section,
    load_all_sources,
)
```

**Do NOT touch:** any other import in this file.

**Verify:** module import succeeds (any test in the file running at all is proof; no dedicated
test needed for an import statement).

### Step 5 — Add the five new tests

**Files:** `tests/tools/test_retrieval_baseline_metrics.py`

**Change:** Insert a new comment-delimited block immediately after the existing AC2 block (ends
after `test_baseline_report_search_count_derivation_matches_stated_fields`, i.e. right before the
`# --- AC3 — phase-duration ... ---` banner), following the file's existing
`# --- ACn — ... ---` banner convention:

```python
# ---------------------------------------------------------------------------
# AC-NEW — raw-investigation (Read) count, derived proxy for grep-equivalent effort
# ---------------------------------------------------------------------------
```

Add all five tests exactly as specified in `test_plan.md`'s "New Tests Required" section:

1. `test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent` — calls
   `build_raw_investigation_count_section([])`; asserts `section["total"]` is `int` (`0`);
   `section["derivation"]` is non-empty and contains `"tool"` and `"Read"`; also contains
   `"Grep"` or `"Bash"`.
2. `test_baseline_report_raw_investigation_count_derivation_matches_stated_fields` — use the exact
   fixture from test_plan.md (7 records mixing `Read`/`Bash`/`Edit`/`mcp__knowledge-search__search_docs`
   across `TCK-A`, `TCK-B`, and `run_id: None`); assert `section["total"] == 4` and
   `section["per_run"] == {"TCK-A": 2, "TCK-B": 1, "unattributed": 1}`.
3. `test_baseline_report_raw_investigation_count_wired_into_report` — build a small inline
   `runs`/`events`/`tools` fixture, call `build_baseline_report(runs, events, tools)`, assert
   `report["raw_investigation_count"] == build_raw_investigation_count_section(tools)`.
4. `test_baseline_report_raw_investigation_count_ratio_never_silent_if_present` — write this test
   against the Decision 1 shape above, not a guessed shape:
   - Case A (`search_total > 0`): construct a `tools` fixture with both `Read` and
     `mcp__knowledge-search__search_docs` records; assert
     `isinstance(section["read_to_search_ratio"], float)` and it equals
     `round(read_total / search_total, 4)` computed by hand from the fixture.
   - Case B (`search_total == 0`, e.g. `tools` has `Read` records only, no `SEARCH_TOOL_NAMES`
     hits): assert `section["read_to_search_ratio"]` is a `str` containing the literal substring
     `"undefined"`, and assert calling the function does **not** raise (no
     `pytest.raises(ZeroDivisionError)` — the test proves the exception never happens by simply
     calling the function directly and asserting on the string return).
5. `test_baseline_report_raw_investigation_count_plausible_on_real_corpus` — call
   `load_all_sources()` then `build_raw_investigation_count_section(tools)` (or read it back out of
   `build_baseline_report(...)`); assert `section["total"]` is `int` and `> 1000` (conservative
   floor, well below the ~18,567 investigation-time figure to tolerate corpus growth/shrinkage —
   do not hardcode 18,567 or any tight range); assert
   `section["total"] == sum(section["per_run"].values())` exactly. Do not assert git-porcelain
   zero-diff in this test (already covered by the existing
   `test_baseline_report_tool_causes_zero_diff_on_real_corpus`, which will exercise the new section
   automatically once it is wired in via Step 2).

**Do NOT touch:** any existing test function's body. Do not weaken
`test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`,
`test_baseline_report_reuses_classify_provenance_not_reimplemented`, or
`test_baseline_report_tool_never_imports_writer_module` — these must stay green unmodified; they
are the guard that the new function reused `tools` instead of adding a loader and never opened a
file for writing.

**Verify:** `pytest tests/tools/test_retrieval_baseline_metrics.py -v` — all tests pass, including
all 3 existing AST reuse guards and the (now-fixed) exact-key-set CLI test from Step 3.

### Step 6 — Update `docs/parity_ledger/infrastructure.yaml` (`INFRA-292`)

**Files:** `docs/parity_ledger/infrastructure.yaml` (entry `INFRA-292`, currently lines 5970-6009)

**Change:**
- `text`: append a clause noting the raw-investigation-count extension, e.g. append after the
  existing sentence: `"Extended by TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC to add a
  raw-investigation (Read-call) count section as a grep-effort proxy, plus a corpus-wide
  read_to_search_ratio derived field."`
- `v2_evidence`: add a new citation clause for `build_raw_investigation_count_section(tools)` at
  its actual post-implementation line range (re-derive the real line numbers after Step 1 lands —
  do not guess/hardcode a number now), noting it is inserted between `build_legacy_schema_notes`
  and `build_baseline_report`, filters `tool == "Read"`, and computes `read_to_search_ratio`
  corpus-wide only via composition with `build_search_count_section`. Re-derive and correct the
  existing combined `:157-180` citation (which currently covers both `build_legacy_schema_notes`
  and `build_baseline_report` together) into two separate, accurate post-insertion line ranges —
  one for `build_legacy_schema_notes` (unchanged), one for `build_baseline_report` (shifted down by
  the new function's line count). Every other existing citation (`:21-29`, `:50-53`, `:56-88`,
  `:91-154`) is unaffected and must be left byte-for-byte as-is.
- Leave `status: verified`, `priority: P2`, `proof_type: regression`,
  `test_path: tests/tools/test_retrieval_baseline_metrics.py`, `divergence_note: null`, and
  `support_boundary` unchanged in kind (this is still read-only agent-tooling infrastructure with
  no simulation-mechanics implication) — `support_boundary`'s prose may be touched only to note the
  new section exists, not to change its meaning.

**Do NOT touch:** any other `INFRA-*` entry in this file, or any other `docs/parity_ledger/*.yaml`
file (investigation.md confirmed `INFRA-292` is the only hit for `retrieval_baseline_metrics`
across all 8 ledgers).

**Verify:** no automated test for prose accuracy — manual re-read of the entry against the final
diff of `retrieval_baseline_metrics.py`, confirming every cited line range is correct post-edit.
This is a Finalize-phase documentation-accuracy check, not a pytest-verified step.

### Step 7 — Update `docs/agent-monitoring/README.md`

**Files:** `docs/agent-monitoring/README.md`

**Change:** This doc currently has zero coverage of `retrieval_baseline_metrics.py`'s report shape
at all (confirmed pre-existing gap, not introduced by this ticket — see investigation.md's Docs
Requiring Update / Gap Found). Add one minimal new subsection — not a rewrite of the file — placed
after the existing `## What It Does NOT Capture` section and before `## Navigation` (i.e. after the
line ending `...Simulation engine telemetry` and the `cost_proxy_score` calibration note, before
the `## Navigation` heading). Content, scoped to a one-liner-plus-list per the ticket's own
instruction ("not a full rewrite"):

```markdown
## Baseline Metrics Snapshot (one-off)

`tools/agent-monitoring/retrieval_baseline_metrics.py` is a separate, one-off/periodic
read-only baseline-snapshot script (distinct from the recurring weekly retro above) that prints a
JSON report over the same `runs.jsonl`/`events.jsonl`/`tools.jsonl` sources. Report sections:
`context_tokens`, `search_count`, `raw_investigation_count`, `duration`, `gate_outcome`,
`review_rework`, `legacy_schema_notes`. Every derived/proxy section states its own computation and
limits inline via a `derivation`/`disclosure`/`reason` field — never a silent number. See
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-292` entry for exact source line-range
provenance of each section.
```

**Do NOT touch:** `## What It Captures`, `## What It Does NOT Capture`'s existing content
(including the `cost_proxy_score` calibration finding paragraph), `## Navigation`, or
`## Quick Start`. Do not add a new `make` target or a new Navigation table row — this script has no
dedicated doc file of its own to link to; the new subsection itself is the documentation.

**Do NOT touch:** `docs/agent-monitoring/schema.md` — investigation.md confirmed that file
documents the 3 JSONL source files' field schemas (not this script's report shape), and is out of
scope; no change needed there.

**Verify:** no automated test; manual read-through confirming the new subsection lists all 7
section keys (matching the final `build_baseline_report` dict) and the placement does not disturb
adjacent sections' Markdown structure.

## Scope Guards

- Do not modify `SEARCH_TOOL_NAMES`, its comment, or `build_search_count_section()`'s body (may
  only be *called*, from within the new function, to obtain `search_total`).
- Do not add a `READ_TOOL_NAMES` (or similarly named) module-level constant/set — the Read filter
  is a single inline `== "Read"` comparison, per the ticket's own scope and investigation.md's
  Anti-Drift Hazards.
- Do not widen the new section's filter to `Edit`/`Write`/any other tool name — `tool == "Read"`
  only.
- Do not add a new data loader, `open()` call, or second read of `tools.jsonl`/any `.jsonl` file —
  the new function takes the already-loaded `tools: list` parameter only.
- Do not invent a second null-key convention (`"none"`, `"null"`, `"n/a"`) — reuse the literal
  string `"unattributed"` exactly as `build_search_count_section` does.
- Do not change the hardcoded `"ticket_id": "TCK-20260728-RETRIEVAL-BASELINE-METRICS"` value inside
  `build_baseline_report`.
- Do not wire this metric into `generate_retro.py`'s weekly retro cadence (explicitly out of
  scope — sibling recurring-cadence tool, untouched).
- Do not touch the `expansion_rate` wiring (tracked separately as
  TCK-20260804-EXPANSION-RATE-WIRING).
- Do not touch `docs/ai/default_packet_scenarios_decision.md` or
  `docs/ai/shadow_promotion_gate_thresholds_decision.md` — both cite `search_count` values as
  already-shipped policy inputs; this ticket does not change `search_count`'s values or shape, so
  neither doc needs an edit.
- Do not loosen `test_baseline_report_cli_runs_against_real_corpus_and_prints_json`'s `==`
  exact-key-set assertion to a subset (`<=`) check.
- Do not modify any `docs/parity_ledger/*.yaml` file other than `infrastructure.yaml`'s `INFRA-292`
  entry, and do not touch any other entry within that file.
- Do not rewrite `docs/agent-monitoring/README.md` beyond the one new subsection specified in
  Step 7; do not touch `docs/agent-monitoring/schema.md`.

## Dependency Map

- Step 1 must land before Steps 2, 3, 4, 5 (they all reference
  `build_raw_investigation_count_section`).
- Step 2 must land before Step 3's test can pass (the key must exist in the report before the
  exact-set assertion can include it) and before Step 5's test #3 (`..._wired_into_report`) can
  pass.
- Steps 3 and 4 are independent of each other but both depend on Step 1; both should land before
  running the full test file so import errors don't mask the Step 3 assertion fix.
- Step 5 depends on Step 1 (and, for test #3 only, Step 2).
- Step 6 depends on Step 1 and Step 2 being finalized (needs real post-edit line numbers).
- Step 7 depends on Step 2 (needs the final 7-key section list to enumerate).
- Steps 6 and 7 are independent of each other and can be done in either order, both last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `build_raw_investigation_count_section()` exists, follows `build_search_count_section()` pattern, wired into report | Steps 1, 2 | `test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent`, `test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`, `test_baseline_report_raw_investigation_count_wired_into_report` |
| AC2 — `derivation` explains Read-as-proxy choice and Grep/Bash non-distinguishability reason | Step 1 | `test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent` |
| AC3 — new tests pass, mirroring never-silent / derivation-matches pattern | Step 5 | all 5 new tests in `tests/tools/test_retrieval_baseline_metrics.py` |
| AC4 — real corpus run produces non-trivial, plausible Read count (order of magnitude ~18,567) | Steps 1, 2 | `test_baseline_report_raw_investigation_count_plausible_on_real_corpus` |
| AC5 — relevant docs updated | Steps 6, 7 | manual review (no automated doc-content test) |
| (Ticket Scope bullet 4) — `read_to_search_ratio` computed without silent assumptions, or explicitly omitted with reason | Step 1 (Decision 1) | `test_baseline_report_raw_investigation_count_ratio_never_silent_if_present` |
| (Regression) existing exact-key-set test must not go red | Step 3 | `test_baseline_report_cli_runs_against_real_corpus_and_prints_json` |

## Anti-Drift Notes

- The corpus-wide-only `read_to_search_ratio` design (Decision 1) is deliberate and must not be
  changed to per-run without re-litigating the key-mismatch/division-by-zero problem investigation.md's
  Risk #2 raised — a per-run version reintroduces exactly the hazard this plan resolved.
- `build_raw_investigation_count_section` calling `build_search_count_section` internally is
  intentional function composition, not a violation of the "no new loader" rule — the "no new
  loader" guard (enforced by `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`'s
  AST walk) is about `.read_text()`/`.read_bytes()`/`.readlines()`/`sqlite3` calls, not about
  calling another already-defined function in the same module. Confirm this reasoning holds if the
  AST guard test ever needs re-reading during implementation.
- The two `docs/ai/*_decision.md` files citing live `search_count` numbers are read-only concerns
  for this ticket (see Scope Guards) — their existence is a reason to be careful not to touch
  `search_count`'s output at all, not a reason to update those docs.
- `INFRA-292`'s `v2_evidence` line ranges are precise, verified citations elsewhere in this repo's
  parity discipline — Step 6 explicitly requires re-deriving real post-edit line numbers rather than
  estimating, to avoid shipping a newly-stale citation in the same change that was meant to fix
  staleness.
- Investigation.md's Risk #5 precedent (from the original baseline ticket) applies again here: any
  specific count cited in this plan or in tests (~18,567, `> 1000` floor) is illustrative and
  should be re-measured at implementation time, never hardcoded as an exact expected value in a
  real-corpus test.

## Deviations

- **Decision 2's claim "No other function's citation shifts" was inaccurate for `def main()`.**
  Decision 2 only reasoned about the `:157-180` combined citation (covering
  `build_legacy_schema_notes` + `build_baseline_report`) needing to split, and asserted every
  other citation — `:21-29`, `:50-53`, `:56-88`, `:91-154` — stays byte-for-byte unchanged. It did
  not account for the pre-existing `:183-196 (def main() ...)` citation in `INFRA-292`'s
  `v2_evidence`, which sits *after* the insertion point in the file and therefore also shifted
  (post-implementation, `main()` is at `:227-240`, with the `_assert_safe_output_path` call moving
  from `:193` to `:237`). Left as `:183-196` this citation would have become exactly the kind of
  stale line-range the ticket exists to prevent. Implement therefore also re-derived and corrected
  the `main()` citation to `:227-240` (and `:193` to `:237` inline) in Step 6, in addition to the
  two splits Decision 2 called for (`build_legacy_schema_notes` at `:157-167` unchanged,
  `build_baseline_report` at `:213-224`) and the new `build_raw_investigation_count_section`
  citation at `:170-210`. No other citation (`:21-29`, `:50-53`, `:56-88`, `:91-154`) was touched,
  consistent with Decision 2's core intent (minimize churn), just not its literal "no other
  citation shifts" wording.
