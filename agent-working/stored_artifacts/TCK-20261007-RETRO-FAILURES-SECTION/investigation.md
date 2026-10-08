---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-FAILURES-SECTION
artifact_type: investigation
tags: [agent-monitoring, retro]
---

# Investigation

- Data on current main: 13878 events; status `failed` 380, `blocked` 111; `reason_code` populated on about 160 of them (dod_condition_failed 119, needs_changes 18, conflicts_detected 6, ...), `None` on about 330 (older events and workflows that do not set it). Runs: `final_status` DONE 1903, plus a long tail of non-DONE values (NEEDS_HUMAN_INPUT 27, DOD_BLOCKED 25, NEEDS_CHANGES 22, BLOCKED 14, TESTS_FAILED 7, ...) and legacy spellings (`completed`, `success`, `done`).
- Reuse, do not re-define: `generate_retro._resolve_status` / `_is_gate_fail` (non-DONE/EPIC_SCOPED/IN_PROGRESS), `_normalize_agent`, `dedupe_to_latest_per_execution`. These live in generate_retro.py; a sibling module that imported them would create an import cycle (generate_retro imports its siblings lazily inside `try`). So the sibling takes the predicates as arguments and `generate_retro` passes its own.
- Sibling pattern to copy: `gate_ledger.render_section` / `path_report.render_section`, wired by `_gates_section` / `_paths_section` returning None on any exception, a keyword on `generate(...)`, appended before `## Notes`.
- No structured per-test failure field exists. Test names appear in event summaries as pytest node ids (`tests/.../test_x.py::test_name`) or bare `test_name` mentions; a regex will be lossy, so the section says "parsed from summaries" and prefers node ids.
- `RETRO-2026-W41.md` already has a hand-written Failures-like discussion in Notes; the section is generated above `## Notes` and does not touch it.
