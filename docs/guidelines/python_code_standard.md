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
- **a named tool, planned**: the tool is not configured in this repo yet. The rule holds today
  only through review. Tool configuration arrives with `TCK-20261002-CODE-HEALTH-TOOL-CONFIG`
  (roadmap M3) and CI gating with roadmap M4. Ruff rule codes are the intended ones and are
  confirmed or replaced by that ticket.
- **mypy, advisory today**: mypy is configured (`[tool.mypy]` in `pyproject.toml`) but runs
  non-blocking in `make typecheck-py` and CI, and five packages are excluded. Blocking is planned
  for roadmap M4.

Where a rule allows a justified exception and also names a tool (E2, M1), the tool cannot read a
plain comment. In new or changed code the exception is written as `# noqa: <code>` followed by the
reason on the same line. This applies only to code you are writing; existing violations in `src/`
stay in the external baseline and get no inline suppression.

As of 2026-10-02 no rule in this doc is blocked by a tool.

## 3. Function and class design

| ID | Rule | Enforcement |
|---|---|---|
| F1 | A function has one responsibility: one of the kinds of work listed in `docs/engine/architecture_reference.md` section 9.2. If its description needs "and", split it. | reviewer |
| F2 | Do not copy existing logic. Search for a helper first; if the same logic is needed twice, extract it. | reviewer; jscpd, planned |
| F3 | Do not use mutable default arguments. | ruff `B006`, planned |
| F4 | A nested function is a short closure. Logic that needs its own tests is a module-level function or a method. | reviewer |
| F5 | New extension points follow an existing pattern in `docs/guidelines/design_patterns.md`; do not invent a parallel mechanism. | reviewer |

## 4. Size and complexity thresholds

These apply to new or changed code. They are ruff and pylint defaults and common convention, not
limits backed by controlled evidence.

| ID | Measure | Limit | Enforcement |
|---|---|---|---|
| S1 | Function length | warn over 50 lines, fail over 80 | line-count script in `tools/code_health/`, planned |
| S2 | Statements per function | 50 | ruff `PLR0915`, planned |
| S3 | Cyclomatic complexity | 10 | ruff `C901`, planned |
| S4 | Cognitive complexity | 15 | complexipy, planned |
| S5 | Arguments per function | 5 | ruff `PLR0913`, planned |
| S6 | Branches per function | 12 | ruff `PLR0912`, planned |
| S7 | Nesting depth | 5 | ruff `PLR1702` (preview rule), planned |
| S8 | Class length | flag over 500 lines | line-count script in `tools/code_health/`, planned |
| S9 | Module length | flag over 1,000 lines | line-count script in `tools/code_health/`, planned |

A function already over a limit must not get longer or more complex when you change it.

## 5. Naming

Domain naming (name by meaning, reuse the existing design vocabulary) is defined in
`docs/engine/architecture_reference.md` section 9 and is not repeated here. The rows below add the
Python identifier conventions that section does not state.

| ID | Rule | Enforcement |
|---|---|---|
| N1 | Follow `docs/engine/architecture_reference.md` section 9 for what a name means. | reviewer |
| N2 | Functions, methods, variables and modules are `snake_case`; classes are `PascalCase`; module-level constants are `UPPER_SNAKE_CASE`. | ruff `N` rules, planned |
| N3 | A leading underscore marks a name as private to its module or class. Do not import a `_private` name from another module. | reviewer |
| N4 | No version or sequence markers in new names (`V2` prefix or suffix, `_v2`, `2`, `_new`). Replace the old thing or name the difference. Existing `V2` names are not to be renamed. | reviewer |

## 6. Docstrings

| ID | Rule | Enforcement |
|---|---|---|
| D1 | Every public module, class and function has a docstring. | ruff `D1` rules, planned |
| D2 | The first line is one sentence saying what it does. Add more only for what the signature cannot say: side effects, determinism constraints, units, invariants. | reviewer |
| D3 | Do not restate argument names and types that the signature already gives. | reviewer |
| D4 | Comment style follows `docs/engine/architecture_reference.md` section 9. | reviewer |

## 7. Typing

| ID | Rule | Enforcement |
|---|---|---|
| T1 | Every function has annotations on all arguments and on the return value. | ruff `ANN` rules, planned; mypy, advisory today |
| T2 | Do not use `Any` in a public signature unless the value is a serialization boundary. Say why in the docstring. | reviewer |
| T3 | Durable data, and anything passed or returned across a module boundary, is a typed model (dataclass or Pydantic), not `dict[str, Any]` (see the Durable State Rule in `CLAUDE.md`). | reviewer |
| T4 | New code passes mypy under the repo config without a new `# type: ignore`. | mypy, advisory today |

## 8. Error handling

| ID | Rule | Enforcement |
|---|---|---|
| E1 | No bare `except:`. | ruff `E722`, planned |
| E2 | Catch the narrowest exception that the code can handle. A justified `except Exception` carries `# noqa: BLE001` and the reason. | ruff `BLE001`, planned; reviewer |
| E3 | Do not swallow an exception silently. Handle it, log it with context, or re-raise. | reviewer |
| E4 | When re-raising as a different type, chain it with `raise ... from err`. | ruff `B904`, planned |

## 9. Module layout

| ID | Rule | Enforcement |
|---|---|---|
| M1 | Imports are at the top of the module, grouped standard library, third party, first party. A justified function-level import (for example to break a circular import) carries `# noqa: PLC0415` and the reason. | ruff `I001` and `PLC0415`, planned; reviewer |
| M2 | No wildcard imports. | ruff `F403`, planned |
| M3 | No I/O and no mutation of unrelated global state when a module is imported. Registering into an existing registry at import time, through that registry's established pattern, is allowed. | reviewer |
| M4 | New repo tooling goes under `tools/` per `docs/guidelines/repo_tooling_layout.md`. | reviewer |
| M5 | A new module belongs to the package whose responsibility it shares. Do not create a new top-level `src/` package without an owner decision. | reviewer |

## 10. Related

- `docs/plans/codebase_health/python_code_craft_roadmap.md`: plan, evidence and toolchain.
- `docs/guidelines/design_patterns.md`: extension points.
- `docs/engine/architecture_reference.md` section 9: naming and readability.
- `docs/audits/D12_pattern_consistency.md`, `docs/audits/D13_type_safety.md`: measured state.
- `docs/guidelines/subsystem_ownership_lifecycle.md`: owner and lifecycle of this doc.
