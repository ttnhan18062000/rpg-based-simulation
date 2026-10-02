---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, planning, process-improvement, documentation]
---

# Python Code Craft Roadmap — Standard, Modern Toolchain, Debt Registry, Refactor Lane

**State: rev 2, approved by the owner 2026-10-02 (decisions in Section 8). Tickets for M1 to M3 are
being scoped; M4 onward are not ticketed yet.** Author: `codebase-planner` session.

## 1. Purpose and scope

Keep `src/` well-written as it grows: good functions and classes, clear module structure, consistent
Python convention, and a way to see and pay down craft debt. Nearly all code here is written by
agents, so the plan is about what agents are held to, not about a human style preference.

**In scope:** a written Python code standard; a modern lint, typing, complexity, duplication and
architecture toolchain; a registry of known violations with a ratchet; agent-facing guidance and
review for craft; a package inventory for `src/`; later, a behaviour-preserving refactor lane.

**Out of scope:** RPG features and mechanics, performance work, test architecture (owned by the
`testing` domain, `tickets/todos/test-architecture/`), resilience and failure modes (D23), and any
change to simulation behaviour.

**Hard constraint (owner, 2026-10-02): no file under `src/` is modified by this plan until the owner
reopens it.** Many sessions are working there. So no autofix, no reformat, no inline suppression
comments. Every existing violation is held in an external baseline, and checks report only new or
worsened ones. Tooling, config, CI, registries, docs and agent guidance are all in play.

## 2. Evidence

Measured 2026-10-02 on `main` by an ad-hoc AST scan of `src/` (744 files, 3,108 functions). The
complexity figure is a rough branch count, not a standard tool, so treat it as indicative.

| Signal | Count |
|---|---|
| Functions over 50 / 100 / 200 lines | 458 / 169 / 42 |
| Functions with approximate complexity over 15 / over 30 | 254 / 85 |
| Classes over 500 lines / with more than 30 methods | 21 / 5 |
| Public functions without a docstring | 1,143 of 2,310 |
| Functions missing a return annotation | 154 |
| Functions with 8 or more parameters | 29 |
| Bare `except:` / mutable default arguments | 9 / 2 |

Worst cases: `create_v2_app` in `src/api/server.py` (2,409 lines, containing a 2,093-line nested
function), `EventExtractor.extract` (1,585 lines), `evaluate_entity_intent` in `src/engine/tactical.py`
(713), `evaluate_strategic_intent` in `src/systems/strategic_systems/intelligence.py` (541).

Tooling today: no Python linter or formatter config, no pre-commit. mypy is configured non-strict
with five packages excluded and runs as `mypy ... || true` in both `Makefile` and CI. Source grew
from 113k LoC (D24, 2026-08-17) to 126k.

