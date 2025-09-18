import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
import config.constants as constants
from schemas.pipeline_state import PipelineState

def recommendation_report_agent(state: PipelineState):
    explicit_skills = state.get("explicit_skills", "")
    implicit_skills = state.get("implicit_skills", "")
    role = state.get("market_intelligence", "")
    market_intelligence = state.get("market_intelligence", "")

    system_prompt = """
    You are a strategist and communicator AI agent."""

    recommendation_report_prompt = f"""
    Your task is to synthesize the analysis from two agents (Specialized Skill Analyst & Market Intelligence Agent).

    ### Specialized Skill Analyst:
    Explicit Skills: {explicit_skills}
    Implicit Skills: {implicit_skills}

    ### Market Intelligence (role: {role}):
    {market_intelligence}

    Return ONLY valid JSON (no extra commentary).
    {{
    "skill_gap_analysis": analysis of the difference between candidate's skills both explicit and implicit, and the market requirements (string),
    "key_strengths": summary of the strongest skills or experiences of the candidate (string),
    "upskilling_plan": concise plan suggesting areas for improvement or additional learning (string),
    "is_candidate_recommended":  boolean indicating whether the candidate is a good fit for the role (true/false),
    "recommendation_reason": explanation supporting the recommendation decision (string)
    }}
    """

    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=recommendation_report_prompt)

    response = constants.llm.invoke([system_message, human_message])
    recommendation_report_raw = response.content

    try:
        # Extract JSON block
        recommendation_report_json_text = re.search(r"\{.*\}", recommendation_report_raw, re.S).group(0)
        recommendation_report_json_obj = json.loads(recommendation_report_json_text)
        print(f"✅ Recommendation report has been created successfully.")
    
    except Exception:
        recommendation_report_json_obj = {
            "skill_gap_analysis": "",
            "key_strengths": "",
            "upskilling_plan": "",
            "is_candidate_recommended": False,
            "recommendation_reason": "Parsing failed, fallback result."
        }
        print(f"❌ Recommendation report is failed to be created.")

    return {"agent_4_recommendation_report": recommendation_report_json_obj}