"""Static check: does every agent/phase literal in `.claude/workflows/*.js` resolve against
`tools/agent-monitoring/vocabulary.py`'s registries (TCK-20260924-WORKFLOW-AGENT-LITERAL-
VOCABULARY-CHECK)?

`tools/gate_checks/monitoring_anomaly_validator.py::check_vocabulary_drift` answers a downstream
question: has the *corpus* (`events.jsonl`) drifted past a ratcheted ceiling of non-canonical agent
literals? That can only fire once drift has accumulated into real rows, on whichever PR happens to
push the count over the ceiling -- not necessarily the PR that introduced the literal. This module
answers the upstream question instead: does the *source* (`.claude/workflows/*.js`) name a literal
the registry does not know, the moment the line is written? The two checks are complements, not
duplicates -- this module never touches `AGENT_DRIFT_CEILING` or that validator's own code.

Five literal call-site shapes, one directory, two registries, both in `tools/agent-monitoring/
vocabulary.py` -- deliberately narrow (see that ticket's own Out of Scope: this is not a general
dormant-literal gate over all of `.claude/`):

  - agent literals:  `agent: '<literal>'`
  - agent literals:  `writeSidecar(<seq>, '<phase>', '<agent>')` -- 3rd positional argument
  - phase literals:  `phase('<literal>')`
  - phase literals:  `pushEvent('<literal>', ...)`                -- 1st positional argument
  - phase literals:  `writeSidecar(<seq>, '<phase>', '<agent>')` -- 2nd positional argument

Full-line `//` comments and `/* ... */` block interiors are stripped before extraction --
`.claude/workflows/*.js` document their own instrumentation heavily (21 comment-line mentions of
`writeSidecar` against 22 real call sites, measured at this ticket's own scoping time), so an
uncommented scan would roughly double its findings with false ones.

**A `.js` file present in neither `WORKFLOW_PHASES` nor `WORKFLOW_AGENTS` is a loud, named FAIL --
never a silent skip.** This is deliberately NOT computed by asking `vocabulary.py::infer_workflow`
(which returns `None`, "skip silently", for any run_id it cannot classify): that contract is right
for its own callers, who only ever see run_ids for workflows already known to exist, but wrong here
-- the entire point of this check is to catch a workflow *file* neither registry has ever heard of
at all. Delegating to `infer_workflow` would silently inherit its blind spot (7 of 11 real workflow
files were unkeyed in either registry before this ticket).

Regex-based, following `workflow_meta_conformance.py`'s own precedent for scanning
`.claude/workflows/*.js` rather than a general JS parser. Confirmed during investigation
(`staging_artifacts/TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK/investigation.md`) that
every real `writeSidecar(...)` call site in all 11 files is single-line -- no multi-line-call
coverage gap to guard against.

Mirrors the batch's own `check_*()` shape (`List[dict]`, `{"status": "PASS"|"FAIL", "evidence":
...}`, `MARKER:` + `json.dumps(...)` stdout contract) but, unlike
`monitoring_anomaly_validator.py`, **always exits 0** -- this check is advisory only (print
findings, never block a workflow run, a commit, or CI; see the owning ticket's Out of Scope). Do
not "fix" this into matching that sibling's `sys.exit(1)`.
"""
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from vocabulary import WORKFLOW_AGENTS, WORKFLOW_PHASES, is_known_agent, is_known_phase  # noqa: E402

DEFAULT_WORKFLOWS_DIR = Path(".claude/workflows")

_AGENT_LITERAL_RE = re.compile(r"\bagent:\s*'([^']+)'")
_PHASE_CALL_RE = re.compile(r"\bphase\(\s*'([^']+)'")
_PUSH_EVENT_RE = re.compile(r"\bpushEvent\(\s*'([^']+)'")
_WRITE_SIDECAR_RE = re.compile(r"\bwriteSidecar\(\s*[^,]+,\s*'([^']+)'\s*,\s*'([^']+)'")


