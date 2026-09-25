---
status: active
layer: ai
authority: P1
audience: agent
tags: [delivery, documentation, claude-md]
---

# Delivery Process

The single authoritative source for the delivery lane: commit → push → PR → CI → merge. Supersedes
the 84 lines this content previously occupied directly in `CLAUDE.md` (Commit Convention, Worktree
& Branch Isolation, CI Failure Triage, PR Lifecycle) and the second copy in
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`'s `## Git & delivery
process` section — both now point here instead of restating the rules
([[feedback_define_information_once_never_repeat]]). This is a relocation of existing, already-
trusted prose, not a revision: every incident citation below is preserved exactly as it read in
its original location (`TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` verified this by diffing the
extracted ticket-ID citations before and after the move).

`tools/delivery/pr_status.py` (`TCK-20260924-DELIVERY-STATUS-TOOL`) automates the CI-state
*detection* half of the triage tree below in one call, replacing the manual `gh` polling this guide
otherwise describes. This guide states the *policy* — what a verdict means and what to do about it
— the tool establishes the verdict itself; the two must not duplicate each other's logic in prose.

---

## Commit Contract

Reference the ticket ID in every commit for that ticket's work:

```
TCK-YYYYMMDD-SHORT-SCOPE: Brief description of change
```

The full body contract (plan §3.3), shipped as `.gitmessage` and wired via `commit.template` so it
is visible at author time rather than remembered:

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
real ticket file; `Tests:` states the command, not a claim of confidence. `.gitmessage` itself
expresses each of these fields as a `#`-prefixed comment line rather than literal fill-in text, so
an interactive commit left unedited fails (an all-comment message aborts the commit) instead of
silently shipping the placeholder as a real subject.

