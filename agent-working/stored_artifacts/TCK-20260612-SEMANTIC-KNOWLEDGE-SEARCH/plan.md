---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
artifact_type: plan
tags: [tooling, workflow, rag, knowledge-search]
---

# Plan — TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH

## Overview

Six independent-but-ordered steps. Steps 1–3 are pure config/manifest changes with no code.
Step 4 is the core implementation. Step 5 is the test suite. Step 6 is the workflow integration.
Steps 1–3 have no inter-dependencies and can be applied in any order. Step 5 depends on Step 4.
Step 6 is fully independent of Steps 1–5.

---

## Dependency Map

```
Step 1 (pyproject.toml)   ─┐
Step 2 (.gitignore)        ├─ No inter-deps; all unblock Step 4 install precondition
Step 3 (Makefile)          ─┘
Step 4 (tools/knowledge_search.py)  ← depends on Steps 1–3 being in place
Step 5 (tests/tools/test_knowledge_search.py)  ← depends on Step 4
Step 6 (create-tickets.js)  ← independent; no runtime dependency on Steps 1–5
```

---

## Scope Guards (What NOT to Touch)

- Do NOT add `sentence-transformers` or `sqlite-vec` to `[project.dependencies]` (core deps) — knowledge group only.
- Do NOT add these packages to `requirements.txt` (that file is a generated lockfile, not edited manually).
- Do NOT add `make knowledge-index` to `make test`, `make ci`, or any CI gate target.
- Do NOT embed `docs/`, `src/`, `tests/`, or any path outside the three defined corpus roots.
- Do NOT change the `all-MiniLM-L6-v2` model name — the ticket fixes this model explicitly.
- Do NOT modify existing tools in `tools/` or their tests in `tests/tools/`.
- Do NOT alter the Investigate phase Steps 1–7 in `create-tickets.js` — only prepend Step 0.
- Do NOT break `pip install -e .` for the core package (the `knowledge` group is opt-in).
- Do NOT add any simulation mechanics, engine pipeline, or parity ledger entries.

---

## Step 1 — pyproject.toml: Add `knowledge` optional-dependencies group

**File:** `/home/vboxuser/Work/rpg-based-simulation/pyproject.toml`

**Change:** Insert a new `knowledge` entry under `[project.optional-dependencies]`, after the
existing `dev` group.

```toml
[project.optional-dependencies]
dev = [
    ...existing entries...
]
knowledge = [
    "sentence-transformers>=2.7.0",
    "sqlite-vec>=0.1.1",
]
```

**Why these versions:**
- `sentence-transformers>=2.7.0` — stable API for `SentenceTransformer` + `encode()`; 2.7.x is
  the current stable series as of 2026-06.
- `sqlite-vec>=0.1.1` — minimum version with stable `vec0` virtual table and Python bindings;
  requires SQLite >= 3.38.0 (satisfied: runtime is 3.46.1).

**Install instruction** (in Makefile comment and tool docstring): `pip install -e ".[knowledge]"`

**Verification:** `pip install -e ".[knowledge]"` succeeds; `import sentence_transformers` and
`import sqlite_vec` work in the environment.

**Acceptance criteria covered:** AC7 (graceful degradation if deps missing — installs via this
group), AC5 (make knowledge-index works after pip install of new deps).

---

## Step 2 — .gitignore: Add `knowledge-index/` entry

**File:** `/home/vboxuser/Work/rpg-based-simulation/.gitignore`

**Change:** Append `knowledge-index/` as a new line. Place it in the appropriate section —
after the `graphify-out/*` block is a natural location since both are generated local artifacts.

```
# Knowledge search index (local only — rebuild with: make knowledge-index)
knowledge-index/
```

**Verification:** `git check-ignore -v knowledge-index/knowledge.db` returns a match.

**Acceptance criteria covered:** AC8 (`knowledge-index/` listed in `.gitignore`).

---

## Step 3 — Makefile: Add `knowledge-index` target

