from pathlib import Path
import shutil
import pytest
from tools.agent_orchestration.errors import ContractValidationError
from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
ROOT=Path(__file__).parent.parent.parent

def test_requires_valid_contract(tmp_path):
    shutil.copytree(ROOT / "agent-orchestration", tmp_path / "agent-orchestration")
    (tmp_path / "agent-orchestration" / "skills.yaml").unlink()
    with pytest.raises(ContractValidationError): render_codex_guidance(tmp_path, tmp_path / "out", allow_outside_contract=True)
