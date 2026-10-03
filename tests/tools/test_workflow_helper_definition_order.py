"""Regression: a workflow script never calls a top-level ``const`` arrow helper before its definition.

A top-level ``await`` runs in program order, so ``const scopeTs = await captureTs()`` above ``const captureTs =
async () => {...}`` throws ``ReferenceError: Cannot access 'captureTs' before initialization`` on every run
(``implement-ticket.js`` did exactly this for ``captureTs`` and ``resolveScopeTicketLocation``).

Two guards: a static order check over every ``.claude/workflows/*.js`` (a call on an unindented, non-comment line
above the helper's definition line), and a node ``vm`` smoke that runs the Scope phase of ``implement-ticket.js``
with every dispatch stubbed to ``null`` and fails on any ``ReferenceError``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".claude" / "workflows"
_DEFINITION = re.compile(r"^const (\w+) = (?:async )?\(.*\) =>")
_NODE = shutil.which("node")


def find_use_before_define(source: str) -> List[Tuple[str, int, int]]:
    """Return ``(name, call_line, definition_line)`` for each top-level helper called above its definition."""
    lines = source.splitlines()
    definitions = {}
    for number, line in enumerate(lines, start=1):
        match = _DEFINITION.match(line)
        if match:
            definitions.setdefault(match.group(1), number)
    violations = []
    for name, defined_at in definitions.items():
        call = re.compile(rf"\b{re.escape(name)}\(")
        for number in range(1, defined_at):
            line = lines[number - 1]
            if line[:1] in (" ", "\t", "/", "") or line.startswith("*"):
                continue
            if call.search(line):
                violations.append((name, number, defined_at))
                break
    return sorted(violations, key=lambda v: v[1])


@pytest.mark.parametrize("script", sorted(WORKFLOWS_DIR.glob("*.js")), ids=lambda p: p.name)
def test_no_workflow_helper_is_called_before_its_definition(script: Path) -> None:
    assert find_use_before_define(script.read_text(encoding="utf-8")) == []


def test_order_check_flags_a_seeded_use_before_define_and_spares_a_comment() -> None:
    seeded = "\n".join(
        [
            "// captureTs() is defined later, this comment must not count",
            "const startTs = await captureTs()",
            "const captureTs = async () => {",
            "  return null",
            "}",
            "const fine = await captureTs()",
        ]
    )
    assert find_use_before_define(seeded) == [("captureTs", 2, 3)]


_SMOKE = """
const vm = require('vm');
const fs = require('fs');
const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^export const meta = /m, 'const meta = ');
const sandbox = {
  args: { ticket_id: process.argv[2] || '', start_ts: '2026-01-01T00:00:00Z', execution_id_suffix: 'smoke' },
  agent: async () => null, bash: async () => '', log: () => {}, phase: () => {}, console,
};
vm.createContext(sandbox);
(async () => {
  try {
    await vm.runInContext('(async () => {' + source + '\\n})()', sandbox);
    process.stdout.write(JSON.stringify({ error: null }));
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: e.name + ': ' + e.message }));
  }
})();
"""


@pytest.mark.skipif(_NODE is None, reason="node not installed")
@pytest.mark.parametrize("ticket_id", ["", "TCK-20260101-SMOKE"], ids=["new-ticket", "existing-ticket"])
def test_implement_ticket_scope_phase_runs_without_a_reference_error(ticket_id: str) -> None:
    script = WORKFLOWS_DIR / "implement-ticket.js"
    proc = subprocess.run(
        [_NODE, "-e", _SMOKE, str(script), ticket_id],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    error = json.loads(proc.stdout)["error"]
    assert error is None or not error.startswith("ReferenceError"), error
