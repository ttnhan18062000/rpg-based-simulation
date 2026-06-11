#!/usr/bin/env python3
"""Bulk-apply minimal frontmatter to tickets/done/ and stored_artifacts/.

Run from repo root:
    python3 tools/add_frontmatter_tickets.py

Idempotency:
- Ticket files: skip if already starts with '---' AND contains 'status: historical'
  (i.e. already has the correct schema frontmatter). Replace if it starts with '---'
  but has an incomplete/non-conformant frontmatter (e.g. only 'ticket:' / 'phase:' keys).
- Artifact files: same logic — replace non-conformant frontmatter, skip conformant ones.
- All .md files under stored_artifacts/ subdirs receive artifact frontmatter
  (validator scans them all; non-standard filenames get artifact_type: misc).
"""

import re
import sys
from pathlib import Path

TICKET_DIR = Path("tickets/done")
ARTIFACT_DIR = Path("stored_artifacts")

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


def process_ticket_file(path: Path) -> str:
    """Prepend ticket frontmatter to path. Returns 'modified' or 'skipped'."""
    content = path.read_text(encoding="utf-8")
    if has_conformant_frontmatter(content, "status: historical"):
        # Also rewrite if an invalid layer value is present (e.g. 'movement' was
        # written in a prior pass before LAYER_KEYWORDS was corrected)
        if "layer: movement" not in content:
            return "skipped"
    stem = path.stem
    body = strip_frontmatter(content) if content.startswith("---") else content
    frontmatter = build_ticket_frontmatter(stem)
    path.write_text(frontmatter + "\n" + body, encoding="utf-8")
    return "modified"


def process_artifact_file(path: Path, ticket_id: str) -> str:
    """Apply artifact frontmatter to path. Returns 'modified' or 'skipped'.

    All .md files under stored_artifacts/ receive frontmatter.
    Files whose stem is in ARTIFACT_TYPED_NAMES get the full artifact schema with
    a typed artifact_type field.  All other files (legacy walkthroughs, task specs,
    etc.) get content_type: doc frontmatter so the validator routes them correctly.
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
            return "skipped"

    artifact_type = stem if is_typed else None
    body = strip_frontmatter(content) if content.startswith("---") else content
    frontmatter = build_artifact_frontmatter(ticket_id, artifact_type)
    path.write_text(frontmatter + "\n" + body, encoding="utf-8")
    return "modified"


def main() -> None:
    ticket_modified = 0
    ticket_skipped = 0
    ticket_misc = 0

    artifact_modified = 0
    artifact_skipped = 0
    artifact_misc = 0

    if not TICKET_DIR.exists():
        print(f"WARNING: {TICKET_DIR} does not exist, skipping tickets", file=sys.stderr)
    else:
        for md_file in sorted(TICKET_DIR.rglob("*.md")):
            result = process_ticket_file(md_file)
            layer = infer_layer(md_file.stem)
            if result == "modified":
                ticket_modified += 1
                if layer == "misc":
                    ticket_misc += 1
            else:
                ticket_skipped += 1

    if not ARTIFACT_DIR.exists():
        print(f"WARNING: {ARTIFACT_DIR} does not exist, skipping artifacts", file=sys.stderr)
    else:
        for subdir in sorted(ARTIFACT_DIR.iterdir()):
            if not subdir.is_dir():
                continue
            ticket_id = subdir.name
            for md_file in sorted(subdir.rglob("*.md")):
                result = process_artifact_file(md_file, ticket_id)
                if result == "modified":
                    artifact_modified += 1
                    if infer_layer(ticket_id) == "misc":
                        artifact_misc += 1
                else:
                    artifact_skipped += 1

    print(f"Done: {ticket_modified} tickets modified, {ticket_skipped} tickets skipped")
    print(f"Done: {artifact_modified} artifacts modified, {artifact_skipped} artifacts skipped")
    print(f"Tickets with layer=misc: {ticket_misc}")
    print(f"Artifacts with layer=misc: {artifact_misc}")


if __name__ == "__main__":
    main()
