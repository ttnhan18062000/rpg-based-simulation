#!/usr/bin/env python3
"""Bulk-apply minimal frontmatter to agent-working/tickets/done/ and agent-working/stored_artifacts/.

Run from repo root:
    python3 tools/add_frontmatter_tickets.py                       # dry run: lists what would change
    python3 tools/add_frontmatter_tickets.py --apply --ticket-id X # write, for ticket X only

Every edit is computed in memory first; nothing is written unless --apply is given and the whole
pass succeeded, so a crash can never leave some files rewritten and others not.

Idempotency:
- Ticket files: skip if already starts with '---' AND contains 'status: historical'
  (i.e. already has the correct schema frontmatter). Replace if it starts with '---'
  but has an incomplete/non-conformant frontmatter (e.g. only 'ticket:' / 'phase:' keys).
- Artifact files: same logic — replace non-conformant frontmatter, skip conformant ones.
- All .md files under agent-working/stored_artifacts/ subdirs receive artifact frontmatter
  (validator scans them all; non-standard filenames get artifact_type: misc).
"""

import argparse
import re
import sys
from pathlib import Path
_REPO_ROOT_STR = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT_STR not in sys.path:
    sys.path.append(_REPO_ROOT_STR)
from tools.agent_working_paths import STORED_ARTIFACTS, TICKETS  # noqa: E402

TICKET_DIR = TICKETS / "done"
ARTIFACT_DIR = STORED_ARTIFACTS

# Only these stems get a typed artifact_type; everything else gets artifact_type: misc
ARTIFACT_TYPED_NAMES = {"investigation", "plan", "test_plan"}

LAYER_KEYWORDS = {
    # Higher-specificity layers listed first — engine/guidelines keywords must not
    # be pre-empted by broad matches (e.g. "test" in "testing" would match "tickets").
    "guidelines": ["docsite", "schema", "frontmatter", "registry", "_fm_", "-fm-", "fm_"],
    "engine": [
        # movement is engine-layer locomotion (not a valid LAYER_VALUE by itself)
        "engine", "kernel", "pipeline", "phase", "tick", "loop", "dispatch",
        "scheduler", "governance", "packetiz", "persist", "resolution",
        "worker", "thread", "singleton", "teardown", "conftest", "content", "infra",
        "broker", "movement", "pathfind", "navigation", "motion", "travel",
    ],
    "combat": ["combat", "battle", "fight", "weapon", "durability", "durab", "damage"],
    "economy": ["resource", "economy", "economic", "crafting", "craft", "harvest", "trade", "market", "item", "gold", "cost", "econ"],
    "strategy": ["strategy", "strat", "cognition", "cognitive", "cognit", "goal", "planning", "decision", "intel", "attention", "lead"],
    "world": ["world", "region", "ecology", "ecosystem", "biome", "terrain", "topology", "climate", "calamit"],
    "core": ["entity", "aspect", "attribute", "stat", "health", "character"],
    "observability": ["observ", "monitor", "metric", "telemetry", "trace", "debug", "profil", "replay"],
    "performance": ["performance", "perf", "optimiz", "latency", "throughput", "benchmark", "speed"],
    "testing": ["fixture", "mock", "assert", "coverage"],
    "simulation": ["simulation", "determinism"],
    "ai": ["social", "narrative", "reputation", "faction", "npc", "workflow", "skill"],
    "architecture": ["adr", "architect"],
}

# Tokens to ignore when building tags from ticket ID parts
_SKIP_TOKENS = {"tck"}


def infer_layer(name: str) -> str:
    """Infer layer from ticket ID or folder name using keyword matching."""
    stem = name.lower().replace("-", "_").replace(".", "_")
    for layer, keywords in LAYER_KEYWORDS.items():
        if any(kw in stem for kw in keywords):
            return layer
    return "misc"


