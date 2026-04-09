from __future__ import annotations

import json
import subprocess
from pathlib import Path

import build_library


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"


def update_tutorial_markdown(tutorial_path: Path, new_title: str, applicability_label: str) -> bool:
    lines = tutorial_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return False

    changed = False
    if lines[0] != f"# {new_title}":
        lines[0] = f"# {new_title}"
        changed = True

    source_index = next((index for index, line in enumerate(lines) if line.startswith("Source video: ")), None)
    if source_index is not None:
        applicable_line = f"Applicable models: `{applicability_label}`"
        first_content_index = source_index + 1
        while first_content_index < len(lines) and not lines[first_content_index].strip():
            del lines[first_content_index]
            changed = True

        while first_content_index < len(lines) and lines[first_content_index].startswith("Applicable models: "):
            del lines[first_content_index]
            changed = True
            while first_content_index < len(lines) and not lines[first_content_index].strip():
                del lines[first_content_index]
                changed = True

        lines[first_content_index:first_content_index] = ["", applicable_line, ""]
        changed = True

    if changed:
        tutorial_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def rebuild_pdf(video_dir: Path) -> None:
    subprocess.run(["python", str(ROOT / "scripts" / "build_tutorial_pdf.py"), str(video_dir)], cwd=ROOT, check=True)


def main() -> None:
    for video_dir in sorted(path for path in VIDEOS_DIR.iterdir() if path.is_dir() and not path.name.startswith("_")):
        manifest_path = video_dir / "manifest.json"
        tutorial_path = video_dir / "tutorial.md"
        if not manifest_path.exists() or not tutorial_path.exists():
            continue

        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        original_title = manifest.get("title", "")
        new_title = build_library.tutorial_title_from_video_title(original_title)
        applicability_label = build_library.applicability_label_for_title(new_title)

        manifest_changed = False
        if manifest.get("title") != new_title:
            manifest["title"] = new_title
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            manifest_changed = True

        tutorial_changed = update_tutorial_markdown(tutorial_path, new_title, applicability_label)
        if manifest_changed or tutorial_changed:
            rebuild_pdf(video_dir)

    build_library.write_library_index([])
    subprocess.run(["python", str(ROOT / "scripts" / "build_site_data.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
