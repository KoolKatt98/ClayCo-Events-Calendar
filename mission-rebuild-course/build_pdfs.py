#!/usr/bin/env python3
"""
MISSION REBUILD™ — PDF Builder
Converts all Markdown files in the course folder to PDFs using ReportLab.
Produces individual PDFs per file + one combined full-course PDF.
"""

import os
import re
import glob
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

# Brand colors
DARK = HexColor("#1a1a2e")
ACCENT = HexColor("#c8a951")   # Gold
MID = HexColor("#2d3561")      # Navy
LIGHT_BG = HexColor("#f5f5f0")
GRAY = HexColor("#555555")
LIGHT_GRAY = HexColor("#999999")

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Style setup
# ---------------------------------------------------------------------------

def make_styles():
    styles = getSampleStyleSheet()

    base = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10.5,
        leading=16,
        textColor=HexColor("#222222"),
        spaceAfter=6,
    )

    h1 = ParagraphStyle(
        "H1",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=DARK,
        spaceAfter=10,
        spaceBefore=18,
    )

    h2 = ParagraphStyle(
        "H2",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=22,
        textColor=MID,
        spaceAfter=8,
        spaceBefore=14,
    )

    h3 = ParagraphStyle(
        "H3",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=DARK,
        spaceAfter=6,
        spaceBefore=10,
    )

    h4 = ParagraphStyle(
        "H4",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=MID,
        spaceAfter=4,
        spaceBefore=8,
    )

    bullet = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        leftIndent=18,
        firstLineIndent=0,
        textColor=HexColor("#222222"),
        spaceAfter=3,
    )

    code = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=9,
        leading=13,
        leftIndent=20,
        textColor=HexColor("#333333"),
        backColor=HexColor("#f0f0e8"),
        spaceAfter=6,
        spaceBefore=4,
    )

    accent_line = ParagraphStyle(
        "AccentLine",
        fontName="Helvetica-BoldOblique",
        fontSize=11,
        leading=16,
        textColor=ACCENT,
        spaceAfter=8,
        spaceBefore=4,
    )

    label = ParagraphStyle(
        "Label",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=ACCENT,
        spaceAfter=2,
        spaceBefore=8,
    )

    return {
        "body": base,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "bullet": bullet,
        "code": code,
        "accent": accent_line,
        "label": label,
    }


# ---------------------------------------------------------------------------
# Markdown → ReportLab flowables
# ---------------------------------------------------------------------------

