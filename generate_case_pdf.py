"""Generate the fence-encroachment case-file PDF used by the VertifyCase demo.

Run:  python generate_case_pdf.py
Out:  d:\\HackNex\\fence_encroachment_case.pdf
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = r"d:\HackNex\fence_encroachment_case.pdf"

styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "DocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=15,
    leading=19, spaceAfter=2, textColor=colors.HexColor("#1a1a1a"),
)
SUB = ParagraphStyle(
    "DocSub", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5,
    leading=11, alignment=1, textColor=colors.HexColor("#444444"),
)
CONF = ParagraphStyle(
    "Conf", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5,
    leading=11, alignment=1, textColor=colors.HexColor("#8b0000"), spaceBefore=4,
)
H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11,
    leading=14, spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#111111"),
)
BODY = ParagraphStyle(
    "Body", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5,
    leading=13, spaceAfter=6, alignment=4,
)
ITEM = ParagraphStyle(
    "Item", parent=BODY, leftIndent=16, bulletIndent=4, spaceAfter=4,
)
CELL = ParagraphStyle(
    "Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11,
)
CELLB = ParagraphStyle(
    "CellB", parent=CELL, fontName="Helvetica-Bold",
)
FOOT = ParagraphStyle(
    "Foot", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=8,
    leading=10, textColor=colors.HexColor("#555555"),
)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(
        doc.leftMargin,
        0.5 * inch,
        "Harrington & Cole LLP  -  File No. 2026-0915-OKO  -  Privileged & Confidential",
    )
    canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


story = []

story.append(Paragraph("HARRINGTON &amp; COLE LLP", SUB))
story.append(Paragraph("Attorneys at Law  ·  1200 Market Street, Suite 400, San Jose, CA 95113  ·  (408) 555-0142", SUB))
story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333")))
story.append(Paragraph("PRIVILEGED &amp; CONFIDENTIAL — ATTORNEY WORK PRODUCT", CONF))
story.append(Spacer(1, 8))
story.append(Paragraph("CLIENT INTAKE &amp; CASE ANALYSIS MEMORANDUM", TITLE))
story.append(Paragraph("Matter: Unauthorized boundary fence encroachment", SUB))
story.append(Spacer(1, 10))

meta = [
    ["Client:", "Margaret H. Okonkwo (fee owner)", "File No.:", "2026-0915-OKO"],
    ["Adjoining owner:", "Daniel Reyes (neighbor)", "Prepared by:", "Sarah J. Harrington, Esq."],
    ["Subject property:", "1428 Larkspur Lane, Sunnyvale, CA 94085 (APN 123-45-678)", "Date:", "September 15, 2026"],
    ["Jurisdiction:", "State of California, County of Santa Clara", "Venue:", "Superior Court of California, Santa Clara County"],
]
t = Table(meta, colWidths=[1.05 * inch, 3.15 * inch, 0.85 * inch, 2.0 * inch])
t.setStyle(TableStyle([
    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8.5),
    ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8.5),
    ("FONT", (1, 0), (1, -1), "Helvetica", 8.5),
    ("FONT", (3, 0), (3, -1), "Helvetica", 8.5),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f4")),
    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
]))
story.append(t)

story.append(Paragraph("1. Statement of Facts", H2))
story.append(Paragraph(
    "Our client, Margaret H. Okonkwo, is the fee owner of the residential parcel commonly known as "
    "1428 Larkspur Lane, Sunnyvale, Santa Clara County, California. The parcel is bounded on the east "
    "by the residential parcel owned by Daniel Reyes.", BODY))
story.append(Paragraph(
    "On August 22, 2026, Ms. Okonkwo discovered that Mr. Reyes had constructed a new six-foot wood "
    "privacy fence along the east side of his yard. A boundary survey commissioned by this office and "
    "completed by Golden Gate Land Surveying on September 2, 2026 (Survey No. GLS-26-4471) establishes "
    "that the new fence line runs approximately three feet (3.0 ft / 0.91 m) east of the true boundary, "
    "so that roughly three feet of the client's land is now enclosed within the neighbor's fenced area.",
    BODY))
story.append(Paragraph(
    "Mr. Reyes constructed the fence without the client's permission and without prior notice. On "
    "September 3, 2026 the client verbally asked Mr. Reyes to relocate the fence to the true boundary "
    "line; he refused, stating that he \"measured from the corner pin and built where it made sense.\" "
    "No written agreement, license, or easement between the parties authorizes the encroachment.",
    BODY))
story.append(Paragraph(
    "<b>Client objectives:</b> (1) have the encroaching fence removed or relocated to the true boundary "
    "line at the neighbor's expense; (2) obtain written confirmation of the boundary; and (3) understand "
    "the legal options and the time limits for taking legal action in this jurisdiction.", BODY))

story.append(Paragraph("2. Jurisdiction and Applicable Law", H2))
story.append(Paragraph(
    "This dispute concerns real property located in California and is therefore governed by California "
    "law, with venue in the Superior Court of California, County of Santa Clara. The following "
    "authorities are potentially relevant:", BODY))
for txt in [
    "Common-law trespass to real property and nuisance — the neighbor's placement of a permanent "
    "structure across the boundary is an actionable invasion of the client's possessory interest.",
    "Code of Civil Procedure section 338 — three-year statute of limitations for trespass to real "
    "property, nuisance, and property damage.",
    "Code of Civil Procedure section 318 — an action for recovery of real property or the recovery of "
    "the possession thereof may be maintained only if the plaintiff was seized or possessed of the "
    "property within five years before commencement of the action.",
    "Code of Civil Procedure section 325 — adverse possession requires continuous occupation and claim "
    "for five years under a substantial enclosure, together with timely payment of all state, county, "
    "or municipal taxes levied on the land during that period.",
    "Applicable city fence ordinance — local zoning codes regulate fence height, setback, and permit "
    "requirements; unpermitted construction may be cited by the city.",
]:
    story.append(Paragraph(txt, ITEM, bulletText="\u2022"))

story.append(Paragraph("3. Legal Options to Get the Fence Moved", H2))
for txt in [
    "<b>Confirm the boundary (completed).</b> The September 2, 2026 survey (GLS-26-4471) fixes the true "
    "line and locates the fence approximately three feet inside the client's parcel. Provide the survey "
    "exhibit to the neighbor.",
    "<b>Written demand letter from counsel.</b> Demand removal or relocation of the fence within 30 "
    "days, attaching the survey. A demand letter is usually the fastest and cheapest resolution path "
    "and preserves the record if suit becomes necessary.",
    "<b>Negotiated written boundary agreement.</b> If the neighbor agrees, document the relocation or a "
    "defined license in writing before any further work is done.",
    "<b>Mediation.</b> If direct negotiation fails, voluntary mediation with a certified mediator can "
    "resolve the dispute faster and more cheaply than litigation.",
    "<b>Civil action for trespass and injunctive relief.</b> If the neighbor refuses, file suit in the "
    "Santa Clara County Superior Court seeking (a) a mandatory injunction compelling removal of the "
    "encroaching fence, (b) trespass damages, and (c) costs. Injunctive relief is the primary remedy "
    "where a permanent structure crosses a boundary line.",
    "<b>Ejectment or quiet title.</b> If the boundary itself is disputed or the neighbor claims rights "
    "over the strip, an action to recover possession of the real property (ejectment) and/or to quiet "
    "title may be required.",
    "<b>Code enforcement referral.</b> Ask the city to inspect for fence height and permit violations; "
    "an enforcement order adds leverage for voluntary compliance.",
]:
    story.append(Paragraph(txt, ITEM, bulletText="\u2022"))

story.append(Paragraph("4. Time Limits for Taking Legal Action in This Jurisdiction", H2))
story.append(Paragraph(
    "The following deadlines apply to this matter under California law. These are the controlling time "
    "limits for taking legal action:", BODY))

rows = [
    [Paragraph("<b>Claim / action</b>", CELLB), Paragraph("<b>Time limit</b>", CELLB),
     Paragraph("<b>Authority</b>", CELLB)],
    [Paragraph("Trespass to real property, nuisance, and property damage "
               "(injunction to remove the fence plus damages)", CELL),
     Paragraph("3 years from accrual under Cal. Code Civ. Proc. section 338 (the encroachment was "
               "completed and discovered in August-September 2026, so approximately "
               "<b>September 2029</b>)", CELL),
     Paragraph("Cal. Code Civ. Proc. section 338", CELL)],
    [Paragraph("Recovery of real property or recovery of possession thereof (ejectment) - plaintiff "
               "must have been seized or possessed within 5 years before suit", CELL),
     Paragraph("5 years before commencement of the action under Cal. Code Civ. Proc. section 318; the "
               "client's recorded title and present possession satisfy this requirement", CELL),
     Paragraph("Cal. Code Civ. Proc. section 318", CELL)],
    [Paragraph("Adverse possession exposure - neighbor's claim to the 3-foot strip via the encroaching "
               "fence", CELL),
     Paragraph("5 years of continuous occupation under a substantial enclosure <b>and</b> timely payment "
               "of all property taxes for those 5 years, per Cal. Code Civ. Proc. section 325(b) "
               "(earliest about 2031)", CELL),
     Paragraph("Cal. Code Civ. Proc. section 325(b)", CELL)],
]
tbl = Table(rows, colWidths=[2.9 * inch, 3.0 * inch, 1.15 * inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]))
story.append(tbl)
story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Recommended filing schedule.</b> Demand letter within 14 days of this memorandum; neighbor's "
    "response deadline of 30 days; mediation if unresolved after 45 days; complaint filed no later than "
    "12 months from the date of this memorandum (September 2026), and in no event later than three "
    "years after accrual (September 2029) under Cal. Code Civ. Proc. section 338, to preserve all "
    "claims. Each day the fence remains may "
    "constitute a continuing trespass, but the client should not rely on continuing-violation theories "
    "to extend the three-year damages window under section 338.", BODY))

story.append(Paragraph("5. Risk Assessment and Conclusion", H2))
story.append(Paragraph(
    "Delay increases risk: if the fence remains in place for years, the neighbor may assert adverse "
    "possession or boundary-by-acquiescence theories, and witness memories fade. The neighbor may also "
    "contend that the fence follows an older fence line; the 2026 survey rebuts that contention. "
    "Mandatory-injunction matters of this type in Santa Clara County typically resolve within 12 to 18 "
    "months of filing.", BODY))
story.append(Paragraph(
    "<b>Conclusion:</b> The client has a strong, survey-supported trespass claim and clean injunctive "
    "remedy. This office recommends an immediate demand letter, mediation if the neighbor does not "
    "comply, and filing suit within 12 months - well inside every statutory deadline identified above.",
    BODY))
story.append(Spacer(1, 8))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999")))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "This memorandum is attorney work product prepared for the internal file of Harrington &amp; Cole "
    "LLP and reflects legal analysis for this matter only. It is not a substitute for advice tailored "
    "to circumstances that may arise later. Statutory references are to the California Code of Civil "
    "Procedure as in effect in 2026; confirm current text before relying on any deadline.", FOOT))

doc = SimpleDocTemplate(
    OUT, pagesize=LETTER, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
    topMargin=0.7 * inch, bottomMargin=0.8 * inch,
    title="Boundary Fence Encroachment - Case File 2026-0915-OKO",
    author="Harrington & Cole LLP",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"WROTE {OUT}")



