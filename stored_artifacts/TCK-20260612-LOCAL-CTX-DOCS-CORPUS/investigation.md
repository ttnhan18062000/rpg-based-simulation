---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-DOCS-CORPUS
artifact_type: investigation
tags: [tooling, rag, knowledge-search, docs]
---

# Investigation — TCK-20260612-LOCAL-CTX-DOCS-CORPUS

## Current Behavior

### tools/knowledge_search.py corpus (as of TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH)

The existing `_collect_corpus()` function reads from exactly three sources:
1. `tickets/done/TCK-*.md` — `## Request Summary` section only (per `_extract_request_summary()`)
2. `stored_artifacts/*/investigation.md` — first 500 characters only
3. `tickets/working_log.csv` — `title + summary` per row via `_extract_working_log_rows()`

`docs/` is explicitly excluded. The foundation investigation doc notes this boundary: *"NOT: `docs/`, `src/`, `tests/`, or any other path."* The `TestCorpusScopeGuard.test_collect_corpus_only_reads_defined_roots` test explicitly asserts that `docs/extra.md` does not leak into the corpus.

### query output format (current)

`cmd_query()` prints three tab-separated fields per result:
```
{doc_id}\t{path}\t{snippet}
```
No `heading`, `section`, or other per-chunk metadata is emitted. The `knowledge_docs` table stores only: `rowid`, `doc_id`, `path`, `text`, `source_type`.

### knowledge_docs schema (current)

```sql
CREATE TABLE knowledge_docs (
    rowid       INTEGER PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    path        TEXT NOT NULL,
    text        TEXT NOT NULL,
    source_type TEXT NOT NULL
)
```

The `source_type` field currently takes values `ticket`, `investigation`, `working_log`. It will gain `doc` as a new value.

---

## Current knowledge_search.py Structure

### Key functions and integration points

| Function | Location | Role |
|---|---|---|
| `_collect_corpus(corpus_root)` | line 117 | Aggregates all documents; returns `list[dict]` with keys `id`, `path`, `text`, `source_type` |
| `_extract_request_summary(text)` | line 61 | Ticket-specific extractor; H2 section parser |
| `_extract_working_log_rows(csv_path)` | line 79 | CSV reader; returns list of row dicts |
| `cmd_build(args)` | line 207 | Embeds corpus, creates sqlite-vec db; prints per-source summary |
| `cmd_query(args)` | line 303 | Encodes query, runs ANN search, prints tab-separated results |
| `_serialize_f32(vector)` | line 198 | Little-endian f32 packing for sqlite-vec |

### How to extend `_collect_corpus()`

`_collect_corpus()` is the single collection point. Each source type appends dicts to the `docs` list. Adding docs corpus support means:

1. Add a new helper function `_collect_docs_chunks(docs_root: Path) -> list[dict]` that:
   - Walks `docs_root` for `*.md` files
   - Skips `docs/archive/` and `docs/lab/` subtrees
   - For each file: strips frontmatter, splits on H2/H3 headings, yields chunk dicts

2. Call `_collect_docs_chunks(corpus_root / "docs")` inside `_collect_corpus()` and extend the `docs` list.

### How to extend `cmd_build()`

The build summary print on lines 235–242 currently reads:
```python
print(
    f"Corpus: {ticket_count} ticket summaries, "
    f"{inv_count} investigation files, "
    f"{wl_count} working log rows"
)
```
Add a `doc_chunk_count` counter and extend the print to include `{doc_chunk_count} docs chunks`.

### How to extend `cmd_query()`

The SELECT query (lines 338–348) joins `knowledge_vec` and `knowledge_docs`. To expose `heading` and `section`, those columns must be added to `knowledge_docs`. The SELECT becomes:
```sql
SELECT d.doc_id, d.path, d.heading, d.section, d.text, v.distance
FROM knowledge_vec v JOIN knowledge_docs d ON d.rowid = v.rowid
WHERE v.embedding MATCH ? AND k = ?
ORDER BY v.distance
```
Output format changes from 3 to 5 tab-separated fields:
```
{doc_id}\t{path}\t{heading}\t{section}\t{snippet}
```
Existing ticket/investigation rows will have `heading=""` and `section=""` (or a sentinel like `"ticket"` / `"investigation"`) — this must not break the query path.

