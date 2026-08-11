---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
artifact_type: test_plan
tags: [cognition, strategy]
---

# Test Plan — TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

This is a pure-docs/chore ticket (no `src/` changes permitted per Out of Scope). There is no new
unit-test surface to author. "Tests" here means: (1) the 4 named regression files the ticket's own
AC5 requires to keep passing after the structural edits, (2) parity-ledger schema/index validation
for the 2 new STRAT entries, (3) frontmatter validation for this ticket's own staging artifacts.

## Regression Surface

**Unit / tools (parity ledger + schema integrity):**
- `tests/tools/test_parity_ledger_scan.py` — scans the canonical 8 ledger files (including
  `strategic_cognition.yaml`) for P0 intersections; must not choke on the 2 new entries.
- `tests/tools/test_parity_index.py` — imports all shards (including `strategic_cognition.yaml`)
  into the SQLite parity index; validates id uniqueness (`STRAT-252`/`STRAT-253` must not collide
  with any existing id — confirmed highest existing id is STRAT-251), reference-table joins,
  `entry_health` (missing-evidence detection).
- `tests/tools/test_parity_index_baseline.py` — baseline manifest generator determinism/coverage
  over the same 8 canonical files.
- `tests/tools/test_cognition_strategy_skill_content.py` — asserts specific formula/phrase
  substrings are present in `.claude/skills/cognition-strategy/SKILL.md`
  (`Interruption_Margin = Profile_Resistance * resistance_multiplier`, `not a hardcoded 30.0`,
  the 3 real scoring formulas, the 4 pipeline phases/flags). This ticket does not touch SKILL.md
  (see investigation.md's flagged-not-fixed SKILL.md drift note) and none of the pinned substrings
  are affected by the `04_strategic_cognition.md`/`adventure_contract.md`/`strategic_cognition.yaml`
  edits, so this file's tests are a pure regression guard here, not something this ticket's edits
  are expected to change.

**Frontmatter validation:**
- `tests/tools/test_validate_frontmatter.py` (if it globs `docs/` and `staging_artifacts/`,
  confirm at Implement time) — this ticket's own `investigation.md`/`test_plan.md`/`plan.md`
  frontmatter blocks must validate; `docs/mechanics/04_strategic_cognition.md` and
  `docs/simulation/domains/adventure_contract.md` keep their existing frontmatter (`status:
  authoritative`/`status: active`, `layer: mechanics`/`layer: simulation`) unless Implement's edit
  requires a `last_verified` bump — check the existing convention in these 2 files (both already
  carry `last_verified`) and update it to today's date if the file's own convention calls for it on
  content edits.

## New Tests Required

None — this ticket makes no `src/` or `tests/` behavior change, and its own Scope does not request
new test authorship. The "new" surface is the 2 new parity-ledger entries (STRAT-252, STRAT-253),
which are themselves data, validated by the existing schema/index tests above, not by new pytest
functions written for this ticket.

If Implement judges a genuinely new doc-content regression guard is warranted (e.g., pinning that
`04_strategic_cognition.md` no longer contains the literal string `"score > 80"` in the interruption
section, mirroring the pattern `test_cognition_strategy_skill_content.py` already uses for SKILL.md),
that would be:
- Test name: `test_strategic_cognition_bypass_section_reflects_generalized_rule` (illustrative name)
- Category: unit (doc-content pin)
- What it verifies: `docs/mechanics/04_strategic_cognition.md`'s §2 no longer asserts the
  `kind=="danger" and score>80` special case verbatim, and does reference
  `supports_adventure_routing`/the generalized dual-condition rule
- Where it should live: `tests/tools/test_strategic_cognition_doc_content.py` (new file, following
  the `test_cognition_strategy_skill_content.py` naming/shape precedent) — **not required by any AC;
  optional hardening only, do not treat as blocking.**

## Scoped Pytest Commands

```
pytest tests/tools/test_cognition_strategy_skill_content.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -v
```

Additionally, if frontmatter validation is exercised via a standalone script rather than pytest
(confirm `tools/validate_frontmatter.py`'s invocation convention at Implement time — CLAUDE.md
references it as "script-checked by done-checker's frontmatter_valid condition", which may run
outside pytest):
```
python3 tools/validate_frontmatter.py docs/mechanics/04_strategic_cognition.md docs/simulation/domains/adventure_contract.md docs/parity_ledger/strategic_cognition.yaml staging_artifacts/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS/
```

Never: `pytest tests/`.

## Acceptance-Criteria-to-Verification Map

| AC | Verification |
|---|---|
| AC1: §1-2 describes eligibility via `supports_adventure_routing` + real bypass rule | Manual diff review against investigation.md's "Current Behavior" code citations; no automated test pins this prose directly (see optional hardening test above) |
| AC2: stale L39 line replaced; §6.6 normalization resolution documented if applicable | Same — manual review; `grep -n "score > 80" docs/mechanics/04_strategic_cognition.md` should return no match in §2 after the edit |
| AC3: adventure_contract.md Role row replaced; "What It Reads" hero-only framing corrected | Manual review; `grep -n "EntityRole = 0" docs/simulation/domains/adventure_contract.md` should return no match after the edit |
| AC4: strategic_cognition.yaml gains STRAT-252+ entries, v2_evidence from actual landed code | `tests/tools/test_parity_index.py` (schema/id/reference-table validation), `tests/tools/test_parity_ledger_scan.py` (P0 intersection scan doesn't break); manual content review against investigation.md's proposed entries |
| AC5: the 4 named test files continue to pass | Scoped pytest command above |

## Anti-Drift Test Guards

- `tests/tools/test_parity_index.py`'s duplicate-id check is the guard against accidentally
  reusing an existing `STRAT-*` id for the 2 new entries (confirmed pre-edit: highest existing id
  in `strategic_cognition.yaml` is `STRAT-251`).
- `tests/tools/test_parity_ledger_scan.py::test_only_scans_canonical_eight_not_faction` and
  sibling tests are an implicit guard that this ticket's edits stay inside
  `strategic_cognition.yaml` and don't require touching any other ledger file.
- `tests/tools/test_cognition_strategy_skill_content.py` passing unmodified after this ticket's
  edits is itself an anti-drift guard proving this ticket did NOT touch `.claude/skills/
  cognition-strategy/SKILL.md` (correctly out of scope) — if that file's tests start failing, it
  is a sign of accidental scope creep into the skill mirror, not an expected consequence of this
  ticket's real Scope.
- Re-run `tests/unit/strategic/test_interruption_resistance.py` and `tests/unit/domains/adventure/`
  (C1/C2's own regression surface, not this ticket's to modify) as a sanity spot-check only if any
  doc edit is later discovered to have been paired with an accidental code touch — this ticket
  should show zero diff under `git diff --stat -- src/` at Finalize.
