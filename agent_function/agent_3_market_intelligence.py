import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
import config.constants as constants
from schemas.pipeline_state import PipelineState

# ---- Nodes ----
def search_jobs(state: PipelineState):
    """Use Gemini to generate search-like job market data."""

    role = state.get("role", "")

    system_prompt = """
    You are an AI agent that simulates job market research."""

    search_jobs_prompt = f"""
    Find the most recent job listings, requirements, skills, and technologies 
    commonly requested for the role '{role}'. Provide concise bullet points 
    as if you had searched the web.
    
    Return ONLY valid JSON (no extra commentary).
    {{
    "job_listings": list of recent job titles or posting summaries (array of strings),
    "job_requirements": list of common job requirements, qualifications, or responsibilities (array of strings),
    "skills": list of skills explicitly requested in job postings (array of strings),
    "list_of_technologies": list of technologies, tools, or frameworks commonly requested (array of strings)
    }}
    """

    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=search_jobs_prompt)

    response = constants.llm.invoke([system_message, human_message])
    search_jobs_raw = response.content

    try:
        search_jobs_json_text = re.search(r"\{.*\}", search_jobs_raw, re.S).group(0)
        search_jobs_json_obj = json.loads(search_jobs_json_text)
        print(f"✅ Industry trends have been successfully extracted.")
    
    except Exception:
        search_jobs_json_obj = {
            "job_listings": [],
            "job_requirements": [],
            "skills": [],
            "list_of_technologies": [] 
            }
        print(f"❌ Industry trends are failed to be extracted.")

    return {"agent_3_market_intelligence": search_jobs_json_obj}
