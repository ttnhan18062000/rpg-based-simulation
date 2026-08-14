---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC
artifact_type: investigation
tags: [agent-monitoring, observability]
---

# Investigation — TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC

## Current Behavior

### `tools/agent-monitoring/retrieval_baseline_metrics.py` — full read

This is a strictly read-only, one-off baseline-snapshot script (distinct from `generate_retro.py`'s
recurring weekly cadence — see its module docstring, lines 1-13). It never writes into
`agent-monitoring/` itself; it prints a JSON report to stdout and optionally mirrors it to a
`--output` path guarded by `manifest.py`'s `_assert_safe_output_path()` (line 29, called at
line 193).

**Imports (lines 20-29):** everything it needs is reused, not reimplemented — `DEFAULT_TOOLS_FILE`,
`_is_gate_fail`, `_load_runs_and_events`, `_resolve_status`, `load_jsonl` from `generate_retro.py`;
`classify_provenance` from `legacy_reader.py`; `_assert_safe_output_path` from `manifest.py`.

**`SEARCH_TOOL_NAMES` (lines 36-40):**
```python
SEARCH_TOOL_NAMES = frozenset({
    "mcp__knowledge-search__search_docs",
    "ToolSearch",
    "WebSearch",
})
```
The comment directly above it (lines 31-35) is the precedent this ticket's scope cites verbatim:
"Bash is excluded even though some Bash calls have search-flavored input_summary text, since that
is not distinguishable by tool name alone and this metric must stay precise, not inflated." This is
the exact non-distinguishability rationale the new section's derivation string must restate for
why `Grep`/Bash-as-grep is not counted.

**`build_search_count_section(tools: list) -> dict` (lines 65-88)** — the exact structural pattern
this ticket must mirror:
```python
def build_search_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") in SEARCH_TOOL_NAMES:
            # tools.jsonl records issued outside any workflow run carry run_id=None
            # (legacy_reader.py's "interactive_null" shape) — grouped under a literal
            # "unattributed" key rather than None, since a None dict key breaks
            # json.dumps(sort_keys=True)'s key comparison against the str keys of real runs.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1
    return {
        "derivation": "Derived from tools.jsonl's literal `tool` field, filtered to "
                      "SEARCH_TOOL_NAMES = {...}. ...",
        "per_run": dict(per_run),
        "total": total,
    }
```
Structural elements to mirror exactly:
1. `per_run: dict = defaultdict(int)` keyed by `run_id` (or literal `"unattributed"` — never `None`,
   because `json.dumps(..., sort_keys=True)` cannot compare a `None` key against `str` keys — this
   bit the report exactly once already, documented inline at lines 70-73).
2. A single `total` int accumulator.
3. Single pass over the `tools: list` parameter (no re-reading a file — the caller already loaded
   it via `load_jsonl`/`_load_runs_and_events`).
4. Return dict shape: `{"derivation": <str>, "per_run": <dict>, "total": <int>}` — `derivation` is
   mandatory and always present (never a silent/absent key), matching the "never a fabricated or
   silent number" house convention documented in this same file's `build_gate_outcome_section`
   (`"disclosure"` key, lines 121-122) and `build_review_rework_section` (`"disclosure"` key, lines
   151-153) — those two use the key name `disclosure` instead of `derivation`; `search_count` is the
   literal precedent to mirror per the ticket's own instruction, so `derivation` is the correct key
   name for the new section, not `disclosure`.
5. The derivation string cites the exact filter set by name (`SEARCH_TOOL_NAMES`) and explains *why*
   the derivation is more precise than a coarser alternative — the new section's derivation should
   follow the same "cite the literal field + constant name, then justify the choice" shape.

### Report assembly — `build_baseline_report(runs, events, tools) -> dict` (lines 170-180)

