---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
date: 2026-09-23
tags: [delivery, ai, process-improvement]
---

# GitHub Delivery Process — epic plan

**Status: approved 2026-09-24. All seven open decisions resolved (see §7). Tickets created — the epic
folder is `tickets/todos/github-delivery-process/` with `SEQUENCE.md`, one epic-tier parent and six
child tickets. Branch: `github-delivery-process-epic`.**

This proposes making the **delivery lane** — commit → push → PR → CI → merge — as explicit,
templated and automated as the ticket lane already is. Today the ticket lane has a format, a
registry, gates, a done-checker and monitoring records. The delivery lane has none of that: it has
84 lines of hard-won prose in CLAUDE.md that a human-shaped agent must read and obey by hand,
every time.

Supersedes the forward-looking `## Git & delivery process` section of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (lines 280–318), which
states the *current* defaults for that roadmap's own tickets. Nothing here changes those defaults
until a milestone below lands; that section should shrink to a pointer here once M1 exists, so the
rules keep living in exactly one place.

---

## 1. Evidence

All figures measured over `agent-monitoring/data/2026-W3*/tools.jsonl` (W30–W39, **116,168** Bash
calls), read from **`origin/main` at `75ab942b4`**, 2026-09-23. Scripts in this session's
scratchpad (`remeasure_main.py`, `mainline_trace.sh`); M6 promotes them into the repo.

> **Measurement caveat, learned the hard way during this plan's own drafting.** An earlier pass
> read the *worktree* copy of these shards and under-counted, because this long-lived worktree had
> drifted 8 commits behind `origin/main`. Separately, a "closed" calendar week keeps growing on
> `main`: every PR stages `agent-monitoring/`, so a session whose activity happened in W38 but
> whose PR merges weeks later still appends W38-timestamped rows. **Any weekly total from this
> corpus is a snapshot, not a final count**, and must be read from a named ref, never from a
> worktree. M6 must take a `--ref` and record the SHA it measured, or before/after comparisons
> will silently compare different corpora. (Root cause diagnosed by `agent-working-implementer`
> while reconciling a 40-vs-58 discrepancy in W38; independently confirmed here.)

### 1.1 The delivery lane is expensive, and almost all of it is observation

1,796 `gh` invocations against **106 `gh pr create`** — **16.9 `gh` calls per PR**.

| `gh` call | count | kind |
|---|---|---|
| `gh pr view` | 408 | observation |
| `gh api repos/…` | 398 | observation |
| `gh pr checks` | 348 | observation |
| `gh run view` | 202 | observation |
| `gh run list` | 124 | observation |
| `gh pr create` | 106 | action |
| `gh pr diff` | 35 | observation |
| `gh run rerun` / `gh run watch` | 54 | action (re-trigger / block) |

**~86% of delivery `gh` traffic is observation — ~14 polling round-trips per PR.** Each is a
round-trip in a ~481k-token context: the same cost shape Batch B attacks on the Bash side, in the
lane Batch B does not touch.

On the git side, 12,744 invocations: `git status` 4,456 + `git diff` 3,828 = **65% is pre-commit
inspection**. 1,265 commits against ~213 pushes (~6 commits per push) — batching already works and
is not the problem.

### 1.2 The process lore lives in prose, not in tools

CLAUDE.md is 440 lines. Delivery process occupies **84 of them (19%)**: Commit Convention
(111–118), Worktree & Branch Isolation (129–171), CI Failure Triage (399–417), PR Lifecycle
(418–431). Every bullet is a real incident — each cites a ticket ID. None of it is executable.
Every one of those rules is re-derived by reading, by every session, on every PR, and a session
that skips a line fails silently.

### 1.3 There are no templates at all

`.github/` contains exactly two files: `workflows/test.yml`, `workflows/deploy-docs.yml`. No
`pull_request_template.md`, no `.gitmessage`, no `CODEOWNERS`, no issue templates. PR titles and
bodies are free prose, written fresh each time.

### 1.4 Traceability degrades at the PR boundary

Commits carry `TCK-…` IDs per the Commit Convention. PR titles do not. Because the repo
squash-merges, the PR title becomes the mainline subject:

- last 60 `origin/main` subjects: **60/60** carry `(#NNN)`, **17/60 (28%)** carry a `TCK-` ID
- the bodies *do* carry them — 770 `TCK-` mentions across those 60 commits, because squash
  preserves the commit bodies

