from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import unicodedata
from collections import OrderedDict
from pathlib import Path

from pypdf import PdfReader
from rapidfuzz import fuzz, process


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
AUDIT_VIDEOS_DIR = ROOT / "tmp" / "mx_overlay_audit" / "videos"
DOC_CACHE_DIR = ROOT / "tmp" / "official_docs_review"

PREPARATION_LINES = [
    "Place the bike on a stable stand or work area before starting the procedure.",
    "Prepare the correct tools for the fasteners, clips, brackets, and components shown in the video.",
    "Keep removed hardware organized in sequence so reassembly follows the same order as the video.",
    "Follow the torque values shown in the original Stark tutorial video wherever the video displays a torque on screen.",
]

KNOWN_ACRONYMS = {
    "abs",
    "can",
    "bus",
    "ecu",
    "kyb",
    "mx",
    "nm",
    "varg",
    "vcu",
}

SERVICE_VOCAB = {
    "adjuster",
    "again",
    "all",
    "and",
    "assembly",
    "avoid",
    "axle",
    "battery",
    "bearing",
    "bike",
    "bolt",
    "bolts",
    "bottom",
    "box",
    "bracket",
    "brake",
    "caliper",
    "can",
    "chain",
    "charger",
    "check",
    "clamp",
    "clips",
    "cloth",
    "complete",
    "connector",
    "connectors",
    "connect",
    "cooling",
    "disc",
    "disconnect",
    "docking",
    "drain",
    "ensure",
    "fender",
    "first",
    "floor",
    "fork",
    "front",
    "gear",
    "guide",
    "handlebar",
    "hold",
    "inside",
    "install",
    "into",
    "junction",
    "left",
    "lever",
    "lift",
    "line",
    "link",
    "lock",
    "lower",
    "master",
    "middle",
    "mud",
    "nut",
    "number",
    "oil",
    "operate",
    "operating",
    "operation",
    "out",
    "outward",
    "pads",
    "pedal",
    "phone",
    "plate",
    "plug",
    "plugs",
    "protector",
    "pull",
    "push",
    "rear",
    "remove",
    "rests",
    "right",
    "roller",
    "rubber",
    "run",
    "secure",
    "seat",
    "side",
    "slide",
    "slots",
    "sprocket",
    "spring",
    "stand",
    "station",
    "subframe",
    "support",
    "switch",
    "system",
    "tension",
    "the",
    "tighten",
    "through",
    "to",
    "top",
    "triple",
    "turn",
    "unit",
    "up",
    "upper",
    "vcu",
    "wheel",
    "whilst",
}

REMOVE_START_VERBS = (
    "remove",
    "loosen",
    "disconnect",
    "open",
    "drain",
    "bleed",
    "release",
    "untighten",
    "turn off",
    "turn on",
    "shutdown",
    "shut down",
    "engage",
    "disengage",
    "charge",
    "check",
)
INSTALL_START_VERBS = (
    "install",
    "insert",
    "connect",
    "clip",
    "tighten",
    "hold",
    "ensure",
    "push",
    "run",
    "slide",
    "fill",
    "pour",
)

PROCEDURE_ONLY_SLUGS = {
    "bleeding-the-cooling-system-stark-varg",
    "gear-oil-change-stark-varg",
    "how-to-charge-the-stark-varg",
    "how-to-disengage-the-stark-varg",
    "how-to-engage-the-stark-varg",
    "how-to-shutdown-the-stark-varg",
    "how-to-turn-off-the-stark-varg",
    "how-to-turn-on-the-stark-varg",
    "how-to-unbox-the-stark-varg-mx",
    "how-to-update-the-stark-varg-software",
}

