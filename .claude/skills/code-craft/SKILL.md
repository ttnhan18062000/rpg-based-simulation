---
name: code-craft
description: Write, refactor or review Python under src/ or tools/ (or review a Python diff) against docs/guidelines/python_code_standard.md. Carries the reviewer-only rules with examples, the pre-commit workflow and the review rubric. Not for docs, YAML, config or test-only work.
source: project
date_added: "2026-10-04"
---

# Code Craft (This Repo)

The standard is `docs/guidelines/python_code_standard.md`. It is the source: a rule here is its ID, one line and an
example, never a second definition. Rules a tool already checks (ruff, complexipy, the ast-grep pack, line-count) are
not repeated; the ratchet reports them. This skill covers what only a reader can judge.

## Before you write

1. Find the package's row in `codebase/structure/package_registry.jsonl` (the first path part under `src/`).
2. When the row's `exemplar_modules` is non-empty, imitate one of those modules. Never imitate a `do_not_imitate` path.
   When it is empty, follow the standard, not a neighbouring file: most of `src/` carries recorded debt.
3. Search for an existing helper before writing logic (F2).

## Reviewer rules, with one pair each

**F1** One responsibility per function (kinds listed in `docs/engine/architecture_reference.md` 9.2); "and" in its description means split it.
Bad: `def load_and_score(path)`. Good: `load_events(path)` and `score_events(events)`.

**F2** Do not copy logic. Bad: the same 6-line normalisation pasted into two modules. Good: one `normalise_name()` both call.

**F4** A nested function is a short closure; logic that needs its own test is module-level.
Bad: a 40-line `def apply()` inside `run()`. Good: `apply_updates()` at module level, called from `run()`.

**F5** An extension point follows a pattern in `docs/guidelines/design_patterns.md`.
Bad: a new ad-hoc `HANDLERS = {}` dict beside the existing registry. Good: register through that registry.

**N1** A name says what the thing means in the design vocabulary (`architecture_reference.md` section 9).
Bad: `extras.py`, `helper2()`. Good: `lead_routing.py`, `route_lead()`.

**N4 (trailing digit)** The ast-grep rule catches `V2`, `_v2`, `_new`; a trailing digit is yours to catch.
Bad: `score_event2`. Good: replace `score_event`, or name the difference: `score_event_with_decay`.

**D2** The first docstring line is one sentence saying what it does, not a path or a title.
Bad: `"""src/world/gate.py"""`. Good: `"""Decide whether an entity may pass a region gate."""`.

**D3** Do not restate what the signature says.
Bad: `"""Args: tick (int): the tick."""` on `def advance(tick: int)`. Good: say units, side effects or invariants only.

**T2** No `Any` in a public signature unless it is a serialization boundary, and the docstring says why.
Bad: `def apply(update: Any) -> Any`. Good: `def apply(update: StateUpdate) -> AppliedUpdate`.

**T3** Durable data and anything crossing a module boundary is a typed model.
Bad: `return {"hp": hp, "xp": xp}` consumed in another module. Good: `return CombatResult(hp=hp, xp=xp)`.

**E2** A justified `except Exception` carries `# noqa: BLE001` and the reason on the same line.
Bad: `except Exception:`. Good: `except Exception:  # noqa: BLE001 - plugin code is untrusted; failure is reported, not raised`.

**E3 (forms the ast-grep rule does not catch)** The rule flags an `except` whose body is only `pass`. Hiding a failure the caller needed to know about in any other way is the same defect. Handling the exception is not: `except KeyError: return default` is a decision, not a swallow.
Bad: `try: data = json.loads(text)` then `except Exception: return None`, with no log, so a corrupt file looks like "no data".
Good: log with context and return a stated fallback, or re-raise: `except json.JSONDecodeError as err: raise ConfigError(f"bad file {path}") from err`.

## Before you commit

- Run `make code-health` (or `python3 -m codebase.gates.staged_ratchet <files>` for the files you changed). It fails only on a new or worse violation.
- In a Claude Code session an edit hook (`codebase/hooks/edit_ratchet_hook.py`) may add a message after you edit a `src/**/*.py` file. It means that file has a new or worse ruff finding: fix it. It is advisory, never blocks, and is silent when the file is fine.
- Do not edit `codebase/baselines/code_health_exceptions.jsonl` by hand.

## Reviewing a change

Use Section 11 "Review rubric" of the standard. Every finding is **Important** (blocks), **Nit** (at most 3) or **Pre-existing** (never blocks). Do not raise by hand what a configured tool reports. An Important finding names a rule ID, an architecture rule, or the concrete failure of a correctness bug.
