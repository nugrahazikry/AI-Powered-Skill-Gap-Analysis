from langgraph.graph import StateGraph, START, END
from config.utils import read_file_node
from agent_function.agent_1_cv_parsing import extract_info_node
from agent_function.agent_2_specialize_skills import skills_node
from agent_function.agent_3_market_intelligence import search_jobs
from agent_function.agent_4_recommendation_report import recommendation_report_agent
from schemas.pipeline_state import PipelineState
import time

def run_pipeline(cv_path: str, role: str, output_dir: str = "output"):
    # os.makedirs(output_dir, exist_ok=True)

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

    # Start with initial state
    initial_state = {"input_path": cv_path, "role": role, }
    result = compiled_pipeline.invoke(initial_state)

    return result


def run_pipeline_with_progress(cv_path: str, role: str, on_stage=None):
    """
    Sequential pipeline runner with real-time progress callbacks and per-agent timing.
    on_stage(stage_key, status, payload_dict) where:
      - status: "running" | "completed"
      - stage_key: "agent_1".."agent_4"
    """
    state: PipelineState = {"input_path": cv_path, "role": role}
    timings_ms = {}

    def _emit(stage_key: str, status: str, payload: dict):
        if on_stage:
            on_stage(stage_key, status, payload or {})

    # Agent 1 (read file + parse CV)
    _emit("agent_1", "running", {"message": "Reading and parsing your CV"})
    t0 = time.perf_counter()
    state.update(read_file_node(state) or {})
    state.update(extract_info_node(state) or {})
    timings_ms["agent_1"] = int((time.perf_counter() - t0) * 1000)
    _emit("agent_1", "completed", {"elapsed_ms": timings_ms["agent_1"]})

    # Agent 2
    _emit("agent_2", "running", {"message": "Classifying explicit and implicit skills"})
    t0 = time.perf_counter()
    state.update(skills_node(state) or {})
    timings_ms["agent_2"] = int((time.perf_counter() - t0) * 1000)
    _emit("agent_2", "completed", {"elapsed_ms": timings_ms["agent_2"]})

    # Agent 3
    _emit("agent_3", "running", {"message": "Researching latest market intelligence"})
    t0 = time.perf_counter()
    state.update(search_jobs(state) or {})
    timings_ms["agent_3"] = int((time.perf_counter() - t0) * 1000)
    _emit("agent_3", "completed", {"elapsed_ms": timings_ms["agent_3"]})

    # Agent 4
    _emit("agent_4", "running", {"message": "Building recommendation report"})
    t0 = time.perf_counter()
    state.update(recommendation_report_agent(state) or {})
    timings_ms["agent_4"] = int((time.perf_counter() - t0) * 1000)
    _emit("agent_4", "completed", {"elapsed_ms": timings_ms["agent_4"]})

    state["timings_ms"] = timings_ms
    return state