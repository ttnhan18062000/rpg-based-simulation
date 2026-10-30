"""Keep pointed-to samples files out of reports/perf/samples/ for every unit test in this directory."""
import pytest


@pytest.fixture(autouse=True)
def _perf_samples_in_tmp(tmp_path_factory, monkeypatch):
    """A run over the embed cap writes its samples file; keep every such file out of reports/perf/samples/ (PERF_SAMPLES_DIR)."""
    monkeypatch.setenv("PERF_SAMPLES_DIR", str(tmp_path_factory.mktemp("perf_samples")))


@pytest.fixture(autouse=True)
def _no_real_run_watch(monkeypatch):
    """``record`` checks a pinned run for foreign load through /proc and the cgroup; a unit test drives it in-process whatever pins pytest."""
    try:
        from tools.perf import rerun_baselines as rr
    except ImportError:
        return

    class _Unpinned:
        def start(self) -> None:
            return None

        def finish(self):
            return None

    monkeypatch.setattr(rr, "new_run_watch", _Unpinned)
