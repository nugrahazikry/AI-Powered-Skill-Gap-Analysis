import os
import re
import tempfile
import shutil
import traceback
import html
import time
import uuid
import threading
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, Response
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth
from main import run_pipeline, run_pipeline_with_progress
from agent_function.agent_4_recommendation_report import recommendation_report_agent

app = FastAPI(title="AI-Powered Skill Gap Analysis")

ANALYSIS_STAGES = [
    {
        "key": "agent_1",
        "index": 1,
        "heading": "Reading your CV",
        "label": "Parsing your CV",
        "subdetail": "Extracting your work experience, education, projects, and qualifications from the uploaded document",
    },
    {
        "key": "agent_2",
        "index": 2,
        "heading": "Mapping your skills",
        "label": "Classifying your skills",
        "subdetail": "Categorizing each skill as explicitly stated or implicitly demonstrated through your experience",
    },
    {
        "key": "agent_3",
        "index": 3,
        "heading": "Researching the market",
        "label": "Analyzing job market",
        "subdetail": "Searching live job market sources to identify what skills and tools employers demand for your target role",
    },
    {
        "key": "agent_4",
        "index": 4,
        "heading": "Building your report",
        "label": "Generating recommendations",
        "subdetail": "Comparing your skill profile against market demand and writing a personalized gap analysis with action steps",
    },
]
STAGE_MAP = {s["key"]: s for s in ANALYSIS_STAGES}

_JOBS_LOCK = threading.Lock()
_JOBS = {}


def _safe_print_traceback(tb: str):
    """Print traceback safely on Windows consoles with non-UTF8 encoding."""
    try:
        print(tb)
    except UnicodeEncodeError:
        print(tb.encode("ascii", errors="backslashreplace").decode("ascii"))


def _strip_debug(d: dict) -> dict:
    """Remove large debug-only fields that bloat API responses."""
    return {k: v for k, v in (d or {}).items() if k not in ("_raw", "_raw_input")}


def _build_response_data(result: dict) -> dict:
    return {
        "agent_1_cv_parsing": _strip_debug(result.get("agent_1_cv_parsing", {})),
        "agent_2_specialize_skills": _strip_debug(result.get("agent_2_specialize_skills", {})),
        "agent_3_market_intelligence": result.get("agent_3_market_intelligence", {}),
        "agent_4_recommendation_report": result.get("agent_4_recommendation_report", {}),
        "timings_ms": result.get("timings_ms", {}),
    }


def _update_job(job_id: str, **kwargs):
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        job.update(kwargs)
        job["updated_at"] = int(time.time() * 1000)


def _run_analysis_job(job_id: str, tmp_path: str, role: str):
    try:
        _update_job(job_id, status="running")
        total_start = time.perf_counter()

        def _on_stage(stage_key: str, status: str, payload: dict):
            meta = STAGE_MAP.get(stage_key, {})
            if status == "running":
                _update_job(
                    job_id,
                    stage_key=stage_key,
                    stage_index=meta.get("index", 0),
                    stage_heading=meta.get("heading", ""),
                    stage_label=meta.get("label", ""),
                    stage_subdetail=meta.get("subdetail", ""),
                    stage_status="running",
                )
            elif status == "completed":
                with _JOBS_LOCK:
                    job = _JOBS.get(job_id)
                    if not job:
                        return
                    stage_timings = dict(job.get("timings_ms", {}))
                    if payload and payload.get("elapsed_ms") is not None:
                        stage_timings[stage_key] = int(payload["elapsed_ms"])
                    job["timings_ms"] = stage_timings
                _update_job(job_id, stage_status="completed")

        result = run_pipeline_with_progress(cv_path=tmp_path, role=role, on_stage=_on_stage)
        total_ms = int((time.perf_counter() - total_start) * 1000)

        response_data = _build_response_data(result)
        _update_job(
            job_id,
            status="completed",
            stage_key="agent_4",
            stage_index=4,
            stage_heading=STAGE_MAP["agent_4"]["heading"],
            stage_label=STAGE_MAP["agent_4"]["label"],
            stage_subdetail=STAGE_MAP["agent_4"]["subdetail"],
            stage_status="completed",
            result=response_data,
            total_elapsed_ms=total_ms,
        )
    except Exception as e:
        tb = traceback.format_exc()
        _safe_print_traceback(tb)
        _update_job(job_id, status="error", error=str(e), traceback=tb)
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def _listify(value):
    if isinstance(value, list):
        return value
    return []


