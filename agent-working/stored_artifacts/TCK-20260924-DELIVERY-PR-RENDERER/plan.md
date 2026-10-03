---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-PR-RENDERER
date: 2026-09-24
tags: [delivery, ai, documentation]
---

# Plan — TCK-20260924-DELIVERY-PR-RENDERER

## Module: `tools/delivery/pr_render.py`

Reuses `tools/delivery/pr_status.CommandResult`/`default_run_command` for injectable `git` calls
(same test seam as ticket 1), `validate_frontmatter.extract_frontmatter`, and
`generate_registry.parse_body_section`/`_strip_frontmatter` — no third parser.

### Functions
- `discover_commit_ticket_ids(run_command, base_ref) -> list[str]` — `git log <base>..HEAD
  --format=%s`, regex `TCK-[0-9]{8}-[A-Z0-9-]+`, de-duplicated, order preserved.
- `discover_changed_ticket_ids(run_command, base_ref) -> list[str]` — `git diff --name-only
  <base>..HEAD -- tickets/`, same regex applied to the paths.
- `find_ticket_file(ticket_id, tickets_root) -> Path | None` — `tickets_root.rglob(f"{ticket_id}.md")`.
- `load_ticket(path) -> dict` — `{ticket_id, layer, title, tier, request_summary, test_summary,
  completion_summary}` via `extract_frontmatter` + `parse_body_section`.
- `discover_tickets(run_command, tickets_root, base_ref) -> tuple[list[dict], list[str]]` — returns
  loaded tickets (commit-subject order) plus a list of mismatch-warning strings (AC7).
- `choose_scope(tickets) -> tuple[str, str|None]` — `(scope, tie_warning_or_None)`.
- `extract_known_gaps(ticket) -> list[str]` — lines containing `FAIL` from Test Summary +
  Completion Summary.
- `render_title(tickets, scope, theme=None) -> str` — always `"<scope>: <text> (<N>
  ticket(s))"` (investigation.md's resolved format).
- `render_body(tickets, spec, warnings) -> str` — walks `pr_template_spec.json`'s `sections` in
  order; for each `rendered: true` section, fills from ticket data; for `rendered: false`
  (`## Review notes`), emits a distinguishable placeholder; appends `Closes:` last.
- `render(pr=None, branch=None, theme=None, base_ref="origin/main", tickets_root=Path("tickets"),
  spec_path=Path("tools/delivery/pr_template_spec.json"), run_command=default_run_command) -> dict`
  — `{"title", "body", "warnings"}`.
- `check_against_live(pr, run_command) -> dict` — `--check` mode: `gh pr view --json title,body`,
  diff against a fresh `render()`, report `{"matches": bool, "title_diff", "body_diff"}`. Advisory,
  always exits 0.

### CLI
```
python3 tools/delivery/pr_render.py [--pr N] [--theme TEXT] [--base-ref REF] [--check] [--json]
```
No write side effect anywhere — stdout only (or `--json`), matching Out of Scope.

## Tests: `tests/tools/test_delivery_pr_render.py`
Fixtures build small throwaway ticket `.md` files under `tmp_path` (real frontmatter + body
sections) and a fake `run_command` for `git log`/`git diff`, mirroring `test_delivery_pr_status.py`'s
`FakeRunner` pattern.

1. AC1 — single ticket, title matches `"<scope>: <title> (1 ticket)"`, `<scope>` verified present in
   the real `registries/layer_registry.jsonl`; a ticket with an unregistered layer is reported, not
   defaulted.
2. AC2 — two tickets, title carries `(2 tickets)`, `## Tickets` table has exactly 2 rows.
3. AC3 — body contains all spec sections in order plus trailing `Closes:` naming every ticket.
4. AC4 — grep rendered output for `Co-Authored-By`, `claude.ai/code`, `Generated with`: zero matches.
5. AC5 — `## Review notes` placeholder is a distinguishable sentinel string, asserted present and
   distinguishable from real hand-written content.
6. AC6 — a ticket fixture whose `## Test Summary` states a `FAIL` renders that line into
   `## Verification`'s Known gaps — asserted present, not merely "no crash."
7. AC7 — commit-subject IDs and changed-ticket-file IDs deliberately diverge in a fixture; assert a
   mismatch warning names both sides.
8. AC8 — `--check` against a `gh pr view` fixture returning byte-identical title/body reports no
   difference; a fixture returning a different body reports the difference; both paths exit 0.
9. AC9 — a fixture spec with reordered/renamed sections is fed in and the rendered output follows
   it, proving no section list is hardcoded in the module.
10. AC10 — `"docs/guides/delivery_process.md" in Path("CLAUDE.md").read_text()`.
11. AC11 — record the real `pytest` command + result once run.

## Out-of-scope guardrails
- No `gh pr create`/`gh pr edit` call anywhere in this module.
- No rewriting of ticket content — thin input renders thin output, by design.
- `--check` never exits non-zero for a real difference; only an internal error does.
