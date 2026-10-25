"""Generate Corrected Technical Blueprint & Architectural Footprint PDF for PPL.

INSA Cybersecurity Summer Camp 2026 - Final Technical Deliverable.
Built using ReportLab Platypus with exact verbatim code excerpts, full 30-test pytest matrix,
native Ethiopic font integration in code and tables, and grounded security assertions.
"""
import os
import sys
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ----------------- Font Registration -----------------
FONTS_DIR = r"C:\Windows\Fonts"
EBRIMA_PATH = os.path.join(FONTS_DIR, "ebrima.ttf")
EBRIMA_BOLD_PATH = os.path.join(FONTS_DIR, "ebrimabd.ttf")

HAS_ETHIOPIC_FONT = False
if os.path.exists(EBRIMA_PATH) and os.path.exists(EBRIMA_BOLD_PATH):
    try:
        pdfmetrics.registerFont(TTFont("Ebrima", EBRIMA_PATH))
        pdfmetrics.registerFont(TTFont("Ebrima-Bold", EBRIMA_BOLD_PATH))
        HAS_ETHIOPIC_FONT = True
    except Exception as e:
        print(f"Warning: Failed to register Ebrima: {e}")

FONT_STD = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ETH = "Ebrima" if HAS_ETHIOPIC_FONT else "Helvetica"
FONT_ETH_BOLD = "Ebrima-Bold" if HAS_ETHIOPIC_FONT else "Helvetica-Bold"

# ----------------- Color Palette -----------------
COLOR_PRIMARY_DARK = colors.HexColor("#0F172A")    # Slate 900
COLOR_TEAL_DARK = colors.HexColor("#0F766E")       # Teal 700
COLOR_TEAL_MID = colors.HexColor("#0D9488")        # Teal 600
COLOR_TEAL_LIGHT = colors.HexColor("#CCFBF1")      # Teal 100
COLOR_TEXT_MAIN = colors.HexColor("#1E293B")       # Slate 800
COLOR_TEXT_MUTED = colors.HexColor("#64748B")      # Slate 500
COLOR_BG_CARD = colors.HexColor("#F8FAFC")         # Slate 50
COLOR_BG_ALT = colors.HexColor("#F1F5F9")          # Slate 100
COLOR_BORDER = colors.HexColor("#CBD5E1")          # Slate 300
COLOR_BORDER_LIGHT = colors.HexColor("#E2E8F0")    # Slate 200
COLOR_RED = colors.HexColor("#BE123C")             # Rose 700
COLOR_RED_BG = colors.HexColor("#FFE4E6")          # Rose 100
COLOR_AMBER = colors.HexColor("#B45309")           # Amber 700
COLOR_AMBER_BG = colors.HexColor("#FEF3C7")        # Amber 100
COLOR_GREEN = colors.HexColor("#047857")           # Emerald 700
COLOR_GREEN_BG = colors.HexColor("#D1FAE5")        # Emerald 100
COLOR_CODE_BG = colors.HexColor("#0F172A")         # Dark slate
COLOR_CODE_TEXT = colors.HexColor("#F8FAFC")       # Slate 50


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print running headers and footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            return

        self.saveState()

        # Running Header
        self.setFont(FONT_BOLD, 7.5)
        self.setFillColor(COLOR_TEAL_DARK)
        self.drawString(46, 752, "PAYMENT PROOF & SALES LEDGER (PPL)")
        self.setFont(FONT_STD, 7.5)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(215, 752, "|   Technical Blueprint & System Architecture")

        self.setStrokeColor(COLOR_BORDER_LIGHT)
        self.setLineWidth(0.75)
        self.line(46, 744, 566, 744)

        # Running Footer
        self.line(46, 44, 566, 44)
        self.setFont(FONT_BOLD, 7.5)
        self.setFillColor(COLOR_TEAL_DARK)
        self.drawString(46, 32, "INSA CYBERSECURITY SUMMER CAMP 2026")
        self.setFont(FONT_STD, 7.5)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(225, 32, "Final Technical Submission - Amanuel Mintesenot & Nahom Mekuria")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(566, 32, page_str)

        self.restoreState()


def esc(text):
    """Safely escape text for ReportLab Paragraphs."""
    return escape(str(text))


