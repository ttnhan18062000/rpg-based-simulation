---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-COST-MEASUREMENT
phase: open
date: 2026-09-24
tags: [delivery, agent-monitoring, benchmarking]
---

# TCK-20260924-DELIVERY-COST-MEASUREMENT

## Title
Report `gh`-calls-per-PR and subject traceability over a week range in one command, so this epic's
before/after is measured rather than asserted

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This epic claims a cost reduction: 16.9 `gh` calls per PR, ~86% of it observation, collapsing to a
single status call (plan §1.1). That claim was measured once, by hand, in a scratchpad, and there is
currently no repeatable way to check whether the epic delivered it.

This ticket makes the measurement a command: `gh` calls per PR and `TCK-`-in-subject traceability over
a week range, reading the same corpus the original figures came from.

**Two measurement traps must be designed in, not discovered again.** Both were hit while drafting this
epic's plan (plan §1's caveat):

1. **Never measure from the working tree.** An earlier pass read the *worktree* copy of the monitoring
   shards and under-counted, because that long-lived worktree had drifted 8 commits behind
   `origin/main`. A weekly total must be read from a named ref.
2. **A "closed" calendar week keeps growing.** Every PR stages `agent-monitoring/`, so a session whose
   activity happened in W38 but whose PR merges weeks later still appends W38-timestamped rows. **Any
   weekly total from this corpus is a snapshot, not a final count.** Two measurements taken from
   different refs are comparing different corpora, silently.

So the tool must take a `--ref` and **record the SHA it measured** in its own output, or before/after
comparisons are meaningless. ([[project_worktree_corpus_measurement_staleness]])

## Scope
1. **A delivery-cost measurement module under `tools/delivery/`**, reporting over a week range:
   - `gh` invocations, broken down by subcommand (`pr view`, `pr checks`, `run view`, `run list`,
     `api repos/…`, `pr create`, `pr diff`, `run rerun`, `run watch`), and classified
     observation vs action
   - **`gh` calls per PR** — the headline figure, denominated by `gh pr create` count
   - **subject traceability** — share of `origin/main` subjects in the range carrying a `TCK-` ID
   - git-side context: `git status` / `git diff` share of git invocations
2. **`--ref` required-in-effect, with the measured SHA recorded in the output.** A report that does not
   name its SHA is not a valid before/after datapoint.
3. **Built on `tools/agent-monitoring/bash_command_mix.py`**, which already exists on `main` and already
   takes `--data-dir`, `--ref`, `--since-week`, `--through-week` and `--json`. **Extend or share that
   module's command-classification logic; do not reimplement it.**
4. **A documented baseline row** for the pre-epic state, so the "before" number is recorded with its ref
   rather than remembered from the plan.

## Out of Scope
- **Reimplementing command classification.** `bash_command_mix.py` already classifies the Bash command
  head; this module classifies `gh` *subcommands*, a narrower question layered on top. Duplicating the
  head-classification logic is explicitly excluded — a second copy drifts, and this ticket exists partly
  to avoid exactly that.
- **Measuring from the working tree.** Excluded by design, per the Request Summary. Reading the shards
  from `agent-monitoring/data/` without a ref is the defect, not a convenience.
- **Presenting a weekly total as final.** Output must carry the snapshot caveat; a total without its ref
  and its as-of meaning is misleading.
- **Token-cost attribution.** `real_token_usage.py::attribute_by_bash_family` answers a different
  question (context tokens per Bash family, from developer-machine-only transcripts). This ticket counts
  calls. Do not conflate them.
- **Per-agent breakdowns.** `agent_tool_usage_baseline.py` already does that.
- **Any blocking threshold, ratchet or gate on the numbers.** Report only. A measurement tool that
  blocks becomes a thing to satisfy rather than a thing to read
  ([[feedback_agent_tooling_checks_proportionate]]).
- **Judging whether the epic succeeded.** It reports the numbers; the user judges.

## Acceptance Criteria
1. One command reports `gh` calls per PR, the observation/action split by subcommand, and subject
   traceability for a given week range.