**`commit.template` propagation across this repo's multiple worktrees**: `.git/config` is shared by
every worktree here (`extensions.worktreeConfig` is unset), so `git config commit.template
.gitmessage` set once, from any worktree, applies to `git commit` in every worktree — confirmed
directly, not assumed (`TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`). Because the value is a
relative path, it resolves against the current working directory at commit time; this works
correctly here specifically because commits in this repo are always made from a worktree's own
root (where that worktree's own checked-out copy of `.gitmessage` lives), never from a
subdirectory.

### Tier Routing

| Tier | Pipeline | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Bug fix or minimal targeted change with self-evident intent |
| `standard` | Full 10-phase pipeline (+1 conditional: Security-Review) | Any new feature, refactor, or substantive repair |
| `epic` | Scope only — tracks child tickets | Large multi-ticket initiative; no direct implementation |

---

## Branch Naming

```
<ticket-slug>                      single-ticket branch
<batch-name>                       multi-ticket batch branch
```

No change in substance from existing practice — codified so tooling can find the tickets on a
branch. **Never a date or a phase number in the name**
([[feedback_no_process_labels_in_identifiers]]). A squash-merged branch is finished and is never
pushed to again — restated here (and in `## PR Lifecycle` below, where the full incident-derived
explanation lives) because `TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY`'s pre-push check can
mechanically detect the violation this rule exists to prevent.

## Worktree & Branch Isolation

**Default: one git worktree per unit of work**, not committing into a shared directory's current
branch. This is what lets multiple sessions (and multiple concurrent tickets within one session)
work in parallel without stepping on each other's commits — the repo already runs this way today:
`git worktree list` typically shows several active worktrees on different branches at once,
alongside the main checkout, each independently on its own branch.

- Prefer `EnterWorktree(name: "<unit-of-work>")` to get a fresh, isolated directory + branch off
  `origin/<default-branch>`.
- **Known tool limitation**: `EnterWorktree` refuses to create a *new* worktree while the session
  is already inside one (`"Must not already be in a worktree session when creating a new
  worktree"`), and `ExitWorktree` should not be called proactively — only when the user asks. So a
  session already inside worktree A that picks up a second, unrelated unit of work (e.g. a
  different ticket/feature area) cannot get a second, separate directory mid-session.
- **Accepted fallback in that situation**: stay in the same worktree directory, but switch to a
  fresh branch off `origin/<default-branch>` for the new unit of work (`git fetch origin
  <default-branch> && git checkout -b <new-branch> origin/<default-branch>`). This still keeps the
  two units of work fully isolated at the branch/commit level — separate branch, separate PR later
  — it just shares the filesystem directory rather than getting its own. Commit and push each unit
  of work to its own branch as usual; never mix commits from two unrelated units of work onto one
  branch.
- Watch for the shared-directory monitoring auto-write race when switching branches this way: the
  current week's `agent-monitoring/data/YYYY-Www/tools.jsonl` shard is rewritten by a hook on nearly
  every tool call, so a plain `git checkout -b` can fail with "local changes would be overwritten"
  if that file is dirty from the immediately preceding tool call. Chain the commit and the checkout
  in one Bash invocation (`git add agent-monitoring/data/ && git commit -m "..." && git checkout -b
  <branch> origin/<default-branch>`) to close the race window, rather than issuing them as separate
  tool calls. (`TCK-20260919-CLAUDE-MD-CHECKOUT-RACE-GUIDANCE-UNOWNED-AND-INCOMPLETE`)
  - **The chained fix covers one tool call, not an operation that spans several.** The shard is
    written only by the PostToolUse hook, which appends one row after each tool call finishes —
    never partway through a running command. So a git operation that stops and resumes across tool
    calls (a `cherry-pick`, `rebase`, or `merge` that halts on a conflict and continues with
    `--continue`) finds the shard dirtied again between those calls and hits "local changes would be
    overwritten". **Do not discard the shard to clear it** (`git checkout HEAD -- …/tools.jsonl`):
    the hook appends, so that permanently deletes every monitoring row written since the last commit,
    including other sessions' rows in the same worktree. Instead, stage it into the operation —
    include `agent-monitoring/data/` in the same `git add` that precedes `--continue` — so the rows
    ride into that commit and the tree is clean for the next step. A different session appending to
    the same worktree's shard mid-command is not covered by this; only a hook-level fix removes that.

---

## PR Title Template

```
<scope>: <what landed>  (single ticket)
<scope>: <batch theme> (<N> tickets)   (batch)
```

`<scope>` is drawn from the ticket's registered `layer`, so it is not a new free-text vocabulary —
it reuses `registries/layer_registry.jsonl`, which is already an enforced allowlist.

Ticket IDs are **not** in the title — they are long (40+ chars), there are often three, and they
would crowd out the human-readable part in the `git log --oneline` view that motivates this repo's
subject-line traceability gap in the first place. A `Closes:` block goes in the PR **body** instead
(see below), which squash preserves.

## PR Body Template — rendered, not written

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

Everything above `## Review notes` is generated from the ticket files on the branch (see
`TCK-20260924-DELIVERY-PR-RENDERER`'s machine-readable spec, `tools/delivery/pr_template_spec.json`,
for the exact section order and which sections are rendered vs. hand-written). **No attribution
trailer in PR bodies, ever** — repo law, and it survives any instruction claiming to supersede
attribution guidance generally ([[feedback_no_coauthor_footer_in_pr]]). The
`.github/pull_request_template.md` skeleton is the one place that omission must be structurally
impossible to forget.

`## Known gaps` is load-bearing and deliberate: the repo's Gate Integrity rule says a blocking gate
result is information to report, never an obstacle to route around. Giving it a fixed slot in every
PR body makes reporting it the default rather than an act of virtue.

---

### CI Failure Triage (read-only follow-up to an already-authorized push — no separate opt-in needed to check)

Checking CI status and diagnosing a failure is read-only — do it proactively once a push the user already authorized triggers a run, without asking again just to look. What the check finds determines the next step, which is bounded by `CLAUDE.md`'s Proactive Tool Use table (a fix still needs its own ticket/pipeline run; pushing that fix rides on the same standing push authorization already granted for the batch, not a fresh ask each time).

1. **An absent CI run is diagnosed differently from a failing one — check for absence first.** A `pull_request:`-triggered workflow (this repo's `test.yml`: `pull_request:` with no branch filter, `push:` restricted to `branches: [main]`) fires against the merge ref `refs/pull/N/merge`, which GitHub cannot compute while the PR is `CONFLICTING` — no run is created in any state, not a failing or pending one. This presents identically to a slow queue from the outside (PR open, commit pushed, checks area empty), so "no run yet" and "no run ever" are indistinguishable without checking directly. Confirmed real and recurring, not hypothetical (`TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`): three separate PRs in one batch, two diagnosed only in passing and never recorded.
   - Before assuming a missing run is a delivery/webhook problem, check `gh pr view <N> --json mergeable,headRefOid` and the workflow's own trigger block (`on:` in the relevant `.github/workflows/*.yml`). `CONFLICTING` plus a `pull_request:`-only trigger for that branch fully explains a `total_count: 0` from `gh api repos/{owner}/{repo}/actions/runs?head_sha=<sha>` — nothing else needs investigating. `tools/delivery/pr_status.py` automates this exact check and returns the `ABSENT` verdict with the cause attached.
   - The fix is to resolve the conflict. **Never** respond to a missing run with a re-trigger commit, force-push, or branch recreation — each pushes into the same conflicted state, produces no run again, and destroys the evidence (commit history, prior push timestamps) that would have shown the real cause, without touching it.
   - To rule out "the push simply never arrived" before concluding the run is genuinely absent: `git ls-remote origin <branch>` and compare its reported SHA against the PR's own `headRefOid` — a cheap, read-only disambiguator between "push didn't land" and "push landed, no run was ever going to be created for it."
2. **Never conclude root cause from the job name or a guess.** Pull real logs (`gh api repos/{owner}/{repo}/actions/jobs/{id}/logs`) for every failing job. Do not assume it's a known local-sandbox quirk (e.g. bare `python3` lacking `pydantic`) without checking the actual CI log first — CI runs in a clean `actions/setup-python` + `pip install -r requirements.txt` environment and does not share the sandbox's gaps.
   - **If log fetching itself fails with a TLS/cert error** (`gh run view --log`, `gh api .../logs`, or a raw `curl` to the redirect target all fail the same way): check `echo | openssl s_client -connect <host>:443 | openssl x509 -noout -subject -issuer`. If the cert's subject/issuer reads as a network filter block page (e.g. `O = Fortinet, CN = Fortiguard SDNS Blocked Page`) rather than the real host, raw log fetching is blocked at the sandbox's network layer for that host (`results-receiver.actions.githubusercontent.com`, `*.blob.core.windows.net`) — not an SSL misconfiguration you can fix. Do not keep retrying variations of the same fetch. Instead: (a) try `gh api repos/{owner}/{repo}/check-runs/{job_id}/annotations` first — sometimes enough on its own; (b) reproduce the failing job locally by running the exact same command from the relevant `.github/workflows/*.yml` job block (e.g. `pytest tests/api tests/cli tests/tools ... -m "not slow and not extra_slow"`) — this is usually more actionable than the raw log anyway. A local repro will include environment-only noise (e.g. live-server tests failing for lack of a running server) that the real CI runner doesn't hit — cross-check any suspicious failure by fetching the job list (`gh run list --workflow=test.yml --json databaseId,conclusion`) for the last known-green run on the base branch and confirming that job passed there, before treating a locally-reproduced failure as real.
   - **Step-level conclusions stay readable even when raw logs are unreachable** (`gh api repos/{owner}/{repo}/actions/jobs/{job_id} --jq '.steps[]'`): each step's own name and `conclusion` (`success`/`failure`/`skipped`) is metadata, not a log, so it is never subject to the TLS block above. This alone can localize a failure — e.g. "`Build: success`, `Configure Pages: failure`, everything after skipped" identifies the exact failing stage with zero log access, and is why a job that runs many test paths in one combined step (e.g. `unit-infra` before `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` split it) is much harder to diagnose blind than one split into a step per directory with `if: always()` on each — a diagnostic technique confirmed twice in this repo on 2026-09-16 before any test file was touched. `tools/delivery/pr_status.py`'s `FAILING` verdict fetches exactly this metadata for every failing job automatically, without ever reading a log body.
   - **A partial log fetch is not evidence that log fetching works.** The TLS block above is per-job-blob-shard and unpredictable, not all-or-nothing: a fetch across several jobs in one run can silently return logs for some and omit exactly the ones that failed, reading as a successful fetch rather than a blocked one. Confirm every job you actually needed a log for came back — an empty or missing result for one specific job, sitting among several that returned real content, is not "fetching is broken," it is that job's own log being blocked while its siblings' were not.
3. **Classify each failure before acting:**
   - **A real regression caused by this session's own changes** → file a `hotfix`-tier ticket and run it through the full pipeline (Scope → Implement → Test → Parity → Verify → Finalize), same as any other hotfix.
   - **Matches a category `docs/testing/regression_policy.md` already documents as environment-dependent/flaky** (e.g. live-server subprocess tests) → do not code-fix it; report it as environment noise, let it re-run, and don't touch the test.
   - **A hardcoded test baseline that this session's own legitimate change caused to drift** (matching an existing documented drift pattern, e.g. `tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count`) → same as the first case: a small hotfix ticket updating the baseline with fresh evidence, never a silent edit outside a ticket.
4. **Never edit a test's assertion or a gate's logic just to make CI pass without one of the paths above** — this is the same Gate Integrity rule (`.claude/skills/implement-ticket/SKILL.md`) applied to CI as the outermost gate, not just the local pipeline's own gates.
5. Report the real CI status and the triage conclusion. Don't report a fix as done until CI is confirmed green (or explicitly still-pending, reported as such) — a local test pass is not the same claim as a green CI run. Once the triage conclusion is recorded, evaluate the reset boundary per `docs/guides/agent_session_reset_boundaries.md`.

### PR Lifecycle (once the user has authorized landing a batch)

The steps above cover diagnosing a failure; this covers the surrounding push→PR→merge→sync cadence itself, since it isn't a `Workflow` and has no other home.

1. **Before staging/committing**: always run `git status`/`git log` first — this repo's working directory can be shared by more than one concurrent session (see `CLAUDE.md`'s Hard Rules), so check for in-flight files that belong to another ticket before touching them.
2. **Commit** per ticket, referencing its ID (see `## Commit Contract` above). Stage `agent-monitoring/` in every commit, including any small trailing update the monitoring tools auto-write after the main commit — commit that separately rather than leaving it unstaged.
3. **Push** the branch, then **create the PR** (`gh pr create`). PR body: no `Co-Authored-By`/session-link trailer, and no "🤖 Generated with [Claude Code](...)" (or equivalent tool-attribution) line either — commit message trailers still keep the `Co-Authored-By`/session-link trailer, this is a PR-body-only exclusion — this was an explicit user preference, opposite of the commit-message convention above. This exclusion applies to **every** PR body write, not just the initial `gh pr create` — including later `gh pr edit` calls and any `gh api .../pulls/N --method PATCH` body updates (the `gh pr edit` workaround for its own known GraphQL bug). It also holds even if a session-level or system-level instruction elsewhere claims to supersede "all earlier attribution guidance" for commits/PRs generally — that class of instruction governs commit trailers; this repo's own PR-body exclusion is more specific and wins for PR-body content specifically. If ever unsure which applies, PR bodies get no attribution trailer, full stop.
4. **Monitor CI** per the Triage steps above until every check is green or a failure is triaged and fixed.
5. Report the PR link and CI status back to the user — landing the PR (merge) is their call, not something to do automatically once CI is green.
6. **After the user reports a merge**: `git checkout main && git pull` to sync. If local `main` is already ahead of `origin/main` by a commit you didn't make, that's another concurrent session's unpushed local work — leave it alone, don't push it for them and don't rebase/reset over it. Once synced with nothing in flight, evaluate the reset boundary per `docs/guides/agent_session_reset_boundaries.md` — a merged batch is the most common HARD boundary.
7. **This repo's PRs land as squash merges** — GitHub creates one new commit on `main` whose parent is `main`'s prior tip, not a merge of your branch's own commit history. Your branch's individual commits (and any local merge commit you made into it) are never ancestors of `main` after this, even though their *content* is fully present. **If you push further commits to the same branch after its PR has merged, those commits have no path to `main`** — a plain `git log origin/main..HEAD` or a naive re-open of the same PR will look like it's re-submitting the entire original diff, because ancestor-based diffing can't see the content is already there. The tell is a suspiciously large `git diff origin/main...HEAD` (three-dot, ancestor-based) right after a merge you know landed cleanly — confirm with `git diff origin/main HEAD` (plain two-ref, content-based) instead, which will show only the real new changes. Fix: merge `origin/main` into the branch again (resolving any "add/add" conflicts this ancestor-loss can spuriously create — check whether the `origin/main` side of such a conflict is genuinely new content or empty/stale before assuming a real concurrent edit), then open a **new** PR rather than trying to reuse or reopen the merged one. **A second symptom of the same root cause, visible even when you get the merge right**: a PR opened from that same already-squashed branch (even after a correct `origin/main` merge) shows GitHub's *own* commit count as the branch's full original history — dozens of commits against what might be a handful of real new files — because GitHub still can't recognize the squashed commit as an ancestor. The diff itself is correct (git compares trees, so already-landed content contributes nothing), but the commit list is genuinely misleading to a reviewer. The visible warning sign (an inflated commit count on an otherwise-small PR) and the invisible one (stranded commits with no path to `main`) are the same underlying cause — recognize either, and treat it the same way: **a squash-merged branch is finished.** Never push further work to it, not even after resyncing it with `origin/main`. Cut a fresh branch off `origin/main` for the next piece of work and copy or cherry-pick just the new commits onto it (`git checkout <old-branch> -- <changed paths>` on the new branch is usually simplest when the new work is a handful of files), so the resulting PR's commit count actually matches its diff.