def make_styles():
    """Build document typographic hierarchy."""
    base = getSampleStyleSheet()

    styles = {
        "CoverTag": ParagraphStyle(
            "CoverTag",
            fontName=FONT_BOLD,
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEAL_DARK,
            alignment=0,
            spaceAfter=8,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            fontName=FONT_BOLD,
            fontSize=23,
            leading=27,
            textColor=COLOR_PRIMARY_DARK,
            alignment=0,
            spaceAfter=8,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName=FONT_STD,
            fontSize=12.5,
            leading=16.5,
            textColor=COLOR_TEAL_MID,
            alignment=0,
            spaceAfter=14,
        ),
        "CoverDesc": ParagraphStyle(
            "CoverDesc",
            fontName=FONT_STD,
            fontSize=9.2,
            leading=14,
            textColor=COLOR_TEXT_MAIN,
            alignment=0,
            spaceAfter=14,
        ),
        "H1": ParagraphStyle(
            "H1",
            fontName=FONT_BOLD,
            fontSize=13,
            leading=17,
            textColor=COLOR_PRIMARY_DARK,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2",
            fontName=FONT_BOLD,
            fontSize=10.5,
            leading=14.5,
            textColor=COLOR_TEAL_DARK,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName=FONT_STD,
            fontSize=8.3,
            leading=12,
            textColor=COLOR_TEXT_MAIN,
            spaceAfter=4,
        ),
        "BodyEth": ParagraphStyle(
            "BodyEth",
            fontName=FONT_ETH,
            fontSize=8.3,
            leading=12,
            textColor=COLOR_TEXT_MAIN,
            spaceAfter=4,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            fontName=FONT_STD,
            fontSize=8.2,
            leading=12,
            textColor=COLOR_TEXT_MAIN,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            fontName=FONT_BOLD,
            fontSize=7.8,
            leading=10,
            textColor=colors.white,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            fontName=FONT_STD,
            fontSize=7.2,
            leading=9.5,
            textColor=COLOR_TEXT_MAIN,
            alignment=0,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            fontName=FONT_BOLD,
            fontSize=7.2,
            leading=9.5,
            textColor=COLOR_PRIMARY_DARK,
            alignment=0,
        ),
        "TableCellCode": ParagraphStyle(
            "TableCellCode",
            fontName="Courier",
            fontSize=6.8,
            leading=9,
            textColor=COLOR_PRIMARY_DARK,
            alignment=0,
        ),
        "TableCellEth": ParagraphStyle(
            "TableCellEth",
            fontName=FONT_ETH,
            fontSize=7.2,
            leading=9.5,
            textColor=COLOR_TEXT_MAIN,
            alignment=0,
        ),
        "CodeText": ParagraphStyle(
            "CodeText",
            fontName="Courier",
            fontSize=6.6,
            leading=8.6,
            textColor=COLOR_CODE_TEXT,
        ),
        "CodeTextEth": ParagraphStyle(
            "CodeTextEth",
            fontName=FONT_ETH,
            fontSize=6.6,
            leading=8.6,
            textColor=COLOR_CODE_TEXT,
        ),
        "CalloutTitle": ParagraphStyle(
            "CalloutTitle",
            fontName=FONT_BOLD,
            fontSize=8.2,
            leading=11,
            textColor=COLOR_PRIMARY_DARK,
            spaceAfter=2,
        ),
        "CalloutBody": ParagraphStyle(
            "CalloutBody",
            fontName=FONT_STD,
            fontSize=7.8,
            leading=10.8,
            textColor=COLOR_TEXT_MAIN,
        ),
        "QTitle": ParagraphStyle(
            "QTitle",
            fontName=FONT_BOLD,
            fontSize=8.2,
            leading=11,
            textColor=COLOR_TEAL_DARK,
            spaceBefore=3,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "QAns": ParagraphStyle(
            "QAns",
            fontName=FONT_ETH if HAS_ETHIOPIC_FONT else FONT_STD,
            fontSize=7.8,
            leading=10.8,
            textColor=COLOR_TEXT_MAIN,
            leftIndent=8,
            spaceAfter=5,
        ),
    }
    return styles


def callout(title, text, styles, kind="teal"):
    """Render a styled callout banner box."""
    if kind == "rose":
        bar_color = COLOR_RED
        bg_color = COLOR_RED_BG
    elif kind == "amber":
        bar_color = COLOR_AMBER
        bg_color = COLOR_AMBER_BG
    elif kind == "green":
        bar_color = COLOR_GREEN
        bg_color = COLOR_GREEN_BG
    else:
        bar_color = COLOR_TEAL_MID
        bg_color = COLOR_BG_ALT

    content = [
        Paragraph(f"<b>{esc(title)}</b>", styles["CalloutTitle"]),
        Spacer(1, 2),
        Paragraph(esc(text), styles["CalloutBody"]),
    ]

    t = Table([[content]], colWidths=[520])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("LINELEFT", (0, 0), (0, -1), 3.5, bar_color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def code_box(code_str, caption_title="", styles=None, has_ethiopic=False):
    """Render an exact code listing with header and Ethiopic glyph support."""
    lines = code_str.strip().split("\n")
    cleaned_code = "\n".join(lines)

    flowables = []
    if caption_title:
        head_p = Paragraph(f"<b>{esc(caption_title)}</b>", ParagraphStyle(
            "CodeHead",
            fontName=FONT_BOLD,
            fontSize=6.8,
            leading=8.8,
            textColor=COLOR_TEAL_LIGHT,
        ))
        head_table = Table([[head_p]], colWidths=[520])
        head_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B132B")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_PRIMARY_DARK),
        ]))
        flowables.append(head_table)

    text_style = styles["CodeTextEth"] if has_ethiopic else styles["CodeText"]
    pre = Preformatted(cleaned_code, text_style)
    body_table = Table([[pre]], colWidths=[520])
    body_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CODE_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_PRIMARY_DARK),
    ]))
    flowables.append(body_table)

    return KeepTogether(flowables)


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=46,
        rightMargin=46,
        topMargin=54,
        bottomMargin=50,
    )

    styles = make_styles()
    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("INSA CYBERSECURITY SUMMER CAMP 2026 &bull; FINAL PROJECT SUBMISSION", styles["CoverTag"]))
    story.append(Paragraph("Payment Proof &amp; Sales Ledger (PPL)", styles["CoverTitle"]))
    story.append(Paragraph("A Tamper-Evident Payment Verification Engine for Ethiopian Micro-Merchants", styles["CoverSubtitle"]))

    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_TEAL_MID, spaceBefore=4, spaceAfter=12))

    abstract_text = (
        "<b>Executive Synopsis:</b> In Ethiopia's digital retail economy, Telebirr and Commercial Bank of "
        "Ethiopia (CBE) Mobile Banking handle daily counter payments. However, small merchants routinely fall "
        "victim to mobile payment deception: scammers present counterfeit SMS generator screens, manipulated "
        "transaction receipts, or replayed past confirmations. <b>Payment Proof &amp; Sales Ledger (PPL)</b> eliminates reliance "
        "on the buyer's smartphone screen by enforcing the zero-trust paradigm: <i>verify payments exclusively via incoming "
        "SMS received on the merchant's own registered phone</i>. Verified sales are recorded in a <b>tamper-evident "
        "SHA-256 hash chain</b> with cross-table integrity audits between sales and ledger records."
    )
    story.append(Paragraph(abstract_text, styles["CoverDesc"]))
    story.append(Spacer(1, 4))

    # Metadata Card Table
    meta_data = [
        [Paragraph("<b>Project Specification</b>", styles["TableHead"]), Paragraph("<b>Details</b>", styles["TableHead"])],
        [Paragraph("Authors", styles["TableCellBold"]), Paragraph("Amanuel Mintesenot (CTC-1849-26) &amp; Nahom Mekuria (CTC-6077-26)", styles["TableCell"])],
        [Paragraph("Host Institution", styles["TableCellBold"]), Paragraph("Information Network Security Administration (INSA)", styles["TableCell"])],
        [Paragraph("Submission Track", styles["TableCellBold"]), Paragraph("Defensive Systems &amp; Application Security", styles["TableCell"])],
        [Paragraph("Source Repository", styles["TableCellBold"]), Paragraph("https://github.com/amanminte/payment-proof-ledger", styles["TableCellCode"])],
        [Paragraph("Target Payment Rails", styles["TableCellBold"]), Paragraph("Telebirr (Ethio Telecom), CBE Mobile Banking (Commercial Bank of Ethiopia)", styles["TableCell"])],
        [Paragraph("Technology Stack", styles["TableCellBold"]), Paragraph("Python 3.12, Flask, SQLite3, SHA-256 Hash Chain, Responsive HTML/CSS, Pytest", styles["TableCell"])],
        [Paragraph("Verification Status", styles["TableCellBold"]), Paragraph("<b>30 of 30 Automated Acceptance Tests Passing in Pytest (100% Pass Rate)</b>", styles["TableCellBold"])],
        [Paragraph("AI Assistance", styles["TableCellBold"]), Paragraph("Antigravity (Google DeepMind) &mdash; Pair-Programming &amp; Adversarial Hardening", styles["TableCell"])],
        [Paragraph("Security Audit Status", styles["TableCellBold"]), Paragraph("<b>11 Code Findings Patched &amp; Verified + Documentation Precision Fixes</b>", styles["TableCellBold"])],
        [Paragraph("Date of Deliverable", styles["TableCellBold"]), Paragraph("October 2026", styles["TableCell"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 380])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_CARD, colors.white]),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 6))
    callout_cover = (
        "Zero-Trust Operational Rule: Cashiers are strictly trained never to glance at the customer's phone screen. "
        "A sale is verified only when the live counter dashboard updates to green and sounds the confirmation chime triggered "
        "by the merchant's private Android forwarder."
    )
    story.append(callout("CORE ARCHITECTURAL MANDATE", callout_cover, styles, kind="teal"))

    story.append(PageBreak())

    # =========================================================================
    # TABLE OF CONTENTS / OUTLINE
    # =========================================================================
    story.append(Paragraph("Document Architecture &amp; Table of Contents", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=8))

    toc_data = [
        [Paragraph("<b>Section</b>", styles["TableHead"]), Paragraph("<b>Description &amp; Key Architectural Highlights</b>", styles["TableHead"]), Paragraph("<b>Focus Area</b>", styles["TableHead"])],
        [Paragraph("<b>Section 1</b>", styles["TableCellBold"]), Paragraph("Problem Space, Fraud Vector Taxonomy &amp; Grounded Zero-Trust Model", styles["TableCell"]), Paragraph("Threat Landscape", styles["TableCellBold"])],
        [Paragraph("<b>Section 2</b>", styles["TableCellBold"]), Paragraph("System Topology, Data Flow &amp; Role Separation (Cashier / Owner / Passcodes)", styles["TableCell"]), Paragraph("System Architecture", styles["TableCellBold"])],
        [Paragraph("<b>Section 3</b>", styles["TableCellBold"]), Paragraph("Database Schema: Tables, Declared Foreign Keys &amp; Integrity Controls", styles["TableCell"]), Paragraph("Data Models", styles["TableCellBold"])],
        [Paragraph("<b>Section 4</b>", styles["TableCellBold"]), Paragraph("Core Matching Engine: Multi-Bank Regex &amp; Tamper-Evident SHA-256 Ledger", styles["TableCell"]), Paragraph("Engine Algorithms", styles["TableCellBold"])],
        [Paragraph("<b>Section 5</b>", styles["TableCellBold"]), Paragraph("Access Control, Sliding Window Rate Limiting &amp; 10-Minute Ephemeral Tokens", styles["TableCell"]), Paragraph("Authentication &amp; RBAC", styles["TableCellBold"])],
        [Paragraph("<b>Section 6</b>", styles["TableCellBold"]), Paragraph("Security Hardening Matrix: 11 Real Code Findings &amp; Document Alignment", styles["TableCell"]), Paragraph("Adversarial Audit", styles["TableCellBold"])],
        [Paragraph("<b>Section 7</b>", styles["TableCellBold"]), Paragraph("Complete Codebase Footprint: Exact Verbatim Excerpts from Production Files", styles["TableCell"]), Paragraph("Verified Source Code", styles["TableCellBold"])],
        [Paragraph("<b>Section 8</b>", styles["TableCellBold"]), Paragraph("Automated Test Suite: Complete Pytest Matrix (All 30 Real Test Cases)", styles["TableCell"]), Paragraph("Verification Matrix", styles["TableCellBold"])],
        [Paragraph("<b>Section 9</b>", styles["TableCellBold"]), Paragraph("Evaluator Defense Guide: 5 Core Questions with Honest 20-Second Answers", styles["TableCell"]), Paragraph("Oral Defense", styles["TableCellBold"])],
        [Paragraph("<b>Section 10</b>", styles["TableCellBold"]), Paragraph("Deployment Runbook, Configuration Modes &amp; Android Hardware Field Trials", styles["TableCell"]), Paragraph("Operations &amp; Field Trials", styles["TableCellBold"])],
    ]
    toc_table = Table(toc_data, colWidths=[65, 335, 120])
    toc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 1: PROBLEM SPACE & THREAT LANDSCAPE
    # =========================================================================
    story.append(Paragraph("1. Threat Landscape &amp; Zero-Trust Architecture", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "In Ethiopia's retail economy, Telebirr and CBE Mobile Banking handle the bulk of digital payments. "
        "Because small retailers do not have direct access to private banking APIs, cashiers traditionally verify payments "
        "by looking at the customer's phone screen. Scammers exploit this by showing fake payment confirmation apps, edited receipts, "
        "or replaying older transaction IDs. PPL protects shopkeepers by enforcing one simple rule: never trust the buyer's phone — "
        "only verify payments using the real SMS received on the merchant's own phone.",
        styles["Body"]
    ))

    threat_data = [
        [Paragraph("<b>Threat Vector</b>", styles["TableHead"]), Paragraph("<b>Mechanism of Attack</b>", styles["TableHead"]), Paragraph("<b>PPL Architectural Defense</b>", styles["TableHead"])],
        [
            Paragraph("<b>Fake SMS Generator Apps</b>", styles["TableCellBold"]),
            Paragraph("Scammers run local mobile apps generating spoofed push notifications matching Telebirr/CBE wording.", styles["TableCell"]),
            Paragraph("Buyer's screen is entirely disregarded. Only SMS received on the merchant SIM triggers verification.", styles["TableCellBold"]),
        ],
        [
            Paragraph("<b>Manipulated Receipts</b>", styles["TableCellBold"]),
            Paragraph("Image editing apps alter amounts and merchant names on past transaction receipts in real time.", styles["TableCell"]),
            Paragraph("Amounts and transaction references are parsed strictly from SMS received on the merchant phone.", styles["TableCellBold"]),
        ],
        [
            Paragraph("<b>Transaction ID Replay</b>", styles["TableCellBold"]),
            Paragraph("Buyer displays a legitimate past receipt or re-submits an earlier reference number.", styles["TableCell"]),
            Paragraph("Application duplicate check flags reuse; database payments.txn_id UNIQUE constraint acts as backstop.", styles["TableCellBold"]),
        ],
        [
            Paragraph("<b>Partial Underpayment</b>", styles["TableCellBold"]),
            Paragraph("Buyer sends 50 ETB for a 500 ETB purchase, counting on the cashier's hurried glance at the notification.", styles["TableCell"]),
            Paragraph("Matching engine enforces strict equality (|delta| &lt; 0.005) and logs wrong_amount alerts.", styles["TableCellBold"]),
        ],
        [
            Paragraph("<b>Dishonest Cashier Manipulation</b>", styles["TableCellBold"]),
            Paragraph("Cashier retroactively edits sales records in the database or creates fake payment records.", styles["TableCell"]),
            Paragraph("Ledger stores entries in a SHA-256 hash chain; verify_chain() detects row edits, deletions, or injected sales.", styles["TableCellBold"]),
        ],
    ]
    threat_table = Table(threat_data, colWidths=[120, 200, 200])
    threat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(threat_table)
    story.append(Spacer(1, 6))

    story.append(callout(
        "ARCHITECTURAL CONSTRAINTS OBSERVED",
        "• CON-01: Zero private banking API access required. Operates on standard bank SMS received on the merchant SIM.\n"
        "• CON-02: Android background forwarder captures RECEIVE_SMS broadcasts and POSTs payloads to /api/sms.\n"
        "• CON-03: Local-first SQLite database. All sales and hash data remain hosted on-premise on the merchant device.",
        styles,
        kind="teal"
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 2: SYSTEM ARCHITECTURE & DATA FLOW
    # =========================================================================
    story.append(Paragraph("2. System Architecture &amp; Component Interaction", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "PPL uses a clean, 3-tier design that keeps cashier counter duties completely separate from the store owner's administrative controls:",
        styles["Body"]
    ))

    arch_diagram = (
        "+-------------------------------------------------------------------------+\n"
        "|                         CUSTOMER PAYMENT FLOW                           |\n"
        "|  Customer transfers funds via Telebirr (*127# / App) or CBE Mobile      |\n"
        "+------------------------------------+------------------------------------+\n"
        "                                     | GSM Network Broadcast (SMS)\n"
        "                                     v\n"
        "+-------------------------------------------------------------------------+\n"
        "|                 SHOP OWNER DEDICATED ANDROID PHONE                      |\n"
        "|  - Receives official bank SMS notification on merchant SIM card         |\n"
        "|  - Background forwarder fires HTTP POST /api/sms with security token    |\n"
        "+------------------------------------+------------------------------------+\n"
        "                                     | Local Network HTTP POST (plain HTTP)\n"
        "                                     v\n"
        "+-------------------------------------------------------------------------+\n"
        "|                       PPL CORE SERVICE (FLASK)                          |\n"
        "|  1. Token Authentication: Constant-time hmac.compare_digest            |\n"
        "|  2. Parsing: Multi-bank regex (Telebirr English/Amharic, CBE URL/FT)    |\n"
        "|  3. Matching Engine: Exact amount matching & FIFO unassigned matching   |\n"
        "|  4. Hash Chain Ledger: Sequential SHA-256 tamper-evident entry logged   |\n"
        "+------------------------------------+------------------------------------+\n"
        "                                     | Real-time HTTP Polling (/api/live)\n"
        "                                     v\n"
        "+-------------------------------------------------------------------------+\n"
        "|                    CASHIER COUNTER DASHBOARD                            |\n"
        "|  - Instant status transition: Pending -> Verified (Green Badge)         |\n"
        "|  - Audio Chime plays automatically upon verification                    |\n"
        "|  - Staged timer escalation: 2m (Waiting/Yellow) -> 10m (Alert/Red)      |\n"
        "|  - Financial revenue totals suppressed for cashier sessions             |\n"
        "+-------------------------------------------------------------------------+"
    )
    story.append(code_box(arch_diagram, "DIAGRAM: End-to-End System Topology & Interaction Flow", styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Separation of Roles &amp; Ephemeral Access Passcodes (FR-10)", styles["H2"]))
    story.append(Paragraph(
        "&bull; <b>Cashier Role:</b> Operates the point-of-sale counter. Cashiers open sales with 1-tap presets (50, 100, 200, 500 ETB), "
        "observe live matching, and hear confirmation chimes. The live API endpoint (<code>/api/live</code>) suppresses today's "
        "revenue totals when called by a cashier session.",
        styles["Bullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Shop Owner Role:</b> Full administrative authority. Owners inspect aggregate daily/monthly revenue, profit margins, "
        "run cryptographic ledger audits, and manage accounts.",
        styles["Bullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Ephemeral Shift Passcodes (10-Minute TTL):</b> To reconcile shifts without sharing permanent owner credentials, "
        "the owner generates a 6-digit passcode valid for 10 minutes (<code>ACCOUNTING_PASSCODE_TTL_MIN</code>). The cashier enters this "
        "single-use code to temporarily unlock the reports view with an auto-expiring in-browser countdown.",
        styles["Bullet"]
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: RELATIONAL DATABASE SCHEMA & CONSTRAINTS
    # =========================================================================
    story.append(Paragraph("3. Relational Database Schema &amp; Data Models", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "The SQLite database (<code>ppl.db</code>) defines six relational tables. Note that SQLite does not enforce foreign-key "
        "constraints unless <code>PRAGMA foreign_keys = ON</code> is explicitly executed (which PPL does not enable); instead, "
        "referential consistency between sales and ledger entries is audited cryptographically by <code>verify_chain()</code>:",
        styles["Body"]
    ))

    schema_sql = (
        "CREATE TABLE IF NOT EXISTS sales (\n"
        "    id          INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    amount      REAL    NOT NULL CHECK (amount > 0),\n"
        "    cost        REAL,                                  -- optional, for profit (FR-07)\n"
        "    status      TEXT    NOT NULL DEFAULT 'pending',    -- pending | verified (yellow/red are computed from age)\n"
        "    created_at  TEXT    NOT NULL,\n"
        "    verified_at TEXT,\n"
        "    payment_id  INTEGER REFERENCES payments(id)\n"
        ");\n\n"
        "CREATE TABLE IF NOT EXISTS payments (\n"
        "    id              INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    provider        TEXT,\n"
        "    amount          REAL NOT NULL,\n"
        "    txn_id          TEXT NOT NULL UNIQUE,\n"
        "    received_at     TEXT NOT NULL,\n"
        "    matched_sale_id INTEGER REFERENCES sales(id)\n"
        ");\n\n"
        "CREATE TABLE IF NOT EXISTS alerts (\n"
        "    id          INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    sale_id     INTEGER REFERENCES sales(id),\n"
        "    type        TEXT NOT NULL,   -- waiting | no_payment | wrong_amount | duplicate_txn\n"
        "    created_at  TEXT NOT NULL,\n"
        "    resolved_at TEXT\n"
        ");\n\n"
        "CREATE TABLE IF NOT EXISTS ledger (\n"
        "    id         INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    sale_id    INTEGER NOT NULL REFERENCES sales(id),\n"
        "    amount     REAL    NOT NULL,\n"
        "    created_at TEXT    NOT NULL,\n"
        "    prev_hash  TEXT    NOT NULL,\n"
        "    hash       TEXT    NOT NULL\n"
        ");\n\n"
        "CREATE TABLE IF NOT EXISTS users (\n"
        "    id            INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,\n"
        "    password_hash TEXT NOT NULL,\n"
        "    role          TEXT NOT NULL CHECK (role IN ('owner', 'cashier')),\n"
        "    created_at    TEXT NOT NULL\n"
        ");\n\n"
        "CREATE TABLE IF NOT EXISTS access_tokens (\n"
        "    id         INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    token      TEXT NOT NULL UNIQUE,\n"
        "    created_by INTEGER REFERENCES users(id),\n"
        "    created_at TEXT NOT NULL,\n"
        "    expires_at TEXT NOT NULL,\n"
        "    is_used    INTEGER NOT NULL DEFAULT 0\n"
        ");"
    )
    story.append(code_box(schema_sql, "EXACT REPO SOURCE: backend/schema.sql (Lines 1-52)", styles))
    story.append(Spacer(1, 6))

    schema_analysis = [
        [Paragraph("<b>Field / Constraint</b>", styles["TableHead"]), Paragraph("<b>Defensive Architectural Purpose</b>", styles["TableHead"])],
        [
            Paragraph("<b>payments.txn_id UNIQUE</b>", styles["TableCellBold"]),
            Paragraph("Storage backstop ensuring duplicate bank transaction references cannot be credited twice.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>alerts.resolved_at TEXT</b>", styles["TableCellBold"]),
            Paragraph("Preserves forensic evidence. Instead of deleting alert rows when late payments arrive, resolved_at is set.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>sales.status computed states</b>", styles["TableCellBold"]),
            Paragraph("Only 'pending' and 'verified' are stored. 'Waiting' (yellow) and 'Alert' (red) are computed dynamically by age.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>ledger.prev_hash NOT NULL</b>", styles["TableCellBold"]),
            Paragraph("Binds each verified transaction to the cryptographic hash of the previous entry, establishing a tamper-evident chain.", styles["TableCell"]),
        ],
    ]
    sat = Table(schema_analysis, colWidths=[160, 360])
    sat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(sat)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: CORE ENGINE MECHANICS
    # =========================================================================
    story.append(Paragraph("4. Core Matching Engine &amp; Cryptographic Ledger", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph("4.1 Multi-Bank SMS Regex Parsing Engine", styles["H2"]))
    story.append(Paragraph(
        "Incoming SMS messages forwarded to <code>/api/sms</code> are parsed to extract amount and transaction ID. "
        "The parser handles English and Amharic formats while filtering out account balances and dropping OTP codes:",
        styles["Body"]
    ))

    parser_code = (
        "OTP_RE = re.compile(r\"\\b(otp|one[- ]?time|verification code|passcode|pin)\\b|የማረጋገጫ\\s*ኮድ\", re.I)\n"
        "RECEIVED_RE = re.compile(r\"\\b(received|credited|deposit(?:ed)?)\\b|ተቀብለዋል|ገቢ\", re.I)\n"
        "AMOUNT_RE = re.compile(\n"
        "    r\"(?:ETB|Birr|ብር)\\s*([\\d,]+(?:\\.\\d{1,2})?)|([\\d,]+(?:\\.\\d{1,2})?)\\s*(?:ETB|Birr|ብር)\", re.I)\n"
        "TXN_RE = re.compile(\n"
        "    r\"\\b(?:transaction\\s*(?:id|number|no\\.?)|txn\\s*id|ref\\.?(?:erence)?(?:\\s*(?:no\\.?|number|id))?|id|የግብይት\\s*ቁጥር)\"\n"
        "    r\"\\s*(?:is|:|-)?\\s*([A-Za-z0-9_-]{6,35})\\b\", re.I)\n"
        "URL_TXN_RE = re.compile(r\"(?:cbe\\.com\\.et|ethiotelecom\\.et/receipt)/([A-Za-z0-9_-]{6,35})\", re.I)\n"
        "TXN_VALID = re.compile(r\"^[A-Za-z0-9_-]{5,35}$\")\n\n"
        "def extract_payment_amount(text):\n"
        "    \"\"\"Find the transaction amount, ignoring account balances.\"\"\"\n"
        "    matches = list(AMOUNT_RE.finditer(text))\n"
        "    if not matches:\n"
        "        return None\n"
        "    for m in matches:\n"
        "        start = m.start()\n"
        "        pre_text = text[max(0, start - 35):start].lower()\n"
        "        if re.search(r\"\\b(balance|bal|current\\s*bal(?:ance)?|ሒሳብ)\\b\", pre_text):\n"
        "            continue\n"
        "        post_text = text[m.end():min(len(text), m.end() + 25)].lower()\n"
        "        if re.search(r\"^\\s*(?:is\\s*)?balance\\b\", post_text):\n"
        "            continue\n"
        "        val_str = (m.group(1) or m.group(2)).replace(\",\", \"\")\n"
        "        try:\n"
        "            return float(val_str)\n"
        "        except ValueError:\n"
        "            continue\n"
        "    return None"
    )
    story.append(code_box(parser_code, "EXACT REPO SOURCE: backend/matching.py (Lines 14-43)", styles, has_ethiopic=True))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.2 Matching Mechanism &amp; Window Semantics", styles["H2"]))
    story.append(Paragraph(
        "<b>Important Window Semantics:</b> In PPL, open pending sales remain open indefinitely until matched or cancelled. "
        "A late payment arriving after the 2-minute (yellow) or 10-minute (red) alert thresholds <b>still matches the open sale</b> "
        "and resolves the alert (tested in <code>AT-09</code>). The 10-minute window (<code>UNASSIGNED_WINDOW_MIN = 10</code>) applies "
        "specifically to payments that arrive <b>before</b> a sale is created, allowing retroactive matching upon sale creation.",
        styles["Body"]
    ))

    matching_code = (
        "def process_payment(amount, txn_id, provider=None, received_at=None, now=None):\n"
        "    now = now or now_utc()\n"
        "    received_at = received_at or now\n"
        "    amount = validate_amount(amount)\n"
        "    txn_id = validate_txn_id(txn_id)\n"
        "    with db.connect() as conn:\n"
        "        if conn.execute(\"SELECT 1 FROM payments WHERE txn_id=?\", (txn_id,)).fetchone():\n"
        "            conn.execute(\"INSERT INTO alerts(sale_id, type, created_at) VALUES (NULL,'duplicate_txn',?)\",\n"
        "                         (iso(now),))\n"
        "            return {\"result\": \"duplicate\"}\n"
        "        sale = conn.execute(\n"
        "            \"SELECT * FROM sales WHERE status = 'pending' AND ABS(amount-?)<0.005 \"\n"
        "            \"ORDER BY created_at LIMIT 1\", (amount,)).fetchone()\n"
        "        pid = conn.execute(\n"
        "            \"INSERT INTO payments(provider, amount, txn_id, received_at, matched_sale_id) VALUES (?,?,?,?,?)\",\n"
        "            (provider, amount, txn_id, iso(received_at), sale[\"id\"] if sale else None)).lastrowid\n"
        "        if sale:\n"
        "            _verify(conn, sale[\"id\"], sale[\"amount\"], pid, now)\n"
        "            return {\"result\": \"verified\", \"sale_id\": sale[\"id\"]}\n"
        "        newest_open = conn.execute(\n"
        "            \"SELECT id FROM sales WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1\").fetchone()\n"
        "        if newest_open:\n"
        "            conn.execute(\"INSERT INTO alerts(sale_id, type, created_at) VALUES (?,'wrong_amount',?)\",\n"
        "                         (newest_open[\"id\"], iso(now)))\n"
        "            return {\"result\": \"mismatch\", \"sale_id\": newest_open[\"id\"]}\n"
        "        return {\"result\": \"unassigned\"}"
    )
    story.append(code_box(matching_code, "EXACT REPO SOURCE: backend/matching.py (Lines 165-195)", styles))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4 CONTINUED: TAMPER-EVIDENT LEDGER
    # =========================================================================
    story.append(Paragraph("4.3 Tamper-Evident SHA-256 Hash Chain &amp; Cross-Table Audit", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "PPL implements a cryptographic SHA-256 hash chain to record every verified transaction. "
        "The genesis block starts with 64 zero characters: <code>GENESIS = '0' * 64</code>. "
        "The ledger is <b>tamper-evident</b>: modifying an old row breaks the hash link. To defend against direct database tampering, "
        "<code>verify_chain()</code> cross-checks the <code>sales</code> table to ensure every verified sale matches a ledger entry:",
        styles["Body"]
    ))

    ledger_code = (
        "def compute_hash(prev_hash, sale_id, amount, created_at):\n"
        "    data = f\"{prev_hash}|{sale_id}|{float(amount):.2f}|{created_at}\".encode()\n"
        "    return hashlib.sha256(data).hexdigest()\n\n"
        "def verify_chain():\n"
        "    rows = db.query(\"SELECT * FROM ledger ORDER BY id\")\n"
        "    prev = GENESIS\n"
        "    seen_sale_ids = set()\n\n"
        "    for r in rows:\n"
        "        expected = compute_hash(r[\"prev_hash\"], r[\"sale_id\"], r[\"amount\"], r[\"created_at\"])\n"
        "        if r[\"prev_hash\"] != prev or r[\"hash\"] != expected:\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": r[\"id\"],\n"
        "                \"reason\": f\"Cryptographic hash chain break at ledger entry #{r['id']}\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": rows[-1][\"hash\"] if rows else None,\n"
        "            }\n\n"
        "        sales = db.query(\"SELECT * FROM sales WHERE id = ?\", (r[\"sale_id\"],))\n"
        "        if not sales:\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": r[\"id\"],\n"
        "                \"reason\": f\"Ledger entry #{r['id']} points to nonexistent sale #{r['sale_id']}\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": rows[-1][\"hash\"] if rows else None,\n"
        "            }\n"
        "        sale = sales[0]\n"
        "        if sale[\"status\"] != \"verified\":\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": r[\"id\"],\n"
        "                \"reason\": f\"Ledger entry #{r['id']} points to unverified sale #{r['sale_id']} (status: {sale['status']})\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": rows[-1][\"hash\"] if rows else None,\n"
        "            }\n"
        "        if abs(float(sale[\"amount\"]) - float(r[\"amount\"])) > 0.001:\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": r[\"id\"],\n"
        "                \"reason\": f\"Ledger entry #{r['id']} amount ({r['amount']}) does not match sale #{r['sale_id']} amount ({sale['amount']})\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": rows[-1][\"hash\"] if rows else None,\n"
        "            }\n"
        "        if r[\"sale_id\"] in seen_sale_ids:\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": r[\"id\"],\n"
        "                \"reason\": f\"Duplicate ledger entry for sale #{r['sale_id']}\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": rows[-1][\"hash\"] if rows else None,\n"
        "            }\n"
        "        seen_sale_ids.add(r[\"sale_id\"])\n"
        "        prev = r[\"hash\"]\n\n"
        "    verified_sales = db.query(\"SELECT * FROM sales WHERE status = 'verified' ORDER BY id\")\n"
        "    for vs in verified_sales:\n"
        "        if vs[\"id\"] not in seen_sale_ids:\n"
        "            return {\n"
        "                \"ok\": False,\n"
        "                \"broken_at\": vs[\"id\"],\n"
        "                \"reason\": f\"Verified sale #{vs['id']} has no matching entry in ledger\",\n"
        "                \"entries\": len(rows),\n"
        "                \"latest_hash\": prev if rows else None,\n"
        "            }\n\n"
        "    return {\n"
        "        \"ok\": True,\n"
        "        \"broken_at\": None,\n"
        "        \"entries\": len(rows),\n"
        "        \"latest_hash\": prev if rows else None,\n"
        "    }"
    )
    story.append(code_box(ledger_code, "EXACT REPO SOURCE: backend/ledger.py (Lines 16-30 & 33-112)", styles))

    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 5: ACCESS CONTROL & RATE LIMITING
    # =========================================================================
    story.append(Paragraph("5. Access Control &amp; Rate Limiting", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "To mitigate brute-force attacks against 6-digit shift passcodes and login credentials, "
        "PPL incorporates a thread-safe sliding window rate limiter:",
        styles["Body"]
    ))

    rate_code = (
        "class RateLimiter:\n"
        "    def __init__(self, max_attempts=MAX_ATTEMPTS, lock_seconds=LOCK_SECONDS):\n"
        "        self.max_attempts = max_attempts\n"
        "        self.lock_seconds = lock_seconds\n"
        "        self._lock = threading.Lock()\n"
        "        self._failures = {}  # key -> list of datetime\n"
        "        self._locked_until = {}  # key -> datetime\n\n"
        "    def check_lockout(self, key, now=None):\n"
        "        \"\"\"Check if `key` is currently locked out. Returns (is_locked, remaining_seconds).\"\"\"\n"
        "        now = now or datetime.now(timezone.utc)\n"
        "        with self._lock:\n"
        "            until = self._locked_until.get(key)\n"
        "            if until:\n"
        "                if now < until:\n"
        "                    rem = int((until - now).total_seconds())\n"
        "                    return True, max(1, rem)\n"
        "                else:\n"
        "                    # Lockout expired\n"
        "                    del self._locked_until[key]\n"
        "                    self._failures.pop(key, None)\n"
        "            return False, 0\n\n"
        "    def record_failure(self, key, now=None):\n"
        "        \"\"\"Record a failed attempt. If limit reached, locks out for `lock_seconds`.\"\"\"\n"
        "        now = now or datetime.now(timezone.utc)\n"
        "        with self._lock:\n"
        "            until = self._locked_until.get(key)\n"
        "            if until and now < until:\n"
        "                rem = int((until - now).total_seconds())\n"
        "                return True, max(1, rem), self.max_attempts\n\n"
        "            cutoff = now - timedelta(seconds=self.lock_seconds)\n"
        "            history = [t for t in self._failures.get(key, []) if t > cutoff]\n"
        "            history.append(now)\n"
        "            self._failures[key] = history\n\n"
        "            if len(history) >= self.max_attempts:\n"
        "                lock_time = now + timedelta(seconds=self.lock_seconds)\n"
        "                self._locked_until[key] = lock_time\n"
        "                return True, self.lock_seconds, len(history)\n\n"
        "            return False, 0, len(history)"
    )
    story.append(code_box(rate_code, "EXACT REPO SOURCE: backend/rate_limit.py (Lines 12-60)", styles))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 5 CONTINUED: AUTH & PASSCODES
    # =========================================================================
    story.append(Paragraph("5.1 Ephemeral Shift Passcodes (FR-10)", styles["H2"]))
    story.append(Paragraph(
        "The shop owner generates 6-digit dynamic passcodes expiring after 10 minutes (<code>ACCOUNTING_PASSCODE_TTL_MIN</code>). "
        "Cashiers use these single-use passcodes to unlock shift reconciliation reports:",
        styles["Body"]
    ))

    auth_code = (
        "def generate_ephemeral_passcode(created_by=None, ttl_minutes=10, now=None):\n"
        "    start = now if now is not None else now_utc()\n"
        "    expiry = start + timedelta(minutes=ttl_minutes)\n"
        "    created_at = iso(start)\n"
        "    expires_at = iso(expiry)\n"
        "    token = f\"{secrets.randbelow(1_000_000):06d}\"\n"
        "    with db.connect() as conn:\n"
        "        conn.execute(\"UPDATE access_tokens SET is_used = 1 WHERE is_used = 0\")\n"
        "        conn.execute(\n"
        "            \"INSERT INTO access_tokens (token, created_by, created_at, expires_at, is_used) VALUES (?, ?, ?, ?, 0)\",\n"
        "            (token, created_by, created_at, expires_at),\n"
        "        )\n"
        "    return {\n"
        "        \"token\": token,\n"
        "        \"created_by\": created_by,\n"
        "        \"created_at\": created_at,\n"
        "        \"expires_at\": expires_at,\n"
        "        \"ttl_minutes\": ttl_minutes,\n"
        "    }\n\n"
        "def verify_and_consume_passcode(passcode, now=None):\n"
        "    code = (passcode or \"\").strip().replace(\" \", \"\")\n"
        "    if not code or len(code) != 6 or not code.isdigit():\n"
        "        return {\"ok\": False, \"error\": \"Passcode must be a 6-digit number.\"}\n"
        "    current = now if now is not None else now_utc()\n"
        "    now_str = iso(current)\n"
        "    with db.connect() as conn:\n"
        "        row = conn.execute(\n"
        "            \"SELECT * FROM access_tokens WHERE token = ? AND is_used = 0 AND expires_at > ?\",\n"
        "            (code, now_str),\n"
        "        ).fetchone()\n"
        "        if not row:\n"
        "            return {\"ok\": False, \"error\": \"Invalid or expired passcode. Request a new code from the Shop Owner.\"}\n"
        "        conn.execute(\"UPDATE access_tokens SET is_used = 1 WHERE id = ?\", (row[\"id\"],))\n"
        "        return {\"ok\": True, \"token\": row[\"token\"], \"expires_at\": row[\"expires_at\"]}"
    )
    story.append(code_box(auth_code, "EXACT REPO SOURCE: backend/auth.py (Lines 106-131 & 151-173)", styles))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 6: ADVERSARIAL SECURITY HARDENING MATRIX
    # =========================================================================
    story.append(Paragraph("6. Adversarial Security Hardening Matrix", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "Prior to final submission, the codebase underwent an adversarial code review and attack probe suite. "
        "A total of 11 real code vulnerabilities were identified and patched with passing regression tests. "
        "OTP filtering was verified as an initial architectural design control, and documentation discrepancies were corrected:",
        styles["Body"]
    ))

    vuln_data = [
        [Paragraph("<b>#</b>", styles["TableHead"]), Paragraph("<b>Vulnerability Area</b>", styles["TableHead"]), Paragraph("<b>Severity</b>", styles["TableHead"]), Paragraph("<b>Attack Probe Finding</b>", styles["TableHead"]), Paragraph("<b>Implemented Fix &amp; Defense</b>", styles["TableHead"])],
        [
            Paragraph("1", styles["TableCellBold"]),
            Paragraph("Public Owner Registration", styles["TableCellBold"]),
            Paragraph("CRITICAL", styles["TableCellBold"]),
            Paragraph("Registration page permitted visitor to select role='owner', bypassing access controls.", styles["TableCell"]),
            Paragraph("Removed role selection; only first user becomes owner; subsequent users are cashiers.", styles["TableCell"]),
        ],
        [
            Paragraph("2", styles["TableCellBold"]),
            Paragraph("Cashier Simulator Access", styles["TableCellBold"]),
            Paragraph("CRITICAL", styles["TableCellBold"]),
            Paragraph("Cashier could POST to /inbox/simulate to forge payments and verify unpaid sales.", styles["TableCell"]),
            Paragraph("Locked /inbox/simulate to owner role and requires ENABLE_SIMULATOR=1; returns 403 otherwise.", styles["TableCell"]),
        ],
        [
            Paragraph("3", styles["TableCellBold"]),
            Paragraph("Ledger / Sales Desync", styles["TableCellBold"]),
            Paragraph("HIGH", styles["TableCellBold"]),
            Paragraph("Editing sale amount in DB altered reports total while hash chain remained intact.", styles["TableCell"]),
            Paragraph("verify_chain() cross-checks sales table: verifies amount equality and catches unindexed sales.", styles["TableCell"]),
        ],
        [
            Paragraph("4", styles["TableCellBold"]),
            Paragraph("Default Secret Acceptance", styles["TableCellBold"]),
            Paragraph("HIGH", styles["TableCellBold"]),
            Paragraph("App booted with 'change-me' or placeholder secrets, allowing session forgery.", styles["TableCell"]),
            Paragraph("validate_secrets() rejects secrets &lt;32 chars or starting with placeholder prefixes in production.", styles["TableCell"]),
        ],
        [
            Paragraph("5", styles["TableCellBold"]),
            Paragraph("Passcode &amp; Login Brute-Force", styles["TableCellBold"]),
            Paragraph("MEDIUM", styles["TableCellBold"]),
            Paragraph("1000 wrong passcode guesses had no lockout, enabling rapid online guessing attacks.", styles["TableCell"]),
            Paragraph("RateLimiter enforces 5 failed attempts per IP (login) and per IP+user (passcode) -&gt; 300-second lockout returning HTTP 429.", styles["TableCell"]),
        ],
        [
            Paragraph("6", styles["TableCellBold"]),
            Paragraph("Debug Server Exposure", styles["TableCellBold"]),
            Paragraph("MEDIUM", styles["TableCellBold"]),
            Paragraph("app.run(debug=True, host='0.0.0.0') exposed interactive debugger on local Wi-Fi.", styles["TableCell"]),
            Paragraph("Disabled debug mode (debug=False); defaults host to 127.0.0.1 or reads HOST from environment.", styles["TableCell"]),
        ],
        [
            Paragraph("7", styles["TableCellBold"]),
            Paragraph("Open Redirect Phishing", styles["TableCellBold"]),
            Paragraph("LOW", styles["TableCellBold"]),
            Paragraph("/login?next=https://evil.example redirected user off-site upon login.", styles["TableCell"]),
            Paragraph("Sanitized next parameter in login_page(): enforces single leading '/' and blocks protocol schemes.", styles["TableCell"]),
        ],
        [
            Paragraph("8", styles["TableCellBold"]),
            Paragraph("Outgoing Transfer Misparse", styles["TableCellBold"]),
            Paragraph("MEDIUM", styles["TableCellBold"]),
            Paragraph("'You have transferred ETB 1,200' parsed as incoming funds, verifying sales.", styles["TableCell"]),
            Paragraph("RECEIVED_RE regex requires incoming keywords (received, credited, deposit, ተቀብለዋል, ገቢ).", styles["TableCellEth"]),
        ],
        [
            Paragraph("9", styles["TableCellBold"]),
            Paragraph("Balance / Amount Collision", styles["TableCellBold"]),
            Paragraph("MEDIUM", styles["TableCellBold"]),
            Paragraph("SMS stating account balance before payment parsed balance instead of payment.", styles["TableCell"]),
            Paragraph("extract_payment_amount() implements regex lookaround discarding numbers adjacent to balance/ሒሳብ.", styles["TableCellEth"]),
        ],
        [
            Paragraph("10", styles["TableCellBold"]),
            Paragraph("Alert Evidence Deletion", styles["TableCellBold"]),
            Paragraph("LOW", styles["TableCellBold"]),
            Paragraph("Verifying late payment deleted waiting/alert rows, losing record of delays.", styles["TableCell"]),
            Paragraph("Alerts marked resolved via resolved_at timestamp rather than being deleted.", styles["TableCell"]),
        ],
        [
            Paragraph("11", styles["TableCellBold"]),
            Paragraph("Cashier Financial Exposure", styles["TableCellBold"]),
            Paragraph("LOW", styles["TableCellBold"]),
            Paragraph("/api/live returned daily revenue totals and transaction counts to cashiers.", styles["TableCell"]),
            Paragraph("Endpoint checks user role and returns today_total: null when requested by cashiers.", styles["TableCell"]),
        ],
        [
            Paragraph("12", styles["TableCellBold"]),
            Paragraph("Documentation Precision", styles["TableCellBold"]),
            Paragraph("INFO", styles["TableCellBold"]),
            Paragraph("Docs had overclaims (e.g. 'immutable' vs 'tamper-evident') and mismatched test counts.", styles["TableCell"]),
            Paragraph("Corrected all documentation to accurately describe 30 tests and honest security boundaries.", styles["TableCell"]),
        ],
    ]
    vuln_table = Table(vuln_data, colWidths=[20, 110, 50, 170, 170])
    vuln_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(vuln_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 7: COMPLETE CODEBASE FOOTPRINT
    # =========================================================================
    story.append(Paragraph("7. Complete Codebase Footprint: Production Routes", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "Below are exact verbatim production excerpts of the primary application routes in <code>backend/app.py</code> "
        "demonstrating token-authenticated webhook ingestion, role-gated SMS simulation, and redirect sanitization:",
        styles["Body"]
    ))

    webhook_code = (
        "@app.route(\"/api/sms\", methods=[\"POST\"])\n"
        "def receive_sms():\n"
        "    token = request.headers.get(\"X-Token\") or request.args.get(\"token\", \"\")\n"
        "    if not hmac.compare_digest(token, config.SMS_TOKEN):\n"
        "        abort(401)\n"
        "    data = request.get_json(silent=True) or request.form\n"
        "    text = (data.get(\"message\") or data.get(\"text\") or data.get(\"body\")\n"
        "            or data.get(\"msg\") or data.get(\"content\") or \"\")\n"
        "    return jsonify(matching.process_message(text))"
    )
    story.append(code_box(webhook_code, "EXACT REPO SOURCE: backend/app.py (Lines 410-418)", styles))
    story.append(Spacer(1, 6))

    sim_code = (
        "@app.route(\"/inbox/simulate\", methods=[\"POST\"])\n"
        "@login_required\n"
        "def simulate_sms():\n"
        "    _check_csrf()\n"
        "    if not config.ENABLE_SIMULATOR:\n"
        "        abort(403)\n"
        "    user = auth.get_user_by_id(session.get(\"user_id\"))\n"
        "    if not user or user[\"role\"] != \"owner\" or not session.get(\"is_owner\", True):\n"
        "        abort(403)\n\n"
        "    try:\n"
        "        message = request.form.get(\"message\", \"\").strip()\n"
        "        if message:\n"
        "            result = matching.process_message(message)\n"
        "        else:\n"
        "            result = matching.process_payment(request.form.get(\"amount\"), request.form.get(\"txn_id\"),\n"
        "                                              request.form.get(\"provider\") or None)\n"
        "    except ValueError as e:\n"
        "        flash(str(e), \"danger\")\n"
        "        return redirect(url_for(\"inbox\"))\n"
        "    flash(f\"Result: {result['result']}\" + (f\" ({result['reason']})\" if \"reason\" in result else \"\"), \"info\")\n"
        "    return redirect(url_for(\"inbox\"))"
    )
    story.append(code_box(sim_code, "EXACT REPO SOURCE: backend/app.py (Lines 386-407)", styles))
    story.append(Spacer(1, 6))

    redirect_code = (
        "        # Sanitize next redirect to prevent Open Redirect\n"
        "        next_url = request.args.get(\"next\")\n"
        "        if not next_url or not next_url.startswith(\"/\") or next_url.startswith(\"//\") or \"\\\\\" in next_url:\n"
        "            next_url = url_for(\"dashboard\")\n"
        "        return redirect(next_url)"
    )
    story.append(code_box(redirect_code, "EXACT REPO SOURCE: backend/app.py (Lines 117-121)", styles))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 8: AUTOMATED TEST SUITE & VERIFICATION RESULTS
    # =========================================================================
    story.append(Paragraph("8. Automated Test Suite: Verified Pytest Matrix", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "The test suite (<code>backend/tests/test_matching.py</code>) executes under <code>pytest -v</code>. "
        "The table below lists all 30 tests verbatim with their real function names and verified pass status:",
        styles["Body"]
    ))

    test_data = [
        [Paragraph("<b>#</b>", styles["TableHead"]), Paragraph("<b>Pytest Function Name (from test_matching.py)</b>", styles["TableHead"]), Paragraph("<b>Verified Behavior / Test Assertion</b>", styles["TableHead"]), Paragraph("<b>Result</b>", styles["TableHead"])],
        [Paragraph("1", styles["TableCellBold"]), Paragraph("test_at01_matching_payment_verifies_sale", styles["TableCellCode"]), Paragraph("Open sale of 500 ETB verified immediately by matching incoming 500 ETB SMS.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("2", styles["TableCellBold"]), Paragraph("test_at02_wrong_amount_not_verified", styles["TableCellCode"]), Paragraph("Incoming 300 ETB for 500 ETB sale rejected; wrong_amount alert recorded.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("3", styles["TableCellBold"]), Paragraph("test_at03_duplicate_txn_id_flagged", styles["TableCellCode"]), Paragraph("App duplicate check catches replayed ID; payments.txn_id UNIQUE is storage backstop.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("4", styles["TableCellBold"]), Paragraph("test_at04_alert_stages", styles["TableCellCode"]), Paragraph("Pending sale escalates to waiting (yellow) at 2m and alert (red) at 10m.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("5", styles["TableCellBold"]), Paragraph("test_at05_unassigned_payment", styles["TableCellCode"]), Paragraph("Payment arriving before sale is placed in unassigned pool for retroactive match.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("6", styles["TableCellBold"]), Paragraph("test_at06_hash_chain_detects_edit", styles["TableCellCode"]), Paragraph("Manual edit of row in ledger table causes verify_chain() to report tampered row ID.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("7", styles["TableCellBold"]), Paragraph("test_at07_missing_token_rejected", styles["TableCellCode"]), Paragraph("Rejects unauthenticated SMS (Trials 1 &amp; 2 fail with 401); accepts valid token via X-Token or URL param (Trial 3 passes with 200).", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("8", styles["TableCellBold"]), Paragraph("test_at08_otp_discarded", styles["TableCellCode"]), Paragraph("SMS containing banking verification OTP is dropped; 0 rows inserted in payments.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("9", styles["TableCellBold"]), Paragraph("test_at09_late_payment_clears_alert", styles["TableCellCode"]), Paragraph("Sale turned red receives late payment; verifies sale, keeps alert with resolved_at.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("10", styles["TableCellBold"]), Paragraph("test_payment_before_sale_still_matches", styles["TableCellCode"]), Paragraph("Payment arriving up to 10m before sale creation retroactively matches sale.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("11", styles["TableCellBold"]), Paragraph("test_parse_message_cases", styles["TableCellCode"]), Paragraph("Tests parsing Telebirr, CBE URL, and Amharic formats (ተቀብለዋል, የግብይት ቁጥር).", styles["TableCellEth"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("12", styles["TableCellBold"]), Paragraph("test_input_validation", styles["TableCellCode"]), Paragraph("Validates amount bounds and rejects malformed characters in transaction IDs.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("13", styles["TableCellBold"]), Paragraph("test_sql_injection_text_is_harmless", styles["TableCellCode"]), Paragraph("SQL injection text in txn_id rejected by validate_txn_id; database intact.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("14", styles["TableCellBold"]), Paragraph("test_reports_totals_and_profit", styles["TableCellCode"]), Paragraph("Verifies revenue totals and profit calculations (amount minus cost).", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("15", styles["TableCellBold"]), Paragraph("test_pages_load_and_csrf_enforced", styles["TableCellCode"]), Paragraph("All web routes return 200/302; POST requests lacking CSRF token return 400.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("16", styles["TableCellBold"]), Paragraph("test_authentication_and_password_hashing", styles["TableCellCode"]), Paragraph("Validates salted Scrypt/PBKDF2 password verification via authenticate().", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("17", styles["TableCellBold"]), Paragraph("test_sql_injection_on_login", styles["TableCellCode"]), Paragraph("SQL injection payload in login credentials safely handled via parameterized query.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("18", styles["TableCellBold"]), Paragraph("test_cancel_pending_sale", styles["TableCellCode"]), Paragraph("Pending sale can be cancelled; warning/alert sales locked against cashier cancel.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("19", styles["TableCellBold"]), Paragraph("test_ephemeral_passcode_lifecycle", styles["TableCellCode"]), Paragraph("6-digit token expires after 10m; marked is_used=1 upon consumption.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("20", styles["TableCellBold"]), Paragraph("test_cashier_accounting_session_flow", styles["TableCellCode"]), Paragraph("Cashier uses passcode to temporarily unlock accounting reports view.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("21", styles["TableCellBold"]), Paragraph("test_public_registration_cannot_create_owner", styles["TableCellCode"]), Paragraph("Registration endpoint refuses owner role creation; cashier provisioning only.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("22", styles["TableCellBold"]), Paragraph("test_simulator_restricted_to_owner_and_flag", styles["TableCellCode"]), Paragraph("Cashier session hitting /inbox/simulate receives HTTP 403 Forbidden.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("23", styles["TableCellBold"]), Paragraph("test_ledger_detects_tampered_sales_table", styles["TableCellCode"]), Paragraph("verify_chain() catches unauthorized sales table amount edit directly in SQLite.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("24", styles["TableCellBold"]), Paragraph("test_ledger_detects_injected_verified_sale", styles["TableCellCode"]), Paragraph("verify_chain() catches injected verified sale with no matching ledger entry.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("25", styles["TableCellBold"]), Paragraph("test_refuse_start_with_default_secrets_in_production", styles["TableCellCode"]), Paragraph("validate_secrets() aborts if secret &lt; 32 chars or starts with placeholder text.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("26", styles["TableCellBold"]), Paragraph("test_rate_limit_lockout_on_login", styles["TableCellCode"]), Paragraph("5 failed login attempts trigger HTTP 429 and 300-second IP lockout.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("27", styles["TableCellBold"]), Paragraph("test_rate_limit_lockout_on_passcode", styles["TableCellCode"]), Paragraph("5 failed passcode attempts trigger HTTP 429 and 300-second IP lockout.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("28", styles["TableCellBold"]), Paragraph("test_login_open_redirect_prevented", styles["TableCellCode"]), Paragraph("next=https://evil.example safely sanitized to internal /dashboard.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("29", styles["TableCellBold"]), Paragraph("test_parser_ignores_outgoing_transfers_and_parses_balance_before_amount", styles["TableCellCode"]), Paragraph("Ignores outgoing 'transferred'; parses 500 payment from SMS mentioning balance.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
        [Paragraph("30", styles["TableCellBold"]), Paragraph("test_cashier_cannot_see_today_totals_on_live_or_dashboard", styles["TableCellCode"]), Paragraph("/api/live returns today_total: null when requested by cashier session.", styles["TableCell"]), Paragraph("PASSED", styles["TableCellBold"])],
    ]
    test_table = Table(test_data, colWidths=[20, 205, 245, 50])
    test_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(test_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 9: EVALUATOR DEFENSE CHEAT SHEET
    # =========================================================================
    story.append(Paragraph("9. Evaluator Defense Guide: 5 Tough Questions &amp; Answers", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "During oral project defense at the INSA Cybersecurity Camp, evaluators probe edge cases and threat boundaries. "
        "The following 20-second answers provide crisp, technically grounded responses:",
        styles["Body"]
    ))

    qa_list = [
        (
            "Q1: 'Can't a scammer fake the SMS too?'",
            "\"A fake-SMS app only fools whoever is looking at the buyer's phone screen. PPL strictly ignores that screen "
            "and trusts only the SMS that arrives on the merchant's own phone from the bank's shortcode. While sender names can "
            "be spoofed cheaply through commercial bulk-SMS services, trusting the sender name is not cryptographic; PPL significantly "
            "reduces counter fraud by ignoring the buyer's device. For large sales, we recommend a quick balance check in the bank app as well.\""
        ),
        (
            "Q2: 'Why not just check the Telebirr or CBE mobile app?'",
            "\"Checking the banking app is right when there's time. In a queue, people skip it. PPL does the match automatically, "
            "warns at 2 minutes and alerts at 10 minutes if nothing arrives, and keeps a record of how often scam attempts happen. "
            "It supports the banking app and doesn't replace it.\""
        ),
        (
            "Q3: 'What stops a dishonest cashier from cheating?'",
            "\"A cashier cannot see sales totals, cannot create owner accounts, cannot use the SMS simulator, and cannot cancel "
            "a sale after the 2-minute warning. If someone edits a sale in the database, the ledger check flags it. What we don't "
            "stop: a cashier who never opens a sale and keeps physical cash. That boundary is documented in our threat model.\""
        ),
        (
            "Q4: 'Is your SHA-256 hash chain tamper-proof?'",
            "\"No, it is tamper-evident. Changing an amount, deleting an entry, or adding an unverified sale is detected. "
            "Someone with full server database access could rebuild the whole chain forward, so the owner saves the daily closing "
            "hash offline and compares it later.\""
        ),
        (
            "Q5: 'Does it work with real messages, and what happens when it cannot read one?'",
            "\"Yes. We verified it against test messages modeled on real Telebirr English, Telebirr Amharic (ተቀብለዋል, የግብይት ቁጥር), and "
            "CBE Mobile Banking receipt formats (mbreciept.cbe.com.et), with all personal details replaced. If a message cannot be read, "
            "it is marked unparsed and nothing is verified. It fails safe, and the seller checks the bank app. It also discards OTP messages "
            "and ignores outgoing transfers.\""
        ),
        (
            "Bonus: 'Did you use AI to build this?'",
            "\"Yes, as an interactive pair-programming and adversarial testing tool. We authored the requirements and threat model, "
            "and we reviewed, tested, and attacked the code. That attack-driven review uncovered real holes—like open owner registration "
            "and unindexed sales table manipulation—which we hardened with 30 passing automated regression tests.\""
        ),
    ]

    for q, a in qa_list:
        story.append(Paragraph(esc(q), styles["QTitle"]))
        story.append(Paragraph(esc(a), styles["QAns"]))

    story.append(Spacer(1, 4))
    story.append(callout(
        "TRANSPARENT SYSTEM LIMITATIONS (DISCLOSED PROACTIVELY)",
        "1. Concurrent Identical Amounts: Matching is by exact amount and time window. If two customers pay 500 ETB simultaneously, "
        "matching occurs on a FIFO basis. Cashiers should note customer names on high-value concurrent sales.\n"
        "2. Plain HTTP Webhook: The Android forwarder communicates over local Wi-Fi via plain HTTP with an X-Token header. "
        "On untrusted shared Wi-Fi, traffic could be intercepted unless tunneled via HTTPS or VPN.\n"
        "3. In-Memory Rate Limiting: Lockouts are tracked in memory per IP; restarting the server resets the failure count.\n"
        "4. Demo Mode: Ships with known demo credentials (owner123, cashier123) for evaluator review; production enforces DEMO_MODE=0.",
        styles,
        kind="amber"
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 10: DEPLOYMENT & PRODUCTION RUNBOOK
    # =========================================================================
    story.append(Paragraph("10. Deployment Runbook &amp; Configuration", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_MID, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "PPL supports two operational configurations: an Evaluation Mode for evaluator testing and live demonstrations, "
        "and a hardened Production Mode for actual store deployment:",
        styles["Body"]
    ))

    story.append(Paragraph("10.1 Evaluation Mode Configuration (INSA Summer Camp Demo)", styles["H2"]))
    eval_env_spec = (
        "# Evaluation / Demo Mode Configuration (.env)\n"
        "DEMO_MODE=1\n"
        "ENABLE_SIMULATOR=1\n"
        "HOST=127.0.0.1\n"
        "DATABASE=ppl.db\n"
        "ACCOUNTING_PASSCODE_TTL_MIN=10\n\n"
        "# Evaluation mode seeds baseline accounts (owner/owner123, cashier/cashier123)\n"
        "# and enables the manual SMS simulator at /inbox for interactive testing."
    )
    story.append(code_box(eval_env_spec, "CONFIGURATION: .env (Evaluation & Demo Mode)", styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("10.2 Production Mode Configuration", styles["H2"]))
    prod_env_spec = (
        "# Hardened Production Environment Configuration (.env)\n"
        "SECRET_KEY=<generate-32-byte-hex-key-via-secrets-token-hex-32>\n"
        "SMS_TOKEN=<generate-32-byte-hex-key-via-secrets-token-hex-32>\n"
        "DEMO_MODE=0\n"
        "ENABLE_SIMULATOR=0\n"
        "HOST=127.0.0.1\n"
        "DATABASE=ppl.db\n"
        "ACCOUNTING_PASSCODE_TTL_MIN=10\n\n"
        "# In production mode, weak or placeholder keys cause the app to reject requests (HTTP 500).\n"
        "# Constants YELLOW_AFTER_MIN (2), RED_AFTER_MIN (10), UNASSIGNED_WINDOW_MIN (10) and\n"
        "# MAX_AMOUNT (1,000,000) are hardcoded in backend/config.py."
    )
    story.append(code_box(prod_env_spec, "EXAMPLE CONFIGURATION: .env (Hardened Production Mode)", styles))
    story.append(Spacer(1, 6))

    deploy_steps = [
        Paragraph("<b>1. Production Secret Generation:</b> Execute <code>python -c \"import secrets; print(secrets.token_hex(32))\"</code> to generate keys for <code>SECRET_KEY</code> and <code>SMS_TOKEN</code>.", styles["Bullet"]),
        Paragraph("<b>2. Database Schema Provisioning:</b> Run <code>python -c \"from backend import db; db.init_db()\"</code> to build the SQLite tables.", styles["Bullet"]),
        Paragraph("<b>3. Initial Owner Provisioning:</b> Launch the server and register the store owner at <code>/register</code>. The system automatically locks owner registration thereafter.", styles["Bullet"]),
        Paragraph("<b>4. Android Gateway Configuration:</b> Set target URL <code>http://&lt;MERCHANT_IP&gt;:5000/api/sms?token=&lt;SMS_TOKEN&gt;</code> (or header <code>X-Token: &lt;SMS_TOKEN&gt;</code>) and enable Local Network Mode in the forwarder.", styles["Bullet"]),
        Paragraph("<b>5. Offline Hash Sealing:</b> At close of business, the owner checks <code>/reports</code>, records the SHA-256 closing hash offline, and runs <code>verify_chain()</code>.", styles["Bullet"]),
    ]
    for s in deploy_steps:
        story.append(s)

    story.append(PageBreak())
    story.append(Paragraph("10.3 Android Hardware Gateway Field Trials (Empirical Validation)", styles["H2"]))
    story.append(Paragraph(
        "During live end-to-end integration testing on the local Wi-Fi subnet (Merchant host <code>192.168.1.3:5000</code>, "
        "Android phone <code>192.168.1.5</code> running <i>Incoming SMS to URL forwarder</i>), "
        "the engineering team logged the following 3-trial validation progression:",
        styles["Body"]
    ))

    trials_data = [
        [
            Paragraph("<b>Trial</b>", styles["TableHead"]),
            Paragraph("<b>Gateway Configuration</b>", styles["TableHead"]),
            Paragraph("<b>HTTP Response</b>", styles["TableHead"]),
            Paragraph("<b>Observed Behavior &amp; Engineering Resolution</b>", styles["TableHead"]),
        ],
        [
            Paragraph("<b>Trial 1</b>", styles["TableCellBold"]),
            Paragraph("Sender: <code>127</code><br/>URL: <code>http://192.168.1.3:5000/api/sms</code><br/>Token: <i>None (omitted)</i>", styles["TableCellCode"]),
            Paragraph("<font color='#c62828'><b>401 Unauthorized</b></font><br/><i>FAILED</i>", styles["TableCellBold"]),
            Paragraph("<b>Security Gate Verified:</b> Server strictly rejected unauthenticated POST request. Proved that unauthenticated third parties cannot inject synthetic payment notifications.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Trial 2</b>", styles["TableCellBold"]),
            Paragraph("Sender: <code>*</code> (Wildcard)<br/>URL: <code>http://192.168.1.3:5000/api/sms</code><br/>Token: <i>None (omitted)</i>", styles["TableCellCode"]),
            Paragraph("<font color='#c62828'><b>401 Unauthorized</b></font><br/><i>FAILED</i>", styles["TableCellBold"]),
            Paragraph("<b>Filter Independence Proved:</b> Changing mobile sender filter from <code>127</code> to wildcard <code>*</code> did not bypass the authentication requirement; request was still rejected with 401.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Trial 3</b>", styles["TableCellBold"]),
            Paragraph("Sender: <code>*</code><br/>URL: <code>http://192.168.1.3:5000/api/sms?token=...</code><br/>Local network mode: <b>ON</b>", styles["TableCellCode"]),
            Paragraph("<font color='#2e7d32'><b>200 OK</b></font><br/><i>SUCCESS</i>", styles["TableCellBold"]),
            Paragraph("<b>Ingestion Operational:</b> Query-string token authenticated successfully, local network bypass active. Test ping returned HTTP 200 and incoming SMS verified on dashboard.", styles["TableCell"]),
        ],
    ]
    trials_table = Table(trials_data, colWidths=[45, 145, 95, 235])
    trials_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CARD]),
    ]))
    story.append(trials_table)
    story.append(Spacer(1, 6))

    live_note = (
        "<b>Live Real-World Validation:</b> Following Trial 3, the team restricted the phone's forwarder to "
        "sender <code>127</code> (acting as a phone-level firewall against non-bank numbers) and executed 4 live Telebirr "
        "transactions. All 4 messages were received, parsed, and verified in real time, triggering the counter audio chime "
        "and extending the SHA-256 ledger to 9 verified blocks (<code>verify_chain()</code> status: OK)."
    )
    story.append(Paragraph(live_note, styles["Body"]))
    story.append(Spacer(1, 6))
    final_callout = (
        "EVALUATOR SUBMISSION INTEGRITY: This technical blueprint accompanies the source code archive submitted for "
        "the INSA Cybersecurity Summer Camp 2026. All 30 automated acceptance tests pass cleanly under pytest, all code excerpts "
        "match repository source files, and all operational limitations are transparently disclosed."
    )
    story.append(callout("INSA 2026 SUBMISSION ATTESTATION", final_callout, styles, kind="green"))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Corrected Technical Blueprint PDF successfully created at {output_path}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "docs")
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, "PPL-Technical-Blueprint.pdf")
    build_pdf(pdf_path)
