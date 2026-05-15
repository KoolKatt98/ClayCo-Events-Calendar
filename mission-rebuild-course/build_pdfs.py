#!/usr/bin/env python3
"""
MISSION REBUILD™ — PDF Builder
Produces:
  1. MISSION-REBUILD-Course-Book.pdf  — single premium sellable PDF
  2. Individual PDFs per file (in pdfs/individual/)
"""

import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether, Table, TableStyle, Flowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas

# ── Brand palette ────────────────────────────────────────────────────────────
DARK        = HexColor("#0d1117")   # near-black
NAVY        = HexColor("#1a2744")   # deep navy
GOLD        = HexColor("#c8a951")   # warm gold
GOLD_LIGHT  = HexColor("#e8c97a")
MID         = HexColor("#2d3561")   # section blue
WHITE       = white
OFF_WHITE   = HexColor("#f5f4ef")
GRAY        = HexColor("#555555")
LIGHT_GRAY  = HexColor("#aaaaaa")
RULE        = HexColor("#c8a951")

W, H = letter  # 8.5 × 11 inches

BASE_DIR = Path(__file__).parent
PDF_DIR  = BASE_DIR / "pdfs"
IND_DIR  = PDF_DIR / "individual"
PDF_DIR.mkdir(exist_ok=True)
IND_DIR.mkdir(exist_ok=True)

# ── File manifest (order matters for the book) ───────────────────────────────
SECTIONS = [
    {
        "label": "PART I — COURSE OVERVIEW",
        "files": [
            ("README.md",              "Course Overview"),
            ("course-positioning.md",  "Course Positioning"),
            ("syllabus.md",            "12-Week Syllabus"),
        ],
    },
    {
        "label": "PART II — MODULES",
        "files": [
            ("modules/module-00-introduction.md",                    "Module 00 · Orientation"),
            ("modules/module-01-identity-after-service.md",          "Module 01 · Identity After Service"),
            ("modules/module-02-discipline-without-the-military.md", "Module 02 · Discipline Without the Military"),
            ("modules/module-03-financial-stability-and-leverage.md","Module 03 · Financial Stability & Leverage"),
            ("modules/module-04-career-and-civilian-professionalism.md","Module 04 · Career & Civilian Professionalism"),
            ("modules/module-05-isolation-burnout-and-mental-resilience.md","Module 05 · Isolation, Burnout & Mental Resilience"),
            ("modules/module-06-relationships-and-communication.md", "Module 06 · Relationships & Communication"),
            ("modules/module-07-physical-health-and-performance.md", "Module 07 · Physical Health & Performance"),
            ("modules/module-08-veteran-benefits-and-systems.md",    "Module 08 · Veteran Benefits & Systems"),
            ("modules/module-09-ownership-and-entrepreneurship.md",  "Module 09 · Ownership & Entrepreneurship"),
            ("modules/module-10-leadership-community-and-legacy.md", "Module 10 · Leadership, Community & Legacy"),
            ("modules/module-11-designing-your-next-mission.md",     "Module 11 · Designing Your Next Mission"),
        ],
    },
    {
        "label": "PART III — PROJECTS",
        "files": [
            ("projects/mid-course-project.md", "Mid-Course Project · The Civilian Rebuild Blueprint"),
            ("projects/final-project.md",       "Final Project · The Next Mission Plan"),
        ],
    },
    {
        "label": "PART IV — ASSESSMENTS",
        "files": [
            ("assessments/quizzes.md", "Module Quizzes"),
            ("assessments/rubrics.md", "Grading Rubrics"),
        ],
    },
    {
        "label": "PART V — STUDENT WORKBOOK",
        "files": [
            ("worksheets/workbook.md", "Complete Student Workbook"),
        ],
    },
    {
        "label": "PART VI — RESOURCES",
        "files": [
            ("resources/resource-list.md", "Resource List"),
            ("resources/glossary.md",      "Glossary"),
        ],
    },
    {
        "label": "PART VII — INSTRUCTOR GUIDE",
        "files": [
            ("instructor-guide.md", "Instructor Guide"),
        ],
    },
    {
        "label": "PART VIII — MARKETING ASSETS",
        "files": [
            ("marketing/sales-page.md",       "Sales Page"),
            ("marketing/email-sequence.md",   "Email Launch Sequence"),
            ("marketing/content-strategy.md", "Content Strategy"),
            ("marketing/lead-magnet.md",      "Lead Magnet · The Veteran Rebuild Checklist"),
        ],
    },
    {
        "label": "PART IX — CERTIFICATE",
        "files": [
            ("certificate-template.md", "Certificate of Completion"),
        ],
    },
]


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10.5,
                               leading=17, textColor=HexColor("#1a1a1a"),
                               spaceAfter=6),
        "h1":   ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=20,
                               leading=26, textColor=NAVY,
                               spaceBefore=20, spaceAfter=10),
        "h2":   ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=15,
                               leading=21, textColor=MID,
                               spaceBefore=14, spaceAfter=8),
        "h3":   ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=12,
                               leading=17, textColor=NAVY,
                               spaceBefore=10, spaceAfter=5),
        "h4":   ParagraphStyle("H4", fontName="Helvetica-Bold", fontSize=10.5,
                               leading=15, textColor=MID,
                               spaceBefore=8, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10.5,
                                 leading=15, leftIndent=18, textColor=HexColor("#222222"),
                                 spaceAfter=3),
        "code": ParagraphStyle("Code", fontName="Courier", fontSize=9,
                               leading=13, leftIndent=20,
                               backColor=HexColor("#f0efe8"), spaceAfter=6),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-BoldOblique",
                                fontSize=11, leading=16, textColor=GOLD,
                                leftIndent=20, spaceAfter=8, spaceBefore=4),
        "toc_part": ParagraphStyle("TocPart", fontName="Helvetica-Bold",
                                   fontSize=12, leading=18, textColor=NAVY,
                                   spaceBefore=10, spaceAfter=2),
        "toc_item": ParagraphStyle("TocItem", fontName="Helvetica",
                                   fontSize=10, leading=15, textColor=GRAY,
                                   leftIndent=16, spaceAfter=1),
        "caption": ParagraphStyle("Caption", fontName="Helvetica-Oblique",
                                  fontSize=9, leading=13, textColor=LIGHT_GRAY,
                                  alignment=TA_CENTER),
    }