def _strip_comments(text: str) -> str:
    """Blank out full-line `//` comments and `/* ... */` block interiors, line by line.

    A line-prefix/line-membership check is sufficient here (not a general tokenizer): investigation
    confirmed no real call site in `.claude/workflows/*.js` shares a line with a trailing `//`
    comment.
    """
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
        if stripped.startswith("/*") and "*/" not in line[line.index("/*") + 2:]:
            in_block = True
            out_lines.append("")
            continue
        if stripped.startswith("//"):
            out_lines.append("")
            continue
        out_lines.append(line)
    return "\n".join(out_lines)


def extract_literals_from_workflow_file(path: Path) -> Tuple[set, set]:
    """Return (agent_literals, phase_literals) found in one workflow file, comments excluded."""
    clean_text = _strip_comments(path.read_text(encoding="utf-8"))

    agent_literals = set(_AGENT_LITERAL_RE.findall(clean_text))
    phase_literals = set(_PHASE_CALL_RE.findall(clean_text))
    phase_literals |= set(_PUSH_EVENT_RE.findall(clean_text))

    for match in _WRITE_SIDECAR_RE.finditer(clean_text):
        phase_literals.add(match.group(1))
        agent_literals.add(match.group(2))

    return agent_literals, phase_literals


def check_workflow_vocabulary(workflows_dir: Path = DEFAULT_WORKFLOWS_DIR) -> List[dict]:
    """Aggregate: every unregistered literal and every unkeyed workflow file, as PASS/FAIL rows.

    A workflow file keyed in neither registry contributes an EXTRA, dedicated FAIL naming the file
    (computed independently of the literal-extraction pass below, never derived from
    is_known_agent()/is_known_phase() returning False for every literal, which alone would leave an
    unkeyed file that happens to contain zero literals -- e.g. a hypothetical future workflow with
    no instrumentation yet -- silently unflagged). This file-level FAIL is IN ADDITION TO, not
    instead of, the per-literal rows below: extraction still runs for an unkeyed file (every literal
    found there is trivially unregistered, since `WORKFLOW_AGENTS`/`WORKFLOW_PHASES` default to an
    empty set for an absent key), so AC2's literal-level 6/23 counts include the unkeyed files'
    literals too, not only the already-keyed files' gaps. Each unregistered literal is its own FAIL
    row tagged with its family ("agent" or "phase") -- the two families are never merged into one
    combined count. A workflow file with zero findings across both the file-level and per-literal
    checks contributes one PASS row.
    """
    results: List[dict] = []
    for path in sorted(Path(workflows_dir).glob("*.js")):
        workflow = path.stem
        keyed_in_agents = workflow in WORKFLOW_AGENTS
        keyed_in_phases = workflow in WORKFLOW_PHASES
        file_had_finding = False

        if not keyed_in_agents and not keyed_in_phases:
            file_had_finding = True
            results.append({
                "status": "FAIL",
                "family": "unkeyed_workflow",
                "workflow": workflow,
                "evidence": (
                    f"{path} is keyed in neither WORKFLOW_AGENTS nor WORKFLOW_PHASES "
                    f"(tools/agent-monitoring/vocabulary.py)"
                ),
            })

        agent_literals, phase_literals = extract_literals_from_workflow_file(path)

        for literal in sorted(agent_literals):
            if not is_known_agent(workflow, literal):
                file_had_finding = True
                results.append({
                    "status": "FAIL",
                    "family": "agent",
                    "workflow": workflow,
                    "evidence": f"{path}: agent literal {literal!r} not registered for {workflow!r}",
                })

        for literal in sorted(phase_literals):
            if not is_known_phase(workflow, literal):
                file_had_finding = True
                results.append({
                    "status": "FAIL",
                    "family": "phase",
                    "workflow": workflow,
                    "evidence": f"{path}: phase literal {literal!r} not registered for {workflow!r}",
                })

        if not file_had_finding:
            results.append({
                "status": "PASS",
                "family": None,
                "workflow": workflow,
                "evidence": f"{path}: every extracted literal is registered",
            })

    return results


if __name__ == "__main__":
    result = check_workflow_vocabulary()
    print("MARKER:" + json.dumps(result))
    sys.exit(0)
