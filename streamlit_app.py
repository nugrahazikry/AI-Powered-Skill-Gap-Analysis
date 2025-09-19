import streamlit as st
import pandas as pd
from main import run_pipeline

def list_to_markdown(items):
    return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])

def main():
    st.title("CV & Skills Parsing Demo")

    # Frontend inputs
    uploaded_file = st.file_uploader("Upload a TXT file", type="txt")
    target_role = st.text_input("Enter target role")

    # Add analyze button
    if st.button("Analyze"):
        if uploaded_file and target_role:
            
            # Save uploaded file to temporary path
            temp_path = "temp.txt"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            multi_agents_result = run_pipeline(cv_path=temp_path, role=target_role)

            with st.expander("Agent 1 - CV Parsing", expanded=False):
                markdown_cv_parsing = f"""### CV Parsing

**Candidate name**\n
{multi_agents_result['agent_1_cv_parsing']['title']}

**CV summary**\n
{multi_agents_result['agent_1_cv_parsing']['summary']}

**Candidate experience**\n
{list_to_markdown(multi_agents_result['agent_1_cv_parsing']['experience'])}

**Candidate skills**\n
{list_to_markdown(multi_agents_result['agent_1_cv_parsing']['skills'])}

**Candidate education**\n
{list_to_markdown(multi_agents_result['agent_1_cv_parsing']['education'])}

**Candidate projects**\n
{list_to_markdown(multi_agents_result['agent_1_cv_parsing']['projects'])}"""

                st.markdown(markdown_cv_parsing)


            with st.expander("Agent 2 - Skills Specialization", expanded=False):
                markdown_candidate_skills = f"""### Skills Specialization

**Candidate explicit skills**\n
{list_to_markdown(multi_agents_result['agent_2_specialize_skills']['explicit_skills'])}

**Candidate implicit **\n
{list_to_markdown(multi_agents_result['agent_2_specialize_skills']['implicit_skills'])}"""

                st.markdown(markdown_candidate_skills)


            with st.expander("Agent 3 - Market Analysis", expanded=False):
                markdown_market_analysis = f"""### Market Analysis

**Job listings**\n
{list_to_markdown(multi_agents_result['agent_3_market_intelligence']['job_listings'])}

**Job requirements**\n
{list_to_markdown(multi_agents_result['agent_3_market_intelligence']['job_requirements'])}

**Demanded skills**\n
{list_to_markdown(multi_agents_result['agent_3_market_intelligence']['skills'])}

**List of demand technologies**\n
{list_to_markdown(multi_agents_result['agent_3_market_intelligence']['list_of_technologies'])}"""

                st.markdown(markdown_market_analysis)


            # st.subheader("Agent 4 - Recommendation Report")
            with st.expander("Agent 4 - Recommendation Report", expanded=False):
                markdown_report = f"""### Final Report

**Skill gap analysis**\n
{multi_agents_result['agent_4_recommendation_report']['skill_gap_analysis']}

**Key Strengths**\n
{multi_agents_result['agent_4_recommendation_report']['key_strengths']}

**Upskilling Plan**\n
{multi_agents_result['agent_4_recommendation_report']['upskilling_plan']}"""

                st.markdown(markdown_report)


if __name__ == "__main__":
    main()