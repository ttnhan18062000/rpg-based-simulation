import pytest
from src.core.state import RegionState
from src.world.transformation import TransformationService

def test_forest_to_burnt_forest():
    region = RegionState(
        id="r1", name="R1", bounds=(0,0,10,10),
        kind="FOREST",
        trauma_score=60.0 # Threshold is 50
    )
    new_region = TransformationService.apply_transformation(region)
    assert new_region.kind == "BURNT_FOREST"

def test_forest_to_wasteland():
    region = RegionState(
        id="r1", name="R1", bounds=(0,0,10,10),
        kind="FOREST",
        trauma_score=110.0,
        calamity_intensity=0.6 # Thresholds are 100 trauma and 0.5 calamity
    )
    new_region = TransformationService.apply_transformation(region)
    assert new_region.kind == "WASTELAND"

def test_no_transformation_under_threshold():
    region = RegionState(
        id="r1", name="R1", bounds=(0,0,10,10),
        kind="FOREST",
        trauma_score=40.0
    )
    new_region = TransformationService.apply_transformation(region)
    assert new_region.kind == "FOREST"

def test_mountain_to_frozen_peaks():
    region = RegionState(
        id="r1", name="R1", bounds=(0,0,10,10),
        kind="MOUNTAIN",
        active_modifiers=["FROST"]
    )
    new_region = TransformationService.apply_transformation(region)
    assert new_region.kind == "FROZEN_PEAKS"
