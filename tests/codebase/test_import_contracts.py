"""Tests for the import-linter config and its generated layers contract (TCK-20261004-IMPORT-LINTER-ADOPTION).

What asserts what: the real-repo tests read only committed files (the config, the registry, the baseline) and
the one fact `src/<pkg>/__init__.py` exists. They never look for a `src/` package the registry does not list,
so a PR that adds an unregistered package is not failed here (the package-registry validator reports that);
a registry row for a namespace package that is not a root in the config is.
"""
from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

from codebase.structure import import_contracts as ic
from codebase.structure.packages import LAYERS, load_rows

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG = _REPO_ROOT / ic.CONFIG_REL_PATH


def _rows(*pairs: tuple[str, str]) -> list[dict]:
    return [{"package": package, "layer": layer} for package, layer in pairs]


def _all_layers_rows() -> list[dict]:
    return _rows(*((f"pkg_{i}", layer) for i, layer in enumerate(ic.LAYER_ORDER)))


def test_layer_order_covers_exactly_the_registry_layer_vocabulary() -> None:
    """Every registry layer is ordered, once."""
    assert set(ic.LAYER_ORDER) == LAYERS and len(ic.LAYER_ORDER) == len(LAYERS)


def test_render_block_orders_layers_and_lists_each_package_once() -> None:
    """Layers come out top to bottom, siblings sorted and joined with a colon, baseline pairs ignored."""
    rows = _rows(("b", "consumer"), ("a", "consumer"), ("e", "engine"), ("f", "foundation"), ("c", "content-pipeline"), ("d", "domain"), ("s", "simulation-systems"))
    block = ic.render_block(rows, ["src.f -> src.e", "src.d -> src.b"])
    assert block.startswith(ic.BEGIN_MARKER) and block.endswith(ic.END_MARKER + "\n")
    layer_lines = [line.split('"')[1] for line in block.splitlines() if line.startswith('    "src.') and "->" not in line]
    assert layer_lines == ["src.a : src.b", "src.s", "src.e", "src.d", "src.c", "src.f"]
    assert '    "src.f -> src.e",' in block and 'unmatched_ignore_imports_alerting = "warn"' in block


def test_render_block_rejects_a_layer_the_order_does_not_know() -> None:
    """A registry layer missing from the order is an error, never skipped."""
    with pytest.raises(ValueError, match="layer order"):
        ic.render_block(_rows(("x", "stratosphere")), [])


def test_parse_violations_reads_ansi_and_terminal_wrapped_entries() -> None:
    """Colour codes, wrapped entries and repeated pairs reduce to unique module pairs."""
    output = (
        "layers\n------\n\nsrc.config is not allowed to import src.engine:\n\n"
        "\x1b[31m- src.config.profiles -> src.engine.cadence (l.5)\x1b[0m\n\n"
        "- src.domains.campaigns.orchestrator -> \nsrc.systems.social_systems.consequence_events (l.1005)\n\n"
        "- src.systems.social_systems.clan_lifecycle -> src.observability.events (l.26, \nl.66, l.102)\n\n"
        "- src.config.profiles -> src.engine.cadence (l.9)\n"
    )
    assert ic.parse_violations(output) == [
        "src.config.profiles -> src.engine.cadence",
        "src.domains.campaigns.orchestrator -> src.systems.social_systems.consequence_events",
        "src.systems.social_systems.clan_lifecycle -> src.observability.events",
    ]


def test_parse_violations_refuses_an_indirect_chain() -> None:
    """A block with more than one edge is never seeded; `seed-baseline` exits 2 for it."""
    chain = "src.a is not allowed to import src.b:\n\n- src.a.x -> src.m.y (l.3)\n  src.m.y -> src.b.z (l.9)\n"
    with pytest.raises(ValueError, match="indirect chain, baseline by hand"):
        ic.parse_violations(chain)


def test_seed_baseline_exits_2_on_an_indirect_chain(tmp_path: Path) -> None:
    """The CLI turns the refusal into exit 2 and leaves the baseline file untouched."""
    (tmp_path / "codebase/structure").mkdir(parents=True)
    for rel in (ic.CONFIG_REL_PATH, ic.BASELINE_REL_PATH, Path("codebase/structure/package_registry.jsonl")):
        (tmp_path / rel).write_text((_REPO_ROOT / rel).read_text())
    fake = tmp_path / "fake-lint-imports"
    fake.write_text("#!/bin/sh\nprintf 'Analyzed 1 files, 1 dependencies.\\n\\n- src.a.x -> src.m.y (l.3)\\n  src.m.y -> src.b.z (l.9)\\n'\n")
    fake.chmod(0o755)
    before = (tmp_path / ic.BASELINE_REL_PATH).read_text()
    assert ic.main(["--root", str(tmp_path), "seed-baseline", "--lint-imports", str(fake)]) == 2
    assert (tmp_path / ic.BASELINE_REL_PATH).read_text() == before