```python
def build_baseline_report(runs: list, events: list, tools: list) -> dict:
    return {
        "ticket_id": "TCK-20260728-RETRIEVAL-BASELINE-METRICS",
        "generated_note": "one-off baseline snapshot — not the recurring weekly retro cadence",
        "context_tokens": build_context_tokens_section(),
        "search_count": build_search_count_section(tools),
        "duration": build_duration_section(runs),
        "gate_outcome": build_gate_outcome_section(runs),
        "review_rework": build_review_rework_section(runs),
        "legacy_schema_notes": build_legacy_schema_notes(runs, events, tools),
    }
```
This is a flat dict literal, each value a call to one `build_*_section()` function. `main()`
(lines 183-196) calls `build_baseline_report(runs, events, tools)` once, then
`json.dumps(report, indent=2, sort_keys=True) + "\n"`, writes to stdout always, and to `--output`
only if provided (after the safety-path assertion). The new
`build_raw_investigation_count_section(tools)` (per the ticket's own function name) must be added
as a new key in this literal dict, alongside `"search_count": build_search_count_section(tools)` —
both consume the same `tools` list parameter already in scope, so no new loader/parameter is
needed.

**Important:** `"ticket_id"` is hardcoded to `"TCK-20260728-RETRIEVAL-BASELINE-METRICS"` (line 172)
— the *original* baseline ticket, not a field this new ticket should change (the script is not
being re-scoped to a new ticket identity; it is being extended in place, consistent with the
Related Tickets framing of this ticket as an extension of, not a fork from, TCK-20260728).

### Frontmatter / derivation-string conventions used elsewhere in the file

- `build_context_tokens_section()` (56-62): uses `"status"`/`"reason"`/`"citation"` keys, not
  `"derivation"` — a different shape for a different situation ("this metric cannot be computed at
  all" vs. "this metric is computed but needs its provenance stated").
- `build_gate_outcome_section()` (109-123) and `build_review_rework_section()` (126-154): use
  `"disclosure"` (not `"derivation"`), always containing the literal substring `"derived proxy"` and
  `"not fabricated"` (see the corresponding tests below) — a second, distinct convention name for
  the same "never silent" intent.
- `build_duration_section()` (91-106): uses a per-row `"flag"` + `"note"` pair instead of a
  section-level derivation/disclosure string — the note explicitly names the missing module
  (`duration_utils.py`) that would replace the flag if it existed.
- `build_legacy_schema_notes()` (157-167): uses a plain `"note"` key.

Net: there is no single universal key name across all sections — each section's "never silent"
marker key name matches its own established precedent. Since the ticket explicitly names
`build_search_count_section()` as the structural precedent to mirror, and that function uses
`"derivation"`, the new section should also use `"derivation"` (not `"disclosure"` or `"note"`) to
stay consistent with the specific sibling it is modeled on.

## Mechanics / Engine Constraints

N/A — this ticket touches agent-tooling observability infrastructure
(`tools/agent-monitoring/retrieval_baseline_metrics.py`, `agent-monitoring/tools.jsonl`), not
simulation mechanics. No chapter of `docs/mechanics/` or contract in `docs/engine/` governs this
area — same finding as `stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/investigation.md`'s
own "Mechanics / Engine Constraints" section for the identical code area, and
`stored_artifacts/TCK-20260721-BASELINE-MONITORING-MANIFEST/investigation.md` before it.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: entry `INFRA-292`'s `v2_evidence` field cites exact line
  ranges of `retrieval_baseline_metrics.py` for each `build_*_section()` function and for
  `build_baseline_report()`'s assembly (lines 5982-5997) — this entry must be updated with the new
  `build_raw_investigation_count_section()` function's line range and its inclusion in
  `build_baseline_report()`'s literal dict once implemented, exactly the same class of update the
  parity ledger requires for any behavior/interface change to code an existing entry's `v2_evidence`
  already cites verbatim.
- `docs/agent-monitoring/README.md`: the ticket's own "Related Docs" names this as the candidate
  location for documenting `retrieval_baseline_metrics.py`'s output shape. As read in full (see Gap
  below), it currently documents `runs.jsonl`/`events.jsonl`/`tools.jsonl` schema and the weekly
  retro cadence only — it does not describe this one-off script's report sections today. Adding one
  sentence noting the script's existence and its section list (including the new one) keeps this
  doc from silently going stale the way the ticket's own Related Docs entry anticipates.

**Gap found:** neither `docs/agent-monitoring/README.md` nor `docs/agent-monitoring/schema.md`
currently documents `retrieval_baseline_metrics.py`'s *report output shape*
(`context_tokens`/`search_count`/`duration`/`gate_outcome`/`review_rework`/`legacy_schema_notes`)
at all — `schema.md` documents the 3 JSONL source files' own field schemas (and, incidentally,
enumerates `tool` values including `Read` at line 361: "Tool name: `Read`, `Edit`, `Write`, `Bash`,
`Agent`, `MultiEdit`, etc." — confirming `Read` is a real, distinctly-recorded value in that
enumeration, consistent with this ticket's premise). The *only* place in `docs/` that documents this
script's exact output shape today, at the level of individual section names and line-range
provenance, is the parity ledger's `INFRA-292` `v2_evidence` field
(`docs/parity_ledger/infrastructure.yaml:5970-6009`). This is a real, pre-existing documentation gap
(not introduced by this ticket) — README.md's "Related Docs" pointer in the ticket is a reasonable
place to close it, but it was never true that README.md already described this script's sections;
this investigation flags it explicitly rather than silently treating the ticket's "if it documents
baseline-metrics output" conditional as already-satisfied.

`docs/ai/default_packet_scenarios_decision.md` and `docs/ai/shadow_promotion_gate_thresholds_decision.md`
both cite `search_count.total`/`search_count.per_run` numbers from a live run of this script as
policy-decision inputs (see Anti-Drift Hazards below) — neither needs a content update from this
ticket (the ticket does not change `search_count`'s values or shape), but both are real downstream
consumers of this script's stdout shape and are listed here for completeness/traceability, not as
required edits.

## Parity Ledger Overlap

- **`INFRA-292`** (`docs/parity_ledger/infrastructure.yaml:5970-6009`), `status: verified`,
  `priority: P2`. Text: "New read-only baseline-metrics reporting tool over
  agent-monitoring/*.jsonl (context-tokens, follow-up-search-count, phase-duration, gate-outcome,
  review-rework) -- TCK-20260728-RETRIEVAL-BASELINE-METRICS." `test_path`:
  `tests/tools/test_retrieval_baseline_metrics.py` — **confirmed to exist** (this file was read in
  full for this investigation). `proof_type: regression`. Not `P0`, so no mandatory
  passing-test-path gate beyond the existing regression suite, but the entry's `v2_evidence` is
  stale the moment this ticket's new function lands (it currently cites only the 5 original
  sections), so it needs updating per the Docs Requiring Update section above — this is a
  same-session parity-ledger update, per the Authoritative Mechanics Rule's "if logic changes,
  update the corresponding doc AND the parity ledger entry in the same session," even though this
  entry sits outside the 8 subsystem-specific ledgers (it is process/infra-tooling, not simulation
  mechanics, but `infrastructure.yaml` is still the correct file per the existing INFRA-281 through
  INFRA-291 precedent for this class of change).
- No `P0` parity entries anywhere touch this ticket's scope (confirmed: `INFRA-292` is the only hit
  for `retrieval_baseline_metrics` across all 8 `docs/parity_ledger/*.yaml` files).

## Prior Work

- **`stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/`** (investigation.md, plan.md,
  test_plan.md — investigation.md read in full): the original ticket that built this script. Its
  investigation.md already surfaced, and left as an explicit open question, the exact same
  Grep/Bash-non-distinguishability finding this ticket's Request Summary restates ("`Grep` never
  appears as a distinct `tool` value... even search-flavored Bash calls are indistinguishable from
  any other Bash call by tool name alone" — see that investigation's "Real corpus data checked
  directly" section, lines 123-134 of that file). This ticket's Read-as-proxy design is a direct,
  consistent continuation of that finding, not a new independent discovery.
- That same investigation's Risk #2 (`stored_artifacts/TCK-20260728-.../investigation.md`, lines
  255-267) already flagged that `search_count`'s derivation (filtering `tools.jsonl` by literal
  `tool` value) was the "more precise" option chosen over a coarser `tool_call_count`-based
  alternative — the new `build_raw_investigation_count_section()` should follow the same
  "filter by literal `tool` field" precision discipline (filtering to `tool == "Read"`), not fall
  back to a coarser proxy.
- No other stored artifact or done ticket computes a Read-count or raw-investigation-effort metric —
  confirmed via `docs/REGISTRY.yaml` tag/title scan for `agent-monitoring`/`observability`/
  `retrieval`/`baseline` (105 matching entries reviewed by title/tag; none mention Read-count,
  grep-proxy, or raw-investigation-effort) and via a direct grep of `docs/plans/agent_infrastructure/`
  and `docs/ai/` for "raw investigation"/"grep-style"/"Read...proxy" (zero hits). This is genuinely
  new reporting logic, consistent with the ticket's own "Assumptions / Open Questions: None."

## Risks and Open Questions

1. **`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`
   (`tests/tools/test_retrieval_baseline_metrics.py:236-247`) asserts an exact report key set**
   (`set(report.keys()) == {"ticket_id", "generated_note", "context_tokens", "search_count",
   "duration", "gate_outcome", "review_rework", "legacy_schema_notes"}`). Wiring the new section
   into `build_baseline_report()` will make this assertion fail until the test itself is updated to
   include the new key. This is an **existing test requiring modification**, not just new tests to
   add — flagged explicitly so it is not missed as "just add tests" scope creep in the wrong
   direction (silently leaving this test red).
2. **The optional `read_to_search_ratio` field (ticket Scope, 4th bullet) has a real division-by-zero
   / mismatched-key-set risk** the ticket itself anticipates ("only if it can be computed without
   silent assumptions — otherwise state explicitly in the derivation why it's omitted"). `per_run`
   for `search_count` and the new Read section will not have identical key sets in general (a run
   with Read calls but zero qualifying searches, or vice versa) — a naive `read_count / search_count`
   per run_id would either KeyError or require a silent `.get(key, 0)` default that makes a
   zero-search run's ratio `ZeroDivisionError` or an arbitrarily large/undefined number. This is a
   genuine open design question for the Plan phase, not resolved here — do not assume either "corpus-
   wide only" or "per-run with skip-on-zero" without the plan making that call explicitly and stating
   it in the derivation string, consistent with the ticket's own instruction.
3. **The `INFRA-292` parity ledger entry's `v2_evidence` line-range citations will shift** once the
   new function is inserted into the file (functions after the insertion point will have new line
   numbers) — the Plan/Implement phase should either insert the new function at the end (after
   `build_legacy_schema_notes`, before `build_baseline_report`) to minimize churn to existing citation
   line ranges, or accept that the parity update must re-verify every existing line-range citation in
   the entry, not just add a new one. This is a mechanical risk, not a design question, but worth
   flagging since a stale `v2_evidence` line range is exactly the class of silent drift this repo's
   parity ledger exists to prevent.
4. **No blocking open question found** — the ticket's own "Assumptions / Open Questions: None" is
   confirmed accurate by this investigation; the two items above are Plan-phase design decisions
   with a clearly bounded solution space, not missing-information blockers.

## Anti-Drift Hazards

- **Do not touch `SEARCH_TOOL_NAMES` or `build_search_count_section()`.** The ticket's Out of Scope
  explicitly forbids this, and two other docs (`docs/ai/default_packet_scenarios_decision.md`,
  `docs/ai/shadow_promotion_gate_thresholds_decision.md`) cite specific `search_count.total`/
  `search_count.per_run` numeric values from a live run of this script as inputs to already-decided
  policy thresholds (e.g. "corpus-wide median currently 3 (n=122)," "`search_count.total = 1738`")
  — changing `search_count`'s filter set or grouping logic would silently invalidate those already-
  shipped decisions' cited evidence.
- **Do not reimplement the `run_id` → `"unattributed"` null-key-avoidance pattern differently.** It
  exists specifically because `json.dumps(..., sort_keys=True)` cannot compare a `None` key against
  `str` keys (see `build_search_count_section`'s inline comment, lines 70-73, and
  `build_gate_outcome_section`'s identical rationale for its `"MISSING_STATUS"` key, lines 110-113).
  The new section must reuse the literal string `"unattributed"` for the same `run_id`-is-`None`
  case, not invent a second convention (e.g. `"none"`, `"null"`, `"n/a"`).
- **Do not silently coerce a missing/absent `derivation`/ratio field to `0` or omit it.** The ticket's
  own AC2 requires the derivation to explicitly state the Grep/Bash non-distinguishability reasoning
  every time — a shortened or paraphrased derivation string that drops the "why Grep is not counted"
  clause would satisfy "a derivation key exists" without satisfying the actual AC intent.
  `build_context_tokens_section`'s own precedent (an entire dedicated `"status": "unavailable"` +
  `"reason"` + `"citation"` shape, not just a bare `null`) is the house style to match if the ratio
  ends up omitted rather than computed.
- **Do not widen the new section's filter beyond literal `tool == "Read"`.** It would be tempting to
  also count `Edit`/`Write`/`Grep`-shaped Bash calls as "investigation effort," but that conflates
  investigation (reading to find something) with modification (`Edit`/`Write`) or the already-
  excluded, non-distinguishable Bash-as-grep case — precisely the imprecision `SEARCH_TOOL_NAMES`'s
  own Bash-exclusion rationale was designed to avoid on the search side. Scope explicitly says
  `tool == "Read"` only.
- **Do not add a new data loader.** `tools` is already loaded once by `load_all_sources()` /
  `main()` and passed into every section builder that needs it (`build_search_count_section(tools)`,
  `build_legacy_schema_notes(runs, events, tools)`); the new
  `build_raw_investigation_count_section(tools)` must take the same already-loaded `tools: list`
  parameter, never call `load_jsonl`/open a file itself.
