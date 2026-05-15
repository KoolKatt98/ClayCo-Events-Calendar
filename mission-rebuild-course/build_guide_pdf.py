#!/usr/bin/env python3
"""
MISSION REBUILD — Course Guide PDF Builder
Produces a clean, short, sellable single PDF from course-guide.md
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus import NextPageTemplate

DARK      = HexColor("#0d1117")
NAVY      = HexColor("#1a2744")
GOLD      = HexColor("#c8a951")
GOLD_LITE = HexColor("#e8c97a")
MID       = HexColor("#2d3561")
GRAY      = HexColor("#444444")
LGRAY     = HexColor("#999999")
OFF_WHITE = HexColor("#f5f4ef")

W, H = letter
BASE = Path(__file__).parent
OUT  = BASE / "pdfs" / "MISSION-REBUILD-Course-Guide.pdf"


# ── Styles ────────────────────────────────────────────────────────────────────
def styles():
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=11,
                          leading=18, textColor=GRAY, spaceAfter=9)
    h1   = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=24,
                          leading=30, textColor=NAVY,
                          spaceBefore=24, spaceAfter=10)
    h2   = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=16,
                          leading=22, textColor=MID,
                          spaceBefore=20, spaceAfter=8)
    h3   = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=13,
                          leading=18, textColor=NAVY,
                          spaceBefore=14, spaceAfter=6)
    quote = ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=11,
                           leading=17, textColor=GOLD,
                           leftIndent=20, rightIndent=20,
                           spaceBefore=8, spaceAfter=8)
    label = ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=10,
                           leading=14, textColor=GOLD,
                           spaceBefore=12, spaceAfter=3)
    center = ParagraphStyle("center", fontName="Helvetica", fontSize=10,
                            leading=15, textColor=LGRAY,
                            alignment=TA_CENTER)
    return dict(body=body, h1=h1, h2=h2, h3=h3,
                quote=quote, label=label, center=center)


# ── Inline formatting ─────────────────────────────────────────────────────────
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(t):
    t = esc(t)
    t = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', t)
    t = re.sub(r'\*\*(.+?)\*\*',     r'<b>\1</b>',         t)
    t = re.sub(r'\*(.+?)\*',         r'<i>\1</i>',          t)
    return t


# ── Markdown parser ───────────────────────────────────────────────────────────
def parse(md, S):
    out = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]

        # HR
        if re.match(r'^[-*_]{3,}\s*$', raw):
            out.append(Spacer(1, 6))
            out.append(HRFlowable(width="100%", thickness=1, color=GOLD))
            out.append(Spacer(1, 6))
            i += 1; continue

        # Headings
        m = re.match(r'^(#{1,3})\s+(.*)', raw)
        if m:
            lvl  = len(m.group(1))
            text = inline(m.group(2).strip())
            if lvl == 1:
                out.append(Spacer(1, 6))
                out.append(Paragraph(text, S["h1"]))
                out.append(HRFlowable(width="100%", thickness=2, color=GOLD))
                out.append(Spacer(1, 6))
            elif lvl == 2:
                out.append(Paragraph(text, S["h2"]))
            else:
                out.append(Paragraph(text, S["h3"]))
            i += 1; continue

        # Blockquote — render as italic quote style
        if raw.startswith(">"):
            text = inline(raw.lstrip("> ").strip())
            out.append(Paragraph(f"<i>{text}</i>", S["quote"]))
            i += 1; continue

        # Bold label lines (standalone **text**)
        if re.match(r'^\*\*[^*].{0,60}\*\*\s*$', raw.strip()):
            text = inline(raw.strip())
            out.append(Paragraph(text, S["label"]))
            i += 1; continue

        # Bullets — convert to clean numbered feel without hyphens
        m = re.match(r'^\s*[-*+]\s+(.*)', raw)
        if m:
            text = inline(m.group(1))
            bullet_s = ParagraphStyle("bl", parent=S["body"],
                                      leftIndent=20, spaceAfter=4)
            out.append(Paragraph(f"• {text}", bullet_s))
            i += 1; continue

        # Numbered list
        m = re.match(r'^\s*(\d+)\.\s+(.*)', raw)
        if m:
            text = inline(m.group(2))
            num_s = ParagraphStyle("nl", parent=S["body"],
                                   leftIndent=24, spaceAfter=4)
            out.append(Paragraph(f"{m.group(1)}. {text}", num_s))
            i += 1; continue

        # Blank
        if raw.strip() == "":
            out.append(Spacer(1, 6))
            i += 1; continue

        # Normal paragraph
        text = inline(raw.strip())
        if text:
            out.append(Paragraph(text, S["body"]))
        i += 1

    return out


# ── Page callbacks ────────────────────────────────────────────────────────────
chapter_title = [""]

def cover_cb(c, doc):
    # Full dark background
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=True, stroke=False)

    # Gold top stripe
    c.setFillColor(GOLD)
    c.rect(0, H - 0.2 * inch, W, 0.2 * inch, fill=True, stroke=False)

    # Gold bottom stripe
    c.rect(0, 0, W, 0.2 * inch, fill=True, stroke=False)

    # Left gold rule
    c.setFillColor(GOLD)
    c.rect(0.6 * inch, 0.2 * inch, 0.05 * inch, H - 0.4 * inch,
           fill=True, stroke=False)

    # Main title
    c.setFont("Helvetica-Bold", 54)
    c.setFillColor(white)
    c.drawCentredString(W / 2, H * 0.60, "MISSION")
    c.drawCentredString(W / 2, H * 0.51, "REBUILD")

    # Gold rule under title
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(1.5 * inch, H * 0.485, W - 1.5 * inch, H * 0.485)

    # Subtitle
    c.setFont("Helvetica", 13)
    c.setFillColor(OFF_WHITE)
    c.drawCentredString(W / 2, H * 0.445, "From Army to Civilian")
    c.setFont("Helvetica", 11)
    c.setFillColor(GOLD_LITE)
    c.drawCentredString(W / 2, H * 0.415,
                        "Building Structure, Purpose, Identity and")
    c.drawCentredString(W / 2, H * 0.390,
                        "Financial Stability After Service")

    # Tagline
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(LGRAY)
    c.drawCentredString(W / 2, H * 0.33,
                        "A 12-Week Life Operating System for Military Veterans")

    # Bottom
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GOLD)
    c.drawCentredString(W / 2, 0.5 * inch, "missionrebuild.com")
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(LGRAY)
    c.drawCentredString(W / 2, 0.32 * inch,
                        "The mission does not end at ETS. It evolves.")


def inner_cb(c, doc):
    # Header
    c.setFillColor(NAVY)
    c.rect(0, H - 0.48 * inch, W, 0.48 * inch, fill=True, stroke=False)
    c.setFillColor(GOLD)
    c.rect(0, H - 0.50 * inch, W, 0.03 * inch, fill=True, stroke=False)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(white)
    c.drawString(0.6 * inch, H - 0.31 * inch, "MISSION REBUILD")
    c.setFont("Helvetica", 8)
    c.setFillColor(GOLD_LITE)
    title = chapter_title[0][:70] if chapter_title[0] else ""
    c.drawRightString(W - 0.5 * inch, H - 0.31 * inch, title)

    # Footer
    c.setFillColor(GOLD)
    c.rect(0, 0.46 * inch, W, 0.02 * inch, fill=True, stroke=False)
    c.setFont("Helvetica", 8)
    c.setFillColor(LGRAY)
    c.drawString(0.6 * inch, 0.27 * inch, "missionrebuild.com")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawRightString(W - 0.5 * inch, 0.27 * inch, str(doc.page - 1))


# ── Build ─────────────────────────────────────────────────────────────────────
def build():
    S = styles()
    md = (BASE / "course-guide.md").read_text(encoding="utf-8")

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="MISSION REBUILD — Course Guide",
        author="MISSION REBUILD",
        subject="12-Week Veteran Transition Course",
    )

    cover_frame = Frame(0, 0, W, H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    inner_frame = Frame(doc.leftMargin, doc.bottomMargin,
                        W - doc.leftMargin - doc.rightMargin,
                        H - doc.topMargin - doc.bottomMargin)

    doc.addPageTemplates([
        PageTemplate("cover", frames=[cover_frame], onPage=cover_cb),
        PageTemplate("inner", frames=[inner_frame], onPage=inner_cb),
    ])

    story = []

    # Cover page (full art, no text flowables needed)
    story.append(Spacer(1, H))
    story.append(NextPageTemplate("inner"))
    story.append(PageBreak())

    # Copyright / opener page
    story.append(Spacer(1, 2.2 * inch))
    c_s = ParagraphStyle("cp", fontName="Helvetica", fontSize=9.5,
                         leading=15, textColor=LGRAY, alignment=TA_CENTER,
                         spaceAfter=8)
    for line in [
        "MISSION REBUILD",
        "Course Guide",
        " ",
        "All rights reserved.",
        "No part of this material may be shared or reproduced",
        "without written permission from the creator.",
        " ",
        "This course is for educational purposes only.",
        "It is not financial, legal, or clinical advice.",
        " ",
        "Veterans in crisis: dial 988, press 1.",
        " ",
        "missionrebuild.com",
    ]:
        story.append(Paragraph(line or "&nbsp;", c_s))
    story.append(PageBreak())

    # Main content
    chapter_title[0] = "Course Guide"
    story += parse(md, S)

    doc.build(story)
    size = OUT.stat().st_size / 1024
    print(f"Done: {OUT.name}  ({size:.0f} KB)")


if __name__ == "__main__":
    build()
