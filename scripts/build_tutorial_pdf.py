from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a PDF from a per-video tutorial markdown file.")
    parser.add_argument("video_dir", help="Path to a per-video workspace directory under videos/.")
    return parser.parse_args()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#111111"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#111111"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading3Custom",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#222222"),
            spaceBefore=6,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallNote",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#444444"),
            spaceAfter=6,
        )
    )
    return styles


def md_to_para(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def add_page_number(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(doc.pagesize[0] - 1.8 * cm, 1.2 * cm, f"Page {doc.page}")


def build_image(markdown_path: Path, relative_path: str):
    image_path = (markdown_path.parent / relative_path).resolve()
    img = Image(str(image_path))
    usable_width = A4[0] - 4 * cm
    img.drawWidth = usable_width
    img.drawHeight = usable_width * 9 / 16
    return img


def build_table(table_lines, styles):
    rows = []
    for idx, table_line in enumerate(table_lines):
        if idx == 1:
            continue
        parts = [md_to_para(cell.strip()) for cell in table_line.strip("|").split("|")]
        rows.append([Paragraph(part, styles["Body"]) for part in parts])
    table = Table(rows, colWidths=[9 * cm, 4 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7cfd9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def flush_kept_block(story, kept_block):
    if kept_block:
        story.append(KeepTogether(kept_block[:]))
        kept_block.clear()


def parse_markdown(markdown_path: Path, manifest: dict):
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    story = []
    styles = build_styles()
    kept_block = []
    block_kind = None
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            i += 1
            continue

        if line.startswith("# "):
            flush_kept_block(story, kept_block)
            block_kind = None
            story.append(Paragraph(md_to_para(line[2:]), styles["TitleCustom"]))
            link = manifest.get("video_url", "")
            if link:
                story.append(
                    Paragraph(
                        f"Video link: <a href=\"{html.escape(link, quote=True)}\">{html.escape(link)}</a>",
                        styles["SmallNote"],
                    )
                )
            i += 1
            continue

        if line.startswith("## "):
            flush_kept_block(story, kept_block)
            block_kind = "section"
            if story:
                story.append(Spacer(1, 0.15 * cm))
            kept_block.append(Paragraph(md_to_para(line[3:]), styles["Heading2Custom"]))
            i += 1
            continue

        if line.startswith("### "):
            if block_kind == "step":
                flush_kept_block(story, kept_block)
            kept_block.append(Paragraph(md_to_para(line[4:]), styles["Heading3Custom"]))
            block_kind = "step"
            i += 1
            continue

        if line.startswith("!["):
            match = re.search(r"\((.+?)\)", line)
            if match:
                kept_block.append(build_image(markdown_path, match.group(1)))
                kept_block.append(Spacer(1, 0.25 * cm))
                if block_kind is None:
                    block_kind = "step"
            i += 1
            continue

        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            kept_block.append(build_table(table_lines, styles))
            kept_block.append(Spacer(1, 0.25 * cm))
            if block_kind is None:
                block_kind = "section"
            continue

        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            for item in items:
                kept_block.append(Paragraph(md_to_para(f"- {item}"), styles["Body"]))
            kept_block.append(Spacer(1, 0.05 * cm))
            if block_kind is None:
                block_kind = "section"
            continue

        paragraph_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|##|###|!\[|\||- )", lines[i]):
            paragraph_lines.append(lines[i].strip())
            i += 1

        text = " ".join(paragraph_lines)
        style = styles["SmallNote"] if text.startswith("Source video:") or text.startswith("Note:") else styles["Body"]
        kept_block.append(Paragraph(md_to_para(text), style))
        if block_kind is None:
            block_kind = "section"

    flush_kept_block(story, kept_block)
    return story


def main():
    args = parse_args()
    video_dir = Path(args.video_dir).resolve()
    manifest = json.loads((video_dir / "manifest.json").read_text(encoding="utf-8"))
    markdown_path = video_dir / manifest["tutorial_markdown"]
    pdf_path = video_dir / manifest["pdf_output"]

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=manifest["title"],
        author="OpenAI Codex",
    )
    story = parse_markdown(markdown_path, manifest)
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    main()
