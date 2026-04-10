from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from rapidfuzz import fuzz

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_video_overlays import extract_overlays, normalize_text


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
TMP_DIR = ROOT / "tmp" / "mx_overlay_audit"
VIDEOS_TMP_DIR = TMP_DIR / "videos"
REPORT_PATH = ROOT / "ORIGINAL_MX_OVERLAY_AUDIT.md"


def tutorial_text_for(video_dir: Path, manifest: dict) -> str:
    path = video_dir / manifest["tutorial_markdown"]
    return path.read_text(encoding="utf-8")


def overlay_matches_guide(overlay_text: str, tutorial_text: str) -> bool:
    lowered = tutorial_text.lower()
    if overlay_text.lower() in lowered:
        return True
    overlay_words = set(re.findall(r"[a-z0-9]+", overlay_text.lower()))
    if len(overlay_words) < 2:
        return False
    for line in tutorial_text.splitlines():
        line_norm = normalize_text(line).lower()
        if not line_norm:
            continue
        if fuzz.ratio(overlay_text.lower(), line_norm) >= 84:
            return True
        line_words = set(re.findall(r"[a-z0-9]+", line_norm))
        if overlay_words and line_words:
            overlap = len(overlay_words & line_words) / len(overlay_words)
            if overlap >= 0.75:
                return True
    return False


def torque_values(texts: list[str]) -> set[str]:
    values = set()
    for text in texts:
        for match in re.finditer(r"(\d+(?:\.\d+)?)\s*Nm", text, flags=re.I):
            values.add(f"{match.group(1)} Nm")
    return values


def dedupe_overlays(overlays: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for item in overlays:
        text = normalize_text(item["text"])
        if not text:
            continue
        if cleaned and fuzz.ratio(text.lower(), cleaned[-1]["text"].lower()) >= 88:
            continue
        cleaned.append({"timestamp": item["timestamp"], "text": text})
    return cleaned


def ensure_video(video_dir: Path, manifest: dict) -> Path:
    url = manifest["video_url"]
    target = VIDEOS_TMP_DIR / f"{manifest['slug']}.mp4"
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "-f",
        "mp4/best[ext=mp4]/best",
        "-o",
        str(target),
        url,
    ]
    subprocess.run(cmd, check=True)
    return target


def main() -> None:
    lines = [
        "# Original MX Overlay Audit",
        "",
        "This report compares OCR-detected on-screen instruction overlays from the original MX tutorial videos against the current guide text.",
        "",
    ]

    for manifest_path in sorted(VIDEOS_DIR.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if manifest.get("source_family") != "MX" or manifest.get("applicability_label") != "MX":
            continue
        video_dir = manifest_path.parent
        tutorial_text = tutorial_text_for(video_dir, manifest)
        video_path = ensure_video(video_dir, manifest)
        overlays = dedupe_overlays(extract_overlays(video_path, fps_sample=0.5))
        missing = [item for item in overlays if not overlay_matches_guide(item["text"], tutorial_text)]
        overlay_torques = torque_values([item["text"] for item in overlays])
        guide_torques = torque_values([tutorial_text])
        missing_torques = sorted(overlay_torques - guide_torques, key=lambda value: float(value.split()[0]))

        lines.append(f"## `{video_dir.name}`")
        lines.append("")
        lines.append(f"- OCR overlays detected: **{len(overlays)}**")
        lines.append(f"- Overlay texts not clearly reflected in guide: **{len(missing)}**")
        lines.append(f"- Torque values shown in video but missing from guide: **{', '.join(missing_torques) if missing_torques else 'None'}**")
        if missing:
            lines.append("- First missing overlays:")
            for item in missing[:10]:
                lines.append(f"  - `{item['timestamp']}s` {item['text']}")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
