"""Single access point for the shared append writer (Step 5).

Loads tools/agent-monitoring/writer.py via importlib.util.spec_from_file_location /
module_from_spec / spec.loader.exec_module — exactly
tools/agent_replay_codex/entry_criterion.py's existing technique for importing a module from the
hyphenated, non-package tools/agent-monitoring/ directory (never renamed, never
sys.path.insert-hacked). This is the only file in this package permitted to reference
tools/agent-monitoring/writer.py or open any file in append mode.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_WRITER_PATH = Path(__file__).resolve().parent.parent / "agent-monitoring" / "writer.py"
_SPEC = importlib.util.spec_from_file_location(
    "agent_codex_posttool_adapter_writer", _WRITER_PATH
)
_writer_module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_writer_module)

write_line = _writer_module.write_line