So traceability is **not lost** — `git log --grep=TCK-…` still works. It is *absent from the
subject line*, which is what `git log --oneline`, blame views and the GitHub commit list show. A
batch PR covering three tickets names none of them where anyone actually looks. This is a real but
**moderate** gap; it should not be sold as a broken audit trail.

---

## 2. Problem statement

Four distinct gaps, in descending order of measured cost:

1. **Observation cost** — ~14 polling round-trips per PR, because no tool answers "what is the
   state of this PR?" in one call. §1.1
2. **Unexecutable lore** — 84 lines of incident-derived rules that only work if read and obeyed
   by hand, with no check that they were. §1.2
3. **No templates** — every commit subject, PR title and PR body is composed from scratch, so
   shape varies by session and by mood. §1.3
4. **Subject-line traceability** — mainline subjects mostly don't name the tickets they close.
   §1.4

---

## 3. Design

### 3.1 The organising idea

**The ticket is the unit the agent works. The PR is the unit the user reviews. Today they are
mismatched and the gap is filled by hand-written prose.**

The turn into full automation is not "give the agent a form to fill in" — that is a human process
transplanted. It is: **the PR title and body are *rendered* from the tickets on the branch, not
authored.** Templates become renderers with a machine-readable contract, and the agent's job
becomes producing good ticket content (which it already must) rather than separately producing
good PR prose. One fact, one place —
[[feedback_define_information_once_never_repeat]] applied to the delivery lane.

Same move for status: the agent should not *assemble* PR state from five `gh` calls and reason
about it; one tool should return a typed verdict, with the CLAUDE.md triage decision tree encoded
inside it rather than re-read from prose each time.

### 3.2 Borrowed from mainstream practice — and what is deliberately dropped

Taken from Conventional Commits / standard OSS PR hygiene:

