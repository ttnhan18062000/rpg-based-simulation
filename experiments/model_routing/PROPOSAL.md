# Proposal: Cost-Aware Model Routing for the Ticket Pipeline

**Status:** proposed, not built
**Location:** `experiments/model_routing/` (lightweight sandbox — exempt from the ticket/staging-artifact workflow; only a validated policy ever graduates into a real ticket)
**Date:** 2026-07-14

---

## 1. Origin — this is a named, deferred idea, not a new one

Traced to its actual source rather than invented from scratch:
`docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` (archived, Tier 1 shipped
by `TCK-20260708-AGENT-COST-OBSERVABILITY`) states directly:

> "Longer-term, once cost-by-agent-type is visible for a few weeks, it becomes the evidence base for
> a **model-routing policy**: route the machine-checkable half of a gate to a cheaper model, keep the
> primary model for the judgment half. That's a genuine AI-first lever."

That doc also poses the open question this proposal exists to answer: *"Does a model-routing policy
need its own quality-regression audit before anyone trusts it in the critical path?"*

**Not a duplicate of `tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md`** — checked
directly. That ticket is about *how* workflows execute (porting `.claude/workflows/*.js` from
LLM-narrated phase sequencing to real runtime code via a Claude Agent SDK program); it says nothing
about which model runs each phase. This proposal is about *which model*, and applies identically
whether orchestration stays narrated or is later ported to real code — it does not depend on that
backlog item and is not blocked by it.

No ticket exists yet for model routing itself (confirmed via `grep -ril` across `docs/` and
`tickets/` for "model-rout", "model tier", "cost-aware", "model selection") — this is the first time
it's been scoped past the one-paragraph mention above.

## 2. The prerequisite already shipped

`TCK-20260708-AGENT-COST-OBSERVABILITY` gives every ticket-pipeline agent call a `cost_proxy_score`,
computed by `tools/agent-monitoring/cost_proxy.py`:

```
cost_proxy_score = (0.001 × sum(Bash duration_ms)) + (50 × count(Agent spawns)) + (1 × count(Read/Edit/Write/MultiEdit))
```

— a unitless, monotonic *ranking* aid ("agent A costs 3x agent B"), not a dollar figure (real
token/cost telemetry is platform-blocked; `agent()` never receives `input_tokens`/`output_tokens`
from the runtime). `make agent-monitoring-retro` already surfaces this as a spend-by-phase and
spend-by-agent breakdown (`generate_retro.py`, filtering to events where `cost_proxy_score is not
None`, aggregating per `phase`/`agent`).

So the data needed to decide *where* routing would matter already exists and is already visible on
a recurring cadence — nobody has built the routing policy on top of it.

## 3. The other prerequisite already shipped: judgment vs. mechanical split

`TCK-20260705-GATE-DET-*` (the `gate-determinism-followups` batch) added a `verified_by` field to
gate verdicts — e.g. `verified_by: ["static:no_raw_domain_return", "static:parity_diff_match",
"llm"]` — distinguishing "passed because a human-legible static rule was true" from "passed because
an LLM judged it." This is exactly the split a routing policy needs: it tells you, per gate, how much
of the verdict is already mechanical (safe to route cheap) versus how much is genuine judgment
(keep on the primary model).

Four of the ticket pipeline's judgment-heavy phases (`done-checker`, `parity-updater`,
`mechanics-auditor`, `architecture-reviewer`) already run a static pre-check *before* the LLM call
and cite its output — the LLM's role in those phases is narrower than "render the whole verdict,"
it's "judge the residual the static check couldn't resolve." That's real signal for routing: the
static-pre-check portion needs no model at all, and the LLM portion covering the residual may not
need the most capable tier either, depending on how narrow the residual actually is.

## 4. What routing would mean, concretely

The `Agent` tool already accepts a per-call `model` override (`sonnet` / `opus` / `haiku` / `fable`)
— no new infrastructure required to *try* routing, only a policy for *when* to use which, plus a way
to validate it's safe.

Candidate phase → tier mapping, to be confirmed empirically (not assumed):

| Phase / agent | Current assumption | Routing candidate | Why |
|---|---|---|---|
| `ticket-scoper` (tag registry check) | primary tier | cheaper tier | Mechanical lookup against `tag_registry.jsonl`, already static-precheck-backed |
| `done-checker` (Verify) | primary tier | cheaper tier for the 5 static-precheck conditions' narration; primary tier retained for the remaining judged conditions | `run_static_precheck` already does the deterministic half |
| `parity-updater` | primary tier | cheaper tier when the conditional agent call is skipped path is not taken; primary tier when it runs (judgment on ledger wording) | Static pre/post checks already bound the mechanical half |
| `architecture-reviewer` (Plan-Review, Architecture-Verify) | primary tier | **no change** | Named explicitly as "the gates that matter most are LLM judgment" in the infra audit (6.5/10 determinism score) — highest-risk to route away from the primary model |
| `implementer`, `planner`, `investigator` | primary tier | **no change** | Core judgment/authorship work — not a routing candidate |

This table is a starting hypothesis for the loop/validation step (§6) to test, not a final decision.

## 5. What this does NOT do

- Does not change any gate's pass/fail *logic* — only which model renders the LLM-judged portion of
  a verdict.
- Does not touch `architecture-reviewer`'s core judgment calls, or `implementer`/`planner`, where the
  infra audit already flags determinism as the weakest category (6.5/10) — adding a cheaper,
  potentially-less-capable model to the least deterministic gates is exactly backwards.
- Does not claim real dollar savings — `cost_proxy_score` is a ranking proxy, not token telemetry;
  savings are reported in proxy-score terms, with that caveat stated every time, same as the retro
  report already does.
