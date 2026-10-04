---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, planning, process-improvement]
---

# Python Code Craft — M6 Agent Integration Ticket Brief (plus M5 follow-ups)

Scoping brief for `create-tickets`. The binding plan is
`docs/plans/codebase_health/python_code_craft_roadmap.md` (M6 row in Section 7, agent-facing design in 6.5,
owner decisions in Section 8). M1 to M3 are done; M4 is in its advisory soak until 2026-10-17; M5 merged
2026-10-04 (PR #315) with three blocked flip/adoption tickets. The owner chose M6 as the next codebase batch on
2026-10-04 and allowed the M5 follow-ups into the same PR.

**Owner decision 2026-10-04 (roadmap 8.17):** the codebase domain implements M6 itself, although
`.claude/**` is routed to agent-working in the session-layer registry (no agent-working session is running).
The PR names agent-working as the owner of those paths, and agent-working gets an FYI in the codebase-planner
outbox.

## Constraints that apply to every ticket

- **No file under `src/` may be modified** (decision 8.7). Every ticket's acceptance criteria include a
  `git diff --stat` check showing no `src/` path.
- **Governing files** (`CLAUDE.md`, `.claude/settings.json`, `.claude/agents/**`, `.claude/skills/**`) are edited
  only by tickets 3 and 4, and only the files named there. The owner confirms the **literal diff** of
  `.claude/settings.json` and `.claude/agents/implementer.md` before the commit that contains it. `CLAUDE.md` is
  not edited (roadmap 6.5: no generic craft text in `CLAUDE.md`).
- **Nothing in this batch blocks a PR or a tool call.** The edit hook only adds advisory context and always exits
  0. New CI output is advisory, in the existing advisory jobs.
- **The M4 soak and the M5 soaks are not disturbed.** No threshold, tool version, or existing row in
  `codebase/baselines/code_health_exceptions.jsonl` changes. The package-registry schema does not change
  (ticket 1 fills an existing field).
- Tests that pin CI or the Makefile may be edited (decision 8.11); the testing planner gets an outbox note.
  Tests owned by other domains are not edited. Agent-working's tests (`tests/agent_orchestration/`,
  `tests/tools/test_settings_json_*`) may be **extended** for the new skill and hook; an existing assertion is not
  weakened.
- Heavy local runs go one at a time under a memory cap (`systemd-run --user --scope -p MemoryMax=2G`).

## Facts measured 2026-10-04 (planner, on `main` at 7fac62b9)

- `codebase/structure/package_registry.jsonl`: 36 rows, **0 with `exemplar_modules`**, 4 with `do_not_imitate`.
  The validator already checks that cited paths exist.
- `codebase/gates/sarif_feedback.py` builds SARIF from ruff and complexipy only (`_tool_sarif`). The pinned
  `ast-grep-cli` 0.45.3 supports `ast-grep scan --format sarif`. The SARIF job (`code-health-sarif` in
  `.github/workflows/test.yml`) runs `uv sync --locked --no-install-project`, which installs the default `lint`
  group that holds `ast-grep-cli`.
- `codebase/health/scan.py`: `ast_grep` is in `ALL_TOOLS` but not in `OFFLINE_TOOLS`, so the snapshot
  (`codebase/health/metrics.py::compute_craft_metrics`, per-dimension counts, never a combined score) has no
  ast-grep dimension. ast-grep is a local binary, so it qualifies as offline. 111 `ast_grep` rows are seeded.
- `codebase/gates/staged_ratchet.py` already does "ruff on given `src/**/*.py` files, compared with the
  registry rows of those files by `ratchet.compare`", with a skip-not-fail rule when it cannot run. The edit
  hook reuses this logic; it does not write a second comparison.
- `.claude/settings.json` PostToolUse has an `Edit|Write|MultiEdit` matcher (graphify update) and three `*`
  hooks. Wiring is pinned by `tests/tools/test_settings_json_hooks_wiring.py`. Hook events are also declared in
  `agent-working/agent-orchestration/hook-surface-policy.yaml`.
- `registries/capability_envelope_registry.jsonl` (118 rows) tracks `permissions.allow` and MCP fields only, not
  hooks. Roadmap 5.8 says new hooks must be added there; the hook ticket checks whether the validator covers
  `hooks` and, if not, records that as a finding for agent-working **without** extending the schema.
