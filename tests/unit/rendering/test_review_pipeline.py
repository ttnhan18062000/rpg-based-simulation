"""Tests for src.rendering.review_pipeline's should_escalate, Tier1Digest/
digest_to_json, and run_tier0_tier1_pipeline orchestration.

TCK-20260821-VISUAL-AGENT-REVIEW. Mirrors test_grading.py's/test_render_core.py's
fixture conventions (synthetic GradeConfig via a local `_make_config` helper, `tmp_path`
for base_dir).

Per test_plan.md test 6 (`test_agent_review_output_contract_shape`) and plan.md Step 6
item 7: this ticket deliberately does NOT add a Python-side output-skeleton helper for
the reviewing agent's findings table -- that structured verdict shape is owned entirely
by `.claude/agents/world-render-reviewer.md`'s own prompt body, matching
`simulation-analyst.md`'s own precedent. AC #4's real verification is a manual
read-through of the finished agent file against `simulation-analyst.md`'s `## Output`
shape; no pytest test exists for it here, and none should.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import struct
import zlib
from pathlib import Path

import pytest

from src.core.state import AuthoritativeState
from src.rendering.grading import GradeConfig, HardRuleConfig, HardRuleResult, SoftRuleConfig
from src.rendering.review_pipeline import (
    Tier1Digest,
    digest_to_json,
    run_tier0_tier1_pipeline,
    should_escalate,
)

_REVIEW_PIPELINE_MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "rendering" / "review_pipeline.py"
)


def _make_config(
    grade_thresholds: dict[str, float] | None = None,
    hard_rules: dict[str, HardRuleConfig] | None = None,
    soft_rules: dict[str, SoftRuleConfig] | None = None,
) -> GradeConfig:
    return GradeConfig(
        grade_thresholds=grade_thresholds
        if grade_thresholds is not None
        else {"S": 2.0, "A": 0.5, "B": 0.0, "C": -0.5, "D": -1.0},
        hard_rules=hard_rules
        if hard_rules is not None
        else {"fully_connected": HardRuleConfig(pass_delta=1.0, fail_delta=-1.0)},
        soft_rules=soft_rules
        if soft_rules is not None
        else {
            "fill_ratio_healthy_band": SoftRuleConfig(
                low=0.0, healthy_low=0.3, healthy_high=0.85, high=1.0,
                peak_delta=1.0, min_delta=-1.0,
            )
        },
    )


def _read_ihdr(png_bytes: bytes) -> tuple[int, int]:
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    (length,) = struct.unpack(">I", png_bytes[offset : offset + 4])
    tag = png_bytes[offset + 4 : offset + 8]
    assert tag == b"IHDR"
    data = png_bytes[offset + 8 : offset + 8 + length]
    (crc,) = struct.unpack(">I", png_bytes[offset + 8 + length : offset + 12 + length])
    assert crc == zlib.crc32(tag + data) & 0xFFFFFFFF
    width, height = struct.unpack(">II", data[:8])
    return width, height


# --- test 1: should_escalate ---------------------------------------------------------

_ESCALATE_CASES = [
    ([HardRuleResult(name="fully_connected", passed=True, delta=1.0)], "A", False),
    ([HardRuleResult(name="fully_connected", passed=False, delta=-1.0)], "A", True),
    ([HardRuleResult(name="fully_connected", passed=True, delta=1.0)], "D", True),
    ([HardRuleResult(name="fully_connected", passed=True, delta=1.0)], "F", True),
    ([HardRuleResult(name="fully_connected", passed=True, delta=1.0)], "C", False),
]


@pytest.mark.parametrize("hard_results,grade,expected", _ESCALATE_CASES)
def test_should_escalate_composes_hard_rule_failure_and_grade(hard_results, grade, expected):
    assert should_escalate(hard_results, grade) is expected


# --- test 2: Tier1Digest / digest_to_json ---------------------------------------------

def _make_digest() -> Tier1Digest:
    return Tier1Digest(
        world_id="test_world",
        seed=42,
        tick=0,
        grade="B",
        combined_score=0.25,
        hard_rule_results=({"name": "fully_connected", "passed": True, "delta": 1.0},),
        soft_rule_results=({"name": "fill_ratio_healthy_band", "raw_value": 0.5, "delta": 0.5},),
        terrain_histogram={"PLAIN": 16},
        entity_count=2,
        connectivity_component_count=1,
        connectivity_percent_reachable=100.0,
        flagged_shape_components=({"terrain_type": "FOREST", "bbox": (0, 0, 4, 4), "fill_ratio": 1.0},),
        escalate=False,
        plain_render_path="/tmp/run/renders/test_world_tick0.png",
        annotated_render_path=None,
    )


def test_tier1_digest_is_json_serializable_and_round_trips():
    digest = _make_digest()

    payload = digest_to_json(digest)
    round_tripped = json.loads(payload)

    field_names = {f.name for f in dataclasses.fields(Tier1Digest)}
    assert field_names <= set(round_tripped.keys())
    assert round_tripped["world_id"] == "test_world"
    assert round_tripped["flagged_shape_components"][0]["terrain_type"] == "FOREST"
    assert round_tripped["annotated_render_path"] is None


# --- test 3: non-escalating pipeline writes zero PNG files ----------------------------

def _build_fully_connected_healthy_state() -> AuthoritativeState:
    terrain = {}
    for x in range(4):
        for y in range(4):
            terrain[(x, y)] = "PLAIN"
    return AuthoritativeState(tick=0, seed=42, entities={}, terrain=terrain)


def test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_not_escalated(tmp_path):
    state = _build_fully_connected_healthy_state()
    config = _make_config()  # fully_connected pass_delta=1.0 -> combined_score=1.0 -> grade "A"

    digest = run_tier0_tier1_pipeline(
        state, "test_world", str(tmp_path), "test_run", grade_config=config
    )

    assert digest.escalate is False
    assert digest.annotated_render_path is None
    assert digest.grade not in ("D", "F")

    png_files = list(Path(tmp_path).glob("**/*.png"))
    assert png_files == [], (
        "no PNG file may exist anywhere under the output tree when escalate is False -- "
        "this is the load-bearing anti-drift guard for AC #1"
    )


# --- test 4: escalating pipeline writes the annotated PNG ------------------------------

def _build_disconnected_state() -> AuthoritativeState:
    terrain = {}
    for x in range(3):
        for y in range(3):
            terrain[(x, y)] = "PLAIN"
    for x in range(10, 13):
        for y in range(10, 13):
            terrain[(x, y)] = "PLAIN"
    return AuthoritativeState(tick=0, seed=42, entities={}, terrain=terrain)


def test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_escalated(tmp_path):
    state = _build_disconnected_state()
    config = _make_config()

    digest = run_tier0_tier1_pipeline(
        state, "test_world", str(tmp_path), "test_run", grade_config=config
    )

    assert digest.escalate is True
    assert digest.annotated_render_path is not None

    out_path = Path(digest.annotated_render_path)
    assert out_path.is_file()

    xs = [p[0] for p in state.terrain.keys()]
    ys = [p[1] for p in state.terrain.keys()]
    grid_w = max(xs) - min(xs) + 1
    grid_h = max(ys) - min(ys) + 1
    margin = 20
    scale = 6

    width, height = _read_ihdr(out_path.read_bytes())
    assert width == grid_w * scale + margin
    assert height == grid_h * scale + margin


# --- test 5: digest golden-hash determinism, exercising the flagged-component sort ----

def _build_state_with_two_flagged_shape_components() -> AuthoritativeState:
    # regression: TCK-20260821-VISUAL-AGENT-REVIEW -- two distinct, non-excluded terrain
    # types (FOREST, CAVE), each a solid 5x5 (25-tile, >= min_size=20) rectangle with
    # fill_ratio == 1.0, both outside the [0.3, 0.85] healthy band configured below --
    # engineered so flagged_shape_components has >= 2 entries and actually exercises the
    # explicit sorted(..., key=lambda d: (d["terrain_type"], d["bbox"])) fix
    # (Decision 5), rather than passing vacuously with 0-1 elements.
    terrain = {}
    for x in range(4):
        for y in range(4):
            terrain[(x, y)] = "PLAIN"
    for x in range(10, 15):
        for y in range(10, 15):
            terrain[(x, y)] = "FOREST"
    for x in range(20, 25):
        for y in range(20, 25):
            terrain[(x, y)] = "CAVE"
    return AuthoritativeState(tick=0, seed=42, entities={}, terrain=terrain)


@pytest.mark.regression
def test_tier1_digest_golden_hash_field_identical_across_three_independent_runs(tmp_path):
    # regression: TCK-20260821-VISUAL-AGENT-REVIEW
    config = _make_config()
    hashes = []
    for _ in range(3):
        state = _build_state_with_two_flagged_shape_components()  # independently constructed
        # base_dir/run_id are fixed across all three runs (not per-iteration) -- the
        # digest embeds annotated_render_path/plain_render_path, both of which are
        # derived from base_dir/run_id, so a varying run_id would break the
        # byte-identical comparison for reasons unrelated to the determinism claim
        # under test here.
        digest = run_tier0_tier1_pipeline(
            state, "test_world", str(tmp_path), "test_run", grade_config=config
        )
        assert len(digest.flagged_shape_components) >= 2
        payload = digest_to_json(digest)
        hashes.append(hashlib.sha256(payload.encode("utf-8")).hexdigest())

    assert hashes[0] == hashes[1] == hashes[2]


# --- test 6: architecture guard --------------------------------------------------------

def test_review_pipeline_module_does_not_subclass_pillar_scorer_or_import_simulation_quality_or_observability_events():
    tree = ast.parse(_REVIEW_PIPELINE_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, "review_pipeline.py must not subclass PillarScorer"
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"review_pipeline.py must not import {name}"
            assert "observability.events" not in name, f"review_pipeline.py must not import {name}"
