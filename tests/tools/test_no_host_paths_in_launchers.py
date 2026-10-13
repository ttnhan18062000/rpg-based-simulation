"""TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS: the Makefile and the MCP launch
scripts name no host-specific `/home/...` path; the main checkout is found through git instead."""
from __future__ import annotations

from pathlib import Path

import pytest

_FILES = ["Makefile", "tools/start_headroom_mcp.sh", "tools/start_search_mcp.sh"]


@pytest.mark.parametrize("path", _FILES)
def test_no_home_path_literal(path: str):
    offenders = [
        f"{n}: {line.strip()}"
        for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1)
        if "/home/" in line
    ]
    assert offenders == []
