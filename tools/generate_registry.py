#!/usr/bin/env python3
"""
Generate docs/REGISTRY.yaml — a flat index of all tagged docs and closed tickets.

Walks docs/ (excluding archive subdirs) and tickets/done/ to produce a single
YAML list with one entry per file. Ticket entries are joined with stored_artifacts/
by ticket_id to enumerate artifact_files.

Usage:
  python3 tools/generate_registry.py [--root <dir>] [--output <path>]

Exit 0 = success.
Exit 1 = one or more doc files missing frontmatter (CI gate).
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import extract_frontmatter from validate_frontmatter (same package).
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(_TOOLS_DIR))
from validate_frontmatter import extract_frontmatter  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Subdirectories under docs/ to skip entirely (not indexed in the registry).
_SKIP_DOC_SUBDIRS = {"archive", "superpowers", "specs", "parity_ledger", "scenarios", "entity"}

_AUTHORITY_SORT = {"P0": 0, "P1": 1, "P2": 2}

# Regex to extract backtick-quoted tokens from a line.
_BACKTICK_RE = re.compile(r"`([^`]+)`")

# ---------------------------------------------------------------------------
# Body section parsing
# ---------------------------------------------------------------------------


def parse_body_section(body: str, section: str) -> str:
    """Extract the text of '## <section>' up to the next '## ' heading.

    Returns stripped text of the section, or "" if not found.
    """
    pattern = re.compile(
        r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return ""
    return match.group(1).strip()


def parse_related_code_areas(section_text: str) -> list:
    """Extract backtick-quoted tokens from each list item line in section_text."""
    areas = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _BACKTICK_RE.search(line)
        if m:
            areas.append(m.group(1))
    return areas


def parse_h1_title(body: str) -> str:
    """Find the first '# Heading' line in body and return the title text."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped[2:].strip()
    return ""


def _strip_frontmatter(text: str) -> str:
    """Return the body of a markdown file with the frontmatter block removed."""
    pattern = re.compile(r"^---[ \t]*\r?\n.*?(?:\r?\n)?---[ \t]*(\r?\n|$)", re.DOTALL)
    match = pattern.match(text)
    if match:
        return text[match.end():]
    return text


# ---------------------------------------------------------------------------
# Artifact join
# ---------------------------------------------------------------------------


def join_artifact_files(root: Path, ticket_id: str) -> list:
    """Return sorted list of relative paths (from root) for files under
    stored_artifacts/{ticket_id}/*.md. Returns [] if folder absent."""
    artifact_dir = root / "stored_artifacts" / ticket_id
    if not artifact_dir.is_dir():
        return []
    files = sorted(artifact_dir.glob("*.md"))
    return [str(f.relative_to(root)) for f in files]


