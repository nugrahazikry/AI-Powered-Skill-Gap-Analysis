import os
import json
from langgraph.graph import StateGraph, START, END
from config.utils import read_file_node
from agent_function.agent_1_cv_parsing import extract_info_node
from agent_function.agent_2_specialize_skills import skills_node
from agent_function.agent_3_market_intelligence import search_jobs
from agent_function.agent_4_recommendation_report import recommendation_report_agent
from schemas.pipeline_state import PipelineState

# ---- Build ONE Graph ----
pipeline = StateGraph(PipelineState)

pipeline.add_node("read_file", read_file_node)
pipeline.add_node("extract_info", extract_info_node)
pipeline.add_node("classify_skills", skills_node)
pipeline.add_node("search", search_jobs)
pipeline.add_node("report", recommendation_report_agent)

pipeline.add_edge(START, "read_file")
pipeline.add_edge("read_file", "extract_info")
pipeline.add_edge("extract_info", "classify_skills")
pipeline.add_edge("classify_skills", "search")
pipeline.add_edge("search", "report")
pipeline.add_edge("report", END)

compiled_pipeline = pipeline.compile()

def run_pipeline(cv_path: str, role: str, output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)

    # Start with initial state
    initial_state = {"input_path": cv_path, "role": role, }
    result = compiled_pipeline.invoke(initial_state)

    # Save final result
    final_path = os.path.join(output_dir, "ai_pipeline_final.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Pipeline finished! Saved at {final_path}")
    return result


if __name__ == "__main__":
    run_pipeline(cv_path="input/CV Zikry Adjie Nugraha.txt", role="Chemical Engineer")