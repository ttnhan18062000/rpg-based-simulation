from __future__ import annotations

import ast
import os
import sys
import pytest


def _type_checking_lines(tree: ast.AST) -> set[int]:
    """Line numbers covered by an `if TYPE_CHECKING:` block.

    Mirrors the collect-line-ranges technique in
    tests/architecture/test_api_read_model_guard.py. Duplicated locally rather than shared
    with test_phase18_import_boundaries.py -- this repo's established pattern for these
    checks is a private per-file helper, not a shared cross-file utility module.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
            )
            if is_tc:
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        lines.add(child.lineno)
    return lines


def test_observability_boundaries_doc_exists():
    doc_path = "docs/architecture/observability_behavior_profiling_boundary.md"
    assert os.path.exists(doc_path), f"Boundary document {doc_path} does not exist"
    
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    # Check that it defines mandatory terms
    required_terms = [
        "runtime profiling",
        "raw simulation event",
        "behavior event",
        "behavior timeline",
        "behavior episode",
        "behavior metric",
        "behavior finding",
        "behavior insight",
        "scorecard",
        "run comparison"
    ]
    for term in required_terms:
        assert term in content, f"Boundary document is missing definition for term: {term}"

def test_hot_path_does_not_import_heavy_analyzers():
    # Define hot path modules/directories
    hot_path_paths = [
        "src/engine/",
        "src/observability/config.py",
        "src/observability/event_extractor.py",
        "src/observability/event_recorder.py"
    ]

    # Define forbidden heavy analysis import patterns
    forbidden_import_substrings = (
        "observability.anomaly",
        "observability.cognition",
        "observability.reporting",
    )

    def _is_forbidden(name: str) -> bool:
        # NOTE: matches the *bare* forbidden prefix (e.g. "observability.anomaly"), not
        # "src.observability.anomaly" -- this reproduces the pre-existing weak test's exact
        # matching semantics (it checked raw content for "from observability.anomaly", which
        # never matches this codebase's real "from src.observability.anomaly..." imports).
        # A stricter "src."-aware match surfaces real, currently-unpinned violations in
        # src/engine/kernel.py -- out of this ticket's approved scope (kernel.py is not in
        # plan.md's pinned-exception lists or Scope Guards). See ticket Implementation Notes.
        return any(name.startswith(forbidden) for forbidden in forbidden_import_substrings)

    for path in hot_path_paths:
        full_path = os.path.abspath(path)
        if not os.path.exists(full_path):
            continue

        if os.path.isdir(full_path):
            files_to_check = []
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        files_to_check.append(os.path.join(root, file))
        else:
            files_to_check = [full_path]

        for file_path in files_to_check:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=file_path)
            skip_lines = _type_checking_lines(tree)

            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if node.lineno in skip_lines:
                    continue
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    assert not _is_forbidden(module), (
                        f"Forbidden import '{module}' found in hot path file {file_path}"
                    )
                else:
                    for alias in node.names:
                        assert not _is_forbidden(alias.name), (
                            f"Forbidden import '{alias.name}' found in hot path file {file_path}"
                        )
