from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"

GENERIC_PATTERNS = [
    "Remove or move aside the surrounding part, cover, or hardware needed to reach",
    "Remove the bolts, screws, nuts, or clips that directly secure",
    "Lift, slide, or guide",
    "Install the main retaining hardware",
]

ELECTRICAL_KEYWORDS = {
    "sensor",
    "light",
    "horn",
    "indicator",
    "tail",
    "head",
    "license plate holder",
    "charging port",
    "control switch",
    "docking station",
    "stark phone",
    "vcu",
    "throttle",
    "locker barrel",
}

BRAKE_KEYWORDS = {
    "brake",
    "master cylinder",
    "caliper",
    "brake line",
}

ROTATING_KEYWORDS = {
    "wheel",
    "fork",
    "swingarm",
    "rocker arm",
    "pull rod",
    "bearing",
}


def component_name(title: str) -> str:
    title = re.sub(r"\s+-\s+Stark.*$", "", title).strip()
    title = re.sub(r"^How to\s+", "", title, flags=re.I).strip()
    title = re.sub(r"^Remove and install(?:ing)?\s+", "", title, flags=re.I).strip()
    title = re.sub(r"\s+on your Stark.*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s+Stark.*$", "", title, flags=re.I).strip()
    return title.strip()


def classify_component(name: str) -> str:
    lowered = name.lower()
    if any(keyword in lowered for keyword in ELECTRICAL_KEYWORDS):
        return "electrical"
    if any(keyword in lowered for keyword in BRAKE_KEYWORDS):
        return "brake"
    if any(keyword in lowered for keyword in ROTATING_KEYWORDS):
        return "rotating"
    return "mechanical"


def replace_line(pattern: str, text: str, fn):
    def repl(match: re.Match[str]) -> str:
        name = match.group("name")
        category = classify_component(name)
        return fn(name, category)

    return re.sub(pattern, repl, text, flags=re.M)


def apply_replacements(text: str) -> str:
    updated = text

    def access_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Open the surrounding panel area so the {name} mounting points and wiring path are fully accessible."
        if category == "brake":
            return f"Remove the surrounding parts needed to expose the {name} and its routing or mounting points."
        if category == "rotating":
            return f"Remove the surrounding hardware needed to expose the {name} and its clamping or axle points."
        return f"Remove the surrounding parts needed to expose the {name} mounting points shown in the video."

    def hardware_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Remove the visible {name} fasteners and support the part so it does not hang on the wiring."
        if category == "brake":
            return f"Remove the visible {name} fasteners while supporting the brake component as the hardware comes free."
        if category == "rotating":
            return f"Remove the visible {name} fasteners in the order shown and support the part as it comes free."
        return f"Remove the visible fasteners that secure the {name} and keep the hardware in removal order."

    def removal_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Remove the {name} from the bike once the connector, routing clips, and mounting hardware are free."
        if category == "brake":
            return f"Remove the {name} from the bike once the last fastener and any routed support pieces are released."
        if category == "rotating":
            return f"Slide the {name} free from the bike once the clamping hardware and support pieces are released."
        return f"Remove the {name} from the bike once the remaining supports and fasteners are free."

    def install_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Install the {name} mounting hardware by hand first and seat the part evenly against its bracket or panel."
        if category == "brake":
            return f"Install the {name} retaining hardware by hand first and keep the brake component aligned during tightening."
        if category == "rotating":
            return f"Install the {name} retaining hardware by hand first and keep the part aligned as the hardware is tightened."
        return f"Install the {name} retaining hardware by hand first so the part stays aligned in its mounting points."

    updated = replace_line(
        r"^Remove or move aside the surrounding part, cover, or hardware needed to reach the (?P<name>.+?)\.$",
        updated,
        access_sentence,
    )
    updated = replace_line(
        r"^Remove the bolts, screws, nuts, or clips that directly secure the (?P<name>.+?)\.$",
        updated,
        hardware_sentence,
    )
    updated = replace_line(
        r"^Lift, slide, or guide the (?P<name>.+?) (?:out of its mounting position once the retaining hardware is removed|clear of the mounting area once the connector and fasteners are released)\.$",
        updated,
        removal_sentence,
    )
    updated = replace_line(
        r"^Install the main retaining hardware for the (?P<name>.+?) by hand first, then tighten it evenly\.$",
        updated,
        install_sentence,
    )
    return updated


def main() -> None:
    changed = []
    for tutorial_path in sorted(VIDEOS_DIR.glob("*/tutorial.md")):
        original = tutorial_path.read_text(encoding="utf-8")
        if not any(pattern in original for pattern in GENERIC_PATTERNS):
            continue

        manifest_path = tutorial_path.parent / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        updated = apply_replacements(original)

        if updated != original:
            tutorial_path.write_text(updated, encoding="utf-8")
            changed.append(tutorial_path.parent.name)

    if changed:
        print("\n".join(changed))


if __name__ == "__main__":
    main()