def escape_xml(text):
    """Escape characters that break ReportLab's XML parser."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def apply_inline(text):
    """Convert inline Markdown bold/italic to ReportLab markup."""
    text = escape_xml(text)
    # Bold-italic ***text***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic *text*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Inline code `text`
    text = re.sub(r'`(.+?)`', r'<font name="Courier" size="9">\1</font>', text)
    return text


def md_to_flowables(md_text, styles):
    """Parse Markdown text into a list of ReportLab Platypus flowables."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Code fences
        if line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_lines)
                for cl in code_lines:
                    flowables.append(Paragraph(escape_xml(cl) or "&nbsp;", styles["code"]))
                code_lines = []
                flowables.append(Spacer(1, 4))
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line):
            flowables.append(Spacer(1, 6))
            flowables.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = apply_inline(m.group(2).strip())
            style_key = f"h{min(level, 4)}"
            if level == 1:
                flowables.append(Spacer(1, 8))
                flowables.append(Paragraph(text, styles["h1"]))
                flowables.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
                flowables.append(Spacer(1, 6))
            elif level == 2:
                flowables.append(Paragraph(text, styles["h2"]))
            elif level == 3:
                flowables.append(Paragraph(text, styles["h3"]))
            else:
                flowables.append(Paragraph(text, styles["h4"]))
            i += 1
            continue

        # Bullet points (-, *, +)
        m = re.match(r'^(\s*)([-*+])\s+(.*)', line)
        if m:
            indent_level = len(m.group(1)) // 2
            text = apply_inline(m.group(3))
            bullet_char = "•" if indent_level == 0 else "–"
            bullet_style = ParagraphStyle(
                "BulletIndented",
                parent=styles["bullet"],
                leftIndent=20 + indent_level * 16,
            )
            flowables.append(Paragraph(f"{bullet_char}&nbsp;&nbsp;{text}", bullet_style))
            i += 1
            continue

        # Numbered lists
        m = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if m:
            text = apply_inline(m.group(2))
            indent_level = len(m.group(1)) // 2
            num_style = ParagraphStyle(
                "NumList",
                parent=styles["bullet"],
                leftIndent=24 + indent_level * 16,
            )
            # Find list number
            num_match = re.match(r'^(\s*)(\d+)\.', line)
            num = num_match.group(2) if num_match else "1"
            flowables.append(Paragraph(f"{num}.&nbsp;&nbsp;{text}", num_style))
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            text = apply_inline(line.lstrip("> ").strip())
            flowables.append(Paragraph(f"<i>{text}</i>", styles["accent"]))
            i += 1
            continue

        # Bold-only line (label style)
        m = re.match(r'^\*\*([^*]+)\*\*\s*$', line.strip())
        if m and len(line.strip()) < 80:
            text = apply_inline(line.strip())
            flowables.append(Paragraph(text, styles["h4"]))
            i += 1
            continue

        # Empty line
        if line.strip() == "":
            flowables.append(Spacer(1, 5))
            i += 1
            continue

        # Regular paragraph
        text = apply_inline(line.strip())
        if text:
            flowables.append(Paragraph(text, styles["body"]))
        i += 1

    return flowables


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def header_footer(canvas, doc):
    canvas.saveState()
    w, h = letter

    # Header bar
    canvas.setFillColor(DARK)
    canvas.rect(0, h - 0.55 * inch, w, 0.55 * inch, fill=True, stroke=False)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h - 0.58 * inch, w, 0.04 * inch, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(white)
    canvas.drawString(0.5 * inch, h - 0.38 * inch, "MISSION REBUILD™")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(ACCENT)
    canvas.drawRightString(w - 0.5 * inch, h - 0.38 * inch,
                           "From Army to Civilian")

    # Footer
    canvas.setFillColor(LIGHT_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.5 * inch, 0.35 * inch,
                      "© MISSION REBUILD™ | missionrebuild.com")
    canvas.drawRightString(w - 0.5 * inch, 0.35 * inch,
                           f"Page {doc.page}")
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0.55 * inch, w, 0.02 * inch, fill=True, stroke=False)

    canvas.restoreState()


def make_cover_page(title, subtitle, styles):
    """Generate a styled cover page flowable list."""
    w, h = letter
    flowables = []
    flowables.append(Spacer(1, 1.8 * inch))

    cover_title = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=40,
        textColor=DARK,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    cover_sub = ParagraphStyle(
        "CoverSub",
        fontName="Helvetica",
        fontSize=14,
        leading=20,
        textColor=MID,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    cover_tag = ParagraphStyle(
        "CoverTag",
        fontName="Helvetica-BoldOblique",
        fontSize=12,
        leading=18,
        textColor=ACCENT,
        alignment=TA_CENTER,
    )

    flowables.append(Paragraph("MISSION REBUILD™", cover_title))
    flowables.append(HRFlowable(width="60%", thickness=3, color=ACCENT,
                                hAlign="CENTER"))
    flowables.append(Spacer(1, 12))
    flowables.append(Paragraph(title, cover_sub))
    if subtitle:
        flowables.append(Spacer(1, 6))
        flowables.append(Paragraph(subtitle, cover_tag))
    flowables.append(Spacer(1, 0.4 * inch))
    flowables.append(HRFlowable(width="40%", thickness=1, color=LIGHT_GRAY,
                                hAlign="CENTER"))
    flowables.append(Spacer(1, 12))
    tagline = ParagraphStyle(
        "Tagline",
        fontName="Helvetica-Oblique",
        fontSize=11,
        leading=16,
        textColor=GRAY,
        alignment=TA_CENTER,
    )
    flowables.append(Paragraph(
        "From Army to Civilian: Building Structure, Purpose,<br/>"
        "Identity &amp; Financial Stability After Service",
        tagline
    ))
    flowables.append(PageBreak())
    return flowables


# ---------------------------------------------------------------------------
# Build a single PDF from one Markdown file
# ---------------------------------------------------------------------------

def build_pdf_from_md(md_path: Path, pdf_path: Path, styles):
    md_text = md_path.read_text(encoding="utf-8")

    # Extract first H1 as title
    title_match = re.search(r'^#\s+(.+)', md_text, re.MULTILINE)
    title = title_match.group(1) if title_match else md_path.stem.replace("-", " ").title()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.8 * inch,
        title=f"MISSION REBUILD™ — {title}",
        author="MISSION REBUILD™",
    )

    story = make_cover_page(title, "", styles)
    story += md_to_flowables(md_text, styles)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"  ✓ {pdf_path.name}")


