---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation (written at close from the work)
- Before this ticket the strict runner wrote only a gitignored `reports/visual_assets/aseprite_local_run.json`, and CI printed only a skip count, so nothing committed said when the real-Aseprite tests last ran or on what.
- Ten test files carry the marker, plus shared support (conftest files, `strict_aseprite.py`, builders, adoption and runtime fixtures). The guarded set is computed from `git ls-files` so CI and the local run see the same files: all of `store/**` and `drawing/**` minus docs, the build config, the marked tests with their support and the two runner tools (108 files at the first record, 110 at the refresh). The planner chose the broad set over an ast import-closure on purpose: a stale record after any code edit there is the intent.
- Honesty rules found necessary: a subset run (any extra pytest argument or a selecting `PYTEST_ADDOPTS`) must write no record; a dirty or untracked guarded file must write no record because the record names the commit it ran on; the marker name is built from parts so the proof module and its test are not "marked" merely by naming it.
- The record states what the licence holder ran and does not authenticate who ran it; CI never runs Aseprite.
