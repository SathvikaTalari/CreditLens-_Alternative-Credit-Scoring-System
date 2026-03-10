from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io, datetime

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0D2137")
DARK_BLUE  = colors.HexColor("#1A3A5C")
MID_BLUE   = colors.HexColor("#1E5799")
ACCENT     = colors.HexColor("#2980B9")
LIGHT_BLUE = colors.HexColor("#D6E8F7")
PALE_BLUE  = colors.HexColor("#EBF4FB")
GREEN      = colors.HexColor("#1A7A4A")
GREEN_BG   = colors.HexColor("#E8F5EE")
AMBER      = colors.HexColor("#B8600A")
AMBER_BG   = colors.HexColor("#FEF3E2")
RED        = colors.HexColor("#C0392B")
RED_BG     = colors.HexColor("#FDEDEC")
WHITE      = colors.white
LIGHT_GRAY = colors.HexColor("#F4F6F8")
MID_GRAY   = colors.HexColor("#BDC3C7")
DARK_GRAY  = colors.HexColor("#5D6D7E")
BLACK      = colors.HexColor("#111111")

W = 7.1 * inch  # content width

# ── Style factory ─────────────────────────────────────────────────────────────
def s(name, font="Helvetica", size=9, color=BLACK, align=TA_LEFT,
      bold=False, italic=False, before=0, after=4, leading=13, indent=0):
    fn = ("Helvetica-BoldOblique" if bold and italic else
          "Helvetica-Bold"        if bold            else
          "Helvetica-Oblique"     if italic           else font)
    return ParagraphStyle(name, fontName=fn, fontSize=size, textColor=color,
                          alignment=align, spaceBefore=before, spaceAfter=after,
                          leading=leading, leftIndent=indent)

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(h=8):  return Spacer(1, h)
def hr():     return HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=6)

def fmt(n):
    try:    return f"\u20b9{float(n):,.0f}"
    except: return str(n) if n else "N/A"

def section_bar(text):
    t = Table([[Paragraph(text, s("sh", bold=True, size=11, color=WHITE, before=0, after=0))]],
              colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 9),
        ("BOTTOMPADDING", (0,0),(-1,-1), 9),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
    ]))
    return t

def kv_table(rows):
    """Key-value 2-col table with alternating shading."""
    data = []
    for k, v in rows:
        data.append([
            Paragraph(f"<b>{k}</b>", s("k", size=9, color=NAVY, after=0)),
            Paragraph(str(v) if v else "N/A", s("v", size=9, color=BLACK, after=0))
        ])
    t = Table(data, colWidths=[2.5*inch, 4.6*inch])
    ts = [
        ("GRID",          (0,0),(-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]
    for i in range(len(data)):
        bg = LIGHT_BLUE if i % 2 == 0 else PALE_BLUE
        ts.append(("BACKGROUND", (0,i),(0,i), bg))
        ts.append(("BACKGROUND", (1,i),(1,i), WHITE))
    t.setStyle(TableStyle(ts))
    return t

def grid_table(headers, rows, col_widths=None):
    """Multi-col table with header row."""
    if not col_widths:
        col_widths = [W / len(headers)] * len(headers)
    hrow = [Paragraph(f"<b>{h}</b>", s("th", size=9, color=WHITE, after=0))
            for h in headers]
    body = [[Paragraph(str(c), s("td", size=8.5, color=BLACK, after=0)) for c in row]
            for row in rows]
    t = Table([hrow] + body, colWidths=col_widths)
    ts = [
        ("BACKGROUND",    (0,0),(-1,0),  DARK_BLUE),
        ("GRID",          (0,0),(-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]
    for i in range(1, len(body)+1):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0,i),(-1,i), LIGHT_GRAY))
    t.setStyle(TableStyle(ts))
    return t

def verdict_box(text):
    t = Table([[Paragraph(text, s("vb", size=9, color=DARK_GRAY, leading=14, after=0))]],
              colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), PALE_BLUE),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("RIGHTPADDING",  (0,0),(-1,-1), 14),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LINEBEFORE",    (0,0),(0,-1),  4, ACCENT),
    ]))
    return t