2. **The output names the ref and the resolved SHA it measured.** Asserted by a test.
3. Reading without an explicit ref does not silently fall back to the working tree — it either requires
   the ref or states unmistakably that the figure is a working-tree snapshot. Asserted by a test.
4. The output carries the "a closed week keeps growing; this is a snapshot" caveat.
5. **Command classification is shared with `tools/agent-monitoring/bash_command_mix.py`, not
   duplicated** — proven by a test or by import structure showing a single implementation. A reviewer
   must be able to see there is one classifier, not two.
6. Re-running against the same ref and week range produces identical output (determinism).
7. A recorded pre-epic baseline exists with its ref and SHA.
8. The reported figures for W30–W39 at a named ref are reproducible, and any difference from plan §1.1's
   figures (1,796 `gh` / 106 `gh pr create` / 16.9 per PR, measured at `75ab942b4`) is explained by ref
   drift rather than treated as a discrepancy to reconcile away.
9. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260924-DELIVERY-STATUS-TOOL` — **dependency**; must have landed, or there is no "after" to
  measure
- `TCK-20260923-BASH-COMMAND-MIX-BASELINE` — shipped `bash_command_mix.py`, the module this builds on.
  **Already merged** (PR #242, `cb3a7ccb0`), so this ticket's prerequisite is satisfied.

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §1 (the figures and the measurement
  caveat), §1.1 (the `gh` table), §1.4 (the 17/60 traceability figure), §4's M6 row
- `docs/guides/delivery_process.md` — created by `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/bash_command_mix.py` — **exists on `main`; the foundation to extend or share,
  never to copy.** Already supports `--data-dir`, `--ref`, `--since-week`, `--through-week`, `--json`
- `tools/agent-monitoring/real_token_usage.py` — the adjacent-but-different token-attribution tool
- `tools/agent-monitoring/agent_tool_usage_baseline.py` — the adjacent per-agent tool
- `agent-monitoring/data/YYYY-Www/tools.jsonl` — the corpus, read via a ref
- `tools/delivery/` — where this module lands

## Assumptions / Open Questions
1. **Correction to the plan, verified 2026-09-24: `delivery_mix.py` and `mainline_trace.sh` do not exist
   anywhere in this repo.** Plan §4's M6 row says this ticket "promotes" them into `tools/delivery/`;
   that is wrong. They were scratchpad-only scripts from the plan's own drafting session and were never
   committed. This ticket **builds fresh** on `bash_command_mix.py`. Do not spend time looking for them.
2. **The Batch B prerequisite is already satisfied** — `bash_command_mix.py` landed in PR #242, merged as
   `cb3a7ccb0`. Plan §8 item 2 and §6's "M6 must land after Batch B ticket 1" are both satisfied. Do not
   re-block on this.
3. Whether the `gh` subcommand breakdown can be read from the corpus's `input_summary` field reliably, or
   whether some invocations are truncated beyond recognition. Measure the unparseable share and report it
   rather than dropping those rows silently.
4. Whether subject traceability should be measured over `origin/main` subjects (as plan §1.4 did, last 60
   commits) or over the same week range as the `gh` figures. The two denominators differ; state which is
   used.
5. Whether this module belongs under `tools/delivery/` or `tools/agent-monitoring/`. It measures the
   delivery lane but reads the monitoring corpus. Leaning `tools/delivery/` with the shared classifier
   staying in `tools/agent-monitoring/` — but if that forces an awkward import, put it beside the module
   it shares code with and say so.

## Implementation Notes
**Runs last in the epic** (see `SEQUENCE.md`) — it measures what the other five changed, so it needs them
landed.

The two measurement traps in the Request Summary are not hypothetical; both were hit during this plan's
own drafting, and the second one (a "closed" week still growing) produced a real 40-vs-58 discrepancy in
W38 that took a session to diagnose. A tool that does not record its ref will reproduce that confusion
every time someone compares two reports.

On the shared-classifier requirement: this epic's whole premise is that one fact should live in one place.
Shipping a second Bash-command classifier inside the tool that measures the epic would be a quiet
self-contradiction, and criterion 5 exists to make it visible in review.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
