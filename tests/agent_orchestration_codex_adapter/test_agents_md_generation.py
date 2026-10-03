import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

def test_agents_md_is_not_stale_draft():
    generated=(ROOT / "AGENTS.md").read_text()
    stale=(ROOT / ".agents" / "rules" / "AGENTS.md").read_text()
    assert generated != stale
    assert stale not in generated

# PERF-D6: prose never states a refinement-phase count as a literal number (the count changes with
# every RPG-core phase). These tests keep their original purpose -- AGENTS.md must not carry a stale
# phase figure and must agree with the live engine contract -- and re-express "agree" as: neither states
# a literal count, and both name the same counted unit ("refinement phase").
_LITERAL_PHASE_COUNT = re.compile(r"\b\d+[- ]phases?\b", re.IGNORECASE)


def _agents_pipeline_note(text: str) -> str:
    lines = [ln for ln in text.splitlines() if "docs/engine/authoritative_pipeline.md" in ln]
    assert lines, "AGENTS.md has no line linking docs/engine/authoritative_pipeline.md"
    return "\n".join(lines)


def test_agents_md_states_authoritative_pipeline_without_a_phase_count():
    text=(ROOT / "AGENTS.md").read_text()
    assert "17-phase" not in text and "17 phase" not in text
    assert "docs/engine/authoritative_pipeline.md" in text
    assert not _LITERAL_PHASE_COUNT.search(_agents_pipeline_note(text))


def test_agents_md_pipeline_note_matches_live_engine_doc():
    pipeline_doc=(ROOT / "docs" / "engine" / "authoritative_pipeline.md").read_text()
    note=_agents_pipeline_note((ROOT / "AGENTS.md").read_text())
    assert not _LITERAL_PHASE_COUNT.search(pipeline_doc)
    assert "refinement phase" in pipeline_doc.lower()
    assert "refinement phase" in note.lower()