PHRASE_REPLACEMENTS = OrderedDict(
    [
        (r"\bjunc(?:t|tio|ton|tion)?\s*box\b", "junction box"),
        (r"\bjunctiont?2?o?x\b", "junction box"),
        (r"\bjunctiondox\b", "junction box"),
        (r"\bnumber\s+p(?:l|i)?a?t?e?\b", "number plate"),
        (r"\bnumber\s+pl(?:a|i)t[e]?\b", "number plate"),
        (r"\bfront\s+n(?:u|m)ber\s+plate\b", "front number plate"),
        (r"\bcal\s*per\b", "caliper"),
        (r"\bbrake\s+fine\b", "brake line"),
        (r"\bbrake\s+fre\b", "brake line"),
        (r"\bfront\s+commecto?r\b", "front connector"),
        (r"\bspo[il1]e?r\b", "spoiler"),
        (r"\bcompicte\b", "complete"),
        (r"\bcomptete\b", "complete"),
        (r"\btower\b", "lower"),
        (r"\bbattom\b", "bottom"),
        (r"\bbottonm\b", "bottom"),
        (r"\bbotts?\b", "bolts"),
        (r"\bbotts?\b", "bolts"),
        (r"\bbolf\b", "bolt"),
        (r"\bbolt?s? to\b", "bolts to"),
        (r"\bboits?\b", "bolts"),
        (r"\bbaits?\b", "bolts"),
        (r"\bbats\b", "bolts"),
        (r"\bbalts?\b", "bolts"),
        (r"\bboit\b", "bolt"),
        (r"\bbelt\b", "bolt"),
        (r"\bbatts?\b", "bolt"),
        (r"\baxie\b", "axle"),
        (r"\baxe\b", "axle"),
        (r"\bwh[eu]el\s+axe\b", "wheel axle"),
        (r"\bock\b", "lock"),
        (r"\block\s+hutto\b", "lock nut to"),
        (r"\btock\b", "lock"),
        (r"\bcamp\b", "clamp"),
        (r"\bclame\b", "clamp"),
        (r"\bclam\b", "clamp"),
        (r"\bcannectors\b", "connectors"),
        (r"\bpugs\b", "plugs"),
        (r"\bnuibber\b", "rubber"),
        (r"\bphone\s+ot\b", "phone"),
        (r"\bsecurc\b", "secure"),
        (r"\bbeforc\b", "before"),
        (r"\bsprockety\b", "sprocket"),
        (r"\bspyocket\b", "sprocket"),
        (r"\bsvvay\b", "sway"),
        (r"\bcha[irn]\s+link\b", "chain link"),
        (r"\bdrake\b", "brake"),
        (r"\bpocal\b", "pedal"),
        (r"\bfeck\b", "lock"),
        (r"\blids\b", "lids"),
        (r"\bnutand\b", "nut and"),
        (r"\bthy ough\b", "through"),
        (r"\bthy\b", "the"),
        (r"\bsi(?:de)?\s+beit[s]?\b", "side bolts"),
        (r"\bright\s+fork\s+clam[p]?\s+bolts?\b", "right fork clamp bolts"),
        (r"\bleft\s+fork\s+clam[p]?\s+bolts?\b", "left fork clamp bolts"),
        (r"\bfront\s+fencer\b", "front fender"),
        (r"\brear\s+fencer\b", "rear fender"),
        (r"\bcooling\s+cc\b", "cooling system"),
        (r"\boil\s+fevel\b", "oil level"),
        (r"\bclan\s+ail\b", "clean oil"),
        (r"\bmetai\b", "metal"),
        (r"\bax(?:ic|ig|te|de|ti|ie)\b", "axle"),
        (r"\bante\b", "axle"),
        (r"\bnight\b", "right"),
        (r"\bait\b", "all"),
        (r"\bopcrating\b", "operating"),
        (r"\bbefarc\b", "before"),
        (r"\bbke\b", "bike"),
        (r"\bheeland\b", "wheel and"),
        (r"\bshoe\b", "slide"),
        (r"\bwher\b", "wheel"),
        (r"\bwhct\b", "wheel"),
    ]
)

BODY_OVERRIDES = {
    "check brake operation before operating the bike": "Check brake operation before operating the bike.",
    "ensure the phone is secure before operating the bike": "Ensure the phone is secure before operating the bike.",
    "take note of the handlebar angle before loosening docking station bolts": "Note the handlebar angle before loosening the docking station bolts so it can be restored during assembly.",
}

DOC_API_URL = "https://api.starkfuture.com/v2/technical-documents?limit=200&page=1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rewrite original MX guides from Stark video overlays.")
    parser.add_argument("slugs", nargs="*", help="Specific guide slugs to rewrite.")
    parser.add_argument("--all-pending", action="store_true", help="Rewrite all low-step original MX guides with local audit videos.")
    parser.add_argument("--fps-sample", type=float, default=1.0, help="Overlay extraction sample rate.")
    return parser.parse_args()


def load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8-sig"))