Environment today: `uv` is installed and `uv.lock` is tracked but stale (last touched in PR #29); CI
installs with `pip install -r requirements.txt`. Dependencies are declared in three places
(`pyproject.toml`, `requirements.txt`, `uv.lock`). CI runs Python 3.13, `pyproject.toml` says
`>=3.11`, mypy targets 3.11.

Agent setup today: `implementer.md` carries no craft guidance; `architecture-reviewer` checks
architecture rules, not craft; no skill covers writing clean Python; no hook lints an edited file.

## 3. What outside research says (2026-10-02, four web passes)

Sources and caveats are in the session record; several figures came from secondary sources.

- **Duplication is the best-evidenced agent failure.** Agent PRs scored 1.87x human PRs on semantic
  redundancy (arXiv 2601.21276); agents also delete less.
- **Deterministic checks beat prose.** Anthropic and OpenAI ("harness engineering") both advise
  turning rules into lints and hooks instead of growing the instruction file, and writing lint
  messages as remediation instructions.
- **Reviewers over-report.** Review in a fresh context, on the diff plus explicit criteria, and
  exclude what a linter already covers.
- **Size is the metric that matters.** Cyclomatic complexity correlates about 0.9 with line count.
  No controlled evidence supports any specific size limit, so the thresholds below are conventions.
- **Agents imitate what they see.** Name good exemplars and mark known-bad files as not to imitate.
- **Agents under-refactor.** A standing cleanup lane is needed; one-off tickets do not hold.
- **Baseline support is uneven.** Ruff and ast-grep have no native baseline. basedpyright, Pyrefly,
  complexipy, `mypy-baseline` and import-linter do. This drives Section 6.3.

## 4. Existing work: reuse, extend, do not duplicate

| Area | What exists | Consequence for this plan |
|---|---|---|
| Repo-scale health metrics | `tools/codebase_health_baseline.py`, `codebase_health_snapshot.py`, `code_health_impact.py`, `pr_impact_report.py` (`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, done) | **Extend** the snapshot with craft metrics. Build no second metrics tool. Note: no snapshot has ever been taken. |
| Type checking | mypy config, `make typecheck-py`, CI step (`TCK-20260623-TYPE-CHECKER`, D13 F1). Pinned by parity ledger `INFRA-TYPE-001` and `tests/static/test_typecheck_gate_configured.py` | Changing the mypy gate must update the ledger entry and that test in the same ticket. |
| Import boundaries | AST tests in `tests/architecture/` (e.g. `test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`), D14 layer model, `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (done) | import-linter is **evaluated, not assumed** (M5): it must replace or clearly add to these tests, never run as a second copy. |
| Dead code | D11, `tools/audit_unreachable_code.py`, `docs/audits/unreachable_code_inventory.*`, `tools/gate_checks/tools_orphan_check.py` | **Reuse.** vulture is a trial only if it finds what these miss. |
| Duplicate classes | `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS` (open, four pairs, raised by `rpg-feature-planning`) | Owned elsewhere. Link it; the duplication check here must not re-file those pairs. |
| Conventions | `docs/guidelines/design_patterns.md` (extension points), `docs/engine/architecture_reference.md` §9 (naming) | The standard cites both and does not restate them. |
| Tools layout | `docs/guidelines/repo_tooling_layout.md`, `TCK-20260929-RETIRE-SCRIPTS-DIR` | **No `tools/` tidy ticket here.** New tools go in a `tools/code_health/` subpackage. |
| Environment | `uv.lock` tracked; `docs/guidelines/agent_working_environment.md` uses `uv venv` / `uv pip`; `tests/static/test_no_hardcoded_venv_interpreter_path.py`; `TCK-20260702-CI-REQUIREMENTS-SPLIT` | uv adoption finishes something half-done. It must keep the knowledge-search stack split and the venv-path guard. |
| Registry pattern | `registries/*.jsonl`, `tools/capability_envelope_baseline.py` (grandfathered baseline with a typed `reviewed` field) | Direct template for the debt registry. |
| Ownership | `docs/guidelines/subsystem_ownership_lifecycle.md` | New subsystems from this plan get rows there. |

## 5. Conflicts found, and how the plan resolves them

1. **Session-layer plan** (`docs/plans/agent_infrastructure/session_layer_working_process.md`, landed
   2026-10-02 in #283). Three seats per domain, one worktree per domain, an authority table.
   - "Codebase" becomes a **new domain** (decision 8.1): one overlay plus three seats.
   - **Only the implementer runs git.** The planner writes ticket and plan drafts and reviews.
   - **Governing files** (`CLAUDE.md`, `settings.json`, hooks) change only with the owner confirming
     the literal diff.
   - The worktree should be named for the domain. It exists as `rpg-code-craft` on branch
     `python-code-craft`; renaming to `codebase` is a follow-up for the implementer.
2. **Agent files belong to the `agent-working` domain.** `.claude/agents/*.md`, workflows, skills and
   hooks are owned there. This plan **requests** those changes and does not implement them.
3. **The formal pipeline barely runs.** `agent_working_direction.md` records about 94% hand closures
   since early September, and `implement-ticket.js` is mid-port. **No new pipeline phase.**
   Enforcement lives in CI and the edit loop; craft review is done by the planner seat on the
   implementer's diff.
4. **Formatting collides with every open branch** and with the `src/` freeze. No formatter now.
5. **Refactor targets are hot files.** The refactor lane is deferred entirely (decision 8.2 applies
   when it opens). Moved symbols will also touch `registries/mechanisms.yaml` `implemented_by`
   citations, parity ledger `v2_evidence` paths and doc-cited paths.
6. **Epic rule is all-or-nothing.** The work is split so each milestone can close (Section 7).
7. **CI has its own static tests** (`tests/static/test_ci_*`, `tools/gate_checks/ci_workflow_test_coverage.py`,
   the requirements split). New CI jobs and dependencies must satisfy them.
8. **New hooks and permissions** must be added to `registries/capability_envelope_registry.jsonl`.

## 6. Design

### 6.1 Code standard

`docs/guidelines/python_code_standard.md`. Short, checkable rules only; nothing an agent already does
by default. Each rule states whether a tool enforces it or a reviewer judges it.

Thresholds for **new or changed code** (ruff and pylint defaults; conventions, per Section 3):

| Measure | Limit |
|---|---|
| Function length | warn over 50 lines, fail over 80 |
| Statements per function | 50 |
| Cyclomatic complexity / cognitive complexity | 10 / 15 |
| Arguments | 5 |
| Branches / nesting depth | 12 / 5 |
| Class length / module length | flag over 500 / over 1,000 lines |

Judgement rules (reviewer, not tool): one responsibility per function; no copy of existing logic
where a helper exists; typed models over free-form dicts (already a project rule); public API
docstrings; no bare `except`.

### 6.2 Toolchain (proposed)

Chosen for one property above all: it can run against `src/` without editing it. Versions and
feature claims come from the 2026-10-02 research pass; items marked *trial* are benchmarked on this
repo before adoption.

| Layer | Primary | Why | Trial / alternative |
|---|---|---|---|
| Environment | **uv**, single project, one `uv.lock` | Already half-adopted. One `.venv` per worktree, hardlinked from a shared cache, removes the "worktree has no venv" problem. Collapses three dependency declarations into one. | |
| Lint | **ruff check** (no `ruff format` yet) | Fast, replaces flake8, isort and pyupgrade. JSON and GitHub-annotation output. | |
| Types | **mypy + `mypy-baseline`** | Keeps the existing config and parity-ledger entry; the baseline makes it blocking without source edits. | **basedpyright** as a second checker with its native baseline; **Pyrefly** benchmarked against it. `ty` is excluded: its only suppression path edits source. |
| Project-specific rules | **ast-grep** | YAML rules with custom fix messages and rule tests. A cheaper home for some of the hand-written AST tests. | Semgrep CE |
| Cognitive complexity | **complexipy** | Native snapshot ratchet and `--diff`. radon, xenon and wily are dormant. | |
| Line-count limits | small script in `tools/code_health/` | No tool has a lines-per-function rule with a baseline. | |
| Duplication | **jscpd** | Token-based clone detection with JSON output. Needs Node, which the repo already has for the frontend. | pylint `R0801`; `arid` (new, unverified) |
| Dependency hygiene | **deptry** | Finds declared-but-unused dependencies (the baseline tool already reports three). Needs dependencies in `pyproject.toml`, so it follows uv. | |
| Dead code | existing `audit_unreachable_code.py` | Already built and tuned to this repo. | vulture, only if it finds more |
| Import architecture | existing `tests/architecture/` AST tests | Already enforced. | **import-linter**, evaluated in M5 as a possible replacement driven by the package registry |
| Docstring coverage | ruff `D` rules through the ratchet | One tool fewer than adding interrogate. | |
| Hook runner | **prek** | Drop-in for `.pre-commit-config.yaml`, faster. Git hooks only; Claude Code hooks stay separate. | pre-commit |
| PR feedback | **diff-quality** (from diff-cover) and **reviewdog** `-filter-mode=added` | Report only on changed lines. | **GitHub code scanning via SARIF upload**: the repo is public, so it needs no licence; ruff, ast-grep and complexipy all emit SARIF |
| Platform | none now | SonarQube Community Build has no PR analysis; the SaaS options are paid per seat. | **Qlty CLI** as a single baseline-aware wrapper; CodeScene for hotspot analysis |

Lint messages state the fix, since the reader is usually an agent.

### 6.3 Code-health registry and ratchet

The home-grown part, needed because ruff and ast-grep have no baseline.

- `registries/code_health_exceptions.jsonl`: one row per grandfathered violation (file, symbol where
  the tool gives one, tool, rule, measured value or count, ceiling, `added_date`, `reviewed`,
  retiring ticket). CLI and validator follow `tools/capability_envelope_baseline.py`.
- `tools/code_health/`: adapters that read each tool's JSON output and normalise it, and one ratchet
  command that fails only when a violation is new or worse than its row.
- Tools with a native baseline (mypy-baseline, basedpyright, complexipy) keep their own baseline
  file; the registry records that the file exists and its size, so the trend is still visible in
  one place.
- Rows are **deleted** when debt is paid, so this registry is not append-only. Trend history goes to
  the existing snapshot tool.
- A moved or renamed function must not resurface as "new". Matching is by file and symbol, not line.

### 6.4 Package registry

`registries/package_registry.jsonl`: one row per `src/` package (purpose, layer, status
`active | legacy | frozen`, strictness tier, exemplar modules, do-not-imitate files). It answers
which of the 36 packages are live, and gives agents a named good example per package. Seeding it
includes an audit of tiny and overlapping packages (`actions`, `logging`, `views`, `runtime`,
`replay`, empty `social`; the `world*` family; `content` / `content_semantics`). The audit produces
decisions only and moves no code. Overlap between these packages has not been verified.

### 6.5 Agent-facing changes (requests to `agent-working`)

- A `code-craft` skill holding the standard's judgement rules and examples, referenced by a short
  pointer in `implementer.md`. No generic craft text in `CLAUDE.md`.
- A PostToolUse hook that runs the ratchet on the edited `.py` file and reports new violations as
  advisory context. Owner confirms the literal `settings.json` diff.
- Review rubric for the planner seat: findings are Important, Nit or Pre-existing; only Important
  blocks; nits capped; nothing a linter covers; Pre-existing findings become registry rows.
- Later, with the refactor lane: a `safe-refactor` skill (characterization tests first, small steps,
  determinism check).

## 7. Milestones

Each is separately closable. None before M6 modifies `src/`.

| # | Milestone | Delivers | Owner domain |
|---|---|---|---|
| M1 | Standard | `python_code_standard.md`; ownership-table row; plans tracking entry | codebase |
| M2 | Environment | uv as the single dependency source: refreshed `uv.lock`, dev tools in a dependency group, CI on `uv sync`, Python version aligned, environment guide updated | codebase |
| M3 | Measure and baseline | Ruff, complexipy, jscpd and the line-count script configured; `tools/code_health/` adapters and ratchet; registry seeded from a full scan; first health snapshot taken | codebase |
| M4 | Gates | Ratchet as an advisory CI job with changed-line PR feedback, blocking after a clean soak; mypy blocking through `mypy-baseline` with ledger and static-test updates; prek hooks; type-checker trial (basedpyright vs Pyrefly) reported | codebase |
| M5 | Structure | Package registry seeded; structure audit decisions; ast-grep rule pack for project rules; import-linter evaluation | codebase |
| M6 | Agent integration | Skill, edit hook, implementer pointer, review rubric | request to agent-working |
| M7 | Refactor lane | **Deferred until the owner reopens `src/`.** Standing batch folder, one file per batch, fed by the registry; first targets `api/server.py` and `observability/event_extractor.py` | codebase, with rpg-planner for engine files |

Order: M1, M2, M3, M4. M5 and M6 can start after M3. M7 is a lane, not an epic, and never closes.

## 8. Owner decisions

Recorded 2026-10-02:

1. **"Codebase" is a new domain** under the session-layer model; the designer seat is held by the
   planner.
2. **Refactors of `src/`**, when the lane opens, are done by `codebase-implementer`, one file per
   batch, after `rpg-planner` confirms no open work on that file.
3. **Formatter:** lint only now; format per package later at quiet points.
4. **Scope of the standard:** `src/` first, `tools/` second, `tests/` left to the `testing` domain.
5. **Gate strictness:** advisory for a soak period, then blocking for new violations only.
6. **Toolchain preference:** modern tools, complexity accepted.
7. **`src/` is frozen for this plan** until the owner says otherwise.

8. **Toolchain approved** as proposed in Section 6.2 (2026-10-02).
9. **M2 (uv in CI) may proceed now**, one job migrated first, `requirements.txt` kept as a generated
   export until every job is moved.
10. **Advisory soak: two weeks** before the gate blocks.
11. **Existing tests that pin CI and the Makefile may be edited** by the foundation tickets
    (2026-10-02). The freeze is on `src/` only. Consequences: the first CI job uses the
    `astral-sh/setup-uv` action, and `TCK-20261002-UV-REMAINING-CI-JOBS` migrates the rest. Those
    tests belong to the `testing` domain, whose planner is told before the change lands.
12. **Python version:** keep the `>=3.11` floor and document 3.13 as the CI-tested version; raising
    the floor would break the 3.12 knowledge-search venv.

Tickets: `tickets/todos/python-code-craft/` (epic plus seven children, order in `SEQUENCE.md`).

## 9. Risks

- **uv migration breaks CI or another domain's setup.** Mitigation: its own milestone, one job
  migrated first, `requirements.txt` kept as a generated export until every job is moved.
- **Home-grown ratchet is the weakest link.** Mitigation: small, tested, one normalised format; Qlty
  CLI kept as a fallback trial.
- **Baseline noise.** Several hundred grandfathered rows. Mitigation: generated, `reviewed: false`.
- **Tool sprawl.** Eight tools is a lot to keep green. Mitigation: one `make code-health` entry
  point, pinned versions in `uv.lock`, and each tool earns its place in M3 or is dropped.
- **Check fatigue.** Mitigation: silent on pass, changed file only, ratcheted.
- **Threshold dispute.** The numbers are conventions held in one config and one doc section.
- **Refactor risk** returns when M7 opens: characterization tests first, determinism and replay
  suites as the gate, one function per ticket.

## 10. Related

- Audits: `docs/audits/D11_dead_code.md`, `D12_pattern_consistency.md`, `D13_type_safety.md`,
  `D14_coupling_depth.md`, `D24_codebase_health_observatory.md`
- Plans: `docs/plans/agent_infrastructure/session_layer_working_process.md`,
  `docs/plans/agent_infrastructure/agent_working_direction.md`,
  `docs/plans/scripts_tools_governance_epic.md`, `docs/plans/test_architecture/`
- Guidelines: `docs/guidelines/design_patterns.md`, `repo_tooling_layout.md`,
  `subsystem_ownership_lifecycle.md`, `agent_working_environment.md`; `docs/guides/delivery_process.md`
- Tickets: `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`,
  `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`, `TCK-20260623-TYPE-CHECKER`,
  `TCK-20260702-CI-REQUIREMENTS-SPLIT`, `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`,
  `TCK-20260929-RETIRE-SCRIPTS-DIR`
