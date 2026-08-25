"""Static, source-text-only guards over Makefile for TCK-20260716-AGENTOPS-BUILD-SERVE.

No live `make` invocation, no subprocess — pure text/regex checks against the
Makefile's raw content. Verifies AC #1 (new dashboard-* targets exist, are
.PHONY, do not shadow existing targets) and AC #4 (Node/npm confined to
dashboard-install/-build/-dev, never dashboard-serve).
"""
from __future__ import annotations

import re
from pathlib import Path

_MAKEFILE = Path("Makefile")

_NEW_TARGETS = ["dashboard-install", "dashboard-build", "dashboard-dev", "dashboard-serve"]

# Captured verbatim from the pre-change Makefile at implementation time
# (TCK-20260716-AGENTOPS-BUILD-SERVE) — any diff here means an existing
# target's recipe was edited, which AC #1 forbids.
_EXISTING_RECIPE_SNAPSHOT = {
    "install": "",
    "install-py": "\tpip install -r requirements.txt\n",
    "install-fe": "\tcd frontend && npm install\n",
    "build": "\tcd frontend && npm run build\n",
    "dev": (
        '\t@echo "Starting backend on :8000 and frontend on :5173..."\n'
        '\t@echo "Open http://localhost:5173 to view the live map."\n'
        '\t@echo "Press Ctrl+C to stop both."\n'
        "\t@trap 'kill 0' INT; \\\n"
        '\t\t$(PYTHON3) -m src serve --port 8000 --api-key-hashes "dev:3e90488c475fb2c2997525497f1e72e82dec6d68b5738dc7cebba4371f9f0ee2" & \\\n'
        "\t\t(cd frontend && npm run dev) & \\\n"
        "\t\twait\n"
    ),
    "dev-backend": "\t$(PYTHON3) -m src serve --port 8000\n",
    "dev-frontend": "\tcd frontend && npm run dev\n",
    "serve": "\t$(PYTHON3) -m src serve --port 8000\n",
    "serve-only": "\t$(PYTHON3) -m src serve --port 8000\n",
    "clean": (
        "\trm -rf frontend/dist\n"
        "\trm -rf frontend/node_modules/.tmp\n"
        "\tfind . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true\n"
    ),
}


def _makefile_text() -> str:
    return _MAKEFILE.read_text(encoding="utf-8")


def _phony_targets(text: str) -> set[str]:
    phony_line = next(line for line in text.splitlines() if line.startswith(".PHONY:"))
    return set(phony_line[len(".PHONY:") :].split())


def _extract_recipe(text: str, target: str) -> str:
    lines = text.splitlines(keepends=True)
    pattern = re.compile(rf"^{re.escape(target)}:")
    recipe_lines: list[str] = []
    in_target = False
    for line in lines:
        if in_target:
            if line.startswith("\t"):
                recipe_lines.append(line)
                continue
            break
        if pattern.match(line):
            in_target = True
    return "".join(recipe_lines)


def test_dashboard_targets_exist_and_are_phony():
    text = _makefile_text()
    phony = _phony_targets(text)

    for target in _NEW_TARGETS:
        assert re.search(rf"^{re.escape(target)}:", text, re.MULTILINE), (
            f"expected target definition for {target}:"
        )
        assert target in phony, f"expected {target} in .PHONY: line"


def test_existing_targets_unmodified():
    text = _makefile_text()

    for target, expected_recipe in _EXISTING_RECIPE_SNAPSHOT.items():
        actual = _extract_recipe(text, target)
        assert actual == expected_recipe, (
            f"recipe for {target}: changed from snapshot\nexpected: {expected_recipe!r}\nactual: {actual!r}"
        )


def test_dashboard_serve_recipe_has_no_npm_or_node():
    text = _makefile_text()

    for target in ("dashboard-install", "dashboard-build", "dashboard-dev"):
        recipe = _extract_recipe(text, target)
        assert "npm" in recipe or "node" in recipe or "cd dashboard-frontend" in recipe, (
            f"expected {target}'s recipe to invoke npm/node/dashboard-frontend"
        )

    serve_recipe = _extract_recipe(text, "dashboard-serve")
    assert "npm" not in serve_recipe
    assert "node" not in serve_recipe
    assert "cd dashboard-frontend" not in serve_recipe
