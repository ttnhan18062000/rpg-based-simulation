# Agent Workflow Rules (AI Assistant Behavior)

Rules for how the AI coding assistant should interact with this project. These are separate from the [system rules](main_rules.md) which govern the engine itself.

---

## 1. Always Analyze First

Before implementing:

* Read relevant files in:

  * `docs/`
  * `tickets/todos/`
  * Related source modules
* Summarize:

  * Current architecture
  * Dependencies affected
  * Risk areas
  * Possible design approaches

If any design decision affects:

* Core engine logic
* Data model structure
* Performance characteristics
* Public interfaces

➡ **You MUST ask for confirmation before implementing.**

No silent architectural changes.

---

## 2. Decision Escalation Rule

You must ask when:

* Multiple valid architecture patterns exist
* Tradeoffs impact performance vs realism
* Schema changes affect the shared pydantic dataclass models
* New feature introduces systemic behavior changes
* Tech stack change is major (framework replacement, new dependency, etc.)

Do NOT ask for:

* Naming trivial variables
* Minor refactors
* Formatting issues

Ask only when it actually matters.

---

## 3. Output Format Rule

When completing a task, always provide:

1. Summary of change
2. Architectural reasoning
3. Code changes
4. Tests added/updated
5. Docs added/updated
6. Future extension ideas (if relevant)

---

## 4. File and Path References

* Project docs live in `docs/`
* Tickets live in `tickets/todos/` (active) and `tickets/done/` (completed)
* Rules live in `tickets/rules/`
* Tests live in `tests/`
* Profiling scripts live in `scripts/`
* Ticket index is `tickets/todos/ticket_metadata.md`

---

## 5. Before Submitting Work

Checklist:

- [ ] `make test` passes (or `make test-quick` for fast iteration)
- [ ] Determinism not broken (`test_deterministic_replay.py` passes)
- [ ] Relevant docs updated
- [ ] Ticket metadata updated if applicable
- [ ] No dead code or commented-out logic left behind
