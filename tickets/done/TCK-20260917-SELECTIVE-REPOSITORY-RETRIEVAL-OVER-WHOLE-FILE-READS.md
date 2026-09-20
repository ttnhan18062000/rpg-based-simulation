---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS
phase: done
date: 2026-09-17
tags: [ai, workflows, process-improvement, optimization]
---

# TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS

## Title
Prefer targeted line-range and symbol retrieval over whole-file reads — the cheapest token lever
available, with no dependency, no license, and no third-party state

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
From an external AI review of this account's Claude usage, supplied by the user 2026-09-17
(`/home/u24desktop/Working/tmp/token-usage-review.md`, §8). **Reviewed rather than adopted** — its
arithmetic was checked and holds, but several of its other recommendations are not executable here
(see Assumptions).

**The observation that motivates it.** Direct user input across all recorded usage is ~363.9K tokens
against ~48.8B cache-read tokens — a ratio of roughly 134,000:1. Prompt wording is therefore not the
lever. Essentially all consumption is *context*: repeated repository reads, tool output, accumulated
history. Of the review's recommendations, targeted retrieval is the one that is **entirely ours** —
no vendor, no license, no machine-wide state, no proxy in the API path — and it is independent of
`TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`'s outcome.

The inefficient pattern it names: search → read several entire files → inspect imports → read
related files → repeat later in the same task. The efficient one: search → identify exact symbols →
retrieve narrow line ranges → expand only when genuinely required.

## Scope
- Establish a retrieval preference order for agent work, and record it where agents will actually
  follow it: symbol/reference search first, then targeted line ranges, then dependency inspection,
  with **full-file reads as an explicit fallback rather than the default**.
- Define when a full-file read *is* correct, so the guidance does not become a blanket prohibition —
  reviewing an unfamiliar module end-to-end, auditing a file for a corpus-wide property, and reading
  a file short enough that ranged reads cost more calls than they save are all legitimate.
- Measure the change with data this repo actually has (see below).

## Out of Scope
- **Any blocking gate, ratchet, or threshold on read behaviour.** Guidance and measurement only.
  Agent monitoring is a side effect of how work happens, not a simulation feature.
- **Weakening CLAUDE.md's mandatory Context Scan.** `search_docs` → `graphify query` → registry
  before grep/read is a Hard Rule and deliberately front-loads retrieval. This ticket refines what
  happens *after* that scan narrows the target; it does not reduce the scan itself. If implementing
  this appears to require relaxing the Hard Rule, stop and report rather than routing around it.
- A token-based success metric. Not available — see Assumptions.
- Any change to `CLAUDE.md` without the user's own direct authorization.

## Acceptance Criteria
- [x] A retrieval preference order exists in a place agents actually consult, with the legitimate
      full-file cases named explicitly. `docs/guidelines/retrieval_preference.md`, pointed to from
      `.claude/agents/investigator.md` and `.claude/agents/implementer.md` at the exact point each
      already tells the agent to read code.
- [x] A measured before/after on **`Read`-tool call counts and full-file versus ranged reads** —
      **with an honest correction to the premise, per this ticket's own Assumptions section**:
      `input_summary` was verified (not assumed) to be file-path-only, so the ranged/whole-file
      split has zero historical data to compare against — it structurally cannot have a real
      "before." What's delivered instead, exactly matching the ticket's own contingency for this
      finding ("the measurement needs a different source and that finding should be recorded"):
      (1) a real, available "before" for `Read`-call **volume** (`total_read_calls=41470` over the
      window below); (2) a new additive `read_ranged` field so the ranged/whole-file split becomes
      measurable from this point forward; (3) `read_ranged_baseline.py` reporting both honestly —
      `read_ranged_unknown_count=41464` (every historical row) versus `read_ranged_true_count=6`
      (this session's own real ranged reads recorded live during this ticket's own implementation,
      after the field shipped) — the real "after" is a later re-run once more activity accumulates.
- [x] The baseline window and its population counts are recorded, so the comparison window can be
      matched rather than eyeballed. `window_start_ts=2026-06-13T17:23:37Z`,
      `window_end_ts=2026-09-20T04:46:56Z`, `total_tool_calls=231712`, `total_read_calls=41470`.
- [x] No gate, ratchet, or blocking check is introduced. `retrieval_preference.md` is guidance only;
      `read_ranged` and `read_ranged_baseline.py` are observability, not an enforcement mechanism.
- [x] Nothing under `agent-monitoring/data/` is mutated; any derivation is read-time only, following
      `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT`'s precedent. No existing row was rewritten —
      `read_ranged` only appears on new rows written by the normal hook going forward; the baseline
      script itself is read-only (`test_cli_does_not_mutate_agent_monitoring`, git-porcelain
      before/after).

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — the vendor-dependent sibling. This ticket is
  deliberately independent of its outcome and should not be blocked on it.
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — established that real token data is
  platform-blocked, which is why this ticket measures read behaviour instead.
- `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` (done) — read-time-only derived-metric precedent.

## Related Docs
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  — the existing in-repo plan for this problem space. Its governing principle applies directly:
  *"A context-budget reduction is successful only when correctness signals hold or improve."*