---

## Docs Corpus Analysis

### Total file counts

| Subtree | .md files | Include? | Notes |
|---|---|---|---|
| `docs/engine/` | 141 | YES | Engine contracts, authoritative pipeline — high-value |
| `docs/specs/` | 37 | YES | Specification docs |
| `docs/mechanics/` | 10 | YES | Mechanics Bible chapters 01–06 + related |
| `docs/observability/` | 15 | YES | Observability contracts |
| `docs/testing/` | 13 | YES | Test taxonomy and patterns |
| `docs/systems/` | 11 | YES | System-level docs |
| `docs/performance/` | 11 | YES | Performance contracts |
| `docs/strategy/` | 9 | YES | Bounded cognition contracts |
| `docs/combat/` | 9 | YES | Combat rulebooks |
| `docs/simulation/` | 8 | YES | Simulation docs |
| `docs/guidelines/` | 8 | YES | Design patterns, divergences |
| `docs/architecture/` | 8 | YES | ADRs |
| `docs/core/` | 6 | YES | State, entities, attributes |
| `docs/ai/` | 5 | YES | AI docs |
| `docs/world/` | 4 | YES | World docs |
| `docs/plans/` | 3 | YES | Plan docs |
| `docs/content/` | 3 | YES | Content docs |
| `docs/compliance/` | 3 | YES | Compliance checklist/gap |
| `docs/agent-monitoring/` | 3 | YES | Monitoring docs |
| `docs/archive/` | 236 | **NO** | Stale — explicit exclusion in ticket scope |
| `docs/lab/` | 0 | **NO** | Empty; excluded per ticket scope |
| `docs/parity_ledger/` | 0 | N/A | Contains only .yaml and .json files — no .md to index |
| `docs/worldmodules/` etc. | 0 | N/A | Empty directories |