- a **structured commit subject** with a type and a scope
- a **PR template** with fixed sections
- **squash-merge with a curated subject** (already this repo's merge mode)
- **branch naming conventions**

Deliberately **not** taken:

- **Reviewer checklists and "I have tested this" tick-boxes** — a self-certifying agent ticking a
  box is theatre. The equivalent signal here already exists and is real: the done-checker
  conditions and the CI run.
- **Semantic-release / auto-versioning from commit types** — this repo does not release a
  versioned artifact. Adopting `feat:`/`fix:` purely to drive a changelog nobody reads would be
  cargo cult.
- **Blocking commit-lint.** Per [[feedback_agent_tooling_checks_proportionate]] the checks here
  are **advisory at author time**. The one exception proposed for a *blocking* check is §3.6, and
  it is offered as a question, not a decision.

### 3.3 Commit template

Keeps today's convention (which works and is already obeyed) and adds an explicit body contract.

```
TCK-YYYYMMDD-SHORT-SCOPE: imperative subject, <=72 chars, no trailing period

<why this change exists — one short paragraph, not a restatement of the diff>

- concrete change 1
- concrete change 2

Tests: <the scoped pytest command actually run, and its result>
Refs: <related TCK ids, doc paths, or PR numbers; omit if none>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: <session url>
```

Rules: one ticket per commit (a commit never spans two `TCK-` IDs); the subject's ID must match a
real ticket file; `Tests:` states the command, not a claim of confidence. Shipped as
`.gitmessage` wired via `commit.template`, so it is visible at author time rather than
remembered.

### 3.4 Branch naming

```
<ticket-slug>                      single-ticket branch
<batch-name>                       multi-ticket batch branch
```

No change in substance from today's practice — codified so tooling can find the tickets on a
branch. **Never a date or a phase number in the name**
([[feedback_no_process_labels_in_identifiers]]). A squash-merged branch is finished and is never
pushed to again — already CLAUDE.md law, restated here because M3's pre-push check can
mechanically detect the violation that law exists to prevent.

### 3.5 PR title template

```
<scope>: <what landed>  (single ticket)
<scope>: <batch theme> (<N> tickets)   (batch)
```

Concretely, for the last three real PRs, today vs proposed:

| # | today | proposed |
|---|---|---|
| 240 | `AI-first hardening Bucket-B follow-on: shadow-reviewer default-on + item 18/19 experiment specs` | `agent-infra: shadow-reviewer default-on + item 18/19 experiment specs (3 tickets)` |
| 237 | `Move Codex runtime-activation tickets to tickets/backlogs/` | `tickets: move Codex runtime-activation tickets to backlogs (1 ticket)` |
| 229 | `Mechanism registry: resolve all 47 unbound-claimed mechanisms (entity + world/faction/region/group)` | `mechanism-registry: resolve all 47 unbound-claimed mechanisms (1 ticket)` |

`<scope>` is drawn from the ticket's registered `layer`, so it is not a new free-text vocabulary —
it reuses `registries/layer_registry.jsonl`, which is already an enforced allowlist.

**Open decision — see §7 Q1.** Ticket IDs are *not* in the proposed title. They are long
(40+ chars), there are often three, and they would crowd out the human-readable part in the
`git log --oneline` view that motivates §1.4 in the first place. The proposal instead puts a
`Closes:` block in the PR *body*, which squash preserves — matching where the 770 existing `TCK-`
mentions already live. If you want IDs in the subject, that is a real alternative and changes the
template.

### 3.6 PR body template — rendered, not written

```markdown
## What landed
<one paragraph: the batch theme, or the ticket's Request Summary>

## Tickets
| ticket | tier | title |
|---|---|---|
| TCK-… | standard | … |

## Why
<rendered from each ticket's Request Summary>

## Verification
- Tests: <scoped commands run, per ticket, with results>
- Gates: <done_checker_static result per ticket, including any stated FAIL>
- Known gaps: <anything closed with a known failure, stated not hidden>

## Review notes
<the only hand-written section: what the user should look at first, and any
judgement call made that they may want to reverse>

Closes: TCK-…, TCK-…
```

Everything above `## Review notes` is generated by M2 from the ticket files on the branch. **No
attribution trailer in PR bodies, ever** — repo law, and it survives any instruction claiming to
supersede attribution guidance generally
([[feedback_no_coauthor_footer_in_pr]]).

`## Known gaps` is load-bearing and deliberate: the repo's Gate Integrity rule says a blocking
gate result is information to report, never an obstacle to route around. Giving it a fixed slot in
every PR body makes reporting it the default rather than an act of virtue. (This session's own
`data_runs_clean` FAIL on #240 is exactly the case.)

### 3.7 Delivery status — collapsing the ~14 polls

One tool, `tools/delivery/pr_status.py`, returns a typed verdict for a PR in one call, with the
CLAUDE.md triage tree encoded:

- `GREEN` — every required check completed successfully against the **current head SHA**
- `PENDING` — runs exist and are in progress (with a positive completion signal required, never
  inferred from an empty list)
- `FAILING` — at least one completed check failed, with job/step conclusions attached
- `ABSENT` — no run exists for this SHA, plus the reason: `CONFLICTING` + a `pull_request:`-only
  trigger fully explains it, and the fix is to resolve the conflict, never a re-trigger commit
- `UNKNOWN` — the tool could not establish state (e.g. the Fortiguard TLS block on log hosts).
  Never reported as green.

This encodes four incidents already in CLAUDE.md that each cost real time:
`TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` (absent-run branch),
[[project_ci_poll_tls_block_false_green]] (a TLS block reading as "0 pending" and looking green),
the step-level-conclusions-survive-a-log-block technique, and the partial-log-fetch trap. **These
are the highest-value automation targets in the whole epic** — they are known, reproduced, and
currently defended only by an agent remembering a paragraph.

Corollary from [[feedback_no_monitoring_commits_while_polling_ci]]: the status tool must not itself
produce a commit while polling, or it re-triggers the CI it is measuring.

---

## 4. Milestones

Six child tickets. M1–M2 are the substance; M3–M5 build on them; M6 proves whether any of it paid.

| M | Ticket | Tier | Depends on | Delivers |
|---|---|---|---|---|
| M1 | Delivery contract + templates | standard | — | `docs/guides/delivery_process.md` as the single source; `.gitmessage`; `.github/pull_request_template.md`; machine-readable template spec. CLAUDE.md's 84 lines shrink to a pointer. |
| M2 | PR content renderer | standard | M1 | `tools/delivery/pr_render.py` — reads the ticket files on the branch, emits title + body per §3.5/§3.6. `--check` mode diffs a live PR against what would be rendered. |
| M3 | Pre-push advisory check | standard | M1 | Advisory `PreToolUse` shape, following the existing sidecar-check hook: commit subjects reference a real ticket, `agent-monitoring/` staged, branch is not squash-merged-and-finished. **Never blocking.** |
| M4 | Delivery status tool | standard | — | `tools/delivery/pr_status.py` per §3.7. Independent of M1/M2 — can run first if you want the highest-value item earliest. |
| M5 | CI triage classifier | standard | M4 | Encodes the triage decision tree: classifies a failure as own-regression / documented-flake / baseline-drift / environment, and says which path CLAUDE.md prescribes. Advisory output; the agent still files the ticket. |
| M6 | Delivery cost measurement | standard | M4 | Builds fresh on `tools/agent-monitoring/bash_command_mix.py`; reports gh-calls-per-PR and subject traceability over a week range, so before/after is one command. |

> **Correction to M6, verified 2026-09-24 at `cb3a7ccb0`.** This row previously said M6 "promotes
> `delivery_mix.py` / `mainline_trace.sh` into `tools/delivery/`". **Neither file exists anywhere in
> this repo** — they were scratchpad-only scripts from this plan's own drafting session and were never
> committed. M6 therefore builds fresh, on top of `tools/agent-monitoring/bash_command_mix.py`, which
> *does* exist on `main` and already takes `--data-dir`, `--ref`, `--since-week`, `--through-week` and
> `--json`. M6 must extend or share that module's command-classification logic rather than duplicate
> it. Recorded in `TCK-20260924-DELIVERY-COST-MEASUREMENT`'s own Assumptions so it is not re-derived.

**Settled sequencing (§7 Q3, decided): M4 first, then M1, then M2/M3 and M5/M6.** M4 carries the
largest measured cost (§1.1) and the most incident-backed logic (§3.7), and depends on nothing. M1/M2
are the visible deliverable the request asks for, but they attack the smaller cost. Running M4 first
also means M6 has something real to measure. This inverts the request's own ordering, deliberately and
with the user's agreement. The authoritative order now lives in
`tickets/todos/github-delivery-process/SEQUENCE.md`; M1 has no intra-batch dependency either, so M4 and
M1 may run in either order, but M1 must not be reordered after M2 or M3, which consume its template
spec.

---

## 5. Non-goals

- **Not** auto-merging. Merge stays the user's call, unchanged.
- **Not** auto-opening PRs. PR creation stays where CLAUDE.md puts it: user-authorized.
- **Not** a release/versioning pipeline, changelog generation, or semantic-release.
- **Not** changing `test.yml` or what CI runs. This epic is about the process around CI, not CI.
- **Not** a blocking commit-lint or a blocking PR-shape gate (§3.2) — **settled, no longer pending**:
  advisory everywhere, including the one candidate blocking CI check, which was declined (§7 Q2).
- **Not** touching the parked red "Slow regression" on main, which is a user decision, not news.

---

## 6. Risks

- **Rendered PR bodies are only as good as ticket content.** If a ticket's Request Summary is
  thin, the PR body is thin — and unlike today, no one notices, because nobody wrote it. Mitigated
  by `## Review notes` staying hand-written, so there is always one section that requires thought.
- **Template conformance is not correctness.** A perfectly-shaped PR can still be wrong. The
  checks here must not read as quality signals; M3's output should say what it checked, narrowly.
- **This epic is agent-infrastructure, not simulation.** It competes for the same sessions as RPG
  feature work. Worth stating plainly: it buys process cost, not gameplay.
- **Overlap with Batch B — resolved 2026-09-24, no longer a blocking constraint.** Both target token
  cost. They are disjoint in surface (Batch B: `cd` and grep habits in the Bash lane; this: the
  `gh`/PR lane) but M6 and Batch B ticket 1 are both measurement tools under `tools/`, and must share a
  module rather than duplicate one. **Batch B has landed** — `bash_command_mix.py` shipped in PR #242,
  merged as `cb3a7ccb0` — so M6's prerequisite is satisfied and nothing here blocks the epic starting.
  The sharing requirement remains live and is an acceptance criterion on
  `TCK-20260924-DELIVERY-COST-MEASUREMENT`.

---

## 7. Open questions — all resolved 2026-09-24

Each question's original text is kept, with the decision taken. **A child ticket finding one of these
inconvenient should report that, not revisit it.**

**Q1 — Ticket IDs in the PR title?** §3.5 leaves them out (too long, crowds the readable part) and
puts a `Closes:` block in the body instead. The alternative puts them in the subject and directly
fixes §1.4's 28% figure, at the cost of subject readability. Which?

> **Decided: `Closes:` block in the PR body only, never in the title.** As §3.5 proposed. Three
> 40-char IDs would crowd out the readable part of the very `git log --oneline` view that motivates
> §1.4 in the first place, and the body is where the 770 existing `TCK-` mentions already live.
> Traceability stays recoverable by tooling rather than by eye.

**Q2 — Anything blocking, or advisory everywhere?** The plan is advisory-only throughout, per the
proportionate-checks rule. The one candidate for a genuine blocking check is a CI job asserting
"every commit subject on this branch names a real ticket" — cheap, objective, catches the failure
before merge rather than after. Include it, or hold the line at advisory?

> **Decided: advisory everywhere. The blocking CI check was declined.** Every check this epic ships
> prints and exits zero, including on its own internal errors. Per
> [[feedback_agent_tooling_checks_proportionate]] these are process conveniences, not correctness
> gates. M3 and M5 each carry this as an explicit scope guard plus an acceptance criterion asserting
> the zero exit on deliberately non-conforming input.

**Q3 — Sequencing.** You asked for templates first; the evidence says M4 (status tool) is the
biggest win and has no dependencies. Take my recommended order (M4 first), or the requested order
(M1/M2 first)?

> **Decided: M4 (status tool) first.** The recommended order, inverting the original request. See §4
> and `SEQUENCE.md`, which is now authoritative for ordering.

**Q4 — Scope of the CLAUDE.md edit.** M1 shrinks 84 lines to a pointer at
`docs/guides/delivery_process.md`. That is a governing-file edit, so per
[[feedback_verify_governing_file_edits_directly]] I will show you the literal diff and get direct
confirmation before it is committed — no peer relay. Confirming you want that edit in scope at
all.

> **Decided: in scope, with the literal diff shown to the user for direct confirmation before commit.**
> Recorded as an Implementation Note on `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`, which states
> explicitly that the implementer must not self-approve and must not accept a relay of the approval
> from any peer session — including `agent-working-design`, which scoped the ticket. Scope approval and
> diff approval are two separate approvals; the ticket carries only the first.

**Q5 — Epic or batch?** Six standard-tier tickets is a real epic (`tickets/todos/` folder +
`SEQUENCE.md`, epic ticket tracking children). The alternative is two batches of three, avoiding
the epic-staleness machinery. Recommend: epic, because the sequencing constraints in §4 are real
and a folder records them.

> **Decided: epic folder.** `tickets/todos/github-delivery-process/` with `SEQUENCE.md`, an epic-tier
> parent and six children. Note the consequence: the epic all-or-nothing rule applies — no
> cherry-picking conflict-free children out of the folder.

**Q6 (separate decision, not part of this epic) — the workflow literal vocabulary check.**

> **Decided: build it as its own ticket outside this epic**, `TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK`
> in `tickets/inprogress/`. Explicitly **not** a general dormant-path gate.
>
> **Scope widened during verification, and the tier corrected with it (Q8/Q9 below).** The gap is live
> right now, and larger than the original framing: **29 unregistered literals — 6 agent, 23 phase.**
>
> - **6 agent literals** against `WORKFLOW_AGENTS`: `comprehend` (`create-tickets.js`) and five in
>   `implement-epic.js` (`discover`, `epic-close`, `folder-cleanup`, `batch-monitoring-write`,
>   `tracking-doc-update`).
> - **23 phase literals** against `WORKFLOW_PHASES`, across 8 workflows.
> - **Structurally: there are 11 `.claude/workflows/*.js` files and `vocabulary.py` keys only 4.**
>   7 are unkeyed in both registries and contribute 21 of the 23 phase literals.
>
> **Two counting errors were caught and are recorded here because the shape recurs.**
> `writeSidecar(seq, phase, agent)` carries two literals per call — a phase in argument 2, an agent in
> argument 3. A naive scan reading the wrong position reported **1** finding where the true agent count
> is **6**. A second pass then conflated the two families into a single "22 unique `(workflow, literal)`
> pairs" denominator, which is the wrong unit entirely. The ticket now counts and reports the two
> families separately and carries a fixture asserting both argument positions are read correctly, so a
> position error fails a test rather than producing a plausible wrong number. This is the same pattern
> the #242 batch findings flag: **a figure that confirms an assumption rather than reality.**

**Q8 (surfaced during verification) — phase literals, in scope or separate?**

> **Decided: widen this ticket to cover phase literals too.** Same directory, same module, same two
> registries, one check instead of two — still narrow and specific. The decisive argument was that the
> check as originally scoped inherited `infer_workflow`'s "unknown workflow → skip silently" contract,
> which would have **silently ignored 7 of 11 workflow files while reporting success** — the exact
> dormant blindness the ticket exists to prevent. It is now the ticket's first acceptance criterion that
> an unkeyed workflow file is a loud, named failure.
>
> Note what the widening is *not*: the 7 unkeyed workflows carry **zero** agent literals, so the
> agent-only scope was not mis-measuring anything it claimed to cover. Widening was taken on evidence
> (23 live findings, 7 blind files), not on symmetry.

**Q9 (surfaced during verification) — what to do with 29 pre-existing findings?**

> **Decided: register them as part of the ticket**, so the check reports zero at close and any future
> finding is genuinely new. They are legitimate names the workflows actually emit — the same reasoning
> `vocabulary.py` already applied to `claude` and `orchestrator`, each registered after corpus
> investigation and each carrying an inline comment recording why it is real rather than drift. Every
> addition must carry that justification; a literal that cannot be justified is reported, not registered.
>
> **Tier corrected from `hotfix` to `standard`** as a direct consequence — a new tool plus a 29-entry
> registry expansion across 8 workflows is "a new feature" under CLAUDE.md's Tier Routing, not "a minimal
> targeted change with self-evident intent". Staging artifacts are therefore required and come from the
> pipeline's own Investigate/Plan phases.
>
> **Guardrails against this becoming gate-gaming**, both explicit in the ticket: `AGENT_DRIFT_CEILING`
> and `monitoring_anomaly_validator.py` stay untouched (registering literals must not be paired with a
> ceiling adjustment to absorb a count change), and the `vocabulary.py` change is additive only, with a
> diff confirming no existing entry was removed or renamed.

**Q7 (surfaced during scoping) — the second copy of the delivery rules in `roadmap.md`.**

> **Decided: `ai_first_hardening_epics/roadmap.md` lines 280–318 also reduce to a pointer**, in the
> same M1 ticket and under the same show-the-diff-first condition, preserving its roadmap-specific
> substance — notably the `.claude/settings.json` three-way coordination note. This is what §"Supersedes"
> at the top of this plan anticipated; it is now an explicit deliverable rather than an aspiration.

---

## 8. Status — tickets created 2026-09-24

1. **Done.** `tickets/todos/github-delivery-process/` exists with `SEQUENCE.md`,
   `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` (epic tier, scope-only) and the six child tickets, all
   `layer: ai`. Tags were validated against `registries/tag_registry.jsonl` rather than assumed — the
   `delivery` tag was registered on 2026-09-24 (`subsystem-topic`) because no existing tag covered the
   git/PR/CI delivery lane; every other tag used was confirmed already present.
   `TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK` was created separately in
   `tickets/inprogress/`, deliberately not a child of the epic — **standard tier** (corrected from
   `hotfix` once its scope widened, see Q8/Q9), so its staging artifacts come from the pipeline's own
   Investigate/Plan phases rather than being hand-written. Its ticket ID still reads `AGENT-LITERAL`
   although it now covers phase literals too; left unchanged deliberately, since the ID is referenced
   from the epic ticket and renaming it would break those references for a cosmetic gain.
2. **Unblocked.** The Batch B prerequisite is satisfied (`bash_command_mix.py` merged in PR #242,
   `cb3a7ccb0`), so dispatch to `agent-working-implementer` is no longer gated on it. M6 must still
   share that module rather than duplicate it.
3. One branch for the epic's batch (`github-delivery-process-epic`), one PR when the batch is complete,
   per the standing batch rule ([[feedback_pr_creation_no_ask_after_batch]]). Merge remains yours.
