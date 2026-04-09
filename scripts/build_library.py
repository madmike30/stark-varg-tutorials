from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import YouTubeTranscriptApiException
from yt_dlp import YoutubeDL


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"

PLAYLISTS = [
    {
        "url": "https://www.youtube.com/playlist?list=PLkap5aPwLLRBoeCpkpNh-ayt6BO0oiq2y",
        "label": "mx-original",
        "title": "Stark VARG MX Tutorials",
        "manual_name": "Stark-VARG-MX-Tutorials-And-Technical",
        "manual_url": "https://starkfuture.com/en-IL/tutorials-and-technical",
        "source_family": "MX",
        "applicability_label": "MX",
        "applicable_models": ["MX"],
    },
    {
        "url": "https://www.youtube.com/playlist?list=PLkap5aPwLLRBqClumfq428p7DvfueeWdW",
        "label": "mx-1-2-shared",
        "title": "Stark VARG MX 1.2 / EX Shared Tutorials",
        "manual_name": "Stark-VARG-MX-1.2-Owners-Manual-ENG-2025-07.pdf",
        "manual_url": "https://assets.starkfuture.com/technical-documents/Stark-VARG-MX-1.2-Owners-Manual-ENG-2025-07.pdf",
        "source_family": "MX 1.2",
        "applicability_label": "MX 1.2 / EX",
        "applicable_models": ["MX 1.2", "EX"],
    },
    {
        "url": "https://www.youtube.com/playlist?list=PLkap5aPwLLRCEirHu95EHvDsCDujl3ia_",
        "label": "ex",
        "title": "Stark VARG EX Tutorials",
        "manual_name": "Stark-VARG-EX-Owners-Manual-ENG-2025-02.pdf",
        "manual_url": "https://assets.starkfuture.com/technical-documents/Stark%2BVARG%2BEX%2BOwners%2BManual%2BENG%2B2025-02.pdf",
        "source_family": "EX",
        "applicability_label": "EX",
        "applicable_models": ["EX"],
    },
]

GENERIC_PREPARATION = [
    "Place the bike on a stable stand or work area before starting the procedure.",
    "Prepare the correct tools for the fasteners, clips, brackets, and components shown in the video.",
    "Keep removed hardware organized in sequence so reassembly follows the same order as the video.",
    "Have a torque wrench ready for any tightening steps that specify a torque value.",
]

MX_MANUAL_TORQUE_RULES = [
    {
        "match": ("unbox",),
        "target": "secure the setup hardware",
        "lines": [
            "Tighten the docking station bolts to 30 Nm.",
            "Tighten the front wheel axle lock bolt to 35 Nm.",
            "Tighten the front wheel clamp bolts to 15 Nm.",
            "Tighten the foot peg pin to 20 Nm.",
        ],
    },
    {
        "match": ("bleeding the cooling system",),
        "target": "reinstall the removed bodywork",
        "lines": [
            "Tighten the skid plate bolts to 15 Nm.",
        ],
    },
    {
        "match": ("gear oil change",),
        "target": "reinstall removed parts",
        "lines": [
            "Tighten the skid plate bolts to 15 Nm.",
        ],
    },
    {
        "match": ("remove and installing chain",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the chain slider bolts to 5 Nm.",
            "Tighten the rear wheel axle lock bolt to 80 Nm.",
        ],
    },
    {
        "match": ("brake pedal",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the brake pedal peg bolts to 5 Nm.",
            "Tighten the brake pedal sway bolts to 20 Nm.",
            "Tighten the brake pedal link bolts to 10 Nm.",
        ],
    },
    {
        "match": ("foot brake master cylinder",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the foot brake master cylinder bolts to 10 Nm.",
        ],
    },
    {
        "match": ("foot brake",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the foot brake master cylinder bolts to 10 Nm.",
            "Tighten the brake pedal peg bolts to 5 Nm.",
            "Tighten the brake pedal sway bolts to 20 Nm.",
            "Tighten the brake pedal link bolts to 10 Nm.",
        ],
    },
    {
        "match": ("charging port",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the charging port bolts to 5 Nm.",
        ],
    },
    {
        "match": ("control switch",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the control switch bolt to 5 Nm.",
        ],
    },
    {
        "match": ("docking station",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the docking station bolts to 30 Nm.",
        ],
    },
    {
        "match": ("front brake assembly",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the front brake caliper bolts to 25 Nm.",
            "Tighten the hand brake master cylinder clamp bolts to 3 Nm.",
            "Tighten the fork brake line bracket screws to 3 Nm.",
        ],
    },
    {
        "match": ("front brake caliper",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the front brake caliper bolts to 25 Nm.",
        ],
    },
    {
        "match": ("front brake line bracket",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the fork brake line bracket screws to 3 Nm.",
        ],
    },
    {
        "match": ("front fender",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the front fender bolts to 8 Nm.",
        ],
    },
    {
        "match": ("front number plate",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the front number plate bolt to 8 Nm.",
        ],
    },
    {
        "match": ("front wheel",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the front wheel axle lock bolt to 35 Nm.",
            "Tighten the front wheel clamp bolts to 15 Nm.",
        ],
    },
    {
        "match": ("hand brake master cylinder",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the hand brake master cylinder clamp bolts to 3 Nm.",
        ],
    },
    {
        "match": ("handlebar",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the docking station bolts to 30 Nm.",
        ],
    },
    {
        "match": ("left side plate",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the side plates top bolt to 45 Nm.",
            "Tighten the side plates bottom bolt to 40 Nm.",
        ],
    },
    {
        "match": ("pull rod",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the pull rod nuts to 60 Nm.",
        ],
    },
    {
        "match": ("rear mud flap",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the lower rear fender bolts to 5 Nm.",
            "Tighten the mud flap screws to 3 Nm.",
        ],
    },
    {
        "match": ("rear shock",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the shock top nut to 40 Nm.",
            "Tighten the shock bottom nut to 40 Nm.",
        ],
    },
    {
        "match": ("rear wheel",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the rear wheel axle lock bolt to 80 Nm.",
        ],
    },
    {
        "match": ("right side plate",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the side plates top bolt to 45 Nm.",
            "Tighten the side plates bottom bolt to 40 Nm.",
        ],
    },
    {
        "match": ("rocker arm",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the rocker arm reverse lock nut to 5 Nm.",
            "Tighten the rocker arm main shaft to 60 Nm.",
            "Tighten the rocker arm shaft lids to 5 Nm.",
            "Tighten the rocker arm lock nut to 60 Nm.",
        ],
    },
    {
        "match": ("side stand",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the side stand bracket bolts to 5 Nm.",
            "Tighten the side stand leg bolt to 15 Nm.",
        ],
    },
    {
        "match": ("skid plate",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the skid plate bolts to 15 Nm.",
        ],
    },
    {
        "match": ("spoiler assembly",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the spoiler assembly rear center bolt to 8 Nm.",
            "Tighten the spoiler assembly side bolts to 40 Nm.",
            "Tighten the spoiler assembly front bolts to 5 Nm.",
        ],
    },
    {
        "match": ("swingarm",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the swingarm axle to 45 Nm.",
            "Tighten the swingarm clamp bolt to 35 Nm.",
        ],
    },
    {
        "match": ("throttle",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the throttle bolt to 3 Nm.",
        ],
    },
    {
        "match": ("vcu",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the VCU bolts to 5 Nm.",
        ],
    },
]

