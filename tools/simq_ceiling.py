#!/usr/bin/env python3
"""TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE — structural_ceiling classification.

Answers "can I trust/interpret this pillar score for this scenario" separately from the score
itself. Three kinds, in increasing order of certainty:

- `tick_budget`: fully computed from real config (config/simulation_quality/detection_params.yaml's
  time_gates vs. each run_key's own tick count, read from corpus_registry.yaml). Deterministic,
  no engine run needed, no false positives possible.
- `flag_gated`: a small, hand-verified table (FLAG_GATED_PILLAR_CEILINGS below) of pillars whose
  ceiling is fully explained by a feature flag being off corpus-wide. NOT an automated
  engine-wide analyzer — each entry requires real evidence (a ticket citation), added
  incrementally as investigations confirm new cases. Absence from this table is not proof a
  pillar has no flag-gated ceiling, only that none has been confirmed yet.
- `content_threshold`: judgment-call entries, sourced from tests/simulation_quality/fixtures/score_ceilings.json.
  Not computed here.

Also supports a `corrected` provenance state — not an ongoing ceiling, but a record that a past
drift was traced to a real, now-fixed cause, so a reader doesn't mistake historical corrected
drift for a live ceiling.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

DETECTION_PARAMS_PATH = Path("config/simulation_quality/detection_params.yaml")
CORPUS_REGISTRY_PATH = Path("config/simulation_quality/corpus_registry.yaml")
SCORE_CEILINGS_PATH = Path("tests/simulation_quality/fixtures/score_ceilings.json")

# time_gates key -> pillar, confirmed by direct grep of each scorer's own
# self.weights.int_param(...) call sites (TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE investigation).
# 3 of the 22 real config keys (war_without_conflict_window, zero_spawn_cadence_check,
# scenario_stall_default) are NOT included here — their consuming logic was not confirmed to live
# directly in a scorer's own int_param() call during this ticket's own investigation pass (may be
# consumed further upstream, e.g. event_extractor.py deciding WHEN to fire the corresponding
# event). Left out deliberately rather than guessed at; a future pass can add them once traced.
TIME_GATE_PILLAR = {
    "zero_harvest_after_tick": "ECONOMY",
    "zero_crafting_after_tick": "ECONOMY",
    "zero_trade_after_tick": "ECONOMY",
    "zero_combat_by_tick": "COMBAT",
    "zero_diplomacy_by_tick": "FACTION",
    "faction_monopoly_by_tick": "FACTION",
    "faction_early_extinction_by_tick": "FACTION",
    "zero_quests_after_tick": "NARRATIVE",
    "zero_chronicle_after_tick": "NARRATIVE",
    "zero_emergence_by_tick": "WORLD",
    "early_extinction_before_tick": "COMBAT",
    "attrition_50pct_by_tick": "COMBAT",
    "attrition_90pct_by_tick": "COMBAT",
    "belief_dormant_window": "INFORMATION",
    "progression_frozen_by_tick": "PROGRESSION",
    "xp_plateau_by_tick": "PROGRESSION",
    "stagnation_window": "SOCIAL",
    "loop_sustained_window": "WORLD",
}

# Hand-verified flag-gated ceilings. Each entry requires real, cited evidence — never speculative.
FLAG_GATED_PILLAR_CEILINGS = {
    "COMBAT": {
        "flag": "ENABLE_COMBAT_ENGAGEMENT",
        "reason": (
            "ENABLE_COMBAT_ENGAGEMENT is corpus-wide OFF (DEV-002 deliberate ruling) — "
            "CombatEngagementPhase (PP-16) never runs anywhere in the SimQ corpus, so no "
            "attacker-tagged CombatUpdate can ever fire, structurally capping COMBAT near its "
            "combat_dormant floor for every affected scenario."
        ),
        "since_ticket": "TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY",
        "confirmed_ticket": "TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE",
    },
}


@dataclass(frozen=True)
class CeilingInfo:
    ceiling_kind: str  # "tick_budget" | "flag_gated" | "content_threshold" | "corrected"
    pillar: str
    reason: str
    evidence: str
    since_ticket: Optional[str] = None


def _load_corpus_registry() -> dict:
    if not CORPUS_REGISTRY_PATH.exists():
        return {}
    return yaml.safe_load(CORPUS_REGISTRY_PATH.read_text()) or {}


def _load_time_gates() -> dict:
    data = yaml.safe_load(DETECTION_PARAMS_PATH.read_text()) or {}
    return data.get("time_gates", {})


def tick_budget_ceilings() -> dict[tuple[str, str], CeilingInfo]:
    """Compute every (run_key, pillar) pair whose scenario tick count is <= a real time_gate
    threshold for that pillar. Deterministic — no engine run needed."""
    registry = _load_corpus_registry()
    time_gates = _load_time_gates()
    result: dict[tuple[str, str], CeilingInfo] = {}
    for run_key, entry in registry.items():
        ticks = entry.get("ticks")
        if ticks is None:
            continue
        for gate_key, pillar in TIME_GATE_PILLAR.items():
            threshold = time_gates.get(gate_key)
            if threshold is not None and ticks <= threshold:
                result[(run_key, pillar)] = CeilingInfo(
                    ceiling_kind="tick_budget",
                    pillar=pillar,
                    reason=(
                        f"scenario ticks={ticks} <= detection_params.yaml's {gate_key}="
                        f"{threshold}; the corresponding dormant/threshold-style rule risks "
                        f"firing regardless of true world behavior"
                    ),
                    evidence=f"config/simulation_quality/detection_params.yaml time_gates.{gate_key}",
                )
    return result


def _load_content_threshold_entries() -> dict[tuple[str, str], CeilingInfo]:
    if not SCORE_CEILINGS_PATH.exists():
        return {}
    data = json.loads(SCORE_CEILINGS_PATH.read_text())
    result: dict[tuple[str, str], CeilingInfo] = {}
    for entry in data.get("entries", []):
        key = (entry["run_key"], entry["pillar"]) if entry.get("run_key") else None
        info = CeilingInfo(
            ceiling_kind=entry["ceiling_kind"],
            pillar=entry["pillar"],
            reason=entry["reason"],
            evidence=entry.get("evidence", ""),
            since_ticket=entry.get("since_ticket"),
        )
        if key:
            result[key] = info
        else:
            result[("*", entry["pillar"])] = info
    return result


def lookup_ceiling(run_key: str, pillar: str) -> Optional[CeilingInfo]:
    """Look up any known ceiling/provenance classification for (run_key, pillar), checking
    tick_budget (computed), flag_gated (hand-verified table), then content_threshold/corrected
    (score_ceilings.json), in that order."""
    tick_result = tick_budget_ceilings().get((run_key, pillar))
    if tick_result:
        return tick_result

    flag_entry = FLAG_GATED_PILLAR_CEILINGS.get(pillar)
    if flag_entry:
        return CeilingInfo(
            ceiling_kind="flag_gated",
            pillar=pillar,
            reason=flag_entry["reason"],
            evidence=f"feature flag {flag_entry['flag']}",
            since_ticket=flag_entry["since_ticket"],
        )

    content_entries = _load_content_threshold_entries()
    if (run_key, pillar) in content_entries:
        return content_entries[(run_key, pillar)]
    if ("*", pillar) in content_entries:
        return content_entries[("*", pillar)]

    return None
