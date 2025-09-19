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
    Find the most recent job listings, requirements, skills, and technologies commonly requested for the role '{role}'. 
    Act as if you searched the web for current job postings and market demand for this role and synthesize the results into concise bullet points.

    Rule-based instructions:  
    1. Focus on the most recent and frequently repeated requirements across job postings (prioritize items that appear in multiple listings).  
    2. Provide the most **detailed and comprehensive information** for each requirement — expand responsibilities, skill sets, and qualifications instead of using short phrases.  
    3. If you couldn't find relevant information, return an empty list for that field.  
    4. Do not include source URLs or commentary in the JSON output (the user asked for JSON-only).  
    5. If you perform a web search to produce this output, prefer authoritative job sites and company listings and ensure the items reflect current demand in the market.  

    Return ONLY valid JSON (no extra commentary).
    {{
    "job_requirements": ["common requirement 1", "common requirement 2", "..."],
    "demanded_skills": ["skill 1", "skill 2", "..."],
    "list_of_technologies": ["technology/tool/framework 1", "technology 2", "..."]
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
            "job_requirements": [],
            "demanded_skills": [],
            "list_of_technologies": [] 
            }
        print(f"❌ Industry trends are failed to be extracted.")

    return {"agent_3_market_intelligence": search_jobs_json_obj}


# Find the most recent job listings, requirements, skills, and technologies 
#     commonly requested for the role '{role}'. Provide concise bullet points 
#     as if you had searched the web.
    
#     Return ONLY valid JSON (no extra commentary).
#     {{
#     "job_requirements": list of common job requirements, qualifications, or responsibilities (array of strings),
#     "demanded_skills": list of skills explicitly requested in job postings (array of strings),
#     "list_of_technologies": list of technologies, tools, or frameworks commonly requested (array of strings)
#     }}