"""Tests for the import-linter config and its generated layers contract (TCK-20261004-IMPORT-LINTER-ADOPTION).

What asserts what: the real-repo tests read only committed files (the config, the registry, the baseline) and
the one fact `src/<pkg>/__init__.py` exists. They never look for a `src/` package the registry does not list,
so a PR that adds an unregistered package is not failed here (the package-registry validator reports that);
a registry row for a namespace package that is not a root in the config is.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

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
    """A registry row for a package with no `__init__.py` needs its own `src.<pkg>` root (a 21st fails here)."""
    roots = set(tomllib.loads(_CONFIG.read_text())["tool"]["importlinter"]["root_packages"])
    rows = load_rows(_REPO_ROOT / "codebase/structure/package_registry.jsonl", _REPO_ROOT)
    namespace = {f"src.{row['package']}" for row in rows if not (_REPO_ROOT / "src" / row["package"] / "__init__.py").exists()}
    assert roots == {"src"} | namespace


def test_every_registry_package_sits_in_the_generated_layers_contract() -> None:
    """The layers contract lists every registry package, and nothing else."""
    contracts = tomllib.loads(_CONFIG.read_text())["tool"]["importlinter"]["contracts"]
    layers = next(c for c in contracts if c["id"] == "layers")["layers"]
    listed = {name.strip() for line in layers for name in line.split(":")}
    rows = load_rows(_REPO_ROOT / "codebase/structure/package_registry.jsonl", _REPO_ROOT)
    assert listed == {f"src.{row['package']}" for row in rows}