MX_1_2_MANUAL_TORQUE_RULES = [
    {
        "match": ("carbon fiber spoiler",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the carbon fiber spoiler bolts to 3 Nm.",
        ],
    },
    {
        "match": ("rear shock",),
        "target": "install the retaining hardware",
        "lines": [
            "Tighten the top shock shaft nut to 40 Nm.",
            "Tighten the bottom shock shaft nut to 40 Nm.",
        ],
    },
]


@dataclass
class Step:
    index: int
    start: float
    duration: float
    title: str
    body_lines: list[str]
    screenshot_name: str
    mode: str = "transcript"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Stark tutorial library content from playlist videos.")
    parser.add_argument("--limit-per-playlist", type=int, default=0, help="Optional limit for testing.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip videos that already have a tutorial and PDF.")
    parser.add_argument("--playlist-label", action="append", dest="playlist_labels", help="Only process the matching playlist label(s).")
    return parser.parse_args()


def slugify(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def get_playlist_entries(url: str) -> list[dict]:
    with YoutubeDL({"extract_flat": True, "quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return info["entries"]


def fetch_transcript(video_id: str):
    api = YouTubeTranscriptApi()
    return api.fetch(video_id)


def clean_sentence(text: str) -> str:
    text = text.replace("it´s", "its").replace("’", "'").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def bold_torque(text: str) -> str:
    return re.sub(r"(\b\d+\s*Nm\b)", r"**\1**", text)


def step_title_from_text(text: str) -> str:
    text = clean_sentence(text)
    text = text.split("NOTE:")[0].strip()
    if text.endswith("."):
        text = text[:-1]
    return text


def step_body_from_text(text: str) -> list[str]:
    text = clean_sentence(text)
    parts = [part.strip() for part in text.split("NOTE:")]
    body = []
    if parts and parts[0]:
        body.append(bold_torque(parts[0]))
    if len(parts) > 1 and parts[1]:
        note_text = parts[1]
        note_text = note_text[0].upper() + note_text[1:] if note_text else note_text
        body.append(bold_torque(note_text))
    return body


def build_steps(transcript) -> list[Step]:
    steps: list[Step] = []
    for index, item in enumerate(transcript, start=1):
        title = step_title_from_text(item.text)
        screenshot_name = f"step_{index:02d}_{slugify(title)[:60]}"
        steps.append(
            Step(
                index=index,
                start=float(item.start),
                duration=float(item.duration),
                title=title,
                body_lines=step_body_from_text(item.text),
                screenshot_name=screenshot_name,
                mode="transcript",
            )
        )
    return steps


def component_from_title(video_title: str) -> str:
    clean = clean_sentence(video_title)
    clean = re.sub(r"^how to\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^remove and install\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^remove and install the\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^the\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+on your stark varg.*$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*-\s*stark varg.*$", "", clean, flags=re.IGNORECASE)
    return clean.strip()


def spaced_stark_model(text: str) -> str:
    text = text.replace("MX1.2", "MX 1.2")
    return re.sub(r"\s+", " ", text).strip()


def infer_metadata_from_title(title: str) -> dict:
    normalized = spaced_stark_model(title).lower()
    if "stark varg ex" in normalized:
        playlist = next(item for item in PLAYLISTS if item["label"] == "ex")
    elif "mx 1.2 / ex" in normalized or "stark varg mx 1.2" in normalized:
        playlist = next(item for item in PLAYLISTS if item["label"] == "mx-1-2-shared")
    else:
        playlist = next(item for item in PLAYLISTS if item["label"] == "mx-original")
    return {
        "source_family": playlist["source_family"],
        "applicability_label": playlist["applicability_label"],
        "applicable_models": playlist["applicable_models"][:],
        "playlist_title": playlist["title"],
    }


def metadata_from_manifest(manifest: dict, fallback_title: str = "") -> dict:
    title = manifest.get("title", fallback_title)
    metadata = infer_metadata_from_title(title)
    if manifest.get("source_family"):
        metadata["source_family"] = manifest["source_family"]
    if manifest.get("applicability_label"):
        metadata["applicability_label"] = manifest["applicability_label"]
    if manifest.get("applicable_models"):
        metadata["applicable_models"] = list(manifest["applicable_models"])
    if manifest.get("playlist_title"):
        metadata["playlist_title"] = manifest["playlist_title"]
    return metadata


def applicability_label_for_title(title: str) -> str:
    return infer_metadata_from_title(title)["applicability_label"]


def source_family_for_title(title: str) -> str:
    return infer_metadata_from_title(title)["source_family"]


def compact_spacing_around_punctuation(text: str) -> str:
    text = re.sub(r"\s+-\s+", " - ", text)
    text = re.sub(r"\s+([,.:;])", r"\1", text)
    text = re.sub(r"([A-Za-z])-\s+([A-Za-z])", r"\1 - \2", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def strip_model_suffix(title: str) -> str:
    title = compact_spacing_around_punctuation(spaced_stark_model(title))
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


def display_title_with_applicability(title: str) -> str:
    return f"{strip_model_suffix(title)} ({applicability_label_for_title(title)})"


def is_wiring_component(component: str) -> bool:
    wiring_keywords = (
        "sensor",
        "light",
        "indicator",
        "horn",
        "license plate holder",
    )
    lower_component = component.lower()
    return any(keyword in lower_component for keyword in wiring_keywords)


def is_guard_or_protector(component: str) -> bool:
    lower_component = component.lower()
    return any(keyword in lower_component for keyword in ("guard", "protector"))


def build_unboxing_steps(duration_seconds: int) -> list[Step]:
    titles_and_bodies = [
        (
            "Inspect the shipping package",
            [
                "Check the outer box, straps, and visible packaging condition before opening the crate.",
                "Confirm the crate is stable and that all included parts remain secured before any hardware is removed.",
            ],
        ),
        (
            "Remove the outer packaging",
            [
                "Cut and remove the external wrapping, cover panels, and protective packing material shown in the video.",
                "Keep the removed packing pieces clear of the bike so the remaining crate hardware is easy to access.",
            ],
        ),
        (
            "Release the crate fasteners and supports",
            [
                "Remove the shipping bolts, brackets, clips, and support pieces that hold the bike and loose parts inside the crate.",
                "Set the shipping hardware aside separately from the service hardware used on the bike.",
            ],
        ),
        (
            "Remove the bike from the crate",
            [
                "Lift or roll the bike out of the crate exactly as shown once the shipping restraints are fully removed.",
                "Support the bike carefully so no bodywork, guards, or controls are loaded during the move.",
            ],
        ),
        (
            "Install the supplied setup parts",
            [
                "Fit the included parts, guards, or accessories that are supplied separately in the crate.",
                "Install each piece in the same order shown so the mounting hardware, spacers, and brackets stay matched correctly.",
            ],
        ),
        (
            "Secure the setup hardware",
            [
                "Install and tighten the visible fasteners for the newly fitted setup parts.",
                "Make sure the parts sit flush and that no clip, washer, or spacer is omitted during assembly.",
            ],
        ),
        (
            "Complete the final setup inspection",
            [
                "Check that the bike is fully assembled, all packing materials are removed, and the controls move freely.",
                "Verify the bike is ready for the next setup steps before riding or charging.",
            ],
        ),
    ]
    interval = max(8, duration_seconds // (len(titles_and_bodies) + 1))
    steps: list[Step] = []
    for index, (title, body_lines) in enumerate(titles_and_bodies, start=1):
        steps.append(
            Step(
                index=index,
                start=float(interval * index),
                duration=float(interval),
                title=title,
                body_lines=body_lines,
                screenshot_name=f"step_{index:02d}_{slugify(title)[:60]}",
                mode="visual",
            )
        )
    return steps


def build_visual_sequence(titles_and_bodies: list[tuple[str, list[str]]], duration_seconds: int) -> list[Step]:
    interval = max(5, duration_seconds // (len(titles_and_bodies) + 1))
    steps: list[Step] = []
    for index, (title, body_lines) in enumerate(titles_and_bodies, start=1):
        steps.append(
            Step(
                index=index,
                start=float(interval * index),
                duration=float(interval),
                title=title,
                body_lines=body_lines,
                screenshot_name=f"step_{index:02d}_{slugify(title)[:60]}",
                mode="visual",
            )
        )
    return steps


def manual_torque_source_label_for_title(title: str) -> str:
    source_family = source_family_for_title(title)
    if source_family == "MX":
        return "the official Stark VARG owner manual torque table"
    if source_family == "MX 1.2":
        return "the official Stark VARG MX 1.2 owner manual torque table"
    return "the official Stark tutorial video"


def find_mx_manual_torque_rule(video_title: str) -> dict | None:
    source_family = source_family_for_title(video_title)
    if source_family == "MX":
        rules = MX_MANUAL_TORQUE_RULES
    elif source_family == "MX 1.2":
        rules = MX_1_2_MANUAL_TORQUE_RULES
    else:
        return None
    lower_title = spaced_stark_model(video_title).lower()
    for rule in rules:
        if all(term in lower_title for term in rule["match"]):
            return rule
    return None


def apply_mx_manual_torque_lines(video_title: str, titles_and_bodies: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    matched_rule = find_mx_manual_torque_rule(video_title)
    if not matched_rule:
        return titles_and_bodies

    torque_lines = [bold_torque(line) for line in matched_rule["lines"]]
    target = matched_rule["target"]
    updated: list[tuple[str, list[str]]] = []
    applied = False

    for step_title, body_lines in titles_and_bodies:
        next_body = list(body_lines)
        if not applied and target in step_title.lower():
            for torque_line in torque_lines:
                if torque_line not in next_body:
                    next_body.append(torque_line)
            applied = True
        updated.append((step_title, next_body))

    if applied:
        return updated

    fallback_markers = ("install ", "reinstall ", "secure ", "close ")
    for index, (step_title, body_lines) in enumerate(updated):
        if step_title.lower().startswith(fallback_markers):
            next_body = list(body_lines)
            for torque_line in torque_lines:
                if torque_line not in next_body:
                    next_body.append(torque_line)
            updated[index] = (step_title, next_body)
            break

    return updated


def apply_mx_manual_torque_lines_to_steps(video_title: str, steps: list[Step]) -> list[Step]:
    matched_rule = find_mx_manual_torque_rule(video_title)
    if not matched_rule:
        return steps

    torque_lines = [bold_torque(line) for line in matched_rule["lines"]]
    target = matched_rule["target"]
    fallback_markers = ("install ", "reinstall ", "secure ", "close ")

    for step in steps:
        if target in step.title.lower():
            for torque_line in torque_lines:
                if torque_line not in step.body_lines:
                    step.body_lines.append(torque_line)
            return steps

    for step in steps:
        if step.title.lower().startswith(fallback_markers):
            for torque_line in torque_lines:
                if torque_line not in step.body_lines:
                    step.body_lines.append(torque_line)
            break

    return steps


def build_turn_on_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Stabilize the bike before power-up", ["Place the bike in a stable position and make sure the controls and surrounding area are clear before switching it on."]),
            ("Locate the main power control", ["Use the control shown in the video to begin the startup sequence for the bike."]),
            ("Switch the bike ON", ["Press the power control as shown and allow the bike electronics and display to boot fully."]),
            ("Confirm the bike has powered up correctly", ["Check the display or system indicators shown in the video to confirm the bike is awake and ready for the next action."]),
            ("Verify normal startup status", ["Make sure no warning state is shown and confirm the bike remains stable before riding or engaging drive."]),
        ],
        duration_seconds,
    )


def build_engage_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Prepare the bike for engagement", ["Hold the bike securely and confirm it has already been powered on before attempting to engage it."]),
            ("Select the engagement control", ["Use the control sequence shown in the video to move the bike from powered-on standby into the engaged state."]),
            ("Engage the drive system", ["Perform the engagement action exactly as shown and wait for the bike to confirm the new state."]),
            ("Check the bike is engaged", ["Verify the display or status indication shown in the video so you know the bike is ready to ride."]),
            ("Confirm the bike is stable before moving", ["Keep the bike controlled and stationary until you are ready to ride away safely."]),
        ],
        duration_seconds,
    )


def build_disengage_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Bring the bike to a controlled stop", ["Hold the bike securely and keep it stable before disengaging the drive system."]),
            ("Use the disengagement control", ["Operate the control shown in the video to move the bike out of the engaged state."]),
            ("Disengage the drive system", ["Complete the disengagement action and wait for the bike to confirm the state change."]),
            ("Verify the bike is no longer engaged", ["Check the display or status indication shown in the video to confirm the bike is safe to handle without drive engagement."]),
            ("Prepare for shutdown or service", ["Once disengaged, continue with shutdown, charging, transport, or service as needed."]),
        ],
        duration_seconds,
    )


def build_turn_off_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Stabilize the bike before powering down", ["Make sure the bike is stopped and secure before switching it off."]),
            ("Locate the power-off control", ["Use the same control area shown in the video for the shutdown command."]),
            ("Switch the bike OFF", ["Perform the power-off action shown and wait for the display and system indicators to power down."]),
            ("Confirm the bike has shut off", ["Verify the bike display and active indicators are off before leaving the bike unattended."]),
        ],
        duration_seconds,
    )


