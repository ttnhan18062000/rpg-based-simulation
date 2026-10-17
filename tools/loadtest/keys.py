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


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_keys(count: int) -> list[str]:
    return [secrets.token_urlsafe(24) for _ in range(count)]


def api_key_hashes(keys: list[str]) -> str:
    """The ``RPG_API_KEY_HASHES`` value: ``loadtest-<i>:<sha256>`` pairs, comma-joined."""
    return ",".join(f"loadtest-{i}:{hash_key(k)}" for i, k in enumerate(keys))


def load_keys(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_keys(path: Path, keys: list[str]) -> None:
    path.write_text("\n".join(keys) + "\n")
    path.chmod(0o600)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--count", type=int, default=250, help="number of keys (>= the largest user step)")
    parser.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE)
    args = parser.parse_args(argv)
    keys = generate_keys(args.count)
    write_keys(args.keys_file, keys)
    print(api_key_hashes(keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
