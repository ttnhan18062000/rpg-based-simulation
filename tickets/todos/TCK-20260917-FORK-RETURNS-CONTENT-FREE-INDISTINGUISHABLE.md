---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE
phase: open
date: 2026-09-17
tags: [ai, agent-monitoring, process-improvement, workflows]
---

# TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE

## Title
A dispatched fork that returns nothing records `status: "ok"` exactly like one that returns real
work — the data to tell them apart already reaches `post_tool_hook.py` and is discarded

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Routed in by `rpg-feature-planning` 2026-09-17, relaying a failure in `rpg-implementer`. **Second
occurrence that day**, so not a one-off. Filed at the user's direction with an explicit deferral:
*"only fix when they are major effect bug"* — see Implementation Notes for the gate.

**What happened.** Three forks were dispatched to investigate mechanism-splitting decisions. **Two
returned content-free.** The third returned a confident recommendation — split all three of its
assigned mechanisms — with none of the supporting evidence reaching the caller. Its
`attributes_biology` verdict was **wrong**: there was no real divergence and it was correctly kept
as one mechanism. It was caught only because the implementer distrusted the report and
re-investigated all five remaining cases by hand, producing materially better grounding than the
fork's report contained.

**Why this is worse than a clean failure.** A fork that errors is obviously unusable. A fork that
returns a confident recommendation with no evidence *looks like a result*. Splits propagate into
`depends_on`, dependents, verified blocks, and both consuming artifacts, so a trusted wrong verdict
has real blast radius.

**Verified independently against monitoring data** rather than accepted on report. Four `Agent`
rows in `.claude/worktrees/m2-foundational-systems-tickets/agent-monitoring/data/2026-W38/tools.jsonl`:

| ts (UTC) | `input_summary` | `status` | `duration_ms` |
|---|---|---|---|
| 05:50:27 | Test identity rule against `inventory_trade_conservation`, `cognition_capacit…` | ok | 2234 |
| 05:50:43 | Test identity rule against `information_trust_deception`, `regional_trauma_ha…` | ok | 1979 |
| 05:50:59 | Test identity rule against `attributes_biology`, `buildings_town_services`, `ca…` | ok | 2892 |
| 05:53:33 | **"Request the actual split/keep findings, not a status check"** | ok | 2556 |

Three dispatches inside 32 seconds, then the caller chasing a hollow return 2.5 minutes later. That
fourth row is documentary evidence of the failure sitting in the corpus. `attributes_biology` — the
wrong verdict — is in the 05:50:59 batch. **All four record `status: "ok"`.**

**Third occurrence, 2026-09-18 — and a new failure shape.** Reported by `rpg-implementer`. A fork
was dispatched to audit all 70 declared `depends_on` edges against real code, with the required
output shape stated explicitly: one line per edge, verdict plus a real file/function citation, no
summarizing.