def build_shutdown_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Secure the bike before shutdown", ["Place the bike in a stable position and make sure the drive system is no longer engaged."]),
            ("Initiate the shutdown sequence", ["Use the shutdown control sequence shown in the video rather than only a quick power toggle."]),
            ("Wait for the bike to complete shutdown", ["Allow the bike electronics to finish the shutdown process fully before disconnecting anything or storing the bike."]),
            ("Confirm the system is fully off", ["Check that the display and system indicators are no longer active once shutdown is complete."]),
        ],
        duration_seconds,
    )


def build_charge_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Prepare the bike and charger", ["Place the bike in a stable position and inspect the charger, cable, and charging port before connecting anything."]),
            ("Open or access the charging port", ["Expose the charging connection point shown in the video and make sure it is clean and unobstructed."]),
            ("Connect the charger to the bike", ["Insert the charging connector carefully as shown so it seats fully without stressing the cable."]),
            ("Connect power and begin charging", ["Supply power to the charger as shown and confirm the charging sequence starts on the bike or charger indicators."]),
            ("Verify charging status", ["Check the visual charging indication shown in the video so you know the bike is actively charging."]),
            ("Disconnect safely after charging", ["Once charging is complete, disconnect the charger in the same careful order shown and secure the port cover or cable routing."]),
        ],
        duration_seconds,
    )


