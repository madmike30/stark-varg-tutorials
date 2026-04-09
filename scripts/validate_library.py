from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"


def main() -> None:
    lines = ["# Validation Report", ""]
    overall_ok = True

    for video_dir in sorted(path for path in VIDEOS_DIR.iterdir() if path.is_dir() and not path.name.startswith("_")):
        tutorial = video_dir / "tutorial.md"
        manifest = video_dir / "manifest.json"
        pdfs = list((video_dir / "output" / "pdf").glob("*.pdf"))
        renders = list((video_dir / "tmp" / "pdfs").glob("page-*.png"))
        source_videos = list(video_dir.rglob("*.mp4"))

        if not tutorial.exists() or not manifest.exists() or not pdfs:
            overall_ok = False
            lines.append(f"- FAIL `{video_dir.name}`: missing tutorial, manifest, or PDF.")
            continue

        text = tutorial.read_text(encoding="utf-8")
        steps = re.findall(r"^###\s+(\d+)\.", text, flags=re.M)
        images = re.findall(r"!\[[^\]]*\]\((assets/screenshots/[^)]+)\)", text)
        pdf_pages = len(PdfReader(str(pdfs[0])).pages)

        ok = len(steps) == len(images) and pdf_pages == len(renders) and not source_videos
        overall_ok = overall_ok and ok
        status = "OK" if ok else "FAIL"
        lines.append(
            f"- {status} `{video_dir.name}`: steps={len(steps)}, images={len(images)}, pdf_pages={pdf_pages}, rendered_pages={len(renders)}, source_videos={len(source_videos)}"
        )

    lines.append("")
    lines.append(f"Overall status: {'OK' if overall_ok else 'FAIL'}")
    (ROOT / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