def _safe_text(value, default="—"):
    text = "" if value is None else str(value).strip()
    return text if text else default


def _source_content_length(source: dict) -> int:
    """Estimate useful source content size using extracted narrative fields."""
    if not isinstance(source, dict):
        return 0
    parts = [
        _safe_text(source.get("title"), ""),
        _safe_text(source.get("role_overview"), ""),
    ]
    list_fields = [
        "key_responsibilities",
        "demanded_skills",
        "soft_skills",
        "tools_software",
        "certifications",
        "requirements",
    ]
    for key in list_fields:
        parts.extend([_safe_text(item, "") for item in _listify(source.get(key))])
    return len(" ".join([p for p in parts if p]).strip())


def _select_top_sources(sources: list, max_count: int = 12, min_chars: int = 200) -> list:
    """
    Prefer sources with richer content (>= min_chars), max max_count total.
    If total sources are <= max_count, include short sources but place them last.
    """
    normalized = [s for s in _listify(sources) if isinstance(s, dict)]
    if not normalized:
        return []

    long_sources = [s for s in normalized if _source_content_length(s) >= min_chars]
    short_sources = [s for s in normalized if _source_content_length(s) < min_chars]

    if len(normalized) <= max_count:
        return (long_sources + short_sources)[:max_count]
    return long_sources[:max_count]


