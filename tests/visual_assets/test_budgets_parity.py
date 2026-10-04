"""`docs/assets/budgets.md` and the code cannot drift apart (U-05).

The doc's bounds table names every bound as (module, attribute, proposed value). This fails when a code bound has no row, a row
names a missing attribute, a row's proposed value differs from the code, or a "provisional (U-05)" comment is left in the code.
The checkers are pure functions over text, so the same code that guards the real tree is proven on planted violations.
No Aseprite needed; runs in CI.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "visual_assets"
DOC = REPO / "docs" / "assets" / "budgets.md"

BOUND_NAME = re.compile(r"^(MAX_\w+|DEFAULT_LIMIT|\w*TIMEOUT\w*|UNSUPPORTED_LIMITATIONS)$")
PROVISIONAL = re.compile(r"provisional[^\n]*\(U-05\)|\(U-05\)[^\n]*provisional", re.IGNORECASE)
ROW = re.compile(r"^\|\s*`(?P<module>[\w.]+)`\s*\|\s*`(?P<attr>\w+)`\s*\|(?P<cells>.*)\|\s*$")


def doc_rows(text: str) -> dict[tuple[str, str], str]:
    """(module, attribute) -> the backticked proposed value, from the bounds table."""
    rows: dict[tuple[str, str], str] = {}
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        cells = [c.strip() for c in match["cells"].split("|")]
        # columns after the first two: Current, Measured, Proposed, Rule, Flag, Status
        proposed = re.fullmatch(r"`(.+)`", cells[2])
        assert proposed, f"{match['module']}.{match['attr']}: the Proposed cell must be one backticked value"
        key = (match["module"], match["attr"])
        assert key not in rows, f"duplicate row {key}"
        rows[key] = proposed[1]
    return rows


def code_bounds(root: Path) -> set[tuple[str, str]]:
    """Every module-level bound (by name) under `visual_assets/`, as (dotted module, attribute)."""
    found = set()
    for path in sorted(root.rglob("*.py")):
        module = ".".join(path.relative_to(root.parent).with_suffix("").parts).removesuffix(".__init__")
        for node in ast.parse(path.read_text()).body:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            for target in targets:
                if isinstance(target, ast.Name) and BOUND_NAME.match(target.id):
                    found.add((module, target.id))
    return found


def value_mismatches(rows: dict[tuple[str, str], str]) -> list[str]:
    problems = []
    for (module, attr), proposed in sorted(rows.items()):
        try:
            actual = getattr(importlib.import_module(module), attr)
        except (ImportError, AttributeError):
            problems.append(f"{module}.{attr}: the row names a missing module or attribute")
            continue
        if isinstance(actual, frozenset):
            expected: object = frozenset(token.strip() for token in proposed.split(","))
        else:
            expected = int(proposed)
        if actual != expected:
            problems.append(f"{module}.{attr}: code has {actual!r}, budgets.md proposes {proposed}")
    return problems


def missing_rows(rows: dict[tuple[str, str], str], bounds: set[tuple[str, str]]) -> list[str]:
    return [f"{module}.{attr}: a bound in the code with no row in budgets.md" for module, attr in sorted(bounds - set(rows))]


def leftover_provisional(root: Path) -> list[str]:
    return [
        f"{path.relative_to(root.parent)}:{number}: {line.strip()}"
        for path in sorted(root.rglob("*.py"))
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if PROVISIONAL.search(line)
    ]


def test_every_row_matches_the_code():
    problems = value_mismatches(doc_rows(DOC.read_text()))
    assert not problems, "\n".join(problems)


def test_every_code_bound_has_a_row():
    problems = missing_rows(doc_rows(DOC.read_text()), code_bounds(PKG))
    assert not problems, "\n".join(problems)


def test_no_provisional_u05_comment_is_left():
    assert not leftover_provisional(PKG)


def test_the_retention_bound_is_an_approved_row_and_every_bound_is_proposed_or_approved():
    text = DOC.read_text()
    # the last unset row (retention) was approved on 2026-10-04 (TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK); no row is UNSET any more
    retention = [line for line in text.splitlines() if "`MAX_UNADOPTED_INTAKE_AGE_DAYS`" in line and ROW.match(line)]
    assert len(retention) == 1 and retention[0].rstrip().endswith("APPROVED 2026-10-04 |"), retention
    assert "| UNSET |" not in text
    for line in text.splitlines():
        if ROW.match(line):
            status = line.strip("| ").split("|")[-1].strip()
            assert re.fullmatch(r"PROPOSED|APPROVED \d{4}-\d{2}-\d{2}", status), line


def test_the_scanner_finds_the_known_bounds():
    bounds = code_bounds(PKG)
    assert ("visual_assets.store.config", "MAX_SOURCE_BYTES") in bounds
    assert ("visual_assets.drawing.config", "JOB_TIMEOUT_S") in bounds
    assert ("visual_assets.store.intake.validator", "UNSUPPORTED_LIMITATIONS") in bounds


def test_planted_violations_are_caught():
    rows = {("visual_assets.store.config", "MAX_DIM"): "129", ("visual_assets.store.config", "NO_SUCH"): "1"}
    problems = value_mismatches(rows)
    assert any("MAX_DIM: code has 128" in p for p in problems)
    assert any("NO_SUCH: the row names a missing" in p for p in problems)
    assert missing_rows({}, {("m", "MAX_X")})
    assert PROVISIONAL.search("MAX_X = 1  # provisional (U-05)")
    assert not PROVISIONAL.search("MAX_X = 1  # budget: docs/assets/budgets.md")
