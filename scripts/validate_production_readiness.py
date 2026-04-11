from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"
REPORT_PATH = ROOT / "PRODUCTION_READINESS_REPORT.md"


SUSPICIOUS_INSTALL_PATTERNS = [
    re.compile(r"^\s*disconnect\b", re.I),
    re.compile(r"^\s*loosen\b", re.I),
    re.compile(r"^\s*untighten\b", re.I),
    re.compile(r"\bdrain the\b", re.I),
    re.compile(r"\bdrain fluid\b", re.I),
    re.compile(r"^\s*remove\s+.+\s+from the bike\b", re.I),
]

SUSPICIOUS_REMOVAL_PATTERNS = [
    re.compile(r"^\s*reconnect\b", re.I),
    re.compile(r"^\s*connect\b", re.I),
    re.compile(r"^\s*tighten\b", re.I),
    re.compile(r"^\s*fill\b", re.I),
]

FASTENER_WORDS = (
    "bolt",
    "bolts",
    "nut",
    "nuts",
    "screw",
    "screws",
    "pin",
    "pins",
    "clamp",
    "clamps",
    "banjo",
    "axle",
    "shaft",
    "bridge bolt",
    "bridge bolts",
)

NON_TORQUE_INSTALL_EXCLUSIONS = (
    "hose clamp",
    "hose clamps",
    "rubber strap",
    "bearing",
    "bearings",
    "circlip",
    "o-ring",
    "seal",
    "phone",
    "plug",
    "connector",
    "connectors",
    "bleed hose",
)

TYPO_RESIDUE_PATTERNS = [
    "is permitted only with the express written permission",
    "step 4 require at least two people",
    "untighten",
    "spouier",
    "shoct",
    "olace",
    "stots",
    "topo",
    "frant",
]


def strip_image_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("!["))


@dataclass
class Step:
    number: int
    title: str
    body: str
    section: str
    line: int


@dataclass
class Finding:
    severity: str
    line: int
    message: str


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def split_steps(text: str) -> list[Step]:
    lines = text.splitlines()
    steps: list[Step] = []
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip().lower()
            i += 1
            continue
        match = re.match(r"^###\s+(\d+)\.\s+(.+)$", line)
        if not match:
            i += 1
            continue
        number = int(match.group(1))
        title = match.group(2).strip()
        body_lines: list[str] = []
        i += 1
        while i < len(lines):
            current = lines[i]
            if current.startswith("## ") or current.startswith("### "):
                break
            stripped = current.strip()
            if stripped and not stripped.startswith("!["):
                body_lines.append(stripped)
            i += 1
        steps.append(Step(number, title, " ".join(body_lines).strip(), section, i - len(body_lines)))
    return steps


def is_fastener_install_step(step: Step) -> bool:
    title = step.title.lower()
    body = step.body.lower()
    text = f"{title} {body}"
    if any(exclusion in text for exclusion in NON_TORQUE_INSTALL_EXCLUSIONS):
        return False
    has_fastener = any(word in text for word in FASTENER_WORDS)
    if not has_fastener:
        return False
    install_action = any(re.match(rf"^\s*{verb}\b", candidate) for verb in ("tighten", "secure") for candidate in (title, body))
    if not install_action:
        install_starts = any(re.match(r"^\s*install\b", candidate) for candidate in (title, body))
        if install_starts:
            install_action = any(word in text for word in ("bolt", "bolts", "nut", "nuts", "screw", "screws", "banjo"))
    if "by hand" in text:
        return False
    return has_fastener and install_action


def has_torque(step: Step) -> bool:
    text = f"{step.title} {step.body}".lower()
    return (
        bool(re.search(r"\b\d+(?:\.\d+)?\s*nm\b", text))
        or "etched torque" in text
        or "engraved on the part" in text
        or "torque value" in text
        or bool(re.search(r"\bfinal\b.*\btorque\b", text))
        or "official stark specification" in text
    )


