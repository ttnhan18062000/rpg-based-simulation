"""#657: store tests never take the real `visual_assets/catalog/.store.lock`; a tmp catalog keeps its own lock."""

from __future__ import annotations

import subprocess
import sys

from tests.visual_assets.store.lock_isolation import REAL_CATALOG_ROOT
from visual_assets.store import cli, config, lock

HOLD = (
    "import fcntl, os, sys, time\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "try:\n"
    "    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "    print('ready', flush=True)\n"
    "except BlockingIOError:\n"
    "    print('busy', flush=True)\n"
    "time.sleep(60)\n"
)


def test_with_the_real_catalog_the_lock_lives_under_tmp(tmp_path):
    assert config.CATALOG_ROOT == REAL_CATALOG_ROOT
    path = lock.lock_path()
    assert path == tmp_path / ".store.lock" and REAL_CATALOG_ROOT not in path.parents


def test_a_tmp_catalog_keeps_its_own_lock(env):
    assert lock.lock_path() == env.catalog / ".store.lock"


def test_a_writing_command_passes_while_another_process_holds_the_real_lock(tmp_path, capsys):
    real = REAL_CATALOG_ROOT / ".store.lock"
    holder = subprocess.Popen([sys.executable, "-c", HOLD, str(real)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() in {"ready", "busy"}  # busy: a real store command already holds it; either way another process holds the real lock
        cli.main(["export-runtime", "--catalog-id", "pilot", "--release-id", "rc-0001", "--out", str(tmp_path / "o")])
        assert "store_locked" not in capsys.readouterr().err  # the command may still refuse for its own reasons (here: the registry changed since rc-0001)
        assert (tmp_path / ".store.lock").exists()  # O_CREAT happens only inside store_write_lock: the redirected lock was acquired, so this did not pass vacuously
    finally:
        holder.kill()
        holder.wait()
