from __future__ import annotations

import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a per-video tutorial PDF to PNG page previews.")
    parser.add_argument("video_dir", help="Path to a per-video workspace directory under videos/.")
    parser.add_argument("--scale", type=float, default=1.35, help="Rendering scale factor.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video_dir = Path(args.video_dir).resolve()
    manifest = json.loads((video_dir / "manifest.json").read_text(encoding="utf-8"))
    pdf_path = video_dir / manifest["pdf_output"]
    render_dir = video_dir / manifest["pdf_render_dir"]
    render_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(pdf_path))
    for index in range(len(pdf)):
        page = pdf[index]
        bitmap = page.render(scale=args.scale)
        bitmap.to_pil().save(render_dir / f"page-{index + 1}.png")

    print(f"pages={len(pdf)}")


if __name__ == "__main__":
    main()
