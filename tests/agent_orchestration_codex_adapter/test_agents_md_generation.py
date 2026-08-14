from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

def test_agents_md_is_not_stale_draft():
    generated=(ROOT / "AGENTS.md").read_text()
    stale=(ROOT / ".agents" / "rules" / "AGENTS.md").read_text()
    assert generated != stale
    assert stale not in generated

def test_agents_md_states_authoritative_32_phase_pipeline():
    text=(ROOT / "AGENTS.md").read_text()
    assert "17-phase" not in text and "17 phase" not in text
    assert "32-phase" in text and "docs/engine/authoritative_pipeline.md" in text


def test_agents_md_pipeline_note_matches_live_engine_doc():
    assert "32 phases" in (ROOT / "docs" / "engine" / "authoritative_pipeline.md").read_text()
