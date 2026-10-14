---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation (written at close from the work)
- Stale claims found by grepping `docs/assets` and the ADR: the "Not built" list still said atlases and animation export were missing; a note said intake did not check animation metadata; the `export-runtime` row did not name `--animation`. `m0_discovery_result.md` keeps its dated historical line on purpose.
- The hardening epic's staging folder was an empty directory left behind by the research move.
- The closure tool refuses identical event summaries across tickets (a guard against copy-pasted monitoring), so each ticket's summaries had to be written for that ticket; two earlier tickets of the same batch need their own `test_plan.md` and `investigation.md`, which `done_checker_static` flagged and which were written at close from the work, not left empty.
- Environmental, not ours: `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails because two project memory directories exist (`-data-...` and `-home-...`).
