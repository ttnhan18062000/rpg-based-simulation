"""
tools/knowledge_search.py — Semantic knowledge search for ticket and investigation history.

Subcommands:
  build   Embed the corpus and write a local vector index to knowledge-index/knowledge.db
  query   Return top-N nearest neighbours with ticket ID, path, and summary snippet

Corpus (targeted — not the full codebase):
  tickets/done/TCK-*.md            → ## Request Summary section only
  stored_artifacts/*/investigation.md → first 500 characters
  tickets/working_log.csv          → title + summary per row
  docs/ (excluding archive/, lab/) → heading-aware chunks

Embedding model: all-MiniLM-L6-v2 via sentence-transformers (~22 MB, cached after first run)
Vector store:    sqlite-vec (single .db file, zero-config, requires SQLite >= 3.38.0)

Install optional deps:
    pip install -e ".[knowledge]"

Usage:
    python3 tools/knowledge_search.py build [--corpus-root PATH] [--db-path PATH]
    python3 tools/knowledge_search.py query "player fatigue during combat" [--top-k 5] [--db-path PATH]
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

# Use locally cached HuggingFace models after first download — avoids SSL cert
# failures on networks where the system Python bundle doesn't trust the HF CDN.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
from hybrid_retrieval import hybrid_fuse_and_filter  # noqa: E402

_DEFAULT_DB = Path("knowledge-index/knowledge.db")
_MANIFEST_PATH = Path("knowledge-index/manifest.json")
_CACHE_PATH = Path("knowledge-index/embeddings_cache.pkl")
_MODEL_NAME = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

def _check_deps() -> tuple[bool, str]:
    """Try importing sentence_transformers and sqlite_vec. Return (ok, error_msg)."""
    missing = []
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        missing.append("sentence-transformers")
    try:
        import sqlite_vec  # noqa: F401
    except ImportError:
        missing.append("sqlite-vec")
    if missing:
        msgs = ", ".join(missing)
        return False, f"Warning: {msgs} not installed — run: pip install -e '.[knowledge]'"
    return True, ""


# ---------------------------------------------------------------------------
# Corpus extraction helpers
# ---------------------------------------------------------------------------

def _extract_request_summary(text: str) -> str:
    """Extract the ## Request Summary section from a ticket markdown file.

    Returns the section body (stripped), or the first 500 chars of the file
    if the section is not found.
    """
    pattern = re.compile(
        r"^##\s+Request\s+Summary\s*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    # Fallback: use first 500 chars (strip YAML frontmatter if present)
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL).strip()
    return body[:500]


def _extract_working_log_rows(csv_path: Path) -> list[dict]:
    """Read working_log.csv, return list of {id, title, summary, path} dicts.

    Read-only: this function never opens csv_path in a write/append mode. Exact-content
    duplicate rows (e.g. the whole-block squash-merge duplication documented in
    TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP) are deduped in-memory here —
    keeping only the first occurrence, the same convention tools/working_log_parser.py's
    own `seen_raw_lines`/`is_duplicate`/`duplicate_of_line` tracking already uses — so the
    corpus this feeds does not carry one document per duplicate physical line.
    """
    rows = []
    skipped_embedded_header_duplicates = 0
    skipped_exact_content_duplicates = 0
    seen_content = set()
    if not csv_path.exists():
        return rows
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Common column name variants across project evolution
                ticket_id = (
                    row.get("ticket_id") or row.get("id") or row.get("ID") or ""
                ).strip()
                title = (
                    row.get("title") or row.get("Title") or row.get("name") or ""
                ).strip()
                summary = (
                    row.get("summary")
                    or row.get("Summary")
                    or row.get("description")
                    or row.get("request_summary")
                    or ""
                ).strip()
                if not ticket_id and not title:
                    continue
                # A data row whose ticket_id is literally the header's own column name is
                # an embedded duplicate header row (e.g. tickets/working_log.csv:1594 from
                # a whole-block merge duplication), not a real corpus document.
                if ticket_id == "ticket_id":
                    skipped_embedded_header_duplicates += 1
                    continue
                content_key = (ticket_id, title, summary)
                if content_key in seen_content:
                    skipped_exact_content_duplicates += 1
                    continue
                seen_content.add(content_key)
                rows.append(
                    {
                        "id": ticket_id or title,
                        "title": title,
                        "summary": summary,
                        "path": str(csv_path),
                    }
                )
    except Exception as exc:
        print(f"Warning: could not read {csv_path}: {exc}", file=sys.stderr)
    if skipped_embedded_header_duplicates:
        print(
            f"Warning: skipped {skipped_embedded_header_duplicates} "
            f"embedded-header-duplicate row(s) in {csv_path}",
            file=sys.stderr,
        )
    if skipped_exact_content_duplicates:
        print(
            f"Warning: skipped {skipped_exact_content_duplicates} "
            f"exact-content-duplicate row(s) in {csv_path}",
            file=sys.stderr,
        )
    return rows


def _collect_corpus(corpus_root: Path) -> list[dict]:
    """Collect all documents from the four defined corpus roots.

    Returns a list of dicts: {id, path, text, source_type}.

    Corpus roots (relative to corpus_root):
      - tickets/done/TCK-*.md              → _extract_request_summary(content)
      - stored_artifacts/*/investigation.md → content[:500]
      - tickets/working_log.csv            → _extract_working_log_rows()
      - docs/ (excluding archive/, lab/)   → _collect_docs_chunks(docs_root)

    ONLY these four paths are traversed — no src/, tests/, or other paths.
    """
    docs: list[dict] = []

    # 1. tickets/done/TCK-*.md — Request Summary section only
    done_dir = corpus_root / "tickets" / "done"
    if done_dir.exists():
        for md_file in sorted(done_dir.glob("TCK-*.md")):
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                extracted = _extract_request_summary(text)
                if not extracted:
                    continue
                # Derive ticket ID from filename stem
                ticket_id = md_file.stem
                docs.append(
                    {
                        "id": ticket_id,
                        "path": str(md_file),
                        "text": extracted,
                        "source_type": "ticket",
                    }
                )
            except Exception as exc:
                print(f"Warning: skipping {md_file}: {exc}", file=sys.stderr)

    # 2. stored_artifacts/*/investigation.md — first 500 characters
    artifacts_root = corpus_root / "stored_artifacts"
    if artifacts_root.exists():
        for inv_file in sorted(artifacts_root.glob("*/investigation.md")):
            try:
                text = inv_file.read_text(encoding="utf-8", errors="replace")
                snippet = text[:500].strip()
                if not snippet:
                    continue
                # Use parent directory name as ID (usually the ticket ID)
                doc_id = inv_file.parent.name
                docs.append(
                    {
                        "id": doc_id,
                        "path": str(inv_file),
                        "text": snippet,
                        "source_type": "investigation",
                    }
                )
            except Exception as exc:
                print(f"Warning: skipping {inv_file}: {exc}", file=sys.stderr)

    # 3. tickets/working_log.csv — title + summary per row
    wl_path = corpus_root / "tickets" / "working_log.csv"
    rows = _extract_working_log_rows(wl_path)
    for row in rows:
        combined = f"{row['title']} {row['summary']}".strip()
        if not combined:
            continue
        docs.append(
            {
                "id": row["id"],
                "path": row["path"],
                "text": combined,
                "source_type": "working_log",
            }
        )

    # 4. docs/ — heading-aware chunks (excludes docs/archive/ and docs/lab/)
    docs_dir = corpus_root / "docs"
    if docs_dir.exists():
        docs.extend(_collect_docs_chunks(docs_dir, corpus_root))

    return docs


