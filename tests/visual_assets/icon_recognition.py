"""The blind recognition check: render every icon unlabelled, have a FRESH agent with no project context name it, score the answers against the spec (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`).

Why: every gate of the sheet rule measures that icons can be told APART; none measures that an icon reads as its object (NN/G tests icons "in isolation, in the absence of a text label" and asks people
to guess). Four misreads in 36 icons passed every gate (the debuff frame as a smile, the shrine as a bell, the ruins as a boot, the sword as a cleaver).

Evidence, not a CI gate: the answers come from a model, so they are not deterministic. What IS deterministic and tested here: the rendering, the neutral shuffled ids (an image's file name and
content carry no key, family or subject), the manifest hashes, the candidate lists (the intended name once plus the spec's distractors, shuffled, plus "none of these"), and the scoring.

Three passes, each by a different fresh agent so none is primed by another:
  1. free text: "what is this? name the object" for every image;
  2. choice: the same images, each with its candidate list;
  3. era (theme fit, D21): "which era or setting does this belong to?"; an answer naming a modern or futuristic setting flags the icon.
An icon is **flagged** when its free-text answer contains none of the spec's synonyms as a whole word. The agent's prompt, model, image hashes and every answer are stored with the result.
"""

from __future__ import annotations

import hashlib
import json
import random
import struct
import zlib
from pathlib import Path

from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets.icon_specs import MODERN_TERMS, Spec, has_word

PLATE_KEY = "icon.plate.location"
PANELS = {"dark": (0x11, 0x18, 0x27), "light": (0xE5, 0xE7, 0xEB)}
TILES = {"dark": (0x1A, 0x1D, 0x27), "light": (0xC8, 0xD8, 0xE8)}  # terrain-v1's darkest (floor) and brightest (snow) fills, under location glyphs
SCALES = (1, 4)
GAP = 6
NONE_OF_THESE = "none of these"


def _png(width: int, height: int, rgb: list[tuple[int, int, int]]) -> bytes:
    raw = b"".join(b"\x00" + b"".join(bytes(rgb[y * width + x]) for x in range(width)) for y in range(height))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def _layers(key: str, sprites: dict[str, rule.Sprite]) -> list[rule.Sprite]:
    return [sprites[PLATE_KEY], sprites[key]] if key.startswith("icon.marker.") else [sprites[key]]


def render(key: str, sprites: dict[str, rule.Sprite]) -> bytes:
    """One PNG per icon: its native size ("1x") and four times larger, each on a dark and a light panel; a location glyph sits on the plate over the darkest and the brightest terrain fill. No text."""
    layers = _layers(key, sprites)
    native = layers[-1].width if not key.startswith("icon.marker.") else layers[0].width
    panels = [(scale, name) for scale in SCALES for name in PANELS]
    pad = 2
    cell = lambda scale: (native + 2 * pad) * scale  # noqa: E731
    width = sum(cell(s) for s, _ in panels) + GAP * (len(panels) - 1)
    height = cell(max(SCALES))
    canvas = [(0x80, 0x80, 0x80)] * (width * height)
    x_at = 0
    for scale, name in panels:
        side = cell(scale)
        bg = TILES[name] if key.startswith("icon.marker.") else PANELS[name]
        top = (height - side) // 2
        for y in range(side):
            for x in range(side):
                canvas[(top + y) * width + x_at + x] = bg
        for layer in layers:
            for i, (r, g, b, a) in enumerate(layer.rgba):
                if not a:
                    continue
                px, py = i % layer.width, i // layer.width
                for dy in range(scale):
                    for dx in range(scale):
                        canvas[(top + (py + pad) * scale + dy) * width + x_at + (px + pad) * scale + dx] = (r, g, b)
        x_at += side + GAP
    return _png(width, height, canvas)