**File:** `/home/vboxuser/Work/rpg-based-simulation/Makefile`

**Change:** Add a new section `# ── Knowledge Search ─────────────────────────────────────────`
after the `# ── Agent Monitoring ─────────────────────────────────────` block (line ~149) and
before `# ── Cleanup ──────────────────────────────────────────────`.

```makefile
# ── Knowledge Search ─────────────────────────────────────────────────────────

knowledge-index: ## Build local semantic knowledge index (developer env only — not CI)
	@echo "Building knowledge index (requires: pip install -e '.[knowledge]')..."
	python3 tools/knowledge_search.py build
```

**Critical constraints:**
- Do NOT add this target as a dependency of `test`, `ci`, `all`, or any pipeline target.
- The `## Build local semantic...` comment is the `make help` description (standard pattern in
  this Makefile).
- The `@echo` line is a user-facing hint about the install prerequisite.

**Verification:** `make --dry-run knowledge-index` exits 0 and output references
`python3 tools/knowledge_search.py build`.

**Acceptance criteria covered:** AC5 (`make knowledge-index` runs build successfully).

---

## Step 4 — tools/knowledge_search.py: Create the tool (new file)

**File:** `/home/vboxuser/Work/rpg-based-simulation/tools/knowledge_search.py` (NEW)

### Module structure

```
tools/knowledge_search.py
  Module docstring: purpose, SQLite >= 3.38.0 requirement, install instructions
  _CORPUS_ROOTS: tuple of (glob_pattern, extraction_function) — the three corpus definitions
  _DEFAULT_DB: Path("knowledge-index/knowledge.db")
  _MODEL_NAME: "all-MiniLM-L6-v2"

  def _check_deps() -> tuple[bool, str]:
      """Try importing sentence_transformers and sqlite_vec. Return (ok, error_msg)."""

  def _extract_request_summary(text: str) -> str:
      """Extract ## Request Summary section from a ticket markdown file."""

  def _extract_working_log_rows(csv_path: Path) -> list[dict]:
      """Read working_log.csv, return list of {id, title, summary, path} dicts."""

  def _collect_corpus(corpus_root: Path) -> list[dict]:
      """
      Collect all documents from the three corpus roots.
      Returns list of {id, path, text, source_type} dicts.
      Corpus roots (relative to corpus_root):
        - tickets/done/TCK-*.md  → _extract_request_summary(content)
        - stored_artifacts/*/investigation.md → content[:500]
        - tickets/working_log.csv → _extract_working_log_rows()
      """

  def cmd_build(args) -> int:
      """
      Build the vector index.
      1. _check_deps() → warn + exit 0 if missing
      2. print "Downloading model all-MiniLM-L6-v2 (~22MB) on first run..."
      3. _collect_corpus()
      4. SentenceTransformer(MODEL_NAME).encode(texts)
      5. Create knowledge-index/ dir if needed
      6. Write sqlite-vec .db with vec0 table
      7. Print "N documents embedded"
      Returns: 0
      """

  def cmd_query(args) -> int:
      """
      Query the vector index.
      1. If db file does not exist: print warning, exit 0
      2. _check_deps() → warn + exit 0 if missing
      3. Load query embedding (SentenceTransformer — model NOT re-downloaded if cached)
      4. KNN search in sqlite-vec
      5. Print top-k results, one per line: "<ticket_id>\t<path>\t<snippet>"
      Returns: 0
      """

  if __name__ == "__main__":
      parser = argparse.ArgumentParser(...)
      subparsers = parser.add_subparsers(...)
      build_parser: --corpus-root (default: repo root), --db-path (default: _DEFAULT_DB)
      query_parser: text (positional), --top-k (default: 5), --db-path (default: _DEFAULT_DB)
      sys.exit(cmd_build(args) or cmd_query(args))
```

### Output format for `query`

