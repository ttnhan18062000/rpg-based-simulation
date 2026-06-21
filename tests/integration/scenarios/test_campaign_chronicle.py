"""
tests/integration/scenarios/test_campaign_chronicle.py
────────────────────────────────────────────────────────────────────────────────
Integration test for ChronicleCompiler.compile() — E51D end-to-end pipeline.

Covers:
  TC-I1 (slow): Full compile() pipeline writes Chronicle.md + chronicle.json
                to a temporary directory and validates output structure.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.compiler import ChronicleCompiler


def _make_entry(
    event_type: str,
    episode: int = 0,
    tick: int = 1,
    subject_id: str = "1",
    payload: dict | None = None,
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=0.0,
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}",
    )


def _make_campaign_state(entries: list[NarrativeLedgerEntry]) -> CampaignState:
    """Build a minimal CampaignState with the given ledger entries."""
    state = CampaignState(
        campaign_id="integration-test",
        episode_index=len({e.episode for e in entries}),
    )
    state.narrative_ledger = entries
    return state


@pytest.mark.slow
def test_chronicle_compiler_writes_md_and_json_to_disk():
    """TC-I1: Full compile() pipeline writes Chronicle.md + chronicle.json to disk.

    Validates:
    - Chronicle.md file exists and contains valid YAML frontmatter
    - chronicle.json file exists and contains required top-level keys
    - Both files round-trip correctly
    """
    # Build a campaign state with enough entries to generate eras
    entries = []
    for ep in range(6):
        entries.append(_make_entry("quest_completed", episode=ep, tick=10 + ep * 5,
                                    subject_id=str(ep + 1)))
        entries.append(_make_entry("entity_death", episode=ep, tick=100 + ep * 5,
                                    subject_id=str(ep + 10)))
    # Add some below-threshold entries (should be filtered)
    for ep in range(6):
        entries.append(_make_entry("harvesting", episode=ep, tick=50 + ep))

    campaign_state = _make_campaign_state(entries)
    entity_names = {
        1: "Aldric", 2: "Bren", 3: "Celara", 4: "Daro", 5: "Elara", 6: "Faun",
        10: "Guard A", 11: "Guard B", 12: "Guard C", 13: "Guard D", 14: "Guard E", 15: "Guard F",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        compiler = ChronicleCompiler()
        md_str, json_dict = compiler.compile(
            campaign_state,
            output_dir=tmpdir,
            entity_names=entity_names,
        )

        # ── Check Chronicle.md ─────────────────────────────────────────────────
        md_path = os.path.join(tmpdir, "Chronicle.md")
        assert os.path.isfile(md_path), "Chronicle.md must be written to output_dir"

        with open(md_path, encoding="utf-8") as f:
            md_on_disk = f.read()

        assert md_on_disk == md_str, "Chronicle.md on disk must match returned md_str"
        lines = md_on_disk.splitlines()
        assert lines[0] == "---", "Chronicle.md must start with YAML --- delimiter"
        assert "campaign_id: integration-test" in md_on_disk
        assert "total_episodes:" in md_on_disk
        assert "era_count:" in md_on_disk
        assert "# Chronicle of integration-test" in md_on_disk

        # ── Check chronicle.json ───────────────────────────────────────────────
        json_path = os.path.join(tmpdir, "chronicle.json")
        assert os.path.isfile(json_path), "chronicle.json must be written to output_dir"

        with open(json_path, encoding="utf-8") as f:
            json_on_disk = json.load(f)

        assert json_on_disk["campaign_id"] == "integration-test"
        assert "eras" in json_on_disk
        assert "episodes" in json_on_disk
        assert "named_milestones" in json_on_disk
        assert isinstance(json_on_disk["eras"], list)
        assert isinstance(json_on_disk["episodes"], list)
        assert isinstance(json_on_disk["named_milestones"], list)

        # Verify no harvesting events (below threshold) leaked through
        milestone_types = {m["event_type"] for m in json_on_disk["named_milestones"]}
        assert "harvesting" not in milestone_types, (
            "Below-threshold events must not appear in named_milestones"
        )

        # Verify milestone name resolution worked
        if json_on_disk["named_milestones"]:
            first_milestone = json_on_disk["named_milestones"][0]
            assert isinstance(first_milestone["name"], str)
            assert len(first_milestone["name"]) > 0
