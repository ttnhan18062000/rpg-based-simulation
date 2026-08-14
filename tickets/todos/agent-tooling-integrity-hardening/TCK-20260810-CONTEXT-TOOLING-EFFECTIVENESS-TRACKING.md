---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
phase: open
date: 2026-08-10
tags: [agent-monitoring, observability, process-improvement]
---

# TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING

## Title
Track, on a recurring cadence, whether context-search (`search_docs`/`graphify`) and parity-index
sqlite queries actually reduce raw investigation effort

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User asked to track whether context-search tooling and parity sqlite queries "improve the
working" (e.g. reduce grep/raw-investigation calls). `TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC`
already answered the measurement-design question: this environment records no distinct `Grep` tool
name (grep-equivalent work runs through the catch-all `Bash` tool, which
`retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design deliberately excludes from
search-tool counting as non-distinguishable). It built `raw_investigation_count` (`Read`-call count,
the precise proxy) and a corpus-wide `read_to_search_ratio` in
`tools/agent-monitoring/retrieval_baseline_metrics.py` — real numbers, last observed
`raw_investigation_count.total = 18594`, `search_count.total = 1924`, `read_to_search_ratio = 9.66`.
That ticket explicitly scoped OUT wiring the metric into the recurring weekly retro
(`generate_retro.py`), calling it "a separate, recurring-cadence tool" — so today it only exists as
a manual one-off run, with no trend visibility and no correlation to actual compliance behavior.

Separately, `tools/parity_index.py`'s `entry`/`impact`/`health` sqlite read path (reviewed GO in
`docs/ai/parity_readpath_gate_a_decision.md`) has **zero real call sites** anywhere — nothing
tracks its usage because nothing calls it yet.

## Scope
- **Investigate (mandatory before Plan):** read `retrieval_baseline_metrics.py`'s current section
  structure (`build_search_count_section`, `build_raw_investigation_count_section`) and
  `generate_retro.py`'s existing report-assembly pattern (`compute_tool_safety_metrics`'s
  `search_before_grep` section is the closest existing precedent: per-`(run_id, seq)` compliance
  keyed off real `events.jsonl` phase data) before designing anything new.
- Wire `raw_investigation_count`/`search_count`/`read_to_search_ratio` (or an equivalent computed
  directly in `generate_retro.py`, reusing rather than duplicating `retrieval_baseline_metrics.py`'s
  logic) into the recurring report, trended report-over-report (comparable across `RETRO-<week>.md`
  runs, the way `Gate Failure Breakdown`/`Agent Status Distribution` already are).
- Add a genuine correlation section: for each Investigate-phase `(run_id, seq)` pair already
  computed by `compute_tool_safety_metrics`'s `per_pair_compliance`, compute that pair's own
  `Read`-call count, then report compliant-pair vs. non-compliant-pair `Read`-count
  median/average — real evidence for or against "does search-before-grep compliance actually
  reduce raw investigation effort," not an assumed causal story.
- Add a `parity_index.py` read-path call-count section (`entry`/`impact`/`health` invocations),
  following the exact same "never a silent/fabricated number" convention as the existing sections
  — today this must explicitly report 0 real call sites with a derivation string stating why
  (nothing wired in yet), not omit the section or fake a value. Design it so it activates
  automatically once `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` or any future ticket adds a
  real call site — do not hardcode a "not implemented" bypass that would need a second ticket to
  remove.
- Update `docs/agent-monitoring/README.md` and/or `docs/agent-monitoring/schema.md` describing the
  new section(s).

## Out of Scope
- Any change to `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design or
  Bash-exclusion rationale — reused, not revisited.
- Wiring `parity_index.py`'s read path into any actual workflow call site — that is
  `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`'s adjacent-but-separate concern (write safety) or
  a future, separately-scoped Phase-3 ticket (read-path wiring) per Gate A's own boundary; this
  ticket only tracks call counts once/if such a site exists.
- Backfilling a correlation number for historical weeks predating this ticket's own code landing —
  the correlation section reports from real data going forward, not a fabricated retroactive claim.

## Acceptance Criteria
- [ ] A real `generate_retro.py` run against the current corpus produces the new trended
      search/read-investigation section with real, non-fabricated numbers.
- [ ] The compliant-vs-non-compliant `Read`-count correlation section produces a real number from
      real `(run_id, seq)` pairs already in the corpus (the 65 Investigate pairs / 27 non-compliant
      ones identified during this ticket's originating audit are available as a real first data
      point).
- [ ] The `parity_index.py` call-count section exists, explicitly reports 0/N call sites today with
      a derivation string explaining why, and requires no further code change to start reporting
      real numbers once a call site exists.
- [ ] Every new section has a `"derivation"` (or equivalent) string, matching the existing
      never-silent convention used by `search_count`/`raw_investigation_count`.
- [ ] New tests mirror the existing `test_retrieval_baseline_metrics.py`/`generate_retro.py` test
      patterns (never-silent, derivation-matches-fields, real-corpus zero-diff where applicable).
- [ ] `docs/agent-monitoring/README.md`/`schema.md` updated.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (DONE; predecessor metric, this ticket wires it
  into the recurring cadence that ticket explicitly deferred)
- TCK-20260804-EXPANSION-RATE-WIRING (DONE; sibling wiring precedent, same user request thread)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (sibling; this ticket's correlation section is
  how that fix's real-world effect becomes visible)
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (sibling; potential future source of real
  `parity_index.py` call sites this ticket's section is built to pick up automatically)
- TCK-20260731-PARITY-READPATH-GATE (DONE; source of the `entry`/`impact`/`health` read path)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (backlog; broader retrieval epic, not a duplicate)

## Related Docs
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- `docs/ai/parity_readpath_gate_a_decision.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/`

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/parity_index.py`
- `tests/tools/test_generate_retro.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
- Whether the correlation section belongs in `generate_retro.py` directly (reusing
  `compute_tool_safety_metrics`'s already-computed `per_pair_compliance`) or as a new function in
  `retrieval_baseline_metrics.py` that `generate_retro.py` then calls — not decided here; Investigate
  should follow whichever file already owns the relevant per-pair data without duplicating a second
  loader, matching this codebase's existing anti-duplication test precedent (e.g.
  `test_baseline_report_tool_reuses_load_data_pattern_not_a_fourth_loader`).

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
