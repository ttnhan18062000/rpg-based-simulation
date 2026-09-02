#!/usr/bin/env python3
"""
Generate docs/brainstorm/idea_index.json — a per-idea cross-document index.

Cross-references each of the RPG design ideas across the four brainstorm
documents that discuss them by number, plus the owning M1-M9 milestone epic:

- rpg_feature_atlas.html      -> id="idea-N" (all ideas, count derived live
                                  from the atlas itself, not hardcoded)
- rpg_expected_schemas.html   -> id="schema-N" (only ideas introducing new
                                  durable state; null otherwise)
- design_merit_scorecard.html -> id="score-N" (ideas 1-65 only; 66/67/68 were
                                  all added after the original scoring pass
                                  and are deliberately left unscored, so null
                                  -- see that document's own grounding note)
- rpg_simulation_wiring_map.html -> no reliable per-idea anchor exists in this
                                  document's current structure (an idea can
                                  span multiple unrelated rows); recorded as a
                                  raw mention count instead of a fake anchor.
- Milestone ownership is parsed directly from each M1-M9 epic doc's own
  **Source:** line (docs/plans/rpg_design_roadmap/rpg_mN_*.md), not
  hardcoded — except idea 66, which predates that convention and is recorded
  per the roadmap's own explicit "scoped under M8" statement. Ideas 67/68
  (added 2026-09-02) are candidates not yet folded into any milestone's
  committed **Source:** line, so their milestone is correctly null until
  that happens, not a bug.

Every non-null anchor is verified to actually exist in its source file before
being written — this script raises rather than emitting a dangling reference.

Usage:
  python3 tools/generate_brainstorm_idea_index.py [--root <dir>] [--output <path>]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# The idea count is derived live from the atlas's own card-sections-data in
# build_index() below -- no longer hardcoded, since the atlas grows over time
# (66 -> 68 on 2026-09-02) and a stale constant here would silently truncate
# the index.

# Idea 66 predates the **Source:** line convention used by ideas 1-65
# (see rpg_design_roadmap.md's Sequencing rules: "scoped under M8" while
# gating M2's ideas 35/48) -- recorded explicitly rather than parsed. This is
# keyed to idea 66 specifically, not "whichever idea number is currently
# last" -- do not repurpose this constant when a later idea 69+ is added.
IDEA_66_MILESTONE = "M8"

EPIC_FILES = [f"rpg_m{n}_" for n in range(1, 10)]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _anchor_ids(text: str, prefix: str) -> set[int]:
    """Return the set of idea numbers with id="{prefix}-N" present in text."""
    return {int(m) for m in re.findall(rf'id="{re.escape(prefix)}-(\d+)"', text)}


def _atlas_idea_ids(atlas_text: str) -> set[int]:
    """The Atlas's id="idea-N" anchors are generated client-side by renderCard's
    regex against each card's title field (^(\\d+)\\.) -- they do not exist as
    literal text in the static HTML source. Derive the same set directly from
    the CARD_SECTIONS JSON data block (TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT),
    replicating that exact regex rather than grepping for a literal id attribute
    that was never written to disk.
    """
    m = re.search(
        r'<script type="application/json" id="card-sections-data">\n(.*?)\n</script>',
        atlas_text,
        re.DOTALL,
    )
    if not m:
        raise SystemExit('ERROR: could not find card-sections-data script block in atlas')
    card_sections = json.loads(m.group(1))
    ids = set()
    for cards in card_sections.values():
        for c in cards:
            title_match = re.match(r"^(\d+)\.", c["title"])
            if title_match:
                ids.add(int(title_match.group(1)))
    return ids


def _mention_counts(text: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for m in re.finditer(r"[Ii]dea\s+(\d+)\b", text):
        n = int(m.group(1))
        counts[n] = counts.get(n, 0) + 1
    return counts


def _milestone_map(roadmap_dir: Path) -> dict[int, str]:
    """Parse each M1-M9 epic doc's **Source:** idea-number line."""
    result: dict[int, str] = {}
    for epic_path in sorted(roadmap_dir.glob("rpg_m*_*.md")):
        m = re.match(r"rpg_m(\d+)_", epic_path.name)
        if not m:
            continue
        milestone = f"M{m.group(1)}"
        text = _read(epic_path)
        # **Source:** line may wrap onto the following raw line(s) before the
        # sentence-ending period; join the Source paragraph's contiguous
        # comma/hyphen-number text up to the first ``.`` that ends a number list.
        src_match = re.search(
            r"\*\*Source:\*\*\s*`docs/brainstorm/rpg_feature_atlas\.html`[^\n]*"
            r"(?:\n[^\n*][^\n]*)*",
            text,
        )
        if not src_match:
            continue  # M7/M8/M9: cite process docs, not idea numbers
        src_text = src_match.group(0)
        # Extract "Design Ideas ..." number list, handling ranges like "15-19".
        # Terminator is either "." (most epics) or ")" (M1's "Rev 60+ (Design
        # Ideas 1, 3, ..., 42), cross-checked against ..." phrasing).
        ideas_match = re.search(r"Design Ideas\s+([\d,\s\-]+)[.)]", src_text)
        if not ideas_match:
            continue
        for token in ideas_match.group(1).split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                lo, hi = token.split("-")
                for n in range(int(lo), int(hi) + 1):
                    result[n] = milestone
            else:
                result[int(token)] = milestone
    return result