def test_splice_block_replaces_only_the_generated_region() -> None:
    """Hand-edited text outside the markers survives and a second splice is a no-op."""
    config = f"head = 1\n{ic.BEGIN_MARKER}\nold\n{ic.END_MARKER}\n\n[[tool.importlinter.contracts]]\nname = 'hand'\n"
    out = ic.splice_block(config, f"{ic.BEGIN_MARKER}\nnew\n{ic.END_MARKER}\n")
    assert out.startswith("head = 1\n") and "old" not in out and "new" in out and "name = 'hand'" in out
    assert ic.splice_block(out, f"{ic.BEGIN_MARKER}\nnew\n{ic.END_MARKER}\n") == out


def test_splice_block_without_markers_is_an_error() -> None:
    """A config without the markers is refused, not appended to."""
    with pytest.raises(ValueError, match="markers"):
        ic.splice_block("no markers here\n", "x\n")


def test_check_mode_fails_on_a_stale_block_and_the_rewrite_fixes_it(tmp_path: Path) -> None:
    """`--check` exits 1 on a stale block; the plain run rewrites it."""
    (tmp_path / "codebase/structure").mkdir(parents=True)
    for rel in (ic.CONFIG_REL_PATH, ic.BASELINE_REL_PATH, Path("codebase/structure/package_registry.jsonl")):
        (tmp_path / rel).write_text((_REPO_ROOT / rel).read_text())
    assert ic.main(["--root", str(tmp_path), "--check"]) == 0
    config = tmp_path / ic.CONFIG_REL_PATH
    config.write_text(config.read_text().replace("ignore_imports = [", "ignore_imports = [\n    \"src.a -> src.b\",", 1))
    assert ic.main(["--root", str(tmp_path), "--check"]) == 1
    assert ic.main(["--root", str(tmp_path)]) == 0
    assert ic.main(["--root", str(tmp_path), "--check"]) == 0


def test_check_mode_reports_could_not_run_when_the_config_is_missing(tmp_path: Path) -> None:
    """A missing config is exit 2, not a pass."""
    assert ic.main(["--root", str(tmp_path), "--check"]) == 2


def test_committed_generated_block_matches_the_registry_and_baseline() -> None:
    """The committed block equals what the generator would write now."""
    assert ic.main(["--check"]) == 0


def test_committed_baseline_is_sorted_unique_module_pairs() -> None:
    """The baseline file is sorted, unique `importer -> imported` module pairs under `src.`."""
    lines = [line for line in (_REPO_ROOT / ic.BASELINE_REL_PATH).read_text().splitlines() if line]
    assert lines == sorted(set(lines))
    assert all(line.count(" -> ") == 1 and line.startswith("src.") for line in lines)


def test_every_registry_namespace_package_is_a_root_package_in_the_config() -> None:
    """A registry row for a package with no `__init__.py` needs its own `src.<pkg>` root (a 21st fails here); `visual_assets` is the one root outside `src`."""
    roots = set(tomllib.loads(_CONFIG.read_text())["tool"]["importlinter"]["root_packages"])
    rows = load_rows(_REPO_ROOT / "codebase/structure/package_registry.jsonl", _REPO_ROOT)
    namespace = {f"src.{row['package']}" for row in rows if not (_REPO_ROOT / "src" / row["package"] / "__init__.py").exists()}
    assert roots == {"src", "visual_assets"} | namespace


def test_every_registry_package_sits_in_the_generated_layers_contract() -> None:
    """The layers contract lists every registry package, and nothing else."""
    contracts = tomllib.loads(_CONFIG.read_text())["tool"]["importlinter"]["contracts"]
    layers = next(c for c in contracts if c["id"] == "layers")["layers"]
    listed = {name.strip() for line in layers for name in line.split(":")}
    rows = load_rows(_REPO_ROOT / "codebase/structure/package_registry.jsonl", _REPO_ROOT)
    assert listed == {f"src.{row['package']}" for row in rows}


def test_contract_ids_are_unique_and_every_forbidden_contract_allows_indirect_imports() -> None:
    """Parity rows name contracts by id; the tests look at direct imports only, so indirect chains are allowed."""
    contracts = tomllib.loads(_CONFIG.read_text())["tool"]["importlinter"]["contracts"]
    ids = [c["id"] for c in contracts]
    assert len(ids) == len(set(ids)) and "layers" in ids
    assert all(c.get("allow_indirect_imports") is True for c in contracts if c["type"] == "forbidden")
    assert all(c.get("unmatched_ignore_imports_alerting") == "warn" for c in contracts)


