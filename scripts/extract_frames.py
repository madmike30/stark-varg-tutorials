from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import imageio
import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract reproducible screenshots for a Stark tutorial video.")
    parser.add_argument("video_dir", help="Path to a per-video workspace directory under videos/.")
    return parser.parse_args()


def extract_frame(video_path: Path, timestamp_seconds: int, output_path: Path) -> None:
    reader = imageio.get_reader(video_path, "ffmpeg")
    try:
        meta = reader.get_meta_data()
        fps = float(meta.get("fps") or 25.0)
        duration = float(meta.get("duration") or 0.0)
        target_index = int(timestamp_seconds * fps)
        if duration > 0:
            max_index = max(0, int(duration * fps) - 1)
            target_index = min(target_index, max_index)
        frame = reader.get_data(target_index)
    finally:
        reader.close()
    iio.imwrite(output_path, frame)


def build_contact_sheet(image_paths: list[Path], output_path: Path, columns: int = 3) -> None:
    images = [Image.open(path).convert("RGB") for path in image_paths]
    if not images:
        return

    thumb_width = 420
    thumb_height = int(thumb_width * 9 / 16)
    label_height = 40
    padding = 24
    rows = math.ceil(len(images) / columns)

    sheet_width = columns * thumb_width + (columns + 1) * padding
    sheet_height = rows * (thumb_height + label_height) + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), color=(245, 245, 245))
    font = ImageFont.load_default()

    for idx, (img, path) in enumerate(zip(images, image_paths)):
        row = idx // columns
        col = idx % columns
        x = padding + col * thumb_width
        y = padding + row * (thumb_height + label_height)
        thumb = img.resize((thumb_width, thumb_height))
        sheet.paste(thumb, (x, y))

        draw = ImageDraw.Draw(sheet)
        label = path.stem.replace("_", " ")
        draw.text((x, y + thumb_height + 10), label, fill=(20, 20, 20), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=90)


def main() -> None:
    args = parse_args()
    video_dir = Path(args.video_dir).resolve()
    manifest_path = video_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    video_path = video_dir / manifest["source_video"]
    screenshot_dir = video_dir / manifest["screenshots_dir"]
    contact_sheet_path = video_dir / manifest["contact_sheet"]
    frames = manifest["frames"]

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []

    for frame in frames:
        timestamp_seconds = int(frame["timestamp"])
        name = frame["name"]
        output_path = screenshot_dir / f"{name}.jpg"
        extract_frame(video_path, timestamp_seconds, output_path)
        generated_paths.append(output_path)

    build_contact_sheet(generated_paths, contact_sheet_path)


if __name__ == "__main__":
    main()