def build_index(brainstorm_dir: Path, roadmap_dir: Path) -> dict:
    atlas_text = _read(brainstorm_dir / "rpg_feature_atlas.html")
    schema_text = _read(brainstorm_dir / "rpg_expected_schemas.html")
    scorecard_text = _read(brainstorm_dir / "design_merit_scorecard.html")
    wiring_text = _read(brainstorm_dir / "rpg_simulation_wiring_map.html")

    atlas_ids = _atlas_idea_ids(atlas_text)
    schema_ids = _anchor_ids(schema_text, "schema")
    scorecard_ids = _anchor_ids(scorecard_text, "score")
    wiring_mentions = _mention_counts(wiring_text)
    milestones = _milestone_map(roadmap_dir)

    total_ideas = max(atlas_ids) if atlas_ids else 0
    missing_atlas = set(range(1, total_ideas + 1)) - atlas_ids
    if missing_atlas:
        raise SystemExit(f"ERROR: atlas missing id=\"idea-N\" for: {sorted(missing_atlas)}")

    ideas = []
    for n in range(1, total_ideas + 1):
        entry = {
            "idea": n,
            "atlas_anchor": f"rpg_feature_atlas.html#idea-{n}",
            "schema_anchor": f"rpg_expected_schemas.html#schema-{n}" if n in schema_ids else None,
            "scorecard_anchor": f"design_merit_scorecard.html#score-{n}" if n in scorecard_ids else None,
            "wiring_map_mentions": wiring_mentions.get(n, 0),
            "milestone": IDEA_66_MILESTONE if n == 66 else milestones.get(n),
        }
        ideas.append(entry)

    return {
        "_meta": {
            "description": (
                "Per-idea cross-document index across the RPG brainstorm corpus. "
                "atlas_anchor is always present (count derived live from the atlas "
                "itself); schema_anchor is present only for ideas with a "
                "durable-state schema section; scorecard_anchor is present for "
                "ideas 1-65 only (66/67/68 were all added after the original "
                "scoring pass and are deliberately left unscored); "
                "wiring_map_mentions is a raw text-mention count, not a clickable "
                "anchor, since that document has no reliable 1:1 per-idea anchor "
                "structure (see TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX's "
                "investigation.md)."
            ),
            "regenerate_with": "make brainstorm-idea-index",
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "ideas": ideas,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output", type=Path, default=Path("docs/brainstorm/idea_index.json")
    )
    args = parser.parse_args()

    brainstorm_dir = args.root / "docs" / "brainstorm"
    roadmap_dir = args.root / "docs" / "plans" / "rpg_design_roadmap"

    data = build_index(brainstorm_dir, roadmap_dir)

    m_counts: dict[str, int] = {}
    for entry in data["ideas"]:
        if entry["milestone"]:
            m_counts[entry["milestone"]] = m_counts.get(entry["milestone"], 0) + 1
    print(f"Indexed {len(data['ideas'])} ideas. Milestone counts: {m_counts}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
