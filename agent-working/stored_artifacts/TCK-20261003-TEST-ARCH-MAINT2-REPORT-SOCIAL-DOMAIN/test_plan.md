---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN

Tests live only in `tests/unit/tools/test_core_rpg_report.py`.

1. Signal present: a social submodule import (for example `from src.systems.social_systems.appraisal import x`)
   sets `social_import_signal` true and leaves the class as before.
2. Excluded: `social_systems.party*` and `social_systems.memory` do not set the signal; memory-only sets
   `social_memory_only`; the bare package import alone does not set the signal.
3. Overlap: a file importing party and a social submodule sets `social_party_overlap` and stays `unowned-domain`.
4. Parse error: a syntactically invalid test file reports all three social keys as `None` and stays `parse-error`.
5. Layer: `social_domain` carries the denominator, `signal_files`, `by_class` (five classes, zeros included),
   `party_overlap_files` and `memory_only_files`.
6. **Invariance**: the `class` of every fixture file, and `classification.counts`, the candidate set and
   `signal_disagreement`, are identical with and without a social importer added (the social file lands in an
   existing class, not a new one).
7. Schema: the existing schema test checks version 3 and still asserts the v2 renames (`scanned_inputs_dirty`
   and the state names); a new assertion covers the `social_domain` keys.
8. Limits and markdown: the limits text names social as mapped-not-core-RPG and keeps `unowned-domain`; the
   markdown shows the social line.
9. Live check, outside pytest: the report run at the then-current `origin/main` gives class counts equal to the
   same run on the unmodified tool (both at the same SHA), differing only by the new keys.

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| class counts unchanged | unit + live comparison | regression | the unmodified tool's output at the same SHA (tooling behaviour; no Bible law) | identical `counts`, candidate set and `signal_disagreement` | `pytest tests/unit/tools/test_core_rpg_report.py` and a before/after report run |
| social field reported with denominator | unit | behaviour | ownership map `architecture_design_notes.md` §3.1 social and Party rows | keys and counts per fixtures 1 to 5 | `pytest tests/unit/tools/test_core_rpg_report.py` |
| other consumers unaffected | unit | regression | `impact_report.py` and `marker_check.py` import the module | their tests still pass | `pytest tests/unit/tools/test_impact_report.py tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_marker_check.py` |

## Scoped Pytest Commands

`pytest tests/unit/tools/test_core_rpg_report.py tests/unit/tools/test_impact_report.py
tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_marker_check.py`

## Anti-Drift Test Guards

Social never enters `_GAMEPLAY_IMPORT_PREFIXES`; the invariance test fails if it does.
