import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
import config.constants as constants
from schemas.pipeline_state import PipelineState


STOPWORDS = {
    "and", "or", "the", "to", "of", "for", "with", "in", "on", "at", "by",
    "skill", "skills", "tool", "tools", "software", "systems", "system", "based"
}


def _empty_report():
    return {
        "certifications_to_pursue": [],
        "market_aligned_skills": [],
        "missing_skills": [],
        "summary_analysis": "",
        "key_strengths": [],
        "resume_action_items": [],
        "upskilling_plan": {"low_effort": [], "medium_effort": [], "high_effort": []},
    }


def _normalize_skill(text: str) -> str:
    if not text:
        return ""
    s = str(text).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9+\-/\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _skill_tokens(text: str):
    norm = _normalize_skill(text)
    tokens = [t for t in norm.split() if len(t) >= 3 and t not in STOPWORDS]
    return set(tokens)


def _is_skill_match(a: str, b: str) -> bool:
    na, nb = _normalize_skill(a), _normalize_skill(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    ta, tb = _skill_tokens(na), _skill_tokens(nb)
    if not ta or not tb:
        return False
    return len(ta & tb) >= 1


def _dedupe_skills(items):
    seen = set()
    out = []
    for item in items or []:
        if not item:
            continue
        label = str(item).strip()
        if not label:
            continue
        key = _normalize_skill(label)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def _extract_candidate_skills(a2: dict):
    explicit = a2.get("explicit_skills") or []
    implicit = a2.get("implicit_skills") or []
    implicit_names = []
    for item in implicit:
        if isinstance(item, dict):
            implicit_names.append(item.get("skill") or item.get("name") or "")
        else:
            implicit_names.append(str(item))
    return _dedupe_skills([*explicit, *implicit_names])


def _extract_market_skills(a3: dict):
    if not isinstance(a3, dict):
        return []
    collected = []
    collected.extend(a3.get("demanded_skills") or [])
    collected.extend(a3.get("list_of_technologies") or [])
    collected.extend(a3.get("soft_skills") or [])

    for src in a3.get("sources") or []:
        if not isinstance(src, dict):
            continue
        collected.extend(src.get("demanded_skills") or [])
        collected.extend(src.get("tools_software") or [])
        collected.extend(src.get("soft_skills") or [])
    return _dedupe_skills(collected)


def _build_seed_gap(candidate_skills, market_skills):
    aligned = []
    missing = []
    for market_skill in market_skills:
        matched = any(_is_skill_match(candidate_skill, market_skill) for candidate_skill in candidate_skills)
        if matched:
            aligned.append(market_skill)
        else:
            missing.append(market_skill)
    return _dedupe_skills(aligned), _dedupe_skills(missing)


def _filter_llm_gap(skills, candidate_skills, market_skills, require_candidate_match):
    filtered = []
    for item in skills or []:
        label = str(item).strip()
        if not label:
            continue
        matches_market = any(_is_skill_match(label, m) for m in market_skills)
        matches_candidate = any(_is_skill_match(label, c) for c in candidate_skills)
        if matches_market and (matches_candidate == require_candidate_match):
            filtered.append(label)
    return _dedupe_skills(filtered)


def _merge_with_seed(primary, seed, limit=16):
    merged = _dedupe_skills(primary)
    for item in seed:
        if len(merged) >= limit:
            break
        if not any(_is_skill_match(item, existing) for existing in merged):
            merged.append(item)
    return merged[:limit]


def _extract_experience_descriptions(a1: dict):
    items = (a1 or {}).get("experience") or []
    lines = []
    for exp in items:
        if not isinstance(exp, dict):
            continue
        desc = exp.get("descriptions") or exp.get("details") or exp.get("highlights") or []
        for line in desc:
            txt = str(line).strip()
            if txt:
                lines.append(txt)
    # Keep order but remove duplicates.
    seen = set()
    unique_lines = []
    for line in lines:
        key = re.sub(r"\s+", " ", line).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique_lines.append(line)
    return unique_lines


def _normalize_phrase(text: str) -> str:
    s = (text or "").lower()
    s = re.sub(r"[\"'`]", "", s)
    s = re.sub(r"[^a-z0-9+\-/\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_phrase_match(source_line: str, candidate_phrase: str) -> bool:
    s = _normalize_phrase(source_line)
    c = _normalize_phrase(candidate_phrase)
    if not s or not c:
        return False
    if c in s or s in c:
        return True
    s_tokens = {t for t in s.split() if len(t) >= 4}
    c_tokens = {t for t in c.split() if len(t) >= 4}
    if not s_tokens or not c_tokens:
        return False
    # Require meaningful overlap to prevent fabricated "instead_of".
    overlap = len(s_tokens & c_tokens)
    return overlap >= 3 or (overlap >= 2 and len(c_tokens) <= 5)


def _filter_resume_action_items(items, source_descriptions):
    if not source_descriptions:
        return []
    filtered = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        instead_of = str(item.get("instead_of") or "").strip()
        change_to = str(item.get("change_to") or "").strip()
        if not instead_of or not change_to:
            continue
        if any(_is_phrase_match(src, instead_of) for src in source_descriptions):
            filtered.append({"instead_of": instead_of, "change_to": change_to})
    # Remove duplicates by normalized instead_of.
    seen = set()
    deduped = []
    for row in filtered:
        key = _normalize_phrase(row["instead_of"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


# ---------- Graph D: Recommendation report
def recommendation_report_agent(state: PipelineState):
    _a2 = state.get("agent_2_specialize_skills") or {}
    if not _a2 or (not _a2.get("explicit_skills") and not _a2.get("implicit_skills")):
        return {"agent_4_recommendation_report": _empty_report()}

    role = state.get("role", "")
    a1_cv = state.get("agent_1_cv_parsing", {}) or {}
    market_intelligence = state.get("agent_3_market_intelligence", {}) or {}
    candidate_skills = _extract_candidate_skills(_a2)
    market_skills = _extract_market_skills(market_intelligence)
    aligned_seed, missing_seed = _build_seed_gap(candidate_skills, market_skills)
    source_descriptions = _extract_experience_descriptions(a1_cv)

    system_prompt = """You are a senior career strategist and AI engineering talent advisor.
    You produce precise, structured career gap reports that help candidates land their target roles faster."""

    recommendation_report_prompt = f"""
    Analyze the candidate's skills against market demands for the role of {role} and produce a
    comprehensive, structured career gap report covering certifications, skill gaps, strengths,
    ATS-optimized resume rewrites, and an upskilling roadmap.

    ### Candidate Skills (from Agent 2):
    {candidate_skills}

    ### Work Experience Description Lines (from Agent 1; only use these for ATS "instead_of"):
    {json.dumps(source_descriptions, ensure_ascii=False)}

    ### Market Intelligence (from Agent 3, latest information):
    {json.dumps(market_intelligence, ensure_ascii=False)}

    ### Deterministic baseline comparison (Agent 2 vs Agent 3):
    Market Aligned Seed: {aligned_seed}
    Missing Seed: {missing_seed}

    IMPORTANT:
    - "market_aligned_skills" MUST come from overlaps between Agent 2 skills and Agent 3 market skills.
    - "missing_skills" MUST come from Agent 3 market skills that are not present in Agent 2.
    - Do not invent unrelated skills outside the market intelligence context.
    - For "resume_action_items", each "instead_of" MUST be copied from the provided Agent 1 work description lines.
    - If Agent 1 work description lines are unavailable/empty, return an empty "resume_action_items" list.

    Return ONLY valid JSON (no extra commentary) following EXACTLY this structure:

    {{
        "certifications_to_pursue": [
            "Top 3-5 certifications from market demand the candidate should pursue (plain strings)"
        ],
        "market_aligned_skills": [
            "Candidate skills that directly match market demand — short labels like 'Python', 'FastAPI', 'LangChain (Agentic AI)'"
        ],
        "missing_skills": [
            "High-demand market skills the candidate lacks — short descriptive labels like 'Kubernetes (Market demand focus)', 'Pinecone / Weaviate (Vector DBs)'"
        ],
        "summary_analysis": "2-3 sentence paragraph summarizing the candidate's fit for the role, highlighting key alignments and the most critical skill gaps.",
        "key_strengths": [
            {{"title": "Strength Title", "description": "One sentence describing this strength based on the candidate's background."}}
        ],
        "resume_action_items": [
            {{"instead_of": "Generic phrase the candidate likely uses now", "change_to": "Stronger, ATS-optimized alternative using market-demanded terminology and tools"}}
        ],
        "upskilling_plan": {{
            "low_effort": [
                {{"skill": "Skill or Tool Name", "timeframe": "X Days", "description": "Concise description of what to do or build."}}
            ],
            "medium_effort": [
                {{"skill": "Skill or Tool Name", "timeframe": "X Weeks", "description": "Concise description of what to do or build."}}
            ],
            "high_effort": [
                {{"skill": "Skill or Tool Name", "timeframe": "X Months", "description": "Concise description of what to do or build."}}
            ]
        }}
    }}

    Rules:
    - key_strengths: provide exactly 3-4 items
    - resume_action_items: provide exactly 4-5 items ONLY when work description lines are available; otherwise return []
    - upskilling_plan.low_effort: 1-2 items (days to learn)
    - upskilling_plan.medium_effort: 2-3 items (weeks to learn)
    - upskilling_plan.high_effort: 2 items (months to learn)
    - All fields must be populated — never return empty arrays for a real candidate
    """

    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=recommendation_report_prompt)

    response = constants.llm.invoke([system_message, human_message])
    recommendation_report_raw = response.content

    try:
        recommendation_report_json_text = re.search(r"\{.*\}", recommendation_report_raw, re.S).group(0)
        recommendation_report_json_obj = json.loads(recommendation_report_json_text)
        print("INFO: Recommendation report created successfully.")
    except Exception:
        recommendation_report_json_obj = _empty_report()
        print("ERROR: Recommendation report failed to be created.")

    if market_skills:
        llm_aligned = recommendation_report_json_obj.get("market_aligned_skills") or []
        llm_missing = recommendation_report_json_obj.get("missing_skills") or []

        aligned_filtered = _filter_llm_gap(
            llm_aligned, candidate_skills, market_skills, require_candidate_match=True
        )
        missing_filtered = _filter_llm_gap(
            llm_missing, candidate_skills, market_skills, require_candidate_match=False
        )

        recommendation_report_json_obj["market_aligned_skills"] = _merge_with_seed(aligned_filtered, aligned_seed, limit=16)
        recommendation_report_json_obj["missing_skills"] = _merge_with_seed(missing_filtered, missing_seed, limit=16)

    recommendation_report_json_obj["resume_action_items"] = _filter_resume_action_items(
        recommendation_report_json_obj.get("resume_action_items") or [],
        source_descriptions,
    )

    return {"agent_4_recommendation_report": recommendation_report_json_obj}