def _fake_lint_imports(tmp_path: Path, stdout: str, exit_code: int) -> str:
    fake = tmp_path / "fake-lint-imports"
    fake.write_text(f"#!/bin/sh\ncat <<'EOF_OUT'\n{stdout}\nEOF_OUT\nexit {exit_code}\n")
    fake.chmod(0o755)
    return str(fake)


def _scratch_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "codebase/structure").mkdir(parents=True)
    for rel in (ic.CONFIG_REL_PATH, ic.BASELINE_REL_PATH, Path("codebase/structure/package_registry.jsonl")):
        (root / rel).write_text((_REPO_ROOT / rel).read_text())
    return root


def test_advisory_reports_a_broken_contract_with_one_warning_and_exits_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A broken contract is a summary line plus one ::warning::, never a failing exit (even though lint-imports exits 1)."""
    out = "Analyzed 9 files, 9 dependencies.\ncore must not import domains BROKEN\nContracts: 16 kept, 1 broken.\n"
    summary = tmp_path / "summary.md"
    code = ic.main(["--root", str(_scratch_repo(tmp_path)), "advisory", "--lint-imports", _fake_lint_imports(tmp_path, out, 1), "--summary-out", str(summary), "--annotate"])
    printed = capsys.readouterr().out
    assert code == 0
    assert printed.count("::warning::") == 1 and "16 kept, 1 broken" in printed
    assert "- broken: `core must not import domains`" in summary.read_text()


def test_advisory_is_quiet_when_every_contract_is_kept(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A clean run prints the totals and no warning."""
    code = ic.main(["--root", str(_scratch_repo(tmp_path)), "advisory", "--lint-imports", _fake_lint_imports(tmp_path, "Contracts: 17 kept, 0 broken.", 0), "--annotate"])
    printed = capsys.readouterr().out
    assert code == 0 and "17 kept, 0 broken" in printed and "::warning::" not in printed


def test_advisory_counts_stale_ignored_imports_as_a_warning(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A fixed import (an `ignore_imports` entry that no longer matches) is surfaced, not hidden."""
    out = "Warnings\n- No matches for ignored import src.a -> src.b\nContracts: 17 kept, 0 broken.\n"
    ic.main(["--root", str(_scratch_repo(tmp_path)), "advisory", "--lint-imports", _fake_lint_imports(tmp_path, out, 0), "--annotate"])
    printed = capsys.readouterr().out
    assert "1 stale ignored import(s)" in printed and printed.count("::warning::") == 1


def test_advisory_exits_0_when_lint_imports_cannot_run_or_the_summary_cannot_be_written(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing binary, garbage output and an unwritable summary file all end in exit 0 with a warning."""
    root = _scratch_repo(tmp_path)
    assert ic.main(["--root", str(root), "advisory", "--lint-imports", str(tmp_path / "missing"), "--annotate"]) == 0
    assert "could not run" in capsys.readouterr().out
    garbage = _fake_lint_imports(tmp_path, "Traceback: boom", 3)
    assert ic.main(["--root", str(root), "advisory", "--lint-imports", garbage, "--summary-out", str(tmp_path / "no/such/dir/s.md"), "--annotate"]) == 0
    printed = capsys.readouterr().out
    assert "could not run" in printed and "summary not written" in printed and "::warning::" in printed


def test_advisory_flags_a_stale_generated_block(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The step also reports a `layers` block that no longer matches the registry."""
    root = _scratch_repo(tmp_path)
    config = root / ic.CONFIG_REL_PATH
    config.write_text(config.read_text().replace("ignore_imports = [", 'ignore_imports = [\n    "src.a -> src.b",', 1))
    ic.main(["--root", str(root), "advisory", "--lint-imports", _fake_lint_imports(tmp_path, "Contracts: 17 kept, 0 broken.", 0), "--annotate"])
    printed = capsys.readouterr().out
    assert "out of date" in printed and printed.count("::warning::") == 1


def test_ci_step_is_the_last_step_of_the_package_registry_job_and_stays_non_blocking() -> None:
    """The step follows the package-registry step, keeps its own continue-on-error and never needs the job's."""
    workflow = yaml.safe_load((_REPO_ROOT / ".github/workflows/test.yml").read_text())
    steps = next(job for job in workflow["jobs"].values() if any(s.get("name") == "Package registry" for s in job["steps"]))["steps"]
    step = steps[-1]
    assert step["name"] == "Import contracts" and step["continue-on-error"] is True
    assert "codebase.structure.import_contracts advisory" in step["run"] and "--annotate" in step["run"]
    assert steps[-2]["name"] == "Package registry"


def test_make_target_runs_the_advisory_command() -> None:
    """`make import-contracts` is the local twin of the CI step."""
    result = subprocess.run(["make", "-n", "import-contracts"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True)
    assert "codebase.structure.import_contracts advisory" in result.stdout
