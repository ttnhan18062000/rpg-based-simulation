"""Reproduction script for TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK's Request Summary
figures (independent re-derivation, not trusting the ticket's stated 6/23/29).

Scans every `.claude/workflows/*.js` file for the five literal call-site shapes named in the
ticket's Scope section:
  - agent literals:  agent: '<literal>'
  - agent literals:  writeSidecar(<seq>, '<phase>', '<agent>')  -- 3rd positional arg
  - phase literals:  phase('<literal>')
  - phase literals:  pushEvent('<literal>', ...)                -- 1st positional arg
  - phase literals:  writeSidecar(<seq>, '<phase>', '<agent>')  -- 2nd positional arg

Comment-line exclusion: a line is skipped if, after stripping leading whitespace, it starts with
`//` or is inside a `/* ... */` block. This matches the ticket's own measurement note (21 comment
mentions of writeSidecar against 22 real call sites) -- a line-prefix check is sufficient because
investigation (below) confirms no in-line trailing `//` comments follow a real call on the same
line in these files.

Run: python3 vocab_scan.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, "tools/agent-monitoring")
from vocabulary import WORKFLOW_AGENTS, WORKFLOW_PHASES, is_known_agent  # noqa: E402

WORKFLOWS_DIR = Path(".claude/workflows")

_AGENT_LITERAL_RE = re.compile(r"\bagent:\s*'([^']+)'")
_PHASE_CALL_RE = re.compile(r"\bphase\(\s*'([^']+)'")
_PUSH_EVENT_RE = re.compile(r"\bpushEvent\(\s*'([^']+)'")
_WRITE_SIDECAR_RE = re.compile(
    r"\bwriteSidecar\(\s*[^,]+,\s*'([^']+)'\s*,\s*'([^']+)'"
)


def strip_comments(text: str) -> list[str]:
    """Return text's lines with block-comment interiors and full-line `//` comments blanked out."""
    out_lines = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if in_block:
            if "*/" in line:
                in_block = False
                line = line[line.index("*/") + 2:]
            else:
                out_lines.append("")
                continue
        if stripped.startswith("/*"):
            if "*/" in line[line.index("/*") + 2:]:
                pass
            else:
                in_block = True
                out_lines.append("")
                continue
        if stripped.startswith("//"):
            out_lines.append("")
            continue
        out_lines.append(line)
    return out_lines


def scan_workflow_file(path: Path) -> tuple[set[str], set[str]]:
    """Return (agent_literals, phase_literals) found in one workflow file, comments excluded."""
    text = path.read_text(encoding="utf-8")
    lines = strip_comments(text)
    clean_text = "\n".join(lines)

    agent_literals = set(_AGENT_LITERAL_RE.findall(clean_text))
    phase_literals = set(_PHASE_CALL_RE.findall(clean_text))
    phase_literals |= set(_PUSH_EVENT_RE.findall(clean_text))

    for m in _WRITE_SIDECAR_RE.finditer(clean_text):
        phase_literals.add(m.group(1))
        agent_literals.add(m.group(2))

    return agent_literals, phase_literals


def main() -> int:
    all_files = sorted(WORKFLOWS_DIR.glob("*.js"))
    print(f"Found {len(all_files)} workflow files: {[f.name for f in all_files]}\n")

    unregistered_agent_rows = []
    unregistered_phase_rows = []
    keyed_in_neither = []

    for path in all_files:
        workflow = path.stem
        agent_literals, phase_literals = scan_workflow_file(path)

        in_agents_registry = workflow in WORKFLOW_AGENTS
        in_phases_registry = workflow in WORKFLOW_PHASES
        if not in_agents_registry and not in_phases_registry:
            keyed_in_neither.append(workflow)

        for lit in sorted(agent_literals):
            if not is_known_agent(workflow, lit):
                unregistered_agent_rows.append((workflow, lit))

        for lit in sorted(phase_literals):
            if lit not in WORKFLOW_PHASES.get(workflow, set()):
                unregistered_phase_rows.append((workflow, lit))

    print("=== Unregistered agent literals ===")
    for w, lit in unregistered_agent_rows:
        print(f"  {w}: {lit!r}")
    print(f"TOTAL agent: {len(unregistered_agent_rows)}\n")

    print("=== Unregistered phase literals ===")
    for w, lit in unregistered_phase_rows:
        print(f"  {w}: {lit!r}")
    print(f"TOTAL phase: {len(unregistered_phase_rows)}\n")

    print(f"TOTAL combined: {len(unregistered_agent_rows) + len(unregistered_phase_rows)}\n")

    print(f"Workflow files keyed in neither registry: {keyed_in_neither}")
    print(f"Files keyed in WORKFLOW_PHASES: {sorted(WORKFLOW_PHASES.keys())}")
    print(f"Files keyed in WORKFLOW_AGENTS: {sorted(WORKFLOW_AGENTS.keys())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
