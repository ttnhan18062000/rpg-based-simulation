---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
artifact_type: test_plan
tags: [tooling, workflow, rag, knowledge-search]
---

# Test Plan — TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH

## Regression Surface

No existing behavior is being changed. `tools/knowledge_search.py` does not exist today, and
no existing code imports it. The Makefile has no `knowledge-index` target today. The
`.gitignore` does not list `knowledge-index/`. The `create-tickets.js` Investigate phase has
no Step 0.

There are no existing tests to protect against regression. The entire test surface is new.

However, the following existing behaviors must NOT break:

- `make test` (existing pytest suite) must still pass after this ticket's changes.
- `make test-quick` must still pass.
- Adding deps to `pyproject.toml` must not break `pip install -e .` for the core package.
- Existing tools in `tools/` are unaffected — their tests in `tests/tools/` must still pass.

---

## New Tests Required

All new tests live in `tests/tools/test_knowledge_search.py`. Follow the pattern established
by `tests/tools/test_validate_frontmatter.py`:
- Import via `sys.path` insertion at repo root (tools/ is not a package)
- Use `subprocess.run` for CLI contract tests
- Use direct function calls for unit tests
- Use `tmp_path` (pytest fixture) for filesystem isolation

### Group 1: build subcommand — happy path

**T1.1 — build produces knowledge.db**
```
Given: a tmp_path corpus with at least one ticket file, one investigation.md, one working_log.csv row
When: python3 tools/knowledge_search.py build --corpus-root <tmp_path> --db-path <tmp_path>/knowledge.db
Then: knowledge.db exists and has non-zero size
```

**T1.2 — build prints document count**
```
Given: same minimal corpus
When: build runs
Then: stdout contains "N documents embedded" where N >= 1
```

**T1.3 — build exits 0 on success**
```
Subprocess exit code == 0
```

**T1.4 — build on empty corpus exits 0 and prints "0 documents embedded"**
```
Given: corpus paths that exist but contain no matching files
Then: exit 0, stdout contains "0 documents embedded"
```

### Group 2: query subcommand — happy path

**T2.1 — query returns top-k results**
```
Given: a pre-built knowledge.db with >= 5 documents
When: query "player fatigue during extended combat" --top-k 5
Then: stdout has exactly 5 lines (or <= 5 if corpus < 5 docs)
      Each line contains: a ticket ID pattern (TCK-\d{8}-\w+) OR a file path, AND a snippet
```

**T2.2 — query returns results in under 2 seconds**
```
Given: knowledge.db built from the live corpus (tickets/done/ + stored_artifacts/ + working_log.csv)
When: query "player fatigue during extended combat" --top-k 5
Then: wall-clock time < 2.0 seconds
```
Note: this test is marked `@pytest.mark.slow` and excluded from `make test-quick`. It requires
the live corpus index to be present; skip if knowledge-index/knowledge.db does not exist.

**T2.3 — each result line includes ticket ID, file path, and snippet**
```
Given: known document in the index with a known TCK-ID
When: query that matches it
Then: output line for that result contains all three: ID, path, snippet (non-empty)
```

**T2.4 — query exits 0**
```
Subprocess exit code == 0 even when results are returned
```

### Group 3: graceful degradation

**T3.1 — query when knowledge-index/ does not exist**
```
Given: no knowledge-index/ directory at the db path
When: python3 tools/knowledge_search.py query "anything" --top-k 5
Then: exit code == 0
      stderr (or stdout) contains "knowledge index not found"
      stdout has zero result lines
```

**T3.2 — build when sentence-transformers is not importable**
```
Given: sentence_transformers patched out (mock ImportError in sys.modules)
When: build runs
Then: exit 0, stderr contains warning ("sentence-transformers not installed" or similar)
      No traceback printed
```

**T3.3 — query when sqlite-vec is not importable**
```
Given: sqlite_vec patched out
When: query runs
Then: exit 0, stderr contains warning
      No traceback printed
```

Implementation note for T3.2 and T3.3: use subprocess with a wrapper script that removes the
package from sys.path, OR mock using `unittest.mock.patch.dict(sys.modules, {...})` inside the
test if the tool supports in-process graceful degradation checks. Prefer subprocess for
isolation fidelity.

### Group 4: make target

**T4.1 — make knowledge-index target exists**
```
Run: make --dry-run knowledge-index
Then: exit 0 (target is defined, dry-run succeeds)
      Output references python3 tools/knowledge_search.py build
```
This is a subprocess test against the real Makefile.

### Group 5: .gitignore coverage

**T5.1 — knowledge-index/ is listed in .gitignore**
```
Read .gitignore
Assert: "knowledge-index/" appears as a line (exact match or glob match)
```
This is an anti-drift guard: if someone removes the gitignore entry, this test fails.

### Group 6: corpus scope guard (anti-drift)

**T6.1 — build does NOT traverse docs/**
```
Given: a corpus with docs/ present (populated with files)
When: build runs with the default corpus roots
Then: the count of embedded documents equals only those from:
      tickets/working_log.csv + stored_artifacts/*/investigation.md + tickets/done/TCK-*.md
      AND does NOT include any path under docs/
```
Implementation: monkeypatch or inspect `build`'s corpus_paths list before embedding.

**T6.2 — build does NOT traverse src/**
Same as T6.1 but for `src/`.

### Group 7: pyproject.toml dependency declaration

**T7.1 — sentence-transformers declared in pyproject.toml knowledge group**
```
Parse pyproject.toml
Assert: [project.optional-dependencies].knowledge contains "sentence-transformers"
```

**T7.2 — sqlite-vec declared in pyproject.toml knowledge group**
```
Parse pyproject.toml
Assert: [project.optional-dependencies].knowledge contains "sqlite-vec"
```

---

## Scoped Pytest Commands

Run all new tests (when sentence-transformers and sqlite-vec are installed):
```bash
pytest tests/tools/test_knowledge_search.py -v
```

Run excluding slow live-corpus test:
```bash
pytest tests/tools/test_knowledge_search.py -v -m "not slow"
```

Run only the gitignore and pyproject guards (no package install needed):
```bash
pytest tests/tools/test_knowledge_search.py -v -k "gitignore or pyproject or corpus_scope or make_target"
```

Run all tools tests to verify no regressions:
```bash
pytest tests/tools/ -v -m "not slow"
```

Do NOT run `pytest tests/` — the full suite is out of scope for this ticket.

---

## Anti-Drift Test Guards

These tests exist specifically to prevent future regressions from routine maintenance:

| Guard | Test | What it prevents |
|---|---|---|
| `.gitignore` entry | T5.1 | knowledge-index/ accidentally committed |
| Corpus scope | T6.1, T6.2 | docs/ or src/ silently added to corpus |
| Graceful degradation (no packages) | T3.1, T3.2, T3.3 | ImportError crash replacing warn-and-continue |
| Dep declaration | T7.1, T7.2 | Deps removed from pyproject.toml without notice |
| make target | T4.1 | Makefile target renamed or removed |

These guards must remain in the test file even after implementation. They are not coverage
padding — each one has a specific regression scenario it prevents.
