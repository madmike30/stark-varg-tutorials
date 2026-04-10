from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
REPORT_PATH = ROOT / "GUIDE_REVIEW_REPORT.md"
DOC_CACHE = ROOT / "tmp" / "official_docs_review"

GENERIC_PATTERNS = [
    "Remove or move aside the surrounding part, cover, or hardware needed to reach",
    "Remove the bolts, screws, nuts, or clips that directly secure",
    "Release any bracket, clip, spacer, linkage, or connector that still ties",
    "Lift, slide, or guide",
    "Install the main retaining hardware",
]


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("stark varg", "").replace("stark future", "")
    text = text.replace("how to ", "")
    text = text.replace("the ", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def significant_words(text: str) -> set[str]:
    stopwords = {
        "remove",
        "install",
        "and",
        "the",
        "how",
        "to",
        "stark",
        "varg",
        "future",
        "of",
        "on",
        "your",
        "assembly",
        "procedure",
    }
    return {word for word in normalize(text).split() if word not in stopwords}


def get_docs() -> list[dict]:
    with urllib.request.urlopen("https://api.starkfuture.com/v2/technical-documents?limit=200&page=1", timeout=30) as response:
        data = json.load(response)
    return data["docs"]


def read_doc_text(code: str, url: str) -> str:
    DOC_CACHE.mkdir(parents=True, exist_ok=True)
    path = DOC_CACHE / f"{code}.pdf"
    if not path.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def find_best_doc(title: str, docs: list[dict]) -> dict | None:
    target = normalize(title)
    target_words = significant_words(title)
    best: tuple[int, dict] | None = None
    for doc in docs:
        name_obj = doc.get("name", {})
        name = name_obj.get("en", "") if isinstance(name_obj, dict) else str(name_obj)
        if not name:
            continue
        score = 0
        doc_norm = normalize(name)
        doc_words = significant_words(name)
        if target == doc_norm:
            score = 100
        elif target_words and target_words == doc_words:
            score = 80
        elif target_words and doc_words and target_words <= doc_words:
            score = 70
        elif target_words and doc_words and doc_words <= target_words:
            score = 65
        elif target_words and doc_words:
            shared = len(target_words & doc_words)
            union = len(target_words | doc_words)
            if shared >= 2 and union and (shared / union) >= 0.75:
                score = int((shared / union) * 50)
        if score and (best is None or score > best[0]):
            best = (score, doc)
    return best[1] if best else None


def main() -> None:
    docs = get_docs()
    doc_candidates = []
    for doc in docs:
        name_obj = doc.get("name", {})
        name = name_obj.get("en", "") if isinstance(name_obj, dict) else str(name_obj)
        url = doc.get("file", {}).get("url", "")
        code = doc.get("code", "")
        if not name or not url or not code:
            continue
        if name.lower().startswith(("remove and install", "change ", "bleeding ", "draining and filling")):
            doc_candidates.append(doc)

    manifests = []
    for manifest_path in sorted(VIDEOS_DIR.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        tutorial_path = manifest_path.parent / manifest["tutorial_markdown"]
        if tutorial_path.exists():
            tutorial_text = tutorial_path.read_text(encoding="utf-8")
        else:
            tutorial_text = ""
        manifests.append((manifest_path.parent, manifest, tutorial_text))

    structural_ok = 0
    generic_guides: list[tuple[str, int]] = []
    torque_flags: list[str] = []

    for video_dir, manifest, tutorial_text in manifests:
        pdf_path = video_dir / manifest["pdf_output"]
        render_dir = video_dir / manifest["pdf_render_dir"]
        steps = re.findall(r"^###\s+(\d+)\.", tutorial_text, flags=re.M)
        images = re.findall(r"!\[[^\]]*\]\((assets/screenshots/[^)]+)\)", tutorial_text)
        pdf_pages = len(PdfReader(str(pdf_path)).pages) if pdf_path.exists() else 0
        rendered_pages = len(list(render_dir.glob("page-*.png"))) if render_dir.exists() else 0
        if tutorial_text and pdf_path.exists() and len(steps) == len(images) and pdf_pages == rendered_pages:
            structural_ok += 1

        generic_hits = sum(tutorial_text.count(pattern) for pattern in GENERIC_PATTERNS)
        if generic_hits:
            generic_guides.append((video_dir.name, generic_hits))

        if manifest.get("source_family") != "MX" or manifest.get("applicability_label") != "MX":
            continue

        doc = find_best_doc(manifest["title"], doc_candidates)
        if not doc:
            continue

        doc_name = doc["name"]["en"] if isinstance(doc["name"], dict) else str(doc["name"])
        doc_text = read_doc_text(doc["code"], doc["file"]["url"])
        guide_nm = sorted(set(re.findall(r"(\d+(?:\.\d+)?\s*Nm)", tutorial_text)))
        doc_nm = sorted(set(re.findall(r"(\d+(?:\.\d+)?\s*Nm)", doc_text)))
        if doc_nm and guide_nm != doc_nm:
            torque_flags.append(
                f"- `{video_dir.name}` vs `{doc['code']} {doc_name}`: guide={guide_nm or ['none']}, manual={doc_nm}"
            )

    lines = [
        "# Guide Review Report",
        "",
        f"- Total guide folders reviewed: **{len(manifests)}**",
        f"- Structural pass (steps/images/PDF renders aligned): **{structural_ok}/{len(manifests)}**",
        f"- Guides using generic template wording: **{len(generic_guides)}**",
        f"- Original MX guides with torque/manual differences still worth manual review: **{len(torque_flags)}**",
        "",
        "## Generic Template Guides",
        "",
    ]

    if generic_guides:
        for name, hits in generic_guides:
            lines.append(f"- `{name}`: {hits} generic pattern hits")
    else:
        lines.append("- None")

    lines.extend(["", "## Remaining Torque Review Flags", ""])
    if torque_flags:
        lines.extend(torque_flags)
    else:
        lines.append("- None")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