def build_blind_set(out_dir: Path, sprites: dict[str, rule.Sprite], keys: list[str], seed: int) -> dict:
    """Write neutral, shuffled images (`icon-01.png` ...) into `out_dir` and return the answer key (id -> icon key) and the manifest. The caller keeps the answer key OUT of `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    order = sorted(keys)
    random.Random(seed).shuffle(order)
    key_of, hashes = {}, {}
    for n, key in enumerate(order, start=1):
        ident = f"icon-{n:02d}"
        data = render(key, sprites)
        (out_dir / f"{ident}.png").write_bytes(data)
        key_of[ident] = key
        hashes[ident] = "sha256:" + hashlib.sha256(data).hexdigest()
    return {"seed": seed, "answer_key": key_of, "image_hashes": hashes}


FREE_PROMPT = (
    "Each of the image files listed below is a small pixel-art icon from a fantasy game, shown four ways on one strip (native size and 4x, on a dark and a light background). "
    "Some sit on a grey plate. For EVERY image, name the object it depicts in one to four words, exactly as you read it at a glance; if you are unsure, say what it looks most like. "
    "Do not open any other file, do not search the file system, and do not guess from file names. Reply with ONLY a JSON object mapping each image's file name without the extension to your answer, "
    'for example {{"icon-01": "a wooden chair"}}.\n\nFiles:\n{files}\n'
)
CHOICE_PROMPT = (
    "Each of the image files listed below is a small pixel-art icon from a fantasy game, shown four ways on one strip (native size and 4x, on a dark and a light background). "
    "Some sit on a grey plate. For EVERY image, pick the ONE candidate that best names what it depicts, or '" + NONE_OF_THESE + "'. "
    "Do not open any other file and do not search the file system. Reply with ONLY a JSON object mapping each image's file name without the extension to the exact candidate text you picked.\n\n{blocks}\n"
)


ERAS = ("medieval or fantasy", "ancient", "modern", "futuristic", "cannot tell")
MODERN_ERAS = ("modern", "futuristic")
ERA_PROMPT = (
    "Each of the image files listed below is a small pixel-art icon from a game. Shown four ways on one strip (native size and 4x, on a dark and a light background); some sit on a grey plate. "
    "For EVERY image, say which era or setting the depicted object (or symbol) belongs to. Answer with exactly one of: " + ", ".join(f"'{e}'" for e in ERAS) + ", then a colon, then the object in two to four words, "
    "for example 'ancient: a clay jug'. Do not open any other file and do not search the file system. Reply with ONLY a JSON object mapping each image's file name without the extension to your answer.\n\nFiles:\n{files}\n"
)


def era_prompt(directory: Path, ids: list[str]) -> str:
    return ERA_PROMPT.format(files="\n".join(str(directory / f"{i}.png") for i in sorted(ids)))


def score_era(answer: str) -> dict:
    """The era question (D21, theme fit). An icon is flagged when the answer names a modern or futuristic era, OR when the object it names is a modern one (`MODERN_TERMS`): a first run answered "cannot tell: a red toolbox", so the era word alone is not enough."""
    era, _, thing = answer.partition(":")
    era, thing = era.strip().lower(), thing.strip()
    modern_object = [t for t in MODERN_TERMS if has_word(thing, t)]
    return {"era": era, "object": thing, "modern_object_named": modern_object, "flagged": era.startswith(MODERN_ERAS) or bool(modern_object)}


def free_prompt(directory: Path, ids: list[str]) -> str:
    return FREE_PROMPT.format(files="\n".join(str(directory / f"{i}.png") for i in sorted(ids)))


def candidates(spec: Spec, seed: int) -> list[str]:
    """The intended name (the spec's subject) once, the spec's distractors and `none of these`, in a seeded shuffle with `none of these` last."""
    options = [spec.subject] + [f"a {d}" if not d.startswith(("a ", "an ")) else d for d in spec.distractors]
    random.Random(f"{seed}:{spec.key}").shuffle(options)
    return options + [NONE_OF_THESE]


def choice_prompt(directory: Path, answer_key: dict[str, str], specs: dict[str, Spec], seed: int) -> str:
    blocks = []
    for ident in sorted(answer_key):
        opts = candidates(specs[answer_key[ident]], seed)
        blocks.append(f"{directory / (ident + '.png')}\n" + "\n".join(f"  - {o}" for o in opts))
    return CHOICE_PROMPT.format(blocks="\n\n".join(blocks))


def score_free(answer: str, spec: Spec) -> dict:
    text = answer.lower()
    named = [w for w in spec.synonyms if has_word(text, w)]
    confused = [w for w in _terms(spec.must_not_read_as) if has_word(text, w)]
    modern = [t for t in MODERN_TERMS if has_word(text, t)]  # D21: an answer that names a modern object ("hammer and wrench", "gear emblem") is a misread even when it also names the right thing
    return {"named": bool(named), "matched": named, "confused_with": [] if named else confused, "modern_object_named": modern, "flagged": not named or bool(modern)}


def _terms(must_not: str) -> list[str]:
    parts = [p.strip().lower() for p in must_not.replace(" or ", ",").split(",")]
    return [p.removeprefix("a ").removeprefix("an ") for p in parts if p]


def score_choice(answer: str, spec: Spec) -> dict:
    picked = answer.strip().lower()
    return {"correct": picked == spec.subject.lower(), "picked": answer.strip()}


def evaluate(answer_key: dict[str, str], free: dict[str, str], choice: dict[str, str], specs: dict[str, Spec], era: dict[str, str] | None = None) -> dict:
    rows = {}
    for ident, key in sorted(answer_key.items(), key=lambda kv: kv[1]):
        spec = specs[key]
        f = score_free(free.get(ident, ""), spec) if ident in free else None
        c = score_choice(choice[ident], spec) if ident in choice else None
        e = score_era(era[ident]) if era and ident in era else None
        rows[key] = {"free_text": free.get(ident), "free": f, "choice": c, "era_answer": (era or {}).get(ident), "era": e, "status": spec.status}
    flagged = sorted(k for k, r in rows.items() if r["free"] and r["free"]["flagged"])
    missed = sorted(k for k, r in rows.items() if r["choice"] and not r["choice"]["correct"])
    out = {"flagged_free_text": flagged, "missed_in_choice": missed, "results": rows}
    if era:
        out["flagged_era"] = sorted(k for k, r in rows.items() if r["era"] and r["era"]["flagged"])
    return out


def dumps(value: dict) -> str:
    return json.dumps(value, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    import argparse
    import sys

    from tests.visual_assets import icon_lookalikes, icon_specs

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write the neutral images and both prompts; the answer key goes to --private")
    b.add_argument("--images", type=Path, required=True)
    b.add_argument("--private", type=Path, required=True, help="directory for the answer key and manifest (NOT shown to the agent)")
    b.add_argument("--seed", type=int, required=True)
    b.add_argument("--proposed", action="store_true", help="render the set as it would stand with the owner-fix revisions (icons-owner-fixes-v1) in place of the adopted r0001 drawings")
    e = sub.add_parser("evaluate", help="score the two answer files against the specs")
    e.add_argument("--private", type=Path, required=True)
    e.add_argument("--free", type=Path, required=True)
    e.add_argument("--choice", type=Path, required=True)
    e.add_argument("--era", type=Path, default=None, help="the answers to the era question (theme fit, D21)")
    args = ap.parse_args()
    specs = icon_specs.load()
    if args.cmd == "build":
        if args.proposed:
            from tests.visual_assets import icon_owner_fixes_draft_set

            sprites = icon_owner_fixes_draft_set.proposed_sprites()
        else:
            sprites = icon_lookalikes.all_icon_sprites()
        info = build_blind_set(args.images, sprites, sorted(sprites), args.seed)
        args.private.mkdir(parents=True, exist_ok=True)
        (args.private / "blind_info.json").write_text(dumps(info))
        (args.private / "task_free.txt").write_text(free_prompt(args.images, sorted(info["answer_key"])))
        (args.private / "task_choice.txt").write_text(choice_prompt(args.images, info["answer_key"], specs, args.seed))
        (args.private / "task_era.txt").write_text(era_prompt(args.images, sorted(info["answer_key"])))
        print(f"wrote {len(info['answer_key'])} images to {args.images}; answer key and prompts in {args.private}")
    else:
        info = json.loads((args.private / "blind_info.json").read_text())
        out = evaluate(info["answer_key"], json.loads(args.free.read_text()), json.loads(args.choice.read_text()), specs, json.loads(args.era.read_text()) if args.era else None)
        sys.stdout.write(dumps(out))
