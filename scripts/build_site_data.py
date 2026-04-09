from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
DATA_DIR = ROOT / "data"


def compact_spacing_around_punctuation(text: str) -> str:
    text = re.sub(r"\s+-\s+", " - ", text)
    text = re.sub(r"\s+([,.:;])", r"\1", text)
    text = re.sub(r"([A-Za-z])-\s+([A-Za-z])", r"\1 - \2", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def is_ex_specific_title(title: str) -> bool:
    return "stark varg ex" in title.lower()


def applicability_label_for_title(title: str) -> str:
    return "EX" if is_ex_specific_title(title) else "MX 1.2 / EX"


def applicable_models_for_title(title: str) -> list[str]:
    return ["EX"] if is_ex_specific_title(title) else ["MX 1.2", "EX"]


def strip_model_suffix(title: str) -> str:
    title = compact_spacing_around_punctuation(title.replace("MX1.2", "MX 1.2"))
    patterns = (
        r"\s*-\s*Stark VARG MX 1\.2\s*/\s*EX\s*$",
        r"\s*Stark VARG MX 1\.2\s*/\s*EX\s*$",
        r"\s*-\s*Stark VARG MX 1\.2\s*$",
        r"\s*Stark VARG MX 1\.2\s*$",
    )
    changed = True
    while changed:
        changed = False
        for pattern in patterns:
            next_title = re.sub(pattern, "", title, flags=re.IGNORECASE)
            if next_title != title:
                title = next_title
                changed = True
    title = re.sub(r"\s*on your Stark VARG EX\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*Stark Varg EX\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*$", "", title)
    return compact_spacing_around_punctuation(title)


def build_dataset() -> list[dict]:
    items: list[dict] = []
    for manifest_path in sorted(VIDEOS_DIR.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        title = manifest["title"]
        applicable_models = applicable_models_for_title(title)
        item = {
            "slug": manifest_path.parent.name,
            "title": strip_model_suffix(title),
            "full_title": title,
            "source_family": "EX" if is_ex_specific_title(title) else "MX",
            "applicability_label": applicability_label_for_title(title),
            "applicable_models": applicable_models,
            "pdf_url": f"videos/{manifest_path.parent.name}/{manifest['pdf_output']}",
            "video_url": manifest["video_url"],
        }
        items.append(item)

    items.sort(key=lambda item: (item["source_family"], item["title"].lower()))
    return items


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"tutorials": build_dataset()}
    (DATA_DIR / "tutorials.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