# ---------------------------------------------------------------------------
# Docs corpus helpers
# ---------------------------------------------------------------------------

def _heading_slug(heading: str) -> str:
    """Generate an ASCII-safe slug from a heading string.

    Strips emoji and non-word characters, lowercases, replaces whitespace
    with hyphens, caps at 40 characters.
    """
    slug = heading.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)   # strip emoji and non-word characters
    slug = re.sub(r"\s+", "-", slug)
    return slug[:40]


def _strip_frontmatter(text: str) -> str:
    """Remove the leading YAML frontmatter block (--- ... ---) from a markdown file."""
    return re.sub(r"^\s*---.*?---\s*", "", text, flags=re.DOTALL).strip()


def _collect_docs_chunks(docs_root: Path, corpus_root: Path) -> list[dict]:
    """Walk docs_root for *.md files and return heading-aware chunks.

    Exclusions: docs/archive/ and docs/lab/ subtrees are never indexed.

    Chunk metadata keys per returned dict:
      id          — "{doc_id}#{heading-slug}-{seq:03d}" or "{doc_id}#body-000"
      doc_id      — full relative path under docs_root, minus ".md" suffix (document-level
                    identity, no chunk qualifier)
      path        — relative path string from corpus_root (e.g. "docs/mechanics/02.md")
      text        — chunk text (never empty)
      source_type — always "doc_chunk"
      heading     — H2/H3 heading text (stripped of leading # and whitespace); "" for no-heading fallback
      section     — immediate subdirectory of docs_root (e.g. "mechanics", "engine")
    """
    chunks: list[dict] = []

    for md_file in sorted(docs_root.rglob("*.md")):
        # Exclusion guard: skip docs/archive/ and docs/lab/ subtrees
        md_str = str(md_file).replace("\\", "/")
        if "/docs/archive/" in md_str or md_str.endswith("/docs/archive"):
            continue
        if "/docs/lab/" in md_str or md_str.endswith("/docs/lab"):
            continue
        # Also handle relative path checks for robustness
        try:
            rel = md_file.relative_to(docs_root)
        except ValueError:
            continue
        rel_parts = rel.parts
        if rel_parts and rel_parts[0] in ("archive", "lab"):
            continue

        try:
            raw = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"Warning: skipping {md_file}: {exc}", file=sys.stderr)
            continue

        body = _strip_frontmatter(raw)
        if not body.strip():
            continue

        # Derive relative path string from corpus_root
        try:
            path_str = str(md_file.relative_to(corpus_root))
        except ValueError:
            path_str = str(md_file)

        # doc_id preserves the full nested relative path under docs_root, not just
        # the immediate subdirectory — fixes TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION.
        doc_id = rel.with_suffix("").as_posix()

        # section retained for the existing "section" chunk-metadata field (used by
        # search_mcp.py's --section post-filter) — still the immediate subdirectory,
        # unchanged semantics, computed the same way as before.
        section = rel_parts[0] if len(rel_parts) > 1 else ""

        # Split body on H2 headings
        h2_parts = re.split(r"^(## .+)$", body, flags=re.MULTILINE)

        # h2_parts structure: [pre-H2-text, "## Heading1", body1, "## Heading2", body2, ...]
        # If no H2 found, h2_parts == [body] (length 1)
        if len(h2_parts) == 1:
            # No H2 headings — emit whole body as one chunk
            text = body.strip()
            if text:
                chunks.append({
                    "id": f"{doc_id}#body-000",
                    "doc_id": doc_id,
                    "path": path_str,
                    "text": text,
                    "source_type": "doc_chunk",
                    "heading": "",
                    "section": section,
                })
            continue

        file_seq = 0

        # Process pre-H2 preamble (index 0) as a no-heading chunk if non-empty
        preamble = h2_parts[0].strip()
        if preamble:
            chunks.append({
                "id": f"{doc_id}#body-{file_seq:03d}",
                "doc_id": doc_id,
                "path": path_str,
                "text": preamble,
                "source_type": "doc_chunk",
                "heading": "",
                "section": section,
            })
            file_seq += 1

        # Process H2 sections: pairs of (heading_line, section_body) starting at index 1
        i = 1
        while i < len(h2_parts) - 1:
            h2_heading_line = h2_parts[i].strip()
            h2_body = h2_parts[i + 1]
            i += 2

            # Extract heading text (strip leading "## ")
            h2_heading_text = re.sub(r"^##\s+", "", h2_heading_line).strip()
            h2_full = (h2_heading_line + "\n" + h2_body).strip()

            word_count = len(h2_full.split())

            if word_count <= 600:
                # Emit entire H2 section as one chunk
                if h2_full:
                    chunks.append({
                        "id": f"{doc_id}#{_heading_slug(h2_heading_text)}-{file_seq:03d}",
                        "doc_id": doc_id,
                        "path": path_str,
                        "text": h2_full,
                        "source_type": "doc_chunk",
                        "heading": h2_heading_text,
                        "section": section,
                    })
                    file_seq += 1
            else:
                # Large H2 section — try splitting on H3 headings
                h3_parts = re.split(r"^(### .+)$", h2_body, flags=re.MULTILINE)

                if len(h3_parts) == 1:
                    # No H3 headings — hard-split at 500-word boundary with 50-word overlap
                    all_words = h2_full.split()
                    chunk_size = 500
                    overlap = 50
                    start = 0
                    while start < len(all_words):
                        end = min(start + chunk_size, len(all_words))
                        chunk_text = " ".join(all_words[start:end])
                        if chunk_text.strip():
                            chunks.append({
                                "id": f"{doc_id}#{_heading_slug(h2_heading_text)}-{file_seq:03d}",
                                "doc_id": doc_id,
                                "path": path_str,
                                "text": chunk_text,
                                "source_type": "doc_chunk",
                                "heading": h2_heading_text,
                                "section": section,
                            })
                            file_seq += 1
                        if end == len(all_words):
                            break
                        start = end - overlap
                else:
                    # Has H3 headings — emit preamble before first H3 (combined with H2 heading)
                    h3_preamble = h3_parts[0].strip()
                    if h3_preamble:
                        preamble_text = (h2_heading_line + "\n" + h3_preamble).strip()
                        if preamble_text:
                            chunks.append({
                                "id": f"{doc_id}#{_heading_slug(h2_heading_text)}-{file_seq:03d}",
                                "doc_id": doc_id,
                                "path": path_str,
                                "text": preamble_text,
                                "source_type": "doc_chunk",
                                "heading": h2_heading_text,
                                "section": section,
                            })
                            file_seq += 1

                    # Process H3 sections: pairs of (heading_line, section_body)
                    j = 1
                    while j < len(h3_parts) - 1:
                        h3_heading_line = h3_parts[j].strip()
                        h3_body = h3_parts[j + 1]
                        j += 2

                        h3_heading_text = re.sub(r"^###\s+", "", h3_heading_line).strip()
                        h3_full = (h3_heading_line + "\n" + h3_body).strip()
                        h3_word_count = len(h3_full.split())

                        if h3_word_count <= 600:
                            if h3_full:
                                chunks.append({
                                    "id": f"{doc_id}#{_heading_slug(h3_heading_text)}-{file_seq:03d}",
                                    "doc_id": doc_id,
                                    "path": path_str,
                                    "text": h3_full,
                                    "source_type": "doc_chunk",
                                    "heading": h3_heading_text,
                                    "section": section,
                                })
                                file_seq += 1
                        else:
                            # Hard-split H3 section with 50-word overlap
                            all_words = h3_full.split()
                            chunk_size = 500
                            overlap = 50
                            start = 0
                            while start < len(all_words):
                                end = min(start + chunk_size, len(all_words))
                                chunk_text = " ".join(all_words[start:end])
                                if chunk_text.strip():
                                    chunks.append({
                                        "id": f"{doc_id}#{_heading_slug(h3_heading_text)}-{file_seq:03d}",
                                        "doc_id": doc_id,
                                        "path": path_str,
                                        "text": chunk_text,
                                        "source_type": "doc_chunk",
                                        "heading": h3_heading_text,
                                        "section": section,
                                    })
                                    file_seq += 1
                                if end == len(all_words):
                                    break
                                start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# sqlite-vec helpers