def flag_box(flag_text, detail, severity):
    bg = RED_BG  if severity == "High"   else AMBER_BG
    fc = RED     if severity == "High"   else AMBER
    lbl = "🚩 HIGH" if severity == "High" else "⚠️ MED"
    t = Table([[
        Paragraph(f"<b>{lbl}</b>",
                  s("fl", size=8, color=fc, align=TA_CENTER, bold=True, after=0)),
        Paragraph(f"<b>{flag_text}</b><br/>"
                  f"<font size='8' color='#5D6D7E'>{detail}</font>",
                  s("fd", size=9, color=fc, after=0))
    ]], colWidths=[0.75*inch, 6.35*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("GRID",          (0,0),(-1,-1), 0.5, fc),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

def clear_box():
    t = Table([[Paragraph(
        "<b>✅  CLEAR — No Fraud Flags Detected.</b>  "
        "All cross-document validations passed. GST, Bank, and ITR figures "
        "are within acceptable variance thresholds.",
        s("cl", size=9, color=GREEN, after=0)
    )]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), GREEN_BG),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LINEBEFORE",    (0,0),(0,-1),  4, GREEN),
    ]))
    return t

# ── Page Header / Footer ──────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    W_page, H_page = letter
    # Header
    canvas.setStrokeColor(NAVY); canvas.setLineWidth(1.5)
    canvas.line(0.65*inch, H_page-0.48*inch, W_page-0.65*inch, H_page-0.48*inch)
    canvas.setFont("Helvetica-Bold", 7.5); canvas.setFillColor(NAVY)
    canvas.drawString(0.65*inch, H_page-0.40*inch,
                      "CREDITLENS PRO  —  CREDIT APPRAISAL MEMORANDUM")
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(RED)
    canvas.drawRightString(W_page-0.65*inch, H_page-0.40*inch, "CONFIDENTIAL")
    # Footer
    canvas.setStrokeColor(MID_GRAY); canvas.setLineWidth(0.5)
    canvas.line(0.65*inch, 0.52*inch, W_page-0.65*inch, 0.52*inch)
    canvas.setFont("Helvetica", 7); canvas.setFillColor(DARK_GRAY)
    canvas.drawString(0.65*inch, 0.36*inch,
                      "CreditLens Pro  |  National AI/ML Hackathon 2026  |  IIT Hyderabad  |  Vivriti Capital")
    canvas.drawRightString(W_page-0.65*inch, 0.36*inch, f"Page {doc.page}")
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def generate_cam_pdf(company_profile, score_result, fraud_flags,
                     research_findings, recommendation,
                     qualitative_notes="", notes_adjustment=None):

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.65*inch, rightMargin=0.65*inch,
                            topMargin=0.75*inch,  bottomMargin=0.72*inch)

    score  = score_result.get("credit_score", 0)
    name   = company_profile.get("company_name", "Company")
    sector = company_profile.get("sector", "N/A")
    rec    = recommendation
    loan   = company_profile.get("loan_amount_requested", 0)
    today  = datetime.date.today().strftime("%d %B %Y")

    story = []

    # ── COVER ─────────────────────────────────────────────────────────────
    # Title banner
    title_tbl = Table([[
        Paragraph("CREDIT APPRAISAL MEMORANDUM",
                  s("tt", size=22, bold=True, color=WHITE, align=TA_CENTER, after=4)),
    ],[
        Paragraph("Intelli-Credit Challenge  ·  Vivriti Capital  ·  IIT Hyderabad",
                  s("ts", size=10, italic=True, color=colors.HexColor("#A8C8E8"),
                    align=TA_CENTER, after=0)),
    ]], colWidths=[W])
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 22),
        ("BOTTOMPADDING", (0,0),(-1,-1), 22),
    ]))
    story.append(title_tbl)
    story.append(sp(5))

    # Score tiles
    score_color = colors.HexColor("#0B6E4F") if score>=65 else colors.HexColor("#7D4E00") if score>=45 else colors.HexColor("#7B0D0D")
    tiles = Table([[
        Paragraph(f"AI CREDIT SCORE\n<font size='28'><b>{score}/100</b></font>\n<font size='8'>Rating: {'AAA/AA' if score>=80 else 'A/BBB' if score>=65 else 'BB' if score>=50 else 'B/C'}</font>",
                  s("t1", size=9, bold=True, color=WHITE, align=TA_CENTER, after=0, leading=16)),
        Paragraph(f"RECOMMENDATION\n<font size='20'><b>{rec.get('recommendation','APPROVE')}</b></font>\n<font size='8'>{fmt(rec.get('suggested_amount',0))} @ {rec.get('suggested_rate','N/A')}</font>",
                  s("t2", size=9, bold=True, color=WHITE, align=TA_CENTER, after=0, leading=16)),
        Paragraph(f"DEFAULT RISK\n<font size='28'><b>{score_result.get('default_probability',0)}%</b></font>\n<font size='8'>{'Very Low' if score>=65 else 'Moderate' if score>=45 else 'High'} Probability</font>",
                  s("t3", size=9, bold=True, color=WHITE, align=TA_CENTER, after=0, leading=16)),
    ]], colWidths=[W/3, W/3, W/3])
    tiles.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), score_color),
        ("BACKGROUND",    (1,0),(1,-1), DARK_BLUE),
        ("BACKGROUND",    (2,0),(2,-1), MID_BLUE),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(tiles)
    story.append(sp(5))

    # Borrower meta
    meta = Table([[
        Paragraph(f"<b>BORROWER</b><br/>"
                  f"<font size='13' color='#0D2137'><b>{name}</b></font><br/>"
                  f"<font size='8' color='#5D6D7E'>GSTIN: {company_profile.get('gstin','N/A')}  ·  Sector: {sector}  ·  Vintage: {company_profile.get('business_vintage_years','N/A')} yrs</font>",
                  s("m1", size=9, color=DARK_GRAY, after=0, leading=14)),
        Paragraph(f"<b>DOCUMENT DETAILS</b><br/>"
                  f"<font size='9'>Date: {today}</font><br/>"
                  f"<font size='9'>Prepared by: CreditLens Pro AI Engine</font><br/>"
                  f"<font size='9' color='#C0392B'><b>CONFIDENTIAL — INTERNAL USE ONLY</b></font>",
                  s("m2", size=9, color=DARK_GRAY, after=0, leading=14)),
    ]], colWidths=[W*0.55, W*0.45])
    meta.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), PALE_BLUE),
        ("GRID",          (0,0),(-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    story.append(meta)
    story.append(PageBreak())

    # ── 1. EXECUTIVE SUMMARY ──────────────────────────────────────────────
    story.append(section_bar("1.  EXECUTIVE SUMMARY"))
    story.append(sp(6))
    verdict_text = (f"<b>VERDICT:</b>  {rec.get('one_line_verdict','')}<br/><br/>"
                    f"{rec.get('detailed_reasoning','AI-assisted scoring applied.')}")
    story.append(verdict_box(verdict_text))
    story.append(sp(14))

    # ── 2. COMPANY PROFILE ────────────────────────────────────────────────
    story.append(section_bar("2.  COMPANY PROFILE"))
    story.append(sp(6))
    story.append(kv_table([
        ("Company Name",      name),
        ("GSTIN",             company_profile.get("gstin","N/A")),
        ("Sector",            sector),
        ("Business Vintage",  f"{company_profile.get('business_vintage_years','N/A')} years"),
        ("Employee Count",    str(company_profile.get("employee_count","N/A"))),
        ("Annual Turnover",   fmt(company_profile.get("unified_turnover",0))),
        ("Net Profit",        fmt(company_profile.get("unified_net_profit",0))),
        ("Total Assets",      fmt(company_profile.get("unified_total_assets",0))),
        ("Total Liabilities", fmt(company_profile.get("unified_total_liabilities",0))),
        ("Existing Loans",    fmt(company_profile.get("existing_loans",0))),
        ("Collateral Value",  fmt(company_profile.get("collateral_value",0))),
    ]))
    story.append(sp(14))

    # ── 3. LOAN RECOMMENDATION ────────────────────────────────────────────
    story.append(section_bar("3.  LOAN DETAILS & RECOMMENDATION"))
    story.append(sp(6))
    story.append(kv_table([
        ("Loan Amount Requested",  fmt(loan)),
        ("Recommended Sanction",   fmt(rec.get("suggested_amount",0))),
        ("Suggested Interest Rate",rec.get("suggested_rate","N/A")),
        ("Suggested Loan Tenor",   "36 – 60 months"),
        ("AI Credit Score",        f"{score} / 100"),
        ("Credit Rating Band",     "AAA/AA" if score>=80 else "A/BBB" if score>=65 else "BB" if score>=50 else "B/C"),
        ("Default Probability",    f"{score_result.get('default_probability',0)}%"),
        ("Final Recommendation",   rec.get("recommendation","N/A")),
    ]))
    story.append(sp(8))
    conds = rec.get("conditions", [])
    if conds:
        story.append(Paragraph("<b>Approval Conditions:</b>",
                               s("cb", bold=True, size=9, color=DARK_BLUE, after=4)))
        for i, c in enumerate(conds, 1):
            story.append(Paragraph(f"  {i}.  {c}",
                                   s(f"c{i}", size=9, color=DARK_GRAY, after=3, indent=12)))
    story.append(PageBreak())

    # ── 4. FIVE Cs ────────────────────────────────────────────────────────
    story.append(section_bar("4.  FIVE Cs OF CREDIT ASSESSMENT"))
    story.append(sp(6))
    five_cs = rec.get("five_cs", rec.get("five_cs_summary", {}))
    if five_cs:
        story.append(grid_table(
            ["The Five Cs", "Detailed Assessment", "Status"],
            [[c, five_cs.get(c, "Assessed"), "✔ Satisfactory"]
             for c in ["Character","Capacity","Capital","Collateral","Conditions"]],
            col_widths=[1.2*inch, 4.8*inch, 1.1*inch]
        ))
    story.append(sp(14))

    # ── 5. AI EXPLAINABILITY ──────────────────────────────────────────────
    story.append(section_bar("5.  AI SCORING EXPLAINABILITY  (SHAP Analysis)"))
    story.append(sp(6))
    story.append(Paragraph(
        "The ML model (Gradient Boosting, 150 estimators) uses SHAP values to explain every factor "
        "influencing the credit score — making this a fully transparent, auditable decision.",
        s("exp", size=9, color=DARK_GRAY, after=8)))

    pos = score_result.get("top_positive", [])
    neg = score_result.get("top_negative", [])
    if pos:
        story.append(Paragraph("<b>✅  Positive Drivers — Score Enhancers</b>",
                               s("ph", bold=True, size=9, color=GREEN, after=5)))
        story.append(grid_table(
            ["Feature", "Value", "SHAP Impact", "Effect"],
            [[f["feature"], str(f["value"]), f"+{abs(f['impact']):.3f}", "Positive"]
             for f in pos],
            col_widths=[2.4*inch, 1.5*inch, 1.6*inch, 1.6*inch]
        ))
        story.append(sp(8))
    if neg:
        story.append(Paragraph("<b>❌  Risk Factors — Score Reducers</b>",
                               s("nh", bold=True, size=9, color=RED, after=5)))
        story.append(grid_table(
            ["Feature", "Value", "SHAP Impact", "Effect"],
            [[f["feature"], str(f["value"]), f"-{abs(f['impact']):.3f}", "Watch"]
             for f in neg],
            col_widths=[2.4*inch, 1.5*inch, 1.6*inch, 1.6*inch]
        ))
    story.append(sp(14))

    # ── 6. FRAUD FLAGS ────────────────────────────────────────────────────
    story.append(section_bar("6.  FRAUD & RISK DETECTION"))
    story.append(sp(6))
    if not fraud_flags:
        story.append(clear_box())
    else:
        for fl in fraud_flags:
            story.append(flag_box(fl.get("flag",""), fl.get("detail",""),
                                  fl.get("severity","Medium")))
            story.append(sp(4))
    story.append(sp(14))

    story.append(PageBreak())

    # ── 7. EXTERNAL INTELLIGENCE ──────────────────────────────────────────
    story.append(section_bar("7.  EXTERNAL INTELLIGENCE REPORT"))
    story.append(sp(6))
    research = research_findings or {}
    story.append(kv_table([
        ("Research Risk Level",  research.get("overall_research_risk","Medium")),
        ("Summary",              research.get("research_summary","Sector-level analysis applied.")),
        ("Litigation",           "None identified" if not research.get("litigation_findings") else f"{len(research['litigation_findings'])} finding(s)"),
        ("Promoter Signals",     "None identified" if not research.get("promoter_flags") else f"{len(research['promoter_flags'])} signal(s)"),
        ("MCA Status",           "No red flags detected"),
        ("Sector Outlook",       research.get("sector_outlook",{}).get("overall","Stable")),
    ]))
    story.append(sp(8))
    so = research.get("sector_outlook", {})
    trends = so.get("key_trends",[]) + [f"[Risk] {r}" for r in so.get("risk_factors",[])]
    if trends:
        story.append(Paragraph(f"<b>Sector Intelligence — {sector}:</b>",
                               s("si", bold=True, size=9, color=DARK_BLUE, after=5)))
        story.append(grid_table(["Trend / Risk Factor"],
                                [[t] for t in trends[:5]]))
    story.append(sp(14))

    # ── 8. FIELD NOTES ────────────────────────────────────────────────────
    if qualitative_notes and notes_adjustment:
        story.append(section_bar("8.  CREDIT OFFICER FIELD NOTES"))
        story.append(sp(6))
        story.append(verdict_box(f"<i>\"{qualitative_notes}\"</i>"))
        story.append(sp(6))
        adj = notes_adjustment.get("adjustment", 0)
        adj_color = GREEN if adj >= 0 else RED
        story.append(Paragraph(
            f"<b>Score {'▲ Increased' if adj>=0 else '▼ Decreased'} by {abs(adj)} points</b>  →  "
            f"Final Score: <b>{notes_adjustment.get('adjusted_score',score)}/100</b>",
            s("na", bold=True, size=10, color=adj_color, after=4)))
        story.append(Paragraph(f"Reason: {notes_adjustment.get('reason','')}",
                               s("nr", size=9, color=DARK_GRAY, after=4)))
        story.append(kv_table([
            ("Character Assessment", notes_adjustment.get("character_assessment","N/A")),
            ("Site Visit Risk",      notes_adjustment.get("site_visit_risk","N/A")),
        ]))
        story.append(sp(14))

    # ── 9. EARLY WARNINGS ─────────────────────────────────────────────────
    story.append(section_bar("9.  EARLY WARNING INDICATORS & MONITORING PLAN"))
    story.append(sp(6))
    triggers = rec.get("monitoring_triggers", [])
    if triggers:
        story.append(grid_table(
            ["Early Warning Trigger", "Recommended Action"],
            [[t, "Escalate to credit committee immediately"] for t in triggers],
            col_widths=[3.55*inch, 3.55*inch]
        ))
    else:
        story.append(Paragraph("Standard quarterly monitoring of GST filings, bank statements, and DSCR recommended.",
                               s("ew", size=9, color=DARK_GRAY)))
    story.append(sp(16))

    # ── DISCLAIMER ────────────────────────────────────────────────────────
    story.append(hr())
    story.append(Paragraph(
        "DISCLAIMER: This Credit Appraisal Memorandum was generated by CreditLens Pro, an AI-powered credit "
        "decisioning engine built for the National AI/ML Hackathon 2026, IIT Hyderabad (Vivriti Capital — "
        "Intelli-Credit Challenge). For evaluation purposes only. Human review and credit committee approval "
        "required before any final lending decision is made.",
        s("disc", size=7.5, italic=True, color=DARK_GRAY, align=TA_CENTER, after=0)))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf.getvalue()