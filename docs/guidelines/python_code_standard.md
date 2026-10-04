---
status: active
layer: guidelines
authority: P1
audience: agent
date: 2026-10-02
tags: [documentation, architecture]
---

# Python Code Standard

Short, checkable rules for writing Python in this repo. It lists only what an agent does not
already do by default. Source plan: `docs/plans/codebase_health/python_code_craft_roadmap.md`
(Section 6.1); shipped by `TCK-20261002-PYTHON-CODE-STANDARD-DOC`.

## 1. Scope

- Applies to `src/` first and `tools/` second. Rules for `tests/` code belong to the testing
  domain and are not set here.
- Lint only. No formatter is adopted; do not reformat code you are not otherwise changing.
- The rules apply to **new or changed code**. Existing violations are held in an external baseline
  and are not a reason to edit a file.
- This doc does not cover extension points or architecture boundaries. For those, read
  `docs/guidelines/design_patterns.md` and the Architecture Rule in `CLAUDE.md`.

## 2. Enforcement markers

Every rule has an Enforcement cell with one of:

- **reviewer**: a person or review agent judges it on the diff. No tool checks it.
- **a named tool, configured**: the tool is configured in this repo (`pyproject.toml`) and can be
  run on demand (below). It is **blocking in CI** for ruff, complexipy and the length limits: the `Code health`
  job runs the ratchet on every PR, reports in its job summary (changed files first) and fails the PR on a new or
  worse violation. The violations that already exist in `src/` are held in
  `codebase/baselines/code_health_exceptions.jsonl`, and `make code-health` fails only on a new or worse one.
  jscpd and the ast-grep rules are report-only in that job (a cell says so where it applies). An opt-in pre-commit hook (`make install-prek-hooks`, see "Git hooks (opt-in)" in
  `docs/guidelines/agent_working_environment.md`) runs the same ratchet on the staged files. The first-run counts are in
  `TCK-20261002-CODE-HEALTH-TOOL-CONFIG`; later counts belong to the code-health snapshot.