def build_update_software_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Prepare the bike for a software update", ["Start with the bike stable, powered on, and ready for the update process shown in the video."]),
            ("Access the software update screen or workflow", ["Open the update menu or control path shown in the video to check for available software updates."]),
            ("Review the available update", ["Confirm the update shown on-screen before starting the installation process."]),
            ("Start the software update", ["Begin the update exactly as shown and keep the bike powered and undisturbed while the software installs."]),
            ("Wait for the update to complete", ["Allow the progress sequence to finish without interrupting power, controls, or connections."]),
            ("Confirm the updated software status", ["Check the final screen or version/status indication shown in the video to verify the update completed successfully."]),
        ],
        duration_seconds,
    )


def build_bleed_cooling_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Prepare access to the cooling system", ["Place the bike on a stable stand and remove the visible bodywork or guards shown in the video to reach the cooling system service points."]),
            ("Position a container for drained coolant", ["Place a suitable container under the bike before opening the cooling system so drained coolant is captured cleanly."]),
            ("Open the cooling system service points", ["Loosen the drain and cap points shown in the video so coolant can move through the system and trapped air can be released."]),
            ("Drain and refill the coolant circuit", ["Drain the old coolant as shown, then refill the system with the coolant type indicated in the procedure."]),
            ("Cycle the system to purge trapped air", ["Operate the bike as shown in the video so the coolant circulates and air is bled from the system."]),
            ("Top off and close the cooling system", ["Bring the coolant level back to the correct height, then close the cap and service points shown in the video."]),
            ("Reinstall the removed bodywork", ["Reinstall the covers, skid plate, and other removed parts in the same order used during access."]),
            ("Check for leaks and correct level", ["Inspect the system for leaks and confirm the coolant level remains correct before riding."]),
        ],
        duration_seconds,
    )


