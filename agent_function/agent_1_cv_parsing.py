from schemas.pipeline_state import PipelineState
from langchain_core.messages import SystemMessage, HumanMessage
import re
import json
import config.constants as constants

# ---------- Graph A: Extractor (reads file -> runs extract prompt)
def extract_info_node(state: PipelineState):
    text = state.get("input_text", "")

    system_prompt = """
    You are an AI agent specialized in concise document parsing 
    and structured information extraction."""

    parsing_prompt = f"""
    Your goal is to read the given document and extract structured information in a concise yet detailed way.

    Rule-based instructions:
    1. Summarize the most important points of the document in 2–3 sentences.  
    2. Extract professional experiences as a list of short, clear strings.  
    3. Extract skills or technical proficiencies as a list of short, clear strings.  
    4. Extract educational qualifications as a list of short, clear strings.  
    5. Extract notable projects as a list of short, clear strings.  
    6. If a category is not found in the document, return an empty list for that field.  
    
    Document:
    ---START---
    {text}
    ---END---
    
    Return ONLY valid JSON (no extra commentary). 
    {{
    "summary": "2–3 sentence summary of the most important points",  
    "experience": ["experience_1", "experience_2", ...],  
    "skills": ["skill_1", "skill_2", ...],  
    "education": ["education_1", "education_2", ...],  
    "projects": ["project_1", "project_2", ...]  
    }}
    """

    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=parsing_prompt)

    response = constants.llm.invoke([system_message, human_message])
    parsing_raw = response.content
    
    try:
        parsing_json_text = re.search(r"\{.*\}", parsing_raw, re.S).group(0)
        parsing_json_obj = json.loads(parsing_json_text)
        print(f"✅ The file has been parsed successfully.")
        
    except Exception:
        parsing_json_obj = {
            "summary": "",
            "experience": [],
            "skills": [],
            "education": [],
            "projects": [],
                    }
        print(f"❌ The file is failed to be parsed.")

    return {"agent_1_cv_parsing": parsing_json_obj}


    # parsing_prompt = f"""
    # You are a concise information extraction assistant.
    # Given the document below, provide the concise yet detail information.
    
    # Document:
    # ---START---
    # {text}
    # ---END---
    
    # Return ONLY valid JSON (no extra commentary). 
    # {{
    # "summary": 2-3 sentence summary of the most important points (string),
    # "experience": list of professional experiences (array of strings),
    # "skills": list of skills or technical proficiencies (array of strings),
    # "education": list of educational qualifications (array of strings),
    # "projects": list of notable projects (array of strings)
    # }}
    # """

    #     "summary": 2-3 sentence summary of the most important points (string),
    # "experience": list of professional experiences (array of strings),
    # "skills": list of skills or technical proficiencies (array of strings),
    # "education": list of educational qualifications (array of strings),
    # "projects": list of notable projects (array of strings)