---
status: active
layer: ai
authority: P0
audience: agent
date: 2026-09-04
tags: [ai, governance, hooks, security, agent-monitoring]
---

# Roadmap — AI-First Engineering Platform: Full Hardening &amp; Evaluation Roadmap

**Purpose**: this doc is the master index for every committed, experimental, and preserved-but-
blocked item in the `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` (Revision 3, READY TO FREEZE,
2026-09-04 — published artifact + `docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html`),
across all four horizons (H0–H3) and all three output buckets — not just the first horizon. It states
shared exit gates and cross-item dependencies once, rather than repeating them in each detail doc
— the same structure `docs/plans/hud_delivery_roadmap.md` established for the HUD effort, applied
here.

**Planning-stage note**: per direct instruction, this pass produces detailed design plans and
milestones only — no tickets are created yet. `TCK-*` IDs anywhere in this subfolder are
placeholders for a future `create-tickets` pass, not yet-existing tickets.

## Full inventory, by horizon and bucket

| # | Item | Bucket | Horizon | Detail doc |
|---|---|---|---|---|
| 1 | Per-agent least-privilege tool scoping | A — Committed | H0, start now | `governance_capability_policy_epic.md` (M1, M3) |
| 2 | Bash secret-exposure advisory hook | A — Committed | H0, start now | `governance_capability_policy_epic.md` (M4) |
| 3 | Versioned capability-envelope baseline | A — Committed | H0, start now | `governance_capability_policy_epic.md` (M2) |
| 4 | AST-based import-boundary enforcement | A — Committed | H0, start now | `guardrail_enforcement_epic.md` (M1) |
| 5 | Convert 2 proven-failing prose rules to hooks | A — Committed | H0, start now | `guardrail_enforcement_epic.md` (M2, M3) |
| 6 | Remove/archive knowledge-gateway | A — Committed | H0, start now | `standalone_items.md` (§1) |
| 7 | Migrate the 2 remaining sidecar stragglers | A — Committed | H1, schedule later | `workflow_reliability_epic.md` (M1) |
| 8 | ~~`tools.jsonl` sharding + reconciled lifecycle~~ **SUPERSEDED — already shipped** on `main` (PR #112, `TCK-20260902/903-MONITORING-*`, found during planning discussion) | A — Committed | H1 (was) | `telemetry_retention_epic.md` (M1 note; remaining scope is M2/M3) |
| 9 | Model-diverse reviewer — deploy shadow logging | A — Committed | H1, schedule later | `review_independence_epic.md` (M1) |
| 10 | Extend `cost_proxy_score` coverage | A — Committed | H2, schedule later | `standalone_items.md` (§2) |
| 11 | `working_log.csv` parser and cleanup | A — Committed | H2, schedule later | `standalone_items.md` (§3) |
| 12 | Provider-portability conformance test | A — Committed | H2, schedule later | `standalone_items.md` (§4) |
| 13 | Filtered replay eval pilot + dataset hygiene + metric design | B — Experiment | H1 | `agent_evaluation_foundation_experiment.md` |
| 14 | Ticket-claim detection logging | B — Experiment | H1 | `workflow_reliability_epic.md` (M2) |
| 15 | Phase-level resume — design/validation-rule resolution | B — Experiment | H1 | `workflow_reliability_epic.md` (M3) |
| 16 | Model-diverse reviewer — shadow comparison &amp; cutover decision | B — Experiment | H2 | `review_independence_epic.md` (M2) |
| 17 | Bash secret-exposure hook — blocking-escalation decision | B — Experiment | H2 | `governance_capability_policy_epic.md` (follow-on, post-M5) |
| 18 | Model-based routing for mechanical agents | C — Future option | H2, blocked | `bucket_c_future_options.md` |
| 19 | Task-success-rate metric closing the improvement loop | C — Future option | H3, blocked | `bucket_c_future_options.md` |
| 20 | Full agent-behavior eval platform | C — Future option | H3, blocked | `bucket_c_future_options.md` |
| 21 | Live Codex provider pilot | C — Future option | H3, blocked | `bucket_c_future_options.md` |
| — | Workflow-engine migration, A2A, full sandboxing, general AI-config platform, general command-risk policy | Rejected | — | `bucket_c_future_options.md` (§"Explicitly not recommended") |

12 committed items (bucket A) were originally scoped — **11 still to implement, plus item 8, found
during planning discussion to already be shipped on `main`** (see the Horizon 0/1 entries above and
`telemetry_retention_epic.md`'s M1 note) — 5 experiments (bucket B), 4 blocked future options
(bucket C), plus 5 explicitly-rejected directions — the full set brainstormed in the frozen
proposal, none silently dropped from this planning pass.

## Epics and detail docs

### Horizon 0 — start now

- **Epic G — Governance &amp; Capability Policy** (`governance_capability_policy_epic.md`): items
  1–3. Per-agent tool scoping, the Bash secret-exposure advisory hook, and the capability-envelope
  baseline.
- **Epic H — Guardrail Enforcement** (`guardrail_enforcement_epic.md`): items 4–5. AST boundary
  enforcement plus the two prose-rule-to-hook conversions with directly observed repeated-failure
  evidence.
- **Standalone — knowledge-gateway removal** (`standalone_items.md` §1): item 6. Not an epic —
  independent value, independent rollback — but shares one real dependency with Epic G (below).

### Horizon 1 — ready, schedule later (horizon label is strategic staging, not an automatic execution-order constraint — three items below have no H0-gate dependency at all)

- **Epic — Workflow Reliability** (`workflow_reliability_epic.md`): items 7, 14, 15. Item 7
  (sidecar stragglers) is Bucket A / READY with **no H0-gate dependency** — it may start in
  parallel with Horizon 0, capacity allowing; the `.claude/settings.json` overlap noted below is a
  git coordination concern, not an architectural one. Items 14–15 are Bucket-B experiment/design
  work within the same epic grouping, matching the frozen proposal's own worked-example grouping
  (sidecar migration + phase resume + ticket-claim detection = one epic).
- **Epic — Telemetry &amp; Retention** (`telemetry_retention_epic.md`): item 8's original scope is
  **superseded — already shipped** on `main` (found mid-planning; see the epic doc's M1 note).
  Remaining live scope is the repo-wide artifact-retention classification and ownership
  documentation (M2/M3), unaffected by the H0 gate — may start immediately, capacity allowing.
- **Standalone — Review Independence, M1 only** (`review_independence_epic.md`): item 9 (shadow
  logging deployment). Independent value, independent rollback, independent of the H0 gate.
- **Experiment — Agent Evaluation Foundation** (`agent_evaluation_foundation_experiment.md`):
  item 13. The single highest-leverage piece of evidence-generating work in the whole roadmap —
  every Bucket-C item downstream is gated on its exit criteria.

### Horizon 2 — ready, schedule later / experiment follow-ons

- **Standalone items** (`standalone_items.md` §2–4): items 10–12. `cost_proxy_score` coverage,
  `working_log.csv` cleanup, provider conformance test — three independent, low-effort committed
  items.
- **Experiment follow-ons**: item 16 (`review_independence_epic.md` M2) and item 17
  (`governance_capability_policy_epic.md`'s post-M5 follow-on) — both are decisions that can only
  be made once their Horizon-0/1 committed counterpart has run long enough to produce real data.

### Horizon 3 &amp; preserved options — not planned, not blocked-indefinitely either

- **`bucket_c_future_options.md`**: items 18–21, each with a named prerequisite (not a date), plus
  the explicitly-rejected directions re-evaluated independently rather than inherited from the
  earlier maturity audit.

## Cross-item dependencies

Four distinct dependency types appear below — kept distinguished deliberately, since collapsing
them was the source of two real inconsistencies this roadmap previously had (see "Corrections"
below the exit gates section):

- **Hard prerequisite** — B cannot safely proceed without A having already happened.
- **Observation gate** — B is a decision that can only be made once A has run long enough to
  produce real data; A itself is not blocked by this.
- **Shared-file coordination** — A and B touch the same file but neither depends on the other's
  *design*; resolved by a normal rebase at merge time, not by sequencing.
- **Execution-timing recommendation** — B is technically startable regardless of A, but running it
  after A avoids a real, named risk.

1. **Hard prerequisite** — `scan_for_secrets()` extraction gates both item 2 (Epic G, M4) and item
   6's archival step (`standalone_items.md` §1). Extract before either proceeds; neither blocks
   the other beyond that shared prerequisite.
2. **Shared-file coordination, not a dependency** — `.claude/settings.json`'s `hooks` block is a
   three-way file-overlap point: item 2 (Epic G, M4 — new hook entry), item 5 (Epic H, M3 —
   possibly a new hook entry, mechanism TBD), and item 7 (Workflow Reliability, M1 — edits the
   *existing* inline sidecar-check hook's embedded script). None of these three items architecturally
   depends on either of the others — same file touched ≠ roadmap dependency. See "Git &amp;
   delivery process" below for the rebase-based resolution.
   **Added during planning discussion**: every hook in `settings.json` is wrapped
   `2>/dev/null || true`, so a malformed entry from any of these three edits fails silently — the
   hook simply stops firing, with no error surfaced to whoever lands the change. The fix scoped to
   match the actual risk (not a general hook-telemetry subsystem, which would be disproportionate
   to a three-file collision): a static CI check that parses `settings.json` and validates each
   hook's embedded shell snippet syntax, plus a minimal smoke test confirming each of the three
   hooks in play still fires on a synthetic tool call after any of the three items lands. This
   belongs with whichever of items 2/5/7 lands first, not as a separate committed item.
3. **Execution-timing recommendation** — item 13 (the eval-pilot experiment)'s *actual replay run*
   is safer after item 7 (sidecar stragglers) lands: `agent_evaluation_foundation_experiment.md`'s
   Method requires the session-scoped sidecar fix to be reliable before replaying tickets in
   isolation. This does not block item 7 from starting on its own schedule (see Horizon 1 above)
   — it only means item 13's execution, not its planning, should follow item 7's completion.
4. **Hard prerequisite, scoped per item — not one blanket gate**:
   - Item 18 (model routing) — hard prerequisite: item 13's eval pilot produces a trusted
     baseline.
   - Item 19 (task-success-rate metric) — hard prerequisite: item 13 establishes a repeatable
     scoring approach.
   - Item 20 (full eval platform) — evidence prerequisite: item 13 proves the signal is useful and
     repeatable.
   - Item 21 (live Codex pilot) — hard prerequisite: item 12 (provider-conformance test) passing.
     Item 13 is an **additional** prerequisite only if the intended pilot includes a comparative
     quality evaluation between providers, not for a contract/runtime-only pilot (see
     `bucket_c_future_options.md` for the two possible pilot objectives — this repo's own prior
     design, `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`, does not yet commit to which one).
5. **Observation gate** — item 17 depends on item 2 having run long enough to produce a
   false-positive-rate measurement; item 16 depends on item 9 the same way. Both are "run the
   committed thing, then decide" pairs, not independent experiments, and neither blocks item 2 or
   item 9 from proceeding on its own schedule.

No dependency exists between Horizon-0 epics/items and Horizon-1 Telemetry &amp; Retention, or
between Telemetry &amp; Retention and any other Horizon-1 item — confirmed while writing this
roadmap, not assumed.

## Sequencing rules

- **Epics G and H (Horizon 0) run in parallel.** Neither gates the other.
- **Within Epic G**, M1 (usage audit) gates M3 (frontmatter rollout). M2 and M4 (once the
  extraction above lands) have no internal ordering constraint.
- **Within Epic H**, M1, M2, and M3 have no ordering constraint between them.
- **Horizon does not automatically impose execution ordering.** Nothing in Horizon 1 depends on
  the Horizon-0 exit signal by default — the exit signal below only gates items whose scope
  genuinely presumes H0's hardened governance posture already exists (none currently do). Item 7
  (sidecar stragglers), Telemetry &amp; Retention's M2/M3 (M1 superseded — already shipped), and
  Review Independence's M1 are all startable immediately, capacity allowing, in parallel with
  Horizon 0.
- **The eval-pilot experiment (item 13)'s actual replay run should be scheduled after item 7**,
  per dependency 3 above (execution-timing recommendation, not a start-blocking dependency) — item
  13 may still be planned/designed in parallel with item 7.
- **Horizon-2 committed items (10–12) have no dependency on Horizon-0 or Horizon-1** — they may
  start whenever capacity allows, independent of every gate on this page.
- **Horizon-2/3 experiment-follow-ons and Bucket-C items never start before their named
  prerequisite clears** — see Cross-item dependencies above and `bucket_c_future_options.md`.

## Git &amp; delivery process

Not yet exercised (no tickets exist), but stated now so the milestone breakdown above and the
eventual `create-tickets`/`implement-ticket` pass agree on how the work actually lands, per
CLAUDE.md's Worktree &amp; Branch Isolation and Commit Convention rules.

- **Worktree granularity: per ticket, not per epic or per milestone.** CLAUDE.md's default is one
  git worktree per unit of work. Once each milestone above becomes a ticket, it gets its own
  `EnterWorktree`-created branch off `origin/main` — the same way the 5 worktrees already active in
  this repo today (`m1-quick-wins`, `m4-institutions-economic-signals-implementation`,
  `navigation-canonical-hash-gap`, `worktree-monitoring-tools-weekly-sharding`,
  `brainstorm-idea-cross-index`) are each scoped to one unit of work. This planning pass itself
  stays directly on `main`, uncommitted, per direct instruction — it is not itself a unit of
  implementation work.
- **The `.claude/settings.json` three-way coordination point** (dependency 2 above): whichever of
  items 2, 5, or 7's tickets merges to `main` first lands cleanly; each subsequent ticket's branch
  rebases onto the updated `main` before opening its own PR, so hook entries/edits are added
  alongside prior ones rather than overwriting them. This is a normal git rebase step at merge
  time — it does **not** make any of the three items depend on the others in the roadmap sense,
  and does not require them to be worked in a fixed order.
- **Branch naming**: standard worktree-per-ticket naming once tickets exist — no epic- or
  milestone-level branch is created ahead of a real ticket.
- **Commit convention**: every commit for a milestone's eventual ticket references that ticket's
  `TCK-YYYYMMDD-SHORT-SCOPE` ID per CLAUDE.md's Commit Convention. No commits exist yet under any
  item in this roadmap — every doc in this subfolder predates ticket creation by design.
- **PR lifecycle**: one PR per ticket, following CLAUDE.md's standard PR Lifecycle steps (push →
  `gh pr create` → CI triage → report back; merge remains the user's call). Nothing about this
  roadmap changes that default flow — the three-way file-overlap note above is the only
  non-default consideration this roadmap introduces.
- **`agent-monitoring/` staging**: per Hard Rules, every commit for every milestone's ticket stages
  `agent-monitoring/` (including any trailing auto-write from the monitoring hook) alongside the
  substantive change — routine for this repo, called out here only for completeness.
- **Planning-doc claim visibility** (added during planning discussion): until an item in this
  subfolder becomes a real ticket, nothing marks it as "someone is actively working from this doc"
  — a real gap given how normal concurrent sessions are in this repo. Lightweight fix, not a new
  mechanism: whoever starts implementing an item from here should say so in the session/PR
  description that references it, the same way any other in-progress work gets flagged today.
  Worth a real claim marker only if this actually causes a collision in practice — not before.

## Shared exit gates

### Horizon 0 → Horizon 1 governance health-check (items 1–6)

Per the frozen proposal's §"Decision gates between horizons" — a general confirmation that the
Horizon-0 governance work landed cleanly, not a start-blocking gate on Horizon-1 tickets. **No
committed Horizon-1 item is currently known to hard-depend on this gate**: item 7 (sidecar
stragglers), Telemetry &amp; Retention's M2/M3 (M1 superseded — already shipped), and Review
Independence's M1 all proceed independently of it (see Sequencing rules). Its concrete effect today is narrower than "Horizon 1
begins" — it feeds item 17's observation gate specifically (dependency 5 above), and stands as a
general health-check before Horizon-2 items that presume a hardened governance posture. All four
conditions:

1. Per-agent capability policies (item 1) deployed with **zero critical workflow breakage** over 2
   weeks of normal operation.
2. The Bash secret-exposure advisory hook (item 2) shows an **acceptable false-positive rate** in
   normal advisory operation.
3. Both converted guardrail hooks (item 5) show **zero recurrence** of their target failure
   pattern across ≥2 subsequent weekly retro reports.
4. `knowledge-gateway` (item 6) archived with **zero renewed calls** observed over 2 weeks.

### Eval-pilot exit gate (item 13)

Per `agent_evaluation_foundation_experiment.md`'s own Exit Criteria: repeatable scoring
established, sample quality accepted for the 2 target defect classes, and replay contamination
risk demonstrably controlled. This directly gates items 18–20 (hard/evidence prerequisites) and
item 21 *only if* its intended pilot includes a comparative quality evaluation — item 21's primary
prerequisite is item 12 (provider-conformance test) regardless. See Cross-item dependency 4 above
and `bucket_c_future_options.md` for the per-item detail.

Both gates are evidence-based, not calendar-based — they fire when the stated signals are actually
observed, not on a target date.

## References

- `docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html` —
  the frozen proposal this roadmap implements in full (Revision 3, READY TO FREEZE, 2026-09-04).
- `docs/brainstorm/agent-working-design/ai_first_architecture_maturity_review.html` — the earlier
  maturity audit the proposal reassessed.
- `governance_capability_policy_epic.md` — items 1–3, and item 17's follow-on.
- `guardrail_enforcement_epic.md` — items 4–5.
- `standalone_items.md` — items 6, 10, 11, 12.
- `workflow_reliability_epic.md` — items 7, 14, 15.
- `telemetry_retention_epic.md` — item 8 (superseded — already shipped) and the remaining
  repo-wide retention/ownership work (M2/M3).
- `review_independence_epic.md` — items 9, 16.
- `agent_evaluation_foundation_experiment.md` — item 13.
- `bucket_c_future_options.md` — items 18–21 and the explicitly-rejected directions.
