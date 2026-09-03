"""
Architecture guards for TCK-20260903-INFORMATION-HUB-ACCUMULATION.

Enforces two Scope guards from the ticket:
  1. No new topology field was added to FactionState -- City-to-City/City-to-Country
     propagation (InformationPropagationService) emits only new WorldEvents, never a
     FactionState mutation.
  2. No Conversation/entity-dialogue class was introduced anywhere in src/ -- AC #5's
     Guide-to-Guide/hub-to-hub exchange requirement was resolved by scoping the exchange
     mechanism out entirely (see docs/mechanics/04_strategic_cognition.md §11), not by
     building a state-level stand-in.
"""
from __future__ import annotations

import re
from pathlib import Path

from src.core.state import FactionState

REPO_SRC = Path(__file__).resolve().parents[2] / "src"

_EXPECTED_FACTION_STATE_FIELDS = {
    "faction_id",
    "territory",
    "resources",
    "diplomatic_relations",
    "active_doctrines",
    "military_strength",
    "tension_level",
    "_canonical_cache",
}


def test_no_new_faction_topology_field_added():
    actual_fields = set(FactionState.__dataclass_fields__.keys())
    assert actual_fields == _EXPECTED_FACTION_STATE_FIELDS, (
        "FactionState's field set changed -- TCK-20260903-INFORMATION-HUB-ACCUMULATION's "
        "propagation mechanism must never add new topology fields to FactionState. "
        f"actual={actual_fields}"
    )


def test_no_conversation_class_introduced():
    pattern = re.compile(r"^\s*class\s+Conversation\b", re.MULTILINE)
    matches = []
    for path in REPO_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            matches.append(str(path))
    assert matches == [], (
        "A Conversation (or similarly named dialogue-system) class was introduced -- "
        "AC #5 requires Guide-to-Guide/hub-to-hub exchange be scoped out entirely, not "
        f"backed by a new Conversation class. Found in: {matches}"
    )
