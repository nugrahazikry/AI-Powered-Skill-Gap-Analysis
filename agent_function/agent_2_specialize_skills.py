from schemas.pipeline_state import PipelineState
from langchain_core.messages import SystemMessage, HumanMessage
import re
import json
import config.constants as constants

# ---------- Graph B: Skills extractor (consumes text -> returns explicit & implicit skills)
def skills_node(state: PipelineState):
    text = state.get("input_text", "")

    system_prompt = """
    You are a specialized AI agent whose role is to identify and classify skills 
    from text into explicit and implicit categories."""

    skill_extractor_prompt = f"""
    You are a helpful assistant that classifies skills.

    Document:
    ---START---
    {text}
    ---END---

    1) "explicit_skills": list **only** skills that are directly mentioned in the text (single words or short phrases).
    2) "implicit_skills": list skills that are reasonably inferred from duties/responsibilities (give a one-line evidence note for each inferred skill).

    Return ONLY valid JSON (no extra commentary).
    {{
    "explicit_skills": ["skillA", "skillB"],
    "implicit_skills": [ {{"skill":"skillX", "evidence":"one-line evidence"}}, ... ]
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