- `docs/agent-monitoring/schema.md` — "What is not recorded"
- `/home/u24desktop/Working/tmp/token-usage-review.md` — the external review this derives from
  (external, unversioned; treat as a source, not as authority)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS/investigation.md`
- `stored_artifacts/TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS/plan.md`
- `stored_artifacts/TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS/test_plan.md`

## Related Code Areas
- `agent-monitoring/data/YYYY-Www/tools.jsonl` (`tool`, `input_summary` — the measurement source)
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `.claude/agents/*.md` and `.claude/skills/*` — the plausible homes for the preference order

## Assumptions / Open Questions
- **The review's own §14 metric program is largely not executable here**, and this ticket
  deliberately does not inherit it. It asks for uncached-input, cache-read, cache-write, output and
  tool-result token counts; `docs/agent-monitoring/schema.md` states token counts are "consumed
  internally by the Claude Code runtime… There is no field for it and no workaround within the
  current platform." Read-call counts are the honest substitute.
- **A real risk of this change is under-context, not over-cost.** The same source plan names it:
  *"under-context: missing an active constraint, paired test, contract, or prior decision and
  producing incorrect work."* Ranged reads make that more likely, not less. This session has twice
  reached wrong conclusions from truncated output. Whatever guidance lands must say plainly that a
  ranged read which turns out to be insufficient should be widened immediately, and that concluding
  from a partial read is the failure mode being traded against.
- Where the preference order belongs is undecided — agent role files, a skill, or CLAUDE.md. The
  first two need no special authorization; CLAUDE.md does.
- Whether `input_summary` is granular enough to classify a read as ranged versus whole-file is
  **unverified**. Check before relying on it; if it is not, the measurement needs a different source
  and that finding should be recorded rather than worked around.

## Implementation Notes
Cheapest item in this family and independent of every vendor question, so it can proceed regardless
of what the Headroom trial concludes.

Resist expanding this into a retrieval-architecture project. The in-repo plan
(`idea_context_efficient_agent_retrieval_observability.md`) already covers that design space and is
sequenced after provider-agnostic orchestration; this ticket is the small behavioural slice that can
be done now without waiting for it.

**Verified before building anything, per this ticket's own explicit instruction**: `input_summary`
is file-path-only for `Read` calls (checked against `post_tool_hook.py` source and real corpus
rows) — the premise of a retroactive ranged/whole-file split from existing data does not hold. See
`stored_artifacts/.../investigation.md` for the full check.

**Guidance placement, deliberately narrow**: a single authoritative doc
(`docs/guidelines/retrieval_preference.md`), pointed to from `investigator.md`/`implementer.md`
only — the two roles that actually do open-ended exploratory reading — rather than duplicated
across every agent file or folded into CLAUDE.md (would need direct user authorization this P2
chore doesn't warrant seeking).

**Schema addition, not a workaround**: `post_tool_hook.py` gained an additive `read_ranged` field
on `tools.jsonl` records, since no existing field could answer the measurement question. No
historical row has it — every historical `Read` row's own count is real, but its ranged/whole-file
classification is honestly `unknown`, not backfilled or guessed.

## Test Summary
- `pytest tests/tools/test_post_tool_hook.py -v`: 22 passed (18 original + 4 new `read_ranged`
  cases; `_RECORD_FIELDS` updated to include the new field).
- `pytest tests/tools/test_read_ranged_baseline.py -v`: 5 passed (new file).
- `pytest tests/tools/ tests/docs/ -m "not slow and not extra_slow" -q`: 2825 passed, 26 skipped,
  28 deselected, 2 xfailed, 0 failed.
- `python3 tools/validate_frontmatter.py docs/guidelines/retrieval_preference.md`: OK.
- `make knowledge-index-update`: 90 files re-embedded (new/modified `docs/` files), 0 errors.
- Real baseline recorded (see Acceptance Criteria above and `stored_artifacts/.../test_plan.md`).

## Files Changed
- `docs/guidelines/retrieval_preference.md` (new) — the retrieval preference order, legitimate
  full-file cases, and the under-context failure-mode warning
- `.claude/agents/investigator.md`, `.claude/agents/implementer.md` — one-line pointers to the new
  doc, added at the existing "read the code" instruction
- `tools/agent-monitoring/post_tool_hook.py` — additive `read_ranged` field on `tools.jsonl`
  records
- `docs/agent-monitoring/schema.md` — `tools` table: `read_ranged` field documented, JSON example
  updated
- `tests/tools/test_post_tool_hook.py` — `_RECORD_FIELDS` updated; 4 new `read_ranged` tests
- `tools/agent-monitoring/read_ranged_baseline.py` (new) — read-only baseline script
- `tests/tools/test_read_ranged_baseline.py` (new)
- `tickets/todos/` → `tickets/done/TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS.md`
- `stored_artifacts/TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS/` (new)

## Completion Summary
Verified the ticket's own flagged assumption before building anything: `input_summary` cannot
distinguish a ranged `Read` from a whole-file one, for any historical row — confirmed against
source and real corpus data, not assumed. Rather than force a metric the data can't support,
recorded the finding and shipped the two things it actually unblocks: (1) a retrieval preference
doc that agents actually consult (pointed to from `investigator`/`implementer`, not duplicated),
and (2) an additive `read_ranged` field plus a dedicated, read-only baseline script that reports
today's real numbers honestly — real Read-call volume as the available "before," and an explicit
`unknown` (not fabricated) for the ranged/whole-file split until real usage accumulates with the
new field present. No gate, ratchet, or CLAUDE.md change. No existing `agent-monitoring/data/` row
was mutated.