def _build_report_pdf(analysis: dict, role: str = "") -> bytes:
    styles = getSampleStyleSheet()
    page_bg = colors.HexColor("#eef2f8")
    title_color = colors.HexColor("#0f172a")
    subtitle_color = colors.HexColor("#334155")
    border_color = colors.HexColor("#d1dce8")
    white = colors.white

    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Title"],
        fontSize=21,
        leading=25,
        alignment=TA_CENTER,
        textColor=title_color,
        spaceAfter=12,
    )
    role_style = ParagraphStyle(
        "PdfRole",
        parent=styles["BodyText"],
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=subtitle_color,
        spaceAfter=14,
    )
    agent_style = ParagraphStyle(
        "PdfAgent",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=title_color,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "PdfHeading",
        parent=styles["Heading3"],
        fontSize=12.5,
        leading=16,
        textColor=title_color,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "PdfBody",
        parent=styles["BodyText"],
        fontSize=10.2,
        leading=14.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "PdfBullet",
        parent=body_style,
        alignment=TA_LEFT,
        leftIndent=0,
        firstLineIndent=0,
        spaceAfter=2,
    )
    ats_change_style = ParagraphStyle(
        "PdfAtsChange",
        parent=styles["BodyText"],
        fontSize=10.2,
        leading=14.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=1,
    )
    meta_style = ParagraphStyle(
        "PdfMeta",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=subtitle_color,
        spaceAfter=3,
    )

    def p(text, style=body_style):
        return Paragraph(html.escape(_safe_text(text)).replace("\n", "<br/>"), style)

    content_width = A4[0] - 64

    def panel(title, header_bg, body_flowables):
        if not isinstance(body_flowables, list):
            body_flowables = [body_flowables]
        if not body_flowables:
            body_flowables = [p("No data available.")]

        # IMPORTANT: Keep each flowable in its own row so long sections can split
        # across pages. A single giant row triggers ReportLab LayoutError.
        rows = [[Paragraph(html.escape(title), heading_style)]]
        for flow in body_flowables:
            rows.append([flow])

        table = Table(
            rows,
            colWidths=[content_width],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                    ("BACKGROUND", (0, 1), (-1, -1), white),
                    ("BOX", (0, 0), (-1, -1), 0.9, border_color),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.8, border_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 1), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def add_bullets_flow(items):
        vals = _listify(items)
        if not vals:
            return [p("No data available.")]
        flows = []
        for item in vals:
            flows.append(p(f"• {_safe_text(item)}", bullet_style))
        return flows

    class ChipCloudFlowable(Flowable):
        """Draws wrapped rounded chips, similar to web tag bubbles."""

        def __init__(self, labels, width, bg_color, text_color, border_color):
            super().__init__()
            self.labels = labels
            self.width = width
            self.bg_color = bg_color
            self.text_color = text_color
            self.border_color = border_color
            self.font_name = "Helvetica"
            self.font_size = 9
            self.pad_x = 10
            self.chip_h = 20
            self.gap_x = 10
            self.gap_y = 10
            self._layout = []
            self._height = 0

        def wrap(self, availWidth, _availHeight):
            usable_width = min(self.width, availWidth)
            rows = []
            current = []
            row_w = 0.0
            for label in self.labels:
                text = _safe_text(label, "").strip()
                if not text:
                    continue
                chip_w = min(usable_width, stringWidth(text, self.font_name, self.font_size) + (self.pad_x * 2))
                needed = chip_w if not current else chip_w + self.gap_x
                if current and (row_w + needed > usable_width):
                    rows.append(current)
                    current = []
                    row_w = 0.0
                current.append((text, chip_w))
                row_w += needed
            if current:
                rows.append(current)
            self._layout = rows
            if not rows:
                self._height = 0
            else:
                self._height = (len(rows) * self.chip_h) + ((len(rows) - 1) * self.gap_y)
            return usable_width, self._height

        def draw(self):
            if not self._layout:
                return
            y = self._height - self.chip_h
            canvas = self.canv
            for row in self._layout:
                x = 0.0
                for text, chip_w in row:
                    canvas.setFillColor(self.bg_color)
                    canvas.setStrokeColor(self.border_color)
                    canvas.setLineWidth(0.8)
                    radius = self.chip_h / 2.0
                    canvas.roundRect(x, y, chip_w, self.chip_h, radius, stroke=1, fill=1)
                    canvas.setFillColor(self.text_color)
                    canvas.setFont(self.font_name, self.font_size)
                    canvas.drawString(x + self.pad_x, y + 6.2, text)
                    x += chip_w + self.gap_x
                y -= (self.chip_h + self.gap_y)

    def chip_rows_flow(items, bg_color, text_color, border_color):
        vals = [_safe_text(item, "").strip() for item in _listify(items)]
        vals = [v for v in vals if v]
        if not vals:
            return [p("No data available.")]
        return [ChipCloudFlowable(vals, content_width - 24, bg_color, text_color, border_color)]

    analysis = analysis or {}
    a1 = analysis.get("agent_1_cv_parsing", {}) or {}
    a2 = analysis.get("agent_2_specialize_skills", {}) or {}
    a3 = analysis.get("agent_3_market_intelligence", {}) or {}
    a4 = analysis.get("agent_4_recommendation_report", {}) or {}

    story = []
    story.append(Paragraph("Skill Gap Analysis Report", title_style))
    if role:
        story.append(Paragraph(html.escape(f"Target role: {role}"), role_style))
    else:
        story.append(Spacer(1, 4))

    # Agent 1 -------------------------------------------------
    story.append(Paragraph("Agent 1 - CV Parsing", agent_style))
    story.append(p("Work history, education, certifications, and projects extracted from your CV.", meta_style))
    story.append(Spacer(1, 8))
    story.append(panel("CV Summary", colors.HexColor("#eef2ff"), [p(a1.get("summary", "No summary available."))]))
    story.append(Spacer(1, 8))

    exp_items = _listify(a1.get("experience"))
    exp_flows = []
    if not exp_items:
        exp_flows.append(p("No experience data available."))
    for idx, exp in enumerate(exp_items, start=1):
        title = _safe_text(exp.get("title"), "Untitled role")
        company = _safe_text(exp.get("company"), "Unknown company")
        period = " - ".join([x for x in [_safe_text(exp.get("period_start"), ""), _safe_text(exp.get("period_end"), "")] if x]).strip(" -")
        line = f"{idx}. {title} | {company}"
        if period:
            line += f" | {period}"
        exp_flows.append(p(line, heading_style))
        descs = _listify(exp.get("descriptions"))
        if not descs:
            exp_flows.append(p("• No job description provided.", bullet_style))
        else:
            for d in descs:
                exp_flows.append(p(f"• {_safe_text(d)}", bullet_style))
        exp_flows.append(Spacer(1, 4))
    story.append(panel("Work Experience", colors.HexColor("#eef2ff"), exp_flows))
    story.append(Spacer(1, 8))

    # 2x info blocks represented as cards
    edu_items = _listify(a1.get("education"))
    edu_flows = []
    if not edu_items:
        edu_flows.append(p("No education data available."))
    else:
        for idx, edu in enumerate(edu_items, start=1):
            period = " - ".join([x for x in [_safe_text(edu.get("period_start"), ""), _safe_text(edu.get("period_end"), "")] if x]).strip(" -")
            gpa = _safe_text(edu.get("gpa"), "")
            line = f"{idx}. {_safe_text(edu.get('degree'))} | {_safe_text(edu.get('institution'))}"
            if period:
                line += f" | {period}"
            if gpa:
                line += f" | GPA {gpa}"
            edu_flows.append(p(line, bullet_style))
    story.append(panel("Education", colors.HexColor("#eef2ff"), edu_flows))
    story.append(Spacer(1, 8))

    cert_items = _listify(a1.get("certifications"))
    cert_flows = []
    if not cert_items:
        cert_flows.append(p("No certification data available."))
    else:
        for idx, cert in enumerate(cert_items, start=1):
            line = f"{idx}. {_safe_text(cert.get('name'))}"
            issuer = _safe_text(cert.get("issuer"), "")
            year = _safe_text(cert.get("year"), "")
            if issuer:
                line += f" | {issuer}"
            if year:
                line += f" | {year}"
            cert_flows.append(p(line))
    story.append(panel("Certifications", colors.HexColor("#f5f3ff"), cert_flows))
    story.append(Spacer(1, 8))

    org_items = _listify(a1.get("organization"))
    org_flows = []
    if not org_items:
        org_flows.append(p("No organization data available."))
    else:
        for idx, org in enumerate(org_items, start=1):
            line = f"{idx}. {_safe_text(org.get('title'))} | {_safe_text(org.get('organization'))}"
            org_flows.append(p(line, heading_style))
            for d in _listify(org.get("descriptions")):
                org_flows.append(p(f"• {_safe_text(d)}", bullet_style))
    story.append(panel("Organization Experience", colors.HexColor("#fdf2f8"), org_flows))
    story.append(Spacer(1, 8))

    proj_items = _listify(a1.get("projects"))
    proj_flows = []
    if not proj_items:
        proj_flows.append(p("No project data available."))
    else:
        for idx, proj in enumerate(proj_items, start=1):
            period = " - ".join([x for x in [_safe_text(proj.get("period_start"), ""), _safe_text(proj.get("period_end"), "")] if x]).strip(" -")
            line = f"{idx}. {_safe_text(proj.get('name'))}"
            if period:
                line += f" | {period}"
            proj_flows.append(p(line, heading_style))
            for d in _listify(proj.get("descriptions")):
                proj_flows.append(p(f"• {_safe_text(d)}", bullet_style))
    story.append(panel("Featured Projects", colors.HexColor("#ecfdf5"), proj_flows))

    story.append(PageBreak())

    # Agent 2 -------------------------------------------------
    story.append(Paragraph("Agent 2 - Skills Specialization", agent_style))
    story.append(p("Classifies explicit and inferred skills from your background.", meta_style))
    story.append(Spacer(1, 8))
    story.append(panel("Skill Summary", colors.HexColor("#eef2ff"), [p(a2.get("skill_summary", "No skill summary available."))]))
    story.append(Spacer(1, 8))

    story.append(
        panel(
            "Explicit Skills",
            colors.HexColor("#fffbeb"),
            chip_rows_flow(
                a2.get("explicit_skills"),
                colors.HexColor("#fff7ed"),
                colors.HexColor("#9a3412"),
                colors.HexColor("#f0c9a5"),
            ),
        )
    )
    story.append(Spacer(1, 8))
    implicit_flows = []
    implicit = _listify(a2.get("implicit_skills"))
    if not implicit:
        implicit_flows.append(p("No implicit skills available."))
    else:
        for item in implicit:
            if isinstance(item, dict):
                skill = _safe_text(item.get("skill"), "Unknown skill")
                evidence = _safe_text(item.get("evidence"), "")
                implicit_flows.append(p(f"• {skill}" + (f" | Evidence: {evidence}" if evidence else ""), bullet_style))
            else:
                implicit_flows.append(p(f"• {_safe_text(item)}", bullet_style))
    story.append(Spacer(1, 8))
    story.append(panel("Implicit Skills", colors.HexColor("#ecfdf5"), implicit_flows))

    story.append(PageBreak())

    # Agent 3 -------------------------------------------------
    story.append(Paragraph("Agent 3 - Market Intelligence", agent_style))
    story.append(p("Surfaces latest information from internet about role requirements and demand signals for your target position.", meta_style))
    story.append(Spacer(1, 8))

    sources = _select_top_sources(a3.get("sources"), max_count=12, min_chars=200)
    source_flows = []
    if not sources:
        source_flows.append(p("No job-source data available."))
    else:
        for i, src in enumerate(sources, start=1):
            if not isinstance(src, dict):
                continue
            source_flows.append(p(f"Source {i}: {_safe_text(src.get('title'))}", heading_style))
            if src.get("role_overview"):
                source_flows.append(p(f"Role overview: {_safe_text(src.get('role_overview'))}", body_style))
            for k in _listify(src.get("key_responsibilities")):
                source_flows.append(p(f"• {_safe_text(k)}", bullet_style))
            source_flows.append(Spacer(1, 4))
    story.append(panel("Job Requirements (Latest Info)", colors.HexColor("#eef2ff"), source_flows))
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "Demanded Skills",
            colors.HexColor("#ffedd5"),
            chip_rows_flow(
                a3.get("demanded_skills"),
                colors.HexColor("#fff7ed"),
                colors.HexColor("#9a3412"),
                colors.HexColor("#f0c9a5"),
            ),
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "Soft Skills",
            colors.HexColor("#ffe4e6"),
            chip_rows_flow(
                a3.get("soft_skills"),
                colors.HexColor("#fff1f2"),
                colors.HexColor("#9f1239"),
                colors.HexColor("#f7c4cf"),
            ),
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "Technologies",
            colors.HexColor("#ecfdf5"),
            chip_rows_flow(
                a3.get("list_of_technologies"),
                colors.HexColor("#ecfdf5"),
                colors.HexColor("#065f46"),
                colors.HexColor("#b9e5d4"),
            ),
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "Certifications",
            colors.HexColor("#f5f3ff"),
            chip_rows_flow(
                a3.get("certifications"),
                colors.HexColor("#f5f3ff"),
                colors.HexColor("#5b21b6"),
                colors.HexColor("#d9cbff"),
            ),
        )
    )

    story.append(PageBreak())

    # Agent 4 -------------------------------------------------
    story.append(Paragraph("Agent 4 - Recommendation Report", agent_style))
    story.append(p(f"Automated structural analysis against live market demands for {_safe_text(role, 'your target role')}.", meta_style))
    story.append(Spacer(1, 8))

    story.append(panel("Summary Analysis", colors.HexColor("#eef2ff"), [p(a4.get("summary_analysis", "No summary analysis available."))]))
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "Market Aligned Skills",
            colors.HexColor("#ecfdf5"),
            chip_rows_flow(
                a4.get("market_aligned_skills"),
                colors.HexColor("#ecfdf5"),
                colors.HexColor("#065f46"),
                colors.HexColor("#b9e5d4"),
            ),
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        panel(
            "High Demand / Missing",
            colors.HexColor("#ffedd5"),
            chip_rows_flow(
                a4.get("missing_skills"),
                colors.HexColor("#fff7ed"),
                colors.HexColor("#9a3412"),
                colors.HexColor("#f0c9a5"),
            ),
        )
    )
    story.append(Spacer(1, 8))

    strengths = _listify(a4.get("key_strengths"))
    strengths_flows = []
    if not strengths:
        strengths_flows.append(p("No key strengths available."))
    else:
        for item in strengths:
            if isinstance(item, dict):
                strengths_flows.append(p(f"• {_safe_text(item.get('title'))}: {_safe_text(item.get('description'))}", bullet_style))
    story.append(panel("Key Strengths", colors.HexColor("#eef2ff"), strengths_flows))
    story.append(Spacer(1, 8))

    ats = _listify(a4.get("resume_action_items"))
    ats_flows = []
    if not ats:
        ats_flows.append(p("No ATS action items available."))
    else:
        for idx, item in enumerate(ats, start=1):
            if isinstance(item, dict):
                ats_flows.append(p(f"{idx}. Instead of: {_safe_text(item.get('instead_of'))}", bullet_style))
                ats_flows.append(p(f"   Recommended rewrite: {_safe_text(item.get('change_to'))}", ats_change_style))
                ats_flows.append(Spacer(1, 4))
    story.append(panel("Resume Action Items (ATS)", colors.HexColor("#eef2ff"), ats_flows))
    story.append(Spacer(1, 8))

    plan = a4.get("upskilling_plan") or {}
    tte_flows = []
    for label, key in [("Low Effort (Days)", "low_effort"), ("Medium Effort (Weeks)", "medium_effort"), ("High Effort (Months)", "high_effort")]:
        tte_flows.append(p(label, heading_style))
        entries = _listify(plan.get(key))
        if not entries:
            tte_flows.append(p("• No data available.", bullet_style))
            continue
        for row in entries:
            if isinstance(row, dict):
                skill = _safe_text(row.get("skill"))
                timeframe = _safe_text(row.get("timeframe"), "")
                desc = _safe_text(row.get("description"), "")
                line = f"• {skill}"
                if timeframe:
                    line += f" ({timeframe})"
                if desc:
                    line += f": {desc}"
                tte_flows.append(p(line, bullet_style))
        tte_flows.append(Spacer(1, 2))
    story.append(panel("Estimated Time to Upskill (TTE)", colors.HexColor("#eef2ff"), tte_flows))

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=32,
        bottomMargin=32,
        title="Skill Gap Analysis Report",
    )

    def _paint_bg(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(page_bg)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canvas.restoreState()

    doc.build(story, onFirstPage=_paint_bg, onLaterPages=_paint_bg)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


def _sanitize_pdf_filename(name: str) -> str:
    base = (name or "skill_gap_report").strip()
    base = re.sub(r"[^\w\-. ]+", "_", base)
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    _safe_print_traceback(tb)
    return JSONResponse(content={"error": str(exc), "traceback": tb}, status_code=500)


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), target_role: str = Form(...)):
    # Save uploaded file to a temp location
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = run_pipeline(cv_path=tmp_path, role=target_role)
        response_data = _build_response_data(result)
        return JSONResponse(content=response_data)

    except Exception as e:
        tb = traceback.format_exc()
        _safe_print_traceback(tb)
        return JSONResponse(content={"error": str(e), "traceback": tb}, status_code=500)

    finally:
        os.unlink(tmp_path)


