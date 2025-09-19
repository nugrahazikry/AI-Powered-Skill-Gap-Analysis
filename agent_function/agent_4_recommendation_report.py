import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
import config.constants as constants
from schemas.pipeline_state import PipelineState

def recommendation_report_agent(state: PipelineState):
    explicit_skills = state.get("agent_2_specialize_skills", {}).get("explicit_skills", [])
    implicit_skills = state.get("agent_2_specialize_skills", {}).get("implicit_skills", [])
    role = state.get("role", "")
    market_intelligence = state.get("agent_3_market_intelligence", "")

    system_prompt = """
    You are a strategist and communicator AI agent."""

    recommendation_report_prompt = f"""
    Your task is to synthesize the analysis from two agents: 
    1. Specialized Candidate Skill Analyst 
    2. Market Intelligence Agent.

    You must give the user clear insights by comparing the candidate's specialized skills with the current market demand for the given role.

    Rule-based instructions:
    1. Compare the information given based on the candidate's explicit and implicit skills with the market demand. Highlight both alignment and gaps.
    2. Give your thoughts and point of view about how well the candidate fits the role requirements.
    3. Identify overlaps between candidate skills and what the market values most for this role.
    4. Point out skills the candidate has that may provide unique advantages even if not explicitly listed in the market demand.
    5. Recommend targeted actions (learning, certifications, or experiences) to close the gap between candidate profile and job market requirements.

    ### Specialized Candidate Skill Analyst:
    Explicit Skills: {explicit_skills}
    Implicit Skills: {implicit_skills}

    ### Market Demand Job Analysis (role: {role}):
    {market_intelligence}

    Return ONLY valid JSON (no extra commentary).
    {{
    "skill_gap_analysis": analysis of the difference between candidate's skills (explicit & implicit) and the market requirements (string),
    "key_strengths": summary of the strongest skills or experiences of the candidate based on the comparison (string),
    "upskilling_plan": concise plan suggesting areas for improvement or additional learning based on missing market-demanded skills (string),
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
        }
        print(f"❌ Recommendation report is failed to be created.")

    return {"agent_4_recommendation_report": recommendation_report_json_obj}