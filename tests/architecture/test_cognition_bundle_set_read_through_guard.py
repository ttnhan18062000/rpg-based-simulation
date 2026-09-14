"""
tests/architecture/test_cognition_bundle_set_read_through_guard.py

TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD (Option 3)

`EntityUpdate.merge()`'s own `cognition_bundle_set` field (src/core/updates.py) is a whole-object
REPLACE. A function that stages a `cognition_bundle_set=...` write while building its new
`CognitionModel` from a raw `<something>.cognition` attribute read -- instead of routing that read
through `src/core/cognition_write.py::read_through_cognition()` -- silently discards whatever an
earlier same-tick phase already staged for that entity, with no error (the exact bug
staging_artifacts/TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD/investigation.md
documents against the real writer set).

This is a backstop, not a fix (see that investigation's own Option 3 verdict): it converts "a
future writer silently gets this wrong" into "a future writer's PR fails CI with a clear message,"
pointing at the one sanctioned helper to use instead. It does not, and cannot, verify a writer that
calls the helper actually threads its *result* into the eventual `cognition_bundle_set=` value
(that is a correctness question for review/tests, not a mechanical AST property) -- it only catches
the mechanically-detectable case: a raw `.cognition` read plus a `cognition_bundle_set=` write in
the same function, with no call to the sanctioned helper anywhere in that function at all.

AST walk over every `.py` file under `src/`, mirroring the resolver style in
tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"

_HELPER_MODULE = "src/core/cognition_write.py"
_HELPER_FUNC_NAME = "read_through_cognition"

# (relative file path, function name) pairs that raw-read `.cognition` and separately stage a
# `cognition_bundle_set=` write in the same function, WITHOUT calling the sanctioned helper --
# verified safe by a different, real mechanism: the caller has already materialized/patched the
# entity's `.cognition` field to the correct same-tick value before this function ever runs, so
# there is nothing for a read-through to do here. Each entry names that mechanism so a future
# reader isn't left to re-derive it.
_ALLOWLIST = {
    ("src/engine/movement.py", "resolve_move"): (
        "Called only from pipeline_phases/movement.py::route_movement_intent(), which already "
        "calls read_through_cognition() and patches `entity.cognition` to the correct same-tick "
        "value BEFORE calling this function -- the `.cognition` read here (habit-bias lookup) and "
        "the later cognition_bundle_set= write both see/produce the already-correct value by "
        "construction, not by this function reading through anything itself."
    ),
}


def _iter_function_defs(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _has_cognition_bundle_set_write(func_node: ast.AST) -> bool:
    """Detects both shapes real writers use: a literal `cognition_bundle_set=...` keyword
    argument (`replace(x, cognition_bundle_set=...)`), and a dict-subscript build-up later
    splatted into one (`kwargs["cognition_bundle_set"] = ...; replace(x, **kwargs)`, as
    src/engine/quests.py::enforce() does for its conditionally-present reputation write) --
    a literal-keyword-only check would miss the second shape entirely."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.keyword) and node.arg == "cognition_bundle_set":
            return True
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "cognition_bundle_set":
                return True
    return False


def _has_raw_cognition_attribute_read(func_node: ast.AST) -> bool:
    for node in ast.walk(func_node):
        if isinstance(node, ast.Attribute) and node.attr == "cognition":
            return True
    return False


def _called_names(func_node: ast.AST):
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            callee = node.func
            name = callee.id if isinstance(callee, ast.Name) else (
                callee.attr if isinstance(callee, ast.Attribute) else None
            )
            if name is not None:
                yield name


def _calls_any_of(func_node: ast.AST, names: set) -> bool:
    return any(called in names for called in _called_names(func_node))


def _parse_all_src_files():
    parsed = []
    for path in sorted(_SRC_DIR.rglob("*.py")):
        rel_path = str(path.relative_to(_REPO_ROOT))
        try:
            tree = ast.parse(path.read_text(), filename=rel_path)
        except SyntaxError:
            continue
        parsed.append((rel_path, tree))
    return parsed


def _find_violations():
    parsed_files = _parse_all_src_files()

    # Any function (at any call depth) that itself directly calls the sanctioned helper is a safe
    # delegate -- e.g. src/domains/combat_engagement/phase.py::_read_through_cognition() wraps
    # read_through_cognition() with this phase's own two-accumulator lookup order. Computed, not
    # hardcoded by name, so a future indirection level is picked up automatically rather than
    # needing its own allowlist entry.
    safe_names = {_HELPER_FUNC_NAME}
    changed = True
    while changed:
        changed = False
        for _, tree in parsed_files:
            for func_node in _iter_function_defs(tree):
                if func_node.name in safe_names:
                    continue
                if _calls_any_of(func_node, safe_names):
                    safe_names.add(func_node.name)
                    changed = True

    violations = []
    for rel_path, tree in parsed_files:
        if rel_path == _HELPER_MODULE:
            continue
        for func_node in _iter_function_defs(tree):
            if not _has_cognition_bundle_set_write(func_node):
                continue
            if not _has_raw_cognition_attribute_read(func_node):
                continue
            if _calls_any_of(func_node, safe_names):
                continue
            if (rel_path, func_node.name) in _ALLOWLIST:
                continue
            violations.append(f"{rel_path}::{func_node.name} (line {func_node.lineno})")

    return violations


def test_every_cognition_bundle_set_writer_reads_through_the_sanctioned_helper():
    violations = _find_violations()
    assert not violations, (
        "Function(s) below stage a cognition_bundle_set= write while reading `.cognition` "
        "directly, without calling src/core/cognition_write.py::read_through_cognition() -- this "
        "risks silently discarding an earlier same-tick phase's own cognition write once "
        "EntityUpdate.merge()'s whole-object replace applies "
        "(TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD). Route the base "
        "CognitionModel through read_through_cognition() before building the new one, or -- if "
        "this call site is safe by a different, real mechanism (e.g. the caller already "
        "materialized/patched `.cognition` before calling in) -- add it to _ALLOWLIST above with "
        "a comment naming that mechanism.\n  " + "\n  ".join(violations)
    )


def test_allowlist_entries_still_exist_and_still_trip_the_raw_pattern():
    """Guards the allowlist itself from silently going stale: if `resolve_move` (or a future
    entry) is refactored to no longer match the raw pattern (e.g. it starts calling the helper, or
    is renamed/removed), this fails so the now-unnecessary or now-wrong allowlist entry gets
    noticed and cleaned up, rather than quietly protecting nothing."""
    for rel_path, func_name in _ALLOWLIST:
        path = _REPO_ROOT / rel_path
        assert path.is_file(), f"Allowlisted file no longer exists: {rel_path}"
        tree = ast.parse(path.read_text(), filename=rel_path)
        matches = [
            node for node in _iter_function_defs(tree)
            if node.name == func_name
            and _has_cognition_bundle_set_write(node)
            and _has_raw_cognition_attribute_read(node)
            and not _calls_any_of(node, {_HELPER_FUNC_NAME})
        ]
        assert matches, (
            f"Allowlist entry ({rel_path}, {func_name}) no longer matches the raw pattern it was "
            "added to suppress -- remove the now-unnecessary entry from _ALLOWLIST."
        )