# ---------------------------------------------------------------------------
# Build the combined full-course PDF
# ---------------------------------------------------------------------------

FILE_ORDER = [
    "README.md",
    "course-positioning.md",
    "syllabus.md",
    "modules/module-00-introduction.md",
    "modules/module-01-identity-after-service.md",
    "modules/module-02-discipline-without-the-military.md",
    "modules/module-03-financial-stability-and-leverage.md",
    "modules/module-04-career-and-civilian-professionalism.md",
    "modules/module-05-isolation-burnout-and-mental-resilience.md",
    "modules/module-06-relationships-and-communication.md",
    "modules/module-07-physical-health-and-performance.md",
    "modules/module-08-veteran-benefits-and-systems.md",
    "modules/module-09-ownership-and-entrepreneurship.md",
    "modules/module-10-leadership-community-and-legacy.md",
    "modules/module-11-designing-your-next-mission.md",
    "projects/mid-course-project.md",
    "projects/final-project.md",
    "assessments/quizzes.md",
    "assessments/rubrics.md",
    "worksheets/workbook.md",
    "resources/resource-list.md",
    "resources/glossary.md",
    "instructor-guide.md",
    "marketing/sales-page.md",
    "marketing/email-sequence.md",
    "marketing/content-strategy.md",
    "marketing/lead-magnet.md",
    "certificate-template.md",
]


def build_combined_pdf(base_dir: Path, pdf_path: Path, styles):
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.8 * inch,
        title="MISSION REBUILD™ — Complete Course Package",
        author="MISSION REBUILD™",
    )

    story = make_cover_page(
        "Complete Course Package",
        "All Modules, Projects, Assessments, Worksheets & Marketing",
        styles
    )

    for rel_path in FILE_ORDER:
        md_path = base_dir / rel_path
        if not md_path.exists():
            print(f"  ⚠ Skipping (not yet generated): {rel_path}")
            continue

        md_text = md_path.read_text(encoding="utf-8")
        story.append(PageBreak())
        story += md_to_flowables(md_text, styles)
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"  ✓ {pdf_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    styles = make_styles()

    print("\n=== MISSION REBUILD™ — PDF Builder ===\n")

    # Collect all .md files (excluding this script's folder artefacts)
    all_md = sorted(BASE_DIR.rglob("*.md"))
    # Exclude any files inside pdfs/ folder
    all_md = [f for f in all_md if "pdfs" not in f.parts and f.name != "build_pdfs.py"]

    print(f"Found {len(all_md)} Markdown files.\n")
    print("Building individual PDFs...")

    for md_path in all_md:
        # Mirror directory structure inside pdfs/
        rel = md_path.relative_to(BASE_DIR)
        pdf_subdir = PDF_DIR / rel.parent
        pdf_subdir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_subdir / (md_path.stem + ".pdf")
        try:
            build_pdf_from_md(md_path, pdf_path, styles)
        except Exception as e:
            print(f"  ✗ ERROR on {md_path.name}: {e}")

    print("\nBuilding combined full-course PDF...")
    combined_path = PDF_DIR / "MISSION-REBUILD-Complete-Course.pdf"
    try:
        build_combined_pdf(BASE_DIR, combined_path, styles)
    except Exception as e:
        print(f"  ✗ ERROR on combined PDF: {e}")

    print("\nDone! PDFs saved to:")
    print(f"  {PDF_DIR}/")
    for pdf in sorted(PDF_DIR.rglob("*.pdf")):
        size_kb = pdf.stat().st_size // 1024
        print(f"    {pdf.relative_to(PDF_DIR)}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
