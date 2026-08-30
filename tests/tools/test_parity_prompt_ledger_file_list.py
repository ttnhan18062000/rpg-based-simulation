"""Static-prose guard for implement-ticket.js's Parity-phase file list
(TCK-20260826-PARITY-FACTION-CANONICAL-SCAN)."""

from pathlib import Path

_JS_PATH = Path(__file__).parent.parent.parent / ".claude" / "workflows" / "implement-ticket.js"


def test_parity_phase_prompt_lists_all_nine_canonical_files():
    source = _JS_PATH.read_text()
    assert "Update docs/parity_ledger/ entries (files:" in source
    for filename in (
        "substrate.yaml", "combat_movement.yaml", "strategic_cognition.yaml",
        "town_resource.yaml", "progression.yaml", "social_narrative.yaml",
        "world_dynamics.yaml", "infrastructure.yaml", "faction.yaml",
    ):
        assert filename in source
