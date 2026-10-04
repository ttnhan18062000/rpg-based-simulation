"""`visual_assets/` supports Python 3.11 (`requires-python >= 3.11`), but CI runs 3.13, which accepts f-strings 3.11 rejects (PEP 701).

A backslash, or the f-string's own quote character, inside a replacement field is a SyntaxError before 3.12 and nothing on 3.13 would notice. This scans every module
under `visual_assets/` and the tests of it, so the mistake cannot reach a 3.11 user unseen. Pure; no Aseprite.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FILES = sorted([*(REPO / "visual_assets").rglob("*.py"), *(REPO / "tests" / "visual_assets").rglob("*.py")])


def pre_312_problems(source: str) -> list[tuple[int, str]]:
    problems = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.JoinedStr):
            continue
        segment = ast.get_source_segment(source, node) or ""
        body = segment.lstrip("fFrR")
        quote = body[:1]
        if not quote or body.startswith(quote * 3):  # a triple-quoted f-string may reuse a single quote, but not a backslash
            quote = ""
        depth = 0
        for char in body[1:-1]:
            if char == "{":
                depth += 1
            elif char == "}":
                depth = max(0, depth - 1)
            elif depth and char == "\\":
                problems.append((node.lineno, "a backslash inside an f-string replacement field"))
                break
            elif depth and quote and char == quote:
                problems.append((node.lineno, "the f-string's own quote inside a replacement field"))
                break
    return problems


def test_the_checker_finds_both_mistakes_and_accepts_the_safe_forms():
    assert pre_312_problems("x = f\"{'a\\'b'}\"")  # backslash in the field
    assert pre_312_problems("x = f\"{d[\"k\"]}\"")  # the same quote inside the field
    assert not pre_312_problems("remark = \"it's\"\nx = f\"{remark}\"\ny = f\"{d['k']}\"")


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(REPO)))
def test_no_f_string_needs_python_312(path):
    assert pre_312_problems(path.read_text()) == [], path
