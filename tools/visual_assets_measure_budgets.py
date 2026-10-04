"""Re-runnable measurements behind `docs/assets/budgets.md` (U-05): one JSON object per measurement.

    python -m tools.visual_assets_measure_budgets --list
    python -m tools.visual_assets_measure_budgets --only decode_scaling      # one measurement, JSON on stdout
    python -m tools.visual_assets_measure_budgets --all                      # each one in its own process, in order

`--all` runs every measurement as a separate subprocess (clean memory peaks), one at a time, under a 2 GB cap when
`systemd-run` is available, and writes `reports/visual_assets/budget_measurements.json` (gitignored). Measurements that
need the real Aseprite (`aseprite_*`) run only on the licence holder's machine (ADR D10) and report `NOT MEASURED` with
the reason when it is missing; nothing is ever estimated. This is a tool, not part of `visual_assets/`, so the boundary
guard does not police its imports (it uses the test builders for synthetic PNGs and fixtures).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import tracemalloc
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "reports" / "visual_assets" / "budget_measurements.json"
MEMORY_CAP = "MemoryMax=2G"
MIB = 1024 * 1024


def _timed(fn, repeats: int = 1) -> float:
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def _peak_bytes(fn) -> int:
    tracemalloc.start()
    try:
        fn()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def _png(width: int, height: int, filter_type: int) -> bytes:
    """An RGBA PNG whose every row uses `filter_type` (4 = Paeth, the slowest to undo), built without a pixel list."""
    from tests.visual_assets.store import builders as b

    row = bytes((i * 37 + 11) % 251 for i in range(width * 4))
    samples = b"".join(row[(y * 4) % len(row) :] + row[: (y * 4) % len(row)] for y in range(height))
    raw = b.filter_rows(samples, width * 4, height, 4, [filter_type])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + b.png_chunk(b"IHDR", ihdr) + b.png_chunk(b"IDAT", zlib.compress(raw, 6)) + b.png_chunk(b"IEND", b"")


# ---------------------------------------------------------------- pure-Python measurements (run anywhere)


def decode_scaling() -> dict:
    """Pure-Python PNG decode + pixels-v1 hash of an RGBA square, time and Python-allocation peak, Paeth rows (worst) and Sub rows."""
    from visual_assets.store import pixels

    rows = []
    for dim in (128, 256, 512, 768, 1024, 1536, 2048):
        for name, ftype in (("paeth", 4), ("sub", 1)):
            data = _png(dim, dim, ftype)
            run = lambda d=data, m=dim: pixels.pixel_hash(d, max_dim=m)  # noqa: E731
            seconds = _timed(run, repeats=3 if dim <= 1024 else 1)  # best of 3 where it is cheap: single runs are noisy
            rows.append(
                {
                    "dim": dim,
                    "filter": name,
                    "png_bytes": len(data),
                    "decoded_bytes": dim * (dim * 4 + 1),
                    "seconds": round(seconds, 3),
                    "peak_python_mib": round(_peak_bytes(run) / MIB, 1) if ftype == 4 else None,  # the same for both filters
                }
            )
    return {"rows": rows}


def decode_at_decoded_bytes_bound() -> dict:
    """Decode + hash of the largest RGBA square whose decoded size fits MAX_DECODED_BYTES (Paeth rows, one run, then a memory pass)."""
    from visual_assets.store import config, pixels

    dim = 1
    while (dim + 1) * ((dim + 1) * 4 + 1) <= config.MAX_DECODED_BYTES:
        dim += 1
    data = _png(dim, dim, 4)
    run = lambda: pixels.pixel_hash(data, max_dim=dim)  # noqa: E731
    return {
        "dim": dim,
        "decoded_bytes": dim * (dim * 4 + 1),
        "png_bytes": len(data),
        "seconds": round(_timed(run), 3),
        "peak_python_mib": round(_peak_bytes(run) / MIB, 1),
        "limits": {"MAX_DECODED_BYTES": config.MAX_DECODED_BYTES},
    }


def registry_scaling() -> dict:
    """Real `load_registry` path (no bound lifted) at growing key counts, realistic keys (2 axes x 4 values) and no-axis keys."""
    import yaml

    from visual_assets.store import config
    from visual_assets.store.catalog.registry import load_registry

    def build(keys: int, aliases: int, axes: int) -> bytes:
        entries = [
            {"key": f"ui.family{i % 40}.entry{i}", "family": f"family{i % 40}", "description": "A realistic one-line description of what this visual key is for",
             "variant_axes": [{"name": f"axis{a}", "values": [f"value{v}" for v in range(4)]} for a in range(axes)], "optional": False}
            for i in range(keys)
        ]
        links = [{"alias": f"ui.old{i}.entry{i}", "target": f"ui.family{i % 40}.entry{i}"} for i in range(aliases)]
        return yaml.safe_dump({"record_type": "visual_key_registry", "schema_version": 1, "keys": entries, "aliases": links}).encode()

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "registry.yaml"
        for axes in (2, 0):
            for keys in (256, 512, 1024):  # MAX_VISUAL_KEYS is 1024: the count at which cost was measured under 2 s
                data = build(keys, min(keys, config.MAX_ALIASES), axes)
                path.write_bytes(data)
                row = {"axes": axes, "keys": keys, "file_bytes": len(data)}
                if len(data) > config.MAX_REGISTRY_BYTES:
                    row["status"] = "over MAX_REGISTRY_BYTES (refused by the byte bound)"
                else:
                    run = lambda: load_registry(path, allow_fixture_namespace=True)  # noqa: E731
                    row["seconds"] = round(_timed(run, repeats=3), 3)
                    row["peak_python_mib"] = round(_peak_bytes(run) / MIB, 1)
                rows.append(row)
    return {"rows": rows, "limits": {"MAX_REGISTRY_BYTES": config.MAX_REGISTRY_BYTES, "MAX_VISUAL_KEYS": config.MAX_VISUAL_KEYS}}


def manifest_scaling() -> dict:
    """Size and parse time of a ReleaseCandidateManifest with N entries of maximum-length ids (the widest legal entry)."""
    from visual_assets.store import config
    from visual_assets.store.contracts import ReleaseCandidateManifest, parse_record
    from visual_assets.store.contracts.base import canonical_json

    config.MAX_MANIFEST_BYTES = 1 << 30  # measure what the contract allows
    rows = []
    for n in (1024, 2048, 3072, 4096):
        entries = [
            {"visual_key": f"a{i:05d}" + "x" * 26 + ".b" + "y" * 31 + ".c" + "z" * 29, "artifact_id": "x" * 62 + f"{i % 100:02d}", "pixel_hash": "pixels-v1:" + f"{i:064x}"}
            for i in range(n)
        ]
        data = json.dumps({"record_type": "release_candidate_manifest", "schema_version": 1, "catalog_id": "catalog", "release_id": "rc-0001", "registry_hash": "sha256:" + "0" * 64, "entries": entries, "status": "CANDIDATE"}).encode()
        record = parse_record(ReleaseCandidateManifest, data)
        size = len(canonical_json(record))
        rows.append({"entries": n, "bytes": size, "parse_seconds": round(_timed(lambda d=data: parse_record(ReleaseCandidateManifest, d), repeats=3), 3)})
    return {"rows": rows}


def worst_png() -> dict:
    """File size of the worst legal store PNG: a 1024 px RGBA noise square written without compression (zlib 0) and at zlib 9."""
    import os as _os

    dim = 1024
    samples = _os.urandom(dim * dim * 4)
    sizes = {}
    for level in (0, 9):
        raw = b"".join(b"\x00" + samples[y * dim * 4 : (y + 1) * dim * 4] for y in range(dim))
        ihdr = struct.pack(">IIBBBBB", dim, dim, 8, 6, 0, 0, 0)
        from tests.visual_assets.store import builders as b

        png = b"\x89PNG\r\n\x1a\n" + b.png_chunk(b"IHDR", ihdr) + b.png_chunk(b"IDAT", zlib.compress(raw, level)) + b.png_chunk(b"IEND", b"")
        sizes[f"zlib_level_{level}_bytes"] = len(png)
    sizes["decoded_bytes"] = dim * (dim * 4 + 1)
    return sizes


def record_sizes() -> dict:
    """Serialized sizes of every fixture record and of the largest record the contracts allow."""
    from tests.visual_assets.store import builders as b
    from visual_assets.store import config
    from visual_assets.store.contracts import CandidateHandoffPackage, IntakeResult, parse_record
    from visual_assets.store.contracts.base import canonical_json
    from visual_assets.store.contracts.handoff import MAX_LIMITATIONS
    from visual_assets.store.contracts.intake import MAX_FINDINGS

    real_limit = config.MAX_RECORD_BYTES
    config.MAX_RECORD_BYTES = 1 << 30  # measure what the contracts allow; the real bound is compared below
    fixtures = {p.name: p.stat().st_size for p in sorted((REPO / "visual_assets/catalog/fixtures/contracts").glob("*.json"))}

    def widest(model, base: dict) -> dict:
        """Set every field to a 256-char (then 128-char) ASCII filler where the contract still accepts it."""
        grown = dict(base)
        for key, value in base.items():
            if not isinstance(value, str):
                continue
            for width in (256, 128):
                trial = {**grown, key: "x" * width}
                try:
                    parse_record(model, json.dumps(trial).encode())
                except Exception:  # noqa: BLE001 - a field with a fixed pattern/enum keeps its value
                    continue
                grown = trial
                break
        return grown

    source, preview = b.aseprite(width=16, height=16), b.png(16, 16)
    package = widest(CandidateHandoffPackage, b.package_dict(source, preview))
    package["declared_limitations"] = ["x" * 256] * MAX_LIMITATIONS
    package_ascii = canonical_json(parse_record(CandidateHandoffPackage, json.dumps(package).encode()))
    package["declared_limitations"] = ["\U0001d4b3" * 256] * MAX_LIMITATIONS  # 4 UTF-8 bytes per character
    package_utf8 = canonical_json(parse_record(CandidateHandoffPackage, json.dumps(package).encode()))

    base = json.loads((REPO / "visual_assets/catalog/fixtures/contracts/intake_result.json").read_text())
    base["verdict"], base["staged_files"] = "QUARANTINED", base["staged_files"][:1]
    findings = lambda text: [{"code": "PACKAGE_INVALID", "detail": text * 256} for _ in range(MAX_FINDINGS)]  # noqa: E731
    result_ascii = canonical_json(parse_record(IntakeResult, json.dumps({**base, "findings": findings("x")}).encode()))
    result_utf8 = canonical_json(parse_record(IntakeResult, json.dumps({**base, "findings": findings("\U0001d4b3")}).encode()))
    return {
        "fixture_record_bytes": fixtures,
        "largest_fixture_record_bytes": max(fixtures.values()),
        "max_candidate_handoff_package_bytes": {"ascii": len(package_ascii), "four_byte_utf8": len(package_utf8)},
        "max_intake_result_bytes": {"ascii": len(result_ascii), "four_byte_utf8": len(result_utf8)},
        "limits": {"MAX_RECORD_BYTES": real_limit, "MAX_FINDINGS": MAX_FINDINGS, "MAX_LIMITATIONS": MAX_LIMITATIONS},
        "legal_records_over_MAX_RECORD_BYTES": [
            name
            for name, size in (("package_utf8", len(package_utf8)), ("package_ascii", len(package_ascii)), ("intake_result_utf8", len(result_utf8)), ("intake_result_ascii", len(result_ascii)))
            if size > real_limit
        ],
    }


def registry_at_byte_bound() -> dict:
    """Load time of a realistic registry (2 axes x 4 values per key) grown to just under MAX_REGISTRY_BYTES, best of 3."""
    import yaml

    from visual_assets.store import config
    from visual_assets.store.catalog.registry import load_registry

    def build(keys: int) -> bytes:
        entries = [
            {"key": f"ui.family{i % 40}.entry{i}", "family": f"family{i % 40}", "description": "A realistic one-line description of what this visual key is for",
             "variant_axes": [{"name": f"axis{a}", "values": [f"value{v}" for v in range(4)]} for a in range(2)], "optional": False}
            for i in range(keys)
        ]
        return yaml.safe_dump({"record_type": "visual_key_registry", "schema_version": 1, "keys": entries, "aliases": []}).encode()

    config.MAX_VISUAL_KEYS = 1 << 20  # the byte bound is what is measured here, not the key count
    keys = 1
    while len(build(keys + 64)) <= config.MAX_REGISTRY_BYTES:
        keys += 64
    data = build(keys)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "registry.yaml"
        path.write_bytes(data)
        run = lambda: load_registry(path, allow_fixture_namespace=True)  # noqa: E731
        return {"keys": keys, "file_bytes": len(data), "MAX_REGISTRY_BYTES": config.MAX_REGISTRY_BYTES, "seconds": round(_timed(run, repeats=3), 3), "peak_python_mib": round(_peak_bytes(run) / MIB, 1)}


# ---------------------------------------------------------------- real-Aseprite measurements (local only, ADR D10)


def _need_aseprite() -> str | None:
    from visual_assets.drawing import config

    if not Path(config.ASEPRITE).exists() or shutil.which("bwrap") is None:
        return "NOT MEASURED: Aseprite or bwrap is not available on this machine (real Aseprite runs locally only, ADR D10)"
    return None


def _noise(width: int, height: int, seed: int) -> list[dict]:
    state, out = seed or 1, []
    for y in range(height):
        for x in range(width):
            state = (state * 1103515245 + 12345) % (1 << 31)
            out.append({"x": x, "y": y, "color": f"#{(state >> 8) & 0xFFFFFF:06x}"})
    return out


def _draw_noise(name: str, rev: str, width: int, height: int, frame: int, seed: int) -> str:
    from visual_assets.drawing import api, config

    pixels = _noise(width, height, seed)
    chunk = config.MAX_PIXELS_PER_OP
    per_call = config.MAX_PIXELS_PER_CALL // chunk
    ops = [{"op": "pixels", "pixels": pixels[i : i + chunk], "frame": frame} for i in range(0, len(pixels), chunk)]
    for i in range(0, len(ops), per_call):
        rev = api.apply_ops(name, rev, ops[i : i + per_call])["revision"]
    return rev


def aseprite_source_bytes() -> dict:
    """Source `.aseprite` bytes per size and frame count: a flat sprite (a few shapes) and a noise sprite (every pixel a new colour)."""
    if (why := _need_aseprite()) is not None:
        return {"status": why}
    from visual_assets.drawing import api, config

    rows = []
    with tempfile.TemporaryDirectory() as ws:
        config.WORKSPACE = Path(ws)
        for dim in (16, 32, 64, 128):
            for frames in (1, config.MAX_FRAMES):
                for kind in ("flat", "noise"):
                    name = f"s{dim}f{frames}{kind}"
                    rev = api.new_sprite(name, dim, dim, "#102030")["revision"]
                    for f in range(1, frames):
                        rev = api.apply_ops(name, rev, [{"op": "add_frame", "copy_from": 1}])["revision"]
                    if kind == "flat":
                        rev = api.apply_ops(
                            name, rev, [{"op": "rect", "x": 2, "y": 2, "width": dim // 2, "height": dim // 2, "color": "#ff0000"}, {"op": "ellipse", "x": 1, "y": 1, "width": dim // 2, "height": dim // 2, "color": "#00ff00", "filled": False}]
                        )["revision"]
                    else:
                        for f in range(1, frames + 1):
                            rev = _draw_noise(name, rev, dim, dim, f, seed=dim * 100 + f)
                    rows.append({"dim": dim, "frames": frames, "kind": kind, "source_bytes": len(api.read_revision(name, rev)[1])})
    return {"rows": rows, "limits": {"MAX_SOURCE_BYTES": 100 * 1024, "MAX_FILE_BYTES": config.MAX_FILE_BYTES}}


def aseprite_timing() -> dict:
    """Wall time of apply_ops with MAX_OPS ops, and of the store's review render, adopt re-render and build export (16 px and 128 px)."""
    if (why := _need_aseprite()) is not None:
        return {"status": why}
    from tests.visual_assets.store import adoption_support as s
    from visual_assets.drawing import api, handoff
    from visual_assets.drawing import config as dcfg
    from visual_assets.store import config
    from visual_assets.store import review as review_mod
    from visual_assets.store.build import exporter
    from visual_assets.store.intake import intake

    rows: dict = {}
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        dcfg.WORKSPACE = tmp / "ws"
        config.CATALOG_ROOT, config.QUARANTINE_ROOT, config.REVIEW_ROOT = tmp / "catalog", tmp / "quarantine", tmp / "review"
        config.CATALOG_ROOT.mkdir()
        s.write_export_config(config.CATALOG_ROOT)
        s.write_store_format(config.CATALOG_ROOT)
        renderer = exporter.default_renderer()

        rev = api.new_sprite("ops", 128, 128, "#102030")["revision"]
        ops = [{"op": "rect", "x": i % 100, "y": (i * 7) % 100, "width": 8, "height": 8, "color": f"#{(i * 977) % 0xFFFFFF:06x}"} for i in range(dcfg.MAX_OPS)]
        start = time.perf_counter()
        api.apply_ops("ops", rev, ops)
        rows["apply_ops_MAX_OPS_rects_128px_seconds"] = round(time.perf_counter() - start, 3)
        rev = api.new_sprite("px", 128, 128, "#102030")["revision"]
        per_call = dcfg.MAX_PIXELS_PER_CALL // dcfg.MAX_PIXELS_PER_OP
        batch = [{"op": "pixels", "pixels": _noise(128, 128, 7)[i * dcfg.MAX_PIXELS_PER_OP : (i + 1) * dcfg.MAX_PIXELS_PER_OP]} for i in range(per_call)]
        start = time.perf_counter()
        api.apply_ops("px", rev, batch)
        rows["apply_ops_MAX_PIXELS_PER_CALL_128px_seconds"] = round(time.perf_counter() - start, 3)

        for dim in (16, 128):
            name = f"hero{dim}"
            rev = api.new_sprite(name, dim, dim, "#102030")["revision"]
            rev = api.apply_ops(name, rev, [{"op": "add_layer", "name": "top"}])["revision"]
            rev = _draw_noise(name, rev, dim, dim, 1, seed=dim)
            package = handoff.build_handoff(name, rev, licence_state="CLEARED", licence_evidence_ref="note", brief_id="brief", review_evidence_ref="NOT_APPLICABLE")
            result = intake(package["directory"], created_at="2026-01-01T00:00:00Z")
            row = {"intake_verdict": result.verdict.value, "preview_png_bytes": (Path(package["directory"]) / "preview.png").stat().st_size}
            source = api.read_revision(name, rev)[1]
            row["source_bytes"] = len(source)
            row["render_scale8_seconds"] = round(_timed(lambda: renderer.render(source, scale=8)), 3)
            row["render_scale16_seconds"] = round(_timed(lambda: renderer.render(source, scale=16)), 3)
            if result.verdict.value == "PASSED":
                start = time.perf_counter()
                review_mod.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer)
                row["review_seconds"] = round(time.perf_counter() - start, 3)
                start = time.perf_counter()
                s.do_adopt(result.intake_id, source_asset_id="hero", renderer=renderer)
                row["adopt_seconds"] = round(time.perf_counter() - start, 3)
                start = time.perf_counter()
                exporter.build(renderer=renderer)
                row["build_seconds"] = round(time.perf_counter() - start, 3)
            else:
                row["status"] = f"NOT MEASURED review/adopt/build: intake verdict {result.verdict.value}: {[f.code.value for f in result.findings]}"
            rows[f"{dim}px"] = row
            for path in (config.QUARANTINE_ROOT, config.REVIEW_ROOT, config.CATALOG_ROOT / "sources", config.CATALOG_ROOT / "provenance", config.CATALOG_ROOT / "generated"):
                shutil.rmtree(path, ignore_errors=True)
    return rows