@app.post("/api/analyze/start")
async def analyze_start(file: UploadFile = File(...), target_role: str = Form(...)):
    """Start analysis as background job and return job_id for progress polling."""
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    job_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "stage_key": "agent_1",
            "stage_index": 1,
            "stage_heading": STAGE_MAP["agent_1"]["heading"],
            "stage_label": STAGE_MAP["agent_1"]["label"],
            "stage_subdetail": STAGE_MAP["agent_1"]["subdetail"],
            "stage_status": "queued",
            "timings_ms": {},
            "total_elapsed_ms": None,
            "result": None,
            "error": None,
            "traceback": None,
            "created_at": now_ms,
            "updated_at": now_ms,
        }

    t = threading.Thread(target=_run_analysis_job, args=(job_id, tmp_path, target_role), daemon=True)
    t.start()
    return JSONResponse(content={"job_id": job_id})


@app.get("/api/analyze/status/{job_id}")
async def analyze_status(job_id: str):
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return JSONResponse(content={"error": "Job not found"}, status_code=404)
        payload = {
            "job_id": job["job_id"],
            "status": job["status"],
            "stage_key": job.get("stage_key"),
            "stage_index": job.get("stage_index"),
            "stage_heading": job.get("stage_heading"),
            "stage_label": job.get("stage_label"),
            "stage_subdetail": job.get("stage_subdetail"),
            "stage_status": job.get("stage_status"),
            "timings_ms": job.get("timings_ms", {}),
            "total_elapsed_ms": job.get("total_elapsed_ms"),
            "error": job.get("error"),
            "traceback": job.get("traceback"),
            "updated_at": job.get("updated_at"),
        }
        if job.get("status") == "completed":
            payload["result"] = job.get("result")
    return JSONResponse(content=payload)


