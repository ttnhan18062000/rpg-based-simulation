"""Capture the rehearsal harness pages from the BUILT bundle and write the evidence record (`make visual-assets-bundle-capture`; local only, CI never runs it).

`TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`. Until now the rehearsal captures ran against the Vite dev server, whose image URLs are `/src/...` paths. This builds the
pages with `frontend/vite.rehearsal-bundle.config.ts` (hashed `/assets/<name>-<hash>.png` URLs), serves them with `vite preview` and runs `frontend/rehearsal-capture/bundle.check.ts` in
Chromium. Two runs:

1. the real bundle: every page loads only hashed images, and `rehearsal.html` draws exactly the three stored artifacts (the drawn cells are hashed with the store's own `pixels-v1`
   hash, `frontend/src/visualAssets/pixelsV1.ts`, proven equal to the Python hash on known vectors);
2. the planted proof: a copy of that bundle in which ONE fixture PNG has ONE pixel changed. The same capture must FAIL, naming that image, or the check could not tell a wrong asset
   from a right one.

Only `rehearsal.html` carries pixel verdicts. The other pages (pilot, map, icons, draft) are asset-loading evidence only, and the record says so per page. No gate result moves: the
surface rehearsal stays INCONCLUSIVE (`docs/assets/surface_rehearsal_result.md`). The compact record `docs/assets/surface_rehearsal_bundle_evidence.json.txt` is the only committed output;
screenshots, the bundle and the raw evidence stay under `reports/visual_assets/bundle_capture/` (not committed).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend"
FIXTURES = FRONTEND / "src" / "visualAssets" / "__fixtures__"
OUT_DIR = REPO / "reports" / "visual_assets" / "bundle_capture"
RECORD_PATH = REPO / "docs" / "assets" / "surface_rehearsal_bundle_evidence.json.txt"
MAKE_TARGET = "visual-assets-bundle-capture"
RECORD_TYPE = "surface_rehearsal_bundle_evidence"
PAGE_NAMES = ("rehearsal", "pilot", "map", "icons", "draft")
PIXEL_PAGE = "rehearsal"
PIXEL_KEYS = ("fixture.rehearsal.gem", "fixture.rehearsal.rock", "fixture.rehearsal.frame")
HASHED_URL = re.compile(r"^/assets/([0-9a-f]{64})-[A-Za-z0-9_-]{8}\.png$")
CHROMIUM_CANDIDATES = ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser")
NOT_TAKEN = "not_taken: asset-loading evidence only, no pixel verdict"
VERIFIED = "verified: the drawn cells were hashed and compared with the stored artifacts"
RECORD_KEYS = frozenset({
    "record_type", "schema_version", "make_target", "run_commit", "run_at_utc", "browser", "browser_version", "device_pixel_ratio", "vite_version", "pages", "planted", "gate_result_moved",
})
PAGE_KEYS = frozenset({
    "page", "settled", "images", "all_images_hashed", "data_url_images", "dev_server_requests", "failed_requests", "pixel_verification", "pixel_verdicts",
})
PLANTED_KEYS = frozenset({"changed_fixture_file", "what_changed", "capture_failed", "failing_verdicts", "unchanged_verdicts_identical"})


# ---- pure rules (proven on planted violations in tests/visual_assets/test_bundle_capture_evidence.py) ----

def plant_one_pixel(png: bytes) -> bytes:
    """The same image with the red byte of its first opaque pixel changed by one: a PNG that decodes and looks right but is a different image."""
    from visual_assets.store import atlas, pixels

    image = pixels.decode_png(png, max_dim=128)
    rgba = bytearray(image.rgba)
    for at in range(0, len(rgba), 4):
        if rgba[at + 3] == 255:
            rgba[at] = rgba[at] ^ 1
            return atlas.encode_png(image.width, image.height, bytes(rgba))
    raise ValueError("the image has no opaque pixel to change")


def find_hashed_file(bundle: Path, stem: str) -> Path:
    found = sorted((bundle / "assets").glob(f"{stem}-*.png"))
    if len(found) != 1:
        raise ValueError(f"expected exactly one built file for {stem}.png in {bundle / 'assets'}, found {len(found)}")
    return found[0]


def fixture_files() -> set[str]:
    return {p.name for p in FIXTURES.glob("*/*.png")}


def compose_record(good: Mapping, planted_run: Mapping, planted_exit: int, *, changed_file: str, commit: str, run_at: str, vite_version: str) -> dict:
    pages = []
    for page in good["pages"]:
        verified = page["pixel_verdicts"] is not None
        pages.append({
            "page": page["page"], "settled": page["settled"],
            "images": [{"url": url, "fixture_file": HASHED_URL.match(url).group(1) + ".png" if HASHED_URL.match(url) else None} for url in page["image_urls"]],
            "all_images_hashed": page["all_images_hashed"], "data_url_images": page["data_url_images"],
            "dev_server_requests": page["dev_server_requests"], "failed_requests": page["failed_requests"],
            "pixel_verification": VERIFIED if verified else NOT_TAKEN,
            "pixel_verdicts": page["pixel_verdicts"] if verified else None,
        })
    planted_verdicts = next(p for p in planted_run["pages"] if p["page"] == PIXEL_PAGE)["pixel_verdicts"] or {}
    return {
        "record_type": RECORD_TYPE, "schema_version": 1, "make_target": MAKE_TARGET, "run_commit": commit, "run_at_utc": run_at,
        "browser": good["browser"], "browser_version": good["browser_version"], "device_pixel_ratio": good["device_pixel_ratio"], "vite_version": vite_version,
        "pages": pages,
        "planted": {
            "changed_fixture_file": changed_file, "what_changed": "the red byte of one pixel (the first opaque one) in one hashed fixture PNG of a copy of the built bundle",
            "capture_failed": planted_exit != 0,
            "failing_verdicts": sorted(k for k, v in planted_verdicts.items() if not v["identical"]),
            "unchanged_verdicts_identical": sum(1 for v in planted_verdicts.values() if v["identical"]),
        },
        "gate_result_moved": False,
    }


def record_problems(record: object, manifest: Mapping | None = None, files: set[str] | None = None) -> list[str]:
    """Everything wrong with an evidence record (empty = it says exactly what the real run established). `manifest` is the committed rehearsal runtime manifest."""
    if not isinstance(record, dict):
        return ["the record is not a JSON object"]
    if set(record) != RECORD_KEYS:
        return [f"record keys differ: missing {sorted(RECORD_KEYS - set(record))}, unexpected {sorted(set(record) - RECORD_KEYS)}"]
    manifest = manifest if manifest is not None else json.loads((FIXTURES / "rehearsal" / "runtime_manifest.json").read_text())
    files = files if files is not None else fixture_files()
    expected = {e["visual_key"]: e for e in manifest["entries"]}
    problems = []
    if (record["record_type"], record["schema_version"], record["make_target"]) != (RECORD_TYPE, 1, MAKE_TARGET):
        problems.append("record_type, schema_version or make_target is not the expected value")
    if record["gate_result_moved"] is not False:
        problems.append("a bundle capture never moves a gate result")
    if record["device_pixel_ratio"] != 1:
        problems.append("the capture is pinned to a device pixel ratio of 1")
    for key in ("run_commit", "run_at_utc", "browser", "browser_version", "vite_version"):
        if not isinstance(record[key], str) or not record[key].strip():
            problems.append(f"{key} must be a non-empty string")
    pages = record["pages"]
    if not isinstance(pages, list) or [p.get("page") if isinstance(p, dict) else None for p in pages] != list(PAGE_NAMES):
        return [*problems, f"pages must be exactly {list(PAGE_NAMES)} in that order"]
    for page in pages:
        name = page["page"]
        if set(page) != PAGE_KEYS:
            problems.append(f"{name}: page keys differ")
            continue
        if not page["images"] or not page["all_images_hashed"]:
            problems.append(f"{name}: every image must come from a hashed /assets URL (and there must be one)")
        for image in page["images"]:
            match = HASHED_URL.match(image.get("url", ""))
            if not match or image.get("fixture_file") != match.group(1) + ".png" or image["fixture_file"] not in files:
                problems.append(f"{name}: image {image.get('url')!r} is not a hashed URL of a committed fixture")
        if page["data_url_images"] != 0 or page["dev_server_requests"] != [] or page["failed_requests"] != []:
            problems.append(f"{name}: inlined data images, dev-server requests or failed requests are not allowed")
        if name == PIXEL_PAGE:
            verdicts = page["pixel_verdicts"]
            if page["pixel_verification"] != VERIFIED or not isinstance(verdicts, dict) or sorted(verdicts) != sorted(PIXEL_KEYS):
                problems.append(f"{name}: must carry the pixel verdicts of exactly {list(PIXEL_KEYS)}")
                continue
            used = {i["fixture_file"] for i in page["images"]}
            for key, verdict in verdicts.items():
                want = expected[key]["pixel_hash"]
                if not (verdict.get("identical") is True and verdict.get("expected") == want and verdict.get("drawn") == want and verdict.get("scale") == 1):
                    problems.append(f"{name}: {key} is not a verified identical draw of the stored artifact")
                if expected[key]["file"] not in used:
                    problems.append(f"{name}: the page did not load {expected[key]['file']}")
        elif page["pixel_verification"] != NOT_TAKEN or page["pixel_verdicts"] is not None:
            problems.append(f"{name}: has no pixel verdicts and must say so ({NOT_TAKEN!r})")
    planted = record["planted"]
    if not isinstance(planted, dict) or set(planted) != PLANTED_KEYS:
        return [*problems, "planted keys differ"]
    gem = expected[PIXEL_KEYS[0]]
    if planted["changed_fixture_file"] != gem["file"]:
        problems.append("the planted proof must change the gem's fixture PNG")
    if planted["capture_failed"] is not True or planted["failing_verdicts"] != [PIXEL_KEYS[0]] or planted["unchanged_verdicts_identical"] != len(PIXEL_KEYS) - 1:
        problems.append("the planted proof must fail on exactly the changed image and keep the other two identical")
    return problems


# ---- the file-system side ----

def chromium() -> str | None:
    wanted = os.environ.get("REHEARSAL_CHROMIUM")
    if wanted:
        return wanted
    return next((c for c in CHROMIUM_CANDIDATES if Path(c).exists()), None)


def _run_capture(env_extra: dict[str, str]) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_extra}
    cmd = ["npx", "playwright", "test", "-c", "playwright.bundle.config.ts"]
    if shutil.which("systemd-run"):
        cmd = ["systemd-run", "--user", "--scope", "-p", "MemoryMax=4G", "--quiet", *cmd]
    return subprocess.run(cmd, cwd=FRONTEND, env=env, check=False)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False).stdout


def dirty_capture_files() -> list[str]:
    """Files that define the capture and are modified or untracked: the record names the commit it ran on, so it must not be written from a dirty tree."""
    paths = ["frontend/src/visualAssets", "frontend/rehearsal-capture", "frontend/vite.rehearsal-bundle.config.ts", "frontend/playwright.bundle.config.ts", "tools/visual_assets_bundle_capture.py"]
    return [line[3:] for line in _git("status", "--porcelain", "--", *paths).splitlines() if len(line) > 3]


def main() -> int:
    sys.path.insert(0, str(REPO))
    browser = chromium()
    if browser is None:
        print("no Chromium found: set REHEARSAL_CHROMIUM to an installed Chromium or Chrome", file=sys.stderr)
        return 2
    if not (FRONTEND / "node_modules").is_dir():
        print("frontend/node_modules is missing: run `npm ci` in frontend/ first (this target adds no dependency)", file=sys.stderr)
        return 2
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    OUT_DIR.mkdir(parents=True)
    good_out, planted_out = OUT_DIR / "good.json", OUT_DIR / "planted.json"

    print("== 1/2 the real bundle: build, preview, capture")
    if _run_capture({"REHEARSAL_CHROMIUM": browser, "REHEARSAL_BUNDLE_EVIDENCE_OUT": str(good_out)}).returncode != 0:
        print("the capture of the real bundle FAILED: no record written", file=sys.stderr)
        return 1
    good = json.loads(good_out.read_text())

    print("== 2/2 the planted proof: one pixel changed in one fixture PNG of a copy of the bundle; the same capture must FAIL")
    manifest = json.loads((FIXTURES / "rehearsal" / "runtime_manifest.json").read_text())
    gem_file = next(e["file"] for e in manifest["entries"] if e["visual_key"] == PIXEL_KEYS[0])
    planted_bundle = OUT_DIR / "planted-bundle"
    shutil.copytree(FRONTEND / "e2e-artifacts" / "rehearsal-bundle", planted_bundle)
    target = find_hashed_file(planted_bundle, gem_file[: -len(".png")])
    original = target.read_bytes()
    target.write_bytes(plant_one_pixel(original))
    assert target.read_bytes() != original
    planted_exit = _run_capture({"REHEARSAL_CHROMIUM": browser, "REHEARSAL_BUNDLE_EVIDENCE_OUT": str(planted_out), "REHEARSAL_BUNDLE_PLANTED_DIR": str(planted_bundle)}).returncode
    if planted_exit == 0 or not planted_out.is_file():
        print("the planted wrong asset was NOT caught (or the run left no evidence): the check cannot be trusted; no record written", file=sys.stderr)
        return 1
    planted = json.loads(planted_out.read_text())

    vite_version = subprocess.run(["npx", "vite", "--version"], cwd=FRONTEND, capture_output=True, text=True, check=False).stdout.strip().splitlines()[-1]
    record = compose_record(
        good, planted, planted_exit, changed_file=gem_file, commit=_git("rev-parse", "HEAD").strip(),
        run_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), vite_version=vite_version,
    )
    problems = record_problems(record)
    if problems:
        print(f"no evidence record written: it would be invalid ({problems})", file=sys.stderr)
        return 1
    dirty = dirty_capture_files()
    if dirty:
        print(f"no evidence record written: capture files are not committed ({dirty[:5]}); the record names the commit it ran on. Raw evidence is in {OUT_DIR}", file=sys.stderr)
        return 1
    RECORD_PATH.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"evidence record written: {RECORD_PATH.relative_to(REPO)} (commit it; screenshots and the bundle are not committed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