# ---------------------------------------------------------------------------

def _serialize_f32(vector: list[float]) -> bytes:
    """Serialize a list of floats to a little-endian f32 byte blob for sqlite-vec."""
    return struct.pack(f"{len(vector)}f", *vector)


# ---------------------------------------------------------------------------
# BM25 helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Tokenize text for BM25: lowercase, split on non-alphanumeric (preserving underscores).

    Preserves underscore-joined tokens (e.g. authoritative_pipeline stays as one token).
    CamelCase is NOT split (stretch goal excluded from this ticket's scope).
    """
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _build_bm25_index(corpus: list[dict], bm25_path: Path) -> None:
    """Build a BM25Okapi index from corpus and serialize to bm25_path.

    Serializes a tuple: (BM25Okapi, list[str]) where the list contains
    the doc_id of each corpus entry in order (parallel to BM25 row indices).

    Raises: ImportError if rank_bm25 is not installed.
    """
    from rank_bm25 import BM25Okapi
    import pickle

    doc_ids = [d["id"] for d in corpus]
    tokenized = [_tokenize(d["text"]) for d in corpus]
    bm25 = BM25Okapi(tokenized)
    with open(bm25_path, "wb") as fh:
        pickle.dump((bm25, doc_ids), fh)


def _load_bm25(bm25_path: Path):
    """Load a serialized (BM25Okapi, doc_ids) tuple from bm25_path.

    Returns:
        (bm25, doc_ids) on success
        (None, [])      on missing file or any error — prints a single warning line

    Never raises.
    """
    if not bm25_path.exists():
        print(
            f"Warning: {bm25_path} not found — falling back to vector-only search",
            file=sys.stderr,
        )
        return None, []
    try:
        import pickle
        with open(bm25_path, "rb") as fh:
            return pickle.load(fh)
    except Exception as exc:
        print(
            f"Warning: could not load {bm25_path}: {exc} — falling back to vector-only",
            file=sys.stderr,
        )
        return None, []


def _hybrid_score(
    semantic: float,
    keyword: float,
    title_boost: float,
    heading_boost: float,
    code_boost: float,
) -> float:
    """Compute the hybrid ranking score.

    Formula (initial weights — tunable post-evaluation):
        final = semantic * 0.55
              + keyword  * 0.25
              + title_boost   * 0.10
              + heading_boost * 0.05
              + code_boost    * 0.05

    All inputs are expected in [0.0, 1.0]; output is in [0.0, 1.0].
    """
    return (
        semantic * 0.55
        + keyword * 0.25
        + title_boost * 0.10
        + heading_boost * 0.05
        + code_boost * 0.05
    )


def _compute_boosts(
    query_tokens: list[str],
    doc_id: str,
    heading: str,
    text: str,
) -> tuple:
    """Return (title_boost, heading_boost, code_boost) for a chunk.

    title_boost:   1.0 if any query token appears in doc_id (lowercased)
    heading_boost: 1.0 if any query token appears in heading (lowercased)
    code_boost:    1.0 if any backtick-delimited token in text matches a query token
    """
    title_boost = 1.0 if any(tok in doc_id.lower() for tok in query_tokens) else 0.0
    heading_boost = 1.0 if any(tok in heading.lower() for tok in query_tokens) else 0.0

    # Extract backtick-delimited tokens from text
    code_tokens = set(re.findall(r"`([^`]+)`", text))
    code_boost = 1.0 if any(ct.lower() in query_tokens for ct in code_tokens) else 0.0

    return title_boost, heading_boost, code_boost


# ---------------------------------------------------------------------------
# Manifest helpers (incremental rebuild)
# ---------------------------------------------------------------------------

def _write_manifest(corpus: list[dict], db_path: Path) -> None:
    """Write manifest.json: maps source path → mtime for incremental change detection."""
    manifest_path = db_path.parent / "manifest.json"
    paths: dict[str, float] = {}
    for doc in corpus:
        p = doc.get("path", "")
        if p and p not in paths:
            try:
                paths[p] = os.path.getmtime(p)
            except OSError:
                paths[p] = 0.0
    data = {
        "version": 1,
        "built_at": datetime.now(tz=timezone.utc).isoformat(),
        "paths": paths,
    }
    manifest_path.write_text(json.dumps(data, indent=2))


def _load_manifest(db_path: Path) -> dict[str, float]:
    """Load manifest.json and return {path: mtime}. Returns {} if not found."""
    manifest_path = db_path.parent / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text())
        return dict(data.get("paths", {}))
    except Exception:
        return {}


def _load_embedding_cache(db_path: Path) -> dict[str, list]:
    """Load embeddings_cache.pkl: {path: [embedding, ...]}. Returns {} if not found."""
    import pickle
    cache_path = db_path.parent / "embeddings_cache.pkl"
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return {}


def _save_embedding_cache(db_path: Path, cache: dict[str, list]) -> None:
    """Save embeddings_cache.pkl: {path: [embedding, ...]}."""
    import pickle
    cache_path = db_path.parent / "embeddings_cache.pkl"
    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)


# ---------------------------------------------------------------------------
# Subcommand: build
# ---------------------------------------------------------------------------

def cmd_build(args) -> int:
    """Build the vector index from the three corpus roots."""
    # Lazy ImportError guard — module must import cleanly even without deps
    try:
        from sentence_transformers import SentenceTransformer
        import sqlite_vec  # noqa: F401
    except ImportError as exc:
        pkg = "sentence-transformers" if "sentence_transformers" in str(exc) else "sqlite-vec"
        print(
            f"Warning: {pkg} not installed — run: pip install -e '.[knowledge]'",
            file=sys.stderr,
        )
        return 0

    # SQLite version check
    if sqlite3.sqlite_version_info < (3, 38, 0):
        print(
            f"Error: sqlite-vec requires SQLite >= 3.38.0, found {sqlite3.sqlite_version}",
            file=sys.stderr,
        )
        return 1

    corpus_root = Path(args.corpus_root) if args.corpus_root else Path(".")
    db_path = Path(args.db_path) if args.db_path else _DEFAULT_DB

    print(f"Collecting corpus from {corpus_root.resolve()} ...")
    corpus = _collect_corpus(corpus_root)

    ticket_count = sum(1 for d in corpus if d["source_type"] == "ticket")
    inv_count = sum(1 for d in corpus if d["source_type"] == "investigation")
    wl_count = sum(1 for d in corpus if d["source_type"] == "working_log")
    doc_chunk_count = sum(1 for d in corpus if d["source_type"] == "doc_chunk")
    print(
        f"Corpus: {ticket_count} ticket summaries, "
        f"{inv_count} investigation files, "
        f"{wl_count} working log rows, "
        f"{doc_chunk_count} docs chunks"
    )

    if not corpus:
        print("Warning: corpus is empty — nothing to embed", file=sys.stderr)
        return 0

    print(f"Downloading model {_MODEL_NAME} (~22MB) on first run...")
    model = SentenceTransformer(_MODEL_NAME)

    texts = [d["text"] for d in corpus]
    print(f"Embedding {len(texts)} documents ...")
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    dim = embeddings.shape[1]

    # Write to sqlite-vec database
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    import sqlite_vec as sv  # noqa: F811 — already imported above, alias for clarity
    conn.enable_load_extension(True)
    sv.load(conn)
    conn.enable_load_extension(False)

    conn.execute(
        f"CREATE VIRTUAL TABLE knowledge_vec USING vec0(embedding float[{dim}])"
    )
    conn.execute(
        """
        CREATE TABLE knowledge_docs (
            rowid       INTEGER PRIMARY KEY,
            doc_id      TEXT NOT NULL,
            path        TEXT NOT NULL,
            text        TEXT NOT NULL,
            source_type TEXT NOT NULL,
            heading     TEXT NOT NULL DEFAULT '',
            section     TEXT NOT NULL DEFAULT ''
        )
        """
    )

    for i, (doc, emb) in enumerate(zip(corpus, embeddings)):
        conn.execute(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (i, doc["id"], doc["path"], doc["text"], doc["source_type"],
             doc.get("heading", ""), doc.get("section", "")),
        )
        conn.execute(
            "INSERT INTO knowledge_vec (rowid, embedding) VALUES (?, ?)",
            (i, _serialize_f32(emb.tolist())),
        )

    conn.commit()
    conn.close()

    # --- BM25 keyword index ---
    bm25_path = db_path.parent / "bm25.pkl"
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401
        _build_bm25_index(corpus, bm25_path)
        print(f"BM25 index ({len(corpus)} docs) → {bm25_path}")
    except ImportError:
        print(
            "Warning: rank-bm25 not installed — BM25 index skipped. "
            "Run: pip install -e '.[knowledge]'",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"Warning: BM25 index build failed (non-fatal): {exc}", file=sys.stderr)

    print(f"{len(corpus)} documents embedded → {db_path}")

    # Write manifest for incremental rebuild support
    _write_manifest(corpus, db_path)

    # Rebuild embedding cache (all paths → their embeddings)
    cache: dict[str, list] = {}
    for doc, emb in zip(corpus, embeddings):
        p = doc.get("path", "")
        if p not in cache:
            cache[p] = []
        cache[p].append(emb.tolist())
    _save_embedding_cache(db_path, cache)

    return 0


def cmd_build_incremental(args) -> int:
    """Incremental rebuild: only re-embeds changed or new files; skips unchanged."""
    corpus_root = Path(args.corpus_root) if args.corpus_root else Path(".")
    db_path = Path(args.db_path) if args.db_path else _DEFAULT_DB

    if not db_path.exists():
        print("No existing index found — running full build instead.", file=sys.stderr)
        args.incremental = False
        return cmd_build(args)

    # Load manifest and embedding cache
    manifest = _load_manifest(db_path)
    cache = _load_embedding_cache(db_path)

    # Collect current corpus
    corpus = _collect_corpus(corpus_root)

    # Determine changed, new, and deleted paths
    current_paths: dict[str, list[dict]] = {}
    for doc in corpus:
        p = doc.get("path", "")
        current_paths.setdefault(p, []).append(doc)

    changed: list[str] = []
    unchanged: list[str] = []
    new_paths: list[str] = []
    deleted: list[str] = []

    for p in list(current_paths.keys()):
        try:
            mtime = os.path.getmtime(p)
        except OSError:
            mtime = 0.0
        if p not in manifest:
            new_paths.append(p)
        elif abs(mtime - manifest[p]) > 0.01:
            changed.append(p)
        else:
            unchanged.append(p)

    for p in manifest:
        if p not in current_paths:
            deleted.append(p)

    n_changed = len(changed) + len(new_paths)
    n_deleted = len(deleted)
    n_unchanged = len(unchanged)

    if n_changed == 0 and n_deleted == 0:
        print(
            f"Incremental update: 0 files changed, {n_unchanged} files unchanged. "
            f"Index is up to date."
        )
        return 0

    print(
        f"Incremental update: {n_changed} files changed/new, "
        f"{n_deleted} deleted, {n_unchanged} unchanged."
    )

    # Lazy dep import — only needed when we must re-embed or rebuild the DB
    try:
        from sentence_transformers import SentenceTransformer
        import sqlite_vec  # noqa: F401
    except ImportError as exc:
        pkg = "sentence-transformers" if "sentence_transformers" in str(exc) else "sqlite-vec"
        print(
            f"Error: {pkg} not installed — run: pip install -e '.[knowledge]'",
            file=sys.stderr,
        )
        return 1

    if sqlite3.sqlite_version_info < (3, 38, 0):
        print(
            f"Error: sqlite-vec requires SQLite >= 3.38.0, found {sqlite3.sqlite_version}",
            file=sys.stderr,
        )
        return 1

    # Re-embed only changed and new files
    paths_to_embed = set(changed) | set(new_paths)
    docs_to_embed = [doc for doc in corpus if doc.get("path", "") in paths_to_embed]

    if docs_to_embed:
        print(f"Embedding {len(docs_to_embed)} chunks from {len(paths_to_embed)} changed files...")
        model = SentenceTransformer(_MODEL_NAME)
        texts = [d["text"] for d in docs_to_embed]
        new_embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

        # Update cache for changed paths (replace old entries)
        for p in paths_to_embed:
            cache.pop(p, None)
        for doc, emb in zip(docs_to_embed, new_embeddings):
            p = doc.get("path", "")
            cache.setdefault(p, []).append(emb.tolist())
    else:
        model = None  # only deletions — no encoding needed

    # Remove deleted paths from cache
    for p in deleted:
        cache.pop(p, None)

    # Rebuild full DB using cached embeddings
    dim = None
    all_embeddings: list = []
    all_corpus: list[dict] = []
    for doc in corpus:
        p = doc.get("path", "")
        doc_embs = cache.get(p, [])
        if not doc_embs:
            continue
        # Each doc in corpus maps to one embedding (in order of appearance per path)
        path_docs = current_paths.get(p, [])
        try:
            idx = path_docs.index(doc)
        except ValueError:
            idx = 0
        if idx < len(doc_embs):
            emb = doc_embs[idx]
        else:
            emb = doc_embs[-1]
        all_corpus.append(doc)
        all_embeddings.append(emb)
        if dim is None:
            dim = len(emb)

    if not all_corpus:
        print("Warning: no embeddings after incremental update — corpus may be empty.", file=sys.stderr)
        return 0

    # Write DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    import sqlite_vec as sv
    conn.enable_load_extension(True)
    sv.load(conn)
    conn.enable_load_extension(False)

    conn.execute(f"CREATE VIRTUAL TABLE knowledge_vec USING vec0(embedding float[{dim}])")
    conn.execute(
        """
        CREATE TABLE knowledge_docs (
            rowid       INTEGER PRIMARY KEY,
            doc_id      TEXT NOT NULL,
            path        TEXT NOT NULL,
            text        TEXT NOT NULL,
            source_type TEXT NOT NULL,
            heading     TEXT NOT NULL DEFAULT '',
            section     TEXT NOT NULL DEFAULT ''
        )
        """
    )

    for i, (doc, emb) in enumerate(zip(all_corpus, all_embeddings)):
        conn.execute(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (i, doc["id"], doc["path"], doc["text"], doc["source_type"],
             doc.get("heading", ""), doc.get("section", "")),
        )
        conn.execute(
            "INSERT INTO knowledge_vec (rowid, embedding) VALUES (?, ?)",
            (i, _serialize_f32(emb)),
        )

    conn.commit()
    conn.close()

    # Rebuild BM25 (fast — no model required)
    bm25_path = db_path.parent / "bm25.pkl"
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401
        _build_bm25_index(all_corpus, bm25_path)
    except ImportError:
        pass
    except Exception as exc:
        print(f"Warning: BM25 rebuild failed (non-fatal): {exc}", file=sys.stderr)

    # Update manifest and cache
    _write_manifest(all_corpus, db_path)
    _save_embedding_cache(db_path, cache)

    print(
        f"Incremental update complete: {len(all_corpus)} chunks total "
        f"({n_changed} files re-embedded, {n_unchanged} from cache, {n_deleted} deleted)."
    )
    return 0


# ---------------------------------------------------------------------------
# Subcommand: query
# ---------------------------------------------------------------------------

def cmd_query(args) -> int:
    """Query the knowledge index and return top-k results with hybrid scoring."""
    db_path = Path(args.db_path) if args.db_path else _DEFAULT_DB

    if not db_path.exists():
        print(
            "knowledge index not found — run make knowledge-index",
            file=sys.stderr,
        )
        return 0

    mode = getattr(args, "mode", "hybrid")
    query_text = args.query
    top_k = args.top_k

    # Lazy ImportError guard — only needed for vector/hybrid modes
    if mode in ("hybrid", "vector"):
        try:
            from sentence_transformers import SentenceTransformer
            import sqlite_vec  # noqa: F401
        except ImportError as exc:
            pkg = "sentence-transformers" if "sentence_transformers" in str(exc) else "sqlite-vec"
            print(
                f"Warning: {pkg} not installed — run: pip install -e '.[knowledge]'",
                file=sys.stderr,
            )
            return 0

    query_tokens = _tokenize(query_text)

    # --- BM25 path ---
    bm25_obj = None
    bm25_raw = None
    bm25_max = 1.0
    if mode in ("hybrid", "keyword"):
        bm25_path = db_path.parent / "bm25.pkl"
        bm25_obj, _bm25_doc_ids = _load_bm25(bm25_path)
        if bm25_obj is None and mode == "hybrid":
            # Graceful fallback: hybrid -> vector
            mode = "vector"
        elif bm25_obj is None and mode == "keyword":
            # keyword mode with no BM25: fall back to vector
            print(
                "Warning: bm25.pkl missing for keyword mode — falling back to vector-only",
                file=sys.stderr,
            )
            mode = "vector"

    if bm25_obj is not None:
        import numpy as _np
        bm25_raw = bm25_obj.get_scores(query_tokens)
        bm25_max = float(bm25_raw.max()) if bm25_raw.max() > 0 else 1.0

    # --- True hybrid path: independent bounded dense + lexical retrieval, RRF fusion ---
    if mode == "hybrid" and bm25_obj is not None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(_MODEL_NAME)
        query_emb = model.encode([query_text], show_progress_bar=False, convert_to_numpy=True)[0]

        conn = sqlite3.connect(str(db_path))
        import sqlite_vec as sv  # noqa: F811
        conn.enable_load_extension(True)
        sv.load(conn)
        conn.enable_load_extension(False)

        hybrid_results = hybrid_fuse_and_filter(
            conn=conn,
            query_vec_bytes=_serialize_f32(query_emb.tolist()),
            query_tokens=query_tokens,
            bm25_obj=bm25_obj,
            bm25_doc_ids=_bm25_doc_ids,
            top_k=top_k,
        )
        conn.close()

        results = [
            (
                r.rrf_score,
                r.semantic_score if r.semantic_score is not None else 0.0,
                r.keyword_score if r.keyword_score is not None else 0.0,
                r.doc_id,
                r.path,
                r.heading,
                r.section,
                r.text,
            )
            for r in hybrid_results
        ]

    # --- Vector-only path (bm25 not loaded, or mode was never "hybrid") — unchanged ---
    elif mode in ("hybrid", "vector"):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(_MODEL_NAME)
        query_emb = model.encode([query_text], show_progress_bar=False, convert_to_numpy=True)[0]

        conn = sqlite3.connect(str(db_path))
        import sqlite_vec as sv  # noqa: F811
        conn.enable_load_extension(True)
        sv.load(conn)
        conn.enable_load_extension(False)

        # Fetch top_k * 3 candidates to allow re-ranking
        candidate_k = top_k * 3
        rows = conn.execute(
            """
            SELECT d.rowid, d.doc_id, d.path, d.heading, d.section, d.text, v.distance
            FROM knowledge_vec v
            JOIN knowledge_docs d ON d.rowid = v.rowid
            WHERE v.embedding MATCH ?
              AND k = ?
            ORDER BY v.distance
            """,
            (_serialize_f32(query_emb.tolist()), candidate_k),
        ).fetchall()
        conn.close()

        results = []
        for rowid, doc_id, path, heading, section, text, dist in rows:
            semantic = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
            keyword = 0.0
            if bm25_raw is not None and rowid < len(bm25_raw):
                keyword = float(bm25_raw[rowid]) / bm25_max
            title_boost, heading_boost, code_boost = _compute_boosts(
                query_tokens, doc_id, heading, text
            )
            final = _hybrid_score(semantic, keyword, title_boost, heading_boost, code_boost)
            results.append((final, semantic, keyword, doc_id, path, heading, section, text))

        # Sort by final score descending, take top_k
        results.sort(key=lambda r: r[0], reverse=True)
        results = results[:top_k]

    else:
        # keyword-only mode: full-scan the docs table, rank by BM25
        conn = sqlite3.connect(str(db_path))
        all_rows = conn.execute(
            "SELECT rowid, doc_id, path, heading, section, text FROM knowledge_docs"
        ).fetchall()
        conn.close()

        results = []
        for rowid, doc_id, path, heading, section, text in all_rows:
            keyword = 0.0
            if bm25_raw is not None and rowid < len(bm25_raw):
                keyword = float(bm25_raw[rowid]) / bm25_max
            title_boost, heading_boost, code_boost = _compute_boosts(
                query_tokens, doc_id, heading, text
            )
            final = _hybrid_score(0.0, keyword, title_boost, heading_boost, code_boost)
            results.append((final, 0.0, keyword, doc_id, path, heading, section, text))

        results.sort(key=lambda r: r[0], reverse=True)
        results = results[:top_k]

    for final, semantic, keyword, doc_id, path, heading, section, text in results:
        snippet = text[:120].replace("\n", " ").replace("\t", " ")
        print(
            f"{doc_id}\t{path}\t{heading}\t{section}\t"
            f"{final:.4f}\t{semantic:.4f}\t{keyword:.4f}\t{snippet}"
        )

    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Semantic knowledge search for ticket and investigation history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build subcommand
    build_p = subparsers.add_parser("build", help="Build local vector index from corpus")
    build_p.add_argument(
        "--corpus-root",
        default=None,
        metavar="PATH",
        help="Repo root to use as corpus root (default: current directory)",
    )
    build_p.add_argument(
        "--db-path",
        default=None,
        metavar="PATH",
        help=f"Output database path (default: {_DEFAULT_DB})",
    )
    build_p.add_argument(
        "--incremental",
        action="store_true",
        default=False,
        help="Only re-embed changed or new files (requires existing index + manifest.json)",
    )

    # query subcommand
    query_p = subparsers.add_parser("query", help="Query the vector index")
    query_p.add_argument("query", metavar="QUERY", help="Natural-language query string")
    query_p.add_argument(
        "--top-k",
        type=int,
        default=5,
        metavar="N",
        help="Number of results to return (default: 5)",
    )
    query_p.add_argument(
        "--db-path",
        default=None,
        metavar="PATH",
        help=f"Database path (default: {_DEFAULT_DB})",
    )
    query_p.add_argument(
        "--mode",
        choices=["hybrid", "vector", "keyword"],
        default="hybrid",
        help="Search mode (default: hybrid; only vector is implemented in this version)",
    )

    return parser


if __name__ == "__main__":
    parser = _build_parser()
    parsed = parser.parse_args()
    if parsed.command == "build":
        if getattr(parsed, "incremental", False):
            sys.exit(cmd_build_incremental(parsed))
        sys.exit(cmd_build(parsed))
    elif parsed.command == "query":
        sys.exit(cmd_query(parsed))
    else:
        parser.print_help()
        sys.exit(1)