MEASUREMENTS = {
    "record_sizes": record_sizes,
    "registry_at_byte_bound": registry_at_byte_bound,
    "registry_scaling": registry_scaling,
    "manifest_scaling": manifest_scaling,
    "worst_png": worst_png,
    "decode_scaling": decode_scaling,
    "decode_at_decoded_bytes_bound": decode_at_decoded_bytes_bound,
    "aseprite_source_bytes": aseprite_source_bytes,
    "aseprite_timing": aseprite_timing,
}


def _run_all() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report: dict = {"aseprite_version": None}
    from tests.visual_assets import strict_aseprite
    from visual_assets.drawing import config

    report["aseprite_version"] = strict_aseprite.read_version(str(config.ASEPRITE)) or "NOT AVAILABLE"
    capped = ["systemd-run", "--user", "--scope", "-p", MEMORY_CAP, "--quiet"] if shutil.which("systemd-run") else []
    for name in MEASUREMENTS:
        done = subprocess.run([*capped, sys.executable, "-m", "tools.visual_assets_measure_budgets", "--only", name], cwd=REPO, capture_output=True, text=True, check=False)
        try:
            report[name] = json.loads(done.stdout)
        except json.JSONDecodeError:
            report[name] = {"status": f"FAILED (exit {done.returncode})", "stderr_tail": done.stderr[-400:]}
        print(f"{name}: done", file=sys.stderr)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--only", choices=sorted(MEASUREMENTS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    if args.list:
        print("\n".join(MEASUREMENTS))
        return 0
    if args.only:
        print(json.dumps(MEASUREMENTS[args.only](), indent=2))
        return 0
    return _run_all()


if __name__ == "__main__":
    os.chdir(REPO)
    sys.exit(main(sys.argv[1:]))
