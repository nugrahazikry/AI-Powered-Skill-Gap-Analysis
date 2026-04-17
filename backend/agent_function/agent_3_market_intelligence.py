import json
import re
from google.genai import types
from langchain_core.messages import SystemMessage, HumanMessage
import config.constants as constants
from schemas.pipeline_state import PipelineState

# ---------- Graph C: Job Market Analysis

def _collect_text_from_response(response) -> str:
    """Collect all text parts from a Gemini response, skipping tool-call parts."""
    collected = ""
    try:
        text = response.text
        if text:
            return text
    except Exception:
        pass
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", None) or []:
            t = getattr(part, "text", None)
            if t:
                collected += t
    return collected


def grounded_response(prompt: str,
                      model_name: str = constants.MODEL_NAME,
                      client=constants.CLIENT):
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )


def _extract_grounding_sources(response, portal: str) -> list:
    """Extract all available web grounding chunks from the response (no HTTP calls)."""
    sources = []
    seen_uris: set = set()
    try:
        for candidate in getattr(response, 'candidates', None) or []:
            gm = getattr(candidate, 'grounding_metadata', None)
            if not gm:
                continue
            chunks = list(getattr(gm, 'grounding_chunks', None) or [])
            print(f"  [grounding] {len(chunks)} chunks found")
            for chunk in chunks:
                web = getattr(chunk, 'web', None)
                if not web:
                    continue
                uri = getattr(web, 'uri', '') or ''
                title = getattr(web, 'title', '') or ''
                if uri and uri not in seen_uris:
                    seen_uris.add(uri)
                    sources.append({'title': title, 'uri': uri, 'portal': portal, 'requirements': []})
    except Exception as e:
        print(f"  [grounding] Exception: {e}")
    print(f"  [grounding] {len(sources)} sources collected")
    return sources



def _build_per_source_context(response, sources: list, fallback_text: str = "") -> str:
    """Build per-source text blocks using grounding_supports attribution."""
    source_texts: dict = {i: [] for i in range(len(sources))}
    try:
        for candidate in getattr(response, 'candidates', None) or []:
            gm = getattr(candidate, 'grounding_metadata', None)
            if not gm:
                continue
            for support in getattr(gm, 'grounding_supports', None) or []:
                seg = getattr(support, 'segment', None)
                seg_text = (getattr(seg, 'text', '') or '').strip() if seg else ''
                if not seg_text:
                    continue
                for idx in getattr(support, 'grounding_chunk_indices', None) or []:
                    if isinstance(idx, int) and idx < len(sources):
                        source_texts[idx].append(seg_text)
    except Exception as e:
        print(f"  [grounding_supports] Exception: {e}")

    blocks = []
    for i, s in enumerate(sources):
        texts = source_texts.get(i, [])
        combined = ' '.join(dict.fromkeys(texts)) if texts else fallback_text
        if combined:
            blocks.append(f"[Source {i}] {s['title']} — {s['uri'][:80]}\n{combined}")
    print(f"  [grounding_supports] {len(blocks)} sources with attributed text")
    return '\n\n'.join(blocks)


