from schemas.pipeline_state import PipelineState
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime
import re
import json
import config.constants as constants

def _safe_print(msg: str):
    """Windows-safe print that won't crash on non-cp1252 characters."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="backslashreplace").decode("ascii"))

# ---------- Experience helpers

_MONTH_MAP = {
    # English full
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    # English abbreviated (with and without dot)
    "jan": 1, "jan.": 1,
    "feb": 2, "feb.": 2,
    "mar": 3, "mar.": 3,
    "apr": 4, "apr.": 4,
    "jun": 6, "jun.": 6,
    "jul": 7, "jul.": 7,
    "aug": 8, "aug.": 8,
    "sept": 9, "sept.": 9, "sep": 9, "sep.": 9,
    "oct": 10, "oct.": 10,
    "nov": 11, "nov.": 11,
    "dec": 12, "dec.": 12,
    # Indonesian
    "januari": 1, "februari": 2, "maret": 3,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "oktober": 10, "november": 11, "desember": 12,
}

_PRESENT_TOKENS = {
    "present", "now", "current", "currently",
    # Indonesian
    "saat ini", "sekarang", "kini", "sampai sekarang",
}

def _parse_exp_date(s: str):
    if not s:
        return None
    s = s.strip().lower()
    # Check multi-word "present" phrases first
    if s in _PRESENT_TOKENS:
        return datetime.now()
    tokens = s.split()
    # Single token: present-synonym, month name, or year number
    if len(tokens) == 1:
        if tokens[0] in _PRESENT_TOKENS:
            return datetime.now()
        # Single month name with no year — infer year
        if tokens[0] in _MONTH_MAP:
            month_num = _MONTH_MAP[tokens[0]]
            now = datetime.now()
            candidate = datetime(now.year, month_num, 1)
            if candidate > now:
                candidate = datetime(now.year - 1, month_num, 1)
            return candidate
        try:
            return datetime(int(tokens[0]), 1, 1)
        except ValueError:
            return None
    # Two tokens expected: "Month YYYY" or "YYYY Month"
    # Try both orderings
    month_num, year_num = None, None
    for tok in tokens[:2]:
        if tok in _MONTH_MAP:
            month_num = _MONTH_MAP[tok]
        else:
            try:
                y = int(tok)
                if 1900 < y < 2200:
                    year_num = y
            except ValueError:
                pass
    if month_num and year_num:
        return datetime(year_num, month_num, 1)
    # Month-only (no year): infer year from current date
    if month_num and year_num is None:
        now = datetime.now()
        candidate = datetime(now.year, month_num, 1)
        if candidate > now:
            candidate = datetime(now.year - 1, month_num, 1)
        return candidate
    return None

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

def _normalize_date_str(s: str) -> str:
    """Convert any date string (any language) to 'Month YYYY' in English.
    Present-equivalent tokens become the actual current month and year."""
    if not s:
        return s
    if s.strip().lower() in _PRESENT_TOKENS:
        now = datetime.now()
        return f"{_MONTH_NAMES[now.month - 1]} {now.year}"
    dt = _parse_exp_date(s)
    if dt is None:
        return s  # unparseable — keep as-is
    return f"{_MONTH_NAMES[dt.month - 1]} {dt.year}"

def _normalize_all_periods(items: list) -> list:
    """Normalize period_start / period_end on every item to English in-place."""
    for item in items:
        for field in ("period_start", "period_end"):
            if field in item and item[field]:
                item[field] = _normalize_date_str(str(item[field]))
    return items

def _add_one_month(dt: datetime) -> datetime:
    """Return a new datetime exactly one month after dt."""
    month = dt.month + 1
    year  = dt.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return datetime(year, month, 1)

def _calc_total_experience(experience_list: list):
    now = datetime.now()
    total_months = 0
    for exp in experience_list:
        start = _parse_exp_date(exp.get("period_start", ""))
        raw_end = (exp.get("period_end") or "").strip()
        if not raw_end:
            # Only a start date is present — treat as 1-month stint
            end = _add_one_month(start) if start else now
        else:
            end = _parse_exp_date(raw_end) or now
        if not start:
            continue
        diff = (end.year - start.year) * 12 + (end.month - start.month)
        if diff > 0:
            total_months += diff
    if total_months == 0:
        return None
    years = total_months // 12
    months = total_months % 12
    parts = []
    if years > 0:
        parts.append(f"{years} Year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} Month{'s' if months != 1 else ''}")
    return ", ".join(parts)

def _sort_experience_desc(experience_list: list) -> list:
    def _key(exp):
        end = _parse_exp_date(exp.get("period_end", "")) or datetime.max
        start = _parse_exp_date(exp.get("period_start", "")) or datetime.min
        return (end, start)
    return sorted(experience_list, key=_key, reverse=True)

def _calc_job_duration(period_start: str, period_end: str):
    now = datetime.now()
    start = _parse_exp_date(period_start)
    raw_end = (period_end or "").strip()
    if not raw_end:
        # Only start period known — treat as 1-month stint
        end = _add_one_month(start) if start else now
    else:
        end = _parse_exp_date(raw_end) or now
    if not start:
        return None
    diff = (end.year - start.year) * 12 + (end.month - start.month)
    if diff <= 0:
        return None
    years = diff // 12
    months = diff % 12
    parts = []
    if years > 0:
        parts.append(f"{years} yr{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} mo")
    return " ".join(parts)

# ---------- Graph A: CV Parsing
def extract_info_node(state: PipelineState):
    text = state.get("input_text", "")

    if not text or not text.strip():
        print("WARN: No CV text available; skipping LLM prompt.")
        return {"agent_1_cv_parsing": {
            "summary": None,
            "experience": [],
            "education": [],
            "organization": [],
            "projects": [],
            "certifications": [],
            "skills": [],
            "total_experience": None,
            "_raw": None,
            "_raw_input": None,
        }}

    system_prompt = """
    You are an AI agent specialized in concise document parsing 
    and structured information extraction."""

    parsing_prompt = f"""
    Your goal is to read the given document and extract structured information in detail.
    You MUST use EXACTLY the field names shown below. Do NOT rename any key.

    FIELD NAMES (mandatory, do not change):
    - experience items      : "title", "company", "period_start", "period_end", "descriptions"
    - education items       : "degree", "institution", "period_start", "period_end", "gpa"
    - organization items    : "title", "organization", "period_start", "period_end", "descriptions"
    - project items         : "name", "period_start", "period_end", "descriptions"
    - certification items   : "name", "issuer", "year", "score"
    - skills list           : a flat list of strings under "skills"

    Instructions:
    1. "skills"     — Scan the ENTIRE document and list every skill explicitly named by the person.
         Include all: programming languages, tools, frameworks, libraries, cloud platforms, methodologies,
         soft skills, spoken/written languages, domain expertise, and any other named competency.
         Each item must be a single word or short phrase, translated to English, no duplicates.
    2. "experience"  — Each professional/work experience entry:
         "title"        : job title TRANSLATED TO ENGLISH (e.g. "Sales" not "Penjualan", "Internship" not "Magang")
         "company"      : company or employer name
         "period_start" : Translate the month name to English. Output EXACTLY what the document says — do NOT add a year if the document does not show one. e.g. if the CV says "September" → output "September"; if it says "March 2022" → output "March 2022"; if it says only "2022" → output "2022".
         "period_end"   : Same rule as period_start. If the job is still ongoing → "Present". Never invent a year.
         "descriptions" : ALL responsibilities and achievements listed in the document for this role — do not skip or summarise any
    3. "education"   — Each academic qualification:
         "degree"       : degree level and field TRANSLATED TO ENGLISH (e.g. "B.Sc. Metallurgical Engineering" not "S1 Teknik Metalurgi", "Senior High School" not "SMA", "Junior High School" not "SMP", "Elementary School" not "SD")
         "institution"  : university or school name — keep the proper noun as-is but translate any generic type prefix to English (e.g. "Universitas Indonesia" stays, "SMP Negeri 227 Jakarta" → "SMPN 227 Jakarta")
         "period_start" : start year (e.g. "2017")
         "period_end"   : graduation year (e.g. "2022")
         "gpa"          : GPA value as string if stated, otherwise empty string ""
    4. "certifications" — Search the ENTIRE document for every certificate, license, language test, professional
         credential, or training completion. Do NOT limit to a "Certifications" section — also check Experience,
         Education, Organizations, and any other part of the document. Include ALL of them.
         "name"         : certificate or credential name TRANSLATED TO ENGLISH (e.g. "UMKM Business Companion" not "Pendamping UMKM", "Digital Marketing" stays as-is)
         "issuer"       : issuing body or organization (e.g. "Google", "Coursera", "ETS") — translate to English if needed
         "year"         : year obtained as string (e.g. "2023"), or empty string "" if not stated
         "score"        : numeric or grade score if stated (e.g. "457", "B2", "850/990"), or empty string "" if not stated
    5. "organization" — Each organizational/volunteer/extracurricular role:
         "title"        : role or position held TRANSLATED TO ENGLISH (e.g. "Head of Internal Affairs" not "Kepala Departemen Internal", "Academic Division Staff" not "Staff Divisi Akademik")
         "organization" : organization or event name TRANSLATED TO ENGLISH (e.g. "Indonesian Metallurgy and Materials Student Association" not "Perhimpunan Mahasiswa Metalurgi dan Material Se-Indonesia")
         "period_start" : Translate the month name to English. Output EXACTLY what is written — do NOT add a year. Month+year → "Month YYYY"; month only → just "Month"; year only → "YYYY".
         "period_end"   : Same rule, or "Present" if still ongoing. Never invent a year.
         "descriptions" : list of contributions TRANSLATED TO ENGLISH; empty list [] if none stated
    6. "projects"    — Search the ENTIRE document for every concrete project the person has built, researched, or delivered.
         A PROJECT is a specific piece of work with a defined output: a software app, a research study, an analysis,
         a product, a designed system, a published paper, a competition entry, etc.
         A PROJECT is NOT: a job title, an internship role, a company worked at, or a general job responsibility.
         Do NOT copy job titles (e.g. "Quality Control Intern", "Nutritionist Intern") as project names.
         DO include projects mentioned inside work experience descriptions, academic work, side/personal projects,
         portfolio items, or any other section. Each entry:
         "name"         : the actual project name or a short descriptive title of what was built/researched (TRANSLATED TO ENGLISH)
         "period_start" : Translate month to English. Output exactly what the document says — no year invention. If nothing stated → empty string "".
         "period_end"   : Same rule. If nothing stated → empty string "".
         "descriptions" : 1–3 concise bullet points describing what the project is, what was built, and the outcome/impact
    7. If a section is absent from the document, return an empty list [] for that field.

    EXAMPLE OUTPUT (fill with real data from the document):
    {{
      "skills": ["SEO", "SEM", "Google Analytics", "Social Media Marketing", "Content Strategy", "Leadership", "English"],
      "experience": [
        {{
          "title": "Digital Marketing Manager",
          "company": "PT Maju Jaya",
          "period_start": "January 2020",
          "period_end": "Present",
          "descriptions": [
            "Led SEO and SEM campaigns that increased organic traffic by 45%",
            "Managed a team of 5 content creators and 2 graphic designers"
          ]
        }}
      ],
      "education": [
        {{
          "degree": "B.Sc. Management",
          "institution": "Universitas Indonesia",
          "period_start": "2015",
          "period_end": "2019",
          "gpa": "3.54"
        }}
      ],
      "organization": [
        {{
          "title": "Head of Events",
          "organization": "Student Marketing Association",
          "period_start": "August 2017",
          "period_end": "July 2018",
          "descriptions": ["Organized 3 annual competitions with 200+ participants"]
        }}
      ],
      "certifications": [
        {{
          "name": "Google Data Analytics Certificate",
          "issuer": "Google",
          "year": "2022",
          "score": ""
        }}
      ],
      "projects": [
        {{
          "name": "Brand Awareness Campaign for UMKM",
          "period_start": "March 2021",
          "period_end": "June 2021",
          "descriptions": ["Designed social media strategy that grew follower count by 30%"]
        }}
      ]
    }}

    Now extract from this document:
    ---START---
    {text}
    ---END---

    Return ONLY valid JSON exactly matching the structure above. No markdown fences, no commentary.
    """

    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=parsing_prompt)

    response = constants.llm.invoke([system_message, human_message])
    parsing_raw = response.content
    _safe_print(f"\n{'='*60}\nRAW CV INPUT:\n{'='*60}\n{text}\n{'='*60}")
    _safe_print(f"\n{'='*60}\nRAW LLM OUTPUT:\n{'='*60}\n{parsing_raw}\n{'='*60}\n")
    
    try:
        parsing_json_text = re.search(r"\{.*\}", parsing_raw, re.S).group(0)
        parsing_json_obj = json.loads(parsing_json_text)
        print("INFO: File parsed successfully.")
        
    except Exception as e:
        _safe_print(f"ERROR: Parse error: {e}")
        _safe_print(f"Raw output was:\n{parsing_raw}")
        parsing_json_obj = {
            "summary": "",
            "experience": [],
            "education": [],
            "certifications": [],
            "organization": [],
            "projects": [],
            "skills": [],
        }
        print("ERROR: File failed to be parsed.")

    # Normalize all date strings to English before any further processing
    for section in ("experience", "education", "organization", "projects"):
        _normalize_all_periods(parsing_json_obj.get(section, []))

    # Drop experience/organization entries where both period_start and period_end are unknown
    def _has_any_date(item):
        start = item.get("period_start") or ""
        end   = item.get("period_end")   or ""
        return bool(start.strip() or end.strip())

    parsing_json_obj["experience"]   = [e for e in parsing_json_obj.get("experience", [])   if _has_any_date(e)]
    parsing_json_obj["organization"] = [o for o in parsing_json_obj.get("organization", []) if _has_any_date(o)]

    # Sort experience, education, and organization from most recent to oldest
    sorted_exp = _sort_experience_desc(parsing_json_obj.get("experience", []))
    parsing_json_obj["education"]     = _sort_experience_desc(parsing_json_obj.get("education", []))
    parsing_json_obj["organization"]  = _sort_experience_desc(parsing_json_obj.get("organization", []))

    # Stamp each experience item with a Python-calculated duration
    for exp in sorted_exp:
        exp["duration"] = _calc_job_duration(
            exp.get("period_start", ""), exp.get("period_end", "")
        )
    parsing_json_obj["experience"] = sorted_exp

    # Stamp each organization item with a Python-calculated duration
    for org in parsing_json_obj["organization"]:
        org["duration"] = _calc_job_duration(
            org.get("period_start", ""), org.get("period_end", "")
        )

    # Calculate total experience in Python
    parsing_json_obj["total_experience"] = _calc_total_experience(
        parsing_json_obj.get("experience", [])
    )

    parsing_json_obj["_raw"] = parsing_raw
    parsing_json_obj["_raw_input"] = text

    # --- Summary micro-call (uses clean structured output + Python-calculated total_experience) ---
    total_exp = parsing_json_obj.get("total_experience")  # e.g. "2 Years, 3 Months" or None
    exp_list  = parsing_json_obj.get("experience", [])
    edu_list  = parsing_json_obj.get("education", [])
    org_list  = parsing_json_obj.get("organization", [])
    skills_list = parsing_json_obj.get("skills", [])

    if total_exp:
        exp_context = (
            f"The candidate has {total_exp} of professional work experience.\n"
            f"Work experience entries:\n{json.dumps(exp_list, indent=2)}"
        )
        fresh_grad_rule = (
            "The candidate HAS work experience. "
            "Sentence 1 MUST include their most recent job title, "
            f"followed by \"{total_exp} of experience\", "
            "then their latest academic degree and field of study."
        )
    else:
        exp_context = (
            "The candidate has NO professional work experience entries — treat them as a fresh graduate.\n"
            "Do NOT mention years or months of experience anywhere in the summary."
        )
        fresh_grad_rule = (
            "The candidate is a FRESH GRADUATE with no work experience. "
            "Sentence 1 MUST introduce them as a fresh graduate, "
            "state their latest degree, field of study, and institution. "
            "Do NOT write any experience duration."
        )

    summary_prompt = f"""
    You are writing a professional candidate summary based on structured CV data.

    EXPERIENCE RULE: {fresh_grad_rule}

    Write exactly 3 sentences (HARD LIMIT: 500 characters total):
    - Sentence 1: {fresh_grad_rule}
    - Sentence 2: Summarise their background across industry sectors and functional domains
                  (use work experience if available, otherwise academic/organisational background).
    - Sentence 3: Highlight key technical and soft skills, then state 1–2 roles this candidate is well suited for.
    
    Write in third person, present tense, professional tone.

    STRUCTURED DATA:
    {exp_context}

    Education:
    {json.dumps(edu_list, indent=2)}

    Organisations / Volunteer:
    {json.dumps(org_list, indent=2)}

    Skills:
    {json.dumps(skills_list)}

    Return ONLY the summary string — no JSON, no quotes, no markdown.
    """

    summary_response = constants.llm.invoke([
        SystemMessage(content="You are a professional CV writer."),
        HumanMessage(content=summary_prompt)
    ])
    generated_summary = summary_response.content.strip().strip('"').strip("'")
    # Enforce 500-char hard limit as a safety net
    if len(generated_summary) > 500:
        generated_summary = generated_summary[:497] + "..."
    parsing_json_obj["summary"] = generated_summary
    print(f"INFO: Summary generated ({len(generated_summary)} chars).")

    return {"agent_1_cv_parsing": parsing_json_obj}