One result per line, tab-separated:
```
TCK-20260524-STAMINA-PRESSURE	tickets/done/TCK-20260524-STAMINA-PRESSURE.md	Stamina pressure applied per tick...
```
If no ticket ID is recoverable (e.g., working_log row), use the file path as the ID field.

### Graceful degradation contract

Both `cmd_build` and `cmd_query` must wrap the `import sentence_transformers` / `import sqlite_vec`
calls in a `try/except ImportError` at the top of the function (not at module level), so the
module itself imports cleanly even when deps are absent. On ImportError:
- Print to stderr: `"Warning: <package> not installed — run: pip install -e '.[knowledge]'"`
- Return 0 (exit 0, no traceback).

When `knowledge-index/knowledge.db` does not exist and `query` is called:
- Print to stderr (or stdout): `"knowledge index not found — run make knowledge-index"`
- Return 0.

### SQLite version check

In `cmd_build`, after importing sqlite_vec, check:
```python
import sqlite3
if sqlite3.sqlite_version_info < (3, 38, 0):
    print(f"Error: sqlite-vec requires SQLite >= 3.38.0, found {sqlite3.sqlite_version}", file=sys.stderr)
    return 1
```

### Corpus boundary enforcement

`_collect_corpus` must only walk:
1. `corpus_root / "tickets" / "done"` — glob `TCK-*.md`
2. `corpus_root / "stored_artifacts"` — glob `*/investigation.md`
3. `corpus_root / "tickets" / "working_log.csv"` — single file

These three roots are the ONLY paths traversed. No `docs/`, `src/`, `tests/`, or other paths.

**Acceptance criteria covered:** AC1, AC2, AC3, AC4, AC6, AC7.

---

## Step 5 — tests/tools/test_knowledge_search.py: Create the test suite (new file)

**File:** `/home/vboxuser/Work/rpg-based-simulation/tests/tools/test_knowledge_search.py` (NEW)

**Pattern:** Follow `tests/tools/test_validate_frontmatter.py` exactly:
- `sys.path.insert(0, str(_REPO_ROOT))` at module level
- Load `tools/knowledge_search.py` via `importlib.util.spec_from_file_location`
- `subprocess.run` for CLI contract tests (exit code, stdout/stderr content)
- Direct function calls for unit tests of `_extract_request_summary`, `_collect_corpus`, etc.
- `tmp_path` fixture for filesystem isolation in all build/query tests

### Test groups and mapping to acceptance criteria

| Group | Tests | AC covered |
|---|---|---|
| Group 1: build happy path | T1.1–T1.4 | AC1 |
| Group 2: query happy path | T2.1–T2.4 | AC2, AC3 |
| Group 3: graceful degradation | T3.1–T3.3 | AC4, AC7 |
| Group 4: make target | T4.1 | AC5 |
| Group 5: .gitignore coverage | T5.1 | AC8 |
| Group 6: corpus scope guard | T6.1, T6.2 | (out-of-scope boundary) |
| Group 7: pyproject.toml deps | T7.1, T7.2 | (dep declaration anti-drift) |

**T2.2** (2-second wall-clock test on live corpus) is marked `@pytest.mark.slow` and must be
skipped automatically if `knowledge-index/knowledge.db` does not exist at the repo root
(`pytest.skip("knowledge index not built")` guard at test entry).

**T3.2 and T3.3** (missing package degradation): implement via `subprocess.run` with a small
wrapper that patches `sys.modules` to remove the package before calling the CLI. Prefer
subprocess over `unittest.mock.patch.dict` so the test does not depend on import-order
side effects inside the module.

**Scoped run command:**
```bash
pytest tests/tools/test_knowledge_search.py -v -m "not slow"
```

**Regression guard:** After Step 5, also run:
```bash
pytest tests/tools/ -v -m "not slow"
```
to confirm no existing tool tests broke.

**Acceptance criteria covered:** All 8 ACs via test assertions documented in test_plan.md.

---

