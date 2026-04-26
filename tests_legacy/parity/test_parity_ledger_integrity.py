import pytest
from tools.parity.validate_ledger import validate_ledger
import os

@pytest.mark.v2_contract
def test_ledger_integrity():
    ledger_dir = "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    assert os.path.exists(ledger_dir), "Ledger directory does not exist"
    assert validate_ledger(ledger_dir), "Ledger validation failed"
