import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from tests.parity.test_parity_regional_sovereignty import test_trauma_accumulation, base_region
from src.core.state import RegionState

reg = RegionState(
    id="wilderness",
    name="The Wilds",
    bounds=(0, 0, 100, 100),
    hazard_level=0.0,
    trauma_score=0.0
)

try:
    test_trauma_accumulation(reg)
    print("Test passed!")
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
