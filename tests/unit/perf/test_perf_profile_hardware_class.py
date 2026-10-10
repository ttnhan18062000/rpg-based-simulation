"""A PERF_* profile's hardware class is detected, not hard-coded (TCK-20261010-PERF-M2-T02B-RECORD, PERF-M2 OD-4)."""
from __future__ import annotations

import pytest

from src.certification.models import HardwareClass as DetectedClass
from src.config.profiles import HardwareClass
from src.perf.profiles import make_perf_profile


@pytest.mark.parametrize("detected, expected", [(DetectedClass.CLASS_A, HardwareClass.CLASS_A), (DetectedClass.CLASS_B, HardwareClass.CLASS_B), (DetectedClass.CLASS_C, HardwareClass.CLASS_C)])
def test_make_perf_profile_takes_the_detected_hardware_class(monkeypatch, detected, expected) -> None:
    monkeypatch.setattr("src.perf.profiles.HardwareClassifier.detect_class", staticmethod(lambda: detected))
    assert make_perf_profile("T", ram_mb=512, workers=0).hardware_class is expected


def test_no_hard_coded_class_a_remains() -> None:
    import inspect

    import src.perf.profiles as module

    assert "HardwareClass.CLASS_A" not in inspect.getsource(module)
