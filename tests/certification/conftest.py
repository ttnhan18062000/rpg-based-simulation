import pathlib

import pytest


def pytest_collection_modifyitems(config, items):
    here = pathlib.Path(__file__).parent
    for item in items:
        if pathlib.Path(str(item.fspath)).parent == here:
            item.add_marker(pytest.mark.legacy_compat)