def extract_date_from_ticket_id(stem: str) -> str:
    """Parse YYYYMMDD from TCK-YYYYMMDD-* pattern. Returns 'unknown' for non-TCK."""
    m = re.match(r"TCK-(\d{4})(\d{2})(\d{2})-", stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "unknown"


def extract_tags_from_ticket_id(stem: str) -> list[str]:
    """Extract scope keywords from ticket ID.

    TCK-20260606-DOCSITE-FM-TICKETS -> ["docsite", "fm", "tickets"]
    METRICS-01 -> ["metrics"]
    """
    parts = stem.replace(".", "-").split("-")
    tags = []
    for part in parts:
        lp = part.lower()
        if lp in _SKIP_TOKENS:
            continue
        # Skip 8-digit date segment and pure numeric segments
        if re.match(r"^\d+$", lp):
            continue
        if len(lp) < 2:
            continue
        tags.append(lp)
    return tags


_FM_CLOSE = re.compile(r"^---[ \t]*$", re.MULTILINE)


def has_conformant_frontmatter(content: str, required_key: str) -> bool:
    """Return True only if the file already has a valid schema frontmatter block.

    A frontmatter block is considered conformant when it:
    - starts with '---'
    - contains the given required_key (e.g. 'status: historical' or 'artifact_type:')
    This guards against the partial-frontmatter pattern (ticket: / phase: only) written
    by an earlier tooling pass that used non-schema keys.
    """
    if not content.startswith("---"):
        return False
    # Find closing ---
    m = _FM_CLOSE.search(content, 3)
    if not m:
        return False
    block = content[3:m.start()]
    return required_key in block


def strip_frontmatter(content: str) -> str:
    """Remove the leading frontmatter block (--- ... ---\\n) from content."""
    if not content.startswith("---"):
        return content
    m = _FM_CLOSE.search(content, 3)
    if not m:
        return content
    # skip past the closing --- and any single trailing newline
    end = m.end()
    if end < len(content) and content[end] == "\n":
        end += 1
    return content[end:]


def build_ticket_frontmatter(stem: str) -> str:
    layer = infer_layer(stem)
    date = extract_date_from_ticket_id(stem)
    tags = extract_tags_from_ticket_id(stem)
    tag_str = "[" + ", ".join(tags) + "]" if tags else "[]"
    lines = [
        "---",
        "status: historical",
        f"layer: {layer}",
        "authority: P1",
        "audience: agent",
        f"ticket_id: {stem}",
        "phase: done",
        f"date: {date}",
        f"tags: {tag_str}",
        "---",
    ]
    return "\n".join(lines) + "\n"


def build_artifact_frontmatter(ticket_id: str, artifact_type: str | None) -> str:
    """Build frontmatter for a stored artifact file.

    If artifact_type is one of the schema enum values (investigation, plan, test_plan),
    emit full artifact frontmatter.  For non-standard filenames (legacy docs, walkthroughs,
    task specs, etc.) set content_type: doc so the validator routes them through the doc
    schema (which has no artifact_type requirement).
    """
    layer = infer_layer(ticket_id)
    tags = extract_tags_from_ticket_id(ticket_id)
    tag_str = "[" + ", ".join(tags) + "]" if tags else "[]"

    if artifact_type is not None:
        # Standard typed artifact — full artifact schema
        lines = [
            "---",
            "status: historical",
            f"layer: {layer}",
            "authority: P2",
            "audience: agent",
            f"ticket_id: {ticket_id}",
            f"artifact_type: {artifact_type}",
            f"tags: {tag_str}",
            "---",
        ]
    else:
        # Non-standard legacy file — validate as doc (no artifact_type field needed)
        lines = [
            "---",
            "content_type: doc",
            "status: historical",
            f"layer: {layer}",
            "authority: P2",
            "audience: agent",
            f"tags: {tag_str}",
            "---",
        ]
    return "\n".join(lines) + "\n"


def compute_ticket_file(path: Path) -> str | None:
    """Return the new content for a ticket file, or None if it is already conformant. Writes nothing."""
    content = path.read_text(encoding="utf-8")
    if has_conformant_frontmatter(content, "status: historical"):
        # Also rewrite if an invalid layer value is present (e.g. 'movement' was
        # written in a prior pass before LAYER_KEYWORDS was corrected)
        if "layer: movement" not in content:
            return None
    stem = path.stem
    body = strip_frontmatter(content) if content.startswith("---") else content
    frontmatter = build_ticket_frontmatter(stem)
    return frontmatter + "\n" + body


def compute_artifact_file(path: Path, ticket_id: str) -> str | None:
    """Return the new content for an artifact file, or None if it is already conformant.

    All .md files under agent-working/stored_artifacts/ receive frontmatter.
    Files whose stem is in ARTIFACT_TYPED_NAMES get the full artifact schema with
    a typed artifact_type field.  All other files (legacy walkthroughs, task specs,
    etc.) get content_type: doc frontmatter so the validator routes them correctly.
    Writes nothing.
    """
    content = path.read_text(encoding="utf-8")
    stem = path.stem
    is_typed = stem in ARTIFACT_TYPED_NAMES

    # Conformance check: skip only if a proper schema frontmatter is already present.
    # Typed artifacts need 'artifact_type:'; non-typed need 'content_type: doc'.
    conformance_key = "artifact_type:" if is_typed else "content_type: doc"
    if has_conformant_frontmatter(content, conformance_key):
        # Rewrite if an invalid layer value is present
        if "layer: movement" not in content:
            return None

    artifact_type = stem if is_typed else None
    body = strip_frontmatter(content) if content.startswith("---") else content
    frontmatter = build_artifact_frontmatter(ticket_id, artifact_type)
    return frontmatter + "\n" + body


def process_ticket_file(path: Path) -> str:
    """Prepend ticket frontmatter to path. Returns 'modified' or 'skipped'."""
    new_content = compute_ticket_file(path)
    if new_content is None:
        return "skipped"
    path.write_text(new_content, encoding="utf-8")
    return "modified"


def process_artifact_file(path: Path, ticket_id: str) -> str:
    """Apply artifact frontmatter to path. Returns 'modified' or 'skipped'."""
    new_content = compute_artifact_file(path, ticket_id)
    if new_content is None:
        return "skipped"
    path.write_text(new_content, encoding="utf-8")
    return "modified"


def plan_edits(ticket_ids: frozenset[str] | None = None) -> tuple[list[tuple[Path, str, str]], dict[str, int]]:
    """Compute every edit in memory. Returns ([(path, kind, new_content)], counts); writes nothing.

    Any exception propagates before the caller has written a single file. `ticket_ids`, when given,
    restricts both walks to those tickets (a done ticket's stem, an artifact folder's name).
    """
    edits: list[tuple[Path, str, str]] = []
    counts = {"ticket_skipped": 0, "artifact_skipped": 0, "ticket_misc": 0, "artifact_misc": 0}

    if not TICKET_DIR.exists():
        print(f"WARNING: {TICKET_DIR} does not exist, skipping tickets", file=sys.stderr)
    else:
        for md_file in sorted(TICKET_DIR.rglob("*.md")):
            if ticket_ids is not None and md_file.stem not in ticket_ids:
                continue
            new_content = compute_ticket_file(md_file)
            if new_content is None:
                counts["ticket_skipped"] += 1
                continue
            edits.append((md_file, "ticket", new_content))
            if infer_layer(md_file.stem) == "misc":
                counts["ticket_misc"] += 1

    if not ARTIFACT_DIR.exists():
        print(f"WARNING: {ARTIFACT_DIR} does not exist, skipping artifacts", file=sys.stderr)
    else:
        for subdir in sorted(ARTIFACT_DIR.iterdir()):
            if not subdir.is_dir():
                continue
            if ticket_ids is not None and subdir.name not in ticket_ids:
                continue
            for md_file in sorted(subdir.rglob("*.md")):
                new_content = compute_artifact_file(md_file, subdir.name)
                if new_content is None:
                    counts["artifact_skipped"] += 1
                    continue
                edits.append((md_file, "artifact", new_content))
                if infer_layer(subdir.name) == "misc":
                    counts["artifact_misc"] += 1
    return edits, counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="write the edits (default: dry run, print what would change and write nothing)")
    parser.add_argument("--ticket-id", action="append", dest="ticket_ids", metavar="ID",
                        help="restrict to this ticket (repeatable); without it every ticket and artifact is walked")
    args = parser.parse_args(argv)

    edits, counts = plan_edits(frozenset(args.ticket_ids) if args.ticket_ids else None)

    ticket_modified = sum(1 for _, kind, _ in edits if kind == "ticket")
    artifact_modified = sum(1 for _, kind, _ in edits if kind == "artifact")

    if not args.apply:
        for path, _kind, _content in edits:
            print(f"would modify: {path}")
        print(f"DRY RUN: {len(edits)} files would be modified; nothing written (pass --apply to write)")
    else:
        for path, _kind, content in edits:
            path.write_text(content, encoding="utf-8")

    print(f"Done: {ticket_modified} tickets modified, {counts['ticket_skipped']} tickets skipped")
    print(f"Done: {artifact_modified} artifacts modified, {counts['artifact_skipped']} artifacts skipped")
    print(f"Tickets with layer=misc: {counts['ticket_misc']}")
    print(f"Artifacts with layer=misc: {counts['artifact_misc']}")


if __name__ == "__main__":
    main()