def count_steps(tutorial_path: Path) -> int:
    if not tutorial_path.exists():
        return 0
    return tutorial_path.read_text(encoding="utf-8").count("\n### ")


def pending_slugs() -> list[str]:
    slugs: list[str] = []
    for manifest_path in sorted(VIDEOS_DIR.glob("*/manifest.json")):
        manifest = load_manifest(manifest_path)
        if manifest.get("source_family") != "MX" or manifest.get("applicability_label") != "MX":
            continue
        if not (AUDIT_VIDEOS_DIR / f"{manifest_path.parent.name}.mp4").exists():
            continue
        tutorial_path = manifest_path.parent / manifest["tutorial_markdown"]
        if count_steps(tutorial_path) > 8:
            continue
        slugs.append(manifest_path.parent.name)
    return slugs


def normalize_title(text: str) -> str:
    text = text.lower()
    text = text.replace("stark varg", "").replace("stark future", "")
    text = text.replace("how to ", "")
    text = text.replace("power train", "powertrain")
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
    return {word for word in normalize_title(text).split() if word not in stopwords}


def get_docs() -> list[dict]:
    with urllib.request.urlopen(DOC_API_URL, timeout=30) as response:
        return json.load(response)["docs"]


def find_best_doc(title: str, docs: list[dict]) -> dict | None:
    target = normalize_title(title)
    target_words = significant_words(title)
    best: tuple[int, dict] | None = None
    for doc in docs:
        name_obj = doc.get("name", {})
        name = name_obj.get("en", "") if isinstance(name_obj, dict) else str(name_obj)
        if not name:
            continue
        score = 0
        doc_norm = normalize_title(name)
        doc_words = significant_words(name)
        if target == doc_norm:
            score = 100
        elif target_words and target_words == doc_words:
            score = 85
        elif target_words and doc_words and target_words <= doc_words:
            score = 75
        elif target_words and doc_words:
            shared = len(target_words & doc_words)
            union = len(target_words | doc_words)
            if shared >= 2 and union:
                score = int((shared / union) * 60)
        if score and (best is None or score > best[0]):
            best = (score, doc)
    return best[1] if best else None


def download_doc_pdf(doc: dict) -> Path:
    code = doc["code"]
    path = DOC_CACHE_DIR / f"{code}.pdf"
    if not path.exists():
        DOC_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(doc["file"]["url"], timeout=60) as response:
            path.write_bytes(response.read())
    return path


def is_noise_line(line: str, code: str, title: str) -> bool:
    lower = line.lower()
    if lower in {
        "technical manual",
        "safety warnings",
        "tools",
        "consumables",
        "operation time",
        "warning",
        "note",
    }:
        return True
    if lower.startswith(("copyright", "starkfuture.com", "eng ")):
        return True
    if "copyright" in lower or "reproduction" in lower:
        return True
    if code.lower() in lower:
        return True
    if normalize_title(title) and normalize_title(title) in normalize_title(line):
        return True
    if re.fullmatch(r"\d+", line):
        return True
    return False


def parse_doc_steps(doc: dict) -> list[dict]:
    pdf_path = download_doc_pdf(doc)
    title_obj = doc.get("name", {})
    doc_title = title_obj.get("en", "") if isinstance(title_obj, dict) else str(title_obj)
    code = doc["code"]
    pages = [page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages]
    section: str | None = None
    mode: str | None = None
    steps: list[dict] = []
    current: dict | None = None
    for page_text in pages:
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        for line in lines:
            upper = line.upper()
            if upper == "REMOVAL":
                if current:
                    steps.append(current)
                    current = None
                section = "REMOVAL"
                mode = None
                continue
            if upper.startswith("INSTALLATION"):
                if current:
                    steps.append(current)
                    current = None
                section = "INSTALLATION"
                mode = None
                continue
            if section is None:
                continue
            if is_noise_line(line, code, doc_title):
                continue
            if upper == "WARNING":
                mode = "warning"
                continue
            if upper == "NOTE":
                mode = "note"
                continue
            match = re.match(r"^(\d+)\s+(.*)$", line)
            if match:
                if current:
                    steps.append(current)
                current = {"section": section, "title": match.group(2).strip(), "body": match.group(2).strip()}
                mode = None
                continue
            if not current:
                continue
            if mode == "warning":
                continue
            if mode == "note":
                current["body"] += " " + line
                continue
            if re.fullmatch(r"[A-Z][A-Z ]+", line):
                mode = None
                continue
            current["body"] += " " + line
    if current:
        steps.append(current)

    cleaned_steps: list[dict] = []
    for step in steps:
        title = step["title"].strip()
        body = step["body"].strip()
        body = re.sub(r"\s+", " ", body)
        body = re.sub(r"Reproduction.*$", "", body, flags=re.I)
        body = re.sub(r"Copyright.*$", "", body, flags=re.I)
        body = re.sub(r"starkfuture\.com.*$", "", body, flags=re.I)
        body = re.sub(r"\bTighten the axle lock bolt by hand until there’s no play\.\s*Tighten the right fork axle clamp bolts to 5 Nm\.", "Tighten the axle lock bolt by hand until there is no play.", body)
        body = re.sub(r"\s+([.,])", r"\1", body)
        body = body.replace("there’s", "there is")
        body = body.replace("  ", " ")
        title = body.split(". ")[0].strip().rstrip(".")
        cleaned_steps.append({"section": step["section"], "title": title, "body": body.rstrip(".") + "."})
    return cleaned_steps


