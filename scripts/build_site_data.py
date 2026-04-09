from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
DATA_DIR = ROOT / "data"
FAMILY_ORDER = {"MX": 0, "MX 1.2": 1, "EX": 2}


def compact_spacing_around_punctuation(text: str) -> str:
    text = re.sub(r"\s+-\s+", " - ", text)
    text = re.sub(r"\s+([,.:;])", r"\1", text)
    text = re.sub(r"([A-Za-z])-\s+([A-Za-z])", r"\1 - \2", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def infer_metadata_from_title(title: str) -> dict:
    normalized = title.replace("MX1.2", "MX 1.2").lower()
    if "stark varg ex" in normalized:
        return {
            "source_family": "EX",
            "applicability_label": "EX",
            "applicable_models": ["EX"],
        }
    if "mx 1.2 / ex" in normalized or "stark varg mx 1.2" in normalized:
        return {
            "source_family": "MX 1.2",
            "applicability_label": "MX 1.2 / EX",
            "applicable_models": ["MX 1.2", "EX"],
        }
    return {
        "source_family": "MX",
        "applicability_label": "MX",
        "applicable_models": ["MX"],
    }


def metadata_from_manifest(manifest: dict) -> dict:
    metadata = infer_metadata_from_title(manifest["title"])
    if manifest.get("source_family"):
        metadata["source_family"] = manifest["source_family"]
    if manifest.get("applicability_label"):
        metadata["applicability_label"] = manifest["applicability_label"]
    if manifest.get("applicable_models"):
        metadata["applicable_models"] = list(manifest["applicable_models"])
    return metadata


def strip_model_suffix(title: str) -> str:
    title = compact_spacing_around_punctuation(title.replace("MX1.2", "MX 1.2"))
    patterns = (
        r"\s*-\s*Stark VARG MX\s*$",
        r"\s*Stark VARG MX\s*$",
        r"\s*-\s*Stark VARG\s*$",
        r"\s*Stark VARG\s*$",
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
    title = re.sub(r"\s+the\s+Stark VARG MX\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+the\s+Stark VARG\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*on your Stark VARG EX\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*Stark Varg EX\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+(?:the|your)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*$", "", title)
    return compact_spacing_around_punctuation(title)


def build_dataset() -> list[dict]:
    items: list[dict] = []
    for manifest_path in sorted(VIDEOS_DIR.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        title = manifest["title"]
        metadata = metadata_from_manifest(manifest)
        item = {
            "slug": manifest_path.parent.name,
            "title": strip_model_suffix(title),
            "full_title": title,
            "source_family": metadata["source_family"],
            "applicability_label": metadata["applicability_label"],
            "applicable_models": metadata["applicable_models"],
            "pdf_url": f"videos/{manifest_path.parent.name}/{manifest['pdf_output']}",
            "video_url": manifest["video_url"],
        }
        items.append(item)

    items.sort(key=lambda item: (FAMILY_ORDER.get(item["source_family"], 99), item["title"].lower()))
    return items


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"tutorials": build_dataset()}
    (DATA_DIR / "tutorials.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
