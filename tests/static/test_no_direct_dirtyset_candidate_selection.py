import os
from pathlib import Path


def test_no_direct_dirtyset_candidate_selection_outside_selector():
    """
    Ensures that simulation phases, systems, and AI modules do not directly access
    DirtySet or its properties (e.g., .dirty_set.movement_entities). All candidate
    selection must go through CandidateSelector or authoritative helper functions in src.core.dirty.
    """
    root_dir = Path(__file__).resolve().parent.parent.parent
    target_dirs = [
        root_dir / "src" / "engine" / "pipeline_phases",
        root_dir / "src" / "systems",
        root_dir / "src" / "ai",
    ]

    forbidden_patterns = [
        ".dirty_set",
        "dirty_set.",
    ]

    violations = []

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for root, _, files in os.walk(target_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_dir)

                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in forbidden_patterns:
                            if pattern in line and not line.strip().startswith("#"):
                                violations.append(f"{rel_path}:{line_num} -> found forbidden usage '{pattern}': {line.strip()}")

    assert not violations, "Found forbidden direct DirtySet access outside CandidateSelector:\n" + "\n".join(violations)