- **First completion:** a bare tally — *26 KEEP / 19 REMOVE / 25 UNCLASSIFIABLE* — with zero
  per-edge evidence. The content-free shape above, but worse: **the numbers were wrong.** The real
  hand audit (`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`, PR #218) found
  **21 / 32 / 17**, so REMOVE was undercounted by 13. Trusting the tally would have left 13 bad
  edges in the mechanism registry, and #218 shows that edge removals move derived priorities
  materially (`betrayal_siege_war` fell from 5th-highest to effectively off the list).
- **Second completion, after one resume restating the required shape:** a claim that *"the full
  70-line verdict table has already been delivered in my previous reply."* No such table had ever
  reached the caller. This is **a false claim about its own prior output**. It is neither empty nor
  an unevidenced conclusion, and is distinct from both shapes above.

Corroborated in the 2026-W38 agent-monitoring shards: an `Agent` row at 02:57:31Z (*"Audit
depends_on edges against real code"*, `status: ok`) and a `SendMessage` at 03:14:00Z addressed to
the fork's own id (*"Need full 70-edge evidence table restate…"*, `status: ok`). **Not verifiable
from any record:** the content of the second reply. Monitoring logs the resume call, not the fork's
answer, so the false-claim wording rests on the implementer's report.

Recovery: the implementer had **decided a retry cutoff before sending either request** (at most
one resume). When the second return was also hollow, they did all 70 edges by hand rather than
retrying. That cutoff is what bounded the cost.

## Scope
- Record, for `Agent` tool calls, a signal distinguishing an empty/whitespace return from a
  substantive one. `tools/agent-monitoring/post_tool_hook.py` **already receives
  `payload["tool_response"]` (line 51)** and currently uses it only to set `status` from
  `is_error`/`error`. The needed data is in hand at the hook and thrown away; this is a recorded
  field, not new plumbing.
- Surface the signal where a reader sees it (retro, or the advisory sweep).

## Out of Scope
- **Any blocking gate, ratchet, or threshold over this signal.** Record and surface only. Agent
  monitoring is a side effect of how work happens, not a simulation feature, and this repo spent
  2026-09-15/16 removing exactly this class of over-strict gate
  (`TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION`).
- **A `duration_ms` threshold.** Measured and rejected: 2234 / 1979 / 2892 / 2556 ms, n=3, bands
  overlapping. The relaying fork was the longest but not separably so. A detector built on this
  would be noise dressed as a signal.
- **Detecting either non-empty failure**: the confident-but-evidence-free return, or the false
  claim about prior output. See Assumptions. Both are stated as unsolved, deliberately.
- Changing `SubagentStop`. Its payload carries `background_tasks`/`stop_hook_active` (session-scoped
  in-flight work, schema extracted from the installed binary's own zod validation — see
  `subagent_stop_background_guard.py`'s docstring). It does **not** carry the subagent's return
  content, so it is the wrong instrument despite being the intuitive one.

## Acceptance Criteria
- [ ] An `Agent` row records enough to distinguish an empty return from a substantive one.
- [ ] A planted empty return is shown to be distinguishable, and a planted substantive one is shown
      not to trip it — both proven, not reasoned about.
- [ ] No gate, ratchet, or blocking check is introduced.
- [ ] The ticket's own limitation is restated in the code/docs: neither non-empty failure (the
      evidence-free verdict, or the false claim about prior output) is covered.

## Related Tickets
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` (done) — the governing precedent: a CLAUDE.md prose Hard
  Rule recurred as a real failure **four times** despite being propagated verbatim into 16 agent
  role files, and was only resolved by deterministic enforcement. "One implementer's habit of
  re-checking" is the prose rule here.
- `TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING` (done) — nearest relative: orchestration
  referencing a subagent that never delivered.
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` (done) — every `Agent` row here has `run_id`, `seq`,
  `phase`, `agent`, `ticket_id` all `null`; recorded dispatches are unattributable to any run or
  ticket.

## Related Docs
- `docs/agent-monitoring/schema.md`
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — the silence-as-a-state
  catalogue this is a new instance of

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/post_tool_hook.py` (`tool_response` at line 51; `status` derivation ~135-141)
- `.claude/settings.json` (`PostToolUse` `*` → `post_tool_hook.py`; the `PreToolUse` `Agent` matcher
  is advisory-only and not a detection point)

## Assumptions / Open Questions
- **Three different failures, and only one is mechanically detectable.**
  1. *Content-free return* (2 of 3 on 2026-09-17; the first completion on 2026-09-18). Trivially
     catchable, though note the 2026-09-18 case wasn't strictly empty: it carried a bare tally,
     which was also wrong.
  2. *Confident recommendation with no supporting evidence* (the wrong `attributes_biology`
     verdict). Well-formed and non-empty.
  3. *False claim about its own prior output* (2026-09-18, second completion: "already
     delivered"). Well-formed and non-empty, and it **defeats re-request as a recovery strategy**:
     asking again just returns a confident "already done."

  **No size check will ever catch 2 or 3**, and this ticket does not claim to. Stating that plainly
  up front is what makes the detectable case trustworthy.
- **Pattern, stated as a hypothesis only (n=3):** all three incidents asked for exhaustive,
  structured, multi-item output (per-mechanism verdicts across batches; a 70-row per-edge table).
  That may be the task shape forks fail to relay. If it holds, the cheapest fix is not a detector
  but not delegating exhaustive enumeration to forks at all. Three incidents in about 21 hours is
  suggestive, not established. Test it before acting on it.
- **Candidate structural fix for the undetectable half, offered by `rpg-feature-planning`, not
  committed scope:** change what investigation forks are asked to *return*. If a fork returns only
  evidence — call sites, state of each half, citations — and the **caller** forms the verdict, then
  a hollow return is obviously useless rather than plausibly complete, and cannot smuggle a wrong
  conclusion through because no conclusion was requested. The stronger argument is **checkability**:
  a fabricated `file:line` citation resolves in seconds and is caught; a fabricated verdict cannot
  be checked without redoing the investigation. Corroborated by what happened — the implementer's
  own investigation produced better evidence than the fork's report contained, so the verdict was
  never the valuable part.
  - **Tension to resolve before adopting:** forks exist partly for *context isolation*. If a fork
    returns evidence the caller must reason over, the caller re-imports the bulk it delegated away,
    which works against the token-efficiency work
    (`TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`). The narrow form — return **citations and
    short findings, not content** — keeps it cheap. Without that constraint this becomes a token
    regression.
  - Scope it to the **investigation-fork case only** if adopted. Plenty of fork uses legitimately
    want a conclusion; a blanket rule would be overreach.
- Whether `tool_response` for an `Agent` call is a string, a dict, or a content-block list is
  unverified — confirm the real shape before writing any check against it.

## Implementation Notes
**DO NOT IMPLEMENT YET.** The user's direction, 2026-09-17: *"only fix when they are major effect
bug."* This is filed as a watch-item, not queued work.

Pick it up when one of these is true, and record which:

1. A wrong fork-relayed conclusion **actually lands** in a durable artifact — mechanism registry,
   parity ledger, `REGISTRY.yaml`, a closed ticket's conclusions — rather than being caught in
   review; or
2. Recurrence becomes frequent enough to cost real rework; or
3. Someone is already editing `post_tool_hook.py` and the recording change rides along for
   near-zero marginal cost.

**Trigger 2 was assessed on 2026-09-18 as arguably met:** three occurrences in about 21 hours, and
the third cost a full manual 70-edge audit. Trigger 1 was a near miss; nothing wrong landed only
because of a pre-decided retry cutoff. **The user reviewed this on 2026-09-19 and chose to keep the
ticket deferred**, recording the new evidence here in the next agent-infra batch rather than
starting implementation.

The reasoning, so it isn't lost: **the scoped detector would not have prevented that rework.** The
implementer spotted the empty return immediately without any tooling, so detection was not the
bottleneck. The cost came from the fork failing to deliver at all. A size signal would have caught
the first completion, missed the second, and saved none of the 70 edges.

**Proven mitigation in the meantime, costing nothing:** decide a retry cutoff *before* dispatching
or resuming a fork (at most one resume), and when it is reached, do the work directly rather than
asking again. This is what bounded the 2026-09-18 cost. It also matters specifically because of
failure shape 3: a fork that claims it already delivered will keep claiming so, and an uncapped
retry loop spends tokens on it indefinitely.

Until implementation, this ticket's value is that the diagnosis, the evidence, the three failure
shapes, and the two rejected approaches (duration threshold, `SubagentStop`) are written down, so
the next occurrence is not re-investigated from scratch.

## Test Summary
_Deferred — see Implementation Notes._

## Files Changed
_Deferred — see Implementation Notes._

## Completion Summary
_Open, deliberately deferred._