- Does not bypass any existing gate (`NEEDS_CHANGES`, `BLOCKED`, `DOD_BLOCKED`, etc.) — routing is
  purely a `model:` parameter choice at the point an agent is invoked, everything downstream is
  unchanged.

## 6. Validation plan — reusing the loop harness, not building a second one

The archived idea doc's own open question — *"does a model-routing policy need its own
quality-regression audit before anyone trusts it in the critical path?"* — has an existing answer
in this repo's toolset: yes, and `experiments/loop/` (proposed 2026-07-14, see its own
`PROPOSAL.md`) is a directly reusable mechanism for exactly this kind of guarded, mechanical
before/after comparison. Rather than a live A/B experiment against production ticket runs (expensive,
slow, and risks a real ticket landing on a bad routing call), the validation should run **against
already-recorded historical data first**:

- **Metric:** proxy-score delta per phase (`cost_proxy_score`, aggregated the same way
  `generate_retro.py` already does) between the current uniform-tier baseline and a routed policy,
  computed by replaying historical `agent-monitoring/events.jsonl` phase/agent distributions against
  the proposed routing table.
- **Guard:** gate-failure-rate must not regress — specifically, the rate of `NEEDS_CHANGES`,
  `BLOCKED`, `DOD_BLOCKED`, and `TAGS_NOT_REGISTERED` outcomes for any phase whose model tier changes.
  A cheaper model causing more rework nets out as a *cost increase*, not a saving, once the
  reopened-ticket cost is counted — so this guard is load-bearing, not optional.
- **Only after historical replay passes** should a real, live trial run happen — one or two actual
  hotfix-tier tickets, routed per the candidate table, compared against the retro's existing
  spend-by-phase baseline for similar tickets.

This reuses the loop's keep/discard shape without needing the loop's git-worktree isolation
machinery — this experiment doesn't modify `src/`, it modifies which `model:` value an orchestrator
passes to `Agent()`, so the "iteration" here is a routing-table variant, not a code diff. A
scaled-down version of `runner.py`/`results.tsv` (a routing-table variant, a proxy-score delta, a
guard-pass/fail verdict, a keep/discard row) is still the right shape, just without the worktree step.

## 7. Bindings to existing features — where this plugs in, not around

Explicitly working through what this touches, per the instruction not to treat this as a standalone
feature:

| Existing feature | How model routing binds to it |
|---|---|
| `agent-monitoring/` (`tools.jsonl`, `events.jsonl`, `runs.jsonl`) | Source of the historical replay data in §6, and where a routed run's own `cost_proxy_score` continues to be recorded identically — no schema change needed, `model` used per call is already implicit in the agent call itself and could be added as a field if routing ships for real. |
| `make agent-monitoring-retro` / `generate_retro.py` | Where the *result* of routing must show up to be trusted — the existing spend-by-phase/spend-by-agent breakdown is the exact before/after comparison surface. A shipped routing policy should make retro's next report show the spend drop directly, not require a separate report. |
| `verified_by` gate-provenance field | The existing signal for "how much of this gate is already mechanical" — the routing table in §4 should be derived from this field's real distribution across recent runs, not guessed per-phase. |
| **CLAUDE.md's retro cadence rule** | *"before changing any agent prompt/phase/tier rule"* is one of the three retro triggers already defined in this repo. A model-routing policy change **is** a tier rule change by this project's own definition — so shipping this for real must run `/agent-monitoring-retro` first (there's already a pending nudge: 9 completed `implement-ticket` runs since the last dated retro, threshold 5, as of this session) and again after, to have a real before/after baseline instead of an assumed one. |
| `experiments/loop/` | Reused validation shape (§6), not a new harness — see that proposal's own guardrails on scope/guard/keep-discard. |
| Gate-determinism static pre-checks (`tools/gate_checks/*.py`) | These already run *before* the LLM call in 4+ phases — routing candidates in §4 are drawn directly from which phases already have this split, not assumed independently. |

## 8. Explicitly out of scope for v1

- Any change to `architecture-reviewer`, `implementer`, or `planner`'s model tier — see §5.
- Real dollar-cost modeling — `cost_proxy_score` stays a ranking proxy until Anthropic forwards real
  usage data (per `idea_agent_cost_observability.md`'s Tier 3, still platform-blocked).
- Making routing automatic/dynamic (e.g. an agent choosing its own tier at runtime) — v1 is a static,
  human-reviewed table, not a self-routing system.
- Touching the `EXECUTABLE-WORKFLOW-RUNTIME` backlog item — independent, not a prerequisite either
  direction.

## 9. Open decisions before building

- [ ] Confirm which phases in §4's table are worth testing first — proposal defaults to the 3 rows
      with an existing static pre-check (`ticket-scoper` tag check, `done-checker`, `parity-updater`).
- [ ] Confirm the historical-replay data window (e.g. last N completed tickets) is large enough for a
      meaningful gate-failure-rate baseline — needs an investigation-tier check against how many
      `NEEDS_CHANGES`/`BLOCKED`/`DOD_BLOCKED` events actually exist per phase in `events.jsonl` today.

## Related

- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` — origin of this idea, Tier 1 evidence base
- `docs/plans/archive/agent_infrastructure/idea_agent_gate_determinism.md` — origin of `verified_by`, the mechanical/judgment split this policy routes on
- `docs/ai/agent_infrastructure_audit.md` — names "Determinism of judged gates" as the lowest-scored category (6.5/10); routing must not make this worse
- `tools/agent-monitoring/cost_proxy.py` — the exact formula this proposal's metric reuses
- `tools/agent-monitoring/generate_retro.py` — the existing spend-by-phase/spend-by-agent surface
- `experiments/loop/PROPOSAL.md` — the sibling proposal whose keep/discard validation shape this reuses
- `tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md` — confirmed non-duplicate, independent axis (how vs. which model)
