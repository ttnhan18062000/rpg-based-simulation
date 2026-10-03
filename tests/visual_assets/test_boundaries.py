"""Architecture guard for `visual_assets/`: layering, no `src` coupling, no write path into the catalog.

Rules come from docs/plans/visual-asset-foundation/README.md ("Layering rules"). The checkers are pure
functions over (relative path, source text), so the same code that guards the real tree is also tested
against planted violations (see `test_planted_*`).

No Aseprite needed; runs in CI.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "visual_assets"
SRC = REPO / "src"

LEAVES = {"config", "errors", "colors"}

# layer of the importing module -> layers it may import (inside visual_assets.drawing).
# Documented deviation from the structure doc's table: `technique` may also import the leaf modules
# `errors` and `colors` (it raises AdapterError and parses colours); it still imports no I/O layer.
DRAWING_ALLOWED: dict[str, set[str]] = {
    "config": set(),
    "errors": set(),
    "colors": {"errors"},
    "technique": {"technique", "errors", "colors"},
    "schema": {"schema", "config", "errors", "colors"},
    "backend": {"backend", "config", "errors"},
    "workspace": {"workspace", "config", "errors"},
    "api": {"api", "schema", "backend", "workspace", "config", "errors", "colors"},
    "compose": {"compose", "api", "technique", "config", "errors", "colors"},
    "handoff": {"handoff", "api", "config", "errors", "colors"},  # + store.contracts (below)
    "server": {"server", "api", "compose", "handoff", "config", "errors", "colors"},
    "pin": set(),
    "__init__": {"api", "errors"},
}

# store.* may import only store.*; `store.build` may also use the shared sandbox (later ticket).
STORE_EXTRA = {"build": {"visual_assets.drawing.backend.sandbox"}}

# layer of a store module -> store layers it may import. A store layer not listed here fails the test, so each
# later ticket must add its own row. Documented deviation from the structure doc (`contracts -> pydantic only`):
# `contracts` also imports the store leaves `identities`, `errors`, `config`; `identities` imports `errors`
# (its helpers raise `IdentityError`).
STORE_ALLOWED: dict[str, set[str]] = {
    "__init__": set(),
    "config": set(),
    "errors": set(),
    "identities": {"identities", "errors"},
    "contracts": {"contracts", "identities", "errors", "config"},
    "catalog": {"catalog", "contracts", "identities", "errors", "config"},
    # intake does file I/O (the quarantine) but takes timestamps as parameters; only `cli` reads the clock
    "intake": {"intake", "pixels", "contracts", "identities", "errors", "config"},
    # pure, stdlib-only PNG decoding and the pixels-v1 hash; intake and build both use it
    "pixels": {"pixels", "errors", "config"},
    # the injected-renderer comparison shared by review and adopt (no Aseprite here: the real renderer lives in build)
    "rendering": {"rendering", "intake", "pixels", "contracts", "identities", "errors", "config"},
    "review": {"review", "rendering", "intake", "pixels", "contracts", "identities", "errors", "config"},
    # build owns the one allowed import from drawing (the shared sandbox)
    "build": {"build", "records", "revoke", "catalogwrite", "intake", "pixels", "contracts", "identities", "errors", "config"},
    "cli": {"cli", "intake", "adoption", "revoke", "audit", "records", "review", "rendering", "build", "release", "verify", "gc", "catalog", "contracts", "identities", "errors", "config"},
    "__main__": {"cli"},
    # catalog records and the human-gated writers (adoption, revoke, catalogwrite) are never reachable from the drawing tools
    "records": {"records", "intake", "contracts", "identities", "errors", "config"},
    "catalogwrite": {"catalogwrite", "intake", "errors", "config"},
    "adoption": {"adoption", "records", "rendering", "catalogwrite", "catalog", "intake", "pixels", "contracts", "identities", "errors", "config"},
    "revoke": {"revoke", "records", "catalogwrite", "intake", "contracts", "identities", "errors", "config"},
    "audit": {"audit", "records", "intake", "contracts", "identities", "errors", "config"},
    "release": {"release", "records", "catalog", "catalogwrite", "revoke", "pixels", "intake", "contracts", "identities", "errors", "config"},
    "verify": {"verify", "records", "audit", "build", "catalog", "pixels", "intake", "contracts", "identities", "errors", "config"},
    "gc": {"gc", "records", "intake", "contracts", "identities", "errors", "config"},
    # shaped, bounded, read-only views for agents; the drawing server may import it
    "readmodel": {"readmodel", "records", "intake", "pixels", "contracts", "identities", "errors", "config"},
}
# store layers that write the tracked catalog (human gates): no drawing module may import them, not even the server
GATE_LAYERS = {"adoption", "revoke", "catalogwrite", "release", "gc"}
# the ONLY store layers the drawing MCP server may import: intake (submit_candidate) and the read-only views, plus the shared leaves.
# Everything else (adoption, revoke, build, release, gc, cli, verify, review, rendering, records, audit, catalogwrite, pixels) is a violation.
SERVER_STORE_ALLOWED = {"intake", "readmodel", "contracts", "identities", "errors", "config"}
# no I/O, clock or process access in the pure layers; PyYAML only in `catalog`
PURE_STORE_LAYERS = {"contracts", "identities", "pixels"}
PURE_FORBIDDEN_IMPORTS = {"os", "pathlib", "io", "time", "datetime", "subprocess", "yaml"}
YAML_LAYERS = {"catalog"}

CATALOG_TOKENS = ("catalog", ".quarantine")


def _module_exists(dotted: str) -> bool:
    p = REPO.joinpath(*dotted.split("."))
    return p.is_dir() or p.with_suffix(".py").is_file()


def imported_modules(tree: ast.AST, current: str) -> list[tuple[str, ast.AST]]:
    """Dotted module names a tree imports (project-local resolution of `from pkg import submodule`)."""
    out: list[tuple[str, ast.AST]] = []
    pkg_parts = current.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend((a.name, node) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg_parts[: len(pkg_parts) - node.level + 1]
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            out.append((module, node))
            for a in node.names:
                cand = f"{module}.{a.name}"
                if _module_exists(cand):
                    out.append((cand, node))
    return out


def drawing_layer(dotted: str) -> str | None:
    parts = dotted.split(".")
    if parts[:2] != ["visual_assets", "drawing"]:
        return None
    return parts[2] if len(parts) > 2 else "__init__"


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def _module_name(rel: str) -> str:
    """Dotted module name of a repo-relative file; a package `__init__` is named `<pkg>.__init__`."""
    return rel[:-3].replace("/", ".")


def check_source(rel: str, source: str) -> list[str]:
    """All boundary violations for one file. `rel` is the path relative to the repo root."""
    problems: list[str] = []
    tree = ast.parse(source)
    name = _module_name(rel)
    mods = imported_modules(tree, name)

    for module, node in mods:
        top = module.split(".")[0]
        if rel.startswith("visual_assets/") and top == "src":
            problems.append(f"{rel}:{node.lineno}: visual_assets must not import src ({module})")
        if rel.startswith("src/") and top == "visual_assets":
            problems.append(f"{rel}:{node.lineno}: src must not import visual_assets ({module})")

    if rel.startswith("visual_assets/drawing/"):
        own = drawing_layer(name)
        allowed = DRAWING_ALLOWED.get(own or "")
        if allowed is None:
            problems.append(f"{rel}: unknown drawing layer {own!r}; add it to DRAWING_ALLOWED")
            allowed = set()
        for module, node in mods:
            if module.startswith("visual_assets.store"):
                if store_layer(module) in GATE_LAYERS:
                    problems.append(f"{rel}:{node.lineno}: drawing must never import the human-gated store layer ({module})")
                    continue
                if own == "handoff" and not module.startswith("visual_assets.store.contracts"):
                    problems.append(f"{rel}:{node.lineno}: handoff may import only store.contracts ({module})")
                elif own == "server" and module != "visual_assets.store" and store_layer(module) not in SERVER_STORE_ALLOWED:
                    problems.append(f"{rel}:{node.lineno}: the drawing server may import only {sorted(SERVER_STORE_ALLOWED)} from the store ({module})")
                elif own not in ("handoff", "server"):
                    problems.append(f"{rel}:{node.lineno}: drawing layer '{own}' must not import the store ({module})")
                continue
            target = drawing_layer(module)
            if target is None or module == "visual_assets.drawing":
                continue  # not drawing; or `from visual_assets.drawing import X` (judged by its submodule entry)
            if target != own and target not in allowed:
                problems.append(f"{rel}:{node.lineno}: layer '{own}' must not import layer '{target}' ({module})")
            if module.startswith("visual_assets.drawing.config") and module != "visual_assets.drawing.config":
                problems.append(f"{rel}:{node.lineno}: unexpected config submodule import ({module})")
        # the config rule: never `from ...config import NAME` (freezes a patchable value at import time)
        for module, node in mods:
            if module == "visual_assets.drawing.config" and isinstance(node, ast.ImportFrom) and node.module and (
                node.level or node.module.endswith("config")
            ):
                problems.append(
                    f"{rel}:{node.lineno}: import config as a module (config.NAME at call time), "
                    "never `from ...config import NAME`"
                )
        # no write path into the catalog (or its quarantine): no catalog token in code or string literals
        docs = _docstring_ids(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                if any(t in node.value.lower() for t in CATALOG_TOKENS):
                    problems.append(f"{rel}:{node.lineno}: drawing code must not reference the catalog ({node.value!r})")
            if isinstance(node, (ast.Name, ast.Attribute)):
                ident = node.id if isinstance(node, ast.Name) else node.attr
                if "catalog" in ident.lower():
                    problems.append(f"{rel}:{node.lineno}: drawing code must not reference the catalog ({ident})")
        for module, node in mods:
            if module.startswith("visual_assets.catalog"):
                problems.append(f"{rel}:{node.lineno}: drawing must not import the catalog ({module})")

    if rel.startswith("visual_assets/store/"):
        parts = rel.split("/")
        extra = STORE_EXTRA.get(parts[2] if len(parts) > 3 else "", set())
        for module, node in mods:
            if module.startswith("visual_assets.drawing") and not any(
                module.startswith(e) or e.startswith(module + ".") for e in extra
            ):
                problems.append(f"{rel}:{node.lineno}: store must not import drawing ({module})")
        problems.extend(_check_store_layering(rel, name, tree, mods))
    return problems


def store_layer(dotted: str) -> str | None:
    parts = dotted.split(".")
    if parts[:2] != ["visual_assets", "store"]:
        return None
    return parts[2] if len(parts) > 2 else "__init__"


def _check_store_layering(rel: str, name: str, tree: ast.AST, mods: list[tuple[str, ast.AST]]) -> list[str]:
    problems: list[str] = []
    own = store_layer(name)
    allowed = STORE_ALLOWED.get(own or "")
    if allowed is None:
        problems.append(f"{rel}: unknown store layer {own!r}; add it to STORE_ALLOWED")
        allowed = set()
    for module, node in mods:
        target = store_layer(module)
        if target is not None and module != "visual_assets.store" and target != own and target not in allowed:
            problems.append(f"{rel}:{node.lineno}: store layer '{own}' must not import layer '{target}' ({module})")
        top = module.split(".")[0]
        if own in PURE_STORE_LAYERS and top in PURE_FORBIDDEN_IMPORTS:
            problems.append(f"{rel}:{node.lineno}: pure store layer '{own}' must not import {top} ({module})")
        elif top == "yaml" and own not in YAML_LAYERS:
            problems.append(f"{rel}:{node.lineno}: only the catalog layer may import yaml ({module})")
        # the config rule: never `from ...config import NAME` (freezes a patchable value at import time)
        if module == "visual_assets.store.config" and isinstance(node, ast.ImportFrom) and node.module and (
            node.level or node.module.endswith("config")
        ):
            problems.append(
                f"{rel}:{node.lineno}: import config as a module (config.NAME at call time), "
                "never `from ...config import NAME`"
            )
    if own in PURE_STORE_LAYERS:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                problems.append(f"{rel}:{node.lineno}: pure store layer '{own}' must not call open()")
    return problems


def _tree_files() -> list[Path]:
    return sorted(p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts)


# --------------------------------------------------------------------------- the real tree


@pytest.mark.parametrize("path", _tree_files(), ids=lambda p: str(p.relative_to(REPO)))
def test_visual_assets_module_respects_the_boundaries(path):
    rel = str(path.relative_to(REPO))
    assert check_source(rel, path.read_text()) == []


def test_src_never_imports_visual_assets():
    offenders = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(errors="ignore")
        if "visual_assets" not in text:
            continue
        offenders += check_source(str(path.relative_to(REPO)), text)
    assert offenders == []


def test_every_drawing_module_has_a_known_layer():
    for path in _tree_files():
        rel = str(path.relative_to(REPO))
        if rel.startswith("visual_assets/drawing/"):
            parts = rel[:-3].split("/")
            layer = "__init__" if rel == "visual_assets/drawing/__init__.py" else parts[2]
            assert layer in DRAWING_ALLOWED, f"{rel}: layer {layer!r} not in DRAWING_ALLOWED"


# --------------------------------------------------------------------------- planted violations
# The checker must catch each rule being broken; these feed it source text that breaks one rule.


def test_planted_technique_importing_api_is_caught():
    src = "from visual_assets.drawing import api\n"
    problems = check_source("visual_assets/drawing/technique/ramps.py", src)
    assert any("layer 'technique' must not import layer 'api'" in p for p in problems), problems


def test_planted_drawing_importing_src_is_caught():
    for src in ("import src.core.items\n", "from src.core import items\n"):
        problems = check_source("visual_assets/drawing/api.py", src)
        assert any("must not import src" in p for p in problems), problems


def test_planted_src_importing_visual_assets_is_caught():
    problems = check_source("src/core/x.py", "from visual_assets.drawing import api\n")
    assert any("src must not import visual_assets" in p for p in problems), problems


def test_planted_catalog_reference_in_drawing_is_caught():
    for src in (
        'from pathlib import Path\nCATALOG = Path("visual_assets/catalog/sources")\n',
        'ROOT = "visual_assets/catalog"\n',
        'p = "x/.quarantine/y"\n',
        "import visual_assets.catalog.registry\n",
    ):
        problems = check_source("visual_assets/drawing/workspace/revisions.py", src)
        assert any("catalog" in p for p in problems), (src, problems)


def test_planted_from_config_import_is_caught():
    for src in (
        "from visual_assets.drawing.config import WORKSPACE\n",
        "from visual_assets.drawing import config\nfrom visual_assets.drawing.config import MAX_DIM\n",
    ):
        problems = check_source("visual_assets/drawing/workspace/jobs.py", src)
        assert any("never `from ...config import NAME`" in p for p in problems), (src, problems)
    # the allowed spelling passes
    assert check_source("visual_assets/drawing/workspace/jobs.py", "from visual_assets.drawing import config\n") == []


def test_planted_relative_from_config_import_is_caught():
    problems = check_source("visual_assets/drawing/workspace/jobs.py", "from ..config import WORKSPACE\n")
    assert any("never `from ...config import NAME`" in p for p in problems), problems


def test_planted_store_importing_drawing_is_caught():
    problems = check_source("visual_assets/store/identities.py", "from visual_assets.drawing import api\n")
    assert any("store must not import drawing" in p for p in problems), problems
    # the sandbox exception for `store.build` is judged on the drawing rule only; `build` has no STORE_ALLOWED
    # row until its ticket adds one (that unknown-layer failure is covered by its own planted test)
    problems = check_source("visual_assets/store/build/exporter.py", "from visual_assets.drawing.backend import sandbox\n")
    assert problems == [], problems  # restored to the strict assertion (planner item 7): the build row exists now


def test_every_store_module_has_a_known_layer():
    for path in _tree_files():
        rel = str(path.relative_to(REPO))
        if rel.startswith("visual_assets/store/"):
            layer = store_layer(_module_name(rel))
            assert layer in STORE_ALLOWED, f"{rel}: layer {layer!r} not in STORE_ALLOWED"


def test_planted_unknown_store_layer_is_caught():
    problems = check_source("visual_assets/store/zzz/thing.py", "import json\n")
    assert any("unknown store layer 'zzz'" in p for p in problems), problems


def test_planted_store_layering_violations_are_caught():
    cases = {
        "visual_assets/store/identities.py": "from visual_assets.store.contracts import base\n",
        "visual_assets/store/errors.py": "from visual_assets.store import identities\n",
        "visual_assets/store/contracts/base.py": "from visual_assets.store.catalog import registry\n",
        "visual_assets/store/config.py": "from visual_assets.store import errors\n",
    }
    for rel, src in cases.items():
        problems = check_source(rel, src)
        assert any("must not import layer" in p for p in problems), (rel, problems)
    # the allowed edges pass
    assert check_source("visual_assets/store/contracts/base.py", "from visual_assets.store import config\n") == []
    assert check_source("visual_assets/store/catalog/registry.py", "import yaml\nfrom visual_assets.store.contracts import base\n") == []


def test_planted_io_import_in_a_pure_store_layer_is_caught():
    for module in ("os", "pathlib", "io", "time", "datetime", "subprocess", "yaml"):
        for rel in ("visual_assets/store/contracts/handoff.py", "visual_assets/store/identities.py"):
            problems = check_source(rel, f"import {module}\n")
            assert any(f"must not import {module}" in p for p in problems), (module, rel, problems)
    problems = check_source("visual_assets/store/identities.py", "from datetime import datetime\n")
    assert any("must not import datetime" in p for p in problems), problems


def test_planted_open_call_in_a_pure_store_layer_is_caught():
    for rel in ("visual_assets/store/contracts/base.py", "visual_assets/store/identities.py"):
        problems = check_source(rel, "def f():\n    return open('x')\n")
        assert any("must not call open()" in p for p in problems), (rel, problems)
    # the catalog layer reads files, so it may
    assert check_source("visual_assets/store/catalog/registry.py", "def f():\n    return open('x')\n") == []


def test_planted_yaml_outside_catalog_is_caught():
    problems = check_source("visual_assets/store/config.py", "import yaml\n")
    assert any("only the catalog layer may import yaml" in p for p in problems), problems


def test_planted_store_from_config_import_is_caught():
    for src in (
        "from visual_assets.store.config import MAX_DIM\n",
        "from visual_assets.store import config\nfrom visual_assets.store.config import MAX_DIM\n",
    ):
        problems = check_source("visual_assets/store/contracts/base.py", src)
        assert any("never `from ...config import NAME`" in p for p in problems), (src, problems)
    problems = check_source("visual_assets/store/contracts/base.py", "from ..config import MAX_DIM\n")
    assert any("never `from ...config import NAME`" in p for p in problems), problems
    assert check_source("visual_assets/store/contracts/base.py", "from visual_assets.store import config\n") == []


def test_planted_drawing_importing_a_human_gate_is_caught():
    for gate in ("adoption", "revoke", "catalogwrite"):
        for rel in ("visual_assets/drawing/server/handoff_tools.py", "visual_assets/drawing/handoff.py", "visual_assets/drawing/api.py"):
            for src in (f"from visual_assets.store import {gate}\n", f"import visual_assets.store.{gate}\n",
                        f"from visual_assets.store.{gate} import x\n"):
                problems = check_source(rel, src)
                assert any("human-gated store layer" in p for p in problems), (gate, rel, src, problems)
    # the allowed link from drawing to the store is unchanged
    assert check_source("visual_assets/drawing/handoff.py", "from visual_assets.store.contracts import canonical_json\n") == []


def test_planted_store_layering_for_the_gated_layers_is_caught():
    cases = {
        "visual_assets/store/audit.py": "from visual_assets.store import adoption\n",  # audit is read-only: no gate module
        "visual_assets/store/records.py": "from visual_assets.store import catalogwrite\n",
        "visual_assets/store/catalogwrite.py": "from visual_assets.store import records\n",
        "visual_assets/store/intake/service.py": "from visual_assets.store import adoption\n",  # intake never adopts
        "visual_assets/store/revoke.py": "from visual_assets.store import adoption\n",
    }
    for rel, src in cases.items():
        problems = check_source(rel, src)
        assert any("must not import layer" in p for p in problems), (rel, problems)
    assert check_source("visual_assets/store/adoption.py", "from visual_assets.store import records, catalogwrite\n") == []
    assert check_source("visual_assets/store/cli.py", "from visual_assets.store import adoption, revoke, audit\n") == []


def test_planted_server_importing_a_forbidden_store_layer_is_caught():
    forbidden = ("adoption", "revoke", "build", "release", "gc", "cli", "verify", "review", "rendering", "records", "audit", "catalogwrite", "pixels")
    for layer in forbidden:
        for src in (f"from visual_assets.store import {layer}\n", f"import visual_assets.store.{layer}\n", f"from visual_assets.store.{layer} import x\n"):
            problems = check_source("visual_assets/drawing/server/store_readonly_tools.py", src)
            assert problems, (layer, src)
            assert any("human-gated" in p or "may import only" in p for p in problems), (layer, problems)
    for layer in sorted(SERVER_STORE_ALLOWED):
        assert check_source("visual_assets/drawing/server/store_readonly_tools.py", f"from visual_assets.store import {layer}\n") == [], layer


def test_planted_non_server_drawing_layers_still_cannot_import_any_store_layer_but_contracts():
    for rel in ("visual_assets/drawing/api.py", "visual_assets/drawing/compose.py"):
        problems = check_source(rel, "from visual_assets.store import intake\n")
        assert any("must not import the store" in p for p in problems), (rel, problems)
    assert check_source("visual_assets/drawing/handoff.py", "from visual_assets.store import intake\n")  # handoff: contracts only
    assert check_source("visual_assets/drawing/handoff.py", "from visual_assets.store.contracts import canonical_json\n") == []


def test_the_real_server_imports_only_the_allowlisted_store_layers():
    imported = set()
    for path in (PKG / "drawing" / "server").glob("*.py"):
        for module, _ in imported_modules(ast.parse(path.read_text()), "visual_assets.drawing.server." + path.stem):
            layer = store_layer(module)
            if layer is not None and module != "visual_assets.store":
                imported.add(layer)
    assert imported <= SERVER_STORE_ALLOWED and {"intake", "readmodel"} <= imported, imported