**Total included**: ~310 `.md` files across 19 subtrees.
**Total excluded**: 236 `docs/archive/` + 0 `docs/lab/` = 236 files excluded.
**Grand total in docs/**: 546 files (matches ticket claim of ~545).

### Heading density — spot-check

`docs/mechanics/02_combat_laws.md`: 7 H2 headings, 2 H3 headings across ~76 lines. Sections are well-bounded, 50–150 words each — well within the 200–500 word target. Most sections will not need further splitting.

`docs/engine/authoritative_pipeline.md`: 7+ H2 headings. Engine docs tend to be denser with numbered phase lists, tables, and code blocks. Some H2 sections may exceed 600 words and need H3 splitting.

### Files with no H2/H3 headings (all docs/, excluding archive/lab/)

Confirmed: exactly 2 files have no H2 or H3 headings:
- `docs/architecture/cognition_domain_ownership.md`
- `docs/mechanics/content_usage_matrix.md`

These must be handled via a "whole file as single chunk" fallback. Both are small enough (under 500 words estimated) that treating the full text as one chunk is correct.

---

## Chunking Design

### Algorithm

```
For each *.md file (excluding archive/, lab/):
  1. Strip YAML frontmatter (--- block)
  2. Extract title from frontmatter or first H1
  3. Split body on H2 headings → sections[]
  4. For each H2 section:
     a. If word_count(section) <= 600: emit as one chunk
     b. If word_count(section) > 600: split on H3 headings
        - Each H3 sub-section: emit as one chunk
        - If sub-section still > 600 words: hard-split at 500-word boundary
           with 50-word overlap carry-forward
  5. If no H2/H3 found: emit whole file body as one chunk (fallback)
```

### Chunk metadata schema

```json
{
  "id":          "mechanics/02_combat_laws#h2-damage-formula-001",
  "doc_id":      "mechanics/02_combat_laws",
  "path":        "docs/mechanics/02_combat_laws.md",
  "text":        "...",
  "source_type": "doc",
  "heading":     "The Damage Formula",
  "section":     "mechanics"
}
```

- `id` (used as `doc_id` in the DB): `{section}/{stem}#{heading-slug}-{sequence:03d}`
- `section`: the immediate subdirectory of `docs/` (e.g. `mechanics`, `engine`, `strategy`)
- `heading`: the H2 or H3 heading text (stripped of leading `#` and whitespace); `""` for no-heading fallback
- `source_type`: always `"doc"` for docs corpus entries

### Heading slug generation

```python
import re
def _heading_slug(heading: str) -> str:
    slug = heading.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)   # strip emoji and punctuation
    slug = re.sub(r"\s+", "-", slug)
    return slug[:40]  # cap length
```

Note: `docs/engine/authoritative_pipeline.md` has emoji in headings (e.g. `🏃 Phase 7`). The slug must strip emoji before generating the ID.

### 50-word overlap

When a section is hard-split at the word boundary, carry the last 50 words of the preceding chunk into the start of the next chunk. This is only triggered when a sub-section exceeds 600 words after H3 splitting — expected to be rare.

### Estimated chunk count

~310 files × average 3–5 H2 sections per file = 930–1,550 chunks before any H3 splitting. With H3 sub-splitting on dense engine docs, estimated total: 1,500–2,500 chunks. Comfortably above the AC threshold of 500 chunks.

---

## sqlite-vec Schema Extension

### Current schema

```sql
CREATE VIRTUAL TABLE knowledge_vec USING vec0(embedding float[{dim}])
CREATE TABLE knowledge_docs (
    rowid       INTEGER PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    path        TEXT NOT NULL,
    text        TEXT NOT NULL,
    source_type TEXT NOT NULL
)
```

### Required extension

```sql
CREATE TABLE knowledge_docs (
    rowid       INTEGER PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    path        TEXT NOT NULL,
    text        TEXT NOT NULL,
    source_type TEXT NOT NULL,
    heading     TEXT NOT NULL DEFAULT '',
    section     TEXT NOT NULL DEFAULT ''
)
```

The `knowledge_vec` virtual table is unchanged — it only stores the float embedding indexed by `rowid`.

### Backward compatibility

The `build` command always drops and recreates the DB (`if db_path.exists(): db_path.unlink()`). There is no migration needed — the new schema takes effect on next `make knowledge-index` run. Existing ticket/investigation rows use `heading=''` and `section=''`.

### INSERT statement update

```python
conn.execute(
    "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    (i, doc["id"], doc["path"], doc["text"], doc["source_type"],
     doc.get("heading", ""), doc.get("section", "")),
)
```

Existing ticket/investigation dicts do not include `heading` or `section` keys — `dict.get()` with default `""` handles this without modifying the existing corpus collection code.

### Query SELECT update

```sql
SELECT d.doc_id, d.path, d.heading, d.section, d.text, v.distance
FROM knowledge_vec v
JOIN knowledge_docs d ON d.rowid = v.rowid
WHERE v.embedding MATCH ?
  AND k = ?
ORDER BY v.distance
```

Output print becomes:
```python
for doc_id, path, heading, section, text, _dist in rows:
    snippet = text[:120].replace("\n", " ").replace("\t", " ")
    print(f"{doc_id}\t{path}\t{heading}\t{section}\t{snippet}")
```

The AC explicitly requires results include `ticket_id_or_doc_id`, `source_path`, `heading`, `section`, `snippet` — 5 fields.

---

## Parity Ledger Overlap

None. `tools/knowledge_search.py` is a standalone developer tooling utility. It has no coupling to simulation mechanics, authoritative mutation pipeline, entity lifecycle, or any subsystem tracked in `docs/parity_ledger/`. No parity ledger entries need to be created or updated for this ticket.

---

## Risks and Open Questions

### R1: Emoji in headings (confirmed)

`docs/engine/authoritative_pipeline.md` contains emoji in H2 headings (e.g. `🏃 Phase 7: Locomotion Routing`, `🗺️ Phase 13`, `🧠 Phase 16`). The heading slug generator must strip non-ASCII and emoji characters before generating chunk IDs. This is low-risk to fix but must be explicitly tested.

### R2: Docs with no H2/H3 headings

Exactly 2 files confirmed without H2 or H3 headings:
- `docs/architecture/cognition_domain_ownership.md`
- `docs/mechanics/content_usage_matrix.md`

Fallback: treat the entire body (post-frontmatter) as one chunk. Both files are small enough that this is correct. The fallback must be exercised by a test.

### R3: Very large single H2 sections in engine docs

Engine docs (`docs/engine/`, 141 files) tend to be dense. Some H2 sections may contain extensive numbered lists and tables that push past 600 words. The H3 sub-splitting path handles this, but very long tables (no H3 children) will fall through to the hard 500-word split. Hard splits mid-table row may produce semantically poor chunks. Mitigation: accept this for now; the 50-word overlap preserves some context. Consider adding a test that verifies no chunk exceeds 800 words.

### R4: Frontmatter-only files

Some docs may have a YAML frontmatter block but no body content. After stripping frontmatter, the remaining text is empty. These files must produce zero chunks (not a chunk with empty text). The collector must guard `if not body.strip(): continue`.

### R5: Performance on 310 files / ~2000 chunks

The build AC requires completion in under 5 minutes on 1 CPU core. The current corpus embeds ~1,622 documents. Adding ~2,000 doc chunks brings the total to ~3,600 rows. `all-MiniLM-L6-v2` encodes ~500–1,000 sentences/second on CPU with batch processing. 3,600 chunks at 200–400 words each will take 10–30 seconds for embedding, well within the 5-minute limit. No performance risk.

### R6: Output format change breaks existing callers

Changing query output from 3 tab-separated fields to 5 will break any caller parsing the current `{doc_id}\t{path}\t{snippet}` format. The existing `test_query_result_format_tab_separated` test asserts `len(parts) == 3` — it must be updated to assert `len(parts) == 5`. The `create-tickets.js` Step 0 parses the first field (ticket ID) and second field (path) — these positions are unchanged, so the Step 0 integration is not broken by the extra columns.

### R7: `parity_ledger/` contains only .yaml files

Confirmed: `docs/parity_ledger/` contains `.yaml` files and `schema.json` only — no `.md` files. The `find docs -name "*.md"` walk will naturally produce zero results from this directory. No special exclusion needed beyond the already-excluded `archive/` and `lab/`.

---

## Anti-Drift Hazards

### Must not index docs/archive/ or docs/lab/

`docs/archive/` contains 236 stale markdown files. Indexing them would add noise and break the query signal. The exclusion must be:
- Implemented as an explicit path prefix check in `_collect_docs_chunks()`: `if "docs/archive" in str(md_file) or "docs/lab" in str(md_file): continue`
- Tested by a new `TestDocsCorpusScopeGuard` test that creates fake archive/lab files and asserts none appear in the corpus.

### Must not break existing ticket/investigation query results

The three existing corpus sources (`ticket`, `investigation`, `working_log`) are unchanged. The only code paths that touch them are inside `_collect_corpus()`, which remains the authoritative aggregator. The schema extension adds two nullable-defaulted columns — existing rows get `heading=""` and `section=""`. The query SELECT change adds two new output fields. The `TestCorpusScopeGuard.test_collect_corpus_includes_all_three_sources` test must continue to pass without modification.

### Output format column count

The format change from 3 to 5 tab-separated columns is a breaking change for test `test_query_result_format_tab_separated`. That test must be updated as part of this ticket. Any other downstream consumer of the query output (currently only `create-tickets.js` Step 0) must be verified to tolerate extra columns (it does — it parses by field index 0 and 1 only).

### Do not add docs embedding to CI or make test target

The `knowledge-index` Makefile target is already excluded from CI (confirmed by `test_knowledge_index_not_in_test_target`). The docs corpus expansion does not change this — it remains a developer-only tool invoked via `make knowledge-index`.