def build_gear_oil_change_steps(duration_seconds: int) -> list[Step]:
    return build_visual_sequence(
        [
            ("Prepare access to the gear oil service points", ["Place the bike on a stable stand and remove any cover or guard shown in the video that blocks the gear oil fill and drain points."]),
            ("Position a container under the drain point", ["Place a suitable drain container under the bike before removing the gear oil drain hardware."]),
            ("Open the fill and drain points", ["Loosen the fill and drain hardware shown in the video so the old gear oil can drain fully."]),
            ("Drain the old gear oil", ["Allow the old oil to drain completely while monitoring the drain container and the service opening."]),
            ("Reinstall the drain hardware", ["Reinstall the drain hardware shown in the video once draining is complete and the mating surfaces are ready for assembly."]),
            ("Refill with fresh gear oil", ["Fill the system with the oil type and level indicated by the procedure shown in the video."]),
            ("Close the fill point and clean the area", ["Reinstall the fill hardware and wipe any spilled oil from the surrounding parts."]),
            ("Reinstall removed parts and inspect for leaks", ["Reinstall any removed guards or covers and check the service area for leaks before returning the bike to use."]),
        ],
        duration_seconds,
    )


def build_visual_fallback_steps(video_title: str, duration_seconds: int) -> list[Step]:
    component = component_from_title(video_title) or "component"
    lower_component = component.lower()
    lower_title = video_title.lower()

    if "unbox" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_unboxing_steps(duration_seconds))
    if "turn on" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_turn_on_steps(duration_seconds))
    if "engage" in lower_title and "disengage" not in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_engage_steps(duration_seconds))
    if "disengage" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_disengage_steps(duration_seconds))
    if "turn off" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_turn_off_steps(duration_seconds))
    if "shutdown" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_shutdown_steps(duration_seconds))
    if "charge" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_charge_steps(duration_seconds))
    if "update" in lower_title and "software" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_update_software_steps(duration_seconds))
    if "cooling system" in lower_title and ("bleed" in lower_title or "bleeding" in lower_title):
        return apply_mx_manual_torque_lines_to_steps(video_title, build_bleed_cooling_steps(duration_seconds))
    if "gear oil" in lower_title and "change" in lower_title:
        return apply_mx_manual_torque_lines_to_steps(video_title, build_gear_oil_change_steps(duration_seconds))
    if "rear shock" in lower_title and source_family_for_title(video_title) == "MX 1.2":
        titles_and_bodies = [
            ("Prepare access to the Rear Shock", ["Prepare access to the Rear Shock."]),
            ("Remove the visible fasteners securing the Rear Shock", ["Remove the visible fasteners securing the Rear Shock."]),
            ("Release the Rear Shock from its mounting position", ["Release the Rear Shock from its mounting position."]),
            ("Remove or free any related clip, bracket, or connector", ["Remove or free any related clip, bracket, or connector."]),
            ("Position the Rear Shock for installation", ["Position the Rear Shock for installation."]),
            ("Install the retaining hardware for the Rear Shock", ["Install the retaining hardware for the Rear Shock."]),
            ("Align the Rear Shock in its final position", ["Align the Rear Shock in its final position."]),
            ("Verify the completed installation", ["Verify the completed installation."]),
        ]
        titles_and_bodies = apply_mx_manual_torque_lines(video_title, titles_and_bodies)
        return build_visual_sequence(titles_and_bodies, duration_seconds)

    if is_wiring_component(component):
        titles_and_bodies = [
            (
                f"Remove the fasteners or panels that block access to the {component}",
                [
                    f"Remove the visible bolts, screws, or trim pieces that must come off before the {component} can be reached.",
                    "Keep the hardware in removal order so the covers and brackets return to the same locations during assembly.",
                ],
            ),
            (
                f"Release the clips and routing points for the {component}",
                [
                    f"Free any clips, retainers, grommets, or brackets that hold the {component} or its wiring in place.",
                    "Document the original routing so the cable or harness can be returned to the same path during installation.",
                ],
            ),
            (
                f"Disconnect the {component}",
                [
                    f"Separate the connector or electrical coupling for the {component} exactly as shown in the video.",
                    "Avoid pulling on the wire itself while releasing the connector lock.",
                ],
            ),
            (
                f"Remove the retaining hardware for the {component}",
                [
                    f"Remove the bolts, screws, clips, or nuts that directly secure the {component} to the bike.",
                    "Support the component as the last fastener is removed so it does not hang on the wiring.",
                ],
            ),
            (
                f"Remove the {component} from the bike",
                [
                    f"Lift, slide, or guide the {component} clear of the mounting area once the connector and fasteners are released.",
                    "Keep any washers, spacers, sleeves, or rubber mounts with the component for reassembly.",
                ],
            ),
            (
                f"Position the {component} for installation",
                [
                    f"Set the {component} back into its mounting position and align it with the original locating points.",
                    "Confirm that no cable is trapped behind the component before the fasteners are started.",
                ],
            ),
            (
                f"Reconnect the {component} and route the wiring correctly",
                [
                    f"Reconnect the {component} connector and return the harness to the same clips, guides, and brackets used before removal.",
                    "Check that the wiring has enough slack for steering or suspension movement where applicable.",
                ],
            ),
            (
                f"Install the retaining hardware for the {component}",
                [
                    f"Install the mounting hardware for the {component} by hand first, then seat the part evenly against its mount.",
                    "Reinstall any removed clips, covers, or brackets after the main hardware is secure.",
                ],
            ),
            (
                f"Verify the operation of the {component}",
                [
                    f"Check that the {component} is aligned correctly and confirm it operates as shown in the video.",
                    "Inspect the surrounding routing and hardware one more time before returning the bike to service.",
                ],
            ),
        ]
    elif is_guard_or_protector(component) or "hand guard" in lower_component:
        titles_and_bodies = [
            (
                f"Remove the retaining hardware for the {component}",
                [
                    f"Remove the visible bolts, screws, or clips that hold the {component} in place.",
                    "Keep track of any washers, collars, or spacers as each fastener is removed.",
                ],
            ),
            (
                f"Release any support piece attached to the {component}",
                [
                    f"Remove any bracket, spacer, clamp, or secondary fastener that still retains the {component}.",
                    "Note the hardware stack order so the same arrangement is used during assembly.",
                ],
            ),
            (
                f"Remove the {component} from its mounting position",
                [
                    f"Slide or lift the {component} free once the retaining hardware is removed.",
                    "Inspect the mounting surfaces and the removed hardware before installation begins.",
                ],
            ),
            (
                f"Position the {component} for installation",
                [
                    f"Place the {component} back into its correct orientation on the bike.",
                    "Align the mounting holes and support points before any hardware is tightened.",
                ],
            ),
            (
                f"Reinstall any spacer, bracket, or clip for the {component}",
                [
                    f"Return each spacer, support piece, or clip to the same position used during removal.",
                    "Confirm the hardware stack is seated flat and centered before the main fasteners are installed.",
                ],
            ),
            (
                f"Install the retaining hardware for the {component}",
                [
                    f"Install the mounting fasteners for the {component} and tighten them evenly while holding the part aligned.",
                    "Check that the part sits flush and does not interfere with nearby moving parts.",
                ],
            ),
            (
                f"Verify the clearance and alignment of the {component}",
                [
                    f"Inspect the completed fitment of the {component} and confirm the surrounding area has proper clearance.",
                    "Make sure no hardware, clip, or support piece is missing before the bike is returned to service.",
                ],
            ),
        ]
    else:
        titles_and_bodies = [
            (
                f"Prepare access to the {component}",
                [
                    f"Remove or move aside the surrounding part, cover, or hardware needed to reach the {component}.",
                    "Keep the removed fasteners organized in sequence so reassembly matches the video.",
                ],
            ),
            (
                f"Remove the visible retaining hardware for the {component}",
                [
                    f"Remove the bolts, screws, nuts, or clips that directly secure the {component}.",
                    "Support the component as the last fastener is removed.",
                ],
            ),
            (
                f"Release any bracket, clip, or coupling attached to the {component}",
                [
                    f"Free any bracket, clip, spacer, linkage, or connector that still ties the {component} to the bike.",
                    "Note the orientation of these supporting pieces before setting them aside.",
                ],
            ),
            (
                f"Remove the {component} from the bike",
                [
                    f"Lift, slide, or guide the {component} out of its mounting position once the retaining hardware is removed.",
                    "Inspect the removed part and the mounting points before reassembly.",
                ],
            ),
            (
                f"Position the {component} for installation",
                [
                    f"Return the {component} to its mounting position and align the holes, tabs, or locating surfaces.",
                    "Hold the component in place until the first retaining hardware is started.",
                ],
            ),
            (
                f"Reconnect or refit the support pieces for the {component}",
                [
                    f"Reinstall any bracket, clip, spacer, linkage, or coupling associated with the {component}.",
                    "Make sure each supporting piece is seated correctly before final tightening.",
                ],
            ),
            (
                f"Install the retaining hardware for the {component}",
                [
                    f"Install the main retaining hardware for the {component} by hand first, then tighten it evenly.",
                    "Check that the component remains aligned while the hardware is brought fully home.",
                ],
            ),
            (
                f"Verify the completed installation of the {component}",
                [
                    f"Inspect the final position of the {component} and confirm that all hardware, clips, and surrounding parts are back in place.",
                    "Check the component for correct fit and movement before returning the bike to service.",
                ],
            ),
        ]

    titles_and_bodies = apply_mx_manual_torque_lines(video_title, titles_and_bodies)
    return build_visual_sequence(titles_and_bodies, duration_seconds)


