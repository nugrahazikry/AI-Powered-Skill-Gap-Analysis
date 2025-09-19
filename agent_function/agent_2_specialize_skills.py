from schemas.pipeline_state import PipelineState
from langchain_core.messages import SystemMessage, HumanMessage
import re
import json
import config.constants as constants

# ---------- Graph B: Skills Specialization
def skills_node(state: PipelineState):
    summary = state.get("agent_1_cv_parsing", {}).get("summary", "")
    experience = state.get("agent_1_cv_parsing", {}).get("experience", [])
    skills = state.get("agent_1_cv_parsing", {}).get("skills", [])
    education = state.get("agent_1_cv_parsing", {}).get("education", [])
    projects = state.get("agent_1_cv_parsing", {}).get("projects", [])

    system_prompt = """
    You are a specialized AI agent whose role is to identify and classify skills 
    from text into explicit and implicit categories."""

    skill_extractor_prompt = f"""
    Your task is to extract both explicit and implicit skills from the given document.  

    Rule-based instructions:
    1. "explicit_skills": List **only** the skills that are directly mentioned in the text. Each entry should be a single word or short phrase.  
    2. "implicit_skills": List skills that can be reasonably inferred from the duties, responsibilities, or context of the document. For each inferred skill, include a short one-line evidence note explaining the reasoning.  
    3. If no skills are found for a category, return an empty list for that field.  

    Document:
    ---START---
    summary: {summary}
    experience: {experience}
    skills: {skills}
    education: {education}
    projects: {projects}
    ---END---

    Return ONLY valid JSON (no extra commentary).
    {{
  "explicit_skills": ["skillA", "skillB"],  
  "implicit_skills": [  
    {{"skill": "skillX", "evidence": "one-line evidence"}},  
    {{"skill": "skillY", "evidence": "one-line evidence"}}  
    ]  
    }}
    """
    
    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=skill_extractor_prompt)

    response = constants.llm.invoke([system_message, human_message])
    skill_extractor_raw = response.content

    try:
        skill_extractor_json_text = re.search(r"\{.*\}", skill_extractor_raw, re.S).group(0)
        skill_extractor_json_obj = json.loads(skill_extractor_json_text)
        print(f"✅ The skills have been listed successfully.")
    
    except Exception:
        skill_extractor_json_obj = {
            "explicit_skills": [], 
            "implicit_skills": []
            }
        print(f"❌ The skills are failed to be listed.")

    return {"agent_2_specialize_skills": skill_extractor_json_obj}