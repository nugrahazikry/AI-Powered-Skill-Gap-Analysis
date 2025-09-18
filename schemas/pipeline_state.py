from typing_extensions import TypedDict

# ---- Unified State ----
class PipelineState(dict):
    # First input, read_file_node
    input_path: str

    # First input, input for agent 3
    role: str

    # Result read_file_node, input for agent_1
    input_text: str

    # result extract_info_node agent_1, input for agent_2
    agent_1_cv_parsing: dict

    # Result skills_node agent_2, input for agent_4
    agent_2_specialize_skills: dict

    # Result search_jobs agent_3, input for agent_4
    agent_3_market_intelligence: dict

    # Final result 
    agent_4_recommendation_report: dict