@app.post("/api/recommend")
async def recommend(request: Request):
    """Run only Agent 4 using provided agent_2 + agent_3 state data (used by demo mode)."""
    try:
        body = await request.json()
        state = {
            "role": body.get("role", ""),
            "agent_2_specialize_skills": body.get("agent_2_specialize_skills", {}),
            "agent_3_market_intelligence": body.get("agent_3_market_intelligence", {}),
        }
        result = recommendation_report_agent(state)
        return JSONResponse(content=result.get("agent_4_recommendation_report", {}))
    except Exception as e:
        tb = traceback.format_exc()
        _safe_print_traceback(tb)
        return JSONResponse(content={"error": str(e), "traceback": tb}, status_code=500)


@app.post("/api/report-pdf")
async def report_pdf(request: Request):
    try:
        body = await request.json()
        analysis = body.get("analysis") or {}
        role = body.get("role", "")
        filename = _sanitize_pdf_filename(body.get("filename", "skill_gap_report.pdf"))
        pdf_bytes = _build_report_pdf(analysis, role)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        tb = traceback.format_exc()
        _safe_print_traceback(tb)
        return JSONResponse(content={"error": str(e), "traceback": tb}, status_code=500)


if __name__ == "__main__":
    from granian import Granian
    from granian.constants import Interfaces

    granian = Granian("app:app", address="0.0.0.0", port=8000, interface=Interfaces.ASGI)
    granian.serve()
