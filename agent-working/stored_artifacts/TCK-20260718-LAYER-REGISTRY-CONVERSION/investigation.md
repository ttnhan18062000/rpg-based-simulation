---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-LAYER-REGISTRY-CONVERSION
date: 2026-07-18
tags: [frontmatter, tagging]
---

# Investigation — TCK-20260718-LAYER-REGISTRY-CONVERSION

## Current Behavior (file:line refs)

- `tools/tag_registry.py` (246 lines, read in full) is the template: an
  append-only JSONL registry (`docs/guidelines/tag_registry.jsonl`), one
  entry per line, `load_registry()` raises on a duplicate entry,
  `add_tag()` refuses to re-add an existing tag, a CLI with `add`/`list`
  subcommands. `category` is a required field on each entry, drawn from a
  4-value `ADDABLE_CATEGORIES` set.
- `tools/validate_frontmatter.py:44-48` (pre-conversion) defines
  `LAYER_VALUES` as a hardcoded `set` literal, 19 values.
- `grep -rln "LAYER_VALUES" --include="*.py" .` found exactly 5 files:
  `tools/validate_frontmatter.py` (definition + `_check_enum` calls),
  `tools/ticket_field_values.py` (`from validate_frontmatter import
  LAYER_VALUES` — a live import, confirmed, not a copy),
  `tests/tools/test_ticket_field_values.py` (identity test),
  `tests/tools/test_validate_frontmatter.py` (anti-drift value-equality
  test at line 678, `test_enum_values_layer`),
  `tests/tools/test_add_frontmatter_tickets.py` (an inference-output
  membership test). All 5 confirmed compatible with a registry-backed
  `LAYER_VALUES` as long as the importable name and its equality to the
  same 19-value set are both preserved.
- `docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md`'s
  original framing (superseded by this ticket, per the user's mid-epic
  design change) treated Layer as staying a hardcoded enum, contrasted
  against Tag's registry. That framing is now obsolete for this ticket.

## Mechanics/Engine Constraints

None — ticket-schema data hygiene tooling, not simulation gameplay.

## Parity Ledger Overlap (IDs + status)

None — no `src/` file is touched (`tools/`, `docs/guidelines/`, `tests/`,
`CLAUDE.md` only), matching the skip-eligibility pattern established by
every prior pure-tooling ticket this session.

## Prior Work

- `tools/tag_registry.py` / `docs/guidelines/tag_registry.jsonl` — direct
  template.
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (DONE) — the prerequisite that
  put `LAYER_VALUES` behind a live import in
  `tools/ticket_field_values.py`, which is exactly what makes this
  conversion transparent to that module (no edit needed there).

## Risks and Open Questions

- **Real risk, not hypothetical**: converting `LAYER_VALUES` from a literal
  to a computed value could silently change its contents if the seed data
  is incomplete or wrong, breaking `check_frontmatter_valid` for the entire
  existing corpus on every future ticket close. Mitigated by seeding via
  the real `add_layer()` API (not hand-written JSONL) and verifying the
  seeded set is byte-identical to the original via a dedicated test run
  against the live repo registry (no fixture), plus a genuine before/after
  full-corpus `validate_file` comparison (via `git stash`) rather than a
  single post-hoc scan.

## Anti-Drift Hazards

- `LAYER_VALUES` must remain importable as a frozenset/set (not, say, a
  list) so `== expected_set` equality checks in existing tests continue to
  work regardless of insertion order.
- Do not give `Layer` registry entries a `category` field — a deliberate
  structural difference from `Tag`, not an oversight; adding one would
  invite exactly the kind of category-taxonomy question that doesn't apply
  to Layer (see this ticket's Request Summary).
