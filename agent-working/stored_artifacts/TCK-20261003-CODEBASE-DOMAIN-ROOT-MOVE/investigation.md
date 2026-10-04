---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
artifact_type: investigation
tags: [architecture, delivery]
---

# Investigation — TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE

Order followed: `search_docs` (surfaced the repo_tooling_layout rule, the history schema doc and earlier tool-config investigation), `graphify query` (the five flat files and their tests form two communities, 33 and 77/163, no `src/` consumers), then follow-up git grep on head `3c8eb71f0`.

- Tracked live reference files outside closed history: 33 non-moved files (list in plan.md section 2) plus 14 moved test files. Ticket estimate of ~60 holds.
- No `src/` or `.claude/` (tracked) reference to any moved path; `.claude/handover/*` mentions only.
- `tools/` has no `__init__.py` (namespace package); `visual_assets/` has one. No `codebase` module resolvable (`find_spec` is None), no dir, no dependency by that name.
- Flat files use sibling imports with sys.path inserts (`code_health_impact`, `codebase_health_baseline`); `tools/code_health/*` use absolute `tools.code_health.*` imports. Only `codebase_health_snapshot` imports `tools.code_health.metrics`.
- jscpd: `scan.py:97` passes `--config .jscpd.json`; Makefile line 281 does too; adapters test copies the file. Whether jscpd accepts a non-root config path is verified in Step 3.
- CI: `tests/tools` is covered by two glob-split jobs; `tests/static` etc. by `arch-docs` (test.yml ~632). Coverage test parses job pytest paths from the live workflow.
- Hooks: prek shim reads `.pre-commit-config.yaml` at run time; installer constants reference only `post-commit-reindex.sh`, which does not move.
- Soak placeholder lines: epic:35, flip-ticket:70, roadmap:230.