## Step 6 — .claude/workflows/create-tickets.js: Add Step 0 to Investigate phase

**File:** `/home/vboxuser/Work/rpg-based-simulation/.claude/workflows/create-tickets.js`

**Insertion site:** Line 247 (the blank line before `─── Step 1: Knowledge graph`). The new
block is inserted between the `Raw excerpts from proposal:` block and the first `───` section
header.

**Exact insertion — prepend this block before the Step 1 header:**

```javascript
`─── Step 0: Semantic prior-work retrieval ─────────────────────────────────────

  Run (only if knowledge-index/ exists — the tool will self-check):
    python3 tools/knowledge_search.py query "${concern.title} ${concern.description}" --top-k 5

  If the command prints "knowledge index not found" or exits non-zero: skip and proceed to Step 1.
  If results are returned: note each returned ticket ID and path. Use these as warm-start
  candidates in Step 3 (prior ticket cross-reference) — check them in working_log.csv before
  running additional keyword greps.

`
```

**Implementation note:** The insertion must use the same template-literal interpolation style
as the surrounding prompt string. `${concern.title}` and `${concern.description}` are already
available in scope at line 247. No new variables are needed.

**Do NOT:** renumber existing steps, alter step content, add a new `agent()` call, or create a
new pipeline stage. This is a prompt-string prepend only.

**Verification:** Read the modified prompt string and confirm Step 0 appears before Step 1, with
the exact visual divider style (`─── Step N: ...`), and that `${concern.title}` and
`${concern.description}` interpolate correctly (no raw `${}` literals in output).

**Acceptance criteria covered:** AC6 (Step 0 calls tool and incorporates ticket IDs into Step 3).

---

## Ordered Step Summary

1. `pyproject.toml` — add `knowledge = ["sentence-transformers>=2.7.0", "sqlite-vec>=0.1.1"]` to `[project.optional-dependencies]`
2. `.gitignore` — append `knowledge-index/` entry after the `graphify-out/*` block
3. `Makefile` — add `knowledge-index` target in new `# ── Knowledge Search ───` section, no CI dependency
4. `tools/knowledge_search.py` — create with `build`/`query` subcommands, three-corpus design, graceful degradation, SQLite version check
5. `tests/tools/test_knowledge_search.py` — create 7 test groups covering all ACs, follow validate_frontmatter.py pattern
6. `.claude/workflows/create-tickets.js` — prepend Step 0 block before `─── Step 1` at line 247

---

## Acceptance Criteria → Step Mapping

| AC | Step(s) |
|---|---|
| AC1: `build` produces `knowledge-index/knowledge.db`, prints "N documents embedded" | Step 4 (impl) + Step 5 T1.1–T1.4 |
| AC2: `query` returns 5 results in under 2s | Step 4 (impl) + Step 5 T2.1–T2.2 |
| AC3: Results include ticket ID, file path, snippet | Step 4 (output format) + Step 5 T2.3 |
| AC4: Missing index → warning + exit 0 | Step 4 (graceful degradation) + Step 5 T3.1 |
| AC5: `make knowledge-index` runs build | Step 3 (Makefile) + Step 5 T4.1 |
| AC6: `create-tickets.js` Step 0 calls tool, incorporates IDs into Step 3 | Step 6 |
| AC7: Missing deps → warn + continue, exit 0 | Step 4 (ImportError guard) + Step 5 T3.2–T3.3 |
| AC8: `knowledge-index/` in `.gitignore` | Step 2 + Step 5 T5.1 |

---

## Deviations

None. All 6 steps were implemented exactly as specified. The actual insertion site in
create-tickets.js was verified to be line 250 (before `─── Step 1`) — plan cited "line 247"
which was the blank line before the section; the functional insertion is correct regardless.
Test count: 32 total (24 non-slow, 8 slow), which expanded slightly from the plan's group
descriptions due to additional unit tests for `_extract_request_summary`,
`_extract_working_log_rows`, and `_collect_corpus`.