- **mypy, blocking**: mypy is configured (`[tool.mypy]` in `pyproject.toml`), runs blocking in
  `make typecheck-py` and the `Type check` CI job, and five packages are excluded. Existing errors are held in
  `codebase/baselines/mypy_baseline.txt` (mypy-baseline 0.7.4, configured in `[tool.mypy_baseline]`; **1569
  entries** at `TCK-20261003-MYPY-BASELINE-ADVISORY`, one per error, line numbers normalised to 0, notes
  ignored), so `make typecheck-py` and the CI `mypy` step report only errors that are not in it. The CI
  job summary prints the new-error count and the current baseline size on every run. A fixed error does
  not fail the gate before the baseline is re-synced (`allow_unsynced`). **Re-syncing** the baseline
  (`make typecheck-baseline-sync`) is done only on `main`, by the codebase domain, together with the
  code-health registry reseed; never to hide a new error and never by a domain fixing one error.
  Blocking is planned for roadmap M4 (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`).

The ruff rule codes and the thresholds below were run against `src/` by
`TCK-20261002-CODE-HEALTH-TOOL-CONFIG` and are the ones in `[tool.ruff.lint]`; the thresholds live
in `pyproject.toml` (`[tool.ruff.lint.mccabe]`, `[tool.ruff.lint.pylint]`, `[tool.complexipy]`,
`[tool.code_health.size]`) and must match section 4.

| Command | What it reports |
|---|---|
| `make lint-py` | `ruff check src` (check only; no formatter, no `--fix`) |
| `make code-health-complexity` | functions over the cognitive-complexity limit (complexipy) |
| `make code-health-size` | functions, classes and modules over the length limits |
| `make code-health-dup` | duplicated Python blocks under `src/` (jscpd, pinned in the Makefile) |
| `make code-health` | all four tools, then the ratchet: fails only on a violation that is new or above its row in `codebase/baselines/code_health_exceptions.jsonl` |

**Edit hook (advisory).** In a Claude Code session, right after an `Edit`, `Write` or `MultiEdit` of a `src/**/*.py` file,
`codebase/hooks/edit_ratchet_hook.py` runs ruff on that one file and compares it with the registry like the pre-commit
check. It speaks only when the file has a new or worse finding, adding that report as context for the agent; it is silent
on a pass, never blocks, and always exits 0 (including when ruff or the registry is missing or it takes over about 5 seconds).
Ruff only: complexity, size and ast-grep are left to `make code-health` and CI.

The registry rows are matched by file, symbol, tool and rule, never by line, so moving code does
not make an old violation look new. Do not edit the file by hand: `python3 -m codebase.health
tighten` lowers ceilings and removes rows for debt you paid, `delete` removes one row, and a ruff or
complexipy version bump needs `seed --force` (which keeps each surviving row's `reviewed`, `retiring_ticket` and `added_date`). The match key for each tool is documented in
`codebase/health/findings.py`.

Where a rule allows a justified exception and also names a tool (E2, M1), the tool cannot read a
plain comment. In new or changed code the exception is written as `# noqa: <code>` followed by the
reason on the same line. This applies only to code you are writing; existing violations in `src/`
stay in the external baseline and get no inline suppression.

As of 2026-10-02 no rule in this doc is blocked by a tool.

## 3. Function and class design

| ID | Rule | Enforcement |
|---|---|---|
| F1 | A function has one responsibility: one of the kinds of work listed in `docs/engine/architecture_reference.md` section 9.2. If its description needs "and", split it. | reviewer |
| F2 | Do not copy existing logic. Search for a helper first; if the same logic is needed twice, extract it. | reviewer; jscpd, configured |
| F3 | Do not use mutable default arguments. | ruff `B006`, configured |
| F4 | A nested function is a short closure. Logic that needs its own tests is a module-level function or a method. | reviewer |
| F5 | New extension points follow an existing pattern in `docs/guidelines/design_patterns.md`; do not invent a parallel mechanism. | reviewer |

## 4. Size and complexity thresholds

These apply to new or changed code. They are ruff and pylint defaults and common convention, not
limits backed by controlled evidence.

| ID | Measure | Limit | Enforcement |
|---|---|---|---|
| S1 | Function length | warn over 50 lines, fail over 80 | `codebase/health/line_count.py`, configured |
| S2 | Statements per function | 50 | ruff `PLR0915`, configured |
| S3 | Cyclomatic complexity | 10 | ruff `C901`, configured |
| S4 | Cognitive complexity | 15 | complexipy, configured |
| S5 | Arguments per function | 5 | ruff `PLR0913`, configured |
| S6 | Branches per function | 12 | ruff `PLR0912`, configured |
| S7 | Nesting depth | 5 | ruff `PLR1702` (a preview rule, enabled by exact code), configured |
| S8 | Class length | flag over 500 lines | `codebase/health/line_count.py`, configured |
| S9 | Module length | flag over 1,000 lines | `codebase/health/line_count.py`, configured |

A function already over a limit must not get longer or more complex when you change it.

## 5. Naming

Domain naming (name by meaning, reuse the existing design vocabulary) is defined in
`docs/engine/architecture_reference.md` section 9 and is not repeated here. The rows below add the
Python identifier conventions that section does not state.

| ID | Rule | Enforcement |
|---|---|---|
| N1 | Follow `docs/engine/architecture_reference.md` section 9 for what a name means. | reviewer |
| N2 | Functions, methods, variables and modules are `snake_case`; classes are `PascalCase`; module-level constants are `UPPER_SNAKE_CASE`. | ruff `N` rules, configured |
| N3 | A leading underscore marks a name as private to its module or class. Do not import a `_private` name from another module. | ast-grep rule `n3-private-name-import` (advisory, own soak) |
| N4 | No version or sequence markers in new names (`V2` prefix or suffix, `_v2`, `2`, `_new`). Replace the old thing or name the difference. Existing `V2` names are not to be renamed. | ast-grep rule `n4-version-marker-name` (advisory, own soak): `V2` prefix or suffix, `_v2`, `_new` at the end of a def or class name; a trailing digit (`2`) is left to the reviewer |

## 6. Docstrings

| ID | Rule | Enforcement |
|---|---|---|
| D1 | Every public module, class, method and function has a docstring. | ruff `D100` to `D104`, configured |
| D2 | The first line is one sentence saying what it does. Add more only for what the signature cannot say: side effects, determinism constraints, units, invariants. | reviewer |
| D3 | Do not restate argument names and types that the signature already gives. | reviewer |
| D4 | Comment style follows `docs/engine/architecture_reference.md` section 9. | reviewer |

## 7. Typing

| ID | Rule | Enforcement |
|---|---|---|
| T1 | Every function has annotations on all arguments and on the return value. | ruff `ANN` rules except `ANN401`, configured; mypy, blocking |
| T2 | Do not use `Any` in a public signature unless the value is a serialization boundary. Say why in the docstring. | reviewer |
| T3 | Durable data, and anything passed or returned across a module boundary, is a typed model (dataclass or Pydantic), not `dict[str, Any]` (see the Durable State Rule in `CLAUDE.md`). | reviewer |
| T4 | New code passes mypy under the repo config without a new `# type: ignore`. | mypy, blocking |

## 8. Error handling

| ID | Rule | Enforcement |
|---|---|---|
| E1 | No bare `except:`. | ruff `E722`, configured |
| E2 | Catch the narrowest exception that the code can handle. A justified `except Exception` carries `# noqa: BLE001` and the reason. | ruff `BLE001`, configured; reviewer |
| E3 | Do not swallow an exception silently. Handle it, log it with context, or re-raise. | ast-grep rule `e3-silent-except` (advisory, own soak): an `except` whose body is only `pass` (comments allowed); other ways of swallowing stay with the reviewer |
| E4 | When re-raising as a different type, chain it with `raise ... from err`. | ruff `B904`, configured |

## 9. Module layout

| ID | Rule | Enforcement |
|---|---|---|
| M1 | Imports are at the top of the module, grouped standard library, third party, first party. A justified function-level import (for example to break a circular import) carries `# noqa: PLC0415` and the reason. | ruff `I001` and `PLC0415`, configured; reviewer |
| M2 | No wildcard imports. | ruff `F403` (part of `F`), configured |
| M3 | No I/O and no mutation of unrelated global state when a module is imported. Registering into an existing registry at import time, through that registry's established pattern, is allowed. | reviewer |
| M4 | New repo tooling goes under `tools/` per `docs/guidelines/repo_tooling_layout.md`. | reviewer |
| M5 | A new module belongs to the package whose responsibility it shares. Do not create a new top-level `src/` package without an owner decision. | reviewer; `python3 -m codebase.structure.packages validate` reports a tracked top-level package with no row (advisory) |

## 10. Correctness

| ID | Rule | Enforcement |
|---|---|---|
| X1 | New or changed code has no pyflakes error: no undefined name, unused import or variable, redefinition of an unused name, or f-string without a placeholder; and no syntax error. | ruff `F` and `E9`, configured |

## 11. Review rubric

For whoever reviews a Python change (the planner seat, `/code-review` style reviews). Examples live in the `code-craft` skill.

| Category | Meaning | Blocks? |
|---|---|---|
| **Important** | The change breaks a rule of this standard or an architecture rule, or is a correctness bug | Yes |
| **Nit** | A taste or polish point that no rule requires | No |
| **Pre-existing** | The problem was there before the change and the change did not make it worse | No |

- Only Important blocks. Every other finding is advice.
- Each Important finding names the rule ID (F1, T3, E3 ...) or the architecture rule it breaks, or, for a correctness bug, the concrete failure (input or state, then wrong result or crash); without one of these it is a Nit.
- At most 3 Nits per review; the rest are dropped.
- Do not raise by hand what a configured tool already reports (the Enforcement column says which); the ratchet reports it.
- A Pre-existing finding never blocks the change under review. If a tool reports it, it is already a row in `codebase/baselines/code_health_exceptions.jsonl`. If it is a reviewer rule and spans the whole file, propose it as a `do_not_imitate` entry in `codebase/structure/package_registry.jsonl`; otherwise mention it once and drop it.

## 12. Related

- `docs/plans/codebase_health/python_code_craft_roadmap.md`: plan, evidence and toolchain.
- `docs/guidelines/design_patterns.md`: extension points.
- `docs/engine/architecture_reference.md` section 9: naming and readability.
- `docs/audits/D12_pattern_consistency.md`, `docs/audits/D13_type_safety.md`: measured state.
- `docs/guidelines/subsystem_ownership_lifecycle.md`: owner and lifecycle of this doc.
