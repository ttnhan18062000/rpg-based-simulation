"""Codex-side conformance test for the gate_policy/artifact_requirements axes
(TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST, AC #4).

The real translated Codex artifact is the generated root `AGENTS.md`
(`tools/agent_orchestration_codex_adapter/generator.py::build_agents_md`) — `.codex/config.toml`
is confirmed deliberately inert (see `test_no_production_hook_enabled.py`) and is never a diffable
gate/artifact source. Reads the real committed `AGENTS.md` directly, mirroring
`test_agents_md_generation.py`'s own direct-read convention (`(ROOT / "AGENTS.md").read_text()`,
no `tmp_path` rendering) — this file must be kept regenerated and committed for these tests to mean
anything.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from tools.agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_AGENTS_MD_PATH = _REPO_ROOT / "AGENTS.md"
_CODEX_CONFIG_PATH = _REPO_ROOT / ".codex" / "config.toml"


def _gate_policy_section(text: str) -> str:
    start = text.index("## Gate Policy")
    end = text.index("## Artifact Requirements", start)
    return text[start:end]


def _artifact_requirements_section(text: str) -> str:
    start = text.index("## Artifact Requirements")
    end = text.index("## Skills", start)
    return text[start:end]


def test_agents_md_gate_policy_section_matches_contract():
    bundle = load_contract(_REPO_ROOT)
    text = _AGENTS_MD_PATH.read_text(encoding="utf-8")
    assert "## Gate Policy" in text

    section = _gate_policy_section(text)
    for gate in bundle.gate_policy["gates"]:
        assert gate["phase"] in section, (
            f"phase {gate['phase']!r} from contract gate_policy not found in AGENTS.md's "
            "## Gate Policy section"
        )


def test_agents_md_artifact_requirements_section_matches_contract():
    bundle = load_contract(_REPO_ROOT)
    text = _AGENTS_MD_PATH.read_text(encoding="utf-8")
    assert "## Artifact Requirements" in text

    section = _artifact_requirements_section(text)
    artifact_requirements = bundle.artifact_requirements
    assert artifact_requirements is not None
    assert artifact_requirements["exempt_tier"] in section
    for filename in artifact_requirements["required_files"]:
        assert filename in section, (
            f"required file {filename!r} not found in AGENTS.md's ## Artifact Requirements section"
        )


def test_codex_config_toml_confirmed_not_a_target():
    # Deliberately does not scan for plain English words/filenames (phase names like "Implement",
    # terminal-status values, or bare "plan.md") — those can appear as innocent substrings of
    # unrelated prose already in this file's own history-recording comments (e.g. "this ticket's
    # plan.md" or "...Implementation Notes"), the same false-positive class
    # `tools/gate_checks/workflow_meta_conformance.py::_title_has_dedicated_mention` documents for
    # "Review" inside "Security-Review". Checked instead against vocabulary that is unambiguously
    # specific to the gate_policy/artifact_requirements axes themselves: the field names and the
    # dotted check-module paths gate-policy.yaml actually carries (e.g.
    # "gate_checks.doc_staleness_check" is not plausible unrelated prose).
    with open(_CODEX_CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)
    text = _CODEX_CONFIG_PATH.read_text(encoding="utf-8")

    assert data == {}, f"{_CODEX_CONFIG_PATH} must stay a comment-only, zero-key TOML file"
    assert "gate_policy" not in text
    assert "artifact_requirements" not in text
    assert "gate-policy.yaml" not in text

    bundle = load_contract(_REPO_ROOT)
    for gate in bundle.gate_policy["gates"]:
        if gate["gate_type"] == "static_check":
            assert gate["check_module"] not in text, (
                f"{_CODEX_CONFIG_PATH} must never carry gate_policy vocabulary like "
                f"{gate['check_module']!r} — the real translated Codex artifact for phase/gate/"
                "status data is AGENTS.md, never this file"
            )