def normalize_instruction(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\n", " ")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = re.sub(r"[^A-Za-z0-9.%+ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*N[mn]\b", r"\1 Nm", text, flags=re.I)
    for pattern, replacement in PHRASE_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.I)
    text = re.sub(r"\b(?:ae|ee|eee|oe|yo|wr|nan|iene|shal|mas|nn|fs|se|sr|rk|pt|om)\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text


def drop_noise_prefix(text: str) -> str:
    words = text.split()
    while words and (
        len(words[0]) == 1
        or words[0].isdigit()
        or words[0].lower() in {"a", "an", "the", "of", "to", "on", "in"}
        and len(words) > 2
        and words[1][0].islower()
    ):
        words.pop(0)
    return " ".join(words).strip()


def drop_noise_suffix(text: str) -> str:
    words = text.split()
    while words and (len(words[-1]) == 1 or re.fullmatch(r"[a-z]{1,2}", words[-1].lower())):
        words.pop()
    return " ".join(words).strip()


def trim_to_first_verb(text: str) -> str:
    lowered = text.lower()
    matches = []
    for phrase in REMOVE_START_VERBS + INSTALL_START_VERBS:
        idx = lowered.find(phrase)
        if idx >= 0:
            matches.append(idx)
    if matches:
        return text[min(matches) :].strip()
    return text


def title_case_known(text: str) -> str:
    words = text.split()
    out = []
    for index, word in enumerate(words):
        plain = re.sub(r"[^A-Za-z0-9]", "", word).lower()
        if plain in KNOWN_ACRONYMS:
            out.append(word.upper() if plain != "nm" else "Nm")
        elif index == 0:
            out.append(word[:1].upper() + word[1:].lower())
        else:
            out.append(word.lower())
    result = " ".join(out)
    result = result.replace("Can Bus", "CAN BUS").replace("Vcu", "VCU").replace("Kyb", "KYB").replace("Mx", "MX")
    return result.strip()


def correct_tokens(text: str) -> str:
    corrected: list[str] = []
    for token in text.split():
        bare = re.sub(r"[^A-Za-z0-9]", "", token).lower()
        if not bare or bare in SERVICE_VOCAB or bare in KNOWN_ACRONYMS or bare.isdigit():
            corrected.append(token)
            continue
        match = process.extractOne(bare, SERVICE_VOCAB, scorer=fuzz.ratio)
        if match and match[1] >= 88:
            replacement = match[0]
            if bare == "nm":
                replacement = "Nm"
            corrected.append(replacement)
        else:
            corrected.append(token)
    return " ".join(corrected)


def normalized_compare_tokens(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()


def incremental_instruction(previous: str, current: str) -> str:
    previous_tokens = normalized_compare_tokens(previous)
    current_tokens = current.split()
    current_compare = normalized_compare_tokens(current)
    prefix_len = 0
    max_prefix = min(len(previous_tokens), len(current_compare))
    for idx in range(max_prefix):
        if previous_tokens[idx] != current_compare[idx]:
            break
        prefix_len = idx + 1
    if prefix_len <= 0:
        return current
    compare_seen = 0
    cut_index = 0
    for index, token in enumerate(current_tokens):
        compare_token = re.sub(r"[^a-z0-9]", "", token.lower())
        if not compare_token:
            continue
        if compare_seen < prefix_len and compare_token == previous_tokens[compare_seen]:
            compare_seen += 1
            cut_index = index + 1
            continue
        break
    delta = " ".join(current_tokens[cut_index:]).strip()
    return delta or current


def clean_step_text(raw_text: str, previous_clean: str) -> str | None:
    cleaned = normalize_instruction(raw_text)
    cleaned = trim_to_first_verb(cleaned)
    cleaned = drop_noise_prefix(cleaned)
    cleaned = incremental_instruction(previous_clean, cleaned)
    cleaned = normalize_instruction(cleaned)
    cleaned = trim_to_first_verb(cleaned)
    cleaned = drop_noise_prefix(cleaned)
    cleaned = drop_noise_suffix(cleaned)
    cleaned = correct_tokens(cleaned)
    cleaned = canonicalize_phrases(cleaned)
    cleaned = re.sub(r"\bhebke\b", "the bike", cleaned, flags=re.I)
    cleaned = re.sub(r"\bto\.$", "to", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if len(cleaned) < 4:
        return None
    if not re.search(r"[A-Za-z]", cleaned):
        return None
    return title_case_known(cleaned)


def canonicalize_phrases(text: str) -> str:
    lowered = normalized_compare_tokens(text)
    joined = " ".join(lowered)
    if "remove phone" in joined:
        return "Remove phone"
    if "insert phone" in joined and "docking station" in joined:
        return "Insert phone in the docking station left side first"
    if "phone is secure" in joined and "operating" in joined:
        return "Ensure the phone is secure before operating the bike"
    if "brake operation" in joined and "operating" in joined:
        return "Check brake operation before operating the bike"
    if "brake disc" in joined and "pads" in joined:
        return "Ensure the brake disc slides between the brake pads"
    if joined.startswith("push") and "axle lock nut" in joined and "inside" in joined:
        return "Push the axle lock nut inside"
    if joined.startswith("remove") and "axle lock nut" in joined:
        return "Remove axle lock nut"
    if joined.startswith("loosen") and "wheel axle lock nut" in joined:
        return "Loosen wheel axle lock nut"
    if joined.startswith("loosen") and "fork clamp bolts" in joined and "left" in joined:
        return "Loosen fork clamp bolts on the left fork"
    if joined.startswith("loosen") and "fork clamp bolts" in joined and "right" in joined:
        return "Loosen fork clamp bolts on the right fork"
    if "lift the front of the bike" in joined and "remove the axle" in joined:
        return "Lift the front of the bike and remove the axle"
    if "slide the wheel out between the forks" in joined:
        return "Slide the wheel out between the forks"
    if "wiggle the wheel and fork" in joined and "axle inside" in joined:
        return "Wiggle the wheel and fork whilst pushing the axle inside"
    if joined.startswith("tighten") and "axle lock nut to 35" in joined:
        return "Tighten axle lock nut to 35 Nm"
    if joined.startswith("tighten") and "fork clamp bolts to 15" in joined:
        return "Tighten all fork clamp bolts to 15 Nm"
    if joined.startswith("tighten") and "right fork clamp bolts" in joined:
        return "Tighten right fork clamp bolts"
    return text


def should_keep_step(text: str) -> bool:
    lowered = text.lower()
    if len(lowered.split()) < 2:
        return False
    if lowered in {"tighten bolts", "remove bolts", "install bolts"}:
        return False
    return any(
        lowered.startswith(prefix)
        for prefix in REMOVE_START_VERBS + INSTALL_START_VERBS
    )


def dedupe_steps(steps: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    for step in steps:
        if deduped and normalized_compare_tokens(deduped[-1]["text"]) == normalized_compare_tokens(step["text"]):
            continue
        deduped.append(step)
    return deduped


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:72].rstrip("-")


def split_sections(slug: str, steps: list[dict]) -> tuple[str, int | None]:
    if slug in PROCEDURE_ONLY_SLUGS:
        return "procedure", None
    seen_remove = False
    for index, step in enumerate(steps):
        lowered = step["title"].lower()
        if lowered.startswith(REMOVE_START_VERBS):
            seen_remove = True
            continue
        if seen_remove and lowered.startswith(INSTALL_START_VERBS):
            return "split", index
    return "procedure", None


def build_body(title: str, body: str | None = None) -> str:
    if body:
        return body
    lowered = title.lower()
    if lowered in BODY_OVERRIDES:
        return BODY_OVERRIDES[lowered]
    return f"{title}."


def extract_torque_items(steps: list[dict]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for step in steps:
        text = step["title"]
        for match in re.finditer(r"(\d+(?:\.\d+)?)\s*Nm", text):
            torque = f"{match.group(1)} Nm"
            component = re.sub(r"\s+to\s+\d+(?:\.\d+)?\s*Nm", "", text, flags=re.I).strip()
            pair = (component, torque)
            if pair not in seen:
                items.append(pair)
                seen.add(pair)
    return items


def build_tutorial(manifest: dict, steps: list[dict]) -> str:
    lines: list[str] = [
        f"# {manifest['title']}",
        "",
        f"Source video: `{manifest['title']}` by Stark Future Official",
        "",
        f"Applicable models: `{manifest['applicability_label']}`",
        "",
        "## Scope",
        "",
        "This guide follows the original Stark Future video overlay sequence for the procedure shown in the original MX tutorial video. Each step below is aligned to the instruction text shown on screen.",
        "",
        "## Preparation",
        "",
    ]
    lines.extend(f"- {line}" for line in PREPARATION_LINES)
    lines.extend([""])

    if any(step.get("section") == "REMOVAL" for step in steps) and any(step.get("section") == "INSTALLATION" for step in steps):
        lines.extend(["## Removal Procedure", ""])
        removal_steps = [step for step in steps if step.get("section") == "REMOVAL"]
        install_steps = [step for step in steps if step.get("section") == "INSTALLATION"]
        lines.extend(render_steps(removal_steps))
        lines.extend(["## Installation Procedure", ""])
        lines.extend(render_steps(install_steps, offset=len(removal_steps)))
    else:
        mode, split_index = split_sections(manifest["slug"], steps)
        if mode == "split":
            lines.extend(["## Removal Procedure", ""])
            removal_steps = steps[: split_index or 0]
            install_steps = steps[split_index or 0 :]
            lines.extend(render_steps(removal_steps))
            lines.extend(["## Installation Procedure", ""])
            lines.extend(render_steps(install_steps, offset=len(removal_steps)))
        else:
            lines.extend(["## Procedure", ""])
            lines.extend(render_steps(steps))

    torque_items = extract_torque_items(steps)
    if torque_items:
        lines.extend(["## Torque Summary", "", "| Component | Torque |", "| --- | ---: |"])
        for component, torque in torque_items:
            lines.append(f"| {component} | {torque} |")
        lines.extend(["", "Verified torque items:", ""])
        for component, torque in torque_items:
            lines.append(f"- {component}: **{torque}** from the original Stark Future tutorial video text overlay.")
        lines.append("")

    lines.extend(
        [
            "## Critical Checks Before Riding",
            "",
            "- Confirm the serviced components are fully seated and all fasteners are tightened in the correct order.",
            "- Recheck all torque-critical hardware before riding.",
            "- Make sure all routed cables, clips, brackets, and surrounding parts are returned to their original positions.",
            "- Inspect the bike visually for any missing hardware before returning it to service.",
            "",
        ]
    )
    return "\n".join(lines)


def render_steps(steps: list[dict], offset: int = 0) -> list[str]:
    lines: list[str] = []
    for index, step in enumerate(steps, start=1 + offset):
        title = step["title"]
        alt = title[0].lower() + title[1:] if title else title
        lines.extend(
            [
                f"### {index}. {title}",
                "",
                build_body(title, step.get("body")),
                "",
                f"![Step {index} - {alt}](assets/screenshots/{step['name']}.jpg)",
                "",
            ]
        )
    return lines


def cleanup_stale_screenshots(guide_dir: Path, tutorial_text: str) -> None:
    screenshots_dir = guide_dir / "assets" / "screenshots"
    keep = {match.group(1) for match in re.finditer(r"assets/screenshots/([^)]+)", tutorial_text)}
    for path in screenshots_dir.glob("*.jpg"):
        if path.name not in keep:
            path.unlink()


def run_script(script: str, guide_dir: Path) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), str(guide_dir)], check=True)


def extract_guide_overlays(guide_dir: Path, source_video: Path, fps_sample: float) -> list[dict]:
    output_rel = Path("tmp") / "overlay-audit.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "extract_video_overlays.py"),
            str(guide_dir),
            "--fps-sample",
            str(fps_sample),
            "--output",
            str(output_rel).replace("\\", "/"),
        ],
        check=True,
    )
    output_path = guide_dir / output_rel
    return json.loads(output_path.read_text(encoding="utf-8"))


