from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import imageio
import pytesseract
from PIL import Image, ImageOps
from rapidfuzz import fuzz


TESSERACT_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract lower-left overlay text from a Stark video.")
    parser.add_argument("video_dir", help="Path to a per-video workspace directory under videos/.")
    parser.add_argument("--fps-sample", type=float, default=1.0, help="Frames per second to sample.")
    parser.add_argument("--crop-height", type=float, default=0.24, help="Bottom crop height ratio.")
    parser.add_argument("--crop-width", type=float, default=0.58, help="Left crop width ratio.")
    parser.add_argument(
        "--output",
        default="tmp/overlay-audit.json",
        help="Relative output path inside the video dir.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"[^A-Za-z0-9.%/+ -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" Nn", " Nm").replace(" nm", " Nm")
    text = text.replace(" lnk ", " link ")
    text = text.replace(" Insta ", " Install ")
    return text.strip()


def looks_like_instruction(text: str) -> bool:
    lowered = text.lower()
    verbs = [
        "remove",
        "install",
        "loosen",
        "tighten",
        "insert",
        "slide",
        "push",
        "hold",
        "ensure",
        "run",
        "check",
        "bleed",
        "change",
        "fill",
        "open",
        "close",
        "disconnect",
        "connect",
        "pull",
        "drain",
    ]
    if len(text) < 8:
        return False
    if not any(char.isalpha() for char in text):
        return False
    return any(verb in lowered for verb in verbs)


def ocr_overlay(frame) -> str:
    img = Image.fromarray(frame).convert("L")
    crop = img.crop((0, int(img.height * (1 - 0.24)), int(img.width * 0.58), img.height))
    crop = ImageOps.autocontrast(crop)
    crop = crop.resize((crop.width * 2, crop.height * 2))
    crop = crop.point(lambda p: 255 if p > 150 else 0)
    text = pytesseract.image_to_string(crop, config="--psm 6")
    return normalize_text(text)


def extract_overlays(video_path: Path, fps_sample: float = 1.0) -> list[dict]:
    reader = imageio.get_reader(video_path, "ffmpeg")
    try:
        meta = reader.get_meta_data()
        fps = float(meta.get("fps") or 25.0)
        duration = float(meta.get("duration") or 0.0)
        step = max(1, int(round(fps / fps_sample)))
        total_frames = int(duration * fps) if duration > 0 else None

        overlays: list[dict] = []
        previous_text = ""
        previous_timestamp = None
        frame_index = 0

        while True:
            if total_frames is not None and frame_index >= total_frames:
                break
            try:
                frame = reader.get_data(frame_index)
            except Exception:
                break
            timestamp = frame_index / fps
            text = ocr_overlay(frame)
            if looks_like_instruction(text):
                if not previous_text or fuzz.ratio(text.lower(), previous_text.lower()) < 88:
                    overlays.append(
                        {
                            "timestamp": round(timestamp, 2),
                            "text": text,
                        }
                    )
                    previous_text = text
                    previous_timestamp = timestamp
                elif previous_timestamp is not None and (timestamp - previous_timestamp) > 8:
                    overlays.append(
                        {
                            "timestamp": round(timestamp, 2),
                            "text": text,
                        }
                    )
                    previous_text = text
                    previous_timestamp = timestamp
            frame_index += step
    finally:
        reader.close()

    return overlays


def main() -> None:
    args = parse_args()
    video_dir = Path(args.video_dir).resolve()
    manifest = json.loads((video_dir / "manifest.json").read_text(encoding="utf-8-sig"))
    video_path = video_dir / manifest["source_video"]
    if not video_path.exists():
        raise SystemExit(f"Missing source video: {video_path}")

    overlays = extract_overlays(video_path, fps_sample=args.fps_sample)
    output_path = video_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(overlays, indent=2), encoding="utf-8")
    print(f"overlays={len(overlays)}")
    for item in overlays:
        print(f"{item['timestamp']:>7}: {item['text']}")


if __name__ == "__main__":
    main()