# ── Inline Markdown ───────────────────────────────────────────────────────────
def escape_xml(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(text):
    text = escape_xml(text)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.+?)\*\*',     r'<b>\1</b>',        text)
    text = re.sub(r'\*(.+?)\*',         r'<i>\1</i>',         text)
    text = re.sub(r'`(.+?)`',
                  r'<font name="Courier" size="9">\1</font>', text)
    return text


# ── Markdown → flowables ──────────────────────────────────────────────────────
def md_to_flowables(md_text, styles, chapter_name=""):
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_acc = []

    while i < len(lines):
        raw = lines[i]

        # code fence
        if raw.strip().startswith("```"):
            if in_code:
                in_code = False
                for cl in code_acc:
                    flowables.append(Paragraph(escape_xml(cl) or "&nbsp;",
                                               styles["code"]))
                code_acc = []
                flowables.append(Spacer(1, 4))
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_acc.append(raw)
            i += 1
            continue

        # HR
        if re.match(r'^[-*_]{3,}\s*$', raw):
            flowables.append(Spacer(1, 6))
            flowables.append(HRFlowable(width="100%", thickness=1, color=GOLD))
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.*)', raw)
        if m:
            lvl  = len(m.group(1))
            text = inline(m.group(2).strip())
            if lvl == 1:
                flowables.append(Spacer(1, 8))
                flowables.append(Paragraph(text, styles["h1"]))
                flowables.append(HRFlowable(width="100%", thickness=2,
                                            color=GOLD))
                flowables.append(Spacer(1, 6))
            elif lvl == 2:
                flowables.append(Paragraph(text, styles["h2"]))
            elif lvl == 3:
                flowables.append(Paragraph(text, styles["h3"]))
            else:
                flowables.append(Paragraph(text, styles["h4"]))
            i += 1
            continue

        # Bullets
        m = re.match(r'^(\s*)([-*+])\s+(.*)', raw)
        if m:
            depth = len(m.group(1)) // 2
            text  = inline(m.group(3))
            s = ParagraphStyle("B_", parent=styles["bullet"],
                               leftIndent=18 + depth * 16)
            char = "•" if depth == 0 else "–"
            flowables.append(Paragraph(f"{char}&nbsp;&nbsp;{text}", s))
            i += 1
            continue

        # Numbered list
        m = re.match(r'^(\s*)(\d+)\.\s+(.*)', raw)
        if m:
            depth = len(m.group(1)) // 2
            num   = m.group(2)
            text  = inline(m.group(3))
            s = ParagraphStyle("N_", parent=styles["bullet"],
                               leftIndent=24 + depth * 16)
            flowables.append(Paragraph(f"{num}.&nbsp;&nbsp;{text}", s))
            i += 1
            continue

        # Blockquote
        if raw.startswith(">"):
            text = inline(raw.lstrip("> ").strip())
            flowables.append(Paragraph(f"<i>{text}</i>", styles["quote"]))
            i += 1
            continue

        # Blank line
        if raw.strip() == "":
            flowables.append(Spacer(1, 5))
            i += 1
            continue

        # Regular paragraph
        text = inline(raw.strip())
        if text:
            flowables.append(Paragraph(text, styles["body"]))
        i += 1

    return flowables


