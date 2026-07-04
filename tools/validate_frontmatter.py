#!/usr/bin/env python3
"""
Validate YAML frontmatter in markdown files against the project schema.

Supports four content types: doc, ticket, artifact, archive.
Content type is inferred from file path unless overridden via --content-type
or an explicit `content_type` field in the frontmatter block.

Usage:
  python3 tools/validate_frontmatter.py <path>
  python3 tools/validate_frontmatter.py <path> --content-type {doc,ticket,artifact,archive}

Exit 0 on success, 1 on any schema violation.
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Enum constants — single source of truth for all valid field values.
# ---------------------------------------------------------------------------

STATUS_VALUES = {"authoritative", "active", "historical", "archive"}
LAYER_VALUES = {
    "mechanics", "engine", "testing", "simulation", "ai", "architecture",
    "core", "ticket", "artifact", "guidelines", "observability", "performance",
    "combat", "compliance", "strategy", "systems", "economy", "world", "misc",
}
AUTHORITY_VALUES = {"P0", "P1", "P2"}
AUDIENCE_VALUES = {"developer", "agent", "designer", "historical"}
PHASE_VALUES = {"open", "inprogress", "blocked", "done"}
ARTIFACT_TYPE_VALUES = {"investigation", "plan", "test_plan"}

# Tag taxonomy — see docs/guidelines/tag_taxonomy.md.
# Enforcement is forward-only: only tickets/artifacts whose ticket_id embeds a date on or
# after this cutoff are checked, per the "no backfill of history" decision (TCK-20260704-TAG-TAXONOMY).
TAG_TAXONOMY_EFFECTIVE_DATE = "20260704"

# Duplicates the dedicated `## Priority` ticket-body field — never valid as a tag, at any date.
FORBIDDEN_PRIORITY_TAGS = {"p0", "p1", "p2"}

# Confirmed synonyms the general format rule (below) cannot derive mechanically, because the
# non-canonical spelling has no separator character to normalize (run-together compounds and
# abbreviations). Keep this small and evidence-based — do not use it to pre-enumerate subsystem
# tags; see docs/guidelines/tag_taxonomy.md's anti-drift note.
TAG_SYNONYM_MAP = {
    "obs": "observability",
    "cog": "cognition",
    "sim": "simulation",
    "worldmodules": "world-modules",
    "selfmodel": "self-model",
    "datamodel": "data-model",
    "worldspec": "world-spec",
}

_PHASE_TAG_PATTERN = re.compile(r"^phase(\d+)$")
_TICKET_ID_DATE_PATTERN = re.compile(r"^TCK-(\d{8})-")

# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

_FM_PATTERN = re.compile(r"^---[ \t]*\r?\n(.*?)(?:\r?\n)?---[ \t]*(\r?\n|$)", re.DOTALL)
_LIST_VALUE_PATTERN = re.compile(r"^\[(.*)?\]$")


def extract_frontmatter(text: str) -> dict | None:
    """Return parsed frontmatter dict, None if absent, raise ValueError on bad YAML."""
    match = _FM_PATTERN.match(text)
    if not match:
        return None

    block = match.group(1)
    result = {}
    for line in block.splitlines():
        # Skip blank lines and YAML comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Unparseable frontmatter line: {line!r}")
        key, _, raw_value = line.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if not key:
            raise ValueError(f"Empty key in frontmatter line: {line!r}")

        # Inline list: key: [a, b, c]
        list_match = _LIST_VALUE_PATTERN.match(raw_value)
        if list_match:
            inner = list_match.group(1).strip()
            if inner:
                result[key] = [item.strip().strip("'\"") for item in inner.split(",")]
            else:
                result[key] = []
        elif raw_value.startswith("[") and not raw_value.endswith("]"):
            raise ValueError(f"Unclosed list in frontmatter key '{key}'")
        else:
            # Strip surrounding quotes if present
            if (raw_value.startswith('"') and raw_value.endswith('"')) or (
                raw_value.startswith("'") and raw_value.endswith("'")
            ):
                raw_value = raw_value[1:-1]
            result[key] = raw_value

    return result


# ---------------------------------------------------------------------------
# Content type detection
# ---------------------------------------------------------------------------

def detect_content_type(path: Path) -> str:
    """Infer content type from file path."""
    parts = path.parts
    if "tickets" in parts:
        return "ticket"
    if "stored_artifacts" in parts:
        return "artifact"
    # docs/archive/, docs/superpowers/, docs/specs/ → archive
    if "docs" in parts:
        idx = list(parts).index("docs")
        sub = parts[idx + 1] if idx + 1 < len(parts) else None
        if sub in ("archive", "superpowers", "specs"):
            return "archive"
        return "doc"
    return "doc"


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def _check_enum(filepath: str, fm: dict, field: str, valid: set) -> list[str]:
    val = fm.get(field)
    if val is not None and val not in valid:
        return [f"{filepath}: {field}: invalid value {val!r} (valid: {sorted(valid)})"]
    return []


def _ticket_id_effective_date(ticket_id) -> str | None:
    """Extract the YYYYMMDD date embedded in a TCK-YYYYMMDD-... ticket_id, or None if unparseable."""
    if not isinstance(ticket_id, str):
        return None
    m = _TICKET_ID_DATE_PATTERN.match(ticket_id)
    return m.group(1) if m else None


def _check_tags(filepath: str, fm: dict) -> list[str]:
    tags = fm.get("tags")
    if not tags:
        return []

    embedded_date = _ticket_id_effective_date(fm.get("ticket_id"))
    if embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE:
        # Predates the taxonomy (or ticket_id unparseable) — exempt, per the explicit
        # no-backfill decision. Every other frontmatter check still applies as normal.
        return []

    errors = []
    for tag in tags:
        lower = tag.lower()
        if lower in FORBIDDEN_PRIORITY_TAGS:
            errors.append(
                f"{filepath}: tags: {tag!r} duplicates the dedicated Priority field — remove it"
            )
            continue
        if tag != lower or "_" in tag:
            errors.append(
                f"{filepath}: tags: {tag!r} is not canonical form "
                f"(use {lower.replace('_', '-')!r})"
            )
            continue
        phase_match = _PHASE_TAG_PATTERN.match(tag)
        if phase_match:
            errors.append(
                f"{filepath}: tags: {tag!r} is not canonical form "
                f"(use {'phase-' + phase_match.group(1)!r})"
            )
            continue
        if tag in TAG_SYNONYM_MAP:
            errors.append(
                f"{filepath}: tags: {tag!r} is a non-canonical synonym "
                f"(use {TAG_SYNONYM_MAP[tag]!r})"
            )
    return errors


def _validate_doc(filepath: str, fm: dict) -> list[str]:
    errors = []
    for field in ("status", "layer", "authority", "audience"):
        if field not in fm:
            errors.append(f"{filepath}: {field}: missing required field")
    errors += _check_enum(filepath, fm, "status", STATUS_VALUES)
    errors += _check_enum(filepath, fm, "layer", LAYER_VALUES)
    errors += _check_enum(filepath, fm, "authority", AUTHORITY_VALUES)
    errors += _check_enum(filepath, fm, "audience", AUDIENCE_VALUES)
    if fm.get("status") == "authoritative" and "last_verified" not in fm:
        errors.append(
            f"{filepath}: last_verified: required when status is 'authoritative'"
        )
    return errors


def _validate_ticket(filepath: str, fm: dict) -> list[str]:
    errors = []
    for field in ("status", "layer", "authority", "audience", "ticket_id", "phase", "date"):
        if field not in fm:
            errors.append(f"{filepath}: {field}: missing required field")
    errors += _check_enum(filepath, fm, "status", STATUS_VALUES)
    errors += _check_enum(filepath, fm, "layer", LAYER_VALUES)
    errors += _check_enum(filepath, fm, "authority", AUTHORITY_VALUES)
    errors += _check_enum(filepath, fm, "audience", AUDIENCE_VALUES)
    errors += _check_enum(filepath, fm, "phase", PHASE_VALUES)
    errors += _check_tags(filepath, fm)
    return errors


def _validate_artifact(filepath: str, fm: dict) -> list[str]:
    errors = []
    for field in ("status", "layer", "authority", "audience", "ticket_id", "artifact_type"):
        if field not in fm:
            errors.append(f"{filepath}: {field}: missing required field")
    errors += _check_enum(filepath, fm, "status", STATUS_VALUES)
    errors += _check_enum(filepath, fm, "layer", LAYER_VALUES)
    errors += _check_enum(filepath, fm, "authority", AUTHORITY_VALUES)
    errors += _check_enum(filepath, fm, "audience", AUDIENCE_VALUES)
    errors += _check_enum(filepath, fm, "artifact_type", ARTIFACT_TYPE_VALUES)
    errors += _check_tags(filepath, fm)
    return errors


def _validate_archive(filepath: str, fm: dict) -> list[str]:
    errors = []
    for field in ("status", "layer", "original_date"):
        if field not in fm:
            errors.append(f"{filepath}: {field}: missing required field")
    if "status" in fm and fm["status"] != "archive":
        errors.append(
            f"{filepath}: status: archive files must have status 'archive', got {fm['status']!r}"
        )
    errors += _check_enum(filepath, fm, "layer", LAYER_VALUES)
    return errors


_VALIDATORS = {
    "doc": _validate_doc,
    "ticket": _validate_ticket,
    "artifact": _validate_artifact,
    "archive": _validate_archive,
}


def validate_file(path: Path, content_type_override: str | None = None) -> list[str]:
    """Return list of error strings for the given file (empty = pass)."""
    filepath = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{filepath}: cannot read file: {exc}"]

    try:
        fm = extract_frontmatter(text)
    except ValueError as exc:
        return [f"{filepath}: frontmatter: {exc}"]

    if fm is None:
        return [f"{filepath}: frontmatter: missing frontmatter block"]

    content_type = (
        content_type_override
        or fm.get("content_type")
        or detect_content_type(path)
    )

    validator = _VALIDATORS.get(content_type)
    if validator is None:
        return [f"{filepath}: content_type: unrecognised value {content_type!r}"]

    return validator(filepath, fm)


def validate_directory(
    path: Path, content_type_override: str | None = None
) -> dict[Path, list[str]]:
    """Recursively validate all .md files under path. Returns path→errors map."""
    results = {}
    for md_file in sorted(path.rglob("*.md")):
        errors = validate_file(md_file, content_type_override)
        results[md_file] = errors
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate YAML frontmatter in markdown files."
    )
    parser.add_argument("path", help="File or directory to validate")
    parser.add_argument(
        "--content-type",
        choices=["doc", "ticket", "artifact", "archive"],
        default=None,
        help="Override content type inference for all files",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    override = args.content_type
    all_errors: list[str] = []

    if target.is_dir():
        results = validate_directory(target, override)
        file_count = len(results)
        for errors in results.values():
            all_errors.extend(errors)
    else:
        errors = validate_file(target, override)
        all_errors.extend(errors)
        file_count = 1

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        print(
            f"FAIL: {len(all_errors)} violation(s) in {file_count} file(s) checked",
            file=sys.stdout,
        )
        sys.exit(1)

    print(f"OK: {file_count} file(s) checked — no violations")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: unexpected failure: {exc}", file=sys.stderr)
        sys.exit(1)
