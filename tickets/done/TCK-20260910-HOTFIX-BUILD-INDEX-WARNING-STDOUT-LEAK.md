---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK
phase: done
date: 2026-09-10
tags: [ai, agent-monitoring]
---

# TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK

## Title
`tools/agent-monitoring/build_index.py`'s WARNING lines print to stdout instead of stderr, breaking JSON-output CLI contracts

## Status
DONE

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

**Corrected 2026-09-13, before implementing: the ticket's own claim of "3" affected print calls is
partly stale.** Re-checked the current code before touching anything: both `WARNING:` prints
(non-canonical tier, missing run_id/seq/tool) **already have `file=sys.stderr`** — someone fixed
those two independently of this ticket, without closing it. The one remaining defect is narrower
than filed: `build()`'s own final summary print (`f"runs: {n_runs} rows, ..."`, still the same
line the ticket names) is the only call left writing unconditionally to stdout, and it is exactly
the one that fires on every rebuild through `generate_retro.py`'s lazy-rebuild path — including the
path `retrieval_baseline_metrics.py` triggers, so it's still the real, live cause of the described
test failure.

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
- [x] `build_index.py`'s WARNING/summary print statements route to stderr, not stdout. **2 of 3
      already did** (re-verified); the remaining summary print now does too.
- [x] `pytest tests/tools/test_retrieval_baseline_metrics.py -v` passes with the index forced
      stale (not just a lucky fresh-index run) — verified by touching `monitoring.db` to predate
      the JSONL sources, forcing a real rebuild. 20/20 passed.
- [x] `pytest tests/tools/test_build_index.py -v` still passes in full (21/21) — no test asserted
      stdout capture of the summary line; the one test touching CLI output (`test_makefile_dry_run_
      agent_monitoring_index`) checks combined stdout+stderr, unaffected.
- [x] No change to warning content/wording — stream destination only.

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
Re-checked the code before implementing, per standing practice — found the ticket's own "3 print
calls need fixing" claim partly stale: the two `WARNING:` prints already had `file=sys.stderr`.
Only `build()`'s final summary print (`f"runs: {n_runs} rows, ..."`) still wrote unconditionally
to stdout. Added `file=sys.stderr` to that one remaining call — no wording change.

## Test Summary
- `tests/tools/test_build_index.py`: 21/21 passed.
- `tests/tools/test_retrieval_baseline_metrics.py`: 20/20 passed, including the target test, run
  with the SQLite index deliberately staled (`touch -d "1 hour ago" agent-monitoring-index/
  monitoring.db`) to force a real rebuild through `generate_retro.py`'s lazy-rebuild path — not a
  lucky fresh-index run.

## Files Changed
- `tools/agent-monitoring/build_index.py` — final summary print now routes to stderr.
- `tickets/inprogress/TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK.md` — corrected the
  ticket's own stale "3 calls" claim before closing.

## Completion Summary
Mechanical fix, exactly as filed once the stale part of the claim was corrected: one remaining
`print()` call routed to stderr. No design judgment involved.
