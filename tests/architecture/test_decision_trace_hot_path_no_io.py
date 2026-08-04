"""
tests/architecture/test_decision_trace_hot_path_no_io.py
───────────────────────────────────────────────────────────────────────────────
Architecture guard for TCK-20260702-OBSISO-TRACE-ASYNC AC #1.

Statically walks the AST of DecisionTraceWriter.write_trace()'s own function
body and asserts no file/index I/O call is reachable from it — proving the
hot-path safety contract §3 violation this ticket fixes cannot silently
regress. `_write_entry_to_file` (the async drain-worker callback) is exempt:
it runs off the phase call path and is where the actual I/O now lives.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from src.observability.cognition.decision_trace_writer import DecisionTraceWriter

FORBIDDEN_CALL_NAMES = {"open", "write", "flush", "dump"}


def _find_method(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Method {name} not found in DecisionTraceWriter source")


def _call_target_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def test_write_trace_has_no_reachable_file_io():
    source = inspect.getsource(DecisionTraceWriter)
    tree = ast.parse(source)
    write_trace = _find_method(tree, "write_trace")

    for node in ast.walk(write_trace):
        if isinstance(node, ast.Call):
            name = _call_target_name(node)
            assert name not in FORBIDDEN_CALL_NAMES, (
                f"write_trace() must not reach file I/O call '{name}()' on the hot path"
            )


def test_write_trace_does_not_reference_file_handle_or_index_append():
    source = inspect.getsource(DecisionTraceWriter)
    tree = ast.parse(source)
    write_trace = _find_method(tree, "write_trace")

    for node in ast.walk(write_trace):
        if isinstance(node, ast.Attribute):
            assert node.attr != "_file", "write_trace() must not reference self._file directly"
            assert node.attr != "append_entry", (
                "write_trace() must not call DecisionTraceIndex.append_entry() directly"
            )
