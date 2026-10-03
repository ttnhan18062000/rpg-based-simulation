---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
artifact_type: investigation
tags: [tooling, workflow, rag, knowledge-search]
---

# Investigation — TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH

## Current Behavior

### tools/knowledge_search.py
Does NOT exist. Confirmed: `ls tools/knowledge_search.py` → NOT FOUND.

### knowledge-index/
Does NOT exist at the repo root. Confirmed: directory absent.

### .gitignore
`knowledge-index/` is NOT listed. The entry must be added as part of this ticket.
Verified by: `grep -n "knowledge" .gitignore` → NOT PRESENT.

### Makefile
No `knowledge-index` target exists. No references to `sqlite-vec`, `sentence-transformers`,
`vector`, `embed`, or `semantic` in any Makefile target. A new `knowledge-index` target must
be added.

### requirements.txt
The file exists and contains 22 pinned packages (output is UTF-16 encoded). Neither
`sentence-transformers` nor `sqlite-vec` is present. They must be added.

### pyproject.toml
Does not declare `sentence-transformers` or `sqlite-vec` in `[project.dependencies]` or
`[project.optional-dependencies]`. The new deps should be added to a new
`[project.optional-dependencies]` group, e.g. `knowledge = [...]`, to keep them opt-in and
not break existing CI that does not run `knowledge-index`.

### .claude/workflows/create-tickets.js
The Investigate phase (Phase 2, lines 140–354) currently runs Steps 1–7 sequentially per
concern, starting with the graphify knowledge graph (Step 1). No Step 0 exists.
The step numbering in the prompt string is implicit: the first bullet is "Step 1: Knowledge
graph — code structure". A Step 0 must be prepended before this existing Step 1 block.

### sqlite-vec SQLite version requirement
sqlite-vec requires SQLite >= 3.38.0. The project's Python runtime ships SQLite 3.46.1.
The minimum is satisfied; no SQLite upgrade is required.

### sentence-transformers / sqlite-vec install status
Neither package is installed in the current environment:
- `import sqlite_vec` → ModuleNotFoundError
- `import sentence_transformers` → ModuleNotFoundError
Both are absent from pyproject.toml and requirements.txt. First-run model download for
`all-MiniLM-L6-v2` (~22 MB) will occur at `build` time; `query` does not load the model.

---

## Mechanics/Engine Constraints

None. This is a pure developer tooling ticket — no simulation mechanics, no engine pipeline,
no world state, no entity lifecycle. The Mechanics Bible and Engine Contracts are not
applicable. No parity ledger entries are affected.

---

## Parity Ledger Overlap

None expected. `tools/knowledge_search.py` is a standalone CLI utility with no coupling to
simulation logic, authoritative mutation pipeline, or any subsystem tracked in the parity
ledger files under `docs/parity_ledger/`. No parity ledger entries need to be created or
updated for this ticket.

---

## Prior Work

### Directly related done tickets
None found in `tickets/done/` or `tickets/working_log.csv` for vector search, sqlite-vec,
sentence-transformers, FAISS, or semantic embedding.

### Tangentially related done tickets
The following done tickets deal with "knowledge" in the simulation domain (not tooling):

| Ticket ID | Summary | Relation |
|---|---|---|
| TCK-20260524-LAB-KNOWLEDGE | UpdateSimulationKnowledge workflow — stores simulation insights into `data/lab_knowledge/` | Different domain: simulation lab knowledge store, not ticket-history search. No shared code. |
| TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT | Splits SYNCED/NO_INSIGHTS status in the lab knowledge workflow | Same lab domain — no overlap with this ticket. |
| TCK-20260410-PH3-STRATEGIC-KNOWLEDGE | Typed strategic leads and blockers in entity cognition | Cognition domain — no overlap. |

No prior implementation of vector indexing, embedding, or sqlite-vec exists anywhere in the
codebase.

### Existing tools/ test patterns
`tests/tools/` has 6 test files covering existing tools
(`test_validate_frontmatter.py`, `test_generate_registry.py`, etc.). The pattern is:
- Module import via `sys.path` manipulation (tools/ is not a package)
- `subprocess.run` for CLI contract tests (exit code, stdout, stderr)
- Direct function call tests for unit coverage
- Anti-drift enum assertions

The new `tests/tools/test_knowledge_search.py` should follow this pattern exactly.

---

## Risks and Open Questions

### R1: sqlite-vec SQLite version
sqlite-vec requires SQLite >= 3.38.0. The current runtime is SQLite 3.46.1, which satisfies
the requirement. However, this is a runtime dependency — if the project is deployed on a
system with an older SQLite (e.g., Ubuntu 20.04 ships 3.31.1), sqlite-vec will fail to load.
The `build` command must check SQLite version at startup and print a clear error if the
minimum is not met. **Recommendation:** document the minimum (3.38.0) in a module-level
docstring and check at import time.

