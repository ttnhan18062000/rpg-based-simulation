# Test Plan — TCK-20260612-LOCAL-CTX-OPS

PHASE_TS: 2026-06-12T00:00:00Z

## Tests needed

| ID | What | How |
|---|---|---|
| T-MANIFEST-01 | manifest written by full build | mock corpus, call cmd_build, check manifest exists |
| T-MANIFEST-02 | manifest written by incremental build | same |
| T-MANIFEST-03 | incremental fast path when nothing changed | call twice, second call prints "up to date" |
| T-INCREMENTAL-01 | incremental re-embeds only changed files | monkeypatch model.encode to track calls |
| T-INCREMENTAL-02 | deleted file removed from corpus | corpus shrinks, index re-built without it |
| T-HOOK-01 | hook script is executable shell | file exists, starts with #!/usr/bin/env bash |

## Location

`tests/tools/test_knowledge_search.py` (extend existing test file — follow established pattern)
