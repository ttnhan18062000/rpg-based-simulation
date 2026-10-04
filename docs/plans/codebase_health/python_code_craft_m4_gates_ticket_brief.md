---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-03
tags: [architecture, planning, process-improvement]
---

# Python Code Craft — M4 Gates Ticket Brief 

Scoping brief for `create-tickets`. The binding plan is
`docs/plans/codebase_health/python_code_craft_roadmap.md` (rev 2; M4 row in Section 7, toolchain in
6.2, registry and reseed rule in 6.3, owner decisions in Section 8). M1 to M3 are done (epic
`TCK-20261002-PYTHON-CODE-CRAFT-EPIC`, PRs #288 and #297). This brief says which parts of M4 become
tickets, under the owner decisions recorded below.

## Constraints that apply to every ticket

- **No file under `src/` may be modified** (decision 8.7). No autofix, no inline `# noqa` or
  `# type: ignore`. Existing violations stay in external baselines. Every ticket's acceptance
  criteria include a `git diff --stat` check showing no `src/` path.
- Governing files (`CLAUDE.md`, `.claude/settings.json`, Claude Code hooks, `.claude/agents|workflows|skills/`)
  are not edited. Git hooks (prek) are in scope; Claude Code hooks are M6.
- Tests that pin CI or the Makefile may be edited (decision 8.11); the `testing` planner is told before
  the change lands, and each edit is listed in the ticket with its reason.
- Heavy local runs go one at a time under a memory cap (`systemd-run --user --scope -p MemoryMax=2G`).
- Every gate ships **advisory first**. Flipping any gate to blocking is its own ticket after the
  two-week soak (decision 8.10), so no ticket in this batch makes a required check fail a PR.

## Facts measured 2026-10-03 (planner, on `main` at b90c3aa9)

- **mypy 2.1.0** (the locked version) over `src/` with the repo config, in an environment with the
  runtime dependencies: **1,569 errors in 236 of 710 files**, 48 s wall, about 400 MB peak. Top codes:
  `call-arg` 443, `arg-type` 342, `assignment` 207, `union-attr` 109, **`name-defined` 104**,
  `no-any-return` 98. Top files: `src/systems/strategic_systems/intelligence.py` 158,
  `src/core/updates.py` 142, `src/config/profiles.py` 89. The 104 `name-defined` errors are
  the undefined names pyflakes reported as F821 (some are real bugs, e.g. an undefined `random`);
  that finding is still un-routed to the rpg domain.
- CI `typecheck` job is informational: `mypy src/ ... || true` plus `continue-on-error: true`, with
  the comment "remove once the baseline error count is documented". Pinned by parity entry
  `INFRA-TYPE-001` (`docs/parity_ledger/infrastructure.yaml`) and
  `tests/codebase/test_typecheck_gate_configured.py` (asserts a step named mypy runs `mypy src/`).
- Ratchet: `python3 -m tools.code_health check` (exit 1 new/worse, 2 tool or registry unusable).
  Registry `registries/code_health_exceptions.jsonl`: 3,617 rows, **all `reviewed: false`** — ruff
  2,892, complexipy 384, line_count 283, jscpd 58. Seeded on the `python-code-craft` branch, so
  `src/` changes merged since then will show as new until the registry is reseeded on `main`.
- jscpd runs through `npx --yes jscpd@5.4.0` (Makefile `JSCPD_VERSION`); its own dependencies are not
  locked, which the roadmap flagged as blocking it from gating.
- No `.pre-commit-config.yaml` exists. `make install-hooks` copies `tools/hooks/post-commit-reindex.sh`
  into `.git/hooks/post-commit`; `.git/hooks` is shared by every worktree on this machine.
- No SARIF upload, reviewdog or diff-quality step exists in `.github/workflows/`.

## Owner decisions (recorded 2026-10-03; all four as recommended)

1. **mypy: soak or block now?** The roadmap says "mypy blocking through mypy-baseline". With a
   baseline, blocking only fails a PR that adds a new type error, but it immediately affects every
   domain that edits `src/`. **Decided: the same two-week advisory soak as the ratchet**, flipped in
   the same follow-up ticket.
2. **Changed-line PR feedback: SARIF upload to GitHub code scanning, or reviewdog PR comments?**
   SARIF needs `security-events: write`, shows findings in the PR's Files view and code-scanning tab,
   and costs nothing on a public repo; ruff and complexipy emit SARIF. reviewdog posts comments
   (`pull-requests: write`) and is noisier for agents re-reading PRs. **Decided: SARIF**, with the job
   summary as the primary place agents read.
3. **prek install: opt-in or automatic?** Because `.git/hooks` is shared across all worktrees, an
   install affects every session on the machine, including other domains'. **Decided: opt-in
   only** (`make install-git-hooks`), installing both the prek pre-commit hook and the existing
   post-commit reindex hook so neither overwrites the other.
4. **jscpd in the eventual blocking set?** **Decided: report only, never blocking**, until a
   lockfile exists; do not add a Node lockfile in this batch.

## Concern 0: Epic — Python Code Craft M4 Gates

Scope-only epic tracking tickets 1 to 5 and the soak-end flip (6). Closes when 1 to 5 are done and 6
is filed with its start date.

## Concern 1: Reseed the registry on main and start the soak with an advisory CI job

- Reseed `registries/code_health_exceptions.jsonl` on current `main` with `seed --force` (keeps
  `reviewed`, `retiring_ticket`, `added_date` for persisting keys, roadmap 6.3). Record the reseed
  commit and the row counts per tool before and after.
- Add a CI job `code-health` (name ends "(advisory)") that syncs the `lint` group plus Node for jscpd,
  runs `python3 -m tools.code_health check`, never fails the PR (`continue-on-error`), and writes a
  job summary: new or worse violations, with the ones in files the PR changed listed first. Add it to
  the job lists that existing CI tests enumerate (`test_ci_uv_install.py` `_LINT_JOBS`, coverage test).
- Record the soak start date (the merge date) in the ticket and the roadmap.
- Investigate measures the job's wall time; if it is above the current longest PR job (Integration,
  about 324 s), say so and propose a split before implementing.

