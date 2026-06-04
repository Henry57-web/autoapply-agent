from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_resume_pdf(content: str) -> BytesIO:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Tailored Resume",
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle("ResumeBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=12)
    heading = ParagraphStyle("ResumeHeading", parent=body, fontName="Helvetica-Bold", fontSize=10.5, leading=13)
    name = ParagraphStyle("ResumeName", parent=body, fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=TA_CENTER)
    bullet = ParagraphStyle("ResumeBullet", parent=body, leftIndent=10, firstLineIndent=-8)
    story = []

    for index, raw_line in enumerate(content.splitlines()):
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
        elif index == 0:
            story.append(Paragraph(escape(line), name))
        elif line.startswith(("-", "•", "*")):
            story.append(Paragraph(f"- {escape(line.lstrip('-•* ').strip())}", bullet))
        elif _looks_like_heading(line):
            story.extend([Spacer(1, 4), Paragraph(escape(line), heading)])
        else:
            story.append(Paragraph(escape(line), body))

    document.build(story)
    buffer.seek(0)
    return buffer


def _looks_like_heading(line: str) -> bool:
    normalized = line.lower().strip()
    return normalized in {
        "education",
        "experience",
        "professional experience",
        "project experience",
        "projects",
        "skills",
        "technical skills",
        "honors & awards",
        "certifications",
        "summary",
        "professional summary",
    }
