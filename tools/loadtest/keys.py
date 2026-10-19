"""Generate a pool of load-test API keys and print the matching ``api_key_hashes`` value.

Keys go to a gitignored file (default ``tools/loadtest/.keys.txt``, one key per line); only the
``loadtest-<i>:<sha256>`` hashes are printed, for ``LOADTEST_API_KEY_HASHES`` (see compose.loadtest.yaml).
"""

from __future__ import annotations

import argparse
import hashlib
import secrets
from pathlib import Path

DEFAULT_KEYS_FILE = Path(__file__).resolve().parent / ".keys.txt"
#: One extra key that is NOT in the pool: the runner reads the engine state with it, so that read never competes with
#: (or is rejected by) the load, and its own bucket stays full.
DEFAULT_STATUS_KEY_FILE = Path(__file__).resolve().parent / ".status-key.txt"
STATUS_CLIENT_ID = "loadtest-status"


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_keys(count: int) -> list[str]:
    return [secrets.token_urlsafe(24) for _ in range(count)]


def api_key_hashes(keys: list[str], status_key: str | None = None) -> str:
    """The ``RPG_API_KEY_HASHES`` value: ``loadtest-<i>:<sha256>`` pairs (plus ``loadtest-status``), comma-joined."""
    pairs = [f"loadtest-{i}:{hash_key(k)}" for i, k in enumerate(keys)]
    if status_key:
        pairs.append(f"{STATUS_CLIENT_ID}:{hash_key(status_key)}")
    return ",".join(pairs)


def load_keys(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_keys(path: Path, keys: list[str]) -> None:
    path.write_text("\n".join(keys) + "\n")
    path.chmod(0o600)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--count", type=int, default=990,
                        help="pool size; the pool carries about 3 x this many req/s before per-key 429s (990 keys: about 2970 req/s; the server keeps at most 1000 client entries, src/api/admission_control.py _MAX_CLIENT_ENTRIES, so pool + status key stay under that)")
    parser.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE)
    parser.add_argument("--status-key-file", type=Path, default=DEFAULT_STATUS_KEY_FILE)
    args = parser.parse_args(argv)
    keys = generate_keys(args.count)
    status_key = generate_keys(1)[0]
    write_keys(args.keys_file, keys)
    write_keys(args.status_key_file, [status_key])
    print(api_key_hashes(keys, status_key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
