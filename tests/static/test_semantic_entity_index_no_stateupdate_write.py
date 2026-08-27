# Compliance IDs: PERF-010, PERF-011
"""
Anti-drift guard (TCK-20260822-SEMANTIC-ENTITY-INDEX, Step 8; extended by
TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD, Step 1): semantic_entity_indexes must only ever be
written via object.__setattr__ on an already-constructed AuthoritativeState, or carried forward
by value in ApplyPath.apply_generation's own AuthoritativeState(...) constructor call (the exact
`getattr(prior_state, "semantic_entity_indexes", None)` pattern world_indexes already uses at the
same call site, src/engine/apply.py) -- never written through a StateUpdate/replace()-driven
mutation elsewhere. If a future edit routes a write through StateUpdate/replace() instead, this
promotes the index to authoritative state, which this test forbids.
"""
import os
from pathlib import Path


def test_semantic_index_never_written_via_stateupdate():
    root_dir = Path(__file__).resolve().parent.parent.parent
    src_dir = root_dir / "src"

    forbidden_patterns = [
        "semantic_entity_indexes=",
    ]

    violations = []

    for root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = Path(root) / file
            rel_path = file_path.relative_to(root_dir)

            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    for pattern in forbidden_patterns:
                        if pattern not in line:
                            continue
                        # The only legal write site: AuthoritativeState.to_readonly()'s replace()
                        # call, which passes the field through unchanged (self.semantic_entity_indexes),
                        # never constructs a new value -- and the dataclass field declaration itself.
                        if "self.semantic_entity_indexes" in line or "semantic_entity_indexes: Any" in line:
                            continue
                        # object.__setattr__ writes are the sanctioned derived-cache write path.
                        if "object.__setattr__" in line:
                            continue
                        # ApplyPath.apply_generation's cross-tick carry-forward (mirrors the
                        # world_indexes getattr(prior_state, ...) line at the same call site) --
                        # not a StateUpdate/replace()-driven write; the value is passed through
                        # unchanged, never constructed anew.
                        if 'getattr(prior_state, "semantic_entity_indexes", None)' in line:
                            continue
                        violations.append(f"{rel_path}:{line_num} -> {stripped}")

    assert not violations, "Found forbidden StateUpdate/replace() write to semantic_entity_indexes:\n" + "\n".join(violations)
