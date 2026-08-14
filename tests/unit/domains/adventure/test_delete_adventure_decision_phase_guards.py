"""
tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py

Architecture/doc guards for TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (plan.md Step 8),
covering AC2/AC3/AC5:
- AC2: AdventureDecisionPhase and its pipeline.py registration are gone.
- AC3: _resolve_cognition_profile_id/_supports_adventure_routing exist byte-identical (same
  signature) in AdventureGoalScorer's module.
- AC5: STRAT-236's v2_evidence and adventure_contract.md's Engine Phase section no longer
  reference AdventureDecisionPhase/phase.py as the live mechanism.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import yaml

import src.engine.pipeline as pipeline_module
from src.ai.goals import adventure_scorer as scorer_module


def test_pipeline_module_has_no_adventure_decision_phase_reference():
    """AC2 regression guard: catches any future reintroduction of the deleted phase into the
    live pipeline."""
    source = inspect.getsource(pipeline_module)
    assert "AdventureDecisionPhase" not in source


def test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source():
    """AC3: _resolve_cognition_profile_id/_supports_adventure_routing exist in
    src.ai.goals.adventure_scorer with the identical signature they had in the deleted
    phase.py. "Byte-identical internals" is ultimately proven by the behavioral tests in
    tests/unit/domains/adventure/test_eligibility_cognition_profile.py passing (the functions
    physically moved files and cannot be textually diffed against deleted source) -- this guard
    pins the API shape (existence + signature) so a future edit cannot silently change the
    call contract without also updating that behavioral suite."""
    assert hasattr(scorer_module, "_resolve_cognition_profile_id")
    assert hasattr(scorer_module, "_supports_adventure_routing")

    resolve_sig = inspect.signature(scorer_module._resolve_cognition_profile_id)
    assert list(resolve_sig.parameters) == ["entity"]

    supports_sig = inspect.signature(scorer_module._supports_adventure_routing)
    assert list(supports_sig.parameters) == ["entity", "cache"]


def test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase():
    """AC5: STRAT-236's v2_evidence must no longer cite AdventureDecisionPhase's own
    (now-deleted) pre-filter as a separate, still-active gate."""
    ledger_path = Path("docs/parity_ledger/strategic_cognition.yaml")
    entries = yaml.safe_load(ledger_path.read_text())
    strat_236 = next(e for e in entries if isinstance(e, dict) and e.get("id") == "STRAT-236")

    assert "AdventureDecisionPhase" not in strat_236["v2_evidence"]
    assert "phase.py:129" not in strat_236["v2_evidence"]


def test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase():
    """AC5: adventure_contract.md's Engine Phase section must describe the tier-5
    GoalRegistry/AdventureGoalScorer mechanism as the live path, not AdventureDecisionPhase."""
    contract_path = Path("docs/simulation/domains/adventure_contract.md")
    text = contract_path.read_text()

    engine_phase_start = text.index("## Engine Phase")
    next_heading = text.index("\n## ", engine_phase_start + 1)
    engine_phase_section = text[engine_phase_start:next_heading]

    assert "AdventureDecisionPhase" not in engine_phase_section