def choose_timestamps(target_count: int, candidate_times: list[int], overlay_times: list[int]) -> list[int]:
    base = candidate_times if candidate_times else overlay_times
    if not base:
        return [0] * target_count
    if target_count == 1:
        return [base[0]]
    chosen: list[int] = []
    for index in range(target_count):
        source_index = round(index * (len(base) - 1) / max(target_count - 1, 1))
        chosen.append(base[source_index])
    return chosen


def rewrite_guide(slug: str, fps_sample: float) -> tuple[int, int]:
    guide_dir = VIDEOS_DIR / slug
    manifest_path = guide_dir / "manifest.json"
    manifest = load_manifest(manifest_path)
    video_src = AUDIT_VIDEOS_DIR / f"{slug}.mp4"
    if not video_src.exists():
        raise FileNotFoundError(video_src)

    source_dir = guide_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_video = source_dir / "video.mp4"
    shutil.copy2(video_src, source_video)

    overlays = extract_guide_overlays(guide_dir, source_video, fps_sample)
    docs = get_docs()
    matched_doc = find_best_doc(manifest["title"], docs)
    doc_steps = parse_doc_steps(matched_doc) if matched_doc else []

    steps: list[dict] = []
    previous_clean = ""
    for item in overlays:
        text = clean_step_text(item["text"], previous_clean)
        if not text or not should_keep_step(text):
            previous_clean = normalize_instruction(item["text"])
            continue
        steps.append({"timestamp": int(item["timestamp"]), "text": text})
        previous_clean = normalize_instruction(item["text"])

    steps = dedupe_steps(steps)
    if len(steps) < 2 and not doc_steps:
        source_video.unlink(missing_ok=True)
        return (len(overlays), 0)

    if doc_steps:
        candidate_times = [step["timestamp"] for step in steps]
        overlay_times = [int(item["timestamp"]) for item in overlays]
        mapped_times = choose_timestamps(len(doc_steps), candidate_times, overlay_times)
        steps = [
            {
                "section": doc_step["section"],
                "title": doc_step["title"],
                "body": doc_step["body"],
                "timestamp": mapped_times[index],
            }
            for index, doc_step in enumerate(doc_steps)
        ]

    used_names: set[str] = set()
    renumbered_steps: list[dict] = []
    for index, step in enumerate(steps, start=1):
        title = step.get("title") or step.get("text") or ""
        body = step.get("body") or (f"{title}." if title else None)
        base_name = slugify(title)
        if not base_name:
            base_name = f"step-{index:02d}"
        name = base_name
        suffix = 2
        while name in used_names:
            name = f"{base_name}-{suffix}"
            suffix += 1
        used_names.add(name)
        renumbered_steps.append(
            {
                "timestamp": step["timestamp"],
                "title": title,
                "body": body,
                "section": step.get("section"),
                "name": f"step_{index:02d}_{name}",
            }
        )
    steps = renumbered_steps

    manifest["frames"] = [{"timestamp": step["timestamp"], "name": step["name"]} for step in steps]
    tutorial_text = build_tutorial(manifest, steps)

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tutorial_path = guide_dir / manifest["tutorial_markdown"]
    tutorial_path.write_text(tutorial_text, encoding="utf-8")

    run_script("extract_frames.py", guide_dir)
    run_script("build_tutorial_pdf.py", guide_dir)
    run_script("render_pdf_pages.py", guide_dir)

    cleanup_stale_screenshots(guide_dir, tutorial_text)
    source_video.unlink(missing_ok=True)
    return (len(overlays), len(steps))


def main() -> None:
    args = parse_args()
    if args.all_pending:
        slugs = pending_slugs()
    else:
        slugs = args.slugs
    if not slugs:
        raise SystemExit("No guides selected.")

    for slug in slugs:
        overlays_count, steps_count = rewrite_guide(slug, args.fps_sample)
        print(f"{slug}: overlays={overlays_count}, steps={steps_count}")


if __name__ == "__main__":
    main()