# ── Page callbacks ────────────────────────────────────────────────────────────
class BookState:
    chapter = ""
    part    = ""

state = BookState()

def cover_page_cb(c, doc):
    """Full-bleed dark cover — called only on page 1."""
    # Background
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=True, stroke=False)

    # Gold top bar
    c.setFillColor(GOLD)
    c.rect(0, H - 0.18 * inch, W, 0.18 * inch, fill=True, stroke=False)

    # Gold bottom bar
    c.rect(0, 0, W, 0.18 * inch, fill=True, stroke=False)

    # Vertical gold rule left
    c.rect(0.55 * inch, 0.18 * inch, 0.04 * inch,
           H - 0.36 * inch, fill=True, stroke=False)

    # MISSION REBUILD™ — large
    c.setFont("Helvetica-Bold", 52)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H * 0.62, "MISSION REBUILD")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(GOLD)
    c.drawCentredString(W / 2, H * 0.56, "™")

    # Gold rule under title
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(1.4 * inch, H * 0.535, W - 1.4 * inch, H * 0.535)

    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(OFF_WHITE)
    c.drawCentredString(W / 2, H * 0.50,
                        "From Army to Civilian:")
    c.drawCentredString(W / 2, H * 0.465,
                        "Building Structure, Purpose, Identity &")
    c.drawCentredString(W / 2, H * 0.43,
                        "Financial Stability After Service")

    # Divider
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(2.2 * inch, H * 0.40, W - 2.2 * inch, H * 0.40)

    # Tag line
    c.setFont("Helvetica-BoldOblique", 11)
    c.setFillColor(GOLD_LIGHT)
    c.drawCentredString(W / 2, H * 0.37,
                        "A 12-Week Life Operating System for Military Veterans")

    # Bottom tag
    c.setFont("Helvetica", 10)
    c.setFillColor(LIGHT_GRAY)
    c.drawCentredString(W / 2, H * 0.10,
                        "COMPLETE COURSE PACKAGE")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GOLD)
    c.drawCentredString(W / 2, H * 0.07, "missionrebuild.com")

    # Bottom gold quote
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(LIGHT_GRAY)
    c.drawCentredString(W / 2, 0.28 * inch,
                        '"The mission doesn\'t end at ETS. It evolves."')


def inner_page_cb(c, doc):
    """Header + footer for every interior page."""
    # Header bar
    c.setFillColor(NAVY)
    c.rect(0, H - 0.5 * inch, W, 0.5 * inch, fill=True, stroke=False)
    c.setFillColor(GOLD)
    c.rect(0, H - 0.52 * inch, W, 0.03 * inch, fill=True, stroke=False)

    # Header text
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(0.55 * inch, H - 0.33 * inch, "MISSION REBUILD™")
    c.setFont("Helvetica", 8)
    c.setFillColor(GOLD_LIGHT)
    chapter_text = state.chapter[:80] if state.chapter else ""
    c.drawRightString(W - 0.5 * inch, H - 0.33 * inch, chapter_text)

    # Footer
    c.setFillColor(GOLD)
    c.rect(0, 0.48 * inch, W, 0.02 * inch, fill=True, stroke=False)
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawString(0.55 * inch, 0.28 * inch,
                 "© MISSION REBUILD™ | missionrebuild.com")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawRightString(W - 0.5 * inch, 0.28 * inch, str(doc.page))


