"""
WSQ Courseware Generator — User Guide PDF Generator
Generates a comprehensive PDF user guide for the app.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib import colors
import os
import datetime

# ── Colors ──
BLUE = HexColor("#4472C4")
DARK_BLUE = HexColor("#2F5496")
LIGHT_BLUE = HexColor("#D6E4F0")
LIGHT_GRAY = HexColor("#F2F2F2")
DARK_GRAY = HexColor("#404040")
MEDIUM_GRAY = HexColor("#666666")
ACCENT_GREEN = HexColor("#548235")
ACCENT_ORANGE = HexColor("#ED7D31")
ACCENT_RED = HexColor("#C00000")

OUTPUT_PATH = os.path.join("docs", "WSQ_Courseware_Generator_User_Guide.pdf")

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=38,
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica",
        fontSize=16,
        textColor=MEDIUM_GRAY,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=22,
    ))
    styles.add(ParagraphStyle(
        name="CoverDate",
        fontName="Helvetica-Oblique",
        fontSize=12,
        textColor=MEDIUM_GRAY,
        alignment=TA_CENTER,
        spaceBefore=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=DARK_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        leading=26,
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=BLUE,
        spaceBefore=14,
        spaceAfter=6,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name="SubSubHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=DARK_GRAY,
        spaceBefore=10,
        spaceAfter=4,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="BulletText",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=20,
        spaceAfter=3,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="StepText",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=25,
        spaceAfter=4,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="NoteBox",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=MEDIUM_GRAY,
        leftIndent=15,
        rightIndent=15,
        spaceBefore=6,
        spaceAfter=8,
        leading=13,
        backColor=LIGHT_GRAY,
        borderPadding=8,
    ))
    styles.add(ParagraphStyle(
        name="TipBox",
        fontName="Helvetica",
        fontSize=9,
        textColor=ACCENT_GREEN,
        leftIndent=15,
        rightIndent=15,
        spaceBefore=6,
        spaceAfter=8,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        name="TOCEntry",
        fontName="Helvetica",
        fontSize=11,
        textColor=DARK_GRAY,
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=10,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="TOCSubEntry",
        fontName="Helvetica",
        fontSize=10,
        textColor=MEDIUM_GRAY,
        spaceBefore=2,
        spaceAfter=2,
        leftIndent=30,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="FooterStyle",
        fontName="Helvetica",
        fontSize=8,
        textColor=MEDIUM_GRAY,
        alignment=TA_CENTER,
    ))
    return styles


def blue_header_table(text):
    """Create a blue banner header."""
    t = Table([[Paragraph(f"<b>{text}</b>",
        ParagraphStyle("bh", fontName="Helvetica-Bold", fontSize=14, textColor=white, leading=18))
    ]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, -1), white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def info_table(data, col_widths=None):
    """Create a styled info table."""
    if col_widths is None:
        col_widths = [50*mm, 120*mm]
    style = []
    for i, row in enumerate(data):
        if i == 0:
            style.append(("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE))
            style.append(("TEXTCOLOR", (0, 0), (-1, 0), white))
            style.append(("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"))
        else:
            bg = LIGHT_GRAY if i % 2 == 0 else white
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
    style += [
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t


def bullet(text, styles):
    return Paragraph(f"&#8226;  {text}", styles["BulletText"])


def step(number, text, styles):
    return Paragraph(f"<b>Step {number}:</b>  {text}", styles["StepText"])


def note(text, styles):
    return Paragraph(f"<b>Note:</b> {text}", styles["NoteBox"])


def tip(text, styles):
    return Paragraph(f"<b>Tip:</b> {text}", styles["TipBox"])


def build_pdf():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=20*mm,
        bottomMargin=20*mm,
        leftMargin=20*mm,
        rightMargin=20*mm,
        title="WSQ Courseware Generator - User Guide",
        author="Tertiary Infotech Academy Pte Ltd",
    )

    styles = get_styles()
    story = []
    today = datetime.date.today().strftime("%d %B %Y")

    # ══════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 60*mm))

    # Try to add logos
    wsq_logo = "assets/slide_logos/wsq_logo.png"
    streamlit_logo = "assets/slide_logos/streamlit_logo.png"
    company_logo = "company/logo/tertiary_infotech_academy_pte_ltd.jpg"
    logos_exist = all(os.path.exists(f) for f in [wsq_logo, company_logo])
    if logos_exist:
        try:
            logo_row = [
                Image(wsq_logo, width=40*mm, height=28*mm),
            ]
            col_widths = [55*mm]
            if os.path.exists(streamlit_logo):
                logo_row.append(Image(streamlit_logo, width=22*mm, height=22*mm))
                col_widths.append(55*mm)
            else:
                logo_row.append(Paragraph("", styles["BodyText2"]))
                col_widths.append(55*mm)
            logo_row.append(Image(company_logo, width=50*mm, height=18*mm))
            col_widths.append(55*mm)

            logo_table = Table([logo_row], colWidths=col_widths)
            logo_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(logo_table)
            story.append(Spacer(1, 15*mm))
        except:
            pass

    story.append(Paragraph("WSQ Courseware Generator", styles["CoverTitle"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="60%", thickness=2, color=BLUE, spaceAfter=10))
    story.append(Paragraph("Complete User Guide", styles["CoverSubtitle"]))
    story.append(Paragraph("Step-by-Step Instructions for All Features", styles["CoverSubtitle"]))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(f"Version 2.0  |  {today}", styles["CoverDate"]))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Prepared by: Tertiary Infotech Academy Pte Ltd", styles["CoverDate"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════
    story.append(Paragraph("Table of Contents", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=10))

    toc_items = [
        ("1.", "Getting Started", [
            "1.1  Opening the App",
            "1.2  Selecting a Company",
            "1.3  Understanding the Sidebar",
        ]),
        ("2.", "Extract Course Info (Step 1 — Always Start Here)", [
            "2.1  Uploading a Course Proposal",
            "2.2  Entering Course Details",
            "2.3  Reviewing Extracted Data",
        ]),
        ("3.", "Generate AP / FG / LG (Step 2)", [
            "3.1  Selecting Documents to Generate",
            "3.2  Running Generation",
            "3.3  Downloading Documents",
        ]),
        ("4.", "Generate Lesson Plan (Step 3)", [
            "4.1  Generating the Schedule",
            "4.2  Previewing & Downloading",
        ]),
        ("5.", "Generate Assessment (Step 4)", [
            "5.1  Uploading Facilitator Guide (Optional)",
            "5.2  Selecting Assessment Types",
            "5.3  Downloading Assessments",
        ]),
        ("6.", "Generate Slides (Step 5)", [
            "6.1  Generating Slides",
            "6.2  Downloading the Slide Deck",
        ]),
        ("7.", "Generate Brochure (Step 6)", [
            "7.1  Tertiary Courses (URL Only)",
            "7.2  Client Courses (Upload CP)",
            "7.3  Downloading & Clearing",
        ]),
        ("8.", "Convert Documents", [
            "8.1  Convert Assessments",
            "8.2  Convert Courseware",
            "8.3  Convert Lesson Plans",
        ]),
        ("9.", "Courseware Audit", [
            "9.1  Quick Check Mode",
            "9.2  Upload & Check Mode",
        ]),
        ("10.", "Company Management (Settings)", [
            "10.1  Adding a Company",
            "10.2  Editing / Deleting a Company",
        ]),
        ("11.", "Troubleshooting & FAQ", []),
    ]

    for num, title, subs in toc_items:
        story.append(Paragraph(f"<b>{num}</b>  {title}", styles["TOCEntry"]))
        for sub in subs:
            story.append(Paragraph(sub, styles["TOCSubEntry"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 1 — GETTING STARTED
    # ══════════════════════════════════════════════
    story.append(blue_header_table("1. Getting Started"))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("1.1  Opening the App", styles["SubHeader"]))
    story.append(Paragraph(
        "The WSQ Courseware Generator runs as a web application in your browser. "
        "To access the app:", styles["BodyText2"]))
    story.append(step(1, "Open <b>Google Chrome</b> (or any web browser).", styles))
    story.append(step(2, "Go to the <b>app link</b> provided to you by your administrator.", styles))
    story.append(step(3, "The app will load and you can start using it immediately.", styles))
    story.append(note(
        "You do not need to install anything. The app runs entirely in your web browser.",
        styles))

    story.append(Paragraph("1.2  Selecting a Company", styles["SubHeader"]))
    story.append(Paragraph(
        "At the top of the left sidebar, you will see a <b>Company dropdown</b>. "
        "This determines which company's branding (logo, UEN, address) appears on all generated documents.",
        styles["BodyText2"]))
    story.append(bullet("Select the correct company <b>before</b> generating any documents.", styles))
    story.append(bullet("The default is 'Tertiary Infotech Academy Pte Ltd'.", styles))
    story.append(bullet("To add or edit companies, see <b>Section 10: Company Management</b>.", styles))

    story.append(Paragraph("1.3  Understanding the Sidebar", styles["SubHeader"]))
    story.append(Paragraph(
        "The left sidebar contains the main navigation menu with 8 pages. "
        "Below the menu, you will find:", styles["BodyText2"]))
    story.append(bullet("<b>Companies button</b> — Opens company management settings.", styles))
    story.append(bullet("<b>Agent Status</b> — Shows if any AI background job is running.", styles))
    story.append(Spacer(1, 4*mm))
    story.append(note(
        "The recommended workflow follows the menu order from top to bottom: "
        "Extract Course Info → Generate AP/FG/LG → Lesson Plan → Assessment → Slides → Brochure → Audit.",
        styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 2 — EXTRACT COURSE INFO
    # ══════════════════════════════════════════════
    story.append(blue_header_table("2. Extract Course Info"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "This is <b>always the first step</b>. You must extract course information from an approved "
        "Course Proposal (CP) before generating any courseware documents. The extracted data is "
        "automatically shared across all other pages.",
        styles["BodyText2"]))

    story.append(Paragraph("2.1  Uploading a Course Proposal", styles["SubHeader"]))
    story.append(step(1, "Navigate to <b>Extract Course Info</b> in the sidebar.", styles))
    story.append(step(2, "Click the <b>file upload area</b> (drag-and-drop also works).", styles))
    story.append(step(3, "Upload your Course Proposal file. Supported formats:", styles))
    story.append(bullet("<b>.docx</b> — Word document (most common)", styles))
    story.append(bullet("<b>.xlsx</b> — Excel spreadsheet", styles))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph("2.2  Entering Course Details", styles["SubHeader"]))
    story.append(step(1, "Enter the <b>Course Reference Code (TGS)</b> — e.g., TGS-2024001234. "
        "This code appears on all generated documents.", styles))
    story.append(step(2, "(Optional) Enter the <b>Course URL</b> — the link to the course webpage. "
        "This is only needed if you plan to generate a brochure later.", styles))
    story.append(step(3, "Click the <b>Extract</b> button to start processing.", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "The system uses AI (Claude Agent) to interpret the Course Proposal and extract structured data. "
        "This runs in the background — you will see a <b>spinning indicator</b> while it processes. "
        "You can wait on this page or navigate away; the extraction will continue.",
        styles["BodyText2"]))

    story.append(Paragraph("2.3  Reviewing Extracted Data", styles["SubHeader"]))
    story.append(Paragraph(
        "Once extraction completes, you will see a <b>success card</b> showing:", styles["BodyText2"]))
    story.append(bullet("Course Title", styles))
    story.append(bullet("Number of Learning Units (LUs)", styles))
    story.append(bullet("Number of Topics", styles))
    story.append(bullet("Assessment Methods", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Below the success card, expandable tables show the full extracted data: "
        "course overview, learning outcomes, topics with bullet points, and assessment details. "
        "<b>Review this data carefully</b> — it forms the basis for all generated documents.",
        styles["BodyText2"]))
    story.append(tip(
        "If the company name in the CP matches a company in the database, the sidebar company "
        "dropdown will auto-select it for you.", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 3 — GENERATE AP / FG / LG
    # ══════════════════════════════════════════════
    story.append(blue_header_table("3. Generate AP / FG / LG"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "This page generates three core WSQ courseware documents using AI agents:",
        styles["BodyText2"]))
    story.append(bullet("<b>Assessment Plan (AP)</b> — Outlines assessment strategy, methods, and criteria.", styles))
    story.append(bullet("<b>Assessment Summary Record (ASR)</b> — Auto-generated alongside the AP.", styles))
    story.append(bullet("<b>Facilitator Guide (FG)</b> — Instructor manual with lesson content and activities.", styles))
    story.append(bullet("<b>Learner Guide (LG)</b> — Student handbook with learning content.", styles))

    story.append(Paragraph("3.1  Selecting Documents to Generate", styles["SubHeader"]))
    story.append(step(1, "Navigate to <b>Generate AP/FG/LG</b> in the sidebar.", styles))
    story.append(step(2, "You will see the extracted course info summary at the top. "
        "If it says 'No course info loaded', go back to Step 2 first.", styles))
    story.append(step(3, "Use the <b>checkboxes</b> to select which documents to generate:", styles))
    story.append(bullet("Learning Guide (LG) — checked by default", styles))
    story.append(bullet("Assessment Plan (AP) — checked by default", styles))
    story.append(bullet("Facilitator Guide (FG) — checked by default", styles))
    story.append(note("You can uncheck any document you don't need. For example, if you only need the LG.", styles))

    story.append(Paragraph("3.2  Running Generation", styles["SubHeader"]))
    story.append(step(1, "Click the <b>Generate Documents</b> button.", styles))
    story.append(step(2, "A spinner will appear as each document is being generated by the AI agent.", styles))
    story.append(step(3, "Generation takes 1-3 minutes per document depending on course complexity.", styles))
    story.append(Paragraph(
        "The system automatically enriches the data with TSC (Training & Skills Competency) fields, "
        "proficiency levels, and sector information before generating.",
        styles["BodyText2"]))

    story.append(Paragraph("3.3  Downloading Documents", styles["SubHeader"]))
    story.append(Paragraph("Once generation completes, you have two download options:", styles["BodyText2"]))
    story.append(bullet("<b>Individual downloads</b> — Click the download button next to each document.", styles))
    story.append(bullet("<b>Bulk download</b> — Click <b>Download All as ZIP</b> to get all documents in one file.", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Files are named as follows:", styles["BodyText2"]))
    story.append(bullet("LG_[TGSCode]_[CourseName].docx", styles))
    story.append(bullet("Assessment_Plan_[TGSCode]_[CourseName].docx", styles))
    story.append(bullet("Assessment_Summary_Record_[TGSCode]_[CourseName].docx", styles))
    story.append(bullet("FG_[TGSCode]_[CourseName].docx", styles))
    story.append(tip(
        "All generated documents are also automatically saved to the Courseware/ folder in the project directory.",
        styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 4 — GENERATE LESSON PLAN
    # ══════════════════════════════════════════════
    story.append(blue_header_table("4. Generate Lesson Plan"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "The Lesson Plan is generated <b>instantly</b> using a pure Python scheduling algorithm — "
        "no AI processing is needed. It creates a day-by-day timetable for the course.",
        styles["BodyText2"]))

    story.append(Paragraph("4.1  Generating the Schedule", styles["SubHeader"]))
    story.append(step(1, "Navigate to <b>Generate Lesson Plan</b> in the sidebar.", styles))
    story.append(step(2, "The extracted course info is auto-loaded. Verify the course details at the top.", styles))
    story.append(step(3, "Click <b>Generate Lesson Plan</b>.", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("The schedule follows these rules:", styles["BodyText2"]))
    story.append(bullet("Daily hours: <b>9:00 AM – 6:00 PM</b>", styles))
    story.append(bullet("Lunch break: <b>12:30 PM – 1:15 PM</b> (45 minutes, fixed)", styles))
    story.append(bullet("Assessment: <b>4:00 PM – 6:00 PM</b> on the last day only", styles))
    story.append(bullet("Topics are distributed evenly across available time", styles))
    story.append(bullet("Breaks fill all remaining gaps to ensure a full 9am–6pm day", styles))

    story.append(Paragraph("4.2  Previewing & Downloading", styles["SubHeader"]))
    story.append(Paragraph(
        "After generation, you will see:", styles["BodyText2"]))
    story.append(bullet("<b>Statistics</b> — Total days, minutes per topic, instructional hours, assessment hours.", styles))
    story.append(bullet("<b>Day-by-day preview</b> — Expandable sections showing each day's timetable.", styles))
    story.append(bullet("<b>Download button</b> — Downloads as LP_[TGSCode]_[CourseName]_v1.docx", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 5 — GENERATE ASSESSMENT
    # ══════════════════════════════════════════════
    story.append(blue_header_table("5. Generate Assessment"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Generate assessment question papers in standard WSQ format. "
        "Supports 9 assessment types.",
        styles["BodyText2"]))

    # Assessment types table
    assess_data = [
        ["Code", "Assessment Type", "Description"],
        ["WA (SAQ)", "Written Assessment", "Short answer questions testing knowledge"],
        ["PP", "Practical Performance", "Hands-on task demonstration"],
        ["CS", "Case Study", "Scenario-based analysis questions"],
        ["OQ", "Oral Questioning", "Verbal Q&A assessment"],
        ["OI", "Oral Interview", "Structured interview assessment"],
        ["DEM", "Demonstration", "Live skill demonstration"],
        ["RP", "Role Play", "Simulated scenario performance"],
        ["PRJ", "Project", "Extended project-based assessment"],
        ["ASGN", "Assignment", "Written assignment submission"],
    ]
    story.append(info_table(assess_data, col_widths=[30*mm, 45*mm, 95*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("5.1  Uploading Facilitator Guide (Optional)", styles["SubHeader"]))
    story.append(Paragraph(
        "You can optionally upload the Facilitator Guide (FG) to extract Knowledge (K) and "
        "Ability (A) statements. This helps the AI map assessment questions to specific K/A items.",
        styles["BodyText2"]))
    story.append(step(1, "Navigate to <b>Generate Assessment</b> in the sidebar.", styles))
    story.append(step(2, "(Optional) Upload the FG .docx file to extract K/A statements.", styles))

    story.append(Paragraph("5.2  Selecting Assessment Types", styles["SubHeader"]))
    story.append(step(1, "Use the <b>checkboxes</b> to select which assessment types to generate.", styles))
    story.append(step(2, "Click <b>Generate Assessments</b>.", styles))
    story.append(step(3, "The AI agent creates questions, expected answers, and K/A mappings for each type.", styles))

    story.append(Paragraph("5.3  Downloading Assessments", styles["SubHeader"]))
    story.append(bullet("<b>Individual downloads</b> — Each assessment type has its own download button.", styles))
    story.append(bullet("<b>Bulk download</b> — Download all as assessments_[CourseName].zip", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 6 — GENERATE SLIDES
    # ══════════════════════════════════════════════
    story.append(blue_header_table("6. Generate Slides"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Generates a presentation slide deck with infographics for the course content. "
        "The system uses a multi-agent pipeline to create content-rich slides with visuals.",
        styles["BodyText2"]))

    story.append(Paragraph("6.1  Generating Slides", styles["SubHeader"]))
    story.append(step(1, "Navigate to <b>Generate Slides</b> in the sidebar.", styles))
    story.append(step(2, "Ensure course info has been extracted (Section 2).", styles))
    story.append(step(3, "Click <b>Generate Slides</b> to start the multi-agent pipeline.", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("The pipeline runs through 5 phases:", styles["BodyText2"]))
    story.append(bullet("<b>Phase 1: Research</b> — Researches topic content", styles))
    story.append(bullet("<b>Phase 2: Content</b> — Generates slide content blocks", styles))
    story.append(bullet("<b>Phase 3: Editor</b> — Refines and structures content", styles))
    story.append(bullet("<b>Phase 4: Infographic</b> — Creates visual infographics", styles))
    story.append(bullet("<b>Phase 5: Assembly</b> — Builds the final PPTX file", styles))

    story.append(Paragraph("6.2  Downloading the Slide Deck", styles["SubHeader"]))
    story.append(Paragraph(
        "Once complete, use the <b>Download</b> button to save the PPTX presentation file. "
        "The slide deck includes company branding, WSQ logos, and topic infographics.",
        styles["BodyText2"]))
    story.append(Spacer(1, 2*mm))

    # Slide count table
    slide_data = [
        ["Course Duration", "Target Slide Count"],
        ["1-day course", "100 slides"],
        ["2-day course", "140 slides"],
        ["3-day course", "210 slides"],
        ["4-day course", "250 slides"],
    ]
    story.append(info_table(slide_data, col_widths=[60*mm, 60*mm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 7 — GENERATE BROCHURE
    # ══════════════════════════════════════════════
    story.append(blue_header_table("7. Generate Brochure"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Creates a marketing brochure PDF for any WSQ course. There are <b>two modes</b> depending on "
        "whether the course is a Tertiary Infotech course or a client course.",
        styles["BodyText2"]))

    story.append(Paragraph("7.1  Tertiary Courses (URL Only)", styles["SubHeader"]))
    story.append(Paragraph(
        "For Tertiary Infotech courses, the brochure is generated entirely from the course webpage:",
        styles["BodyText2"]))
    story.append(step(1, "Navigate to <b>Generate Brochure</b> in the sidebar.", styles))
    story.append(step(2, "Leave the <b>Client Course</b> upload area empty.", styles))
    story.append(step(3, "Paste the <b>Course URL</b> (e.g., from MySkillsFuture or tertiarycourses.com).", styles))
    story.append(step(4, "Click <b>Generate Brochure</b>.", styles))
    story.append(Paragraph(
        "The system scrapes all course details (title, topics, fees, requirements) from the URL "
        "and generates a branded PDF with the Tertiary Infotech logo and contact details.",
        styles["BodyText2"]))

    story.append(Paragraph("7.2  Client Courses (Upload CP)", styles["SubHeader"]))
    story.append(Paragraph(
        "For client courses (e.g., Laures, other training providers), MySkillsFuture has limited info. "
        "Instead, upload the client's Course Proposal:",
        styles["BodyText2"]))
    story.append(step(1, "Navigate to <b>Generate Brochure</b> in the sidebar.", styles))
    story.append(step(2, "Upload the client's <b>Course Proposal</b> (.docx or .xlsx).", styles))
    story.append(step(3, "Enter the <b>TGS Reference Code</b> (e.g., TGS-2026062163).", styles))
    story.append(step(4, "(Optional) Paste the <b>Course URL</b> — used to fetch the estimated payable fee.", styles))
    story.append(step(5, "Click <b>Generate Brochure</b>.", styles))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("The system will automatically:", styles["BodyText2"]))
    story.append(bullet("<b>Extract course data</b> from the CP (title, topics, learning outcomes, description).", styles))
    story.append(bullet("<b>Detect the company name</b> from the CP and look up the company in the database.", styles))
    story.append(bullet("<b>Replace all branding</b> — company name, logo, address, email from the database.", styles))
    story.append(bullet("<b>Fetch the estimated fee</b> from the URL (if provided).", styles))
    story.append(bullet("<b>Remove Tertiary-specific content</b> — phone, WhatsApp, registration link, funding table.", styles))
    story.append(note(
        "The client company must be added in Company Management (Section 10) with their address, email, "
        "and logo BEFORE generating the brochure. Otherwise the brochure will have missing details.",
        styles))

    story.append(Paragraph("7.3  Downloading & Clearing", styles["SubHeader"]))
    story.append(bullet("<b>Download PDF</b> — Click to save the brochure.", styles))
    story.append(bullet("<b>Clear & Generate New</b> — Click to reset and upload a new CP for the next course.", styles))
    story.append(tip(
        "When generating brochures for multiple client courses, use the Clear button after each one "
        "to ensure fresh data for the next course.", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 8 — CONVERT DOCUMENTS
    # ══════════════════════════════════════════════
    story.append(blue_header_table("8. Convert Documents"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Convert existing (non-standard) documents into standardized WSQ format. "
        "This page has <b>three tabs</b>:",
        styles["BodyText2"]))

    story.append(Paragraph("8.1  Convert Assessments", styles["SubHeader"]))
    story.append(step(1, "Go to the <b>Convert Assessment</b> tab.", styles))
    story.append(step(2, "Upload one or more assessment .docx files (question papers, answer keys).", styles))
    story.append(step(3, "Click <b>Convert</b>. The AI extracts questions, answers, and K/A mappings.", styles))
    story.append(step(4, "Download the converted files as a ZIP — each file is in standard WSQ format.", styles))

    story.append(Paragraph("8.2  Convert Courseware", styles["SubHeader"]))
    story.append(step(1, "Go to the <b>Convert Courseware</b> tab.", styles))
    story.append(step(2, "Upload AP, FG, LG, or ASR documents (.docx).", styles))
    story.append(step(3, "Click <b>Convert</b> to reformat into WSQ standard.", styles))

    story.append(Paragraph("8.3  Convert Lesson Plans", styles["SubHeader"]))
    story.append(step(1, "Go to the <b>Convert Lesson Plan</b> tab.", styles))
    story.append(step(2, "Upload existing lesson plan .docx files.", styles))
    story.append(step(3, "Click <b>Convert</b> to restructure into the standard timetable format.", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 9 — COURSEWARE AUDIT
    # ══════════════════════════════════════════════
    story.append(blue_header_table("9. Courseware Audit"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "The audit tool cross-checks your generated courseware documents against the "
        "Course Proposal (source of truth) to catch any mismatches or errors.",
        styles["BodyText2"]))

    story.append(Paragraph("9.1  Quick Check Mode", styles["SubHeader"]))
    story.append(Paragraph(
        "If you have just generated documents on the AP/FG/LG page, you can use <b>Quick Check</b>:",
        styles["BodyText2"]))
    story.append(step(1, "Navigate to <b>Courseware Audit</b> in the sidebar.", styles))
    story.append(step(2, "Click <b>Quick Check</b> — it automatically audits the documents "
        "you just generated using the session data.", styles))
    story.append(step(3, "Review the audit table: green checkmarks (✓) for matches, "
        "red crosses (✗) for mismatches.", styles))

    story.append(Paragraph("9.2  Upload & Check Mode", styles["SubHeader"]))
    story.append(Paragraph(
        "For auditing existing documents (not just generated ones):",
        styles["BodyText2"]))
    story.append(step(1, "Upload the <b>Course Proposal</b> (.docx, .xlsx, or .pdf).", styles))
    story.append(step(2, "Upload the <b>courseware documents</b> to audit (AP, FG, LG, LP).", styles))
    story.append(step(3, "Click <b>Audit</b>. The AI compares fields across all documents.", styles))
    story.append(step(4, "Review the results table showing: field name, CP value, document value, and status.", styles))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Fields checked include:", styles["BodyText2"]))
    story.append(bullet("Course title, TSC code, TSC title", styles))
    story.append(bullet("Learning outcomes and topics", styles))
    story.append(bullet("Assessment methods and durations", styles))
    story.append(bullet("Organization name and UEN", styles))
    story.append(bullet("Proficiency levels and credit hours", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 10 — COMPANY MANAGEMENT
    # ══════════════════════════════════════════════
    story.append(blue_header_table("10. Company Management (Settings)"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Manage the training provider companies whose branding appears on generated documents.",
        styles["BodyText2"]))

    story.append(Paragraph("10.1  Adding a Company", styles["SubHeader"]))
    story.append(step(1, "Click the <b>Companies</b> button at the bottom of the sidebar.", styles))
    story.append(step(2, "Click <b>Add New Company</b>.", styles))
    story.append(step(3, "Fill in the details:", styles))
    story.append(bullet("<b>Company Name</b> — Full legal name", styles))
    story.append(bullet("<b>UEN</b> — Unique Entity Number (e.g., 20120096W)", styles))
    story.append(bullet("<b>Address</b> — Registered address", styles))
    story.append(bullet("<b>Email</b> — Contact email", styles))
    story.append(bullet("<b>Phone</b> — Contact number", styles))
    story.append(step(4, "Upload the <b>company logo</b> (PNG or JPG). This appears on all documents.", styles))
    story.append(step(5, "Click <b>Save</b>.", styles))

    story.append(Paragraph("10.2  Editing / Deleting a Company", styles["SubHeader"]))
    story.append(bullet("<b>Edit:</b> Click the edit button next to any company to update its details or logo.", styles))
    story.append(bullet("<b>Delete:</b> Click delete — the system auto-backs up the company data "
        "before removing it (saved in company/deleted_companies/).", styles))
    story.append(bullet("<b>Search:</b> Use the search bar to find companies by name, UEN, or address.", styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SECTION 11 — TROUBLESHOOTING
    # ══════════════════════════════════════════════
    story.append(blue_header_table("11. Troubleshooting & FAQ"))
    story.append(Spacer(1, 4*mm))

    faq_data = [
        ["Problem", "Solution"],
        [
            "App won't load / page error",
            "Refresh the page (F5 or Ctrl+R). If it still doesn't load, "
            "contact your administrator to check if the app is running."
        ],
        [
            "'No course info loaded' warning",
            "Go to Extract Course Info (page 1) and upload a Course Proposal first. "
            "All other pages depend on this."
        ],
        [
            "Generation is stuck / spinning forever",
            "Check the Agent Status in the sidebar. If a job is stuck, refresh the page (F5) "
            "and try generating again."
        ],
        [
            "Generated document has wrong company name",
            "Check the Company dropdown in the sidebar — make sure the correct company is selected "
            "before generating."
        ],
        [
            "Downloaded DOCX looks wrong / formatting issues",
            "Open the file in Microsoft Word (not Google Docs or LibreOffice) for best results. "
            "WSQ templates are optimized for MS Word."
        ],
        [
            "Brochure generation fails",
            "Ensure the Course URL is valid and accessible. Some websites block automated scraping."
        ],
        [
            "Slides have fewer than expected",
            "The system auto-pads to hit the target count. If still short, try regenerating."
        ],
        [
            "Need to re-extract course info",
            "Simply upload the CP again on the Extract Course Info page. "
            "It will overwrite the previous extraction."
        ],
    ]

    # Build FAQ table with wrapping
    faq_styled = []
    ps_header = ParagraphStyle("faqh", fontName="Helvetica-Bold", fontSize=9, textColor=white, leading=12)
    ps_cell = ParagraphStyle("faqc", fontName="Helvetica", fontSize=9, textColor=DARK_GRAY, leading=12)
    for i, row in enumerate(faq_data):
        if i == 0:
            faq_styled.append([Paragraph(row[0], ps_header), Paragraph(row[1], ps_header)])
        else:
            faq_styled.append([Paragraph(row[0], ps_cell), Paragraph(row[1], ps_cell)])
    story.append(info_table(faq_styled, col_widths=[50*mm, 120*mm]))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=10))
    story.append(Spacer(1, 4*mm))

    # ── Workflow Summary ──
    story.append(Paragraph("Quick Reference — Recommended Workflow", styles["SubHeader"]))
    story.append(Spacer(1, 2*mm))

    workflow_data = [
        ["Step", "Page", "Action", "Output"],
        ["1", "Extract Course Info", "Upload CP + enter TGS code", "Extracted JSON (session)"],
        ["2", "Generate AP/FG/LG", "Select docs → Generate", "AP, ASR, FG, LG (.docx)"],
        ["3", "Generate Lesson Plan", "Click Generate", "LP (.docx)"],
        ["4", "Generate Assessment", "Select types → Generate", "Assessment papers (.docx)"],
        ["5", "Generate Slides", "Click Generate", "Slide deck (.pptx)"],
        ["6", "Generate Brochure", "URL (Tertiary) or CP (Client)", "Brochure (.pdf)"],
        ["7", "Courseware Audit", "Quick Check or Upload", "Audit report"],
    ]
    story.append(info_table(workflow_data, col_widths=[15*mm, 42*mm, 52*mm, 52*mm]))

    story.append(Spacer(1, 15*mm))
    story.append(HRFlowable(width="40%", thickness=1, color=MEDIUM_GRAY, spaceAfter=6))
    story.append(Paragraph(
        f"WSQ Courseware Generator User Guide  |  Version 2.0  |  {today}",
        styles["FooterStyle"]))
    story.append(Paragraph(
        "© Tertiary Infotech Academy Pte Ltd. All Rights Reserved.",
        styles["FooterStyle"]))

    # ── Build ──
    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_pdf()
    print(f"Done! File saved to: {path}")
