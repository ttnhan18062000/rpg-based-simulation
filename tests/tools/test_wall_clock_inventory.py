"""Tests for tools/perf/wall_clock_inventory.py (TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY).

The real-source test finds the reads behind the three PERF-D1 inputs by enclosing function name, never
by line number or a total count: RPG-core keeps changing both.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.perf import wall_clock_inventory as wi

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "perf" / "wall_clock_inventory.py"

SYNTHETIC = '''
import os
import time
import datetime as dt
import datetime
import psutil
import gc
from time import perf_counter as pc
from datetime import datetime as DT
from os import getenv


class Kernel:
    def __init__(self):
        self._p = psutil.Process(os.getpid())
        self.started = time.time()

    def direct(self):
        return time.perf_counter_ns()

    def aliased(self):
        return pc()

    def module_alias(self):
        return dt.datetime.now()

    def attribute_chain(self):
        return datetime.datetime.now()

    def from_import_class(self):
        return DT.utcnow()

    def guarded(self, audit):
        if not audit and self.tick > 5:
            return time.monotonic()
        return 0.0

    def cond_expr(self, audit):
        return 0.0 if audit else time.process_time()

    def rss(self):
        return self._p.memory_info().rss

    def host(self):
        return os.cpu_count(), os.getloadavg(), psutil.cpu_count(), gc.get_count()

    def env(self):
        a = os.environ.get("FOO_MODE", "x")
        b = os.environ["BAR_LEVEL"]
        c = getenv("BAZ")
        return a, b, c

    def unknown_receiver(self, clock):
        return clock.now(), self._clock.perf_counter()

    def not_a_read(self):
        return time.sleep(0)
'''


def _scan(source: str, rel: str = "src/x/mod.py"):
    return wi.scan_source(source, rel)


def _by_fn(found, function):
    return [r for r in found["reads"] if r["enclosing_function"] == function]


def test_direct_alias_and_chain_forms_resolve_to_canonical_sources():
    found = _scan(SYNTHETIC)
    assert [r["source"] for r in _by_fn(found, "Kernel.direct")] == ["time.perf_counter_ns"]
    assert [r["source"] for r in _by_fn(found, "Kernel.aliased")] == ["time.perf_counter"]
    assert [r["source"] for r in _by_fn(found, "Kernel.module_alias")] == ["datetime.datetime.now"]
    assert [r["source"] for r in _by_fn(found, "Kernel.attribute_chain")] == ["datetime.datetime.now"]
    assert [r["source"] for r in _by_fn(found, "Kernel.from_import_class")] == ["datetime.datetime.utcnow"]
    assert all(r["receiver_resolved_by_name"] for r in found["reads"])


def test_source_kinds():
    found = _scan(SYNTHETIC)
    kinds = {r["source"]: r["kind"] for r in found["reads"]}
    assert kinds["time.perf_counter_ns"] == wi.WALL
    assert kinds["time.process_time"] == wi.CPU
    assert kinds["os.cpu_count"] == wi.HOST
    assert kinds["os.getloadavg"] == wi.HOST
    assert kinds["gc.get_count"] == wi.MEM
    assert kinds["psutil.cpu_count"] == wi.HOST
    assert kinds["psutil.Process.memory_info"] == wi.MEM
    assert kinds["os.getenv"] == wi.ENV


def test_guards_are_reported_as_written_inside_the_function_only():
    found = _scan(SYNTHETIC)
    (guarded,) = _by_fn(found, "Kernel.guarded")
    assert guarded["guards"] == ["if not audit and self.tick > 5"]
    assert guarded["guarded"] is True
    (cond,) = _by_fn(found, "Kernel.cond_expr")
    assert cond["guards"] == ["else of: audit (conditional expression)"]
    (plain,) = _by_fn(found, "Kernel.direct")
    assert plain["guards"] == [] and plain["guarded"] is False


def test_environment_reads_record_the_variable_name():
    found = _scan(SYNTHETIC)
    env = {r["source"]: r["env_var"] for r in _by_fn(found, "Kernel.env")}
    assert env == {"os.environ.get": "FOO_MODE", "os.environ[...]": "BAR_LEVEL", "os.getenv": "BAZ"}


def test_unresolved_receivers_are_listed_not_guessed():
    found = _scan(SYNTHETIC)
    calls = sorted(u["call"] for u in found["unresolved_candidates"])
    assert calls == ["clock.now", "self._clock.perf_counter"]
    assert not [r for r in found["reads"] if r["enclosing_function"] == "Kernel.unknown_receiver"]


def test_calls_that_are_not_reads_are_ignored():
    assert not _by_fn(_scan(SYNTHETIC), "Kernel.not_a_read")


def test_modules_with_no_candidate_text_are_skipped_without_parsing():
    assert wi.scan_source("this is not python ((", "src/x/y.py") == {"reads": [], "unresolved_candidates": []}


def _make_tree(tmp_path: Path, files: dict) -> Path:
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


TREE = {
    "src/__init__.py": "",
    "src/engine/__init__.py": "",
    "src/engine/kernel.py": "import time\nfrom src.engine import helper\n\ndef tick():\n    return time.perf_counter_ns()\n",
    "src/engine/helper.py": "from src.core.clock import read\n",
    "src/core/__init__.py": "",
    "src/core/clock.py": "import time\n\ndef read():\n    return time.time()\n",
    "src/api/__init__.py": "",
    "src/api/routes.py": "import time\n\ndef handler():\n    return time.time()\n",
}


def test_reachability_follows_the_import_graph_from_the_kernel(tmp_path):
    report = wi.build_report(_make_tree(tmp_path, TREE))
    by_file = {r["file"]: r["reachable_from_kernel"] for r in report["reads"]}
    assert by_file["src/engine/kernel.py"] is True
    assert by_file["src/core/clock.py"] is True
    assert by_file["src/api/routes.py"] is False


def test_output_is_ordered_and_numbered(tmp_path):
    report = wi.build_report(_make_tree(tmp_path, TREE))
    keys = [(r["file"], r["line"]) for r in report["reads"]]
    assert keys == sorted(keys)
    assert [r["ordinal"] for r in report["reads"]] == list(range(1, len(keys) + 1))


def test_check_passes_on_identical_tree_and_ignores_line_shifts(tmp_path):
    root = _make_tree(tmp_path / "a", TREE)
    committed = tmp_path / "report.json"
    committed.write_text(wi.to_json(wi.build_report(root)), encoding="utf-8")
    assert wi.check_against(committed, wi.build_report(root)) == (0, [])
    shifted = dict(TREE)
    shifted["src/core/clock.py"] = "import time\n\n\n\ndef read():\n    return time.time()\n"
    live = wi.build_report(_make_tree(tmp_path / "b", shifted))
    assert wi.check_against(committed, live) == (0, [])


def test_check_fails_when_a_read_is_added_or_removed(tmp_path):
    root = _make_tree(tmp_path / "a", TREE)
    committed = tmp_path / "report.json"
    committed.write_text(wi.to_json(wi.build_report(root)), encoding="utf-8")
    added = dict(TREE)
    added["src/core/clock.py"] += "\ndef more():\n    return time.monotonic()\n"
    code, diff = wi.check_against(committed, wi.build_report(_make_tree(tmp_path / "b", added)))
    assert code == 1 and any(line.startswith("read added") for line in diff)
    removed = dict(TREE)
    removed["src/core/clock.py"] = "def read():\n    return 0\n"
    code, diff = wi.check_against(committed, wi.build_report(_make_tree(tmp_path / "c", removed)))
    assert code == 1 and any(line.startswith("read removed") for line in diff)


def test_check_reports_unreadable_committed_file(tmp_path):
    code, diff = wi.check_against(tmp_path / "missing.json", {"reads": [], "unresolved_candidates": []})
    assert code == 2 and "cannot read" in diff[0]


def test_update_doc_rewrites_only_the_generated_block(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text(f"before\n{wi.BEGIN_MARK}\nold\n{wi.END_MARK}\nafter\n", encoding="utf-8")
    wi.update_doc(doc, f"{wi.BEGIN_MARK}\nnew\n{wi.END_MARK}")
    assert doc.read_text(encoding="utf-8") == f"before\n{wi.BEGIN_MARK}\nnew\n{wi.END_MARK}\nafter\n"


def test_update_doc_refuses_a_document_without_markers(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("no markers\n", encoding="utf-8")
    try:
        wi.update_doc(doc, "x")
    except SystemExit as exc:
        assert "no generated-block markers" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit")


def test_real_source_parses_and_finds_the_three_perf_d1_reads_by_function():
    report = wi.build_report(REPO_ROOT)
    assert report["scanned"]["unparsed_files"] == []

    def functions(file, source):
        return {r["enclosing_function"] for r in report["reads"] if r["file"] == file and r["source"] == source}

    kernel = "src/engine/kernel.py"
    assert "Kernel._phase_resolution" in functions(kernel, "time.perf_counter_ns")  # mid-tick cutoff
    assert "Kernel._phase_cleanup" in functions(kernel, "time.perf_counter_ns")  # end-of-tick compute time
    assert "Kernel._tick_once_inner" in functions(kernel, "time.perf_counter_ns")  # phase stamps
    assert "SignalCollector.collect_platform_signals" in functions(
        "src/engine/observability.py", "psutil.Process.memory_info"
    )  # RSS read behind the governor's memory input
    assert all(r["reachable_from_kernel"] for r in report["reads"] if r["file"] == kernel)


def test_cli_runs_are_byte_identical_and_do_not_import_src():
    def run(fmt):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--format", fmt],
            check=True, capture_output=True, text=True, cwd=REPO_ROOT,
        ).stdout

    assert run("json") == run("json")
    assert run("md") == run("md")
    assert json.loads(run("json"))["reads"]
    probe_code = (
        "import contextlib, io, runpy, sys\n"
        "sys.argv = ['x', '--format', 'json']\n"
        "with contextlib.redirect_stdout(io.StringIO()):\n"
        "    try:\n"
        "        runpy.run_path('tools/perf/wall_clock_inventory.py', run_name='__main__')\n"
        "    except SystemExit:\n"
        "        pass\n"
        "print(any(m == 'src' or m.startswith('src.') for m in sys.modules))\n"
    )
    probe = subprocess.run([sys.executable, "-c", probe_code], capture_output=True, text=True, cwd=REPO_ROOT)
    assert probe.stdout.strip().endswith("False"), probe.stderr
