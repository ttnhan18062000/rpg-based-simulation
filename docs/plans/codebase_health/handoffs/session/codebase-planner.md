---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-05
tags: [planning, delivery]
---

# Handover — codebase-planner
Updated: 2026-10-05 (#329 parked until 2026-10-18; batch `import-linter-adoption` in progress, planning commit 926285167 pushed and approved)

**On another machine:** fetch `import-linter-adoption`, copy `docs/plans/codebase_health/handoffs/session/*.md` into `.claude/handover/`; lines marked "(this machine)" describe the original VM only.

## Open
- Branch: none of mine · PR: **#329** (`python-code-craft-gates-flip`, codebase-implementer's; remote head `434000a3b` (docs-only on top of green `8b0865cf7`), CONFLICTING on REGISTRY.yaml until merge day; "BLOCKED" = ruleset, merge with `--admin`). Demo PR #331 closed, demo branch deleted.
- **New batch (2026-10-04 night): `import-linter-adoption`**, brief committed at `docs/plans/codebase_health/import_linter_adoption_ticket_brief.md` (planning commit 926285167; reviewed OK 2026-10-05; REGISTRY.yaml still to regenerate before the PR). Owner said yes to import-linter advisory + accept the 20 `src.<pkg>` roots (no `__init__.py` in src/). No test retired in this batch (testing condition 1); flip + retirement = new BLOCKED ticket 2. phase19's 5 kernel.py imports allowlisted pending rpg. My job: review each ticket commit and the PR; ask the owner before any push other than the handover-copy pushes on that branch.
- **Handover travels by git:** owner wants both codebase handovers pushed for the other machine. Committed copies at `docs/plans/codebase_health/handoffs/session/{codebase-planner,codebase-implementer}.md` on the `import-linter-adoption` branch, re-copied by the implementer at each push. On another machine: fetch that branch and read those copies first, then copy them back into `.claude/handover/`.
- Pending user decisions: none open. Owner-only, not yet raised: reopening `src/` for M7, the codebase-seat diff of `session_authority.yaml` (when agent-working's PR shows it).
- Awaiting: codebase-implementer works batch `import-linter-adoption` (worktree `rpg-import-linter`, this machine) and sends each ticket commit for review; nothing unpushed on #329. I message it on 2026-10-18 for tickets TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING, TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING (all in `agent-working/tickets/inprogress/` on that branch).

## What #329 contains (all reviewed and approved by me)
- Ratchet + mypy blocking; `REPORT_ONLY_TOOLS={jscpd}`; `SKIPPABLE_TOOLS={jscpd}` (npx can fail or stall: 300 s timeout → skipped, "not measured", never "gone"; seed/tighten/--from never skip). Jobs renamed `Code health` / `Type check`, `timeout-minutes` 20/10, only "Paths this PR changed" keeps continue-on-error. Package-registry step blocking + real-repo completeness test (Tools · a–e). ast-grep N3/N4/E3 blocking. 6 tightened + 4 deleted registry rows. No `src/`.
- Planning commit: brief, cycles addendum, roadmap 8.18/8.19 + M5 soaks line, import-linter conditions, handoff sections (agent-working: path-map entry + the `scope_files == 296` pin at `tests/unit/tools/test_mechanism_registry_completeness_check.py:191`, which fails any PR adding a `src/` file; rpg: M7 move ideas + kernel.py function-local imports decision; testing: flip notice, cc on the pin).
- Demos on #331, all proven: runs 37210551134 (Ubuntu 26.04 clean pass), 37210796539 (ruff+mypy fail), 37211037495 (no-row fail), 37213113973 (row → green), 37213577739 (ast-grep E3 fail; typed `except OSError: pass` to avoid ruff E722). The step 3 push (20386ff93) had the owner's yes.
- Soak reviews drafted: `docs/plans/codebase_health/python_code_craft_gates_soak_review.md` (69 runs, 4 real exit-1, 0 false positives; #291 SARIF live proof) and `python_code_craft_structure_soak_review.md`. Finalized on merge day.

## Dated next steps
- **2026-10-10 mid-soak check (by hand; no cron).** On origin/main, read the annotations (not the colour) of `Code health (advisory)` / `Type check (informational)` and the code-scanning runs, plus every PR merged since 2026-10-04 that touched `src/`. New/worse → owning planner (perf/asset via SendMessage; rpg/testing/agent-working: add to #329's handoff sections via the implementer, never a standalone PR).
- **2026-10-18 ≥ 05:00Z (12:00 local), one sitting, owner's yes at each step.** mypy reached main in #313 at 2026-10-04T04:59Z, so its window ends then.
  1. Implementer merges origin/main into #329 (expect a REGISTRY-only conflict), finalizes both soak reviews, re-runs ratchet (incl. ast_grep) / `packages validate` / mypy gate on fresh main.
  2. Closure commit (closure tool, working_log, ticket + staging moves, gates epic + `python-code-craft-gates/` folder to done; structure folder stays, import-linter is still open) → push → CI green.
  3. Owner adds required checks on `main`: exactly `Code health` + `Type check`. Never earlier (memory: required-check timing).
  4. `gh pr checks 329 --required` lists both.
  5. Merge `--admin --match-head-commit`; sync main; I announce to all planners (perf/asset live, the others via owner) incl. "open PRs need a re-run/push to report the new checks".

## For the owner (not tickets)
- (this machine) Main checkout is behind origin/main, with 2 dirty W40 tools shards (`main.tools.jsonl`, `python-code-craft-agent-integration.tools.jsonl`): on the next sync commit or move the extra lines; never a plain reset.
- (this machine) `data/runs/` cleanup undone; local clutter: untracked `src/social/`, `src/graphify-out/`, root `agent-monitoring/`, `reviews/`, `stored_artifacts/`; `graphify-out/graph.json` stale (rebuild OOMs at 2 GB).
- Follow-up noted in #329's body: `actions/setup-node@v4` Node 20 deprecation (frontend job shares it).

## Blocked codebase tickets
- `todos/python-code-craft-structure/TCK-20261004-IMPORT-LINTER-ADOPTION` (owner yes + rpg's kernel.py decision).
- `todos/codebase-domain-root/TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC` (scope-only).
- M7 refactor lane deferred while `src/` is frozen (debt: ~3,724 registry rows, 1,569 mypy baseline).

## Review checklist (lessons)
- Advisory jobs are always green: read summaries / `gh api .../check-runs/<id>/annotations` and the code-scanning runs.
- New tests must pass `tests/tools/test_*guard*.py`; compare pass/skip totals with main.
- A live-repo completeness test in a blocking lane makes the rule blocking.
- Dependency added to a group: re-run the `tests/static` pin tests.
- A REGISTRY-only CONFLICTING PR runs no workflows: merge main locally, push.
- A PR adding any `src/` file trips the `scope_files` pin until agent-working changes it: read every failing job.
- A subprocess timeout doesn't bound npx grandchildren: keep a job `timeout-minutes` backstop.
- Ask the implementer to run `git status -sb` before every push question.

## Pointers
- Brief (ignored copy): `.claude/handover/next-batch/python_code_craft_gates_flip_ticket_brief.md`; committed copy on #329 at `docs/plans/codebase_health/`.
- Roadmap `docs/plans/codebase_health/python_code_craft_roadmap.md`; handoffs `docs/plans/codebase_health/handoffs/`.
- Implementer handover: `.claude/handover/codebase-implementer.md`.