def split_sections(video_title: str, steps: list[Step]) -> list[tuple[str, list[Step]]]:
    lower_title = video_title.lower()
    if "remove and install" in lower_title or "remove and install" in lower_title.replace("-", " "):
        install_markers = (
            "install ",
            "tighten ",
            "position ",
            "place ",
            "reinstall ",
            "apply ",
            "route ",
            "fill ",
            "bleed ",
        )
        for idx, step in enumerate(steps):
            if idx == 0:
                continue
            if step.title.lower().startswith(install_markers):
                return [("Removal Procedure", steps[:idx]), ("Installation Procedure", steps[idx:])]
    return [("Procedure", steps)]


def tutorial_title_from_video_title(video_title: str) -> str:
    clean = spaced_stark_model(clean_sentence(video_title))
    metadata = infer_metadata_from_title(clean)
    if metadata["source_family"] == "MX 1.2":
        patterns = (
            r"\s+on your Stark VARG MX 1\.2(?:\s*/\s*EX)?\s*$",
            r"\s*-\s*Stark VARG MX 1\.2(?:\s*/\s*EX)?\s*$",
            r"\s+Stark VARG MX 1\.2(?:\s*/\s*EX)?\s*$",
        )
        changed = True
        while changed:
            changed = False
            for pattern in patterns:
                next_clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)
                if next_clean != clean:
                    clean = next_clean
                    changed = True
        clean = re.sub(r"\s*-\s*$", "", clean)
        clean = compact_spacing_around_punctuation(clean)
        return f"{clean} - Stark VARG MX 1.2 / EX"
    if clean.lower().startswith("how to "):
        return clean[0].upper() + clean[1:]
    if clean.lower().startswith("remove and install"):
        return clean[0].upper() + clean[1:]
    return clean[0].upper() + clean[1:]


