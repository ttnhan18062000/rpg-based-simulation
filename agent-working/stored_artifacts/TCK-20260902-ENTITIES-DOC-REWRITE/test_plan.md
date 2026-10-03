---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-ENTITIES-DOC-REWRITE
artifact_type: test_plan
tags: [documentation]
---

# Test Plan — TCK-20260902-ENTITIES-DOC-REWRITE

## Regression Surface
This is a pure documentation change — no `src/` files are modified (ticket Out of Scope), so
there is no runtime/unit/integration/arena-combat regression surface in the usual sense. The real
regression surface is documentation-accuracy and frontmatter-validity tooling that reads
`docs/core/entities.md` or the docs tree it lives in. Checked in this investigation:

- `tests/docs/test_doc_integrity.py` — reads `docs/engine/manifest.json`'s `mandatory_documents`
  list and validates structural headers / terminology alignment for the docs listed there.
  **Confirmed not applicable**: `docs/core/entities.md` is not present in
  `docs/engine/manifest.json`'s `mandatory_documents` list (grep-confirmed, zero match). This test
  will not touch the rewritten file.
- `tests/docs/test_doc_path_existence.py` — validates that every `src/tests/tools/docs`-shaped
  path cited inside a scoped doc resolves on disk. **Confirmed not applicable**: its `SCOPE_DIRS`
  is `("docs/engine", "docs/architecture", "docs/performance")` only (per
  `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`'s narrowing) — `docs/core/` is out of its scope entirely.
  This means the rewritten `entities.md`'s own path citations (e.g. `src/core/state.py`,
  `src/core/strategic.py`) are not machine-checked by this test; accuracy of those citations rests
  on this investigation's own verification and the implementer/doc-updater's care, not an automated
  gate. Worth calling out explicitly rather than silently relying on a gate that doesn't apply here.
- `tools/validate_frontmatter.py` (invoked by `done-checker`'s `frontmatter_valid` condition via
  `tools/gate_checks/done_checker_static.py`) — validates the YAML frontmatter block of
  `docs/core/entities.md` itself (`content_type: doc`, inferred from the `docs/` path).
  Since `status: authoritative` is being kept, the existing rule "`last_verified` required when
  `status == authoritative`" applies — the rewrite must update `last_verified` to the ticket's
  close date (already required by ticket Scope) or this check fails.
- `docs/REGISTRY.yaml` (`path: docs/core/entities.md`, line 23) — regenerated unconditionally at
  Finalize per project CLAUDE.md; no manual test needed, but the rewrite should not remove/rename
  the file (path must stay stable) or the registry entry orphans.
- No test under `tests/static/`, `tests/tools/`, or elsewhere was found that reads
  `docs/core/entities.md`'s *content* (as opposed to its frontmatter/path) — repo-wide grep for
  `docs/core/entities.md` across `.py`/`.yaml`/`.yml` returned only the `docs/REGISTRY.yaml` path
  entry.

## New Tests Required
No new automated test is required by the acceptance criteria — they are all either (a) manually
verifiable content assertions (zero occurrences of `Aspect`/`IdentityAspect`/etc.; every claimed
component name verifiable in `src/core/state.py` or `src/core/strategic.py`; framing consistency
with `docs/core/state.md`) or (b) existing tooling invocations (`validate_frontmatter.py`,
`make knowledge-index-update`) rather than new pytest coverage. Per the project's Testing Rule
("test meaningful behavior, not superficial coverage"), inventing a new pytest test whose entire
job is "assert a string does not appear in one markdown file" would be low-value, easily-drifted
scaffolding rather than real regression protection — the `test_doc_path_existence.py` pattern this
repo already uses for `docs/engine`/`docs/architecture`/`docs/performance` shows the intended shape
of that kind of guard, and `docs/core` was deliberately left out of its `SCOPE_DIRS` by a prior
ticket; expanding that scope is a separate decision outside this ticket's Scope, not something to
improvise here.

If a future ticket decides to bring `docs/core` into `test_doc_path_existence.py`'s `SCOPE_DIRS`,
that would be the natural home for ongoing path-citation verification of `entities.md` going
forward — flagged here as a possible follow-up, not undertaken in this ticket (Out of Scope: this
ticket is a one-time content fix, not a new-gate ticket).

## Scoped Pytest Commands
```
pytest tests/docs/ -m "not slow"
```
Run the full `tests/docs/` suite (not just the two files inspected above) since a docs-content
change is exactly the class of edit that suite exists to guard, even though the specific two tests
checked above were confirmed not to touch this file. This keeps the regression check honest without
scoping so narrowly that an unexpected doc-tooling dependency is missed.

```
python3 tools/validate_frontmatter.py docs/core/entities.md
```
Directly exercises the same frontmatter check `done-checker`'s `frontmatter_valid` condition runs,
against the rewritten file specifically.

Do not run `pytest tests/` (whole suite) — this is a docs-only change with no `src/` modification,
so scoping to `tests/docs/` plus the direct frontmatter-tool invocation is the correct, narrow
regression surface per the project's Testing Rule.

## Anti-Drift Test Guards
- `tools/validate_frontmatter.py docs/core/entities.md` passing is itself an anti-drift guard: it
  would catch an accidental frontmatter field change (e.g. `status`, `layer`, `authority`,
  `audience` altered instead of only `last_verified`, which the ticket Scope explicitly forbids
  changing).
- `grep -c 'Aspect\|src/core/entities/entity\.py\|IdentityAspect\|SpatialAspect\|CombatAspect\|ProgressionAspect\|MindAspect' docs/core/entities.md` returning `0` is the direct, cheap check for
  acceptance criterion 1 (zero occurrences of the fictional terms) — run this manually or as part
  of Verify; it does not need a dedicated pytest test given the one-time nature of this fix.
- `git diff --stat` (or `git status`) showing only `docs/core/entities.md` (plus `docs/REGISTRY.yaml`
  and `agent-monitoring/` per the standard ticket-close staging) changed is the guard against
  accidentally touching `docs/core/state.md` or `docs/core/attributes_and_classes.md` (both
  explicitly Out of Scope) or any `src/` file (also explicitly Out of Scope, and would indicate the
  ticket has silently expanded beyond a docs-only fix).
- Running `pytest tests/docs/ -m "not slow"` both before and after the edit and diffing the results
  is the guard against `test_doc_integrity.py`'s manifest-driven checks or any other doc-suite test
  picking up an unexpected new dependency on `entities.md` that this investigation did not find.
