---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN

Approved by test-architecture-reviewer at plan review of `38423a1151a0ee2c9f6d6de0a55ad67406d009d4`: design C
(non-exclusive signal), `schema_version` 2 to 3, addendum in `docs/testing/social_test_report_2026-10-03.md`.

## Steps (all in `tools/test_architecture/core_rpg_report.py` unless stated)

1. Constants: `_SOCIAL_PACKAGE = "src.systems.social_systems"` and `_SOCIAL_EXCLUDED_IMPORT_PREFIXES =
   ("src.systems.social_systems.party*", "src.systems.social_systems.memory")`. Not added to
   `DOMAIN_IMPORT_PREFIXES` or `_GAMEPLAY_IMPORT_PREFIXES`.
2. A helper `_social_signal(names)`: true when some name starts with `src.systems.social_systems.` and matches
   neither excluded prefix. The bare package name alone is not a signal (`from pkg import x` adds `pkg` and
   `pkg.x`).
3. `classify_file` adds three keys and changes nothing it already returns: `social_import_signal`,
   `social_party_overlap` (social signal and a party import) and `social_memory_only` (imports `memory`, no
   social signal); all three are `None` for a parse error. The `class` logic is not touched.
4. `classification_layer` adds a `social_domain` block: `denominator` (test files), `signal_files`, `by_class`
   (all five classes, zeros included), `party_overlap_files`, `memory_only_files`, and a one-line `rule` that
   says it is a non-exclusive signal, not a class.
5. `SCHEMA_VERSION` 2 to 3, with a short "Schema v3 added" note at the top of the module docstring.
6. `V0_LIMITS`: update the party sentence so it also says what social is (mapped, not core-RPG, reported
   separately, never changes a class or the candidate set). `unowned-domain` stays in the text.
7. `render_markdown`: one social line under Classification.
8. Tests in `tests/unit/tools/test_core_rpg_report.py` only (see test_plan.md).
9. Run the report once at the then-current `origin/main` (clean checkout state recorded) and write the dated
   addendum in `docs/testing/social_test_report_2026-10-03.md`; `make knowledge-index-update`.

## Scope guards

No other test file; no `src/`, `docs/parity_ledger/` or RPG test change; no new tool; `class` values and counts
byte-identical; `impact_report.py`, `marker_check.py` and the marker vocabulary untouched.
