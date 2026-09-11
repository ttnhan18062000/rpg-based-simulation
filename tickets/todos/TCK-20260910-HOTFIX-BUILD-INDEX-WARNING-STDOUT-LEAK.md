---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK
phase: open
date: 2026-09-10
tags: [ai, agent-monitoring]
---

# TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK

## Title
`tools/agent-monitoring/build_index.py`'s WARNING lines print to stdout instead of stderr, breaking JSON-output CLI contracts

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found incidentally while independently re-verifying `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s
test results (unrelated to that ticket's own diff — zero file overlap, confirmed via `git status`).

`tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_cli_runs_against_real_corpus_and_prints_json`
runs `tools/agent-monitoring/retrieval_baseline_metrics.py` as a subprocess and asserts
`json.loads(result.stdout)` parses cleanly. This fails consistently (confirmed via 2 repeated
isolated runs, not a flake) whenever the derived agent-monitoring SQLite index is stale relative
to its JSONL sources — which happens routinely on any actively-used session, since every tool call
appends to `agent-monitoring/data/*/tools.jsonl`.

Root cause: `retrieval_baseline_metrics.py` imports `load_data_glob`/related loaders from
`tools/agent-monitoring/generate_retro.py`. `generate_retro.py::_load_runs_and_events()`
(lines ~104-140) checks `_index_is_stale()` and, if true, lazily imports `build_index` and calls
`build_index.build(...)` to rebuild it on demand. `build_index.py`'s own `print(f"WARNING: ...")`
calls (lines 118, 162, 204) have no `file=` argument, so they default to **stdout** — inconsistent
with `generate_retro.py`'s own equivalent warning at line 138, which correctly uses
`file=sys.stderr`. These warnings (reporting genuinely pre-existing malformed/non-canonical legacy
records elsewhere in the monitoring corpus, e.g. records dating back to 2026-06-28 — not anything
wrong with *current* data) leak into any CLI built on top of this loading path that assumes pure
JSON on stdout, corrupting `retrieval_baseline_metrics.py`'s own contract.

## Scope
- Change `tools/agent-monitoring/build_index.py`'s 3 `print(f"WARNING: ...")` calls (lines 118,
  162) and the final summary print (line 204, `print(f"runs: {n_runs} rows, ...")`) to route to
  stderr (`file=sys.stderr`), matching `generate_retro.py`'s own established convention for
  identical-purpose warnings.
- Re-verify `tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_cli_runs_against_real_corpus_and_prints_json`
  passes cleanly with the index in a genuinely stale state (force a rebuild, don't just get lucky
  with a fresh index).
- Check `tools/agent-monitoring/build_index.py`'s own test suite (if one exists) for any assertion
  that currently expects these lines on stdout — update if so, since this is a deliberate behavior
  change (verify no test currently asserts stdout capture of these specific lines before treating
  it as a pure bug fix with no test-visible current dependency).

## Out of Scope
- Investigating or fixing the underlying pre-existing malformed/non-canonical legacy records
  themselves (the `non-canonical tier`/`missing run_id/seq/tool` warnings) — those are a separate,
  much older data-quality question, not this ticket's concern. This ticket is only about which
  stream (stdout vs stderr) the warnings print to.
- Any change to `tools/agent-monitoring/retrieval_baseline_metrics.py` or
  `tools/agent-monitoring/generate_retro.py`'s own logic — the fix is scoped to `build_index.py`'s
  print destinations only.
- Any change to `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` or its own scope — this ticket is
  purely a byproduct finding from that ticket's own independent test re-verification, unrelated to
  the Knowledge Gateway MCP.

## Acceptance Criteria
- [ ] `build_index.py`'s 3 WARNING/summary print statements route to stderr, not stdout.
- [ ] `pytest tests/tools/test_retrieval_baseline_metrics.py -v` passes with the index forced
      stale (not just a lucky fresh-index run).
- [ ] `pytest tests/tools/test_build_index*.py -v` (if such a test file exists) still passes in
      full — confirm no test currently depends on these lines appearing on stdout before making
      the change.
- [ ] No change to warning content/wording — stream destination only.

## Related Tickets
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (done) — the ticket whose own independent
  post-Implement re-verification surfaced this finding; zero functional relationship otherwise.

## Related Docs
None identified yet — check at Implement time whether any `docs/agent-monitoring/` doc describes
`build_index.py`'s CLI output contract and would need a matching update.

## Related Stored Artifacts
None — hotfix tier, self-evident intent per project convention.

## Related Code Areas
- `tools/agent-monitoring/build_index.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
- Assumed this is a pure bug fix (warnings belong on stderr, not stdout, by the same convention
  `generate_retro.py` itself already follows) rather than an intentional design choice — no
  comment or docstring anywhere claims these lines are meant to be captured on stdout. Verify this
  assumption holds (no hidden stdout-scraping consumer) before implementing.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
