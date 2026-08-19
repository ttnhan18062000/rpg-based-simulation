"""Unit tests for ChronicleNamer faction naming templates (E53Da).

Tickets: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
AC: dual-faction subject resolution, region templates, era names, backward-compat.
"""
from __future__ import annotations

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.naming import ChronicleNamer


def _make_entry(
    event_type: str,
    subject_id: str = "test",
    tick: int = 1,
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=0,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload={},
        significance=0.0,
        entry_id=f"0:{tick}:{event_type}:{subject_id}",
    )


# ---------------------------------------------------------------------------
# Dual-faction colon-pair templates
# ---------------------------------------------------------------------------

def test_war_declared_dual_faction_template():
    """war_declared with ALPHA:BETA subject_id → dual-faction title."""
    entry = _make_entry("war_declared", subject_id="ALPHA:BETA")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The ALPHA War against BETA"


def test_alliance_formed_dual_faction_template():
    """alliance_formed with ALPHA:BETA subject_id → dual-faction title."""
    entry = _make_entry("alliance_formed", subject_id="ALPHA:BETA")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The ALPHA–BETA Alliance"


def test_peace_treaty_dual_faction_template():
    """peace_treaty with ALPHA:BETA subject_id → dual-faction title."""
    entry = _make_entry("peace_treaty", subject_id="ALPHA:BETA")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The Peace of ALPHA and BETA"


def test_betrayal_dual_faction_template():
    """betrayal with ALPHA:BETA subject_id → dual-faction title."""
    entry = _make_entry("betrayal", subject_id="ALPHA:BETA")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The Betrayal of ALPHA by BETA"


# ---------------------------------------------------------------------------
# Region templates
# ---------------------------------------------------------------------------

def test_territory_transferred_region_template():
    """territory_transferred with region_id subject → region-based title."""
    entry = _make_entry("territory_transferred", subject_id="border_region")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The Conquest of border_region"


def test_siege_begins_region_template():
    """siege_begins with region_id subject → region-based title."""
    entry = _make_entry("siege_begins", subject_id="fortress_north")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "The Siege of fortress_north"


# ---------------------------------------------------------------------------
# faction_names / region_names dict resolution
# ---------------------------------------------------------------------------

def test_faction_names_resolved_in_dual_faction_template():
    """faction_names dict is used to resolve display names for faction IDs."""
    entry = _make_entry("war_declared", subject_id="ALPHA:BETA")
    # Display names without article — template "The {source_faction} War..." supplies "The"
    faction_names = {"ALPHA": "Iron Throne", "BETA": "Thornwood Republic"}
    name = ChronicleNamer.name_milestone(entry, entity_names={}, faction_names=faction_names)
    assert name == "The Iron Throne War against Thornwood Republic"


def test_region_names_resolved_in_region_template():
    """region_names dict is used to resolve display names for region IDs."""
    entry = _make_entry("territory_transferred", subject_id="border_region")
    region_names = {"border_region": "The Borderlands"}
    name = ChronicleNamer.name_milestone(entry, entity_names={}, region_names=region_names)
    assert name == "The Conquest of The Borderlands"


def test_faction_names_fallback_to_raw_id():
    """Missing key in faction_names falls back to raw faction ID."""
    entry = _make_entry("alliance_formed", subject_id="ALPHA:GAMMA")
    name = ChronicleNamer.name_milestone(entry, entity_names={}, faction_names={"ALPHA": "Iron Throne"})
    assert name == "The Iron Throne–GAMMA Alliance"


# ---------------------------------------------------------------------------
# Faction era names
# ---------------------------------------------------------------------------

def test_war_declared_era_name():
    """war_declared dominant type → 'The Age of War'."""
    assert ChronicleNamer.name_era(0, "war_declared") == "The Age of War"


def test_alliance_formed_era_name():
    """alliance_formed dominant type → 'The Age of Alliances'."""
    assert ChronicleNamer.name_era(1, "alliance_formed") == "The Age of Alliances"


def test_territory_transferred_era_name():
    """territory_transferred dominant type → 'The Age of Conquest'."""
    assert ChronicleNamer.name_era(2, "territory_transferred") == "The Age of Conquest"


# ---------------------------------------------------------------------------
# Backward-compat: entity path unchanged
# ---------------------------------------------------------------------------

def test_entity_path_unchanged():
    """Entity-keyed templates still resolve via entity_names."""
    entry = _make_entry("entity_death", subject_id="42")
    entity_names = {42: "Aldric the Bold"}
    name = ChronicleNamer.name_milestone(entry, entity_names)
    assert name == "The Death of Aldric the Bold"


def test_non_colon_non_region_unknown_subject_fallback():
    """Non-colon subject on unknown event_type falls back to raw subject string."""
    entry = _make_entry("some_unknown_event", subject_id="unknown-entity")
    name = ChronicleNamer.name_milestone(entry, entity_names={})
    assert name == "unknown-entity"


# ---------------------------------------------------------------------------
# format_map safety: no KeyError on unexpected template vars
# ---------------------------------------------------------------------------

def test_format_map_no_keyerror_on_extra_vars():
    """format_map(defaultdict(str)) handles templates with unknown keys gracefully."""
    entry = _make_entry("calamity", subject_id="5", tick=99)
    # calamity template uses {tick} only — other vars are extra; must not raise
    name = ChronicleNamer.name_milestone(entry, entity_names={5: "Flood"})
    assert "99" in name
    assert name == "The Calamity at Tick 99"