def _fallback_market_intelligence(role: str) -> dict:
    """Fallback when grounded search/parsing fails: synthesize structured market data."""
    prompt = f"""
Create practical market intelligence for the role: "{role}".

Return ONLY valid JSON with this schema:
{{
  "source_requirements": [
    {{
      "source_name": "String",
      "source_url": "String or empty",
      "role_overview": "String",
      "key_responsibilities": ["..."],
      "demanded_skills": ["..."],
      "soft_skills": ["..."],
      "tools_software": ["..."],
      "certifications": ["..."]
    }}
  ],
  "job_requirements": ["..."],
  "demanded_skills": ["..."],
  "soft_skills": ["..."],
  "list_of_technologies": ["..."],
  "certifications": ["..."]
}}

Rules:
- source_requirements: 3-5 sources
- demanded_skills: 12-20 items
- soft_skills: 6-10 items
- list_of_technologies: 10-20 items
- certifications: 3-6 items
"""
    try:
        resp = constants.llm.invoke([
            SystemMessage(content="You are a structured market-intelligence assistant."),
            HumanMessage(content=prompt),
        ])
        raw = (resp.content or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
        data = json.loads(raw)

        fields = [
            "role_overview", "key_responsibilities",
            "demanded_skills", "soft_skills", "tools_software", "certifications",
        ]
        sources = []
        for sr in data.get("source_requirements", []):
            entry = {
                "title": sr.get("source_name", "Market Source"),
                "uri": sr.get("source_url", ""),
                "portal": "Web",
                "requirements": [],
            }
            for f in fields:
                entry[f] = sr.get(f, "" if f == "role_overview" else [])
            sources.append(entry)

        return {
            "job_requirements": data.get("job_requirements", []),
            "demanded_skills": data.get("demanded_skills", []),
            "soft_skills": data.get("soft_skills", []),
            "list_of_technologies": data.get("list_of_technologies", []),
            "certifications": data.get("certifications", []),
            "sources": sources,
        }
    except Exception as e:
        print(f"  [agent3 fallback] LLM fallback failed: {e}")
        # Last-resort minimal non-empty structure
        return {
            "job_requirements": [
                f"Design and deliver solutions for {role}",
                "Collaborate with product and engineering stakeholders",
                "Build, test, and deploy production-ready systems",
            ],
            "demanded_skills": ["Python", "System Design", "APIs", "Cloud", "CI/CD", "Data Engineering", "MLOps"],
            "soft_skills": ["Communication", "Collaboration", "Problem Solving", "Adaptability"],
            "list_of_technologies": ["Python", "FastAPI", "Docker", "Kubernetes", "GitHub Actions", "AWS", "GCP"],
            "certifications": ["AWS Certified", "Google Cloud Certification"],
            "sources": [],
        }


def _source_content_length(source: dict) -> int:
    if not isinstance(source, dict):
        return 0
    pieces = [
        str(source.get("title") or "").strip(),
        str(source.get("role_overview") or "").strip(),
    ]
    for key in ["key_responsibilities", "demanded_skills", "soft_skills", "tools_software", "certifications", "requirements"]:
        for item in source.get(key, []) or []:
            pieces.append(str(item or "").strip())
    return len(" ".join([p for p in pieces if p]))


def _select_top_sources(sources: list, max_count: int = 12, min_chars: int = 200) -> list:
    """
    Prefer detailed sources (>= min_chars) up to max_count.
    If total sources are <= max_count, include shorter ones too but place them last.
    """
    valid_sources = [s for s in (sources or []) if isinstance(s, dict)]
    if not valid_sources:
        return []

    long_sources = [s for s in valid_sources if _source_content_length(s) >= min_chars]
    short_sources = [s for s in valid_sources if _source_content_length(s) < min_chars]

    if len(valid_sources) <= max_count:
        return (long_sources + short_sources)[:max_count]
    return long_sources[:max_count]


def search_jobs(state: PipelineState):
    role = state.get("role", "")

    # ---- Step 1: grounded search — ask for per-source coverage ----
    all_market_text = ""
    all_sources = []

    search_prompt = f"""
    Search for comprehensive job market information about the role: '{role}'.

    You MUST cover EACH website or source you find SEPARATELY and in full detail.
    For every source, write a dedicated section that addresses ALL of the following:
    1. How does this source define the role of '{role}'?
    2. What key responsibilities and daily tasks does this source describe?
    3. What education, degrees, and qualifications does this source require?
    4. Which industries or sectors does this source associate with this role?
    5. What technical skills and competencies does this source emphasize?
    6. What soft skills and interpersonal traits does this source mention?
    7. What specific tools, platforms, or software does this source list?
    8. What certifications or credentials does this source recommend?

    Do NOT merge or summarize across sources — each source must have its own section
    with all 8 points covered using details specific to that source.
    Base your answer only on what each source actually says. Write in plain text.
    """
    resp = None
    MAX_ATTEMPTS = 3
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = grounded_response(search_prompt)
            all_market_text = _collect_text_from_response(resp).strip()
            all_sources = _extract_grounding_sources(resp, "Web")
            # Log finish reason / safety info to help diagnose empty responses
            for cand in getattr(resp, 'candidates', None) or []:
                finish = getattr(cand, 'finish_reason', None)
                if finish:
                    print(f"  [grounding] finish_reason={finish}")
            print(f"  INFO: Grounded search attempt {attempt}: {len(all_market_text)} chars, {len(all_sources)} sources")
            if all_market_text:
                break
            print(f"  WARN: Empty response on attempt {attempt}, retrying...")
        except Exception as e:
            print(f"  WARN: Grounded search attempt {attempt} failed: {e}")
            all_market_text = ""
            all_sources = []

    if not all_market_text.strip():
        print("ERROR: Industry trends failed to be extracted.")
        print("   Error: grounded search returned empty text after all retries")
        return {"agent_3_market_intelligence": _fallback_market_intelligence(role)}

    # ---- Step 2: Build per-source context from grounding_supports attribution ----
    per_source_context = _build_per_source_context(resp, all_sources, fallback_text="") if resp is not None else ""
    sources_available = len(all_sources) > 0
    print(f"  [agent3] sources_available={sources_available}, per_source_context len={len(per_source_context)}")

    if sources_available:
        task1_block = f"""════ INPUT B — PER-SOURCE ATTRIBUTED TEXT (unique text per website) ════
{per_source_context}
════ END INPUT B ════

TASK 1 — source_requirements [use INPUT B ONLY]:
For each [Source N] block in Input B, extract the 8 structured fields below.
Use ONLY the text inside that source's block — do NOT copy content from other sources.
Every source must have UNIQUE content reflecting what that specific website actually says.
If a field is not mentioned in that source's block, use "" or [].

Include "source_index" matching the N in [Source N].

Fields per source:
- source_index: integer matching [Source N] above
- role_overview: 1-2 sentences defining the role as described by this specific source (string)
- key_responsibilities: 4-6 core day-to-day duties mentioned by this source (array of strings)
- demanded_skills: Abstract/conceptual knowledge areas and domain competencies this source emphasizes.
  ⚠️ NO named tools, software, platforms, or libraries here — those go in tools_software only.
  Examples: "Machine Learning", "Data Analysis", "Statistical Modeling", "Financial Reporting" (array of strings)
- soft_skills: Interpersonal and behavioral traits mentioned by this source (array of strings)
- tools_software: ONLY specific named products, platforms, frameworks, libraries, or software this source lists.
  ⚠️ NO abstract skills here — only concrete named tools.
  Examples: "Python", "Salesforce", "TensorFlow", "AWS", "Excel", "Jira" (array of strings)
- certifications: Professional credentials, licenses, or certificates mentioned by this source (array of strings)"""
    else:
        task1_block = """TASK 1 — source_requirements [use INPUT A, identify sources from text]:
The research text contains information from several distinct websites/sources.
Identify each distinct source mentioned in the text (by name, domain, or reference).
For each source found, extract the 5 structured fields below from the portion of the text
that is specific to that source. Include "source_name" (website/org name) and
"source_url" (URL if mentioned, else "").

Fields per source:
- source_name: website or organization name (string)
- source_url: URL if mentioned in text, else "" (string)
- role_overview: 1-2 sentences defining the role per this source (string)
- key_responsibilities: 4-6 core duties from this source (array of strings)
- demanded_skills: Abstract/conceptual knowledge areas and domain competencies.
  ⚠️ NO named tools, software, or libraries — those go in tools_software only. (array of strings)
- soft_skills: Interpersonal and behavioral traits mentioned by this source (array of strings)
- tools_software: ONLY specific named products, platforms, frameworks, libraries, or software.
  ⚠️ NO abstract skills — only concrete named tools. (array of strings)
- certifications: Professional credentials, licenses, or certificates mentioned by this source (array of strings)"""

    structure_prompt = f"""You are analyzing job market research for the role: '{role}'.

════ INPUT A — FULL SYNTHESIZED MARKET RESEARCH (all sources combined) ════
{all_market_text}
════ END INPUT A ════

{task1_block}


TASK 2 — demanded_skills [use INPUT A, professional/technical skills only]:
List EVERY professional, technical, and domain-specific skill mentioned anywhere in the full research text.
Do NOT limit the count — include all distinct skills found.
⚠️ EXCLUDE interpersonal/behavioral soft skills — those go in Task 3.
Return short, clear labels (2–4 words max per item).

TASK 3 — soft_skills [use INPUT A, interpersonal/behavioral skills only]:
List every interpersonal, behavioral, and transferable soft skill from the full research text.
⚠️ Non-technical people/behavior skills ONLY — nothing technical from Task 2.
Return 6–10 short labels.

TASK 4 — list_of_technologies [use INPUT A]:
List every specific tool, platform, framework, library, and programming language mentioned.
Return 10–20 items.

Return ONLY valid JSON — no explanation, no markdown:
{{
  "source_requirements": [
    {{
      "source_index": 0,
      "source_name": "Example Site",
      "source_url": "https://example.com",
      "role_overview": "Brief role definition from this source.",
      "key_responsibilities": ["task 1", "task 2", "task 3"],
      "demanded_skills": ["Machine Learning", "Data Analysis"],
      "soft_skills": ["Communication", "Adaptability"],
      "tools_software": ["Python", "TensorFlow", "AWS"],
      "certifications": ["AWS Certified ML Specialty"]
    }}
  ],
  "demanded_skills": ["Skill A", "Skill B"],
  "soft_skills": ["Communication", "Critical Thinking"],
  "list_of_technologies": ["Tool A", "Tool B"]
}}"""
    lm_response = constants.llm.invoke([
        SystemMessage(content=(
            "You are a structured data extraction assistant. "
            "Follow every task instruction exactly. "
            "Output only valid JSON matching the schema provided."
        )),
        HumanMessage(content=structure_prompt),
    ])
    raw = lm_response.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw).strip()

    try:
        search_jobs_json_obj = json.loads(raw)
        source_reqs = search_jobs_json_obj.get("source_requirements", [])
        fields = [
            "role_overview", "key_responsibilities",
            "demanded_skills", "soft_skills", "tools_software", "certifications",
        ]
        if sources_available:
            # Merge 8 structured fields into existing all_sources entries by index
            for sr in source_reqs:
                idx = sr.get("source_index", -1)
                if isinstance(idx, int) and 0 <= idx < len(all_sources):
                    for f in fields:
                        all_sources[idx][f] = sr.get(f, "" if f == "role_overview" else [])
        else:
            # Fallback: build all_sources from LLM-extracted source names
            for sr in source_reqs:
                entry = {
                    'title': sr.get("source_name", "Unknown Source"),
                    'uri': sr.get("source_url", ""),
                    'portal': 'Web',
                    'requirements': [],
                }
                for f in fields:
                    entry[f] = sr.get(f, "" if f == "role_overview" else [])
                all_sources.append(entry)
            print(f"  [agent3] fallback: built {len(all_sources)} sources from LLM extraction")
        # Flat deduplicated job_requirements (key_responsibilities) for Agent 4
        seen_reqs: set = set()
        flat_reqs = []
        for sr in source_reqs:
            for req in sr.get("key_responsibilities", []):
                if req not in seen_reqs:
                    seen_reqs.add(req)
                    flat_reqs.append(req)
        search_jobs_json_obj["job_requirements"] = flat_reqs

        # Count skill frequency across all source cards → keep top 30
        from collections import Counter
        skill_counter: Counter = Counter()
        for src in all_sources:
            for skill in src.get("demanded_skills", []):
                if skill:
                    skill_counter[skill.lower()] += 1
        # Also count skills from the LLM global list (TASK 2) with weight 1
        for skill in search_jobs_json_obj.get("demanded_skills", []):
            if skill:
                skill_counter[skill.lower()] += 1
        # Build canonical label map (first seen casing wins)
        label_map: dict = {}
        for src in all_sources:
            for skill in src.get("demanded_skills", []):
                if skill and skill.lower() not in label_map:
                    label_map[skill.lower()] = skill
        for skill in search_jobs_json_obj.get("demanded_skills", []):
            if skill and skill.lower() not in label_map:
                label_map[skill.lower()] = skill
        top_skills = [label_map[k] for k, _ in skill_counter.most_common(30)]
        search_jobs_json_obj["demanded_skills"] = top_skills
        print(f"  [agent3] demanded_skills → top {len(top_skills)} (from {len(skill_counter)} unique)")

        # Aggregate certifications across all source cards (deduplicated)
        seen_certs: set = set()
        all_certifications = []
        for src in all_sources:
            for cert in src.get("certifications", []):
                if cert and cert.lower() not in seen_certs:
                    seen_certs.add(cert.lower())
                    all_certifications.append(cert)
        search_jobs_json_obj["certifications"] = all_certifications
        print(f"  [agent3] certifications collected: {len(all_certifications)}")

        # Keep only up to 12 sources, prioritizing richer content (>= 200 chars).
        search_jobs_json_obj["sources"] = _select_top_sources(all_sources, max_count=12, min_chars=200)
        print("INFO: Industry trends extracted successfully.")
    except Exception as e:
        print("ERROR: Industry trends failed to be extracted.")
        print(f"   Error: {e}")
        print(f"   Raw LLM output (first 500 chars): {raw[:500]}")
        search_jobs_json_obj = _fallback_market_intelligence(role)

    return {"agent_3_market_intelligence": search_jobs_json_obj}
