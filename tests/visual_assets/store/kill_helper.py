"""Child process for the kill tests (ADR D24): runs one store operation against isolated roots and SIGKILLs itself at a named point.

    python -m tests.visual_assets.store.kill_helper <mode> <point> <base>

modes: `hold` (take the store lock, print `ready`, sleep), `publish <n>` (a real `adopt`: kill when the n-th of its five `os.link` calls is about to run, n = 0 is before the first, `end` is after the last, before the temp directory is removed), `export <point>` (`first-write`, `second-write`, `before-rename`).
`<base>` holds `catalog/` with `.quarantine/` and `.review/` inside it (the real layout); for `export`, `<base>/out/runtime` is the (absent) output directory.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path


def die() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


def main(argv: list[str]) -> int:
    mode, point, base = argv[0], argv[1], Path(argv[2])
    from visual_assets.store import catalogwrite, config, lock, runtime_export

    config.CATALOG_ROOT = base / "catalog"
    config.QUARANTINE_ROOT, config.REVIEW_ROOT = config.CATALOG_ROOT / ".quarantine", config.CATALOG_ROOT / ".review"
    config.CATALOG_ROOT.mkdir(exist_ok=True)
    if mode == "hold":
        with lock.store_write_lock("hold", started_at="2026-01-01T00:00:00Z"):
            print("ready", flush=True)
            time.sleep(120)
        return 0
    if mode == "publish":
        from tests.visual_assets.store import adoption_support as support

        support.write_export_config(config.CATALOG_ROOT)
        support.write_store_format(config.CATALOG_ROOT)
        intake_id = support.make_intake(base / "packages", 16).intake_id
        print(intake_id, flush=True)
        real = os.link
        state = {"n": 0}

        def link(src, dst):
            if point != "end" and state["n"] == int(point):
                die()
            state["n"] += 1
            real(src, dst)

        catalogwrite._link = link
        if point == "end":
            catalogwrite.shutil.rmtree = lambda *a, **k: die()  # every file is linked; the temporary directory is about to be removed
        support.do_adopt(intake_id)
        return 0
    if mode == "export":
        real_write = runtime_export._write_new
        calls = {"n": 0}

        def write(path, data):
            calls["n"] += 1
            if (point == "first-write" and calls["n"] == 1) or (point == "second-write" and calls["n"] == 2):
                die()
            real_write(path, data)

        runtime_export._write_new = write
        if point == "before-rename":
            runtime_export.os = type("O", (), {"rename": staticmethod(lambda *a: die()), "__getattr__": lambda self, n: getattr(os, n)})()
        runtime_export.export_runtime("rehearsal", "rc-0001", base / "out" / "runtime", allow_fixture_namespace=True)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