# ── Cover back / copyright page ───────────────────────────────────────────────
def copyright_page(styles):
    items = []
    items.append(Spacer(1, 3 * inch))
    t = ParagraphStyle("CopyTitle", fontName="Helvetica-Bold", fontSize=14,
                       textColor=NAVY, alignment=TA_CENTER, spaceAfter=16)
    items.append(Paragraph("MISSION REBUILD™", t))
    items.append(HRFlowable(width="40%", thickness=1, color=GOLD,
                             hAlign="CENTER"))
    items.append(Spacer(1, 16))
    body_c = ParagraphStyle("CopyBody", fontName="Helvetica", fontSize=9.5,
                            leading=15, textColor=GRAY, alignment=TA_CENTER)
    lines = [
        "Complete Course Package",
        " ",
        "© MISSION REBUILD™. All rights reserved.",
        "No portion of this material may be reproduced, shared,",
        "or distributed without written permission from the creator.",
        " ",
        "This course is intended for educational and informational purposes.",
        "It does not constitute financial, legal, or mental health advice.",
        "Veterans in crisis: contact the Veterans Crisis Line — dial 988, press 1.",
        " ",
        "First Edition",
        " ",
        "missionrebuild.com",
    ]
    for line in lines:
        items.append(Paragraph(line or "&nbsp;", body_c))
    items.append(PageBreak())
    return items


# ── Table of Contents ─────────────────────────────────────────────────────────
def toc_page(styles):
    items = []
    title_s = ParagraphStyle("TocH", fontName="Helvetica-Bold", fontSize=22,
                             textColor=NAVY, spaceAfter=6)
    items.append(Spacer(1, 0.2 * inch))
    items.append(Paragraph("TABLE OF CONTENTS", title_s))
    items.append(HRFlowable(width="100%", thickness=2, color=GOLD))
    items.append(Spacer(1, 14))

    for section in SECTIONS:
        items.append(Paragraph(section["label"], styles["toc_part"]))
        for rel_path, display_name in section["files"]:
            full = BASE_DIR / rel_path
            marker = "✓" if full.exists() else "–"
            items.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{marker}&nbsp;&nbsp;{display_name}",
                                   styles["toc_item"]))
        items.append(Spacer(1, 6))

    items.append(PageBreak())
    return items


# ── Section divider page ──────────────────────────────────────────────────────
class SectionDivider(Flowable):
    def __init__(self, part_label, description=""):
        Flowable.__init__(self)
        self.part_label  = part_label
        self.description = description
        self._avail_w = 0
        self._avail_h = 0

    def wrap(self, availWidth, availHeight):
        self._avail_w = availWidth
        self._avail_h = availHeight
        self.width  = availWidth
        self.height = availHeight
        return (availWidth, availHeight)

    def draw(self):
        c = self.canv
        aw, ah = self._avail_w, self._avail_h
        # Dark background fills available frame space
        c.setFillColor(NAVY)
        c.rect(0, 0, aw, ah, fill=True, stroke=False)
        # Gold left accent bar
        c.setFillColor(GOLD)
        c.rect(0, 0, 0.1 * inch, ah, fill=True, stroke=False)
        # Gold top accent bar
        c.rect(0, ah - 0.1 * inch, aw, 0.1 * inch, fill=True, stroke=False)
        # Part text (vertically centered)
        mid_y = ah * 0.5
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(GOLD)
        c.drawString(0.5 * inch, mid_y + 20, self.part_label)
        # Rule
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.line(0.5 * inch, mid_y + 12, aw - 0.5 * inch, mid_y + 12)
        if self.description:
            c.setFont("Helvetica", 10)
            c.setFillColor(HexColor("#cccccc"))
            c.drawString(0.5 * inch, mid_y - 4, self.description)
        # Bottom tagline
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(LIGHT_GRAY)
        c.drawCentredString(aw / 2, 0.3 * inch,
                            '"The mission doesn\'t end at ETS. It evolves."')


