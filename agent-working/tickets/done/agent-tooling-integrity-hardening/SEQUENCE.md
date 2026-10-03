# Implementation Sequence — agent-tooling-integrity-hardening

Tickets in this folder can mostly run independently; ordering below is about maximizing the value
of the tracking tickets (#4, #5) rather than a hard dependency chain.

## Order

1. TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (scope-only parent)
2. TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (parallel with #3 after parent)
3. TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (parallel with #2 after parent)
4. TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (best done after #2/#3 — its correlation
   section is most useful once #2's fix has real post-fix data to show, and its `parity_index.py`
   call-count section is ready to pick up any call site #3 adds; it does not hard-block on either,
   since it must report a real "0 call sites" state either way)
5. TCK-20260810-SKILL-USAGE-RETRO-TRACKING (independent of #2/#3; can run in parallel with #4 —
   different subsystem, same "wire a real metric into the recurring retro" shape)
6. TCK-20260810-STATUS-DRIFT-CHECK-WIRING (fully independent of #2-#5 — different corpus
   (`tickets/done/` body text, not `agent-monitoring/*.jsonl`) and different checker; can run any
   time after the parent, in parallel with everything else)

## Verification Note

The epic is not closed by #2-#6 merely landing code. A follow-up `agent-monitoring-retro` run
(next ISO week or `--days` window after #2-#5 are DONE) must show the search-before-grep compliance
rate, parity write-safety co-occurrence count, and skill-adoption numbers actually move in the real
retro report; separately, a follow-up `status_drift_check.py` run after #6 is DONE must show zero
real (non-false-positive) `FAIL` records — that is what Acceptance Criteria's "epic is not closed
merely because code exists" line requires.
