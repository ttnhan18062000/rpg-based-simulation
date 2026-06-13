# Plan — TCK-20260612-LOCAL-CTX-OPS

PHASE_TS: 2026-06-12T00:00:00Z

## Steps

1. knowledge_search.py: add `_write_manifest()`, `_load_manifest()`, `_MANIFEST_PATH`, `_CACHE_PATH`; extend `cmd_build` to write manifest after full build; add `--incremental` flag and incremental build logic
2. tools/hooks/post-commit-reindex.sh: new git hook script
3. Makefile: add `search-server-docker`, `knowledge-index-update`, `install-hooks`; rename targets to match agent_working_environment.md naming
4. CLAUDE.md: add `make knowledge-index-update` to After Work section
5. implement-ticket SKILL.md: add Step 0 context search before Scope phase

## Scope guards

- Docker infrastructure (Dockerfile, docker-compose.yml) already done — no changes
- agent_working_environment.md already done — no changes
- create-tickets.js Step 0 already done — no changes
