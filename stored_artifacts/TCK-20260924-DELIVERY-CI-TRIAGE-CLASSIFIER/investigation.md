---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# Investigation — TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER

## Confirmed facts

- **`docs/testing/regression_policy.md` read in full.** It is prose overall, but its `## 3. Soft
  Monitors — Alert Only` section is a real markdown table with a `Location` column listing
  backtick-quoted test file/directory paths (e.g. `` `tests/api/test_live_health_api.py` ``,
  `` `tests/integration/observability/` ``). **Decision (Assumption 1): parse backtick-quoted paths
  from Section 3's table specifically, not the whole document.** This is a real, narrow, honestly-
  scoped parse — not a full markdown-table parser, and not a claim that the rest of the document is
  machine-readable (it is not; §4–§12 are decision trees and worked-example prose with no further
  structure to extract).
- **`tools/delivery/pr_status.py`'s `FAILING` payload only carries job name + per-step name/
  conclusion** (`{"run_id", "job_id", "job_name", "steps": [{"name", "conclusion"}]}`) — no
  individual failing *test* path, since that would require reading a log body, which is explicitly
  out of scope for both that tool and this one. **Consequence for Scope item 5 (changed-file
  correlation)**: correlation happens at *job* granularity, not test-file granularity — the job
  name (e.g. `"Unit · core / world"`) is mapped to the `pytest <paths...>` arguments its
  `.github/workflows/test.yml` step actually runs, and *those* paths are checked against the
  branch's changed files. This is a coarser, honestly-weaker signal than "the exact failing test
  file," and Scope item 5 itself calls this "a signal, not proof" — the classifier's output states
  the job-level correlation basis explicitly rather than implying test-level precision it doesn't
  have.
- **Category 3 (baseline drift) known pattern**: only one is explicitly named in the ticket
  (`tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count`). Per Assumption 3,
  starting from known patterns only (not generalizing) means this is a short, explicit, documented
  allowlist — any failing job whose covered paths do **not** include a listed pattern never gets
  category 3, falling through toward category 1 or `UNCLASSIFIED` instead.
- **The parked "Slow regression" job** (`project_slow_regression_determinism_root_cause` —
  BLOCKED by user decision until engine re-architecture) must never be presented as a *new* finding
  per Assumption 4. Implemented as a small known-parked-jobs set; a match adds a `parked: true` /
  "not a new finding" note to the output without silently suppressing the underlying signal.

## Design decisions

1. **`ABSENT` verdicts map to category 4 directly** — no job/step analysis needed, since `pr_status.py`
   already did the causal analysis (`CONFLICTING`+trigger-only vs. push-not-landed vs. unexplained).
   The classifier's job is to attach the `CLAUDE.md`-prescribed remedy text, not re-derive the cause.
2. **`UNKNOWN` verdicts map to category 4 only when the `reason` text carries a TLS/network-block
   signature** (reusing `pr_status.py`'s own `_TLS_BLOCK_KEYWORDS` list via import, not a second
   copy) — every other `UNKNOWN` shape (a stale-SHA-only run, a generic fetch failure with no
   TLS signature) is `UNCLASSIFIED`, since the classifier has no basis to assert environment/
   infrastructure over "genuinely couldn't tell."
3. **Multiple failing jobs with disagreeing per-job classifications resolve to `UNCLASSIFIED`
   overall** — a mixed signal is exactly the "signals do not clearly place this failure" case AC5
   protects, and forcing one job's category onto another job's independent failure would be a
   fabricated confidence the ticket's Implementation Notes explicitly warns against.
