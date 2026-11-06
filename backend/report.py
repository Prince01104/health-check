"""PDF report (English only: the default PDF fonts have no Devanagari)."""
import datetime as dt
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .content import describe
from .ml import pretty

TEAL = colors.HexColor("#0E6B66")
CHECK_TITLES = {"oral": "Oral Check", "skin": "Skin Check", "infection": "Infection Check", "nail": "Nail Check"}


def build_pdf(user_name: str, row: dict, probs: list, img_path, heat_path) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title="Health Check report")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=TEAL, fontSize=20, alignment=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=TEAL, fontSize=13)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10.5, leading=15)
    small = ParagraphStyle("s", parent=body, fontSize=8.5, textColor=colors.HexColor("#555555"))

    when = dt.datetime.fromtimestamp(row["created"]).strftime("%d %b %Y, %I:%M %p")
    info = describe(row["check_type"], row["label"])["en"]
    story = [Paragraph("Health Check - screening report", h1),
             Paragraph(f"<b>Name:</b> {user_name} &nbsp;&nbsp; <b>Date:</b> {when}", body),
             Paragraph(f"<b>Check:</b> {CHECK_TITLES.get(row['check_type'], row['check_type'])}", body),
             Spacer(1, 6)]

    pics = []
    for p in (img_path, heat_path):
        if p and p.exists():
            pics.append(Image(str(p), width=80 * mm, height=80 * mm, kind="proportional"))
    if pics:
        t = Table([pics], colWidths=[85 * mm] * len(pics))
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story += [t, Paragraph("Left: your photo. Right: areas the AI looked at (heatmap).", small), Spacer(1, 6)]

    status_txt = {"ok": "Result", "uncertain": "Not sure (low confidence)", "invalid": "Photo not suitable"}[row["status"]]
    story += [Paragraph("Result", h2),
              Paragraph(f"<b>{status_txt}:</b> possible {pretty(row['label'])} "
                        f"({row['confidence'] * 100:.0f}% confidence)", body),
              Paragraph(info["about"], body), Spacer(1, 4)]

    data = [["Possibility", "Probability"]] + [[pretty(p["label"]), f"{p['p'] * 100:.1f}%"] for p in probs[:5]]
    t = Table(data, colWidths=[80 * mm, 40 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
                           ("FONTSIZE", (0, 0), (-1, -1), 9.5)]))
    story += [t, Spacer(1, 8), Paragraph("General tips", h2)]
    story += [Paragraph(f"- {tip}", body) for tip in info["tips"]]
    story += [Spacer(1, 12),
              Paragraph("<b>Important:</b> This is an AI screening aid for learning and awareness. "
                        "It is NOT a medical diagnosis and does not replace a doctor. "
                        "Please consult a qualified doctor for any health concern.", small)]
    doc.build(story)
    return buf.getvalue()