def classify_findings(slug: str, text: str, steps: list[Step]) -> list[Finding]:
    findings: list[Finding] = []
    text_without_images = strip_image_lines(text)

    seen_titles: dict[str, list[int]] = defaultdict(list)
    previous_body = ""
    previous_step: Step | None = None

    for step in steps:
        title_key = normalize(step.title)
        seen_titles[title_key].append(step.number)

        body_key = normalize(step.body)
        if previous_step and body_key and body_key == previous_body:
            findings.append(
                Finding(
                    "medium",
                    step.line,
                    f"Step {previous_step.number} and step {step.number} use the same body text; verify this is intentional mirrored work.",
                )
            )
        previous_body = body_key
        previous_step = step

        full = f"{step.title} {step.body}"
        lower = full.lower()
        if "installation procedure" in step.section:
            for pattern in SUSPICIOUS_INSTALL_PATTERNS:
                if "right fork clamp bolts" in lower or "right fork axle clamp bolts" in lower:
                    continue
                if pattern.search(step.title) or pattern.search(step.body):
                    findings.append(
                        Finding(
                            "high",
                            step.line,
                            f"Step {step.number} is inside installation but still reads like a removal action.",
                        )
                    )
                    break

            if is_fastener_install_step(step) and not has_torque(step):
                findings.append(
                    Finding(
                        "medium",
                        step.line,
                        f"Step {step.number} installs or tightens hardware without a visible torque note.",
                    )
                )

            if "banjo bolt" in lower and "copper washer" not in lower:
                findings.append(
                    Finding(
                        "medium",
                        step.line,
                        f"Step {step.number} references a banjo bolt without explicitly mentioning new or reused copper washers.",
                    )
                )

        if "removal procedure" in step.section:
            for pattern in SUSPICIOUS_REMOVAL_PATTERNS:
                if pattern.search(step.title) or pattern.search(step.body):
                    findings.append(
                        Finding(
                            "high",
                            step.line,
                            f"Step {step.number} is inside removal but reads like an installation action.",
                        )
                    )
                    break

    for title, numbers in seen_titles.items():
        if len(numbers) > 1:
            findings.append(
                Finding(
                    "medium",
                    0,
                    f"Repeated step title appears in steps {', '.join(map(str, numbers))}: `{title}`.",
                )
            )

    text_lower = text_without_images.lower()
    for pattern in TYPO_RESIDUE_PATTERNS:
        if pattern in text_lower:
            findings.append(
                Finding(
                    "medium" if pattern not in {"front caliper bleed screw", "is permitted only with the express written permission"} else "high",
                    0,
                    f"Suspicious residue or incorrect wording found: `{pattern}`.",
                )
            )

    if "rear-brake" in slug or "foot-brake" in slug:
        if "front caliper bleed screw" in text_lower:
            findings.append(
                Finding(
                    "high",
                    0,
                    "Rear brake guide still references a front caliper bleed screw.",
                )
            )

    if "front-brake" in slug and "rear caliper bleed screw" in text_lower:
        findings.append(
            Finding(
                "high",
                0,
                "Front brake guide still references a rear caliper bleed screw.",
            )
        )

    if "vcu" in slug and "disconnect the handlebar controls" in text_lower and "## installation procedure" in text_lower:
        install_part = text_lower.split("## installation procedure", 1)[1]
        if "disconnect the handlebar controls" in install_part:
            findings.append(
                Finding(
                    "high",
                    0,
                    "VCU installation still says to disconnect the handlebar controls instead of reconnecting them.",
                )
            )

    if re.search(r"\b\d+(?:\.\d+)?\s*nm\b", text_lower) and "## torque summary" not in text_lower:
        findings.append(
            Finding(
                "medium",
                0,
                "Guide includes torque values in the steps but does not provide a Torque Summary table.",
            )
        )

    return findings


def main() -> None:
    report_lines = [
        "# Production Readiness Report",
        "",
        "Automated checks focus on high-value trust risks for workshop repair PDFs.",
        "",
    ]

    summary = {"high": 0, "medium": 0}
    guide_count = 0
    guides_with_findings = 0

    for tutorial_path in sorted(VIDEOS_DIR.glob("*/tutorial.md")):
        guide_count += 1
        text = tutorial_path.read_text(encoding="utf-8-sig")
        steps = split_steps(text)
        findings = classify_findings(tutorial_path.parent.name, text, steps)
        if not findings:
            continue
        guides_with_findings += 1
        report_lines.append(f"## `{tutorial_path.parent.name}`")
        report_lines.append("")
        for finding in findings:
            summary[finding.severity] += 1
            prefix = "HIGH" if finding.severity == "high" else "MED"
            location = f" line {finding.line}" if finding.line else ""
            report_lines.append(f"- **{prefix}**{location}: {finding.message}")
        report_lines.append("")

    report_lines[3:3] = [
        f"- Guides reviewed: **{guide_count}**",
        f"- Guides with findings: **{guides_with_findings}**",
        f"- High-severity findings: **{summary['high']}**",
        f"- Medium-severity findings: **{summary['medium']}**",
        "",
    ]

    if guides_with_findings == 0:
        report_lines.extend(["- No findings.", ""])

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