- Skills are catalogued in `agent-working/agent-orchestration/skills.yaml` (pinned by
  `tests/agent_orchestration/test_skills_catalog.py`); several skills have a content test
  (`tests/tools/test_*_skill_content.py`). A Codex `.agents/skills/` generator exists; the skill ticket follows
  whatever the catalog test requires for a new skill.
- `.claude/agents/implementer.md` (112 lines) has a "Code Quality Rules" section with generic rules and no
  pointer to `docs/guidelines/python_code_standard.md`.
- PR #314 (session layer M1, open) changes `.claude/agents/session-*.md`, `registries/session_*.yaml` and
  `docs/guidelines/session_roles/**`, but not `implementer.md`, `settings.json` or `.claude/skills/`. Re-check
  before the push.

## Ticket 1: Exemplar modules in the package registry

- Fill `exemplar_modules` (0 to 3 paths) for the `active` packages by a written, repeatable criterion, measured
  on `main`: the module has **no row** in `code_health_exceptions.jsonl` (any tool), is between about 60 and 400
  lines, has a module docstring, and is not in any row's `do_not_imitate`. Prefer modules that other modules
  in the package import. A package with no qualifying module gets `[]`, and that is a valid result.
- The criterion and the measurement command go in `docs/plans/codebase_health/src_package_structure_audit.md`
  (a new short section), so a later reseed can repeat it. `reviewed` stays `false`: the owner reviews the picks
  in the PR and can veto any of them.
- `legacy` and `frozen` packages get no exemplars.
- Tests: the registry validator passes; a test pins that every exemplar has no registry row at the commit
  (fails if a future row is added for an exemplar, which is the signal to re-pick).
- Out of scope: changing the schema; `do_not_imitate` additions beyond what the measurement shows.

## Ticket 2: Review rubric

- A new section in `docs/guidelines/python_code_standard.md`, "Review rubric", for whoever reviews Python changes
  (the planner seat, and the `/code-review` style reviews):
  - Every finding is **Important**, **Nit** or **Pre-existing**. Only Important blocks.
  - At most 3 Nits per review; the rest are dropped.
  - Nothing a configured tool already reports is raised by hand (the Enforcement column says which).
  - A Pre-existing finding never blocks the change under review. If a tool reports it, it is already a registry
    row; if it is a reviewer rule and file-wide, it is proposed as a `do_not_imitate` entry in the package
    registry; otherwise it is mentioned once and dropped.
  - Each Important finding names the rule ID (F1, T3, E3, ...) or the architecture rule it breaks.
- Rubric text is short (one table plus up to 6 bullets). No examples here; examples go in the skill (ticket 4).
- Tests: a doc test pins the three categories and the "only Important blocks" sentence.
- Out of scope: changing any reviewer agent prompt (`.claude/agents/*review*`); the skill points at the rubric.

## Ticket 3: Code-health edit hook (advisory PostToolUse)

- `codebase/hooks/edit_ratchet_hook.py`: reads the PostToolUse JSON from stdin. If the tool is `Edit`, `Write` or
  `MultiEdit` and `tool_input.file_path` is an existing `src/**/*.py` inside the repo, run the staged-ratchet
  comparison on that one file (refactor `staged_ratchet.py` so both callers share one function; the pre-commit
  behaviour and its tests stay the same).
- Output: on NEW or WORSE, print the hook JSON with `hookSpecificOutput.additionalContext` holding the ratchet's
  report (capped at about 20 lines, with the count of the rest) and the standard's rule IDs. **Silent on pass.**
  Always exit 0, including when it cannot run (no ruff, no registry, timeout): then it prints nothing, so an
  unsynced worktree is not noisy. A hard time budget (about 5 seconds) kills ruff and stays silent.
- Wiring: one new entry in `.claude/settings.json` PostToolUse with matcher `Edit|Write|MultiEdit` and a command
  of the form `python3 -m codebase.hooks.edit_ratchet_hook 2>/dev/null || true`. **The owner confirms the
  literal settings.json diff before it is committed.** Extend `tests/tools/test_settings_json_hooks_wiring.py`
  to pin the entry. Check `hook-surface-policy.yaml` and update it if it lists hook commands.
- Capability envelope: check whether `tools/capability_envelope_baseline.py` covers hooks. If it does, add the row.
  If it does not, write the gap as a finding in the ticket and in the codebase-planner outbox for agent-working;
  do not extend the schema.
