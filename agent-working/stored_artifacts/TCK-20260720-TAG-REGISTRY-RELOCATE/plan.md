---
status: active
layer: ai
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260720-TAG-REGISTRY-RELOCATE
date: 2026-07-30
tags: [tagging, frontmatter]
---

# Plan — TCK-20260720-TAG-REGISTRY-RELOCATE

## Ordered Steps

1. **Create `registries/` and move the 3 files.**
   Files: `registries/` (new dir), `docs/guidelines/tag_registry.jsonl` →
   `registries/tag_registry.jsonl`, same for `layer_registry.jsonl`, `glossary_registry.jsonl`.
   Use `git mv` for rename-history preservation. Byte-identical content (plain `mv`, no transform).

2. **Update the 3 `_REGISTRY_REL_PATH` constants.**
   Files: `tools/tag_registry.py:116`, `tools/layer_registry.py:60`, `tools/glossary_registry.py:68`.
   Change `Path("docs/guidelines/X_registry.jsonl")` → `Path("registries/X_registry.jsonl")`.
   Also update the 6 docstring/description-string mentions of the old path in these same 3 files
   (lines 3, 159/155/211 per investigation.md) — cosmetic but part of "every active reference."

3. **Update the 2 hardcoded-path test fixtures.**
   Files: `tests/tools/test_agent_ops_dashboard_glossary.py:27,32`,
   `tests/tools/test_generate_retro.py` (fixture-writer helper + its line-168 docstring).
   Change `tmp_path/"docs"/"guidelines"/"X_registry.jsonl"` → `tmp_path/"registries"/"X_registry.jsonl"`.

4. **Update `docs/parity_ledger/infrastructure.yaml`'s 2 `v2_evidence` occurrences.**
   Lines 5038, 5539 (per investigation.md's exact classification) — old path → `registries/` path.
   Explicitly do NOT touch the 2 `text:`-block occurrences (lines 5018, 5525) — historical
   narrative, out of scope per this ticket's own AC wording.

5. **Update all remaining active prose/comment/docstring references.**
   Files (all confirmed via investigation.md's grep): `tools/validate_frontmatter.py`,
   `tools/tag_report.py`, `tests/tools/test_validate_frontmatter.py`,
   `tests/tools/test_tag_report.py`, `docs/guidelines/tag_taxonomy.md`, `docs/ai/system_overview.md`,
   `docs/ai/ticket-lifecycle.md`, `docs/ai/workflows.md`, `docs/guides/ticket_reporting.md`,
   `docs/guides/ticket_tagging.md`, `docs/guides/agent_ops_dashboard.md`,
   `docs/observability/agent_ops_dashboard_contract.md`, `docs/agent-monitoring/schema.md`,
   `.claude/workflows/create-tickets.js`, `.claude/agents/ticket-scoper.md`,
   `.claude/workflows/implement-ticket.js`, `.claude/workflows/simq-audit.js`, `CLAUDE.md`,
   `docs/plans/tag_dedup/proposal_tag_corpus_dedup.md` (active, not archived — see investigation.md's
   explicit decision).
   Do NOT touch `docs/plans/archive/agent_ops_dashboard/*.md` (6 files) — explicit decision,
   recorded in this ticket's Assumptions/Open Questions, to leave archived historical docs as-is.

6. **Run the regression suite** (see test_plan.md's Scoped Pytest Commands).

7. **Run `make docs-registry` before/after diff** to empirically confirm the no-op claim (AC #7),
   not just assert it from reading `generate_registry.py`.

8. **Final grep sweep** for the 3 old path strings across `tools/ src/ tests/ docs/ .claude/
   CLAUDE.md`, confirming zero matches outside the 2 intentionally-excluded classes (archive docs,
   `infrastructure.yaml` `text:` blocks).

## Files to Change

Exactly the list in Steps 1-5 above — no file outside that list is touched.

## Explicit Scope Guards

- No change to `src/api/agent_ops_dashboard/ingest.py` or `models.py` — investigation confirmed
  neither contains a literal old-path string; both already consume registries only via
  `load_registry()` function calls.
- No change to `docs/plans/archive/agent_ops_dashboard/*.md` (6 files) — historical archive.
- No change to `infrastructure.yaml`'s `text:` blocks (2 occurrences) — historical narrative.
- No redesign of `tag_registry.py`/`layer_registry.py`/`glossary_registry.py` beyond the one-constant
  change — that is out of scope for this pure-relocation ticket (covered by sibling tickets in this
  batch instead, e.g. `TCK-20260720-TAG-CATEGORY-REGISTRY`).

## Dependency Map

Step 1 must land before Steps 2-4 can be tested (the tools/tests would fail against a
half-migrated tree). Step 5 is independent of 2-4 (pure prose) and can happen in any order
relative to them, but is grouped last for review clarity. Steps 6-8 are verification, strictly
after 1-5.

## Acceptance Criteria Map

- AC1 (byte-identical move, old files gone) → Step 1
- AC2 (`_REGISTRY_REL_PATH` resolves from any cwd) → Step 2, verified in Step 6/7
- AC3 (zero old-path matches in active files) → Steps 2-5, verified in Step 8
- AC4 (5 named test files pass) → Step 3, verified in Step 6
- AC5 (`infrastructure.yaml` `v2_evidence` updated) → Step 4
- AC6 (explicit archive decision recorded) → investigation.md's Risks section + this plan's Scope Guards
- AC7 (`make docs-registry` no-op) → Step 7

## Unresolved Questions

None.