# ---------------------------------------------------------------------------
# YAML serialisation (stdlib-only, no PyYAML dependency required)
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml

    def _dump_yaml(entries: list, stream, header: str) -> None:
        stream.write(header)
        _yaml.dump(
            entries,
            stream,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    _HAS_PYYAML = True

except ImportError:
    _HAS_PYYAML = False

    def _scalar(value) -> str:
        """Serialise a Python scalar to a YAML scalar string."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        s = str(value)
        # Quote if necessary: empty string, contains special chars, or looks like
        # a YAML special value.
        needs_quote = (
            not s
            or any(c in s for c in ':{}[]|>&*!,#\n\r')
            or s in ("true", "false", "null", "yes", "no", "on", "off")
            or s.startswith(("- ", "? ", "| ", "> "))
        )
        if needs_quote:
            escaped = s.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return s

    def _dump_entry(entry: dict, indent: str = "  ") -> str:
        lines = []
        for i, (k, v) in enumerate(entry.items()):
            prefix = "- " if i == 0 else "  "
            if isinstance(v, list):
                if not v:
                    lines.append(f"{prefix}{k}: []")
                else:
                    lines.append(f"{prefix}{k}:")
                    for item in v:
                        lines.append(f"    - {_scalar(item)}")
            else:
                lines.append(f"{prefix}{k}: {_scalar(v)}")
        return "\n".join(lines)

    def _dump_yaml(entries: list, stream, header: str) -> None:
        stream.write(header)
        parts = [_dump_entry(e) for e in entries]
        stream.write("\n".join(parts))
        stream.write("\n")


# ---------------------------------------------------------------------------
# Doc collection
# ---------------------------------------------------------------------------


def collect_docs(root: Path) -> tuple:
    """Walk root/docs/ recursively, skipping excluded subdirs.

    Returns (entries: list[dict], errors: list[str]).
    Errors are doc files with missing frontmatter.
    """
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return [], []

    entries = []
    errors = []

    for md_file in sorted(docs_dir.rglob("*.md")):
        # Determine relative path parts after docs/
        rel = md_file.relative_to(docs_dir)
        parts = rel.parts
        # Skip if the first sub-directory is in the exclusion set.
        if parts and parts[0] in _SKIP_DOC_SUBDIRS:
            continue

        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError as exc:
            errors.append(f"{md_file.relative_to(root)}: frontmatter parse error: {exc}")
            continue

        if fm is None:
            errors.append(str(md_file.relative_to(root)))
            continue

        body = _strip_frontmatter(text)
        title = fm.get("title") or parse_h1_title(body) or ""

        # Normalise tags: always a list.
        raw_tags = fm.get("tags", [])
        tags = raw_tags if isinstance(raw_tags, list) else []

        entry = {
            "type": "doc",
            "path": str(md_file.relative_to(root)),
            "title": title,
            "status": fm.get("status", ""),
            "layer": fm.get("layer", ""),
            "authority": fm.get("authority", ""),
            "audience": fm.get("audience", ""),
            "tags": tags,
            "last_verified": fm.get("last_verified") or None,
        }
        entries.append(entry)

    return entries, errors


# ---------------------------------------------------------------------------
# Ticket collection
# ---------------------------------------------------------------------------


def collect_tickets(root: Path) -> list:
    """Walk root/tickets/done/*.md (flat).

    Returns list of ticket entry dicts. Missing frontmatter → warning to
    stderr, entry still emitted with defaults (backward compat).
    """
    done_dir = root / "tickets" / "done"
    if not done_dir.is_dir():
        return []

    entries = []

    for md_file in sorted(done_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError as exc:
            print(
                f"WARNING: {md_file.relative_to(root)}: frontmatter parse error: {exc}",
                file=sys.stderr,
            )
            fm = None

        if fm is None:
            print(
                f"WARNING: {md_file.relative_to(root)}: missing frontmatter — emitting with defaults",
                file=sys.stderr,
            )
            fm = {}

        body = _strip_frontmatter(text)

        # Derive ticket_id from frontmatter or filename stem.
        ticket_id = fm.get("ticket_id") or md_file.stem

        # Parse body sections.
        title = parse_body_section(body, "Title")
        tier = parse_body_section(body, "Tier")
        ticket_type = parse_body_section(body, "Type")
        priority = parse_body_section(body, "Priority")
        rca_section = parse_body_section(body, "Related Code Areas")
        related_code_areas = parse_related_code_areas(rca_section)

        # Normalise tags.
        raw_tags = fm.get("tags", [])
        tags = raw_tags if isinstance(raw_tags, list) else []

        date_val = fm.get("date", "")

        artifact_files = join_artifact_files(root, ticket_id)

        entry = {
            "type": "ticket",
            "path": str(md_file.relative_to(root)),
            "ticket_id": ticket_id,
            "title": title,
            "tier": tier,
            "ticket_type": ticket_type,
            "date": date_val,
            "related_code_areas": related_code_areas,
            "artifact_files": artifact_files,
            "tags": tags,
        }
        entries.append(entry)

    return entries


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


def sort_entries(entries: list) -> list:
    """Sort: doc entries first, ticket entries second.

    Within doc: authority P0 → P1 → P2, then path ascending.
    Within ticket: date descending (empty = "0000-00-00"), then path ascending.
    """
    docs = [e for e in entries if e.get("type") == "doc"]
    tickets = [e for e in entries if e.get("type") == "ticket"]

    docs_sorted = sorted(
        docs,
        key=lambda e: (_AUTHORITY_SORT.get(e.get("authority", ""), 99), e.get("path", "")),
    )
    tickets_sorted = sorted(
        tickets,
        key=lambda e: (
            # Negate lexicographic date for descending sort by prefixing with "~" (sorts after digits).
            # Simpler: use a tuple with negation trick — invert via a wrapper.
            _invert_date(e.get("date", "")),
            e.get("path", ""),
        ),
    )
    return docs_sorted + tickets_sorted


def _invert_date(date_str: str) -> str:
    """Return a sort key that inverts date ordering (newest first).

    We replace each digit d with (9-d) so lexicographic ascending = date descending.
    Empty string → "9999-99-99" (sorts last in inverted order, i.e., oldest).
    """
    if not date_str:
        return "9999-99-99"
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in date_str)


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------


def print_summary(entries: list) -> None:
    doc_entries = [e for e in entries if e.get("type") == "doc"]
    ticket_entries = [e for e in entries if e.get("type") == "ticket"]

    print(f"Registry summary: {len(entries)} total entries")
    print(f"  docs:    {len(doc_entries)}")
    print(f"  tickets: {len(ticket_entries)}")

    # By status.
    status_counts: dict = {}
    for e in entries:
        s = e.get("status", "(none)")
        status_counts[s] = status_counts.get(s, 0) + 1
    print("  by status:", ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items())))

    # By layer (docs only).
    layer_counts: dict = {}
    for e in doc_entries:
        l = e.get("layer", "(none)")
        layer_counts[l] = layer_counts.get(l, 0) + 1
    if layer_counts:
        print("  doc layers:", ", ".join(f"{k}={v}" for k, v in sorted(layer_counts.items())))

    # By authority (docs only).
    auth_counts: dict = {}
    for e in doc_entries:
        a = e.get("authority", "(none)")
        auth_counts[a] = auth_counts.get(a, 0) + 1
    if auth_counts:
        print("  doc authority:", ", ".join(f"{k}={v}" for k, v in sorted(auth_counts.items())))


# ---------------------------------------------------------------------------
# YAML output: emit ticket_type as "type" key
# ---------------------------------------------------------------------------


def _normalise_entry_for_output(entry: dict) -> dict:
    """Return a copy of the entry ready for YAML output.

    For ticket entries, the internal key 'ticket_type' (the ticket's bug/feature/etc.
    classification) is emitted as 'ticket_type' in YAML to avoid collision with the
    'type' key that carries the entry kind ('doc' or 'ticket').
    """
    out = {}
    for k, v in entry.items():
        out[k] = v
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_registry(root: Path, output: Path) -> int:
    """Generate docs/REGISTRY.yaml. Returns exit code (0=ok, 1=doc errors)."""
    doc_entries, doc_errors = collect_docs(root)
    ticket_entries = collect_tickets(root)

    all_entries = sort_entries(doc_entries + ticket_entries)

    # Build output entries, renaming ticket_type → type for YAML.
    output_entries = [_normalise_entry_for_output(e) for e in all_entries]

    # Remove None last_verified fields for clean output.
    for e in output_entries:
        if e.get("type") == "doc" and e.get("last_verified") is None:
            e.pop("last_verified", None)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (
        "# docs/REGISTRY.yaml — generated by tools/generate_registry.py\n"
        "# Do not edit manually. Regenerate with: make docs-registry\n"
        f"# Generated: {ts}\n"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        _dump_yaml(output_entries, f, header)

    print(f"Wrote {len(output_entries)} entries to {output}")
    print_summary(all_entries)

    if doc_errors:
        print(f"\nERROR: {len(doc_errors)} doc file(s) missing frontmatter:", file=sys.stderr)
        for err in doc_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate docs/REGISTRY.yaml from frontmatter-tagged docs and tickets."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="docs/REGISTRY.yaml",
        help="Output path for the registry YAML (default: docs/REGISTRY.yaml)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output

    sys.exit(generate_registry(root, output))


if __name__ == "__main__":
    main()
