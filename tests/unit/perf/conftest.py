"""Keep pointed-to samples files out of reports/perf/samples/ for every unit test in this directory."""
import pytest


@pytest.fixture(autouse=True)
def _perf_samples_in_tmp(tmp_path_factory, monkeypatch):
    """A run over the embed cap writes its samples file; keep every such file out of reports/perf/samples/ (PERF_SAMPLES_DIR)."""
    monkeypatch.setenv("PERF_SAMPLES_DIR", str(tmp_path_factory.mktemp("perf_samples")))
