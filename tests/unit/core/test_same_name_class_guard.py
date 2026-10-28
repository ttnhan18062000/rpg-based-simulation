"""Guard: a top-level class name defined in two ``src/`` modules must be recorded here with a reason.

Two classes with one name let an import pick the wrong one without an error (the dead
``SkillScalingService`` twin sat next to the live one for months). A new duplicate name fails this
test until it is classified below; a recorded name that is no longer duplicated also fails, so the
table cannot rot. Mechanism-shaped names (the suffixes below) need a reason that names each side's
role, not just a classification.

Lives under tests/unit because testing-planner was not running when it was written; testing-planner
may move it to tests/architecture.
"""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

SRC = Path(__file__).resolve().parents[3] / "src"
MECHANISM_SUFFIXES = ("Service", "System", "Gate", "Phase", "Evaluator", "Resolver", "Manager", "Registry")

INTENTIONAL = "intentional"  # different shape or layer, same word
CONFUSABLE = "confusable"  # different referent a reader can mix up; no rename decided
DRIFT_RISK = "drift-risk"  # one concept copied; the copies can drift
KEEP = "keep-with-reason"  # mechanism-shaped, both kept on purpose

DUPLICATE_NAMES: Dict[str, Tuple[str, str]] = {
    # Mechanism-shaped: both sides kept, each with a stated role.
    "ItemRegistry": (
        KEEP,
        "src/core/items.py is the static registry and src/core/registries.py the catalog-mode one: the same data, "
        "different failure semantics for an unknown id. Kept on purpose (TCK-20260914, user-approved).",
    ),
    "CapacityService": (
        KEEP,
        "src/strategy/capacity.py ENFORCES the cap in the live pipeline (capacity_enforcement phase); "
        "src/strategy/cognition_capacity.py DERIVES a profile (hunger halving the capacity) and is not wired to "
        "the tick. Different roles, not twins; the unwired derivation is TCK-20261027-HUNGER-CAPACITY-DERIVATION-HAS-NO-LIVE-CALLER.",
    ),
    # Not mechanism-shaped.
    "AnalysisContext": (INTENTIONAL, "anomaly pipeline context vs the understanding-layer analyzers' context"),
    "AnomalyRecord": (INTENTIONAL, "domain record in the rules engine vs warehouse row"),
    "BehaviorChangeProofDetector": (INTENTIONAL, "campaign-side detector vs observability pattern detector"),
    "BudgetCheckResult": (INTENTIONAL, "certification artifact budget vs lab guardrails"),
    "ConfidenceLevel": (INTENTIONAL, "two enums in two analyzers"),
    "ErrorResponse": (DRIFT_RISK, "identical `detail` model copied into three route modules"),
    "HardwareClass": (DRIFT_RISK, "certification/models.py and config/profiles.py define the same members, each with its own readers"),
    "InformationQuery": (INTENTIONAL, "domain schema vs world provider"),
    "ItemDefinition": (INTENTIONAL, "content catalog schema vs runtime item template"),
    "KnowledgeFact": (INTENTIONAL, "persisted self-model fact vs provider DTO"),
    "MetricWindowRecord": (INTENTIONAL, "metric recorder record vs warehouse row"),
    "ObservabilityMode": (CONFUSABLE, "8 operational modes (observability/config.py) vs 4 backpressure states (event_recorder.py)"),
    "QuestTemplate": (INTENTIONAL, "three unrelated definitions (generator, templates, world system)"),
    "RuntimeProfile": (INTENTIONAL, "config profile vs feature-pack profile"),
    "SkillDefinition": (INTENTIONAL, "live src/core/skills.py vs genetics' own record"),
    "SocialScorer": (INTENTIONAL, "goal scorer vs SimQ pillar scorer"),
    "ValidationIssue": (INTENTIONAL, "content validator vs worldbuilding validator"),
    "ValidationResult": (INTENTIONAL, "baseline-evolution quality result vs scenario feature validator"),
}


def _duplicated_names() -> Dict[str, List[str]]:
    defs: Dict[str, List[str]] = defaultdict(list)
    for path in sorted(SRC.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                defs[node.name].append(str(path.relative_to(SRC.parent)))
    return {name: mods for name, mods in defs.items() if len(mods) > 1}


def test_every_duplicated_class_name_is_recorded():
    found = _duplicated_names()
    unrecorded = sorted(set(found) - set(DUPLICATE_NAMES))
    assert not unrecorded, (
        "top-level class name defined in two src/ modules and not recorded in DUPLICATE_NAMES: "
        + ", ".join(f"{n} {found[n]}" for n in unrecorded)
    )


def test_recorded_names_are_still_duplicated():
    stale = sorted(set(DUPLICATE_NAMES) - set(_duplicated_names()))
    assert not stale, f"recorded but no longer defined twice (remove the row): {stale}"


@pytest.mark.parametrize("name", sorted(DUPLICATE_NAMES))
def test_each_record_has_a_reason_and_mechanism_shaped_names_are_kept_with_reason(name):
    classification, reason = DUPLICATE_NAMES[name]
    assert classification in {INTENTIONAL, CONFUSABLE, DRIFT_RISK, KEEP}
    assert len(reason) > 30 or classification != KEEP, name
    if name.endswith(MECHANISM_SUFFIXES):
        assert classification == KEEP and len(reason) > 80, f"{name} is mechanism-shaped: name each side's role"
