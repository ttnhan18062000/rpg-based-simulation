"""Tests for tools/perf/hash_callsite_inventory.py (TCK-20261003-PERF-HASH-CALLSITE-INVENTORY).

The real-source test finds the known kernel call sites by mechanism and enclosing function, never by
line number or a total count: RPG-core keeps changing both.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.perf import hash_callsite_inventory as hi

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "perf" / "hash_callsite_inventory.py"

SYNTHETIC = '''
import hashlib
from src.engine.checkpoint import CanonicalStateHasher, CanonicalHashScheduler as Sched
from src.engine import checkpoint as cp


class Kernel:
    def __init__(self):
        self._scheduler = Sched()

    def direct(self):
        return CanonicalStateHasher.get_hash(self._state)

    def guarded(self):
        if self._audit_mode and self.richness == "FULL":
            h = CanonicalStateHasher.get_hash(self._state)
        else:
            h = None
        return h

    def aliased(self):
        return Sched().compute_hash(self._state, tick=1)

    def via_module(self):
        return cp.CanonicalStateHasher.get_hash(self._state)

    def via_instance(self):
        return self._scheduler.compute_digest(self._state, tick=3)

    def fingerprinting(self):
        a = self._state.fingerprint() if self._audit_mode else None
        return a

    def shortcircuit(self):
        return self.enabled and CanonicalStateHasher.get_hash(self._state)

    def hand_rolled(self, state):
        data = CanonicalStateHasher.to_canonical_data(state)
        return hashlib.sha256(str(data).encode()).hexdigest()

    def unrelated(self, other):
        return other.get_hash()  # receiver is not a known class by name
'''


def _by_function(found):
    out = {}
    for s in found["call_sites"]:
        out.setdefault(s["enclosing_function"], []).append(s)
    return out


class TestScanSource:
    def test_direct_aliased_module_and_instance_calls_are_resolved(self):
        sites = _by_function(hi.scan_source(SYNTHETIC, "x.py"))
        assert sites["Kernel.direct"][0]["mechanism"] == "CanonicalStateHasher.get_hash"
        assert sites["Kernel.aliased"][0]["mechanism"] == "CanonicalHashScheduler.compute_hash"  # `as Sched`
        assert sites["Kernel.via_module"][0]["mechanism"] == "CanonicalStateHasher.get_hash"    # cp.Class.method
        assert sites["Kernel.via_instance"][0]["mechanism"] == "CanonicalHashScheduler.compute_digest"  # self._scheduler = Class()

    def test_guard_is_reported_as_written_and_unguarded_is_empty(self):
        sites = _by_function(hi.scan_source(SYNTHETIC, "x.py"))
        assert sites["Kernel.direct"][0]["guards"] == [] and sites["Kernel.direct"][0]["guarded"] is False
        assert sites["Kernel.guarded"][0]["guards"] == ["if self._audit_mode and self.richness == 'FULL'"]

    def test_conditional_expression_and_short_circuit_guards(self):
        sites = _by_function(hi.scan_source(SYNTHETIC, "x.py"))
        assert sites["Kernel.fingerprinting"][0]["mechanism"] == "AuthoritativeState.fingerprint"
        assert sites["Kernel.fingerprinting"][0]["guards"] == ["if self._audit_mode (conditional expression)"]
        assert sites["Kernel.shortcircuit"][0]["guards"] == ["after: self.enabled"]

    def test_hand_rolled_digest_of_canonical_data_is_listed_separately(self):
        sites = _by_function(hi.scan_source(SYNTHETIC, "x.py"))
        mechs = {s["mechanism"] for s in sites["Kernel.hand_rolled"]}
        assert mechs == {hi.DIRECT_DIGEST_MECHANISM}
        assert sites["Kernel.hand_rolled"][0]["call"] == "hashlib.sha256"

    def test_unknown_receiver_is_an_unresolved_candidate_not_a_silent_miss(self):
        found = hi.scan_source(SYNTHETIC, "x.py")
        assert [u["call"] for u in found["unresolved_candidates"]] == ["other.get_hash"]
        assert "Kernel.unrelated" not in _by_function(found)

    def test_hasher_own_implementation_is_not_a_bypass(self):
        src = (
            "import hashlib\n"
            "class CanonicalStateHasher:\n"
            "    @staticmethod\n"
            "    def get_hash(state):\n"
            "        j = CanonicalStateHasher.to_canonical_json(state)\n"
            "        return hashlib.sha256(j.encode()).hexdigest()\n"
        )
        assert hi.scan_source(src, "src/engine/checkpoint.py")["call_sites"] == []

    def test_producer_modules_mark_delegations(self):
        src = "class S:\n    def fp(self, st):\n        return CanonicalStateHasher.get_hash(st)\n"
        found = hi.scan_source(src, "src/engine/checkpoint.py")
        assert found["call_sites"][0]["kind"] == "delegation inside a mechanism"
        found = hi.scan_source(src, "src/engine/kernel.py")
        assert found["call_sites"][0]["kind"] == "caller"


class TestProducers:
    def test_digest_producers_report_algorithm_and_delegates(self):
        src = (
            "import hashlib\n"
            "class A:\n"
            "    def flat(self, s):\n"
            "        return hashlib.sha256(b'').hexdigest()\n"
            "    def light(self, s):\n"
            "        return hashlib.md5(b'').hexdigest() + CanonicalStateHasher.get_hash(s)\n"
            "    def other(self):\n"
            "        return 1\n"
        )
        got = {p["function"]: p for p in hi.scan_digest_producers(src, "m.py")}
        assert set(got) == {"A.flat", "A.light"}
        assert got["A.flat"]["hashlib_algorithms"] == ["sha256"]
        assert got["A.light"]["delegates_to"] == ["CanonicalStateHasher.get_hash"]


def _make_root(tmp_path: Path, src_text: str, test_text: str = "") -> Path:
    (tmp_path / "src" / "engine").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "engine" / "kernel.py").write_text(src_text, encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text(test_text, encoding="utf-8")
    return tmp_path


class TestReportAndCheck:
    def test_output_is_deterministic_and_has_no_timestamp(self, tmp_path):
        root = _make_root(tmp_path, SYNTHETIC, "x = State().fingerprint()\n")
        first, second = hi.to_json(hi.build_report(root)), hi.to_json(hi.build_report(root))
        assert first == second and "timestamp" not in first.lower()

    def test_tests_are_listed_as_references_not_call_sites(self, tmp_path):
        root = _make_root(tmp_path, "x = 1\n", "import a\nv = state.fingerprint()\n")
        report = hi.build_report(root)
        assert report["call_sites"] == []
        assert [t["mechanism"] for t in report["test_references"]] == ["AuthoritativeState.fingerprint"]

    def test_check_passes_on_unchanged_tree_and_ignores_line_shifts(self, tmp_path):
        root = _make_root(tmp_path, SYNTHETIC)
        committed = tmp_path / "committed.json"
        committed.write_text(hi.to_json(hi.build_report(root)), encoding="utf-8")
        assert hi.check_against(committed, hi.build_report(root)) == (0, [])
        _make_root(tmp_path, "# a new first line\n\n" + SYNTHETIC)
        assert hi.check_against(committed, hi.build_report(tmp_path))[0] == 0

    def test_check_reports_added_and_removed_call_sites(self, tmp_path):
        root = _make_root(tmp_path, SYNTHETIC)
        committed = tmp_path / "committed.json"
        committed.write_text(hi.to_json(hi.build_report(root)), encoding="utf-8")

        added = SYNTHETIC + "\n    def extra(self):\n        return CanonicalStateHasher.get_hash(self._state)\n"
        _make_root(tmp_path, added)
        code, diff = hi.check_against(committed, hi.build_report(tmp_path))
        assert code == 1 and any("call site added" in d and "Kernel.extra" in d for d in diff)

        removed = SYNTHETIC.replace("        return CanonicalStateHasher.get_hash(self._state)\n\n    def guarded", "        return None\n\n    def guarded", 1)
        _make_root(tmp_path, removed)
        code, diff = hi.check_against(committed, hi.build_report(tmp_path))
        assert code == 1 and any("call site removed" in d and "Kernel.direct" in d for d in diff)

    def test_check_with_unreadable_committed_file_is_exit_code_two(self, tmp_path):
        code, diff = hi.check_against(tmp_path / "missing.json", {})
        assert code == 2 and diff

    def test_update_doc_replaces_only_the_generated_block(self, tmp_path):
        root = _make_root(tmp_path, SYNTHETIC)
        doc = tmp_path / "doc.md"
        doc.write_text(f"hand written intro\n\n{hi.BEGIN_MARK}\nold\n{hi.END_MARK}\n\nhand written outro\n", encoding="utf-8")
        hi.update_doc(doc, hi.to_markdown_block(hi.build_report(root), "abc1234"))
        text = doc.read_text(encoding="utf-8")
        assert text.startswith("hand written intro\n") and text.endswith("hand written outro\n")
        assert "commit `abc1234`" in text and "old\n" not in text

    def test_update_doc_without_markers_fails_loudly(self, tmp_path):
        doc = tmp_path / "doc.md"
        doc.write_text("no markers\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            hi.update_doc(doc, "x")


class TestRealSource:
    def test_known_kernel_call_sites_are_found_by_mechanism_not_line(self):
        sites = hi.build_report(REPO_ROOT)["call_sites"]
        kernel = [s for s in sites if s["file"] == "src/engine/kernel.py"]
        by_fn = {}
        for s in kernel:
            by_fn.setdefault(s["enclosing_function"], set()).add(s["mechanism"])
        # PERF-M1-T03b: the kernel's digests go through the scheduler, not a direct `get_hash` call.
        assert "CanonicalHashScheduler.compute_digest" in by_fn.get("Kernel._phase_persistence", set())
        assert "CanonicalHashScheduler.compute_digest" in by_fn.get("Kernel.shutdown", set())
        assert "AuthoritativeState.fingerprint" in by_fn.get("Kernel._guard_stability", set())

    def test_real_scan_parses_everything_and_numbers_call_sites(self):
        report = hi.build_report(REPO_ROOT)
        assert report["scanned"]["unparsed_files"] == []
        ordinals = [s["ordinal"] for s in report["call_sites"]]
        assert ordinals == list(range(1, len(ordinals) + 1)) and ordinals

    def test_script_never_imports_src(self):
        probe = (
            "import runpy, sys, io, contextlib\n"
            "sys.argv = ['hash_callsite_inventory.py', '--format', 'json']\n"
            "buf = io.StringIO()\n"
            "with contextlib.redirect_stdout(buf):\n"
            "    try:\n"
            "        runpy.run_path('tools/perf/hash_callsite_inventory.py', run_name='__main__')\n"
            "    except SystemExit:\n"
            "        pass\n"
            "assert not any(m == 'src' or m.startswith('src.') for m in sys.modules), 'engine code was imported'\n"
        )
        done = subprocess.run([sys.executable, "-c", probe], cwd=REPO_ROOT, capture_output=True, text=True)
        assert done.returncode == 0, done.stderr

    def test_cli_json_is_byte_identical_and_check_exit_codes(self, tmp_path):
        cmd = [sys.executable, str(SCRIPT), "--format", "json"]
        a = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        b = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert a == b
        good = tmp_path / "good.json"
        good.write_text(a, encoding="utf-8")
        ok = subprocess.run([sys.executable, str(SCRIPT), "--check", str(good)], cwd=REPO_ROOT, capture_output=True, text=True)
        assert ok.returncode == 0, ok.stderr
        data = json.loads(a)
        data["call_sites"].pop()
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        failed = subprocess.run([sys.executable, str(SCRIPT), "--check", str(bad)], cwd=REPO_ROOT, capture_output=True, text=True)
        assert failed.returncode == 1 and "call site added" in failed.stderr
        missing = subprocess.run([sys.executable, str(SCRIPT), "--check", str(tmp_path / "nope.json")], cwd=REPO_ROOT,
                                 capture_output=True, text=True)
        assert missing.returncode == 2