## Concern 2: Changed-line PR feedback via SARIF (decision 2)

- ruff and complexipy write SARIF for files changed in the PR; upload with
  `github/codeql-action/upload-sarif` pinned by version; job permission `security-events: write`
  only on that job. Findings already in the registry are filtered out before upload so a PR shows
  only what it introduced.
- Advisory like Concern 1; may be a step in the Concern 1 job if the wall time allows.
- Security-tagged: the ticket touches workflow permissions, so the Security-Review phase runs.

## Concern 3: mypy baseline (advisory until the flip)

- Add `mypy-baseline` (pinned exactly) to a dependency group the `typecheck` job syncs; generate the
  baseline file from `main` (about 1,569 entries) at a stable path under `registries/` and record
  its size in the code-health registry per roadmap 6.3.
- Change the CI step to `mypy ... | mypy-baseline filter`, still advisory: drop `|| true` only in the
  flip ticket. Investigate confirms how `mypy-baseline` normalises line numbers so an unrelated edit
  above an existing error does not resurface it.
- `make typecheck-py` gains the same filter; update `INFRA-TYPE-001` evidence and
  `test_typecheck_gate_configured.py` (listing the edit), and the open-audit-backlog note the CI
  comment points to.
- Out of scope: changing `[tool.mypy]` strictness or excludes; fixing any error.

## Concern 4: prek git hooks, opt-in install (decision 3)

- `.pre-commit-config.yaml` run by prek (pinned): ruff check on staged `.py` files filtered through
  the ratchet (no new violations), `uv lock --check`. Fast: under 5 s on a typical commit.
- Opt-in Makefile target that installs prek's pre-commit hook and keeps the existing post-commit
  reindex hook; document in `agent_working_environment.md`. No automatic install anywhere.
- Out of scope: Claude Code hooks (M6), formatting (decision 8.3).

## Concern 5: Type-checker trial (report only)

- Run basedpyright (with its native baseline) and Pyrefly over `src/` on the same commit; record
  version, wall time, peak memory, error count, baseline support and overlap with mypy's errors.
- Output: a decision record in `docs/plans/codebase_health/` recommending keep mypy, replace, or add a
  second checker. No CI or dependency change.

## Concern 6 (file only, start after the soak): flip the gates to blocking

- Filed by the Concern 1 ticket with the soak end date (start + 14 days). Makes the ratchet (minus
  jscpd), the SARIF step if any, and the mypy baseline filter blocking for new violations only; removes
  `continue-on-error`; marks the checks required (an owner action in GitHub settings).
- Precondition recorded in the ticket: soak review of false positives and the reviewed-row count.

## Order

1 first (reseed must precede anything that reads the registry), then 2 and 3 in either order, 4 after
1, 5 any time. 6 waits for the soak.

## Not in this batch

M5 (package registry, ast-grep, import-linter evaluation), M6 (agent integration requests), M7
(refactor lane, deferred). Routing the 104 undefined names to the rpg domain is a separate hand-off
note, not an M4 ticket.
