from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

styles = getSampleStyleSheet()
title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=14, spaceAfter=4)
label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=10, leading=14)

doc = SimpleDocTemplate(
    "sample_complaint_metformin_api.pdf",
    pagesize=A4,
    topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
)

story = [
    Paragraph("QUALITY COMPLAINT NOTIFICATION", title_style),
    Paragraph("Reference: QC-CMP-2026-0714 &nbsp;&nbsp;|&nbsp;&nbsp; Date: 12-Jul-2026", label_style),
    Spacer(1, 10),
    Paragraph(
        "To: Quality Assurance Department, Meethu Pharma API Division<br/>"
        "From: Sourcing &amp; QA, Vantura Life Sciences Pvt. Ltd.<br/>"
        "Subject: Customer complaint regarding Metformin Hydrochloride API batch received under PO# VLS-8843",
        label_style,
    ),
    Spacer(1, 14),
    Paragraph(
        "This is to formally notify a quality complaint against the Metformin Hydrochloride API "
        "(IP/BP grade) supplied under batch/lot number MFH260712A. Upon receipt at our formulation "
        "facility and subsequent incoming QC testing, the material exhibited off-white to pale yellow "
        "discoloration inconsistent with the reference standard, along with a slightly elevated moisture "
        "content on Karl Fischer titration.",
        label_style,
    ),
    Spacer(1, 10),
]

table_data = [
    ["Field", "Details"],
    ["Product Name", "Metformin Hydrochloride API"],
    ["Product Grade", "IP/BP"],
    ["Batch/Lot Number", "MFH260712A"],
    ["Manufacturing Date", "2026-01-18"],
    ["Expiry Date", "2028-01-17"],
    ["Quantity Affected", "50 kg (2 HDPE drums)"],
    ["Complaint Type", "Discoloration / Moisture Deviation"],
    ["Complaint Date", "2026-07-12"],
    ["Reported By", "Vantura Life Sciences Pvt. Ltd. — QA Dept."],
]

t = Table(table_data, colWidths=[150, 320])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(Spacer(1, 14))
story.append(Paragraph(
    "We request root cause investigation, CAPA, and confirmation of retained sample analysis for this "
    "batch. Please advise on replacement material timelines given the discoloration and moisture "
    "deviation observed, as this batch is currently on hold at our incoming stores.",
    label_style,
))
story.append(Spacer(1, 14))
story.append(Paragraph("Regards,<br/>QA Manager, Vantura Life Sciences Pvt. Ltd.", label_style))

doc.build(story)
print("done")