### R2: sentence-transformers first-run model download
`all-MiniLM-L6-v2` (~22 MB) is downloaded from HuggingFace on first call to
`SentenceTransformer('all-MiniLM-L6-v2')`. In air-gapped environments or CI without internet
access, this will silently hang or fail. The `build` command must print:
`"Downloading model all-MiniLM-L6-v2 (~22MB) on first run..."` before calling the model.
The model is cached in `~/.cache/huggingface/` after the first download.
**Open question:** should CI skip `make knowledge-index`? Yes — this target is for developer
environments only, not CI. It must not be added to `make test` or any CI gate.

### R3: Incremental update is out of scope
The ticket explicitly defers incremental update (add one ticket without full rebuild) to a
follow-up. The current design requires a full rebuild via `make knowledge-index` after each
ticket closes. This is acceptable for the current corpus size (660 done tickets + 382
investigations + 580 working log rows = ~1622 documents) but will grow. The follow-up ticket
is not yet created.

### R4: Corpus scope discipline
The corpus is strictly:
1. `tickets/working_log.csv` (embed `title + summary` per row)
2. `stored_artifacts/*/investigation.md` (embed first 500 chars)
3. `tickets/done/TCK-*.md` (embed `## Request Summary` section only)

NOT: `docs/`, `src/`, `tests/`, or any other path. This boundary must be enforced in the
`build` subcommand and tested explicitly. See Anti-Drift Hazards below.

### R5: pyproject.toml vs requirements.txt
The project uses both `pyproject.toml` (authoritative for package metadata) and
`requirements.txt` (pinned lockfile, UTF-16 encoded). New deps (`sentence-transformers`,
`sqlite-vec`) should be added to `pyproject.toml` under a new `[project.optional-dependencies]`
`knowledge` group. They should NOT be added to `requirements.txt` (which is a generated
lockfile). The install instruction in `make knowledge-index` or its docs should use
`pip install -e ".[knowledge]"`.

---

## Anti-Drift Hazards

### Corpus boundary drift
The most likely long-term bug: a future maintainer adds `docs/` or `src/` to the corpus
because it "seems useful". This would break the explicit out-of-scope boundary and balloon
index size. The test suite must assert that `build` only reads from the three defined paths.

### Graceful degradation regression
If a future refactor removes the `try/except ImportError` guard, `query` will crash instead
of warning when packages are absent. This is a regression risk. The graceful-degradation test
must be run in a subprocess with `PYTHONPATH` configured to exclude the real packages
(or by mocking the import).

### Step 0 positional drift in create-tickets.js
If `create-tickets.js` is refactored and the Investigate phase prompt is reorganized, Step 0
may move out of position or lose its "skip if index absent" guard. The integration point
description below specifies the exact insertion site.

---

## Integration Point: Step 0 in create-tickets.js

### Current structure (lines 248–332)
The per-concern agent prompt in `create-tickets.js` begins at line 248 (`return agent(...`).
The prompt string starts with:
```
Investigate concern "${concern.id}: ${concern.title}" using the project's structured
knowledge assets before falling back to grep.
...
─── Step 1: Knowledge graph — code structure ──────
```

### Required change
Prepend a Step 0 block **before** the `─── Step 1` header, inside the same agent prompt
string. The step must:

1. Run `python3 tools/knowledge_search.py query "<concern title> <concern description>" --top-k 5`
2. If the command exits non-zero or prints the "knowledge index not found" warning, skip and continue.
3. For each line of output: parse the ticket ID (format: `TCK-YYYYMMDD-SCOPE`) and file path.
4. Pass the found ticket IDs into Step 3 (prior ticket history) as warm-start candidates —
   the agent should cross-reference these IDs in the working log without re-running the query.

### Insertion site
Immediately after the `Raw excerpts from proposal:` block and before the first `───` section
header. The new Step 0 section header should follow the same visual style:

```
─── Step 0: Semantic prior-work retrieval ─────────────────────────────────────

  Run (only if knowledge-index/ exists — the tool will self-check):
    python3 tools/knowledge_search.py query "${concern.title} ${concern.description}" --top-k 5

  If the command prints "knowledge index not found" or exits non-zero: skip and proceed to Step 1.
  If results are returned: note each returned ticket ID and path. Use these as warm-start
  candidates in Step 3 (prior ticket cross-reference) — check them in working_log.csv before
  running additional keyword greps.

```

### Why not a separate agent call
The ticket calls for Step 0 to be part of the Investigate phase concern-agent prompt, not a
separate pipeline stage. This keeps the semantic results in the same agent context as the
structured lookups, so the agent can synthesize both without a handoff.
