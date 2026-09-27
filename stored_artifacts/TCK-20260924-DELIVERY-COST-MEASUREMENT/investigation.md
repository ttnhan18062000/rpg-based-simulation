---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-COST-MEASUREMENT
date: 2026-09-24
tags: [delivery, agent-monitoring, benchmarking]
---

# Investigation — TCK-20260924-DELIVERY-COST-MEASUREMENT

## Confirmed facts

- **`tools/agent-monitoring/bash_command_mix.py` read in full (312 lines).** It already provides
  everything the Request Summary's two measurement traps require: `resolve_ref_sha`,
  `load_tools_rows_from_ref` (reads `agent-monitoring/data/*/tools.jsonl` via `git ls-tree`/`git
  show` against a pinned SHA, never the working tree), `week_shards`, `bash_head`, and
  `bash_subcommand_key` (a 2-word breakdown for `git`/`gh`/`make`/`python3`/`grep`/`rg` heads —
  `gh` is already in `_SUBCOMMAND_HEADS`, so `gh pr`/`gh api`/`gh run` are already distinguished at
  the 2-word level). `build_bash_mix_report` already reports `bash_head_counts["gh"]` (total `gh`
  calls) and the `git status`/`git diff` share this ticket's Scope item 1 also asks for.
- **The existing 2-word `gh` breakdown is not fine-grained enough for this ticket's own headline
  figure.** `gh pr view`, `gh pr create`, `gh pr checks`, and `gh pr diff` all collapse to the same
  `"gh pr"` key at 2 words — the ticket needs `pr create` distinguished from `pr view`/`pr checks`/
  `pr diff` specifically to compute "gh calls per PR." **Extension, not duplication**: a new
  `gh_subcommand_key()` function added to `bash_command_mix.py` itself (not a second file, not a
  parallel classifier) goes one word deeper *only* for rows already classified `head == "gh"` by
  the existing `bash_head()` — it calls into, rather than reimplements, the existing head
  classification.
- **`tools/agent-monitoring/` has no `__init__.py`** (confirmed earlier this session, ticket 3's
  own investigation) — cross-module reuse from `tools/delivery/` follows the same
  try/absolute-import-then-sys.path-fallback pattern already established in `pr_render.py` and
  `ci_triage_classifier.py`, not a new pattern.
- **`origin/main` right now resolves to a SHA that predates every commit on
  `github-delivery-process-epic`** (the epic branch has not merged) — so `origin/main` itself is a
  valid, legitimate "before this epic" baseline ref with no special pinning needed; it simply *is*
  the pre-epic state as of this ticket's own run.
- **Sibling ticket `TCK-20260923-BASH-COMMAND-MIX-BASELINE`'s own baseline is recorded as prose in
  the ticket/plan, not a separate committed JSON artifact** (`stored_artifacts/TCK-20260923-
  BASH-COMMAND-MIX-BASELINE/` holds only `investigation.md`/`plan.md`/`test_plan.md`, no data
  file). **Decision: follow the same convention** — the baseline row (AC7) is recorded as the full
  tool output (with ref and resolved SHA) pasted into this ticket's own `## Test Summary`/
  `## Completion Summary`, not a new artifact-storage convention this ticket wasn't asked to
  invent.
- **Design's explicit warning, taken as a hard constraint, not a suggestion**: this batch's own
  W39 corpus is not a valid "after" datapoint — the epic's tools were not in use while tickets 1–5
  were implemented, and this session's own review/implementation traffic is git-heavy and gh-light
  for reasons unrelated to the epic. **This ticket records the baseline only. It does not attempt,
  compute, or present an "after" number** — Out of Scope's "judging whether the epic succeeded" and
  AC7's "pre-epic baseline" both point the same direction, and design's message states plainly that
  an apparent "after" number right now would itself be evidence the measurement is wrong, not a
  bonus finding.

## Design decisions

1. **`gh_subcommand_key(input_summary)` classifies 8 named observation/action subcommands** (`gh pr
   view`, `gh pr checks`, `gh pr diff`, `gh run view`, `gh run list`, `gh api` — collapsed past the
   path, since paths vary per call — plus actions `gh pr create`, `gh run rerun`, `gh run watch`),
   falling through to a generic `gh <verb>` bucket for anything else, and to an `unparseable`
   count (Assumption 3) for a `gh` row with fewer than 2 tokens.
2. **Subject traceability is measured over the same week range as the `gh` figures** (Assumption
   4), not `origin/main`'s literal last-60-commits window plan §1.4 used — the two are different
   questions (a fixed recent-commit sample vs. a corpus time window), and this ticket's own headline
   is a week-range report, so its second figure should share that same window rather than mixing
   two different denominators in one report.
3. **Module lands at `tools/delivery/delivery_cost_measurement.py`** (Assumption 5's leaning),
   importing `bash_command_mix`'s shared functions via the sys.path-fallback pattern rather than
   forcing the shared classifier itself to move — the awkward-import case Assumption 5 flags as the
   alternative trigger did not materialize.
