---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260925-RETRO-WATCHLIST-TABLE
artifact_type: test_plan
tags: [agent-monitoring, documentation, process-improvement]
---

# Test Plan — TCK-20260925-RETRO-WATCHLIST-TABLE

New file: `tests/tools/test_agent_monitoring_readme_watchlist.py`

1. `test_watchlist_heading_and_nonempty_table_exist` — reads `docs/agent-monitoring/README.md`,
   asserts `## Measurement Watchlist` is present and the markdown table immediately under it has at
   least one row beyond the header/separator.
2. `test_kgmcp_stub_removed` — asserts the literal heading text `Knowledge Gateway MCP Phase 0
   Measurement Baseline` no longer appears in the file.
3. `test_seeded_row_carries_ref_and_no_after_caveat` — asserts the seeded row's text contains the
   baseline value (`16.04`), its SHA (`0e0ff8f2`), and the words `not` and `this batch` (or
   equivalent) marking the "don't measure after from this batch" caveat, so a future edit can't
   silently drop the caveat while keeping the number.
4. `test_durable_sections_untouched` — asserts each of the 6 durable section headings
   (`Baseline Metrics Snapshot`, `Security Gate Firing Check`, `Skill Usage Metric`,
   `Done-Ticket Monitoring Coverage Audit`, `Agent Tool-Usage Baseline`, `Bash Command Mix
   Baseline`) is still present, unchanged in count (AC1's "no measurement commitment previously
   documented there is lost" — for durable sections, "not lost" means "still there").
5. `test_removal_rule_stated_in_preamble` — asserts the watchlist section's preamble text mentions
   deletion/removal once answered (AC3).
6. `test_retro_skill_names_readme_path_in_procedure` — reads
   `.claude/skills/agent-monitoring-retro/SKILL.md`, extracts the `## What This Skill Does` section,
   asserts it (not `## Related`) contains the literal string `docs/agent-monitoring/README.md`
   (AC4/AC5).

No test asserts a specific verdict was computed, no test enforces a schema beyond "heading exists,
table has rows" — matching the ticket's explicit "light... not a schema validator" instruction and
its explicit Out-of-Scope on any blocking gate/threshold.
