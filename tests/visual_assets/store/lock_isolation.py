"""Keep the store write lock of a test off the real catalog (`TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK`, GitHub issue #657).

`store/lock.py::lock_path()` is `config.CATALOG_ROOT / ".store.lock"`. A test that runs a writing store command while `config.CATALOG_ROOT` is still the real
`visual_assets/catalog` would take `LOCK_EX|LOCK_NB` on the real, shared lock file, so a second process (pytest-xdist, or a store command run by hand) makes it fail with
`store_locked`. `redirect_real_catalog_lock` makes `lock_path()` answer a file under `tmp_path` in that one case. A test that points `CATALOG_ROOT` at a tmp catalog keeps its
lock at `<tmp catalog>/.store.lock` (`test_lock.py`, `test_deletion_log.py`, `test_kill_mid_publish.py` assert on that). The check is made at call time, so it does not matter whether
the test patches `CATALOG_ROOT` before or after this fixture runs. Only the test side changes; `lock.py` is not touched.

Use it as an autouse fixture: `store_lock_in_tmp = pytest.fixture(autouse=True)(redirect_real_catalog_lock)` in a conftest, or a one-line fixture in a top-level test file.
"""

from __future__ import annotations

from visual_assets.store import config, lock

REAL_CATALOG_ROOT = config.CATALOG_ROOT  # read at import (collection) time, before any test patches it


def redirect_real_catalog_lock(tmp_path, monkeypatch):
    original = lock.lock_path

    def lock_path():
        if config.CATALOG_ROOT == REAL_CATALOG_ROOT:
            return tmp_path / lock.LOCK_NAME
        return original()

    monkeypatch.setattr(lock, "lock_path", lock_path)
