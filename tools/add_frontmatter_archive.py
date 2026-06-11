#!/usr/bin/env python3
"""Bulk-apply minimal frontmatter to docs/archive/, docs/superpowers/specs/, docs/specs/."""

import re
import sys
from pathlib import Path

TARGET_DIRS = [
    Path("docs/archive"),
    Path("docs/superpowers/specs"),
    Path("docs/specs"),
]

LAYER_KEYWORDS = {
    "combat": ["combat", "battle", "fight", "weapon", "durability", "damage"],
    "movement": ["movement", "pathfind", "navigation", "motion", "travel"],
    "economy": ["resource", "economy", "economic", "crafting", "harvest", "trade", "market", "item", "gold", "cost"],
    "strategy": ["strategy", "strat", "cognition", "cognitive", "goal", "planning", "decision", "intel", "attention"],
    "world": ["world", "region", "ecology", "ecosystem", "biome", "terrain", "zone", "map", "topology", "climate", "calamit"],
    "core": ["entity", "aspect", "attribute", "stat", "health", "class", "character"],
    "observability": ["observ", "monitor", "metric", "log", "telemetry", "trace", "debug", "profil"],
    "performance": ["performance", "perf", "optimiz", "latency", "throughput", "benchmark", "speed"],
    "testing": ["test", "coverage", "fixture", "mock", "assert"],
    "engine": ["engine", "kernel", "pipeline", "phase", "tick", "loop", "dispatch", "scheduler", "governance"],
    "simulation": ["simulation", "sim", "run", "replay", "determinism"],
}

def infer_layer(filename: str) -> str:
    stem = filename.lower().replace("-", "_").replace(".", "_")
    for layer, keywords in LAYER_KEYWORDS.items():
        if any(kw in stem for kw in keywords):
            return layer
    return "misc"

def extract_date(filename: str) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else "unknown"

def has_frontmatter(content: str) -> bool:
    return content.startswith("---")

def build_frontmatter(filename: str) -> str:
    layer = infer_layer(filename)
    original_date = extract_date(filename)
    lines = [
        "---",
        "status: archive",
        "authority: P2",
        "audience: historical",
        f"layer: {layer}",
    ]
    if original_date != "unknown":
        lines.append(f"original_date: {original_date}")
    else:
        lines.append("original_date: unknown")
    lines.append("---")
    return "\n".join(lines) + "\n"

def process_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    if has_frontmatter(content):
        return "skipped"
    frontmatter = build_frontmatter(path.name)
    path.write_text(frontmatter + "\n" + content, encoding="utf-8")
    return "modified"

def main():
    modified = 0
    skipped = 0
    misc_count = 0

    for target_dir in TARGET_DIRS:
        if not target_dir.exists():
            print(f"WARNING: {target_dir} does not exist, skipping")
            continue
        for md_file in sorted(target_dir.rglob("*.md")):
            result = process_file(md_file)
            layer = infer_layer(md_file.name)
            if result == "modified":
                modified += 1
                if layer == "misc":
                    misc_count += 1
            else:
                skipped += 1

    print(f"Done: {modified} files modified, {skipped} files skipped (already had frontmatter)")
    print(f"Files with layer=misc: {misc_count}")

if __name__ == "__main__":
    main()
