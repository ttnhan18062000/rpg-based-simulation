---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation — TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

## Origin
Item 1 (Phase 1, item 4) of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`. Extracted
into its own standalone ticket per the same "extract once concrete, mechanical, self-contained"
pattern used for this session's other epic-item extractions — this is the one Epic K item with no
dependency on anything else (unlike the impact command / scorecard / PR-report-generator chain,
which are genuinely sequential and stay bundled in the epic — see plan.md for the full
cross-reference).

## Cross-checked against D24's own 11-item master implementation plan
`docs/audits/D24_codebase_health_observatory.md` §M lists an 11-item Phase 1-4 plan. Cross-
referencing against this session's actual completed work: **Phases 1-2 (items 1-3, 5-7, 9) are
now all done** (`src_legacy/`/`tests_legacy/` deleted, doc-drift fixed, boundary tests AST-
hardened, domains test-dir placement fixed, `pipeline.py`/`tactical.py` coverage verified,
epic-staleness `## Status` check added). Only items 4, 8, 10, 11 remain — exactly Epic K's own 4
scope items. Epic K's own stated prerequisite (Epic G, architecture boundary hardening) is
confirmed done (`tickets/done/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC.md` exists) —
Epic K is now genuinely unblocked, not just theoretically scoped.

## What this specific item needs to produce
`docs/audits/D24_codebase_health_observatory.md` §C ("Current Health Baseline") is the exact
shape of table the target should reproduce on demand:
```
Source LoC / files, Test LoC / files, Test:source ratio (LoC), Top-level src/ packages,
Test subdirectories, Commits (full history), Docs (.md), docs/REGISTRY.yaml size,
Dead bytecode files, Declared-but-unused core dependencies
```
**§C's own numbers are now stale** — measured before this session's work (`src_legacy/`/
`tests_legacy/` deletion, multiple test-file relocations, dependency removal). Do not copy §C's
numbers into the new tool as a hardcoded baseline; the tool must measure fresh each run.

**Verified: no existing script or make target for this exists anywhere in the repo** (`find`
across the whole tree for `*loc*churn*`/`*churn*baseline*`/`*codebase*health*baseline*` returns
nothing). This is a genuine build-from-scratch item, not a wiring task like most of the rest of
this epic tree turned out to be.

**Critical requirement, explicit in both the ticket and the source audit**: must exclude known
append-only bookkeeping files (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
`docs/REGISTRY.yaml`) from churn measurement specifically — without this exclusion, every report
is dominated by expected bookkeeping churn (these files get touched on nearly every ticket close),
not real code-instability signal. LoC/file-count measurement (not churn) may still legitimately
include `docs/REGISTRY.yaml`'s own size as one of the baseline table's rows (per §C's own
inclusion of it) — the exclusion is specifically for the *churn* dimension, not every metric.

## Related
- `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` (item extracted from here; epic remains
  open for its other 3 items — impact command, historical snapshots/scorecard, PR report
  generator — which stay bundled since they're genuinely sequential/interdependent, not
  independently extractable the way this item is)
- `docs/audits/D24_codebase_health_observatory.md` §B, §C, §M (source data and methodology)