def collect_torque_lines(steps: list[Step], title: str) -> tuple[list[tuple[str, str]], list[str]]:
    summary: list[tuple[str, str]] = []
    manual_matched: list[str] = []
    source_label = manual_torque_source_label_for_title(title)
    seen = set()
    for step in steps:
        for body in step.body_lines:
            match = re.search(r"(.+?)\s+to\s+\*\*(\d+\s*Nm)\*\*", body, flags=re.IGNORECASE)
            if not match:
                continue
            component = match.group(1).strip()
            torque = match.group(2).replace("  ", " ")
            key = (component.lower(), torque)
            if key in seen:
                continue
            seen.add(key)
            summary.append((component[0].upper() + component[1:], torque))
            manual_matched.append(f"{component[0].upper() + component[1:]}: **{torque}** from {source_label}.")
    return summary, manual_matched


def write_manifest(video_dir: Path, title: str, video_url: str, playlist: dict, steps: list[Step]) -> None:
    manifest = {
        "slug": video_dir.name,
        "title": title,
        "video_url": video_url,
        "source_family": playlist["source_family"],
        "applicability_label": playlist["applicability_label"],
        "applicable_models": playlist["applicable_models"],
        "playlist_title": playlist["title"],
        "tutorial_markdown": "tutorial.md",
        "source_video": "source/video.mp4",
        "screenshots_dir": "assets/screenshots",
        "contact_sheet": "assets/contact-sheet.jpg",
        "pdf_output": f"output/pdf/{slugify(title)}.pdf",
        "pdf_render_dir": "tmp/pdfs",
        "references": [playlist["manual_url"]],
        "frames": [
            {
                "timestamp": int(step.start if step.duration < 2 else step.start + min(1.0, step.duration / 2)),
                "name": step.screenshot_name,
            }
            for step in steps
        ],
    }
    (video_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_tutorial(video_dir: Path, title: str, video_title: str, steps: list[Step], sections: list[tuple[str, list[Step]]]) -> None:
    torque_summary, manual_lines = collect_torque_lines(steps, title)
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Source video: `{video_title}` by Stark Future Official")
    lines.append("")
    lines.append(f"Applicable models: `{applicability_label_for_title(title)}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    if steps and steps[0].mode == "visual":
        lines.append(
            "This guide follows the same step-by-step workshop structure as the MX tutorials, but it is derived as a visual sequence from the official Stark Future ASMR video. "
            "Because the source video does not provide usable captions or narration, the procedure is documented through curated screenshots and concise action guidance."
        )
    else:
        lines.append(
            "This guide converts the official Stark Future tutorial video into a step-by-step workshop procedure. "
            "It documents each action shown in the video in sequence and pairs every step with a dedicated screenshot."
        )
    lines.append("")
    lines.append("## Preparation")
    lines.append("")
    for item in GENERIC_PREPARATION:
        lines.append(f"- {item}")
    lines.append("")

    for section_title, section_steps in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        for step in section_steps:
            lines.append(f"### {step.index}. {step.title}")
            lines.append("")
            for body in step.body_lines:
                lines.append(body)
                lines.append("")
            lines.append(f"![Step {step.index} - {step.title.lower()}](assets/screenshots/{step.screenshot_name}.jpg)")
            lines.append("")

    if torque_summary:
        lines.append("## Torque Summary")
        lines.append("")
        lines.append("| Component | Torque |")
        lines.append("| --- | ---: |")
        for component, torque in torque_summary:
            lines.append(f"| {component} | {torque} |")
        lines.append("")
        lines.append("Verified torque items:")
        lines.append("")
        for item in manual_lines:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Critical Checks Before Riding")
    lines.append("")
    lines.append("- Confirm the serviced component is fully seated and all fasteners are tightened in the correct order.")
    lines.append("- Recheck all torque-critical hardware before riding.")
    lines.append("- Make sure all routed cables, clips, brackets, and surrounding parts are returned to their original positions.")
    lines.append("- Inspect the bike visually for any missing hardware before returning it to service.")
    lines.append("")
    (video_dir / "tutorial.md").write_text("\n".join(lines), encoding="utf-8")


def download_video(video_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "python",
            "-m",
            "yt_dlp",
            "--no-playlist",
            "--js-runtimes",
            "node",
            "--retries",
            "20",
            "--file-access-retries",
            "20",
            "--fragment-retries",
            "20",
            "--force-overwrites",
            "--no-part",
            "-f",
            "22/18/136",
            "-o",
            str(output_path),
            video_url,
        ],
        cwd=ROOT,
        check=True,
    )


def run_script(script_name: str, video_dir: Path) -> None:
    subprocess.run(
        ["python", str(ROOT / "scripts" / script_name), str(video_dir)],
        cwd=ROOT,
        check=True,
    )


def run_root_script(script_name: str) -> None:
    subprocess.run(
        ["python", str(ROOT / "scripts" / script_name)],
        cwd=ROOT,
        check=True,
    )


def process_video(entry: dict, playlist: dict, skip_existing: bool) -> dict:
    if not entry.get("id") or not entry.get("title") or entry.get("title") == "[Private video]":
        return {"slug": slugify(entry.get("title", "unavailable-video")), "status": "unavailable"}

    title = entry["title"]
    video_id = entry["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    slug = slugify(title)
    video_dir = VIDEOS_DIR / slug
    manifest_path = video_dir / "manifest.json"
    if skip_existing and manifest_path.exists() and (video_dir / "tutorial.md").exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            existing_pdf = video_dir / existing_manifest["pdf_output"]
            if existing_pdf.exists():
                return {"slug": slug, "status": "skipped"}
        except Exception:
            pass

    (video_dir / "assets" / "screenshots").mkdir(parents=True, exist_ok=True)
    (video_dir / "output" / "pdf").mkdir(parents=True, exist_ok=True)
    (video_dir / "tmp" / "pdfs").mkdir(parents=True, exist_ok=True)

    source_video = video_dir / "source" / "video.mp4"
    download_video(video_url, source_video)

    try:
        transcript = fetch_transcript(video_id)
        steps = build_steps(transcript)
    except YouTubeTranscriptApiException:
        steps = build_visual_fallback_steps(title, int(entry.get("duration") or 120))
    tutorial_title = tutorial_title_from_video_title(title)
    write_manifest(video_dir, tutorial_title, video_url, playlist, steps)
    write_tutorial(video_dir, tutorial_title, title, steps, split_sections(title, steps))

    run_script("extract_frames.py", video_dir)
    run_script("build_tutorial_pdf.py", video_dir)
    run_script("render_pdf_pages.py", video_dir)

    if source_video.exists():
        source_video.unlink()
    if source_video.parent.exists() and not any(source_video.parent.iterdir()):
        source_video.parent.rmdir()

    return {"slug": slug, "status": "generated", "steps": len(steps)}


def write_library_index(results: list[dict]) -> None:
    readme = ROOT / "README.md"
    lines = [
        "# Stark Varg Tutorials",
        "",
        "Garage-friendly Stark VARG service tutorials converted from the official Stark Future video playlists into step-by-step markdown guides and printable PDFs.",
        "",
        "## Source Material",
        "",
        "These tutorials are derived from videos published on Stark Future's official YouTube playlists.",
        "",
        "- Original MX playlist: https://www.youtube.com/playlist?list=PLkap5aPwLLRBoeCpkpNh-ayt6BO0oiq2y",
        "- MX 1.2 playlist: https://www.youtube.com/playlist?list=PLkap5aPwLLRBqClumfq428p7DvfueeWdW",
        "- EX playlist: https://www.youtube.com/playlist?list=PLkap5aPwLLRCEirHu95EHvDsCDujl3ia_",
        "",
        "## Copyright and Attribution",
        "",
        "Stark VARG, Stark Future, the official manuals, and the original video content remain the property of their respective owners.",
        "",
        "This repository does not claim ownership of Stark's source material. It only organizes publicly available official video guidance into a more workshop-friendly reference format and links back to official sources where possible.",
        "",
        "## Why This Library Exists",
        "",
        "Watching a video while working on the bike is awkward when your hands are dirty, the bike is on a stand, and the step you need is buried in a long clip. This library turns each official video into a workshop document that is easier to use next to the bike.",
        "",
        "Each tutorial is built to be practical in the garage:",
        "",
        "- One discrete service action per numbered step.",
        "- A clear screenshot for every step so the visual reference stays close to the instruction.",
        "- Removal and installation broken apart so reassembly is easier to follow.",
        "- Torque values called out in the relevant steps when they are available.",
        "- A PDF version for phone, tablet, laptop, or printed bench use.",
        "",
        "## Disclaimer",
        "",
        "This repository is an unofficial convenience conversion of Stark Future's original video content into written guides and PDFs. It is provided for general guidance only.",
        "",
        "By using this repository, you accept full responsibility for any maintenance, inspection, assembly, torque verification, riding, damage, injury, or loss connected to its use. Always refer to official Stark documentation and use your own judgment before working on the bike. No warranty or liability is assumed for accuracy, completeness, interpretation, or results.",
        "",
        "## Library",
        "",
        "Original MX procedures are marked `MX`.",
        "",
        "MX 1.2-derived procedures are marked `MX 1.2 / EX` where the same service steps apply to both bikes.",
        "",
    ]
    existing_entries: list[dict] = []
    for video_dir in sorted(path for path in VIDEOS_DIR.iterdir() if path.is_dir() and not path.name.startswith("_")):
        tutorial_path = video_dir / "tutorial.md"
        manifest_path = video_dir / "manifest.json"
        if not tutorial_path.exists() or not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            title = spaced_stark_model(manifest.get("title", tutorial_path.stem))
            metadata = metadata_from_manifest(manifest, title)
            pdf_output = manifest.get("pdf_output", "")
            existing_entries.append(
                {
                    "slug": video_dir.name,
                    "playlist": metadata["playlist_title"],
                    "title": title,
                    "pdf_output": pdf_output,
                }
            )
        except Exception:
            continue

    for playlist in PLAYLISTS:
        lines.append(f"### {playlist['title']}")
        lines.append("")
        entries = sorted(
            [r for r in existing_entries if r.get("playlist") == playlist["title"]],
            key=lambda item: item["title"],
        )
        for item in entries:
            slug = item["slug"]
            lines.append(f"- [{display_title_with_applicability(item['title'])}](videos/{slug}/{item['pdf_output']})")
        lines.append("")
    readme.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    results: list[dict] = []
    selected_playlists = PLAYLISTS
    if args.playlist_labels:
        selected = set(args.playlist_labels)
        selected_playlists = [playlist for playlist in PLAYLISTS if playlist["label"] in selected]

    for playlist in selected_playlists:
        entries = get_playlist_entries(playlist["url"])
        if args.limit_per_playlist:
            entries = entries[: args.limit_per_playlist]
        for entry in entries:
            result = process_video(entry, playlist, args.skip_existing)
            result["playlist"] = playlist["title"]
            results.append(result)
    write_library_index(results)
    run_root_script("build_site_data.py")


if __name__ == "__main__":
    main()