# ── Build the premium sellable single PDF ────────────────────────────────────
def build_course_book():
    styles = make_styles()
    out_path = PDF_DIR / "MISSION-REBUILD-Course-Book.pdf"

    doc = BaseDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.75 * inch,
        title="MISSION REBUILD™ — Complete Course Book",
        author="MISSION REBUILD™",
        subject="12-Week Veteran Transition Course",
        keywords="veteran, transition, military, career, identity, finance",
    )

    cover_frame = Frame(0, 0, W, H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    inner_frame = Frame(doc.leftMargin, doc.bottomMargin,
                        W - doc.leftMargin - doc.rightMargin,
                        H - doc.topMargin - doc.bottomMargin)

    doc.addPageTemplates([
        PageTemplate("cover", frames=[cover_frame],
                     onPage=cover_page_cb),
        PageTemplate("inner", frames=[inner_frame],
                     onPage=inner_page_cb),
    ])

    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, H))          # fills the cover frame; cb does the art
    story.append(PageBreak())

    # Switch to inner template
    from reportlab.platypus import NextPageTemplate
    story.append(NextPageTemplate("inner"))
    story.append(PageBreak())

    # ── Copyright ────────────────────────────────────────────────────────────
    story += copyright_page(styles)

    # ── TOC ──────────────────────────────────────────────────────────────────
    story += toc_page(styles)

    # ── Content sections ─────────────────────────────────────────────────────
    for section in SECTIONS:
        # Section divider
        story.append(PageBreak())
        story.append(SectionDivider(section["label"]))
        story.append(PageBreak())

        for rel_path, display_name in section["files"]:
            md_path = BASE_DIR / rel_path
            if not md_path.exists():
                print(f"  ⚠  Skipping (not yet ready): {rel_path}")
                continue

            state.chapter = display_name
            state.part    = section["label"]

            md_text = md_path.read_text(encoding="utf-8")
            story += md_to_flowables(md_text, styles, display_name)
            story.append(Spacer(1, 0.3 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=LIGHT_GRAY))
            story.append(PageBreak())

    doc.build(story)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  ✓  {out_path.name}  ({size_mb:.1f} MB)")
    return out_path


# ── Build individual PDFs (lightweight) ──────────────────────────────────────
def build_individual(md_path: Path, pdf_path: Path, styles):
    from reportlab.platypus import SimpleDocTemplate

    md_text = md_path.read_text(encoding="utf-8")
    m = re.search(r'^#\s+(.+)', md_text, re.MULTILINE)
    title = m.group(1) if m else md_path.stem.replace("-", " ").title()

    def hf(c, doc):
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, H - 0.5 * inch, W, 0.5 * inch, fill=True, stroke=False)
        c.setFillColor(GOLD)
        c.rect(0, H - 0.52 * inch, W, 0.03 * inch, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(WHITE)
        c.drawString(0.55 * inch, H - 0.33 * inch, "MISSION REBUILD™")
        c.setFont("Helvetica", 8)
        c.setFillColor(GOLD_LIGHT)
        c.drawRightString(W - 0.5 * inch, H - 0.33 * inch, title[:72])
        c.setFillColor(GOLD)
        c.rect(0, 0.48 * inch, W, 0.02 * inch, fill=True, stroke=False)
        c.setFont("Helvetica", 8)
        c.setFillColor(GRAY)
        c.drawString(0.55 * inch, 0.28 * inch,
                     "© MISSION REBUILD™ | missionrebuild.com")
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawRightString(W - 0.5 * inch, 0.28 * inch, str(doc.page))
        c.restoreState()

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch,
                            title=f"MISSION REBUILD™ — {title}",
                            author="MISSION REBUILD™")

    story = md_to_flowables(md_text, styles)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    print(f"  ✓  {pdf_path.name}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    styles = make_styles()

    print("\n=== MISSION REBUILD™ — PDF Builder ===\n")

    all_md = sorted(BASE_DIR.rglob("*.md"))
    all_md = [f for f in all_md
              if "pdfs" not in f.parts and f.name != "build_pdfs.py"]

    print(f"Found {len(all_md)} Markdown files.\n")
    print("Building individual PDFs...")
    for md_path in all_md:
        rel = md_path.relative_to(BASE_DIR)
        out_dir = IND_DIR / rel.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / (md_path.stem + ".pdf")
        try:
            build_individual(md_path, pdf_path, styles)
        except Exception as e:
            print(f"  ✗  {md_path.name}: {e}")

    print("\nBuilding premium sellable course book...")
    try:
        build_course_book()
    except Exception as e:
        print(f"  ✗  Course book error: {e}")
        raise

    print("\n── Summary ──────────────────────────────────────────────")
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        print(f"  📄  {pdf.name}  ({pdf.stat().st_size//1024} KB)")
    ind_count = len(list(IND_DIR.rglob("*.pdf")))
    print(f"  📁  individual/  ({ind_count} PDFs)")
    print()


if __name__ == "__main__":
    main()