- Tests (`tests/codebase/`): new violation in the edited file gives additionalContext; grandfathered-only gives no
  output; a non-`src` or non-`.py` path, a path outside the repo, and malformed stdin give no output and exit 0;
  missing ruff and the time budget give no output and exit 0; the pre-commit path still rejects NEW/WORSE.
- Docs: `codebase/README.md` hooks row; `docs/guidelines/python_code_standard.md` Section 2 (the command table or
  a sentence: what the edit hook reports); `docs/guidelines/agent_working_environment.md` if it lists Claude
  Code hooks.
- Out of scope: ast-grep, complexipy or line-count in the hook (ruff only, for speed; the ratchet and CI cover
  the rest); `tools/**` and `tests/**` files; making any hook blocking.

## Ticket 4: `code-craft` skill and the implementer pointer

- `.claude/skills/code-craft/SKILL.md`: the standard's **reviewer** rules (F1, F2, F4, F5, N1, the trailing-digit
  part of N4, D2, D3, T2, T3, E2's justification and the E3 forms that ast-grep does not catch), each with a
  short bad/good pair taken from this repo's style (no `src/` edits; examples can be written fresh). Then: run
  `make code-health` or the staged ratchet before committing; what the edit hook's advisory message means; look up
  the package's row in `codebase/structure/package_registry.jsonl` and imitate an `exemplar_modules` entry, never a
  `do_not_imitate` one; the review rubric (ticket 2) for reviewers. No rule text is duplicated from the standard
  beyond the rule ID and one line; the standard stays the source.
- Catalog: add the skill to `agent-working/agent-orchestration/skills.yaml` and do whatever
  `test_skills_catalog.py` and the Codex generator require for a new skill (regenerate, do not hand-edit generated
  files).
- `.claude/agents/implementer.md`: one short pointer in "Code Quality Rules", e.g. "For Python code, follow
  `docs/guidelines/python_code_standard.md`; load the `code-craft` skill for the reviewer rules and examples."
  No other change to that file. **The owner confirms the literal diff before it is committed.**
- Tests: a content test in the style of `tests/tools/test_*_skill_content.py` (the rule IDs it covers exist in the
  standard; the paths it cites exist); the catalog test passes; a test pins the implementer pointer.
- Out of scope: a `safe-refactor` skill (M7); `CLAUDE.md`; other agent files.

## Ticket 5: ast-grep in the SARIF feedback and the snapshot

- SARIF: `codebase/gates/sarif_feedback.py` also runs `ast-grep scan --format sarif` (with the repo's
  `codebase/rules/sgconfig.yml`) on the changed `src/` files and filters out findings whose `(file, symbol, rule)`
  is already an `ast_grep` registry row within ceiling, the same way ruff and complexipy findings are filtered.
  A missing ast-grep binary is a "could not run" result (exit 2, summary line, warning), never a silent pass.
- Snapshot: add `ast_grep` to `OFFLINE_TOOLS` and add **one count per rule** (`n3`, `n4`, `e3`) to
  `compute_craft_metrics` as new dimensions. Existing dimensions keep the same values on the same tree (a test
  computes them before and after on the fixture). Check that the snapshot history schema accepts new keys; if a
  schema change is needed, it is additive and documented in the ticket.
- Tests: SARIF with an ast-grep finding that is new, one that is grandfathered, and a missing binary; snapshot
  metrics with and without ast-grep findings; existing dimensions unchanged.
- Out of scope: making ast-grep blocking (its flip ticket, soak ends 2026-10-18); new rules.

## Epic

`TCK-20261004-PYTHON-CODE-CRAFT-AGENT-INTEGRATION-EPIC`, scope-only, tracks tickets 1 to 5 and closes when all five
are done. Folder `agent-working/tickets/todos/python-code-craft-agent-integration/` with `SEQUENCE.md`:

1. Exemplar modules (no deps)
2. Review rubric (no deps)
3. Edit hook (no deps)
4. Skill and implementer pointer (depends on 1, 2, 3: it cites all three)
5. ast-grep SARIF and snapshot (independent)

All five ship in one PR together with this brief and the roadmap update (decision 8.17, M6 row).

## Not in this batch

M4 flip (2026-10-17), ast-grep flip (2026-10-18), package-registry flip, import-linter adoption (owner and testing
planner), M7 refactor lane (deferred; `src/` frozen), `safe-refactor` skill.
